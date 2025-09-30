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
    description='''Vogelhaus Remote Steuerung für Audioaufnahme
    Beispiel für einen Aufruf:
    python ai-had-audio-remote-param-vogel-libcamera-single.py --duration 10'''
)
parser.add_argument('--version', action='version', version=f'Vogel-Kamera-Linux v{__version__}')
parser.add_argument('--duration', type=int, required=True, help='Aufnahmedauer in Minuten')
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
base_path = config.get_video_path(year, week_number, timestamp, "Audio")

# Erstelle das Verzeichnis, falls es nicht existiert
os.makedirs(base_path, exist_ok=True)

# System-Monitoring Funktionen
def get_remote_system_status():
    """Zeigt den aktuellen System-Status des Remote-Hosts an"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        print(f"\n📊 System-Status für {remote_host['hostname']}:")
        print("=" * 50)
        
        # CPU-Temperatur
        stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
        temp_output = stdout.read().decode().strip()
        if temp_output.startswith("temp="):
            temp_str = temp_output.split("=")[1].replace("'C", "")
            temp = float(temp_str)
            if temp > 70:
                status = "🔴 KRITISCH"
            elif temp > 60:
                status = "🟡 WARNUNG"
            else:
                status = "🟢 OK"
            print(f"🌡️  CPU-Temperatur: {temp}°C {status}")
        
        # Disk-Speicherplatz
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1")
        disk_output = stdout.read().decode().strip()
        if disk_output:
            disk_parts = disk_output.split()
            used_percent = disk_parts[4].replace("%", "")
            if int(used_percent) > 90:
                status = "🔴 VOLL"
            elif int(used_percent) > 80:
                status = "🟡 WARNUNG"
            else:
                status = "🟢 OK"
            print(f"💾 Festplatte: {disk_parts[2]} verwendet von {disk_parts[1]} ({disk_parts[4]}) {status}")
        
        # Arbeitsspeicher
        stdin, stdout, stderr = ssh.exec_command("free -h | grep Mem:")
        mem_output = stdout.read().decode().strip()
        if mem_output:
            mem_parts = mem_output.split()
            print(f"🧠 Arbeitsspeicher: {mem_parts[2]} verwendet von {mem_parts[1]} ({mem_parts[6]} verfügbar)")
        
        # CPU Load Average
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        if "load average:" in uptime_output:
            load_part = uptime_output.split("load average:")[1].strip()
            load_1min = float(load_part.split(",")[0].strip())
            if load_1min > 2.0:
                status = "🔴 HOCH"
            elif load_1min > 1.0:
                status = "🟡 MITTEL"
            else:
                status = "🟢 NIEDRIG"
            print(f"⚡ CPU-Load (1min): {load_1min} {status}")
        
        ssh.close()
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f"❌ Fehler beim Abrufen des System-Status: {e}")

def check_system_readiness():
    """Prüft kritische System-Parameter für Audio-Aufnahme"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        warnings = []
        
        # CPU-Temperatur prüfen
        stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
        temp_output = stdout.read().decode().strip()
        if temp_output.startswith("temp="):
            temp = float(temp_output.split("=")[1].replace("'C", ""))
            if temp > 70:
                warnings.append(f"❌ CPU-Temperatur kritisch: {temp}°C (>70°C)")
            elif temp > 60:
                warnings.append(f"⚠️ CPU-Temperatur hoch: {temp}°C (>60°C)")
        
        # Festplattenspeicher prüfen
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1")
        disk_output = stdout.read().decode().strip()
        if disk_output:
            used_percent = int(disk_output.split()[4].replace("%", ""))
            if used_percent > 90:
                warnings.append(f"❌ Festplatte fast voll: {used_percent}% (>90%)")
            elif used_percent > 80:
                warnings.append(f"⚠️ Festplatte wird voll: {used_percent}% (>80%)")
        
        # CPU Load prüfen
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        if "load average:" in uptime_output:
            load_1min = float(uptime_output.split("load average:")[1].split(",")[0].strip())
            if load_1min > 2.0:
                warnings.append(f"❌ CPU-Load sehr hoch: {load_1min} (>2.0) - kann Audio-Qualität beeinträchtigen")
            elif load_1min > 1.0:
                warnings.append(f"⚠️ CPU-Load erhöht: {load_1min} (>1.0) - Audio-Performance beobachten")
        
        ssh.close()
        
        if warnings:
            print("\n⚠️ System-Warnungen erkannt:")
            for warning in warnings:
                print(f"  {warning}")
            return False
        else:
            print("\n✅ System bereit für Audio-Aufnahme")
            return True
            
    except Exception as e:
        print(f"❌ Fehler bei System-Bereitschaftscheck: {e}")
        return False

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
        
        # Beende alle relevanten Prozesse (ffmpeg)
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

# Befehl zum Ausführen auf dem Remote-Host (nur Audioaufnahme)
def get_remote_audio_command():
    remote_path = config.get_remote_audio_path(year, timestamp)
    return f"""
    mkdir -p {remote_path} && \
    cd {remote_path} && \
    arecord -D {audio_device} -f S16_LE -r 44100 -c 1 -t wav -d {recording_duration_s} audio_{timestamp}.wav
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
        
        # Kopiere die Audiodatei mit Zeitstempel
        remote_path = config.get_remote_audio_path(year, timestamp)
        scp.get(f"{remote_path}/audio_{timestamp}.wav", base_path)
        
        scp.close()
        ssh.close()
        print(f"Audiodatei vom Remote-Host {remote_host['hostname']} erfolgreich kopiert.")
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

# Zeige System-Status vor der Aufnahme
get_remote_system_status()

# Prüfe System-Bereitschaft für Audio-Aufnahme
if not check_system_readiness():
    response = input("⚠️ System-Warnung erkannt. Trotzdem fortfahren? (j/N): ")
    if response.lower() not in ['j', 'ja', 'y', 'yes']:
        print("❌ Audio-Aufnahme abgebrochen.")
        exit(1)

# Threads zum gleichzeitigen Ausführen der Befehle auf dem Remote-Host
stop_event = threading.Event()
threads = []

audio_thread = threading.Thread(target=execute_remote_command, args=(get_remote_audio_command(),))
threads.append(audio_thread)
audio_thread.start()

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

# Kopiere die Audiodatei vom Remote-Host
copy_files_from_remote()

progress.close()

print("Audioaufnahme abgeschlossen und Datei kopiert.")