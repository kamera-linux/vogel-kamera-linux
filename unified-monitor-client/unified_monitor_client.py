#!/usr/bin/env python3
"""
Unified Monitor Client - Python-Replacement für start-unified-monitoring.sh

Orchestriert die komplette Vogel-Kamera-Überwachung auf dem Client-Rechner:
- SSH-Verbindung & Version-Checking
- Remote-Skript-Synchronisation
- Live-Log-Tailing (Event-Monitoring)
- Video-Watching & Synchronisation
- Status-Reporting
"""

import sys
import time
import logging
import signal
import click
from pathlib import Path
from datetime import datetime

from config import (
    RECORDING_MODES, DEFAULT_THRESHOLD, DEFAULT_COOLDOWN,
    DEFAULT_TRIGGER_DURATION, DEFAULT_AUDIO_THRESHOLD,
    LOG_COLORS, SSH_HOST, SSH_USER, REMOTE_VIDEO_BASE,
    REMOTE_SCRIPT_DIR
)
from ssh_manager import get_ssh_manager, SSHManager
from version_manager import VersionManager
from monitors import LogMonitor, VideoWatcher, StatusReporter

# Logging-Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_colored(color: str, message: str):
    """Print farbige Nachricht"""
    sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
    sys.stdout.flush()


def show_banner(mode: str, version: str):
    """Zeigt Start-Banner"""
    log_colored('cyan', "")
    log_colored('cyan', "======================================================================")
    log_colored('cyan', "🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung (Python)")
    log_colored('cyan', "======================================================================")
    log_colored('cyan', f"   Version: v{version}")
    log_colored('cyan', "======================================================================")
    log_colored('cyan', "")
    
    # Modus-Info
    if mode in RECORDING_MODES:
        mode_info = RECORDING_MODES[mode]
        emoji = {
            'slowmo': '🎬',
            '4k': '📹',
            'ai-had': '🎤',
            'normal': '📹',
        }.get(mode, '🎥')
        
        log_colored('cyan', f"{emoji} Modus: {mode_info['desc']}")
    
    log_colored('cyan', "")


def show_parameters(threshold: float, cooldown: int, trigger: float, audio_threshold: float, enable_audio: bool, duration: int = 0, audio_only: bool = False, fps: int = 0, resolution: str = None, bitrate: int = 0, manual_record: bool = False):
    """Zeigt Monitor-Parameter"""
    if manual_record:
        log_colored('red', f"🔴 MANUELLER AUFNAHMEMODUS - Keine Vogelerkennung!")
        log_colored('blue', f"⚙️  Trigger: {trigger}s (ignoriert)")
    else:
        log_colored('blue', f"⚙️  Threshold: {threshold} | Cooldown: {cooldown}s | Trigger: {trigger}s")
    
    # Video-Parameter
    video_params = []
    if resolution:
        video_params.append(f"{resolution}")
    if fps > 0:
        video_params.append(f"{fps} fps")
    if bitrate > 0:
        video_params.append(f"{bitrate} kbps")
    
    if video_params:
        log_colored('cyan', f"📹 Video: {' | '.join(video_params)}")
    
    if duration > 0:
        log_colored('cyan', f"⏱️  Duration: {duration} Minuten")
    if audio_only:
        log_colored('magenta', f"🎤 Audio-Only Modus")
    if enable_audio and not audio_only:
        log_colored('magenta', f"🎤 Audio-Threshold: {audio_threshold}")
    log_colored('cyan', "")


def system_check(ssh: SSHManager) -> bool:
    """Führt System-Check durch"""
    log_colored('cyan', "🔍 System-Check...")
    log_colored('cyan', "")
    
    # SSH-Verbindung
    sys.stdout.write("📡 SSH-Verbindung zu {} ... ".format(f"{SSH_USER}@{SSH_HOST}"))
    sys.stdout.flush()
    
    if not ssh.connect():
        log_colored('red', "❌")
        log_colored('red', "FEHLER: Keine SSH-Verbindung!")
        return False
    
    log_colored('green', "✅")
    
    # Version-Check
    log_colored('cyan', "")
    vm = VersionManager()
    if not vm.compare_versions():
        log_colored('yellow', "⚠️  Remote-Skripte sind veraltet")
    
    # Remote-Skripte synchronisieren
    sys.stdout.write("🔄 Remote-Skripte synchronisieren ... ")
    sys.stdout.flush()
    
    if not vm.sync_remote_scripts():
        log_colored('red', "❌")
        log_colored('red', "Fehler beim Synchronisieren der Remote-Skripte")
        return False
    
    log_colored('green', "✅")
    
    # Prüfe Dateien auf Pi
    sys.stdout.write("📄 Remote Scripts ... ")
    sys.stdout.flush()
    
    if ssh.file_exists(f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor.py'):
        log_colored('green', "✅")
    else:
        log_colored('red', "❌")
        log_colored('red', "FEHLER: Scripts fehlen auf Pi!")
        return False
    
    log_colored('cyan', "")
    log_colored('green', "✅ System-Check erfolgreich")
    log_colored('cyan', "")
    
    return True


def approval_check():
    """FREIGABE-CHECK vor dem Start"""
    log_colored('cyan', "=======================================================================")
    log_colored('cyan', "🚀 FREIGABE-CHECK:")
    log_colored('cyan', "=======================================================================")
    log_colored('cyan', "   ✅ SSH-Verbindung hergestellt")
    log_colored('cyan', "   ✅ Remote-Skripte synchronisiert")
    log_colored('cyan', "   ✅ Alle Dateien vorhanden")
    log_colored('cyan', "=======================================================================")
    log_colored('cyan', "")
    log_colored('green', "✅ SYSTEM BEREIT ZUM START")
    log_colored('cyan', "")


def cleanup_remote_processes(ssh: SSHManager):
    """Bereinigt alte Processes auf Pi"""
    sys.stdout.write("🧹 Alte Kamera-Prozesse bereinigen ... ")
    sys.stdout.flush()
    
    cleanup_cmd = (
        "pkill -f 'start-tcp-preview-watchdog' 2>/dev/null; "
        "sleep 1; "
        "pkill -9 -f 'rpicam' 2>/dev/null; "
        "pkill -9 -f 'unified-camera-monitor.py' 2>/dev/null; "
        "killall -9 python3 2>/dev/null; "
        "pkill -9 -f 'libcamera' 2>/dev/null; "
        "sleep 3"
    )
    
    ssh.exec_command(cleanup_cmd, timeout=15)
    log_colored('green', "✅")


def start_remote_monitor(ssh: SSHManager, mode: str, threshold: float, cooldown: int, trigger: float, audio_threshold: float, duration: int = 0, audio_only: bool = False, fps: int = 0, resolution: str = None, bitrate: int = 0, manual_record: bool = False) -> bool:
    """Startet Remote Monitor auf Pi"""
    if manual_record:
        log_colored('cyan', "🚀 Starte MANUELLE Videoaufnahme...")
    else:
        log_colored('cyan', "🚀 Starte Remote Monitor...")
    
    # Baue Python-Befehl für Pi
    monitor_script = f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor.py'
    
    # Mode-spezifische Parameter
    mode_args = ""
    
    if audio_only:
        # Audio-only Modus überschreibt andere Modi
        mode_args = "--audio-only"
    elif mode == 'slowmo':
        mode_args = "--slowmo"
    elif mode == '4k':
        # 4K-Basisparameter (FPS kann durch --fps überschrieben werden)
        mode_args = "--recording-width 4096 --recording-height 2160"
    elif mode == 'ai-had':
        mode_args = f"--audio-threshold {audio_threshold}"
    elif mode == 'normal':
        mode_args = ""
    
    # Manuelle Aufnahme aktivieren, falls gewünscht
    manual_args = ""
    if manual_record:
        manual_args = "--manual-record --skip-detection"
    
    # Aufnahmedauer hinzufügen, falls angegeben
    duration_args = ""
    if duration > 0:
        duration_seconds = duration * 60  # Konvertiere Minuten zu Sekunden
        duration_args = f"--duration-seconds {duration_seconds}"
    
    # Auflösungs-Presets abbilden
    resolution_args = ""
    if resolution:
        resolution_map = {
            '480p': '--recording-width 854 --recording-height 480',
            '720p': '--recording-width 1280 --recording-height 720',
            '1080p': '--recording-width 1920 --recording-height 1080',
            '4k': '--recording-width 4096 --recording-height 2160',
            '2k': '--recording-width 2560 --recording-height 1440',
        }
        resolution_args = resolution_map.get(resolution, f"--resolution-preset {resolution}")
    
    # FPS-Parameter
    fps_args = ""
    if fps > 0:
        fps_args = f"--recording-fps {fps}"
    
    # Bitrate-Parameter
    bitrate_args = ""
    if bitrate > 0:
        bitrate_args = f"--bitrate {bitrate}k"
    
    # Baue kompletten Befehl
    cmd = (
        f"cd {REMOTE_SCRIPT_DIR} && "
        f"nohup python3 {monitor_script} "
        f"--threshold {threshold} "
        f"--cooldown {cooldown} "
        f"--trigger-duration {trigger} "
        f"{mode_args} "
        f"{manual_args} "
        f"{duration_args} "
        f"{resolution_args} "
        f"{fps_args} "
        f"{bitrate_args} "
        f"> /tmp/unified-camera-monitor.log 2>&1 &"
    )
    
    success, _, err = ssh.exec_command(cmd, timeout=10)
    
    if success:
        log_colored('green', "✅ Remote Monitor gestartet")
        return True
    else:
        log_colored('red', "❌ Konnte Monitor nicht starten")
        if err:
            log_colored('red', f"   Fehler: {err}")
        return False


def show_initial_status(ssh: SSHManager):
    """Zeigt initialen Status vom Monitor"""
    log_colored('cyan', "⏳ Warte auf Monitor-Start...")
    time.sleep(5)
    
    log_colored('cyan', "======================================================================")
    log_colored('cyan', "📊 INITIALER STATUS-REPORT")
    log_colored('cyan', "======================================================================")
    
    # Prüfe Monitor-Prozess
    cmd = "ps aux | grep 'python3.*unified-camera-monitor' | grep -v bash | grep -v grep"
    success, output, _ = ssh.exec_command(cmd)
    
    if success and output:
        parts = output.split()
        pid = parts[1] if len(parts) > 1 else "?"
        cpu = parts[2] if len(parts) > 2 else "?"
        mem = parts[3] if len(parts) > 3 else "?"
        
        log_colored('green', f"✅ Monitor läuft (PID: {pid} | CPU: {cpu}% | RAM: {mem}%)")
    else:
        log_colored('red', "❌ Monitor-Prozess nicht gefunden!")
    
    # Letzte Log-Zeilen
    log_colored('cyan', "")
    log_colored('cyan', "📋 Letzte Log-Zeilen:")
    
    last_logs = ssh.exec_command_safe("tail -10 /tmp/unified-camera-monitor.log 2>/dev/null || echo '(Noch keine Logs)'")
    for line in last_logs.split('\n'):
        if line.strip():
            log_colored('blue', f"   {line}")
    
    log_colored('cyan', "======================================================================")
    log_colored('cyan', "")


class MonitoringSession:
    """Verwaltet alle Monitoring-Threads"""
    
    def __init__(self):
        self.threads = []
        self.running = True
        self.monitors = {
            'log': None,
            'video': None,
            'status': None,
        }
    
    def start(self):
        """Startet alle Monitoring-Dienste"""
        log_colored('cyan', "📊 Starte lokale Monitoring-Dienste...")
        log_colored('cyan', "")
        
        # Event-Log-Follower
        log_monitor = LogMonitor()
        thread = log_monitor.start()
        self.threads.append(thread)
        self.monitors['log'] = log_monitor
        log_colored('green', f"✅ Event-Monitor gestartet (PID: {thread.ident})")
        
        # Video-Watcher
        video_watcher = VideoWatcher()
        thread = video_watcher.start()
        self.threads.append(thread)
        self.monitors['video'] = video_watcher
        log_colored('green', f"✅ Video-Watcher gestartet (PID: {thread.ident})")
        
        # Status-Reporter
        status_reporter = StatusReporter()
        thread = status_reporter.start()
        self.threads.append(thread)
        self.monitors['status'] = status_reporter
        log_colored('green', f"✅ Status-Reporter gestartet (PID: {thread.ident})")
        
        log_colored('cyan', "")
        log_colored('cyan', "======================================================================")
        log_colored('cyan', "✅ SYSTEM BEREIT - Alle Komponenten gestartet")
        log_colored('cyan', "======================================================================")
        log_colored('cyan', "")
        log_colored('cyan', "🔄 Monitoring aktiv - Drücke Ctrl+C zum Beenden")
        log_colored('cyan', "")
    
    def wait(self):
        """Wartet auf Monitoring-Threads"""
        try:
            for thread in self.threads:
                thread.join()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stoppt alle Monitoring-Services"""
        self.running = False
        
        for monitor in self.monitors.values():
            if monitor:
                monitor.stop()
        
        # Warte kurz auf sauberes Herunterfahren
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2)


def signal_handler(signum, frame):
    """Behandelt Ctrl+C"""
    log_colored('yellow', "")
    log_colored('yellow', "🛑 Beende Unified Monitoring System...")
    sys.exit(0)


@click.command()
@click.argument('mode', type=click.Choice(['normal', 'slowmo', '4k', 'ai-had']), default='normal')
@click.option('--threshold', type=float, default=DEFAULT_THRESHOLD, help='Erkennungs-Schwellenwert')
@click.option('--cooldown', type=int, default=DEFAULT_COOLDOWN, help='Cooldown zwischen Aufnahmen (Sekunden)')
@click.option('--trigger', type=float, default=DEFAULT_TRIGGER_DURATION, help='Trigger-Dauer für Erkennung (Sekunden)')
@click.option('--audio-threshold', type=float, default=DEFAULT_AUDIO_THRESHOLD, help='Audio-Schwellenwert für AI-HAD')
@click.option('--duration', type=int, default=0, help='Aufnahmedauer in Minuten (0 = unbegrenzt)')
@click.option('--audio-only', is_flag=True, default=False, help='Nur Audio aufnehmen (kein Video)')
@click.option('--fps', type=int, default=0, help='Framerate (fps): 15, 24, 30, 60, 120')
@click.option('--resolution', type=click.Choice(['480p', '720p', '1080p', '2k', '4k']), default=None, required=False, help='Auflösungs-Preset')
@click.option('--bitrate', type=int, default=0, help='Video-Bitrate in kbps (z.B. 5000, 10000)')
@click.option('--manual-record', is_flag=True, default=False, help='Manuelle Aufnahme - kein Trigger/Erkennung nötig')
def main(mode: str, threshold: float, cooldown: int, trigger: float, audio_threshold: float, duration: int, audio_only: bool, fps: int, resolution: str, bitrate: int, manual_record: bool):
    """
    🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung
    
    Orchestriert die komplette Remote-Kamera-Überwachung.
    
    MODI:
    - normal      Standard-Modus (1920x1080 @ 30fps + Audio)
    - slowmo      Zeitlupen-Modus (1536x864 @ 120fps)
    - 4k          Cinema 4K-Modus (4096x2160 @ 25fps + Audio)
    - ai-had      AI-HAD Modus (1920x1080 @ 30fps + Audio-Erkennung)
    
    BEISPIELE:
    
        # Standard-Modus mit Vogelerkennung
        python3 unified_monitor_client.py normal
        
        # Zeitlupe mit Cooldown-Anpassung
        python3 unified_monitor_client.py slowmo --cooldown 5
        
        # 4K Cinema mit niedriger Bitrate
        python3 unified_monitor_client.py 4k --bitrate 5000 --fps 25
        
        # AI-HAD Modus mit Audio-Threshold
        python3 unified_monitor_client.py ai-had --audio-threshold 0.2
        
        # MANUELLE Aufnahme 30 Minuten ohne Trigger
        python3 unified_monitor_client.py normal --manual-record --duration 30
        
        # MANUELLE HD-Aufnahme 60fps für Hochgeschwindigkeit
        python3 unified_monitor_client.py normal --manual-record --resolution 1080p --fps 60
        
        # MANUELLE 4K Aufnahme mit Custom Bitrate
        python3 unified_monitor_client.py 4k --manual-record --resolution 4k --bitrate 8000 --duration 45
        
        # MANUELLE Audio-only Aufnahme 60 Minuten (Vogelgesang)
        python3 unified_monitor_client.py --manual-record --audio-only --duration 60
        
        # Energiesparmodus: 720p @ 15fps für lange Aufnahmen
        python3 unified_monitor_client.py normal --manual-record --resolution 720p --fps 15 --bitrate 2000
    """
    
    # Signal-Handler für Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Lese Version
    version_file = Path(__file__).parent / 'VERSION'
    version = version_file.read_text().strip() if version_file.exists() else "UNKNOWN"
    
    # Bestimme Audio-Aktivierung basierend auf Modus
    enable_audio = RECORDING_MODES[mode].get('audio', False) or audio_only
    
    # Banner
    show_banner(mode, version)
    show_parameters(threshold, cooldown, trigger, audio_threshold, enable_audio, duration, audio_only, fps, resolution, bitrate, manual_record)
    
    # SSH-Manager
    ssh = get_ssh_manager()
    
    # System-Check
    if not system_check(ssh):
        sys.exit(1)
    
    # Freigabe-Check
    approval_check()
    
    # Bereinigung alter Prozesse
    cleanup_remote_processes(ssh)
    
    # Starte Remote Monitor
    if not start_remote_monitor(ssh, mode, threshold, cooldown, trigger, audio_threshold, duration, audio_only, fps, resolution, bitrate, manual_record):
        sys.exit(1)
    
    # Zeige initialen Status
    show_initial_status(ssh)
    
    # Starte Monitoring-Services
    session = MonitoringSession()
    session.start()
    
    # SPECIAL: Manual-Mode - Nur kurz laufen lassen bis Video synchronisiert
    if manual_record:
        log_colored('yellow', "")
        log_colored('yellow', "⏳ Warte auf Video-Synchronisation...")
        
        # Warte bis Video da ist (duration + Konvertierung + Audio-Merge + rsync-Transfer)
        # Formula: (duration * 2) + 120 = realistische Wartezeit
        # - Aufnahme: duration Minuten  
        # - Konvertierung H264→MP4: ~30-60s
        # - Audio-Merge: ~10-20s  
        # - rsync-Transfer (4K ~500-800MB): ~60-180s
        # - Puffer: +60s
        # Beispiel: 1min (60s) Video = (1 * 2) + 120 = 302 Sekunden (~5 min)
        actual_wait = int(duration * 120 + 120)
        
        log_colored('cyan', f"⏱️  Warte {actual_wait}s auf Sync ({actual_wait//60} Minuten)...")
        log_colored('cyan', f"    Aufnahme→Konvertierung→Audio-Merge→rsync-Transfer")
        time.sleep(actual_wait)
        
        log_colored('green', "✅ Video-Synchronisation abgeschlossen!")
        log_colored('yellow', "")
        log_colored('yellow', "🛑 Manuelle Aufnahme abgeschlossen - Beende System...")
        
        # Cleanup und Exit
        session.stop()
        ssh.close()
        log_colored('yellow', "")
        sys.exit(0)
    else:
        # Warte auf Monitoring
        try:
            session.wait()
        except KeyboardInterrupt:
            pass
    
    # Cleanup
    session.stop()
    ssh.close()
    
    log_colored('yellow', "")
    log_colored('yellow', "🛑 Unified Monitoring System beendet")
    log_colored('yellow', "")


if __name__ == '__main__':
    main()
