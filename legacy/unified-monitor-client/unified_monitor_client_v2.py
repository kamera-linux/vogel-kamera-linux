#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vogel-Kamera-Linux - Neue Pipeline-basierte Version mit Threads

EINFACHER EINSTIEGSPUNKT mit neuer Architektur:

Demonstriert die neue Thread-basierte Pipeline:
- Kontinuierliche Detection
- Asynchrone Recording-Verarbeitung
- Parallele Konvertierung
- Asynchrone Datei-Synchronisation

Nutzung:
    python3 unified_monitor_client_v2.py normal --detect-and-record --detect-hybrid --repeat
"""

import sys
import time
import threading
from pathlib import Path
from datetime import datetime

# Import der neuen Pipeline
from camera_pipeline import CameraPipeline, RecordingJob, DetectionEvent, JobStatus

# SSH Manager (aus bestehendem Code)
from ssh_manager import get_ssh_manager

# Farben für ausgabе
LOG_COLORS = {
    'reset': '\033[0m',
    'cyan': '\033[96m',
    'green': '\033[92m',
    'red': '\033[91m',
    'yellow': '\033[93m',
    'magenta': '\033[95m',
    'blue': '\033[94m',
}


def log_colored(color: str, message: str):
    """Print farbige Nachricht"""
    sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
    sys.stdout.flush()


class VogelKameraV2:
    """
    Neue Version mit Thread-basiertem Pipeline-System
    
    Workflow:
    1. Detection Thread läuft ständig → überwacht auf Vögel
    2. Wenn Vogel erkannt → RecordingJob in Queue
    3. Recording Thread verarbeitet Jobs asynchron
    4. Conversion Thread konvertiert H364→MP4 parallel
    5. Sync Thread überträgt Dateien kontinuierlich
    
    Vorteil: Alle Prozesse laufen parallel, nicht sequenziell!
    """

    def __init__(self,
                 ssh_host: str = 'raspberrypi-5-ai-had',
                 ssh_user: str = 'roimme',
                 ssh_key: str = '~/.ssh/id_rsa_ai-had',
                 threshold: float = 0.6,
                 duration: int = 60,
                 resolution: str = '2k',
                 fps: int = 30):
        
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_key = Path(ssh_key).expanduser()
        
        self.threshold = threshold
        self.duration = duration
        self.resolution = resolution
        self.fps = fps
        
        # SSH Manager
        self.ssh = get_ssh_manager(ssh_host, ssh_user, self.ssh_key)
        
        # Pipeline
        self.pipeline = CameraPipeline(self.ssh)
        
        # Job Counter
        self.job_counter = 0
        
        # Cleanup Event
        self.stop_event = threading.Event()

    def start(self):
        """Starte das System"""
        try:
            log_colored('cyan', '\n' + '=' * 75)
            log_colored('cyan', '🚀 VOGEL-KAMERA-LINUX v2 - THREAD-BASIERTES SYSTEM')
            log_colored('cyan', '=' * 75 + '\n')
            
            # Verbinde SSH
            if not self.ssh.connect():
                log_colored('red', '❌ SSH-Verbindung fehlgeschlagen')
                return False
            
            log_colored('green', '✅ SSH-Verbindung erfolgreich\n')
            
            # Starte Pipeline
            self.pipeline.start()
            
            # Hauptschleife
            self._event_loop()
            
            return True
            
        except KeyboardInterrupt:
            log_colored('yellow', '\n\n🛑 Abgebrochen vom Benutzer')
            self.stop()
        
        except Exception as e:
            log_colored('red', f'❌ Fehler: {e}')
            import traceback
            traceback.print_exc()
            self.stop()
            return False

    def _event_loop(self):
        """Hauptverarbeitungsschleife"""
        log_colored('cyan', '📊 Überwache auf Ereignisse...')
        log_colored('cyan', '   Detection → Recording → Conversion → Sync\n')
        
        stats_counter = 0
        
        while not self.stop_event.is_set():
            try:
                # Alle 10 Sekunden: Gebe Status aus
                if stats_counter % 5 == 0:
                    stats = self.pipeline.get_stats()
                    log_colored('blue', f'📈 Queue Status:')
                    log_colored('blue', f'   Detection: {stats["detection_queue_size"]} | '
                              f'Recording: {stats["recording_queue_size"]} | '
                              f'Conversion: {stats["conversion_queue_size"]} | '
                              f'Sync: {stats["sync_queue_size"]}')
                
                stats_counter += 1
                time.sleep(2)  # Check alle 2 Sekunden
                
            except Exception as e:
                log_colored('red', f'❌ Event Loop Error: {e}')
                time.sleep(5)

    def stop(self):
        """Stoppe das System sauber"""
        log_colored('yellow', '🛑 Fahre System herunter...')
        
        self.stop_event.set()
        self.pipeline.stop()
        
        if self.ssh:
            self.ssh.close()
        
        log_colored('green', '✅ System gestoppt')


def main():
    """Haupteinstiegspunkt"""
    
    # Einfache Konfiguration - kann später zu Click erweitert werden
    system = VogelKameraV2(
        ssh_host='raspberrypi-5-ai-had',
        ssh_user='roimme',
        ssh_key='~/.ssh/id_rsa_ai-had',
        threshold=0.6,
        duration=60,
        resolution='2k',
        fps=30
    )
    
    success = system.start()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
