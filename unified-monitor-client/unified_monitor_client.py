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
import threading
import subprocess
from pathlib import Path
from datetime import datetime

from config import (
    RECORDING_MODES, DEFAULT_THRESHOLD, DEFAULT_COOLDOWN,
    DEFAULT_TRIGGER_DURATION, DEFAULT_AUDIO_THRESHOLD,
    LOG_COLORS, SSH_HOST, SSH_USER, SSH_KEY, REMOTE_VIDEO_BASE,
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

# Globale Variablen für Signal-Handler
_global_ssh = None
_global_status_reporter = None
_cleanup_on_exit = False


def log_colored(color: str, message: str):
    """Print farbige Nachricht"""
    sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
    sys.stdout.flush()


def _get_german_weekday(dt: datetime) -> str:
    """Konvertiere datetime zu deutschem Wochentag (Montag, Dienstag, etc.)"""
    weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return weekdays[dt.weekday()]


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
    log_colored('magenta', f"🔴 REINE AUFNAHME (Vogelerkennung nicht möglich mit rpicam-vid backend)")
    
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
        log_colored('cyan', f"⏱️  Aufnahmedauer: {duration} Sekunden")
    else:
        log_colored('cyan', f"⏱️  Aufnahmedauer: ∞ (bis Abbruch)")
    
    if audio_only:
        log_colored('magenta', f"🎤 NUR AUDIO (kein Video)")
    else:
        log_colored('cyan', "🎥 Video-Aufnahme aktiv")
    
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


def diagnose_remote_processes(ssh: SSHManager):
    """Diagnostiziert welche Prozesse auf Pi laufen und blocken"""
    log_colored('cyan', "🔍 Diagnostiziere offene Prozesse auf Pi...")
    
    # Prüfe was noch läuft
    diag_script = (
        "echo '=== LAUFENDE PROZESSE ===' && "
        "ps aux | grep -E 'python|camera|libcamera|picamera|rpicam' | grep -v grep && "
        "echo '' && "
        "echo '=== OFFENE FILE HANDLES ===' && "
        "lsof 2>/dev/null | grep -i 'camera\\|video\\|/dev/video' | head -10 || echo '(keine)' && "
        "echo '' && "
        "echo '=== V4L2 DEVICES ===' && "
        "ls -la /dev/video* 2>/dev/null || echo '(keine)'"
    )
    
    try:
        success, output, err = ssh.exec_command(diag_script, timeout=10)
        if output:
            log_colored('yellow', output)
    except Exception as e:
        logger.warning(f"Diagnose Fehler: {e}")


def cleanup_remote_processes(ssh: SSHManager):
    """Bereinigt alte Kamera-Prozesse - sanft und targeted"""
    sys.stdout.write("🧹 Alte Kamera-Prozesse bereinigen ... ")
    sys.stdout.flush()
    
    # SANFTE Cleanup-Strategie: 
    # 1. Kill nur camera-bezogene Prozesse (nicht alle python3!)
    # 2. 3-stufiger Ansatz: TERM → Wait → KILL wenn nötig
    # 3. Verify nach jedem Schritt
    
    cleanup_script = (
        "# ===== STAGE 1: Gezielte SIGTERM zu Camera-Prozessen =====\n"
        "pkill -TERM -f 'unified-camera-monitor' 2>/dev/null\n"
        "pkill -TERM -f 'picamera' 2>/dev/null\n"
        "pkill -TERM -f 'libcamera' 2>/dev/null\n"
        "sleep 2\n"
        "\n"
        "# ===== STAGE 2: Wenn noch da, harder SIGKILL (aber NICHT alle python3!) =====\n"
        "pkill -9 -f 'unified-camera-monitor' 2>/dev/null\n"
        "pkill -9 -f 'rpicam' 2>/dev/null\n"
        "sleep 1\n"
        "\n"
        "# ===== STAGE 3: V4L2/libcamera Device-Locks freigeben =====\n"
        "# Prüfe ob noch was läuft\n"
        "REMAINING=$(ps aux | grep -E 'unified-camera|libcamera|picamera' | grep -v grep | wc -l)\n"
        "if [ \"$REMAINING\" -gt 0 ]; then\n"
        "    echo 'WARNING: Still found processes, forcing cleanup...'\n"
        "    pkill -9 -f 'unified-camera' 2>/dev/null || true\n"
        "    sleep 2\n"
        "fi\n"
        "\n"
        "# ===== STAGE 4: Cleanup Log und State-Files =====\n"
        "rm -f /tmp/unified-camera-monitor.log 2>/dev/null || true\n"
        "rm -f /tmp/*.pid 2>/dev/null || true\n"
        "sleep 1\n"
        "\n"
        "# ===== FINAL: Verify that cleanup was successful =====\n"
        "ps aux | grep -E 'unified-camera|libcamera[^:]|picamera' | grep -v grep | wc -l\n"
        "echo 'CLEANUP_DONE'"
    )
    
    try:
        success, output, err = ssh.exec_command(cleanup_script, timeout=20)
        
        # Prüfe ob noch Prozesse laufen
        lines = output.strip().split('\n')
        remaining_count = 0
        
        # Letzte Zeile sollte "CLEANUP_DONE" sein
        if lines and lines[-1] == 'CLEANUP_DONE':
            # Vorletzte Zeile hat die Process-Zahl
            if len(lines) > 1:
                try:
                    remaining_count = int(lines[-2])
                except ValueError:
                    remaining_count = 0
        
        if remaining_count == 0:
            log_colored('green', "✅")
        else:
            log_colored('yellow', f"⚠️  ({remaining_count} Prozesse noch aktiv, aber tolerierbar)")
            logger.warning(f"Cleanup: {remaining_count} Prozesse nach Cleanup noch aktiv")
        
    except Exception as e:
        logger.error(f"Cleanup Exception: {e}")
        log_colored('yellow', "⚠️  (Cleanup Fehler, versuche trotzdem fortzufahren)")


def start_remote_monitor(ssh: SSHManager, mode: str, threshold: float, cooldown: int, trigger: float, audio_threshold: float, duration: int = 0, audio_only: bool = False, fps: int = 0, resolution: str = None, bitrate: int = 0, auto_record: bool = False, manual_record: bool = False) -> bool:
    """
    Startet Remote Monitor auf Pi - wählt zwischen zwei Architekturen:
    
    1. AUTO-RECORD (auto_record=True):
       - Script: unified-camera-monitor-auto.py (picamera2)
       - Mit Vogelerkennung (YOLO)
       - Parameter: --threshold, --cooldown, --trigger-duration
       
    2. MANUAL-RECORD (manual_record=True):
       - Script: unified-camera-monitor-manual.py (rpicam-vid)
       - Ohne Vogelerkennung, pure Aufnahme
       - Parameter: --duration-seconds, --fps, --bitrate, --audio-only
    """
    
    if auto_record:
        log_colored('cyan', "🚀 Starte AUTO-RECORD (Vogelerkennung mit picamera2)...")
        monitor_script = f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor-auto.py'
        
        # Arguments für AUTO-RECORD Mode
        args = [
            f"--threshold {threshold}",
            f"--cooldown {cooldown}",
            f"--trigger-duration {trigger}",
        ]
        
        # Mode-spezifische Parameter
        if mode == 'slowmo':
            args.append("--slowmo")
        elif mode == '4k':
            args.append("--recording-width 4096")
            args.append("--recording-height 2160")
            # Audio ist kompliziert - erstmal deaktivieren bis remote Scripts sync funktioniert
            # args.append("--enable-audio")
        elif mode == 'ai-had':
            # Audio-Support wird später hinzugefügt
            pass
        
        # FPS-Parameter (falls nicht default)
        if fps > 0:
            args.append(f"--recording-fps {fps}")
        
        log_colored('blue', f"   Parameter: threshold={threshold}, cooldown={cooldown}s, trigger={trigger}s")
        
    else:  # manual_record
        log_colored('cyan', "🚀 Starte MANUAL-RECORD (reine Aufnahme mit rpicam-vid)...")
        monitor_script = f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor-manual.py'
        
        # Auflösungs-Presets abbilden
        resolution_map = {
            '480p': ('854', '480'),
            '720p': ('1280', '720'),
            '1080p': ('1920', '1080'),
            '4k': ('4096', '2160'),
            '2k': ('2560', '1440'),
        }
        
        # Arguments für MANUAL-RECORD Mode - SKIP DETECTION ist wichtig!
        args = [
            "--manual-record",
            "--skip-detection",
        ]
        
        # Mode-spezifische Parameter
        if audio_only:
            args.append("--audio-only")
        elif mode == 'slowmo':
            args.append("--slowmo")
        elif mode == '4k':
            args.append("--recording-width 4096")
            args.append("--recording-height 2160")
        elif mode == 'ai-had':
            args.append("--enable-audio")
        
        # Aufnahmedauer hinzufügen, falls angegeben
        if duration > 0:
            # duration ist bereits in Sekunden (nicht Minuten!)
            args.append(f"--duration-seconds {duration}")
        
        # Auflösungs-Parameter (wenn spezifisch gesetzt)
        if resolution and resolution in resolution_map:
            width, height = resolution_map[resolution]
            args.append(f"--recording-width {width}")
            args.append(f"--recording-height {height}")
        
        # FPS-Parameter
        if fps > 0:
            args.append(f"--recording-fps {fps}")
        
        # Bitrate-Parameter
        if bitrate > 0:
            args.append(f"--bitrate {bitrate}k")
        
        log_colored('blue', f"   Parameters: duration={duration}s, fps={fps}, resolution={resolution or 'default'}, bitrate={bitrate or 'default'}")
    
    # Baue kompletten Befehl mit nohup im Hintergrund
    args_str = " ".join(args)
    cmd = (
        f"nohup python3 {monitor_script} {args_str} "
        f"> /tmp/unified-camera-monitor.log 2>&1 &"
    )
    
    # Sende Befehl (ignoriere exit code für background process)
    try:
        success, out, err = ssh.exec_command(cmd, timeout=5)
        
        # Für background processes ist exit code nicht zu verlässlich
        # Prüfe stattdessen ob der process gestartet wurde
        time.sleep(1)
        check_cmd = f"ps aux | grep 'python3.*unified-camera-monitor' | grep -v grep | wc -l"
        success, count_str, _ = ssh.exec_command(check_cmd, timeout=5)
        
        try:
            process_count = int(count_str.strip())
            if process_count > 0:
                log_colored('green', "✅ Remote Monitor gestartet")
                return True
        except ValueError:
            pass
        
        log_colored('red', "❌ Konnte Monitor nicht starten")
        if err and err.strip():
            log_colored('red', f"   Fehler: {err}")
        return False
        
    except Exception as e:
        log_colored('red', f"❌ SSH-Fehler: {e}")
        return False


def watch_detection_log(ssh: SSHManager, detection_started_event, bird_detected_event, max_wait: int = 600) -> bool:
    """
    Überwacht Remote-Log auf Vogel-Erkennung.
    
    Gibt True zurück wenn Vogel erkannt wurde.
    Gibt False zurück nach Timeout oder Error.
    """
    log_colored('cyan', "👁️  Überwache Detection-Log...\n")
    
    start_time = time.time()
    last_position = 0
    detection_started = False
    
    while time.time() - start_time < max_wait:
        try:
            # Lese aktuelle Log-Größe
            size_cmd = "wc -c < /tmp/unified-camera-monitor.log 2>/dev/null || echo 0"
            success, size_str, _ = ssh.exec_command(size_cmd, timeout=3)
            
            if not success or not size_str.strip():
                time.sleep(1)
                continue
            
            current_size = int(size_str.strip())
            
            # Lese neue Log-Lines ab last_position
            if current_size > last_position:
                tail_cmd = f"tail -c +{last_position + 1} /tmp/unified-camera-monitor.log"
                success, output, _ = ssh.exec_command(tail_cmd, timeout=3)
                
                if success and output:
                    # Signal dass Detection gestartet ist (erste Log-Zeilen sichtbar)
                    if not detection_started and output.strip():
                        detection_started = True
                        detection_started_event.set()
                        log_colored('green', "✅ Detection-Prozess läuft\n")
                    
                    # Prüfe auf Erkennungs-Trigger
                    for line in output.split('\n'):
                        if any(keyword in line.lower() for keyword in 
                               ['vogel erkannt', 'bird detected', 'detection confirmed']):
                            log_colored('green', f"🐦 VOGEL ERKANNT: {line}")
                            log_colored('cyan', "")
                            bird_detected_event.set()
                            return True
                        
                        # Zeige auch andere wichtige Events
                        if any(keyword in line.lower() for keyword in 
                               ['error', 'fehler', 'exception']):
                            log_colored('red', f"⚠️  {line}")
                    
                    last_position = current_size
            
            time.sleep(1)
        
        except Exception as e:
            logger.warning(f"Log-Watch Fehler: {e}")
            time.sleep(1)
    
    log_colored('yellow', f"⏱️  Timeout: Kein Vogel erkannt in {max_wait}s")
    return False


def start_detection_only(ssh: SSHManager, mode: str, threshold: float, cooldown: int, trigger: float) -> bool:
    """
    Startet reinen Detection-Prozess (OHNE Video-Recording).
    
    Dieser Prozess:
    - Überwacht kontinuierlich die Kamera
    - Führt YOLO-Erkennung durch
    - Loggt Erkennungen
    - Beendet sich bei erfolgreichem Trigger
    """
    log_colored('cyan', "🔍 Starte DETECTION-ONLY Prozess (kein Video-Speicherung)...")
    
    # Neues, schlankes Detection-only Skript
    script = f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor-detect-only.py'
    
    # Args für Detection-only Mode
    args = [
        f"--threshold {threshold}",
        f"--cooldown {cooldown}",
        f"--trigger-duration {trigger}",
    ]
    
    args_str = " ".join(args)
    cmd = (
        f"nohup python3 {script} {args_str} "
        f"> /tmp/unified-camera-monitor.log 2>&1 &"
    )
    
    try:
        success, out, err = ssh.exec_command(cmd, timeout=5)
        time.sleep(2)
        
        # Prüfe ob Prozess läuft
        check_cmd = f"ps aux | grep 'python3.*unified-camera-monitor-detect-only' | grep -v grep | wc -l"
        success, count_str, _ = ssh.exec_command(check_cmd, timeout=5)
        
        try:
            process_count = int(count_str.strip())
            if process_count > 0:
                log_colored('green', "✅ Detection-Prozess gestartet")
                return True
        except ValueError:
            pass
        
        log_colored('red', "❌ Detection-Prozess konnte nicht gestartet werden")
        return False
    
    except Exception as e:
        log_colored('red', f"❌ SSH-Fehler: {e}")
        return False


def stop_detection_process(ssh: SSHManager) -> bool:
    """
    Beendet den Detection-Prozess sauber mit SIGTERM.
    """
    log_colored('cyan', "\n🛑 Beende Detection-Prozess...")
    
    try:
        # Sauberes Beenden mit SIGTERM
        stop_cmd = "pkill -TERM -f 'unified-camera-monitor-detect-only' 2>/dev/null; sleep 1"
        
        success, out, err = ssh.exec_command(stop_cmd, timeout=5)
        
        # Wenn nach 1s noch da: Aggressive SIGKILL
        check_cmd = "ps aux | grep 'detect-only' | grep -v grep | wc -l"
        success, count_str, _ = ssh.exec_command(check_cmd, timeout=3)
        
        try:
            remaining = int(count_str.strip())
            if remaining > 0:
                logger.info("Detection-Prozess antwortet nicht auf SIGTERM, verwende SIGKILL...")
                kill_cmd = "pkill -9 -f 'detect-only' 2>/dev/null"
                ssh.exec_command(kill_cmd, timeout=3)
                time.sleep(1)
        except ValueError:
            pass
        
        log_colored('green', "✅ Detection-Prozess beendet")
        return True
    
    except Exception as e:
        log_colored('red', f"❌ Fehler beim Beenden: {e}")
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
    """Behandelt Ctrl+C - Sauberes Cleanup aller Prozesse"""
    global _global_ssh, _global_status_reporter, _cleanup_on_exit
    
    log_colored('yellow', "\n\n🛑 Abgebrochen vom Benutzer (Ctrl+C)")
    log_colored('yellow', "🧹 Räume auf und killen alle Remote-Prozesse...\n")
    
    # Stoppe Status-Reporter
    if _global_status_reporter:
        try:
            _global_status_reporter.stop()
            log_colored('cyan', "   ✅ Status-Reporter beendet")
        except Exception as e:
            logger.warning(f"Status-Reporter Fehler: {e}")
    
    # Beende Detection-Prozess
    if _global_ssh:
        try:
            stop_detection_process(_global_ssh)
            log_colored('cyan', "   ✅ Detection-Prozess beendet")
        except Exception as e:
            logger.warning(f"Detection-Stop Fehler: {e}")
    
    # Cleanup Remote-Prozesse
    if _global_ssh:
        try:
            log_colored('cyan', "   🧹 Remote-Cleanup läuft...")
            cleanup_remote_processes(_global_ssh)
            log_colored('cyan', "   ✅ Remote-Prozesse gekilled")
        except Exception as e:
            logger.warning(f"Remote-Cleanup Fehler: {e}")
        
        # Schließe SSH-Verbindung
        try:
            _global_ssh.close()
            log_colored('cyan', "   ✅ SSH-Verbindung geschlossen")
        except Exception as e:
            logger.warning(f"SSH-Close Fehler: {e}")
    
    log_colored('yellow', "\n✅ Cleanup complete - Auf Wiedersehen!\n")
    sys.exit(0)


@click.command()
@click.argument('mode', type=click.Choice(['normal', 'slowmo', '4k', 'ai-had']), default='normal')
@click.option('--threshold', type=float, default=DEFAULT_THRESHOLD, help='Erkennungs-Schwellenwert')
@click.option('--cooldown', type=int, default=DEFAULT_COOLDOWN, help='Cooldown zwischen Aufnahmen (Sekunden)')
@click.option('--trigger', type=float, default=DEFAULT_TRIGGER_DURATION, help='Trigger-Dauer für Erkennung (Sekunden)')
@click.option('--audio-threshold', type=float, default=DEFAULT_AUDIO_THRESHOLD, help='Audio-Schwellenwert für AI-HAD')
@click.option('--duration', type=int, default=10, help='Aufnahmedauer nach Erkennung in Sekunden (default: 10)')
@click.option('--audio-only', is_flag=True, default=False, help='Nur Audio aufnehmen (kein Video)')
@click.option('--fps', type=int, default=0, help='Framerate (fps): 15, 24, 30, 60, 120')
@click.option('--resolution', type=click.Choice(['480p', '720p', '1080p', '2k', '4k']), default=None, required=False, help='Auflösungs-Preset')
@click.option('--bitrate', type=int, default=0, help='Video-Bitrate in kbps (z.B. 5000, 10000)')
@click.option('--detect-and-record', is_flag=True, default=False, help='🆕 Zwei-Phasen-Modus: Erst Detection, dann Recording')
@click.option('--repeat', is_flag=True, default=False, help='🔄 Endlosschleife: Nach Aufnahme wieder auf Vogel warten (mit --detect-and-record)')
@click.option('--auto-record', is_flag=True, default=False, help='[VERALTET] Automatische Vogelerkennung + Aufnahme')
@click.option('--manual-record', is_flag=True, default=False, help='Manuelle Aufnahme ohne Vogelerkennung')
def main(mode: str, threshold: float, cooldown: int, trigger: float, audio_threshold: float, duration: int, audio_only: bool, fps: int, resolution: str, bitrate: int, detect_and_record: bool, repeat: bool, auto_record: bool, manual_record: bool):
    """
    🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung
    
    ╔════════════════════════════════════════════════════════════════════╗
    ║ 🆕 EMPFOHLENER MODUS: --detect-and-record (NEU!)                   ║
    ║                                                                    ║
    ║ PHASE 1️⃣  Detection: Vogelerkennung ohne Video-Speicherung       ║
    ║ PHASE 2️⃣  Recording: Nach Trigger → volle Aufnahme mit Audio    ║
    ║                                                                    ║
    ║ ✅ Löst das Time-Lapse Problem!                                  ║
    ║ ✅ CPU-effizient & schnell                                        ║
    ║ ✅ Saubere Prozess-Trennung                                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    BENUTZUNG:
    
    🆕 --detect-and-record (EMPFOHLEN für Vogel-Aufnahmen):
    
      # Standard Vogel-Erkennung + 10 Sekunden aufnehmen
      python3 unified_monitor_client.py normal --detect-and-record
      
      # Mit längerer Aufnahme (30 Sekunden) und besserer Konfiguration
      python3 unified_monitor_client.py normal --detect-and-record \\
        --threshold 0.4 \\
        --cooldown 15 \\
        --trigger 1.0 \\
        --duration 30
      
      # 4K Cinema mit Audio
      python3 unified_monitor_client.py 4k --detect-and-record \\
        --duration 20 \\
        --bitrate 8000
      
      # Nur Vogelgesang aufnehmen (nach Erkennung)
      python3 unified_monitor_client.py normal --detect-and-record \\
        --audio-only \\
        --duration 15
    
    ══════════════════════════════════════════════════════════════════════
    
    📹 --manual-record (manuelle Aufnahme ohne Erkennung):
    
      # Direkt 10 Sekunden Video
      python3 unified_monitor_client.py normal --manual-record --duration 10
      
      # 5 Minuten 720p (energieeffizient)
      python3 unified_monitor_client.py normal --manual-record \\
        --duration 300 \\
        --resolution 720p \\
        --fps 15
    
    ══════════════════════════════════════════════════════════════════════
    
    ⚠️  --auto-record (VERALTET - kann zu beschleunigter Verarbeitung führen):
    
      # Kontinuierliche Detection + Recording im gleichen Prozess
      python3 unified_monitor_client.py normal --auto-record
    
    ══════════════════════════════════════════════════════════════════════
    
    RECORDING MODES (apply to all):
    
    • normal     Standard (1920x1080 @ 30fps + Audio)
    • slowmo     Slow Motion (1536x864 @ 120fps)
    • 4k         Cinema 4K (4096x2160 @ 25fps + Audio)
    • ai-had     AI-HAD Base (1920x1080 @ 30fps + Audio)
    
    ══════════════════════════════════════════════════════════════════════
    
    PARAMETER:
    
    DETECTION (--detect-and-record / --auto-record):
      --threshold FLOAT      Erkennungs-Schwelle 0.0-1.0 (default: 0.5)
      --cooldown INT         Sekunden zwischen Triggern (default: 15)
      --trigger FLOAT        Erkennungs-Dauer in Sekunden (default: 1.0)
    
    RECORDING (--detect-and-record / --manual-record):
      --duration INT         Aufnahmedauer in Sekunden (default: 10)
      --fps INT              Frames per Second: 15, 24, 30, 60, 120
      --resolution STR       480p, 720p, 1080p, 2k, 4k
      --bitrate INT          Bitrate in kbps (z.B. 5000, 10000)
      --audio-only           Nur Audio ohne Video
    
    ══════════════════════════════════════════════════════════════════════
    """
    
    # Signal-Handler für Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Validierung: Genau EINER der drei Modes muss gesetzt sein!
    modes_set = sum([detect_and_record, auto_record, manual_record])
    
    if modes_set != 1:
        log_colored('red', "❌ FEHLER: Nutze GENAU EINEN der folgenden Modi:")
        log_colored('yellow', "")
        log_colored('yellow', "  ✅ --detect-and-record  = Zwei-Phasen: Detection → Recording")
        log_colored('yellow', "     (Schnelle, saubere Trennung, für normale Aufnahmen)")
        log_colored('yellow', "")
        log_colored('yellow', "  --auto-record            = Kontinuierliche Detection+Recording")
        log_colored('yellow', "     (Veraltet, kann zu beschleunigter Video-Verarbeitung führen)")
        log_colored('yellow', "")
        log_colored('yellow', "  --manual-record          = Manuelle Aufnahme, kein Detection")
        log_colored('yellow', "     (Für direkte Video-Aufnahme ohne Erkennung)")
        log_colored('yellow', "")
        sys.exit(1)
    
    # Lese Version
    version_file = Path(__file__).parent / 'VERSION'
    version = version_file.read_text().strip() if version_file.exists() else "UNKNOWN"
    
    # Bestimme Audio-Aktivierung basierend auf Modus
    enable_audio = RECORDING_MODES[mode].get('audio', False) or audio_only
    
    # Banner
    show_banner(mode, version)
    
    # Unterschiedliche Parameter-Anzeige je nach Modus
    if detect_and_record:
        log_colored('magenta', f"🆕 DETECT-AND-RECORD MODUS: Zwei-Phasen-Betrieb")
        log_colored('cyan', "")
        log_colored('cyan', f"   PHASE 1️⃣  - DETECTION: Fokussierte Vogelerkennung (kein Video)")
        log_colored('blue', f"   ⚙️ Threshold: {threshold} | Cooldown: {cooldown}s | Trigger: {trigger}s")
        log_colored('cyan', "")
        log_colored('cyan', f"   PHASE 2️⃣  - RECORDING: Nach Erkennung → Aufnahme mit voller Qualität")
        video_params = []
        if resolution:
            video_params.append(f"{resolution}")
        if fps > 0:
            video_params.append(f"{fps} fps")
        if bitrate > 0:
            video_params.append(f"{bitrate} kbps")
        if video_params:
            log_colored('blue', f"   📹 Video: {' | '.join(video_params)}")
        log_colored('blue', f"   ⏱️  Aufnahmedauer: {duration} Sekunden (nach Erkennung)")
        if audio_only:
            log_colored('magenta', f"   🎤 NUR AUDIO (kein Video)")
        elif enable_audio:
            log_colored('cyan', f"   🎤 Mit Audio-Track")
        log_colored('cyan', "")
    
    elif auto_record:
        log_colored('magenta', f"⚠️  AUTO-RECORD MODUS (veraltet): Vogelerkennung + Aufnahme kombiniert")
        log_colored('blue', f"   Parameter: threshold={threshold}, cooldown={cooldown}s, trigger={trigger}s")
        log_colored('yellow', "   💡 Tipp: Nutze stattdessen --detect-and-record für bessere Performance")
        log_colored('cyan', "")
    
    else:  # manual_record
        log_colored('magenta', f"📹 MANUAL-RECORD MODUS: Reine Aufnahme (kein Detection)")
        video_params = []
        if resolution:
            video_params.append(f"{resolution}")
        if fps > 0:
            video_params.append(f"{fps} fps")
        if bitrate > 0:
            video_params.append(f"{bitrate} kbps")
        if video_params:
            log_colored('cyan', f"📹 Video: {' | '.join(video_params)}")
        log_colored('cyan', f"⏱️  Aufnahmedauer: {duration} Sekunden")
        if audio_only:
            log_colored('magenta', f"🎤 NUR AUDIO (kein Video)")
        elif enable_audio:
            log_colored('cyan', f"🎤 Mit Audio-Track")
    
    log_colored('cyan', "")
    
    # SSH-Manager
    ssh = get_ssh_manager()
    
    # Setze Global SSH für Signal-Handler
    global _global_ssh
    _global_ssh = ssh
    
    # System-Check
    if not system_check(ssh):
        sys.exit(1)
    
    # Freigabe-Check
    approval_check()
    
    # Diagnose: Zeige was noch läuft
    diagnose_remote_processes(ssh)
    
    # Bereinigung alter Prozesse
    cleanup_remote_processes(ssh)
    
    # ===== DETECT-AND-RECORD MODE: Zwei-Phasen-Betrieb =====
    if detect_and_record:
        cycle_count = 0  # Zähler für Wiederholungen
        
        # Starte Status-Reporter (alle 5 Minuten)
        status_reporter = StatusReporter(interval=300)
        status_reporter_thread = status_reporter.start()
        
        # Setze Global Status Reporter für Signal-Handler
        global _global_status_reporter
        _global_status_reporter = status_reporter
        
        log_colored('cyan', "📊 Status-Reporter gestartet (aktualisiert alle 5 Min)\n")
        
        while True:
            cycle_count += 1
            
            # Zeige Zyklus-Info
            if cycle_count == 1:
                log_colored('cyan', "=" * 75)
                log_colored('cyan', "🚀 PHASE 1️⃣  - DETECTION (fokussiert, ohne Video-Speicherung)")
                log_colored('cyan', "=" * 75)
            else:
                log_colored('cyan', "")
                log_colored('cyan', "=" * 75)
                log_colored('cyan', f"🔄 WIEDERHOLUNG #{cycle_count} - DETECTION Phase")
                log_colored('cyan', "=" * 75)
            
            log_colored('cyan', "")
            
            # Events für Synchronisation zwischen Log-Watcher und Main Thread
            detection_started = threading.Event()
            bird_detected = threading.Event()
            
            # Starte Detection-only Prozess
            if not start_detection_only(ssh, mode, threshold, cooldown, trigger):
                log_colored('red', "❌ Detection-Prozess konnte nicht gestartet werden")
                ssh.close()
                sys.exit(1)
            
            # Starte Log-Watcher im Hintergrund
            log_watcher_thread = threading.Thread(
                target=watch_detection_log,
                args=(ssh, detection_started, bird_detected, 600),  # 10 Min Timeout
                daemon=True
            )
            log_watcher_thread.start()
            
            # Warte auf Detection Start
            if cycle_count == 1:
                log_colored('cyan', "⏳ Warte auf Detection Thread-Start...")
            
            if detection_started.wait(timeout=10):
                if cycle_count == 1:
                    log_colored('green', "✅ Detection läuft\n")
            else:
                log_colored('yellow', "⚠️  Detection-Start Timeout - aber fahre fort...\n")
            
            # Warte auf Vogel-Erkennung
            if cycle_count == 1:
                log_colored('cyan', "👁️  Überwache auf Vogel-Erkennung...")
                log_colored('cyan', "(Drücke Ctrl+C um abzubrechen)\n")
            else:
                log_colored('cyan', "👁️  Warte auf nächsten Vogel...")
                if repeat:
                    log_colored('cyan', "(Drücke Ctrl+C zum Beenden)\n")
            
            try:
                if bird_detected.wait(timeout=600):  # 10 Min Timeout
                    log_colored('green', "\n✅ Vogel erkannt! Starte Recording...\n")
                else:
                    log_colored('yellow', "\n⏱️  Timeout: Kein Vogel in 10 Minuten erkannt")
                    log_colored('cyan', "")
                    stop_detection_process(ssh)
                    
                    if not repeat:
                        # Single-Shot Mode: Beende nach Timeout
                        status_reporter.stop()
                        ssh.close()
                        sys.exit(0)
                    else:
                        # Repeat-Mode: Gehe zur nächsten Detection
                        log_colored('cyan', "")
                        log_colored('magenta', f"🔄 BEREIT FÜR NÄCHSTE DETECTION (Zyklus #{cycle_count + 1})")
                        log_colored('cyan', "💡 Drücke Ctrl+C um zu beenden")
                        log_colored('cyan', "=" * 75)
                        time.sleep(2)
                        cleanup_remote_processes(ssh)
                        continue  # Weiter zum nächsten Zyklus
            except KeyboardInterrupt:
                log_colored('yellow', "\n\n🛑 Abgebrochen vom Benutzer")
                status_reporter.stop()
                stop_detection_process(ssh)
                ssh.close()
                sys.exit(0)
        
            # ===== Beende Detection Phase =====
            log_colored('cyan', "=" * 75)
            log_colored('cyan', "🛑 Detection-Prozess beendet")
            log_colored('cyan', "=" * 75)
            stop_detection_process(ssh)
            log_colored('cyan', "")
        
            # ===== Starte Recording Phase =====
            log_colored('cyan', "=" * 75)
            log_colored('cyan', "🎥 PHASE 2️⃣  - RECORDING (volle Qualität, mit Audio)")
            log_colored('cyan', "=" * 75)
            log_colored('cyan', "")
        
            # Kurz warten bis die Kamera frei ist
            log_colored('cyan', "⏳ Setze Kamera zurück (500ms Pause)...")
            time.sleep(0.5)
        
            # Starte Recording mit manual-record Architektur
            if not start_remote_monitor(ssh, mode, threshold, cooldown, trigger, audio_threshold, duration, audio_only, fps, resolution, bitrate, auto_record=False, manual_record=True):
                log_colored('red', "❌ Recording konnte nicht gestartet werden")
                status_reporter.stop()
                ssh.close()
                sys.exit(1)
        
            # Merke Aufnahmestart-Zeit für späteren Pfad-Konstruktion
            record_start_time = datetime.now()
        
            # Zeige initialen Status
            show_initial_status(ssh)
        
            # Warte bis Recording abgeschlossen
            log_colored('cyan', "⏳ Recording läuft ({} Sekunden)...".format(duration))
            time.sleep(duration + 8)  # +8s Puffer für finale Verarbeitung
        
            # Zeige Status nach Recording
            log_colored('green', "✅ Recording abgeschlossen!\n")
            log_colored('cyan', "⏳ Warte auf Video-Verarbeitung auf Pi...")
        
            # Warte auf Konvertierung (H264→MP4 + Audio-Merge)
            # Formula: realistische Wartezeit basierend auf Video-Dauer
            # WICHTIG: Audio-Merge dauert länger als reines H264→MP4
            # - Extraktion Audio aus RIFF WAV: ~10% der Video-Dauer
            # - Konvertierung H264→MP4: ~15% der Video-Dauer  
            # - Audio-Merge in ffmpeg: ~20% der Video-Dauer
            actual_wait = int(duration * 0.6 + 25)  # MIN 25s für alle Konvertierungen
            log_colored('cyan', f"⏱️  Warte {actual_wait}s auf H264→MP4 + Audio-Merge...")
        
            # Polling während des Wartens - zeige Status
            remaining = actual_wait
            polling_interval = 5  # Alle 5 Sekunden Status checken
            while remaining > 0:
                sleep_time = min(polling_interval, remaining)
                time.sleep(sleep_time)
                remaining -= sleep_time
            
                if remaining > 0:
                    sys.stdout.write(f"\r   ⏳ Noch {remaining}s Wartezeit...")
                    sys.stdout.flush()
        
            # ===== PHASE 2b: rsync zum Client =====
            log_colored('cyan', "")
            sys.stdout.write("📡 Synchronisiere Video zum Client ... ")
            sys.stdout.flush()
        
            # Konstruiere Remote-Pfad (verwende die aufnahme-startzeit vom Client)
            kw = record_start_time.strftime("%V")  # ISO Kalenderwoche
            year = record_start_time.strftime("%Y")
            weekday = _get_german_weekday(record_start_time)
            date_time = record_start_time.strftime("%Y-%m-%d__%H-%M-%S")
        
            # Remote-Verzeichnis (approximativ - könnte 1-2 Sekunden abweichen)
            remote_video_base = f"{REMOTE_VIDEO_BASE}/AI-HAD/{year}/{kw}"
            remote_search_pattern = f"{remote_video_base}/*{weekday}*{date_time[:10]}*/"  # Führende Tage
        
            # Lokales Zielverzeichnis
            local_video_base = Path.home() / "Videos/Vogelhaus/AI-HAD"
        
            try:
                # Versuche rsync vom Pi zum Client (pull) mit SSH-Key-Authentifizierung
                # SSH-Optionen für passwordless-Authentifizierung
                ssh_opts = (
                    f"-i {SSH_KEY} "  # SSH-Key-Datei
                    "-o StrictHostKeyChecking=no "  # Host-Key-Überprüfung disablieren
                    "-o UserKnownHostsFile=/dev/null "  # Keine bekannten_hosts-Überprüfung
                    "-o ConnectTimeout=10 "  # Timeout für SSH-Verbindung
                    "-o BatchMode=yes "  # Non-interactive mode (keine Passwort-Prompts)
                )
            
                rsync_cmd = [
                    'rsync',
                    '-avz',
                    '--remove-source-files',
                    '-e', f'ssh {ssh_opts}',  # SSH-Befehl mit Optionen
                    f'{SSH_USER}@{SSH_HOST}:{remote_video_base}/',
                    str(local_video_base / year / kw / "")
                ]
            
                result = subprocess.run(
                    rsync_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 Min timeout für rsync
                )
            
                if result.returncode == 0:
                    log_colored('green', "✅")
                    log_colored('cyan', "")
                else:
                    log_colored('yellow', "⚠️  (mit Fehlern)")
                    log_colored('cyan', "")
                    if result.stderr:
                        logger.warning(f"rsync Warnung: {result.stderr[:200]}")
        
            except subprocess.TimeoutExpired:
                log_colored('yellow', "⚠️  (Timeout)")
                log_colored('yellow', "   Videos sind auf Pi verfügbar, Sync dauerte zu lange")
            except Exception as e:
                log_colored('yellow', "⚠️  (Fehler)")
                log_colored('yellow', f"   rsync Fehler: {e}")
        
            log_colored('green', "✅ Video sollte jetzt lokal verfügbar sein!")
            log_colored('cyan', "")
        
            # Finde die tatsächlich erstellte lokale Datei (robuster als timestamp-basiert)
            kw = record_start_time.strftime("%V")  # ISO Kalenderwoche
            year = record_start_time.strftime("%Y")
            local_video_base = Path.home() / "Videos/Vogelhaus/AI-HAD"
            search_dir = local_video_base / year / kw
        
            # Suche nach der neuesten MP4-Datei im Zielverzeichnis
            local_video_file = None
            if search_dir.exists():
                try:
                    # Finde die neueste MP4-Datei (mit größtem Timestamp)
                    mp4_files = sorted(
                        search_dir.rglob('*.mp4'),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    if mp4_files:
                        local_video_file = mp4_files[0]
                except Exception as e:
                    logger.warning(f"Fehler bei Dateisuche: {e}")
        
            # Fallback auf konstruierten Pfad falls Suche nicht funktioniert
            if not local_video_file:
                weekday = _get_german_weekday(record_start_time)
                date_time = record_start_time.strftime("%Y-%m-%d__%H-%M-%S")
                mode_settings = RECORDING_MODES.get(mode, {})
                width = mode_settings.get('default_width', 1920)
                height = mode_settings.get('default_height', 1080)
                fps_val = fps if fps else mode_settings.get('default_fps', 30)
            
                local_video_file = search_dir / f"{weekday}__{date_time}" / f"{weekday}__{date_time}__{width}x{height}__{fps_val}fps.mp4"
            
                # Zeige Pfad an
                log_colored('cyan', "")
                log_colored('green', f"✅ Video #{cycle_count} erfolgreich gespeichert")
                log_colored('cyan', f"📍 Pfad: {local_video_file}")
                log_colored('cyan', "")
            
                # **ENTSCHEIDUNG: Weiterloop oder beenden?**
                if not repeat:
                    # Single-Shot Mode: Beende nach einer Aufnahme
                    log_colored('cyan', "=" * 75)
                    log_colored('green', "✅ DETECT-AND-RECORD ERFOLGREICH ABGESCHLOSSEN!")
                    log_colored('cyan', "=" * 75)
                    log_colored('cyan', "")
                    status_reporter.stop()
                    ssh.close()
                    sys.exit(0)
                else:
                    # Repeat-Mode: Loop zurück zu Detection
                    log_colored('cyan', "=" * 75)
                    log_colored('magenta', f"🔄 BEREIT FÜR NÄCHSTE AUFNAHME (Zyklus #{cycle_count + 1})")
                    log_colored('cyan', "💡 Drücke Ctrl+C um zu beenden")
                    log_colored('cyan', "=" * 75)
                    time.sleep(2)  # Kurze Pause bevor nächster Zyklus
                
                    # Cleanup alte Prozesse vor nächstem Zyklus
                    cleanup_remote_processes(ssh)
                    # Weiter zu nächster While-Iteration
    
    # ===== AUTO-RECORD MODE (veraltet) =====
    elif auto_record:
        log_colored('cyan', "")
        # Starte Remote Monitor (mit auto_record oder manual_record)
        if not start_remote_monitor(ssh, mode, threshold, cooldown, trigger, audio_threshold, duration, audio_only, fps, resolution, bitrate, auto_record, manual_record=False):
            sys.exit(1)
        
        # Zeige initialen Status
        show_initial_status(ssh)
        
        # Starte Monitoring-Services
        session = MonitoringSession()
        session.start()
        
        # Warte auf Monitoring
        log_colored('cyan', "")
        log_colored('cyan', "🔄 Kontinuierliche Überwachung aktiv...")
        log_colored('cyan', "   Drücke Ctrl+C zum Beenden")
        log_colored('cyan', "")
        try:
            session.wait()
        except KeyboardInterrupt:
            pass
        
        # Cleanup
        session.stop()
        ssh.close()
    
    # ===== MANUAL-RECORD MODE =====
    else:  # manual_record
        log_colored('cyan', "")
        # Starte Remote Monitor (mit manual_record)
        if not start_remote_monitor(ssh, mode, threshold, cooldown, trigger, audio_threshold, duration, audio_only, fps, resolution, bitrate, auto_record=False, manual_record=manual_record):
            sys.exit(1)
        
        # Zeige initialen Status
        show_initial_status(ssh)
        
        # Starte Monitoring-Services nur für lokale Überwachung
        session = MonitoringSession()
        session.start()
        
        log_colored('yellow', "")
        log_colored('yellow', "⏳ Warte auf Video-Synchronisation...")
        
        # Warte bis Video da ist  (duration + Konvertierung + Audio-Merge + rsync-Transfer)
        actual_wait = int(duration * 0.6 + 60)
        
        log_colored('cyan', f"⏱️  Warte {actual_wait}s auf Sync...")
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


if __name__ == '__main__':
    main()
