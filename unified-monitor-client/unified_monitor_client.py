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


def show_parameters(threshold: float, cooldown: int, trigger: float, audio_threshold: float, enable_audio: bool):
    """Zeigt Monitor-Parameter"""
    log_colored('blue', f"⚙️  Threshold: {threshold} | Cooldown: {cooldown}s | Trigger: {trigger}s")
    if enable_audio:
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


def start_remote_monitor(ssh: SSHManager, mode: str, threshold: float, cooldown: int, trigger: float, audio_threshold: float) -> bool:
    """Startet Remote Monitor auf Pi"""
    log_colored('cyan', "🚀 Starte Remote Monitor...")
    
    # Baue Python-Befehl für Pi
    monitor_script = f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor.py'
    
    # Mode-spezifische Parameter
    mode_args = ""
    
    if mode == 'slowmo':
        mode_args = "--slowmo"
    elif mode == '4k':
        mode_args = "--recording-width 4096 --recording-height 2160 --recording-fps 25 --enable-audio"
    elif mode == 'ai-had':
        mode_args = f"--enable-audio --audio-threshold {audio_threshold}"
    elif mode == 'normal':
        mode_args = "--enable-audio"
    
    # Baue kompletten Befehl
    cmd = (
        f"cd {REMOTE_SCRIPT_DIR} && "
        f"nohup python3 {monitor_script} "
        f"--threshold {threshold} "
        f"--cooldown {cooldown} "
        f"--trigger-duration {trigger} "
        f"{mode_args} "
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
def main(mode: str, threshold: float, cooldown: int, trigger: float, audio_threshold: float):
    """
    🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung
    
    Orchestriert die komplette Remote-Kamera-Überwachung.
    
    MODI:
    - normal      Standard-Modus (1920x1080 @ 30fps + Audio)
    - slowmo      Zeitlupen-Modus (1536x864 @ 120fps)
    - 4k          Cinema 4K-Modus (4096x2160 @ 25fps + Audio)
    - ai-had      AI-HAD Modus (1920x1080 @ 30fps + Audio-Erkennung)
    
    BEISPIELE:
    
        python3 unified_monitor_client.py slowmo
        
        python3 unified_monitor_client.py 4k --cooldown 5
        
        python3 unified_monitor_client.py ai-had --audio-threshold 0.2
    """
    
    # Signal-Handler für Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Lese Version
    version_file = Path(__file__).parent / 'VERSION'
    version = version_file.read_text().strip() if version_file.exists() else "UNKNOWN"
    
    # Bestimme Audio-Aktivierung basierend auf Modus
    enable_audio = RECORDING_MODES[mode].get('audio', False)
    
    # Banner
    show_banner(mode, version)
    show_parameters(threshold, cooldown, trigger, audio_threshold, enable_audio)
    
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
    if not start_remote_monitor(ssh, mode, threshold, cooldown, trigger, audio_threshold):
        sys.exit(1)
    
    # Zeige initialen Status
    show_initial_status(ssh)
    
    # Starte Monitoring-Services
    session = MonitoringSession()
    session.start()
    
    # Warte auf Monitoring
    try:
        session.wait()
    except KeyboardInterrupt:
        pass
    finally:
        session.stop()
        ssh.close()
        
        log_colored('yellow', "")
        log_colored('yellow', "🛑 Unified Monitoring System beendet")
        log_colored('yellow', "")


if __name__ == '__main__':
    main()
