#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vogel-Kamera Auto-Trigger mit AI-Objekterkennung
================================================

Überwacht kontinuierlich das Vogelhaus und startet automatisch Aufnahmen,
wenn ein Vogel erkannt wird.

Features:
- 🐦 Automatischer Trigger bei Vogel-Erkennung
- 📊 Ressourcen-Monitoring (CPU, Temperatur, Load)
- ⚠️ Automatisches Beenden bei zu hoher System-Last
- 📈 Status-Report alle 15 Minuten
- 🔄 Cooldown-System zwischen Aufnahmen
- 🛑 Sauberes Beenden und Cleanup

Verwendung:
    python ai-had-kamera-auto-trigger.py --trigger-duration 2 --ai-model bird-species
    
    Strg+C zum sauberen Beenden
"""

import paramiko
from scp import SCPClient
from datetime import datetime, timedelta
import locale
import threading
import time
import subprocess
import os
import signal
import argparse
import sys

# Import config und version aus python-skripte Verzeichnis
# Füge Pfade zum Python-Path hinzu
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
python_skripte_dir = os.path.join(project_root, 'python-skripte')

sys.path.insert(0, python_skripte_dir)

from config import config
from __version__ import __version__

# Import StreamProcessor aus gleichem Verzeichnis
try:
    sys.path.insert(0, script_dir)
    from stream_processor import StreamProcessor
    HAS_STREAM_PROCESSOR = True
except ImportError:
    HAS_STREAM_PROCESSOR = False
    print("⚠️  StreamProcessor nicht gefunden - verwende Fallback-Modus")
    print("   Installiere Dependencies: pip install opencv-python ultralytics")

# Setze die Locale auf Deutsch
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

# Globale Variablen für Cleanup
running = True
monitoring_thread = None
trigger_count = 0
last_trigger_time = None
start_time = datetime.now()
stream_processor = None  # StreamProcessor-Instanz
monitoring_paused = False  # Flag zum Pausieren der Status-Reports während Aufnahme

# Argumente parsen
parser = argparse.ArgumentParser(
    description='''🐦 Vogel-Kamera Auto-Trigger mit AI-Objekterkennung
    
    Überwacht kontinuierlich das Vogelhaus und startet automatisch HD-Aufnahmen,
    wenn ein Vogel erkannt wird.
    
    Beispiele:
    # Standard: 2 Minuten Aufnahme, bird-species Modell
    python ai-had-kamera-auto-trigger.py --trigger-duration 2 --ai-model bird-species
    
    # Mit Custom-Einstellungen
    python ai-had-kamera-auto-trigger.py --trigger-duration 3 --cooldown 60 --trigger-threshold 0.5
    
    Beenden: Strg+C für sauberen Shutdown''',
    formatter_class=argparse.RawDescriptionHelpFormatter
)

parser.add_argument('--version', action='version', version=f'Vogel-Kamera-Linux Auto-Trigger v{__version__}')
parser.add_argument('--trigger-duration', type=int, default=2, help='Aufnahmedauer bei Vogel-Erkennung in Minuten (default: 2)')
parser.add_argument('--ai-model', type=str, default='bird-species', choices=['yolov8', 'bird-species', 'custom'], 
                    help='AI-Modell für Objekterkennung (default: bird-species)')
parser.add_argument('--ai-model-path', type=str, help='Pfad zu benutzerdefiniertem AI-Modell (für --ai-model custom)')
parser.add_argument('--cooldown', type=int, default=30, help='Wartezeit zwischen Aufnahmen in Sekunden (default: 30)')
parser.add_argument('--trigger-threshold', type=float, default=0.45, help='AI-Schwelle für Trigger (default: 0.45)')
parser.add_argument('--preview-fps', type=int, default=5, help='FPS für Monitoring-Modus (default: 5)')
parser.add_argument('--preview-width', type=int, default=640, help='Breite für Monitoring-Vorschau (default: 640)')
parser.add_argument('--preview-height', type=int, default=480, help='Höhe für Monitoring-Vorschau (default: 480)')
parser.add_argument('--max-cpu-temp', type=float, default=70.0, help='Maximale CPU-Temperatur in °C (default: 70)')
parser.add_argument('--max-cpu-load', type=float, default=3.0, help='Maximale CPU-Load (default: 3.0)')
parser.add_argument('--status-interval', type=int, default=15, help='Status-Report Intervall in Minuten (default: 15)')
parser.add_argument('--width', type=int, default=4096, help='Breite für HD-Aufnahme (default: 4096)')
parser.add_argument('--height', type=int, default=2160, help='Höhe für HD-Aufnahme (default: 2160)')
parser.add_argument('--rotation', type=int, choices=[0, 90, 180, 270], default=180, help='Rotation des Videos (default: 180)')
parser.add_argument('--cam', type=int, default=0, choices=[0, 1], help='Kamera-ID (default: 0)')

args = parser.parse_args()

# SSH-Verbindungsdetails für den Remote-Host
remote_host = config.get_remote_host_config()

# Konfiguration validieren
config_errors = config.validate_config()
if config_errors:
    print("⚠️ Konfigurationsprobleme gefunden:")
    for error in config_errors:
        print(f"  - {error}")
    print("\nBitte konfigurieren Sie das System entsprechend der README.md")
    exit(1)

print(f"""
╔══════════════════════════════════════════════════════════════╗
  🐦 Vogel-Kamera Auto-Trigger v{__version__}
╠══════════════════════════════════════════════════════════════╣
  Modus: Automatische Vogel-Erkennung
  AI-Modell: {args.ai_model}
  Trigger-Dauer: {args.trigger_duration} Minuten
  Cooldown: {args.cooldown} Sekunden
  Schwelle: {args.trigger_threshold}
╚══════════════════════════════════════════════════════════════╝
""")

def get_system_status():
    """Hole System-Status vom Remote-Host"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                   key_filename=remote_host['key_filename'], timeout=10)
        
        # CPU-Temperatur
        stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
        temp_output = stdout.read().decode().strip()
        temp_val = float(temp_output.replace("temp=", "").replace("'C", ""))
        
        # CPU Load
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        load_1min = 0.0
        if "load average:" in uptime_output:
            load_1min = float(uptime_output.split("load average:")[1].split(',')[0].strip().replace(',', '.'))
        
        # Festplatte
        stdin, stdout, stderr = ssh.exec_command("df / | tail -1")
        disk_output = stdout.read().decode().strip()
        disk_parts = disk_output.split()
        used_percent = int(disk_parts[4].replace('%', '')) if len(disk_parts) >= 5 else 0
        
        # Memory
        stdin, stdout, stderr = ssh.exec_command("free -h | grep 'Speicher\\|Mem'")
        mem_output = stdout.read().decode().strip()
        mem_parts = mem_output.split()
        mem_used = mem_parts[2] if len(mem_parts) >= 3 else "N/A"
        mem_total = mem_parts[1] if len(mem_parts) >= 2 else "N/A"
        
        ssh.close()
        
        return {
            'temp': temp_val,
            'load': load_1min,
            'disk_percent': used_percent,
            'mem_used': mem_used,
            'mem_total': mem_total,
            'healthy': temp_val < args.max_cpu_temp and load_1min < args.max_cpu_load
        }
    
    except Exception as e:
        print(f"⚠️ Fehler beim Abrufen des System-Status: {e}")
        return None

def check_for_bird_detection():
    """
    Prüfe ob ein Vogel erkannt wurde mittels AI-Stream-Analyse
    
    Verwendet StreamProcessor für:
    - TCP/RTSP Stream vom Raspberry Pi
    - Echtzeit AI-Inferenz auf Preview-Frames
    - YOLOv8 bird-species Erkennung
    
    Returns:
        bool: True wenn Vogel erkannt, sonst False
    """
    global stream_processor
    
    # Verwende StreamProcessor wenn verfügbar
    if HAS_STREAM_PROCESSOR and stream_processor:
        try:
            # Verarbeite Frame mit AI-Erkennung
            bird_detected = stream_processor.process_frame()
            return bird_detected
            
        except Exception as e:
            if args.debug:
                print(f"⚠️ Fehler bei Stream-Verarbeitung: {e}")
            return False
    
    # Fallback: Keine echte Erkennung möglich
    else:
        # Gibt immer False zurück wenn kein StreamProcessor verfügbar
        return False

def trigger_recording():
    """Starte HD-Aufnahme auf Remote-Host"""
    global trigger_count, last_trigger_time, stream_processor, monitoring_paused
    
    timestamp = datetime.now().strftime("%A__%Y-%m-%d__%H-%M-%S")
    year = datetime.now().year
    week_number = datetime.now().isocalendar()[1]
    
    # Pausiere Status-Reports während Aufnahme (reduziert System-Last)
    monitoring_paused = True
    print(f"\n🎬 TRIGGER! Starte {args.trigger_duration}-minütige Aufnahme...")
    print(f"   Zeitstempel: {timestamp}")
    print(f"   ⏸️  Status-Reports pausiert während Aufnahme")
    
    try:
        # WICHTIG: Stream temporär trennen und auf Pi stoppen, da Kamera exklusiv genutzt wird
        if stream_processor and stream_processor.connected:
            print("   📡 Trenne Preview-Stream (Kamera wird für HD-Aufnahme benötigt)...")
            stream_processor.disconnect()
            
            # Stoppe Stream-Prozess auf Raspberry Pi (inkl. Wrapper!)
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                           key_filename=remote_host['key_filename'], timeout=5)
                # Stoppe Wrapper (der rpicam-vid automatisch neu startet)
                # UND rpicam-vid selbst
                ssh.exec_command("pkill -9 -f stream-wrapper.sh; pkill -9 -f rpicam-vid; rm -f /tmp/rtsp-stream.pid")
                ssh.close()
                time.sleep(2)  # Warte bis Prozesse sicher beendet sind
                print("   ✅ Preview-Stream auf Raspberry Pi gestoppt")
            except Exception as e:
                print(f"   ⚠️  Konnte Stream auf Raspberry Pi nicht stoppen: {e}")
        
        # Rufe das Haupt-Aufnahme-Skript auf (im Hauptverzeichnis)
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        recording_script = os.path.join(script_dir, 'python-skripte', 'ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py')
        
        cmd = [
            'python3',
            recording_script,
            '--duration', str(args.trigger_duration),
            '--width', str(args.width),
            '--height', str(args.height),
            '--rotation', str(args.rotation),
            '--cam', str(args.cam),
            '--ai-modul', 'on',
            '--ai-model', args.ai_model,
            '--no-stream-restart'  # Auto-Trigger managed Stream-Neustart selbst
        ]
        
        if args.ai_model == 'custom' and args.ai_model_path:
            cmd.extend(['--ai-model-path', args.ai_model_path])
        
        # Führe Aufnahme-Skript aus
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            trigger_count += 1
            last_trigger_time = datetime.now()
            print(f"✅ Aufnahme #{trigger_count} erfolgreich abgeschlossen")
        else:
            print(f"❌ Fehler bei Aufnahme: Exit Code {result.returncode}")
        
        # Stream wieder starten und verbinden nach Aufnahme
        if stream_processor:
            print("   📡 Starte Preview-Stream auf Raspberry Pi neu...")
            try:
                # Starte Stream-Skript auf Raspberry Pi neu
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                           key_filename=remote_host['key_filename'], timeout=5)
                # Starte Stream im Hintergrund mit bash -c für persistente Ausführung
                ssh.exec_command("bash -c 'nohup ~/start-rtsp-stream.sh > /tmp/stream-restart.log 2>&1 & disown'")
                ssh.close()
                print("   ✅ Preview-Stream-Start initiiert")
                
                # Warte bis Stream bereit ist (rpicam-vid braucht ~5-8 Sekunden für Init)
                print("   ⏳ Warte auf Stream-Initialisierung (8 Sekunden)...")
                time.sleep(8)
                
                # Verbinde Client wieder
                print("   📡 Verbinde Client zum Preview-Stream...")
                if stream_processor.connect():
                    print("   ✅ Preview-Stream wieder verbunden")
                else:
                    print("   ⚠️  Konnte Client nicht verbinden, versuche später erneut")
            except Exception as e:
                print(f"   ⚠️  Fehler beim Neustart des Preview-Streams: {e}")
            
            # Cooldown-Phase NACH der Aufnahme (Status-Reports bleiben pausiert)
            print(f"   ⏳ Cooldown: {args.cooldown} Sekunden (keine weiteren Trigger)...")
            time.sleep(args.cooldown)
            
            # Setze Status-Reports fort nach Cooldown
            monitoring_paused = False
            print("   ▶️  Status-Reports wieder aktiv - Überwachung läuft\n")
    
    except Exception as e:
        print(f"❌ Fehler beim Triggern der Aufnahme: {e}")
        # Versuche Stream neu zu starten bei Fehler
        if stream_processor:
            print("   📡 Versuche Preview-Stream neu zu starten...")
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                           key_filename=remote_host['key_filename'], timeout=5)
                # Nutze bash -c mit disown für persistente Ausführung
                ssh.exec_command("bash -c 'nohup ~/start-rtsp-stream.sh > /tmp/stream-restart.log 2>&1 & disown'")
                ssh.close()
                time.sleep(8)  # Warte länger bei Fehler-Recovery
                stream_processor.connect()
            except:
                pass
        
        # Cooldown auch bei Fehler einhalten
        print(f"   ⏳ Cooldown: {args.cooldown} Sekunden...")
        time.sleep(args.cooldown)
        
        # Setze Status-Reports fort auch bei Fehler
        monitoring_paused = False
        print("   ▶️  Status-Reports wieder aktiv\n")

def print_status_report():
    """Gebe Status-Report aus"""
    global trigger_count, last_trigger_time, start_time
    
    uptime = datetime.now() - start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    
    status = get_system_status()
    
    print(f"\n{'='*70}")
    print(f"📊 STATUS-REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print(f"⏱️  Laufzeit: {hours}h {minutes}min")
    print(f"🎬 Aufnahmen getriggert: {trigger_count}")
    
    if last_trigger_time:
        since_last = datetime.now() - last_trigger_time
        print(f"🕐 Letzte Aufnahme: vor {int(since_last.total_seconds() // 60)} Minuten")
    else:
        print(f"🕐 Letzte Aufnahme: Noch keine")
    
    if status:
        temp_status = "🟢" if status['temp'] < 50 else "🟡" if status['temp'] < 60 else "🔴"
        load_status = "🟢" if status['load'] < 1.0 else "🟡" if status['load'] < 2.0 else "🔴"
        disk_status = "🟢" if status['disk_percent'] < 80 else "🟡" if status['disk_percent'] < 90 else "🔴"
        
        print(f"\n🖥️  Remote-Host ({remote_host['hostname']}):")
        print(f"   🌡️  CPU-Temp: {status['temp']:.1f}°C {temp_status}")
        print(f"   ⚡ CPU-Load: {status['load']:.2f} {load_status}")
        print(f"   💾 Festplatte: {status['disk_percent']}% belegt {disk_status}")
        print(f"   💭 RAM: {status['mem_used']} / {status['mem_total']}")
        
        if not status['healthy']:
            print(f"\n⚠️  WARNUNG: System-Ressourcen kritisch!")
    
    print(f"{'='*70}\n")

def resource_monitor():
    """Überwache System-Ressourcen"""
    global running, monitoring_paused
    
    last_status_report = datetime.now()
    status_interval = timedelta(minutes=args.status_interval)
    
    while running:
        try:
            # Status-Report alle X Minuten (nur wenn nicht pausiert)
            if datetime.now() - last_status_report >= status_interval:
                if not monitoring_paused:
                    print_status_report()
                    last_status_report = datetime.now()
                # Wenn pausiert, warte einfach bis zur Fortsetzung
                # (last_status_report wird NICHT aktualisiert, Report kommt nach Pause)
            
            # Prüfe System-Status
            status = get_system_status()
            
            if status and not status['healthy']:
                print(f"\n🚨 KRITISCH: System-Ressourcen überschritten!")
                print(f"   🌡️  CPU-Temp: {status['temp']:.1f}°C (Max: {args.max_cpu_temp}°C)")
                print(f"   ⚡ CPU-Load: {status['load']:.2f} (Max: {args.max_cpu_load})")
                print(f"\n⛔ Beende Auto-Trigger aus Sicherheitsgründen...")
                
                shutdown()
                break
            
            time.sleep(60)  # Prüfe jede Minute
        
        except Exception as e:
            print(f"⚠️ Fehler im Ressourcen-Monitor: {e}")
            time.sleep(60)

def monitoring_loop():
    """Haupt-Monitoring-Loop für Vogel-Erkennung"""
    global running, last_trigger_time
    
    print("👁️  Starte Vogel-Überwachung...")
    print(f"   Preview: {args.preview_width}x{args.preview_height} @ {args.preview_fps}fps")
    print(f"   Schwelle: {args.trigger_threshold}")
    print(f"   Cooldown: {args.cooldown}s zwischen Aufnahmen")
    print("\n🔍 Überwache Vogelhaus... (Strg+C zum Beenden)\n")
    
    while running:
        try:
            # Prüfe ob Cooldown noch aktiv
            if last_trigger_time:
                time_since_last = (datetime.now() - last_trigger_time).total_seconds()
                if time_since_last < args.cooldown:
                    time.sleep(1)
                    continue
            
            # PLACEHOLDER: Prüfe auf Vogel-Erkennung
            # In echter Implementierung: AI-Analyse auf Preview-Stream
            bird_detected = check_for_bird_detection()
            
            if bird_detected:
                print(f"🐦 Vogel erkannt!")
                trigger_recording()
                
                # Cooldown läuft jetzt - Status-Reports bleiben pausiert
                # (monitoring_paused wird in trigger_recording() erst am Ende zurückgesetzt)
            
            else:
                # Warte kurz bevor nächster Check
                time.sleep(1.0 / args.preview_fps)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️ Fehler im Monitoring-Loop: {e}")
            time.sleep(5)

def shutdown():
    """Sauberes Beenden"""
    global running, stream_processor
    
    print("\n\n🛑 Beende Auto-Trigger...")
    running = False
    
    # Gebe finalen Status-Report aus
    print_status_report()
    
    # Beende StreamProcessor
    if stream_processor:
        print("📡 Trenne Stream-Verbindung...")
        stream_processor.disconnect()
        
        # Zeige Stream-Statistiken
        stats = stream_processor.get_statistics()
        print(f"   Frames verarbeitet: {stats['frames_processed']}")
        print(f"   Vögel erkannt: {stats['birds_detected']}")
        if stats['avg_inference_time'] > 0:
            print(f"   Ø Inferenz-Zeit: {stats['avg_inference_time']*1000:.1f}ms")
    
    # Beende alle Remote-Prozesse
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                   key_filename=remote_host['key_filename'], timeout=10)
        
        ssh.exec_command("pkill -f rpicam-vid")
        ssh.exec_command("pkill -f arecord")
        ssh.close()
        print("✅ Remote-Prozesse beendet")
    except Exception as e:
        print(f"⚠️ Fehler beim Beenden der Remote-Prozesse: {e}")
    
    print("\n👋 Auto-Trigger sauber beendet. Auf Wiedersehen!")
    sys.exit(0)

def signal_handler(sig, frame):
    """Signal-Handler für Ctrl+C"""
    shutdown()

# Setze Signal-Handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Hauptfunktion"""
    global monitoring_thread, stream_processor
    
    # Prüfe Verbindung zum Remote-Host
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                   key_filename=remote_host['key_filename'], timeout=10)
        ssh.close()
        print(f"✅ Verbindung zu {remote_host['hostname']} erfolgreich\n")
    except Exception as e:
        print(f"❌ Keine Verbindung zu {remote_host['hostname']}: {e}")
        sys.exit(1)
    
    # Initialisiere StreamProcessor wenn verfügbar
    if HAS_STREAM_PROCESSOR:
        print("🎬 Initialisiere Stream-Verarbeitung...")
        stream_processor = StreamProcessor(
            host=remote_host['hostname'],
            port=8554,  # Standard RTSP/TCP Port
            model_type=args.ai_model,
            model_path=args.ai_model_path,
            threshold=args.trigger_threshold,
            width=args.preview_width,
            height=args.preview_height,
            fps=args.preview_fps,
            trigger_duration=2.0,  # Vogel muss 2 Sekunden erkannt werden für Trigger
            debug=False
        )
        
        # Verbinde mit Preview-Stream
        print(f"📡 Verbinde mit Preview-Stream: tcp://{remote_host['hostname']}:8554...")
        if stream_processor.connect():
            print("✅ Preview-Stream verbunden")
            print(f"   AI-Model: {args.ai_model}")
            print(f"   Threshold: {args.trigger_threshold}")
            print(f"   Trigger-Dauer: 2.0s (Vogel muss konsistent erkannt werden)")
            print(f"   Resolution: {args.preview_width}x{args.preview_height} @ {args.preview_fps}fps\n")
        else:
            print("❌ Konnte nicht mit Preview-Stream verbinden")
            print("⚠️  Stelle sicher dass der Preview-Stream auf dem Raspberry Pi läuft:")
            print(f"   ssh {remote_host['username']}@{remote_host['hostname']}")
            print("   ./raspberry-pi-scripts/start-preview-stream.sh\n")
            
            response = input("Fortfahren ohne Stream? (j/N): ")
            if response.lower() != 'j':
                sys.exit(1)
    else:
        print("⚠️  StreamProcessor nicht verfügbar - Fallback-Modus")
        print("   Installiere Dependencies für echte Erkennung:")
        print("   pip install opencv-python opencv-contrib-python ultralytics\n")
    
    # Zeige initialen System-Status
    print_status_report()
    
    # Starte Ressourcen-Monitor in separatem Thread
    monitor_thread = threading.Thread(target=resource_monitor, daemon=True)
    monitor_thread.start()
    
    # Starte Monitoring-Loop
    try:
        monitoring_loop()
    except KeyboardInterrupt:
        shutdown()

if __name__ == '__main__':
    main()
