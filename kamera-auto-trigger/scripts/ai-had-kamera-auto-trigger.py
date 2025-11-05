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

# Unterdrücke FFmpeg/H.264 stderr Ausgaben (MUSS VOR allen Imports sein!)
import sys
import os

class H264ErrorFilter:
    """Filter für stderr der H.264-Dekodierungsfehler ausfiltert"""
    def __init__(self, stream):
        self.stream = stream
        self.buffer = []
        
    def write(self, text):
        # Filtere H.264/FFmpeg-Fehler und -Warnungen
        filtered_patterns = [
            '[h264',
            'error while decoding',
            'corrupted macroblock',
            'negative number of zero',
            'cbp too large',
            'left block unavailable',
            'Invalid level prefix',
            'reference picture missing',
            'concealing',
        ]
        
        text_lower = text.lower()
        should_filter = any(pattern.lower() in text_lower for pattern in filtered_patterns)
        
        if not should_filter and text.strip():  # Nur nicht-leere, nicht-gefilterte Zeilen
            self.stream.write(text)
            
    def flush(self):
        self.stream.flush()

# Ersetze stderr durch gefilterte Version
sys.stderr = H264ErrorFilter(sys.stderr)

# CPU-Optimierung: Begrenze Thread-Nutzung für AI-Inferenz
os.environ['OMP_NUM_THREADS'] = '2'  # OpenMP auf 2 Threads begrenzen
os.environ['OPENBLAS_NUM_THREADS'] = '2'  # OpenBLAS auf 2 Threads begrenzen
os.environ['MKL_NUM_THREADS'] = '2'  # Intel MKL auf 2 Threads begrenzen

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
__version__ = "1.3.1"  # Trixie Release - TCP Stream mit Watchdog, Bookworm-Logik

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

# Tracking für anhaltende Last-Probleme
high_load_start_time = None  # Zeitpunkt, wann Last-Problem begann
high_load_host = None  # 'local' oder 'remote'

# Argumente parsen
parser = argparse.ArgumentParser(
    description='''🐦 Vogel-Kamera Auto-Trigger mit AI-Objekterkennung
    
    Überwacht kontinuierlich das Vogelhaus und startet automatisch HD-Aufnahmen,
    wenn ein Vogel erkannt wird. Die Erkennung erfolgt IMMER mit KI, aber die
    Aufnahme kann mit oder ohne KI-Modul erfolgen.
    
    Beispiele:
    # Standard: Trigger MIT KI, Aufnahme OHNE KI (schneller)
    python ai-had-kamera-auto-trigger.py --trigger-duration 2 --ai-model bird-species
    
    # Trigger UND Aufnahme mit KI (Objekterkennung während Aufnahme)
    python ai-had-kamera-auto-trigger.py --trigger-duration 2 --recording-ai --recording-ai-model bird-species
    
    # Mit Custom-Einstellungen
    python ai-had-kamera-auto-trigger.py --trigger-duration 3 --cooldown 60 --trigger-threshold 0.5
    
    Beenden: Strg+C für sauberen Shutdown''',
    formatter_class=argparse.RawDescriptionHelpFormatter
)

parser.add_argument('--version', action='version', version=f'Vogel-Kamera-Linux Auto-Trigger v{__version__}')
parser.add_argument('--trigger-duration', type=int, default=2, help='Aufnahmedauer bei Vogel-Erkennung in Minuten (default: 2)')
parser.add_argument('--ai-model', type=str, default='bird-species', choices=['yolov8', 'bird-species', 'custom'], 
                    help='AI-Modell für Vogel-Erkennung (default: bird-species)')
parser.add_argument('--ai-model-path', type=str, help='Pfad zu benutzerdefiniertem AI-Modell (für --ai-model custom)')
parser.add_argument('--recording-ai', action='store_true', 
                    help='Aufnahme mit KI-Modul (Objekterkennung während Aufnahme). Default: Ohne KI (nur Trigger nutzt KI)')
parser.add_argument('--recording-ai-model', type=str, default='bird-species', choices=['yolov8', 'bird-species', 'custom'],
                    help='AI-Modell für Aufnahme (nur mit --recording-ai, default: bird-species)')
parser.add_argument('--recording-slowmo', action='store_true',
                    help='Zeitlupen-Aufnahme (120fps, 1536x864). Überschreibt --recording-ai und Auflösungsparameter')
parser.add_argument('--cooldown', type=int, default=30, help='Wartezeit zwischen Aufnahmen in Sekunden (default: 30)')
parser.add_argument('--trigger-threshold', type=float, default=0.25, help='AI-Schwelle für Trigger (default: 0.25, optimiert für Vogelerkennung)')
parser.add_argument('--preview-fps', type=int, default=5, help='FPS für Monitoring-Modus (default: 5, CPU-optimierter Kompromiss)')
parser.add_argument('--preview-width', type=int, default=640, help='Breite für Monitoring-Vorschau (default: 640, CPU-optimierter Kompromiss)')
parser.add_argument('--preview-height', type=int, default=480, help='Höhe für Monitoring-Vorschau (default: 480, CPU-optimierter Kompromiss)')
parser.add_argument('--max-cpu-temp', type=float, default=70.0, help='Maximale CPU-Temperatur in °C (default: 70)')
parser.add_argument('--max-cpu-load', type=float, default=5.0, help='Maximale CPU-Load (default: 5.0)')
parser.add_argument('--max-cpu-load-duration', type=int, default=300, help='CPU-Load muss für X Sekunden über Schwelle sein (default: 300s = 5min)')
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

# Bestimme Aufnahme-Modus (Priorität: Zeitlupe > AI > Standard)
if args.recording_slowmo:
    recording_mode = "🎬 Zeitlupe (120fps, OHNE Audio)"
    recording_model = ""
elif args.recording_ai:
    recording_mode = "🤖 Mit KI + Audio"
    recording_model = f" ({args.recording_ai_model})"
else:
    recording_mode = "📹 Ohne KI (Video + Audio)"
    recording_model = ""

print(f"""
╔══════════════════════════════════════════════════════════════╗
  🐦 Vogel-Kamera Auto-Trigger v{__version__}
╠══════════════════════════════════════════════════════════════╣
  Modus: Automatische Vogel-Erkennung
  Trigger-KI: {args.ai_model}
  Aufnahme-Modus: {recording_mode}{recording_model}
  Trigger-Dauer: {args.trigger_duration} Sekunden (Vogel muss konsistent erkannt werden)
  Aufnahme-Länge: 1 Minute
  Cooldown: {args.cooldown} Sekunden
  Schwelle: {args.trigger_threshold}
╚══════════════════════════════════════════════════════════════╝
""")

def get_local_system_status():
    """Hole System-Status vom lokalen Host"""
    try:
        # CPU-Temperatur (vcgencmd oder /sys/class/thermal)
        temp_val = None
        try:
            result = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                temp_output = result.stdout.strip()
                temp_val = float(temp_output.replace("temp=", "").replace("'C", "").replace("°C", ""))
        except:
            # Fallback: /sys/class/thermal
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp_millidegrees = int(f.read().strip())
                    temp_val = temp_millidegrees / 1000.0
            except:
                pass
        
        # CPU Load
        result = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
        uptime_output = result.stdout.strip()
        load_1min = 0.0
        if "load average:" in uptime_output:
            load_1min = float(uptime_output.split("load average:")[1].split(',')[0].strip().replace(',', '.'))
        
        # Festplatte
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        disk_output = result.stdout.strip()
        disk_lines = disk_output.splitlines()
        used_percent = 0
        if len(disk_lines) > 1:
            disk_parts = disk_lines[1].split()
            used_percent = int(disk_parts[4].replace('%', '')) if len(disk_parts) >= 5 else 0
        
        # Memory
        result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        mem_output = result.stdout.strip()
        mem_parts = []
        for line in mem_output.splitlines():
            if "Mem:" in line or "Speicher:" in line:
                mem_parts = line.split()
                break
        mem_used = mem_parts[2] if len(mem_parts) >= 3 else "N/A"
        mem_total = mem_parts[1] if len(mem_parts) >= 2 else "N/A"
        
        return {
            'temp': temp_val,
            'load': load_1min,
            'disk_percent': used_percent,
            'mem_used': mem_used,
            'mem_total': mem_total,
            'healthy': (temp_val is None or temp_val < args.max_cpu_temp) and load_1min < args.max_cpu_load
        }
    
    except Exception as e:
        print(f"⚠️ Fehler beim Abrufen des lokalen System-Status: {e}")
        return None

def get_system_status():
    """Hole System-Status vom Remote-Host"""
    ssh = None
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
        
        return {
            'temp': temp_val,
            'load': load_1min,
            'disk_percent': used_percent,
            'mem_used': mem_used,
            'mem_total': mem_total,
            'healthy': temp_val < args.max_cpu_temp and load_1min < args.max_cpu_load
        }
    
    except Exception as e:
        # Detailliertere Fehlerausgabe mit Fehlertyp
        error_type = type(e).__name__
        print(f"⚠️ Fehler beim Abrufen des System-Status ({error_type}): {e}")
        return None
    
    finally:
        # Stelle sicher, dass SSH-Verbindung immer geschlossen wird
        if ssh is not None:
            try:
                ssh.close()
            except:
                pass

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
    print(f"\n🎬 TRIGGER! Starte 1-minütige Aufnahme...")
    print(f"   Zeitstempel: {timestamp}")
    print(f"   ⏸️  Status-Reports pausiert während Aufnahme")
    
    try:
        # Wähle das richtige Recording-Skript basierend auf Modus (Priorität: Zeitlupe > AI > Standard)
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        if args.recording_slowmo:
            # ZEITLUPE: Nutze Zeitlupen-Skript (120fps, 1536x864)
            print(f"   🎬 Modus: Zeitlupen-Aufnahme (120fps, 1536x864)")
            
            recording_script = os.path.join(script_dir, 'python-skripte', 'ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py')
            
            cmd = [
                'python3',
                recording_script,
                '--duration', '1',  # 1 Minute (Script multipliziert mit 60)
                '--width', '1536',  # Zeitlupe: feste Auflösung für Performance
                '--height', '864',
                '--fps', '120',     # Zeitlupe: 120fps
                '--rotation', str(args.rotation),
                '--cam', str(args.cam),
                '--slowmotion'      # Aktiviere Zeitlupen-Flag
            ]
        else:
            # Standard oder AI: Nutze AI-Modul-Skript
            recording_script = os.path.join(script_dir, 'python-skripte', 'ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py')
            
            if args.recording_ai:
                # MIT KI: Objekterkennung während Aufnahme
                print(f"   🤖 Modus: Aufnahme MIT KI ({args.recording_ai_model})")
                
                cmd = [
                    'python3',
                    recording_script,
                    '--duration', str(args.trigger_duration),
                    '--width', str(args.width),
                    '--height', str(args.height),
                    '--rotation', str(args.rotation),
                    '--cam', str(args.cam),
                    '--ai-modul', 'on',
                    '--ai-model', args.recording_ai_model,
                    '--no-stream-restart'  # Auto-Trigger managed Stream-Neustart selbst
                ]
                
                if args.recording_ai_model == 'custom' and args.ai_model_path:
                    cmd.extend(['--ai-model-path', args.ai_model_path])
            else:
                # OHNE KI: Nur Video-Aufnahme (schneller, weniger CPU-Last)
                print(f"   📹 Modus: Aufnahme OHNE KI (nur Video)")
                
                cmd = [
                    'python3',
                    recording_script,
                    '--duration', '1',  # 1 Minute (Script multipliziert mit 60)
                    '--width', str(args.width),
                    '--height', str(args.height),
                    '--rotation', str(args.rotation),
                    '--cam', str(args.cam),
                    '--ai-modul', 'off',  # KI deaktiviert = nur Video
                    '--no-stream-restart'  # Auto-Trigger managed Stream-Neustart selbst
                ]
        
        # Stoppe TCP Watchdog vor Aufnahme (gibt Kamera frei)
        print("   ⏸️  Stoppe TCP Watchdog (Kamera wird exklusiv für Aufnahme)...")
        try:
            ssh_stop = paramiko.SSHClient()
            ssh_stop.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_stop.connect(
                hostname=remote_host['hostname'],
                username=remote_host['username'],
                key_filename=remote_host['key_filename']
            )
            stdin, stdout, stderr = ssh_stop.exec_command('cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-tcp-preview-watchdog.sh --stop')
            stdout.channel.recv_exit_status()
            ssh_stop.close()
            time.sleep(2)  # Warte bis Kamera freigegeben ist
            print("   ✅ Watchdog gestoppt, Kamera freigegeben")
        except Exception as e:
            print(f"   ⚠️  Konnte Watchdog nicht stoppen: {e}")
        
        # Führe Aufnahme-Skript aus (stdout/stderr nicht capturen für tqdm-Progressbar)
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        # Starte TCP Watchdog nach Aufnahme wieder
        print(f"   🔄 Starte TCP Watchdog neu...")
        try:
            ssh_start = paramiko.SSHClient()
            ssh_start.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_start.connect(
                hostname=remote_host['hostname'],
                username=remote_host['username'],
                key_filename=remote_host['key_filename']
            )
            stdin, stdout, stderr = ssh_start.exec_command(
                f'cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-tcp-preview-watchdog.sh --port 8554 --width {args.preview_width} --height {args.preview_height} --fps {args.preview_fps} --camera {args.cam}'
            )
            stdout.channel.recv_exit_status()
            ssh_start.close()
            
            # Warte bis Stream bereit ist (Watchdog braucht Zeit zum Starten)
            print(f"   ⏳ Warte auf Stream-Verfügbarkeit (20 Sekunden)...")
            time.sleep(20)
            print(f"   ✅ Watchdog läuft wieder (Stream bereit)")
        except Exception as e:
            print(f"   ⚠️  Konnte Watchdog nicht starten: {e}")
        
        if result.returncode == 0:
            trigger_count += 1
            last_trigger_time = datetime.now()
            print(f"✅ Aufnahme #{trigger_count} erfolgreich abgeschlossen")
        else:
            print(f"❌ Fehler bei Aufnahme: Exit Code {result}")
        
        # Preview-Stream läuft weiter (andere Kamera) - kein Neustart nötig
        # Nur Cooldown-Phase
        print(f"   ⏳ Cooldown: {args.cooldown} Sekunden (keine weiteren Trigger)...")
        time.sleep(args.cooldown)
        
        # Setze Status-Reports fort nach Cooldown
        monitoring_paused = False
        print("   ▶️  Status-Reports wieder aktiv - Überwachung läuft\n")
    
    except Exception as e:
        print(f"❌ Fehler beim Triggern der Aufnahme: {e}")
        # Preview-Stream läuft weiter (andere Kamera) - kein Recovery nötig
        monitoring_paused = False
        
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
    local_status = get_local_system_status()
    
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
    
    # Lokaler Host Status
    if local_status:
        print(f"\n💻 Localhost:")
        
        if local_status['temp'] is not None:
            temp_status = "🟢" if local_status['temp'] < 50 else "🟡" if local_status['temp'] < 60 else "🔴"
            print(f"   🌡️  CPU-Temp: {local_status['temp']:.1f}°C {temp_status}")
        
        load_status = "🟢" if local_status['load'] < 1.0 else "🟡" if local_status['load'] < 2.0 else "🔴"
        disk_status = "🟢" if local_status['disk_percent'] < 80 else "🟡" if local_status['disk_percent'] < 90 else "🔴"
        
        print(f"   ⚡ CPU-Load: {local_status['load']:.2f} {load_status}")
        print(f"   💾 Festplatte: {local_status['disk_percent']}% belegt {disk_status}")
        print(f"   💭 RAM: {local_status['mem_used']} / {local_status['mem_total']}")
    
    # Remote-Host Status
    if status:
        temp_status = "🟢" if status['temp'] < 50 else "🟡" if status['temp'] < 60 else "🔴"
        load_status = "🟢" if status['load'] < 1.0 else "🟡" if status['load'] < 2.0 else "🔴"
        disk_status = "🟢" if status['disk_percent'] < 80 else "🟡" if status['disk_percent'] < 90 else "🔴"
        
        print(f"\n🖥️  Remote-Host ({remote_host['hostname']}):")
        print(f"   🌡️  CPU-Temp: {status['temp']:.1f}°C {temp_status}")
        print(f"   ⚡ CPU-Load: {status['load']:.2f} {load_status}")
        print(f"   💾 Festplatte: {status['disk_percent']}% belegt {disk_status}")
        print(f"   💭 RAM: {status['mem_used']} / {status['mem_total']}")
        
        if not status['healthy'] or (local_status and not local_status['healthy']):
            print(f"\n⚠️  WARNUNG: System-Ressourcen kritisch!")
    
    print(f"{'='*70}\n")

def resource_monitor():
    """Überwache System-Ressourcen mit zeitlicher Toleranz für Last-Spitzen"""
    global running, monitoring_paused, high_load_start_time, high_load_host
    
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
            
            # Prüfe System-Status (Remote & Local)
            status = get_system_status()
            local_status = get_local_system_status()
            
            # Prüfe Remote-Host mit zeitlicher Toleranz
            remote_critical = False
            if status:
                # Temperatur: Sofortiges Beenden (keine Toleranz)
                if status['temp'] >= args.max_cpu_temp:
                    print(f"\n🚨 KRITISCH: Remote-Host CPU-Temperatur zu hoch!")
                    print(f"   🖥️  Host: {remote_host['hostname']}")
                    print(f"   🌡️  CPU-Temp: {status['temp']:.1f}°C (Max: {args.max_cpu_temp}°C)")
                    print(f"\n⛔ Beende Auto-Trigger aus Sicherheitsgründen...")
                    shutdown()
                    break
                
                # Load: Zeitliche Toleranz (muss anhaltend sein)
                if status['load'] >= args.max_cpu_load:
                    if high_load_start_time is None or high_load_host != 'remote':
                        # Erste Erkennung der hohen Last
                        high_load_start_time = datetime.now()
                        high_load_host = 'remote'
                        print(f"\n⚠️  WARNUNG: Remote-Host hohe CPU-Last erkannt")
                        print(f"   ⚡ CPU-Load: {status['load']:.2f} (Max: {args.max_cpu_load})")
                        print(f"   ⏱️  Toleranz: {args.max_cpu_load_duration}s (beende wenn anhaltend)")
                    else:
                        # Prüfe ob Last schon zu lange anhält
                        duration = (datetime.now() - high_load_start_time).total_seconds()
                        if duration >= args.max_cpu_load_duration:
                            print(f"\n🚨 KRITISCH: Remote-Host CPU-Last anhaltend zu hoch!")
                            print(f"   🖥️  Host: {remote_host['hostname']}")
                            print(f"   ⚡ CPU-Load: {status['load']:.2f} (Max: {args.max_cpu_load})")
                            print(f"   ⏱️  Dauer: {int(duration)}s (Max: {args.max_cpu_load_duration}s)")
                            print(f"\n⛔ Beende Auto-Trigger aus Sicherheitsgründen...")
                            shutdown()
                            break
                        else:
                            # Noch in Toleranz-Phase
                            remaining = args.max_cpu_load_duration - int(duration)
                            print(f"   ⏳ Hohe Last seit {int(duration)}s (beende in {remaining}s wenn anhaltend)")
                else:
                    # Last wieder normal - reset Timer
                    if high_load_start_time is not None and high_load_host == 'remote':
                        duration = (datetime.now() - high_load_start_time).total_seconds()
                        print(f"\n✅ Remote-Host CPU-Last wieder normal (war {int(duration)}s erhöht)")
                        high_load_start_time = None
                        high_load_host = None
            
            # Prüfe Localhost mit zeitlicher Toleranz
            if local_status:
                # Temperatur: Sofortiges Beenden (keine Toleranz)
                if local_status['temp'] is not None and local_status['temp'] >= args.max_cpu_temp:
                    print(f"\n🚨 KRITISCH: Localhost CPU-Temperatur zu hoch!")
                    print(f"   🌡️  CPU-Temp: {local_status['temp']:.1f}°C (Max: {args.max_cpu_temp}°C)")
                    print(f"\n⛔ Beende Auto-Trigger aus Sicherheitsgründen...")
                    shutdown()
                    break
                
                # Load: Zeitliche Toleranz (muss anhaltend sein)
                if local_status['load'] >= args.max_cpu_load:
                    if high_load_start_time is None or high_load_host != 'local':
                        # Erste Erkennung der hohen Last
                        high_load_start_time = datetime.now()
                        high_load_host = 'local'
                        print(f"\n⚠️  WARNUNG: Localhost hohe CPU-Last erkannt")
                        print(f"   ⚡ CPU-Load: {local_status['load']:.2f} (Max: {args.max_cpu_load})")
                        print(f"   ⏱️  Toleranz: {args.max_cpu_load_duration}s (beende wenn anhaltend)")
                    else:
                        # Prüfe ob Last schon zu lange anhält
                        duration = (datetime.now() - high_load_start_time).total_seconds()
                        if duration >= args.max_cpu_load_duration:
                            print(f"\n🚨 KRITISCH: Localhost CPU-Last anhaltend zu hoch!")
                            print(f"   ⚡ CPU-Load: {local_status['load']:.2f} (Max: {args.max_cpu_load})")
                            print(f"   ⏱️  Dauer: {int(duration)}s (Max: {args.max_cpu_load_duration}s)")
                            print(f"\n⛔ Beende Auto-Trigger aus Sicherheitsgründen...")
                            shutdown()
                            break
                        else:
                            # Noch in Toleranz-Phase
                            remaining = args.max_cpu_load_duration - int(duration)
                            print(f"   ⏳ Hohe Last seit {int(duration)}s (beende in {remaining}s wenn anhaltend)")
                else:
                    # Last wieder normal - reset Timer
                    if high_load_start_time is not None and high_load_host == 'local':
                        duration = (datetime.now() - high_load_start_time).total_seconds()
                        print(f"\n✅ Localhost CPU-Last wieder normal (war {int(duration)}s erhöht)")
                        high_load_start_time = None
                        high_load_host = None
            
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
    
    # Beende TCP Watchdog (NICHT MediaMTX starten - bleibt deaktiviert)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], 
                   key_filename=remote_host['key_filename'], timeout=10)
        
        # Cleanup: Stoppe Watchdog (beendet auch Stream)
        print("   ⏸️  Stoppe TCP Watchdog...")
        stdin, stdout, stderr = ssh.exec_command('cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-tcp-preview-watchdog.sh --stop')
        stdout.channel.recv_exit_status()
        
        ssh.close()
        print("✅ TCP Watchdog gestoppt")
    except Exception as e:
        print(f"⚠️ Fehler beim Watchdog-Cleanup: {e}")
    
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
    
    # Starte TCP Preview Watchdog
    print("🔄 Prüfe TCP Preview Watchdog...")
    try:
        ssh_ctrl = paramiko.SSHClient()
        ssh_ctrl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_ctrl.connect(
            hostname=remote_host['hostname'],
            username=remote_host['username'],
            key_filename=remote_host['key_filename']
        )
        
        # Prüfe ob Watchdog bereits läuft
        stdin, stdout, stderr = ssh_ctrl.exec_command(
            'cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-tcp-preview-watchdog.sh --status'
        )
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            # Watchdog läuft bereits
            print("   ✅ Watchdog läuft bereits")
            print("   ⏳ Gebe Stream 5s Zeit zum Stabilisieren...")
            time.sleep(5)
            print("   ✅ Stream sollte bereit sein\n")
        else:
            # Starte Watchdog neu
            print("   🔄 Starte Watchdog...")
            stdin, stdout, stderr = ssh_ctrl.exec_command(
                f'cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-tcp-preview-watchdog.sh --port 8554 --width {args.preview_width} --height {args.preview_height} --fps {args.preview_fps} --camera {args.cam}'
            )
            stdout.channel.recv_exit_status()
            
            print("   ✅ Watchdog gestartet")
            print("   ⏳ Warte auf Stream-Initialisierung...")
            time.sleep(20)  # Watchdog braucht ~3s + rpicam-vid Start ~10s + Socket-Stabilisierung + Reserve
            print("   ✅ Stream sollte bereit sein\n")
        
        ssh_ctrl.close()
    except Exception as e:
        print(f"   ⚠️  Watchdog-Verwaltung fehlgeschlagen: {e}\n")
    
    # Initialisiere StreamProcessor wenn verfügbar
    if HAS_STREAM_PROCESSOR:
        print("🎬 Initialisiere Stream-Verarbeitung...")
        stream_processor = StreamProcessor(
            host=remote_host['hostname'],
            port=8554,  # TCP Port
            model_type=args.ai_model,
            model_path=args.ai_model_path,
            threshold=args.trigger_threshold,
            width=args.preview_width,
            height=args.preview_height,
            fps=args.preview_fps,
            trigger_duration=1.5,  # Vogel muss 1.5 Sekunden erkannt werden (mehr Frames für bessere Konsistenz)
            debug=True  # Aktiviere Debug-Ausgaben um Erkennungen zu sehen
        )
        
        # Verbinde mit TCP Preview-Stream
        print(f"📡 Verbinde mit Preview-Stream: tcp://{remote_host['hostname']}:8554...")
        if stream_processor.connect():
            print("✅ Preview-Stream verbunden")
            print(f"   AI-Model: {args.ai_model}")
            print(f"   Threshold: {args.trigger_threshold}")
            print(f"   Trigger-Dauer: 1.0s (Vogel muss konsistent erkannt werden)")
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
