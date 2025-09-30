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
parser.add_argument('--system-status', action='store_true', help='Zeige nur System-Status ohne Aufnahme')
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
        
        # Warnung bei hoher Load während Zeitlupe-Aufnahme (besonders kritisch)
        if "load average:" in uptime_output:
            load_1min = float(uptime_output.split("load average:")[1].split(',')[0].strip().replace(',', '.'))
            if load_1min > 1.5:  # Niedrigere Schwelle für Zeitlupe
                print(f"   ⚠️  WARNUNG: Hohe CPU-Last ({load_1min:.2f}) - Zeitlupe-Qualität gefährdet!")
            elif load_1min > 0.8:
                print(f"   💡 Moderate CPU-Last ({load_1min:.2f}) - Zeitlupe könnte ruckeln")
        
    except Exception as e:
        print(f"⚠️ Fehler beim Abrufen des System-Status: {e}")

def check_system_readiness_slowmotion():
    """Prüfe ob System bereit für Zeitlupe-Aufnahme ist (strengere Kriterien)"""
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
        
        # Bewertung (strengere Kriterien für Zeitlupe)
        issues = []
        if temp_val > 65:  # Niedrigere Schwelle für Zeitlupe
            issues.append(f"🔴 CPU-Temperatur kritisch für Zeitlupe: {temp_val}°C")
        elif temp_val > 55:
            issues.append(f"🟡 CPU-Temperatur hoch für Zeitlupe: {temp_val}°C")
        
        if load_1min > 2.0:  # Niedrigere Schwelle für Zeitlupe
            issues.append(f"🔴 CPU-Last kritisch für Zeitlupe: {load_1min:.2f}")
        elif load_1min > 1.0:
            issues.append(f"🟡 CPU-Last hoch für Zeitlupe: {load_1min:.2f}")
        
        if used_percent > 95:
            issues.append(f"🔴 Festplatte fast voll: {used_percent}%")
        elif used_percent > 90:
            issues.append(f"🟡 Festplatte wird knapp: {used_percent}%")
        
        if issues:
            print("⚠️  System-Warnungen vor Zeitlupe-Aufnahme:")
            for issue in issues:
                print(f"   {issue}")
            
            if any("🔴" in issue for issue in issues):
                print("❌ KRITISCH: Zeitlupe-Aufnahme nicht empfohlen!")
                return False
            else:
                print("⚡ Zeitlupe-Aufnahme möglich, aber mit Vorsicht")
                return True
        else:
            print("✅ System bereit für Zeitlupe-Aufnahme")
            return True
    
    except Exception as e:
        print(f"⚠️ Fehler bei System-Bereitschaftsprüfung: {e}")
        return True  # Im Zweifel erlauben

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

# Zeige System-Status vor der Aufnahme
get_remote_system_status()

# Nur System-Status anzeigen, wenn --system-status Parameter gesetzt
if args.system_status:
    print("✅ System-Status-Abfrage abgeschlossen.")
    exit(0)

# Prüfe System-Bereitschaft für Zeitlupe-Aufnahme
if not check_system_readiness_slowmotion():
    response = input("⚠️ System-Warnung erkannt. Trotzdem fortfahren? (j/N): ")
    if response.lower() not in ['j', 'ja', 'y', 'yes']:
        print("❌ Zeitlupe-Aufnahme abgebrochen.")
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

# Konvertiere die Videodatei in MP4 mit mehreren Frameraten
convert_to_mp4()

progress.close()

print("Befehl auf dem Remote-Host ausgeführt und Dateien kopiert.")