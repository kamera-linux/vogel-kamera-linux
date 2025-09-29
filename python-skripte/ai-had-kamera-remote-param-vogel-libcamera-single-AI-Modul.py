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
    description='''Vogelhaus Remote Steuerung
    Beispiel für einen Aufruf:
    python kamera-remote-param-vogel-libcamera-single-AI-Modul.py --duration 3 --width 1920 --height 1080 --codec h264 --autofocus_mode continuous --rotation 180 --ai-modul on'''
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
        
        # Beende alle relevanten Prozesse (libcamera-vid und ffmpeg)
        ssh.exec_command("pkill -f libcamera-vid")
        ssh.exec_command("pkill -f ffmpeg")
        ssh.close()
        print("Alle relevanten Prozesse auf dem Remote-Host wurden beendet.")
    except Exception as e:
        print(f"Fehler beim Beenden der Prozesse auf dem Remote-Host: {e}")

# Ermitteln des aktiven USB-Audio-Geräts
audio_device = get_usb_audio_device_remote()
if not audio_device:
    print("Kein USB-Audio-Gerät auf dem Remote-Host gefunden. Beende das Skript.")
    kill_remote_processes()
    exit(1)

print(f"Verwendetes Audio-Gerät auf dem Remote-Host: {audio_device}")

# Befehl zum Ausführen auf dem Remote-Host (Video- und Audioaufnahme)
def get_remote_video_command():
    remote_path = config.get_remote_video_path(year, timestamp)
    roi_param = f"--roi {args.roi}" if args.roi else ""
    ai_param = "--post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json" if getattr(args, 'ai_modul') == 'on' else ""
    return f"""
    mkdir -p {remote_path} && \
    cd {remote_path} && \
    rpicam-vid --camera {args.cam} --hdr {args.hdr} {ai_param} --width {args.width} --height {args.height} --codec {args.codec} --rotation {args.rotation} --framerate {args.fps} --autofocus-mode {args.autofocus_mode} --autofocus-range {args.autofocus_range} {roi_param} -o "video.h264" -t {recording_duration_s * 1000} & \
    arecord -D {audio_device} -f S16_LE -r 44100 -c 1 -t wav -d {recording_duration_s} {remote_path}/audio.wav
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
    try:
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        scp = create_scp_client(ssh)
        
        # Kopiere die Video- und Audiodateien
        remote_path = config.get_remote_video_path(year, timestamp)
        scp.get(f"{remote_path}/video.h264", base_path)
        scp.get(f"{remote_path}/audio.wav", base_path)
        
        scp.close()
        ssh.close()
        print(f"Dateien vom Remote-Host {remote_host['hostname']} erfolgreich kopiert.")
    except Exception as e:
        print(f"Fehler beim Kopieren der Dateien von {remote_host['hostname']}: {e}")

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

# Konvertiere die .h264- und .wav-Dateien in eine .mp4-Datei
video_file = f"{base_path}/video.h264"
audio_file = f"{base_path}/audio.wav"
mp4_file = f"{base_path}/{timestamp}__{args.width}x{args.height}.mp4"  # MP4-Datei mit Zeitstempel und Auflösung

# Überprüfen, ob die Audio-Datei existiert
if not os.path.exists(audio_file):
    print(f"Fehler: Die Audio-Datei {audio_file} wurde nicht gefunden.")
    exit(1)

ffmpeg_command = f"ffmpeg -fflags +genpts -r {args.fps} -i {video_file} -i {audio_file} -c:v copy -c:a aac {mp4_file}"
process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if process.returncode == 0:
    print(f"ffmpeg erfolgreich ausgeführt. Video wurde in {mp4_file} konvertiert.")
    print(f"Ausgabe von ffmpeg: {stdout.decode()}")
    
    # Lösche die ursprünglichen Dateien
    os.remove(video_file)
    os.remove(audio_file)
else:
    print(f"Fehler beim Ausführen von ffmpeg: {stderr.decode()}")
# Führe ls -lah auf das Zielverzeichnis aus
subprocess.run(["ls", "-lah", base_path])

progress.close()

print("Befehl auf dem Remote-Host ausgeführt und Dateien kopiert.")