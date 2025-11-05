# -*- coding: utf-8 -*-
import paramiko
from scp import SCPClient
from datetime import datetime
import locale
import threading
import time
import subprocess
import os
import signal
import argparse
from tqdm import tqdm
from config import config
from __version__ import __version__, get_version_info

# Setze die Locale auf Deutsch
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

# Argumente parsen
parser = argparse.ArgumentParser(
    description='''Vogelhaus Remote Steuerung mit AI-Objekterkennung
    
    Beispiele für Aufrufe:
    # Standard YOLOv8 (allgemeine Objekterkennung)
    python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py --duration 3 --ai-modul on --ai-model yolov8
    
    # Vogelarten-spezifisches Modell (falls verfügbar)
    python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py --duration 3 --ai-modul on --ai-model bird-species
    
    # Benutzerdefiniertes Modell
    python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py --duration 3 --ai-modul on --ai-model custom --ai-model-path /path/to/model.json
    
    Für Details siehe: AI-MODELLE-VOGELARTEN.md'''
)
parser.add_argument('--version', action='version', version=f'Vogel-Kamera-Linux v{__version__}')
parser.add_argument('--duration', type=int, required=True, help='Aufnahmedauer in Minuten')
parser.add_argument('--width', type=int, default=4096, help='Breite des Videos (default: 4096)')
parser.add_argument('--height', type=int, default=2160, help='Höhe des Videos (default: 2160)')
parser.add_argument('--codec', type=str, default='h264', help='Codec für das Video (default: h264)')
parser.add_argument('--autofocus_mode', type=str, default='continuous', help='Autofokus-Modus (default: continuous)')
parser.add_argument('--autofocus_range', type=str, default='macro', help='Autofokus-Bereich (default: full)')
parser.add_argument('--hdr', type=str, choices=['auto', 'off'], default='off', help='HDR-Modus (default: auto)')
parser.add_argument('--roi', type=str, help='Region of Interest im Format x,y,w,h (optional)')
parser.add_argument('--rotation', type=int, choices=[0, 90, 180, 270], default=180, help='Rotation des Videos (default: 0)')
parser.add_argument('--fps', type=int, default=15, help='Framerate für Video und Audio (default: 15)')
parser.add_argument('--cam', type=int, default=0, choices=[0, 1], help='Kamera-ID (default: 0)')
parser.add_argument('--ai-modul', choices=['on', 'off'], default='off', help='KI-Objekterkennung aktivieren (default: off)')
parser.add_argument('--ai-model', type=str, default='yolov8', choices=['yolov8', 'bird-species', 'custom'], help='AI-Modell für Objekterkennung (default: yolov8)')
parser.add_argument('--ai-model-path', type=str, help='Pfad zu benutzerdefiniertem AI-Modell (für --ai-model custom)')
parser.add_argument('--system-status', action='store_true', help='Zeige nur System-Status ohne Aufnahme')
parser.add_argument('--no-stream-restart', action='store_true', help='Preview-Stream nicht automatisch neu starten (sinnvoll für On-Demand Aufnahmen, unnötig ohne Auto-Trigger)')
args = parser.parse_args()

# Erzeuge den Zeitstempel mit deutschem Wochentag
timestamp = datetime.now().strftime("%A__%Y-%m-%d__%H-%M-%S")
year = datetime.now().year
week_number = datetime.now().isocalendar()[1]  # Wochennummer des aktuellen Datums

# SSH-Verbindungsdetails für den Remote-Host (aus Konfiguration)
remote_host = config.get_remote_host_config()

# Konfiguration validieren
config_errors = config.validate_config()
if config_errors:
    print("⚠️ Konfigurationsprobleme gefunden:")
    for error in config_errors:
        print(f"  - {error}")
    print("\nBitte konfigurieren Sie das System entsprechend der README.md")
    print("Kopieren Sie .env.example zu .env und passen Sie die Werte an.")
    exit(1)

# Definiere den Pfad (aus Konfiguration)
base_path = config.get_video_path(year, week_number, timestamp, "AI-HAD")

# Erstelle das Verzeichnis, falls es nicht existiert
os.makedirs(base_path, exist_ok=True)

# Aufnahmezeit in Sekunden
recording_duration_s = args.duration * 60

# Funktion zum Ermitteln des aktiven USB-Audio-Geräts auf dem Remote-Host
def get_usb_audio_device_remote():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])

        # Führe arecord -l auf dem Remote-Host aus
        stdin, stdout, stderr = ssh.exec_command("arecord -l")
        output = stdout.read().decode()
        ssh.close()

        # Debugging: Ausgabe von arecord -l anzeigen
        print("Debug: Ausgabe von 'arecord -l' auf dem Remote-Host:")
        print(output)

        # Suche nach einem Gerät mit "USB" im Namen
        for line in output.splitlines():
            if "USB" in line:
                # Extrahiere die Karte und das Subgerät (z. B. hw:0,0)
                parts = line.split()
                card_index = parts[1].replace(":", "")  # Karte
                subdevice_index = "0"  # Standard-Subgerät
                return f"hw:{card_index},{subdevice_index}"

        # Falls kein USB-Gerät gefunden wurde, None zurückgeben
        return None
    except Exception as e:
        print(f"Fehler beim Ermitteln des USB-Audio-Geräts auf dem Remote-Host: {e}")
        return None

# Funktion zum Beenden aller Prozesse auf dem Remote-Host
def kill_remote_processes():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        # Beende alle relevanten Prozesse (inkl. Preview-Stream)
        # WICHTIG: Stoppe stream-wrapper.sh ZUERST (verhindert Auto-Restart von rpicam-vid)
        ssh.exec_command("pkill -9 -f stream-wrapper.sh")
        ssh.exec_command("pkill -9 -f rpicam-vid")
        ssh.exec_command("pkill -f libcamera-vid")
        ssh.exec_command("pkill -f ffmpeg")
        # Lösche PID-Files für sauberen Neustart
        ssh.exec_command("rm -f /tmp/rtsp-stream.pid /tmp/*.pid")
        ssh.close()
        print("✅ Alle relevanten Prozesse auf dem Remote-Host wurden beendet.")
        print("   (inkl. Preview-Stream für exklusiven Kamera-Zugriff)")
    except Exception as e:
        print(f"Fehler beim Beenden der Prozesse auf dem Remote-Host: {e}")

# Ermitteln des aktiven USB-Audio-Geräts (optional)
audio_device = get_usb_audio_device_remote()
if not audio_device:
    print("⚠️  Kein USB-Audio-Gerät auf dem Remote-Host gefunden.")
    print("ℹ️  Aufnahme wird OHNE Audio fortgesetzt (nur Video).")
else:
    print(f"Verwendetes Audio-Gerät auf dem Remote-Host: {audio_device}")

# Funktion zur Überprüfung der Modell-Verfügbarkeit auf Remote-Host
def check_ai_model_availability():
    """Prüfe verfügbare AI-Modelle auf dem Remote-Host"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        # Prüfe verfügbare Modell-Dateien
        stdin, stdout, stderr = ssh.exec_command("ls /usr/share/rpi-camera-assets/hailo_*_inference.json")
        available_models = stdout.read().decode().strip().split('\n')
        ssh.close()
        
        return [model.split('/')[-1].replace('hailo_', '').replace('_inference.json', '') for model in available_models if model]
    except Exception as e:
        print(f"⚠️ Fehler beim Prüfen der Modell-Verfügbarkeit: {e}")
        return ['yolov8']  # Fallback

def get_remote_system_status():
    """Zeige System-Status vom Remote-Host mit Load-Berücksichtigung"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        # CPU-Temperatur
        stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
        temp_output = stdout.read().decode().strip()
        
        # Festplattenbelegung (nur Root-Partition)
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1")
        disk_output = stdout.read().decode().strip()
        
        # Memory
        stdin, stdout, stderr = ssh.exec_command("free -h | grep 'Speicher\\|Mem'")
        mem_output = stdout.read().decode().strip()
        
        # CPU Load und Uptime
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        
        ssh.close()
        
        # Parse und formatiere Output
        temp = temp_output.replace("temp=", "").replace("'C", "°C")
        temp_val = float(temp.replace("°C", "")) if temp.replace("°C", "").replace(".", "").isdigit() else 0
        temp_status = "🟢" if temp_val < 50 else "🟡" if temp_val < 60 else "🔴"
        
        disk_parts = disk_output.split()
        if len(disk_parts) >= 5:
            used_percent = int(disk_parts[4].replace('%', ''))
            disk_status = "🟢" if used_percent < 80 else "🟡" if used_percent < 90 else "🔴"
            disk_info = f"{disk_parts[2]} / {disk_parts[1]} ({disk_parts[4]} belegt) {disk_status}"
        else:
            disk_info = "Nicht verfügbar"
        
        mem_parts = mem_output.split()
        mem_info = f"{mem_parts[2]} / {mem_parts[1]} verwendet" if len(mem_parts) >= 3 else "Nicht verfügbar"
        
        # Parse Load Average
        load_info = "Nicht verfügbar"
        if "load average:" in uptime_output:
            load_part = uptime_output.split("load average:")[1].strip()
            load_1min = float(load_part.split(',')[0].strip().replace(',', '.'))
            load_status = "🟢" if load_1min < 1.0 else "🟡" if load_1min < 2.0 else "🔴"
            load_info = f"{load_1min:.2f} (1min) {load_status}"
        
        print(f"🖥️ Remote-Host Status ({remote_host['hostname']}):")
        print(f"   🌡️ CPU-Temperatur: {temp} {temp_status}")
        print(f"   💾 Festplatte: {disk_info}")
        print(f"   💭 Arbeitsspeicher: {mem_info}")
        print(f"   ⚡ CPU-Last: {load_info}")
        
        # Warnung bei hoher Load während Videoaufnahme
        if "load average:" in uptime_output:
            load_1min = float(uptime_output.split("load average:")[1].split(',')[0].strip().replace(',', '.'))
            if load_1min > 2.0:
                print(f"   ⚠️  WARNUNG: Hohe CPU-Last ({load_1min:.2f}) - Videoqualität könnte beeinträchtigt werden!")
            elif load_1min > 1.0:
                print(f"   💡 Moderate CPU-Last ({load_1min:.2f}) - System unter Last")
        
    except Exception as e:
        print(f"⚠️ Fehler beim Abrufen des System-Status: {e}")

def check_system_readiness():
    """Prüfe ob System bereit für Videoaufnahme ist"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        # CPU-Temperatur prüfen
        stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
        temp_output = stdout.read().decode().strip()
        temp_val = float(temp_output.replace("temp=", "").replace("'C", ""))
        
        # Load prüfen
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        load_1min = 0.0
        if "load average:" in uptime_output:
            load_1min = float(uptime_output.split("load average:")[1].split(',')[0].strip().replace(',', '.'))
        
        # Festplatte prüfen
        stdin, stdout, stderr = ssh.exec_command("df / | tail -1")
        disk_output = stdout.read().decode().strip()
        disk_parts = disk_output.split()
        used_percent = int(disk_parts[4].replace('%', '')) if len(disk_parts) >= 5 else 0
        
        ssh.close()
        
        # Bewertung
        issues = []
        if temp_val > 70:
            issues.append(f"🔴 CPU-Temperatur kritisch: {temp_val}°C")
        elif temp_val > 60:
            issues.append(f"🟡 CPU-Temperatur hoch: {temp_val}°C")
        
        if load_1min > 3.0:
            issues.append(f"🔴 CPU-Last kritisch: {load_1min:.2f}")
        elif load_1min > 2.0:
            issues.append(f"🟡 CPU-Last hoch: {load_1min:.2f}")
        
        if used_percent > 95:
            issues.append(f"🔴 Festplatte fast voll: {used_percent}%")
        elif used_percent > 90:
            issues.append(f"🟡 Festplatte wird knapp: {used_percent}%")
        
        if issues:
            print("⚠️  System-Warnungen vor Aufnahme:")
            for issue in issues:
                print(f"   {issue}")
            
            if any("🔴" in issue for issue in issues):
                print("❌ KRITISCH: Aufnahme nicht empfohlen!")
                return False
            else:
                print("⚡ Aufnahme möglich, aber mit Vorsicht")
                return True
        else:
            print("✅ System bereit für Videoaufnahme")
            return True
    
    except Exception as e:
        print(f"⚠️ Fehler bei System-Bereitschaftsprüfung: {e}")
        return True  # Im Zweifel erlauben

# Befehl zum Ausführen auf dem Remote-Host (Video- und Audioaufnahme)
def get_ai_model_path():
    """Bestimme den Pfad zum AI-Modell basierend auf der Auswahl mit Verfügbarkeits-Check"""
    if getattr(args, 'ai_modul') == 'off':
        return ""
    
    model_paths = {
        'yolov8': '/usr/share/rpi-camera-assets/hailo_yolov8_inference.json',
        'bird-species': '/usr/share/rpi-camera-assets/hailo_bird_species_inference.json',
        'custom': args.ai_model_path
    }
    
    model_path = model_paths.get(args.ai_model)
    
    # Spezielle Behandlung für bird-species
    if args.ai_model == 'bird-species':
        # Prüfe ob bird-species Modell existiert
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
            
            stdin, stdout, stderr = ssh.exec_command("test -f /usr/share/rpi-camera-assets/hailo_bird_species_inference.json && echo 'exists'")
            result = stdout.read().decode().strip()
            ssh.close()
            
            if result != 'exists':
                print("⚠️ bird-species Modell nicht gefunden! Erstelle temporäres Modell...")
                create_bird_species_model()
                
        except Exception as e:
            print(f"⚠️ Fehler beim Prüfen des bird-species Modells: {e}")
            print("🔄 Fallback zu YOLOv8...")
            model_path = '/usr/share/rpi-camera-assets/hailo_yolov8_inference.json'
    
    if args.ai_model == 'custom' and not args.ai_model_path:
        print("⚠️ Für --ai-model custom muss --ai-model-path angegeben werden!")
        return ""
    
    return f"--post-process-file {model_path}" if model_path else ""

def create_bird_species_model():
    """Erstelle ein bird-species Modell basierend auf YOLOv8 mit Vogel-fokussierten Einstellungen"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        # Erstelle bird-species Konfiguration basierend auf YOLOv8
        bird_species_config = """{
    "rpicam-apps":
    {
        "lores":
        {
            "width": 640,
            "height": 640,
            "format": "rgb"
        }
    },

    "hailo_yolo_inference":
    {
        "hef_file_8L": "/usr/share/hailo-models/yolov8s_h8l.hef",
        "hef_file_8": "/usr/share/hailo-models/yolov8s_h8.hef",
        "max_detections": 10,
        "threshold": 0.3,
        "class_filter": [14],

        "temporal_filter":
        {
            "tolerance": 0.15,
            "factor": 0.8,
            "visible_frames": 8,
            "hidden_frames": 2
        }
    },

    "object_detect_draw_cv":
    {
        "line_thickness" : 3,
        "font_thickness": 2
    }
}"""
        
        # Erstelle die Datei auf dem Remote-Host
        stdin, stdout, stderr = ssh.exec_command(f'sudo tee /usr/share/rpi-camera-assets/hailo_bird_species_inference.json > /dev/null << EOF\n{bird_species_config}\nEOF')
        stdout.channel.recv_exit_status()
        
        ssh.close()
        print("✅ bird-species Modell erfolgreich erstellt!")
        print("🐦 Optimiert für Vogelerkennung: niedrigere Schwelle, Fokus auf Klasse 14 (bird)")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des bird-species Modells: {e}")
        print("🔄 Verwende Standard YOLOv8...")

def get_remote_video_command():
    remote_path = config.get_remote_video_path(year, timestamp)
    roi_param = f"--roi {args.roi}" if args.roi else ""
    ai_param = get_ai_model_path()
    return f"""
    mkdir -p {remote_path} && \
    cd {remote_path} && \
    rpicam-vid --camera {args.cam} --hdr {args.hdr} {ai_param} --width {args.width} --height {args.height} --codec {args.codec} --rotation {args.rotation} --framerate {args.fps} --autofocus-mode {args.autofocus_mode} --autofocus-range {args.autofocus_range} {roi_param} -o "video.h264" -t {recording_duration_s * 1000}
    """

def get_remote_audio_command():
    """Audio-Aufnahme parallel zum Video (nur wenn Audio-Gerät verfügbar)"""
    if not audio_device:
        return None
    
    remote_path = config.get_remote_video_path(year, timestamp)
    # Audio-Aufnahme mit arecord (Mono, S16_LE Format)
    return f"""
    mkdir -p {remote_path} && \
    cd {remote_path} && \
    arecord -D {audio_device} -f S16_LE -r 44100 -c 1 -t wav -d {recording_duration_s} audio.wav
    """

# Funktion zum Überprüfen der Erreichbarkeit des Remote-Hosts
def is_reachable(host):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host['hostname'], username=host['username'], key_filename=host['key_filename'], timeout=5)
        ssh.close()
        return True
    except Exception as e:
        print(f"Fehler bei der Verbindung zu {host['hostname']}: {e}")
        return False

# Funktion zum Erstellen einer SCP-Verbindung
def create_scp_client(ssh):
    return SCPClient(ssh.get_transport())

# Funktion zum Ausführen eines Befehls auf dem Remote-Host
def execute_remote_command(command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        print(f"Ausgabe auf {remote_host['hostname']}: {output}")
        
        # Warte, bis der Befehl abgeschlossen ist
        stdout.channel.recv_exit_status()
        ssh.close()
    except Exception as e:
        print(f"Fehler bei der Verbindung zu {remote_host['hostname']}: {e}")

# Funktion zum Kopieren der Dateien vom Remote-Host
def copy_files_from_remote():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    has_audio = False
    try:
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        scp = create_scp_client(ssh)
        
        # Kopiere die Videodatei
        remote_path = config.get_remote_video_path(year, timestamp)
        print(f"📥 Kopiere Video von {remote_path}/video.h264...")
        scp.get(f"{remote_path}/video.h264", base_path)
        
        # Prüfe ob Audio-Datei existiert (optional)
        stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path}/audio.wav && echo 'exists'")
        has_audio = stdout.read().decode().strip() == 'exists'
        
        if has_audio:
            print(f"📥 Kopiere Audio von {remote_path}/audio.wav...")
            scp.get(f"{remote_path}/audio.wav", base_path)
        else:
            print(f"ℹ️  Keine Audio-Datei gefunden (nur Video)")
        
        scp.close()
        ssh.close()
        print(f"✅ Dateien vom Remote-Host {remote_host['hostname']} erfolgreich kopiert.")
    except Exception as e:
        print(f"❌ Fehler beim Kopieren der Dateien von {remote_host['hostname']}: {e}")
    return has_audio

# Signal-Handler zum Beenden des Skripts mit Ctrl+C
def signal_handler(sig, frame):
    print("Beenden des Skripts...")
    stop_event.set()

# Setze den Signal-Handler
signal.signal(signal.SIGINT, signal_handler)

# Überprüfe die Erreichbarkeit des Remote-Hosts
if not is_reachable(remote_host):
    print(f"Der Remote-Host {remote_host['hostname']} ist nicht erreichbar.")
    exit(1)

# Zeige System-Status vor der Aufnahme
get_remote_system_status()

# Nur System-Status anzeigen, wenn --system-status Parameter gesetzt
if args.system_status:
    print("✅ System-Status-Abfrage abgeschlossen.")
    exit(0)

# Prüfe System-Bereitschaft für Videoaufnahme
if not check_system_readiness():
    response = input("⚠️ System-Warnung erkannt. Trotzdem fortfahren? (j/N): ")
    if response.lower() not in ['j', 'ja', 'y', 'yes']:
        print("❌ Aufnahme abgebrochen.")
        exit(1)

# WICHTIG: Beende alle laufenden Kamera-Prozesse (inkl. Preview-Stream)
# für exklusiven Kamera-Zugriff bei HD-Aufnahme
print("🔧 Bereite Kamera vor (stoppe laufende Prozesse)...")
kill_remote_processes()
time.sleep(2)  # Warte bis Prozesse sicher beendet sind

# Threads zum gleichzeitigen Ausführen der Befehle auf dem Remote-Host
stop_event = threading.Event()
threads = []

# Video-Aufnahme starten
video_thread = threading.Thread(target=execute_remote_command, args=(get_remote_video_command(),))
threads.append(video_thread)
video_thread.start()

# Audio-Aufnahme starten (nur wenn Gerät verfügbar)
audio_command = get_remote_audio_command()
if audio_command:
    print("🎤 Starte parallele Audio-Aufnahme...")
    audio_thread = threading.Thread(target=execute_remote_command, args=(audio_command,))
    threads.append(audio_thread)
    audio_thread.start()
else:
    print("ℹ️  Keine Audio-Aufnahme (Gerät nicht verfügbar)")

# Warte, bis die Aufnahme abgeschlossen ist (mit Live-Fortschritt)
print("🎥 Aufnahme läuft...", flush=True)
try:
    for i in range(recording_duration_s):
        if stop_event.is_set():
            break
        time.sleep(1)
        elapsed = i + 1
        percent = elapsed * 100 // recording_duration_s
        remaining = recording_duration_s - elapsed
        # Progressbar: [████████░░░░░░] 50% (30/60s, noch 30s)
        bar_length = 20
        filled = int(bar_length * elapsed / recording_duration_s)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r   [{bar}] {percent}% ({elapsed}/{recording_duration_s}s, noch {remaining}s)  ", end='', flush=True)
except KeyboardInterrupt:
    signal_handler(None, None)

print("\n✅ Aufnahme abgeschlossen\n")

# Setze das Stop-Event, um die Threads zu beenden
stop_event.set()

# Warte, bis alle Threads beendet sind
for thread in threads:
    thread.join()

# Kopiere die Dateien vom Remote-Host
has_audio = copy_files_from_remote()

# Konvertiere die .h264-Datei (mit oder ohne Audio) in eine .mp4-Datei
video_file = f"{base_path}/video.h264"
audio_file = f"{base_path}/audio.wav"
mp4_file = f"{base_path}/{timestamp}__{args.width}x{args.height}.mp4"  # MP4-Datei mit Zeitstempel und Auflösung

# Überprüfen, ob die Video-Datei existiert
if not os.path.exists(video_file):
    print(f"❌ Fehler: Die Video-Datei {video_file} wurde nicht gefunden.")
    exit(1)

# FFmpeg-Befehl mit oder ohne Audio
if has_audio and os.path.exists(audio_file):
    print(f"🎬 Konvertiere Video mit Audio...")
    ffmpeg_command = f"ffmpeg -fflags +genpts -r {args.fps} -i {video_file} -i {audio_file} -c:v copy -c:a aac {mp4_file}"
else:
    print(f"🎬 Konvertiere Video ohne Audio...")
    ffmpeg_command = f"ffmpeg -fflags +genpts -r {args.fps} -i {video_file} -c:v copy {mp4_file}"
process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if process.returncode == 0:
    print(f"ffmpeg erfolgreich ausgeführt. Video wurde in {mp4_file} konvertiert.")
    print(f"Ausgabe von ffmpeg: {stdout.decode()}")
    
    # Lösche die ursprünglichen Dateien
    os.remove(video_file)
    if os.path.exists(audio_file):
        os.remove(audio_file)
else:
    print(f"Fehler beim Ausführen von ffmpeg: {stderr.decode()}")

# Führe ls -lah auf das Zielverzeichnis aus
subprocess.run(["ls", "-lah", base_path])

# Optionaler Stream-Neustart (falls Preview-Stream verwendet wird)
# Wird übersprungen wenn --no-stream-restart gesetzt (z.B. bei Auto-Trigger)
if not args.no_stream_restart:
    # Preview-Stream nur neu starten wenn nicht explizit deaktiviert
    # (sinnvoll für Auto-Trigger, überflüssig für On-Demand Aufnahmen)
    if not args.no_stream_restart:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
            
            # Prüfe ob Stream-Skript existiert
            stdin, stdout, stderr = ssh.exec_command("test -f ~/start-rtsp-stream.sh && echo 'EXISTS'")
            if 'EXISTS' in stdout.read().decode():
                print("\n🔄 Starte Preview-Stream neu...")
                ssh.exec_command("nohup ~/start-rtsp-stream.sh > /dev/null 2>&1 &")
                time.sleep(2)
                print("✅ Preview-Stream wurde neu gestartet")
            
            ssh.close()
        except Exception as e:
            # Ignoriere Fehler beim Stream-Neustart (nicht kritisch)
            pass
    else:
        print("\n⏭️  Preview-Stream Neustart übersprungen (--no-stream-restart)")


print("\n✅ Aufnahme erfolgreich abgeschlossen!")

print("Befehl auf dem Remote-Host ausgeführt und Dateien kopiert.")