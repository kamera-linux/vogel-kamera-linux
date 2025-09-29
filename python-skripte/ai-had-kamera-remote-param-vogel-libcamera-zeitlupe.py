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
    description='''Kamerawagen Remote Steuerung
    Beispiel für einen Aufruf:
    python kamera-remote-param-vogel-libcamera-zeitlupe.py --duration 3 --width 1536 --height 864 --fps 120 --cam 0 --slowmotion --rotation 180 --autofocus_mode continuous'''
)
parser.add_argument('--version', action='version', version=f'Vogel-Kamera-Linux v{__version__}')
parser.add_argument('--duration', type=int, required=True, help='Aufnahmedauer in Minuten')
parser.add_argument('--width', type=int, default=1536, help='Breite des Videos (default: 1536 für Zeitlupe)')
parser.add_argument('--height', type=int, default=864, help='Höhe des Videos (default: 864 für Zeitlupe)')
parser.add_argument('--codec', type=str, default='h264', help='Codec für das Video (default: h264)')
parser.add_argument('--autofocus_mode', type=str, default='continuous', help='Autofokus-Modus (default: continuous)')
parser.add_argument('--autofocus_range', type=str, default='full', help='Autofokus-Bereich (default: full)')
parser.add_argument('--hdr', type=str, choices=['auto', 'off'], default='off', help='HDR-Modus (default: off)')
parser.add_argument('--roi', type=str, help='Region of Interest im Format x,y,w,h (optional)')
parser.add_argument('--rotation', type=int, choices=[0, 90, 180, 270], default=180, help='Rotation des Videos (default: 0)')
parser.add_argument('--fps', type=int, default=120, help='Framerate für Video (default: 120 für Zeitlupe)')
parser.add_argument('--cam', type=int, default=0, choices=[0, 1], help='Kamera-ID (default: 0)')
parser.add_argument('--slowmotion', action='store_true', help='Aktiviere Zeitlupe (default: deaktiviert)')
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
base_path = config.get_video_path(year, week_number, timestamp, "Zeitlupe")

# Erstelle das Verzeichnis, falls es nicht existiert
os.makedirs(base_path, exist_ok=True)

# Aufnahmezeit in Sekunden
recording_duration_s = args.duration * 60

# Funktion zum Generieren des Remote-Befehls für die Videoaufnahme
# Befehl zum Ausführen auf dem Remote-Host (nur Video)
def get_remote_video_command():
    remote_path = config.get_remote_video_path(year, timestamp)
    roi_param = f"--roi {args.roi}" if args.roi else ""
    return f"""
    mkdir -p {remote_path} && \
    cd {remote_path} && \
    rpicam-vid --camera {args.cam} --hdr {args.hdr} --width {args.width} --height {args.height} --codec {args.codec} \
    --rotation {args.rotation} --framerate {args.fps} --autofocus-mode {args.autofocus_mode} \
    --autofocus-range {args.autofocus_range} {roi_param} -o video.h264 -t {recording_duration_s * 1000}
    """

# Funktion zum Ausführen eines Befehls auf dem Remote-Host
def execute_remote_command(command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        print(f"Ausgabe auf {remote_host['hostname']}: {output}")
        stdout.channel.recv_exit_status()  # Warte, bis der Befehl abgeschlossen ist
        ssh.close()
    except Exception as e:
        print(f"Fehler bei der Verbindung zu {remote_host['hostname']}: {e}")

# Funktion zum Kopieren der Dateien vom Remote-Host
def copy_files_from_remote():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        scp = SCPClient(ssh.get_transport())
        
        # Kopiere die Videodatei
        remote_path = config.get_remote_video_path(year, timestamp)
        scp.get(f"{remote_path}/video.h264", base_path)
        
        scp.close()
        ssh.close()
        print(f"Dateien vom Remote-Host {remote_host['hostname']} erfolgreich kopiert.")
    except Exception as e:
        print(f"Fehler beim Kopieren der Dateien von {remote_host['hostname']}: {e}")

# Funktion zur Konvertierung der Videodatei in MP4 mit mehreren Frameraten
def convert_to_mp4():
    video_file = f"{base_path}/video.h264"
    
    # Liste der Ziel-Frameraten
    playback_fps_list = [5, 10, 20, 30, 120]
    
    for playback_fps in playback_fps_list:
        # MP4-Dateiname mit Framerate im Namen
        mp4_file = f"{base_path}/{timestamp}__{args.width}x{args.height}__{playback_fps}fps.mp4"
        
        # ffmpeg-Befehl zur Konvertierung mit Framerate-Anpassung
        ffmpeg_command = f"ffmpeg -fflags +genpts -r {playback_fps} -i {video_file} -c:v copy {mp4_file}"
        process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print(f"ffmpeg erfolgreich ausgeführt. Video wurde in {mp4_file} konvertiert.")
        else:
            print(f"Fehler beim Ausführen von ffmpeg für {playback_fps} FPS: {stderr.decode()}")
    
    # Lösche die ursprüngliche .h264-Datei nach der Konvertierung
    os.remove(video_file)

# Signal-Handler zum Beenden des Skripts mit Ctrl+C
def signal_handler(sig, frame):
    print("Beenden des Skripts...")
    stop_event.set()

# Setze den Signal-Handler
signal.signal(signal.SIGINT, signal_handler)

# Threads zum gleichzeitigen Ausführen der Befehle auf dem Remote-Host
stop_event = threading.Event()
threads = []

video_thread = threading.Thread(target=execute_remote_command, args=(get_remote_video_command(),))
threads.append(video_thread)
video_thread.start()

# Fortschrittsanzeige initialisieren
progress = tqdm(total=recording_duration_s, desc="Fortschritt", unit="s")

# Warte, bis die Aufnahme abgeschlossen ist
try:
    for _ in range(recording_duration_s):
        if stop_event.is_set():
            break
        time.sleep(1)
        progress.update(1)
except KeyboardInterrupt:
    signal_handler(None, None)

# Setze das Stop-Event, um die Threads zu beenden
stop_event.set()

# Warte, bis alle Threads beendet sind
for thread in threads:
    thread.join()

# Kopiere die Dateien vom Remote-Host
copy_files_from_remote()

# Konvertiere die Videodatei in MP4 mit mehreren Frameraten
convert_to_mp4()

progress.close()

print("Befehl auf dem Remote-Host ausgeführt und Dateien kopiert.")