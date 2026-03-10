"""
Monitoring-Komponenten: Log-Tailing, Video-Watching, Status-Reporting
"""
import sys
import logging
import time
import threading
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Set

from config import (
    REMOTE_LOG_FILE, REMOTE_VIDEO_BASE, CLIENT_VIDEO_BASE,
    VIDEO_WATCH_INTERVAL, RECENT_DAYS, LOG_COLORS,
    SSH_USER, SSH_HOST, SSH_KEY
)
from ssh_manager import get_ssh_manager

logger = logging.getLogger(__name__)


class LogMonitor:
    """Monitort Remote-Log-Datei und zeigt wichtige Events"""
    
    def __init__(self):
        self.ssh = get_ssh_manager()
        self.last_lines_read = 0
        self.recording_active = False
        self.recording_start = 0
        self.recording_duration = 60
        self.last_recording_path = ""
        self.ssh_failures = 0
        self.running = False
    
    def _log(self, color: str, message: str):
        """Print farbige Log-Nachricht"""
        import sys
        sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
        sys.stdout.flush()
    
    def start(self) -> threading.Thread:
        """Startet Log-Monitor in Hintergrund-Thread"""
        self._log('cyan', "📡 Starte Live-Event-Monitor...")
        
        # Initialisiere letzte Zeilen-Position
        output = self.ssh.exec_command_safe(f"wc -l < {REMOTE_LOG_FILE} 2>/dev/null || echo 0")
        try:
            self.last_lines_read = int(output.strip() or 0)
        except ValueError:
            self.last_lines_read = 0
        
        self.running = True
        thread = threading.Thread(target=self._run, daemon=True, name="LogMonitor")
        thread.start()
        return thread
    
    def _run(self):
        """Hauptschleife für Log-Monitoring"""
        while self.running:
            time.sleep(2)
            
            # Hole aktuelle Zeilen-Anzahl
            output = self.ssh.exec_command_safe(f"wc -l < {REMOTE_LOG_FILE} 2>/dev/null || echo 0")
            
            if not output:
                self.ssh_failures += 1
                if self.ssh_failures == 3:
                    self._log('yellow', "⚠️  SSH-Verbindung unterbrochen, versuche Wiederverbindung...")
                elif self.ssh_failures > 10:
                    self._log('red', "❌ SSH-Verbindung dauerhaft verloren!")
                    self._log('yellow', f"💡 Prüfe: ping {SSH_HOST}")
                    self._log('cyan', "🔄 Automatischer Neustart in 30 Sekunden...")
                    time.sleep(30)
                    self.ssh_failures = 0
                continue
            
            self.ssh_failures = 0
            
            try:
                current_lines = int(output.strip())
            except ValueError:
                continue
            
            if current_lines <= self.last_lines_read:
                time.sleep(1)
                continue
            
            new_lines = current_lines - self.last_lines_read
            
            # Hole neue Log-Zeilen
            log_output = self.ssh.exec_command_safe(
                f"tail -{new_lines} {REMOTE_LOG_FILE}"
            )
            
            if log_output:
                self._process_log_lines(log_output)
                self.last_lines_read = current_lines
    
    def _process_log_lines(self, log_output: str):
        """Verarbeitet Log-Output und zeigt wichtige Events"""
        for line in log_output.split('\n'):
            if not line.strip():
                continue
            
            # Extrahiere Timestamp und Nachricht
            parts = line.split(' - ', 1)
            timestamp = parts[0] if len(parts) > 0 else ""
            message = parts[1] if len(parts) > 1 else line
            
            # Recording-Status verfolgen
            if "Starte Aufnahme" in message:
                self.recording_active = True
                self.recording_start = time.time()
                self._log('green', f"[{timestamp}] {message}")
                
                # Extrahiere Aufnahme-Pfad für spätere Video-Sync
                if '.h264' in message:
                    parts = message.split("'")
                    if len(parts) >= 2:
                        self.last_recording_path = parts[1]
            
            elif "Aufnahme beendet" in message:
                self.recording_active = False
                self._log('green', f"[{timestamp}] {message}")
                self._log('', "")  # Leere Zeile
            
            # Zeige Vogel-Erkennung nur wenn nicht aufgenommen wird
            elif "Vogel erkannt" in message or "Trigger-Bedingungen" in message:
                if not self.recording_active:
                    self._log('green', f"[{timestamp}] {message}")
            
            # Zeige Konvertierungs-Progress
            elif any(x in message for x in ["Konvertiere", "erstellt", "Konvertierung abgeschlossen", "H264-Datei gelöscht"]):
                if "Konvertierung abgeschlossen" in message:
                    self._log('green', f"[{timestamp}] {message}")
                    self._log('', "")
                else:
                    self._log('cyan', f"[{timestamp}] {message}")
            
            # Zeige Health-Status
            elif "Status:" in message and any(x in message for x in ["🟢", "🟡", "🔴"]):
                self._log('cyan', f"[{timestamp}] {message}")
                self._log('', "")
            
            # Zeige Heartbeat nur wenn nicht aufgenommen wird
            elif "Monitor aktiv" in message:
                if not self.recording_active:
                    self._log('blue', f"[{timestamp}] {message}")
    
    def stop(self):
        """Stoppt Log-Monitor"""
        self.running = False


class VideoWatcher:
    """Überwacht Video-Verzeichnisse und synchronisiert neue Videos"""
    
    def __init__(self, ssh=None):
        self.ssh = ssh or get_ssh_manager()
        self.synced_videos: Set[str] = set()
        self.running = False
    
    def _log(self, color: str, message: str):
        """Print farbige Log-Nachricht"""
        import sys
        sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
        sys.stdout.flush()
    
    def start(self) -> threading.Thread:
        """Startet Video-Watcher in Hintergrund-Thread"""
        self._log('cyan', "🎥 Starte Video-Watcher...")
        self.running = True
        thread = threading.Thread(target=self._run, daemon=True, name="VideoWatcher")
        thread.start()
        return thread
    
    def _run(self):
        """Hauptschleife für Video-Watching"""
        while self.running:
            time.sleep(VIDEO_WATCH_INTERVAL)
            
            # Berechne cutoff-Zeit (nur Videos der letzten N Tage)
            days_ago = datetime.now() - timedelta(days=RECENT_DAYS)
            
            # Finde alle Video-Verzeichnisse (Namen basierend auf Wochentagen)
            weekday_names = [
                'Montag__', 'Dienstag__', 'Mittwoch__', 'Donnerstag__',
                'Freitag__', 'Samstag__', 'Sonntag__'
            ]
            
            find_cmd = (
                f"find '{REMOTE_VIDEO_BASE}' -type d -mtime -{RECENT_DAYS} "
                f"\\( {' -o '.join([f'-name \"{name}*\"' for name in weekday_names])} \\) "
                f"2>/dev/null | sort -u"
            )
            
            output = self.ssh.exec_command_safe(find_cmd, fallback="")
            
            if not output:
                continue
            
            for video_dir in output.split('\n'):
                if not video_dir.strip():
                    continue
                
                self._process_video_dir(video_dir.strip())
    
    def _process_video_dir(self, video_dir: str):
        """Verarbeitet ein Video-Verzeichnis"""
        # Verbose logging suppressed - these checks run frequently and create log spam
        # self._log('blue', f"🔍 Prüfe Video-Verzeichnis")
        # self._log('blue', f"   {video_dir}")
        
        # Prüfe ob Verzeichnis MP4-Dateien hat
        mp4_output = self.ssh.exec_command_safe(
            f"ls -1 '{video_dir}'/*.mp4 2>/dev/null || echo ''"
        )
        
        # Zähle Dateien zuverlässig (ohne grep-Fehler!)
        mp4_files = [f for f in mp4_output.split('\n') if f.strip()]
        mp4_count = len(mp4_files)
        
        # Verbose logging suppressed - only show when videos are actually being synced
        # self._log('blue', f"   📊 MP4-Dateien: {mp4_count}")
        
        if mp4_count > 0:
            dir_name = Path(video_dir).name
            
            if dir_name not in self.synced_videos:
                self._log('yellow', f"⏳ Neue Videos gefunden - starte Synchronisation...")
                self._log('yellow', f"   Quelle: {video_dir}")
                
                if self._sync_videos(video_dir):
                    self.synced_videos.add(dir_name)
                    self._log('green', f"✅ Markiert als synchronisiert")
    
    def _sync_videos(self, remote_video_dir: str) -> bool:
        """Synchronisiert Videos vom Remote"""
        try:
            # Extrahiere Pfad-Komponenten
            parts = remote_video_dir.split('/')
            year = None
            month = None
            
            # Finde Jahr und Monat im Pfad
            for part in parts:
                if part.isdigit() and 2020 <= int(part) <= 2100:
                    year = part
                elif part.isdigit() and 1 <= int(part) <= 12:
                    month = part
            
            # Bestimme Modus basierend auf Remote-Pfad
            mode_dir = "AI-HAD"  # Standard
            if "/Zeitlupe/" in remote_video_dir:
                mode_dir = "Zeitlupe"
            elif "/4K/" in remote_video_dir:
                mode_dir = "4K"
            elif "/Normal/" in remote_video_dir:
                mode_dir = "Normal"
            
            dir_name = Path(remote_video_dir).name
            
            if year and month:
                local_dir = CLIENT_VIDEO_BASE / mode_dir / year / month / dir_name
            else:
                local_dir = CLIENT_VIDEO_BASE / mode_dir / dir_name
            
            local_dir.mkdir(parents=True, exist_ok=True)
            
            self._log('cyan', "📥 Synchronisiere Videos via rsync")
            self._log('cyan', f"   Remote: {remote_video_dir}")
            self._log('cyan', f"   Lokal:  {local_dir}")
            
            # Verwende rsync für Synchronisation (robust & effizient)
            rsync_cmd = [
                'rsync', '-avz', '--progress',
                '-e', f"ssh -i '{SSH_KEY}' -o ConnectTimeout=10 -o StrictHostKeyChecking=no",
                f"{SSH_USER}@{SSH_HOST}:{remote_video_dir}/",
                f"{local_dir}/",
                '--include=*.mp4',
                '--exclude=*'
            ]
            
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                self._log('red', f"❌ rsync-Fehler: {result.stderr[:200]}")
                return False
            
            # Verifiziere lokale Dateien
            local_mp4s = list(local_dir.glob('*.mp4'))
            
            if local_mp4s:
                self._log('green', f"✅ {len(local_mp4s)} Video(s) übertragen")
                for mp4 in local_mp4s[:5]:
                    size_mb = mp4.stat().st_size / (1024 * 1024)
                    self._log('', f"   📊 {mp4.name} ({size_mb:.1f} MB)")
                return True
            else:
                self._log('red', f"❌ Keine Dateien lokal gefunden nach rsync")
                return False
        
        except Exception as e:
            self._log('red', f"❌ Video-Sync Fehler: {e}")
            return False
    
    def stop(self):
        """Stoppt Video-Watcher"""
        self.running = False


class StatusReporter:
    """Periodisches Status-Reporting"""
    
    def __init__(self, interval: int = 300, ssh=None):
        self.ssh = ssh or get_ssh_manager()
        self.interval = interval
        self.running = False
    
    def _log(self, color: str, message: str):
        """Print farbige Log-Nachricht"""
        import sys
        sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
        sys.stdout.flush()
    
    def start(self) -> threading.Thread:
        """Startet Status-Reporter in Hintergrund-Thread"""
        self.running = True
        thread = threading.Thread(target=self._run, daemon=True, name="StatusReporter")
        thread.start()
        return thread
    
    def _run(self):
        """Hauptschleife für Status-Reporting"""
        while self.running:
            time.sleep(self.interval)
            self._report_status()
    
    def _report_status(self):
        """Gibt Status-Report aus"""
        self._log('', "")
        self._log('cyan', "===================================================================")
        self._log('cyan', f"🕐 STATUS-UPDATE ({datetime.now().strftime('%H:%M:%S')})")
        self._log('cyan', "===================================================================")
        
        # Prüfe Monitor-Prozess
        cmd = "ps aux | grep 'python3.*unified-camera-monitor' | grep -v bash | grep -v grep"
        success, output, _ = self.ssh.exec_command(cmd)
        
        if success and output:
            # Extrahiere PID und Ressourcen
            parts = output.split()
            pid = parts[1] if len(parts) > 1 else "?"
            cpu = parts[2] if len(parts) > 2 else "?"
            mem = parts[3] if len(parts) > 3 else "?"
            
            self._log('green', f"✅ Monitor läuft | PID: {pid} | CPU: {cpu}% | RAM: {mem}%")
        else:
            self._log('red', "❌ Monitor-Prozess nicht aktiv")
        
        # Temperatur auslesen
        self._log('', "")
        self._log('', "🌡️  PI-RESSOURCEN:")
        temp_output = self.ssh.exec_command_safe("vcgencmd measure_temp 2>/dev/null || echo 'N/A'")
        if temp_output and "temp=" in temp_output:
            # Extrahiere Temperatur (z.B. "temp=45.1'C" → 45.1°C)
            import re
            match = re.search(r"temp=([0-9.]+)", temp_output)
            if match:
                temp = match.group(1)
                # Farbcodierung basierend auf Temperatur
                if float(temp) > 80:
                    color = 'red'
                    emoji = "🔥"
                elif float(temp) > 70:
                    color = 'yellow'
                    emoji = "⚠️ "
                else:
                    color = 'green'
                    emoji = "✅"
                self._log(color, f"   {emoji} CPU-Temperatur: {temp}°C")
        else:
            self._log('yellow', f"   ⚠️  Temperatur: N/A (vcgencmd nicht verfügbar)")
        
        # Disk-Speicher prüfen
        disk_cmd = "df -BG /home/roimme 2>/dev/null | tail -1 | awk '{print $2, $3, $4, int($3/$2*100)}'"
        disk_output = self.ssh.exec_command_safe(disk_cmd)
        if disk_output:
            parts = disk_output.split()
            if len(parts) >= 4:
                total, used, free, percent = parts[0], parts[1], parts[2], parts[3]
                # Farbcodierung für Speicher
                try:
                    usage_pct = int(percent.rstrip('%'))
                    if usage_pct > 90:
                        disk_color = 'red'
                        disk_emoji = "🔴"
                    elif usage_pct > 80:
                        disk_color = 'yellow'
                        disk_emoji = "🟡"
                    else:
                        disk_color = 'green'
                        disk_emoji = "🟢"
                    self._log(disk_color, f"   {disk_emoji} Disk /home/roimme: {used}/{total} ({percent}% genutzt)")
                except ValueError:
                    self._log('cyan', f"   💾 Disk: {used}/{total} ({percent}% genutzt)")
        
        # Letzte Log-Zeile
        self._log('', "")
        self._log('', "📋 Letzte Log-Zeile:")
        last_log = self.ssh.exec_command_safe(f"tail -1 {REMOTE_LOG_FILE}")
        if last_log:
            self._log('blue', f"   {last_log}")
        
        self._log('cyan', "===================================================================")
        self._log('', "")
    
    def stop(self):
        """Stoppt Status-Reporter"""
        self.running = False


def format_log(timestamp: str, message: str, color: str = 'reset') -> str:
    """Formatiert Log-Zeile mit Farbe"""
    return f"{LOG_COLORS.get(color, '')}{timestamp} | {message}{LOG_COLORS['reset']}"
