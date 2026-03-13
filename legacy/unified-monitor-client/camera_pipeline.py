#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera Pipeline - Thread-basierte Verarbeitung für Vogel-Erkennung und Recording

Modular structured threads:
- DetectionThread: Kontinuierliche Vogelerkennung
- RecordingThread: Verarbeitet Aufnahmen aus Queue
- ConversionThread: Konvertiert H264→MP4 asynchron
- SyncThread: Überträgt Dateien zum Client asynchron
- MonitorThread: Überwacht Systemstatus

Alle Threads sind thread-safe über queue.Queue und threading.Event
"""

import subprocess
import queue
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status für Jobs"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DetectionEvent:
    """Vogel-Erkennungs-Event"""
    timestamp: datetime
    bird_count: int
    confidence: float
    frame_number: int


@dataclass
class RecordingJob:
    """Aufnahme-Job für Queue"""
    job_id: str
    detection_event: DetectionEvent
    duration_seconds: int
    resolution: str
    fps: int
    bitrate: int
    enable_audio: bool
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    mp4_path: Optional[Path] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DetectionThread(threading.Thread):
    """
    Kontinuierliche Vogel-Erkennungs-Thread
    - Läuft ständig im Hintergrund
    - Überwacht Detection-Log auf dem Pi
    - Sendet DetectionEvents an RecordingQueue, wenn Vogel erkannt
    """

    def __init__(self, ssh_manager, detection_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True, name="DetectionThread")
        self.ssh = ssh_manager
        self.detection_queue = detection_queue
        self.stop_event = stop_event
        self.last_log_position = 0
        self.threshold = 0.6

    def run(self):
        """Überwache Detection-Log kontinuierlich"""
        logger.info("🔍 DetectionThread gestartet")
        
        while not self.stop_event.is_set():
            try:
                # Lese letzte Log-Zeilen vom Pi
                cmd = "tail -20 /tmp/hailo-detection.log 2>/dev/null"
                success, output, _ = self.ssh.exec_command(cmd, timeout=5)
                
                if success and output:
                    for line in output.split('\n'):
                        if 'Birds:' in line and 'FPS:' in line:
                            # Parse: "Frame: 167 | Birds: 1 | FPS: 12.3"
                            try:
                                self._parse_detection_line(line)
                            except Exception as e:
                                logger.debug(f"Parse error: {e}")
                
                time.sleep(2)  # Poll alle 2 Sekunden
                
            except Exception as e:
                logger.error(f"❌ DetectionThread Error: {e}")
                time.sleep(5)
        
        logger.info("✅ DetectionThread beendet")

    def _parse_detection_line(self, line: str):
        """Parse Detection-Log-Zeile"""
        # Format: "08:50:48 [INFO] 📊 Frame: 378 | Birds: 10 | FPS: 7.1"
        try:
            if 'Birds:' in line:
                birds_str = line.split('Birds:')[1].split('|')[0].strip()
                bird_count = int(birds_str)
                
                fps_str = line.split('FPS:')[1].strip() if 'FPS:' in line else "0"
                fps = float(fps_str.split()[0])
                
                # Nur bei echten Vogel-Erkennungen (>0 und Confidence hoch)
                if bird_count > 0 and fps > 5:  # Nur wenn Detektor aktiv läuft
                    event = DetectionEvent(
                        timestamp=datetime.now(),
                        bird_count=bird_count,
                        confidence=0.8,  # Default für alte Logs
                        frame_number=0
                    )
                    
                    logger.info(f"🐦 Detection: {bird_count} Vögel @ {fps} FPS")
                    self.detection_queue.put(event)
        except Exception as e:
            logger.debug(f"Parse error: {e}")


class RecordingThread(threading.Thread):
    """
    Aufnahme-Job Verarbeiter
    - Liest RecordingJobs aus Queue
    - Startet Recording auf dem Pi via SSH
    - Wartet auf Fertigstellung
    - Stellt Video-Pfade bereit für nächsten Thread
    """

    def __init__(self, ssh_manager, recording_queue: queue.Queue, conversion_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True, name="RecordingThread")
        self.ssh = ssh_manager
        self.recording_queue = recording_queue
        self.conversion_queue = conversion_queue
        self.stop_event = stop_event

    def run(self):
        """Verarbeite Recording-Jobs aus Queue"""
        logger.info("🎥 RecordingThread gestartet")
        
        while not self.stop_event.is_set():
            try:
                # Warte auf Job (mit Timeout um regelmäßig stop_event zu checken)
                try:
                    job = self.recording_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                job.status = JobStatus.IN_PROGRESS
                job.started_at = datetime.now()
                
                logger.info(f"🎬 Starte Recording Job {job.job_id}")
                
                # Starte Recording auf dem Pi
                success, video_path, audio_path = self._record_on_pi(job)
                
                if success and video_path:
                    job.video_path = Path(video_path)
                    job.audio_path = Path(audio_path) if audio_path else None
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    
                    # Sende zu Conversion-Queue
                    self.conversion_queue.put(job)
                    logger.info(f"✅ Recording fertig: {job.video_path}")
                else:
                    job.status = JobStatus.FAILED
                    job.error = "Recording fehlgeschlagen"
                    logger.error(f"❌ Recording failed: {job.job_id}")
                
                self.recording_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ RecordingThread Error: {e}")
                time.sleep(1)
        
        logger.info("✅ RecordingThread beendet")

    def _record_on_pi(self, job: RecordingJob) -> Tuple[bool, Optional[str], Optional[str]]:
        """Starte Remote Recording - gibt (success, video_path, audio_path) zurück"""
        try:
            # Baue Remote-Befehl für unified-camera-monitor-manual.py
            script = '~/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-manual.py'
            
            cmd_args = [
                '--manual-record',
                '--skip-detection',
                f'--duration-seconds {job.duration_seconds}',
                f'--recording-fps {job.fps}',
                f'--enable-audio',
            ]
            
            # Auflösungs-Mapping
            resolution_map = {
                '480p': ('854', '480'),
                '720p': ('1280', '720'),
                '1080p': ('1920', '1080'),
                '4k': ('4096', '2160'),
                '2k': ('2560', '1440'),
            }
            
            if job.resolution in resolution_map:
                w, h = resolution_map[job.resolution]
                cmd_args.append(f'--recording-width {w}')
                cmd_args.append(f'--recording-height {h}')
            
            if job.bitrate > 0:
                cmd_args.append(f'--bitrate {job.bitrate}k')
            
            args_str = ' '.join(cmd_args)
            cmd = f'cd ~/vogel-kamera-linux/raspberry-pi-scripts && python3 {script} {args_str}'
            
            # Starte Recording
            logger.info(f"   Kommando: {cmd}")
            success, output, err = self.ssh.exec_command(cmd, timeout=job.duration_seconds + 30)
            
            # Parse Output um Video-Pfade zu extrahieren
            # Format aus unified-camera-monitor-manual.py:
            # "✅ Video: Freitag__2026-03-13__09-23-39.h264 (50.5MB)"
            # "✅ Audio: Freitag__2026-03-13__09-23-39.wav (2.3MB)"
            
            video_path = None
            audio_path = None
            
            if output:
                for line in output.split('\n'):
                    if '✅ Video:' in line:
                        # Extrahiere Pfad
                        parts = line.split('Video:')[1].split('(')[0].strip()
                        if parts:
                            # Pfad ist usually nur Dateiname, ergänze Verzeichnis
                            video_path = f'/home/roimme/Videos/Vogelhaus/AI-HAD/{parts}'
                    
                    elif '✅ Audio:' in line:
                        parts = line.split('Audio:')[1].split('(')[0].strip()
                        if parts:
                            audio_path = f'/home/roimme/Videos/Vogelhaus/AI-HAD/{parts}'
            
            if success and video_path:
                logger.info(f"   ✅ Recording erfolgreich: {video_path}")
                return (True, video_path, audio_path)
            else:
                # Nur echte Fehler loggen (keine SSH-Warnungen)
                if success:  # Befehl erfolgreich (returncode=0) aber keine Video-Pfade?
                    logger.warning(f"   ⚠️  Recording beendet ohne Video-Output (möglich bei zu kurzer Dauer)")
                else:  # Echtes Fehler
                    logger.error(f"   ❌ Recording fehlgeschlagen")
                    if err and not any(skip in err for skip in ['Warning:', 'Permanently added']):
                        logger.error(f"   Error: {err[:200]}")
                return (False, None, None)
                
        except Exception as e:
            logger.error(f"❌ Recording Exception: {e}")
            return (False, None, None)


class ConversionThread(threading.Thread):
    """
    H364→MP4 Konvertierungs-Thread
    - Liest abgeschlossene Recording-Jobs aus Queue
    - Startet ffmpeg Konvertierung auf dem Pi
    - Überträgt MP4 zu Sync-Queue
    """

    def __init__(self, ssh_manager, conversion_queue: queue.Queue, sync_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True, name="ConversionThread")
        self.ssh = ssh_manager
        self.conversion_queue = conversion_queue
        self.sync_queue = sync_queue
        self.stop_event = stop_event

    def run(self):
        """Konvertiere H364→MP4"""
        logger.info("🔄 ConversionThread gestartet")
        
        while not self.stop_event.is_set():
            try:
                try:
                    job = self.conversion_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                logger.info(f"📝 Konvertiere Video {job.job_id}: {job.video_path.name}")
                
                # Starte ffmpeg auf dem Pi
                success, mp4_path = self._convert_h364_to_mp4(job)
                
                if success and mp4_path:
                    job.mp4_path = Path(mp4_path)
                    self.sync_queue.put(job)
                    logger.info(f"✅ Konvertierung fertig: {job.mp4_path.name}")
                else:
                    logger.error(f"❌ Konvertierung fehlgeschlagen: {job.job_id}")
                
                self.conversion_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ ConversionThread Error: {e}")
                time.sleep(1)
        
        logger.info("✅ ConversionThread beendet")

    def _convert_h364_to_mp4(self, job: RecordingJob) -> Tuple[bool, Optional[str]]:
        """Konvertiere H364→MP4 auf dem Pi"""
        try:
            h364_file = job.video_path
            audio_file = job.audio_path
            
            # Generiere MP4-Namen (gleiche Basis wie H364)
            mp4_file = h364_file.with_suffix('.mp4')
            
            # Baue ffmpeg Befehl für Remote-Ausführung
            if audio_file:
                # Mit Audio-Merge
                ffmpeg_cmd = (
                    f'ffmpeg -fflags +genpts '
                    f'-i "{h364_file}" '
                    f'-i "{audio_file}" '
                    f'-c:v copy -c:a aac '
                    f'-af "volume=2.0,loudnorm=I=-23" '
                    f'-y "{mp4_file}" 2>&1'
                )
            else:
                # Nur Video
                ffmpeg_cmd = (
                    f'ffmpeg -fflags +genpts '
                    f'-i "{h364_file}" '
                    f'-c:v copy '
                    f'-y "{mp4_file}" 2>&1'
                )
            
            logger.info(f"   ffmpeg läuft... (timeout: {job.duration_seconds * 2.5 + 60}s)")
            
            # Führe auf dem Pi aus (mit großem Timeout für CPU-intensive Konvertierung)
            success, output, err = self.ssh.exec_command(
                ffmpeg_cmd,
                timeout=int(job.duration_seconds * 2.5 + 60)  # Konservativ!
            )
            
            if success:
                logger.info(f"   ✅ MP4 erstellt: {mp4_file.name}")
                return (True, str(mp4_file))
            else:
                logger.error(f"   ❌ ffmpeg Error: {err[:200] if err else output[:200]}")
                return (False, None)
                
        except subprocess.TimeoutExpired:
            logger.error(f"   ❌ Konvertierung Timeout (zu langsam auf Pi)")
            return (False, None)
        except Exception as e:
            logger.error(f"   ❌ Konvertierung Exception: {e}")
            return (False, None)


class SyncThread(threading.Thread):
    """
    rsync-basierter Datei-Transfer-Thread
    - Liest fertige MP4s aus Queue
    - Überträgt zum lokalen Client via rsync
    - Thread-safe durch Queue-basierte Kommunikation
    """

    def __init__(self, sync_queue: queue.Queue, stop_event: threading.Event, 
                 ssh_host: str = 'raspberrypi-5-ai-had',
                 ssh_user: str = 'roimme',
                 ssh_key: str = '~/.ssh/id_rsa_ai-had'):
        super().__init__(daemon=True, name="SyncThread")
        self.sync_queue = sync_queue
        self.stop_event = stop_event
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_key = Path(ssh_key).expanduser()

    def run(self):
        """Synchronisiere Dateien zum Client"""
        logger.info("📡 SyncThread gestartet")
        
        while not self.stop_event.is_set():
            try:
                try:
                    job = self.sync_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                logger.info(f"📤 Synchronisiere {job.job_id}")
                
                # Starte rsync Transfer
                success = self._rsync_files(job)
                
                if success:
                    logger.info(f"✅ Sync fertig: {job.mp4_path.name} → lokal")
                else:
                    logger.error(f"❌ Sync fehlgeschlagen für {job.job_id}")
                
                self.sync_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ SyncThread Error: {e}")
                time.sleep(1)
        
        logger.info("✅ SyncThread beendet")

    def _rsync_files(self, job: RecordingJob) -> bool:
        """Übertrage MP4 zum lokalen Client via rsync"""
        try:
            if not job.mp4_path:
                logger.warning(f"   ⚠️  Keine MP4-Datei zum Sync available")
                return False
            
            # Lokales Zielverzeichnis
            local_base = Path.home() / "Videos/Vogelhaus/AI-HAD"
            local_base.mkdir(parents=True, exist_ok=True)
            
            # SSH-Optionen für rsync (mit LogLevel=ERROR um Warnungen zu unterdrücken)
            ssh_opts = (
                f"-i {self.ssh_key} "
                "-o StrictHostKeyChecking=accept-new "
                "-o UserKnownHostsFile=~/.ssh/known_hosts "
                "-o ConnectTimeout=10 "
                "-o BatchMode=yes "
                "-o LogLevel=ERROR"  # WICHTIG: Unterdrücke SSH-Warnungen
            )
            
            # Remote-Pfad für rsync (mit Trailing Slash=Verzeichnisinhalt)
            remote_dir = job.mp4_path.parent
            
            # rsync Kommando
            rsync_cmd = [
                'rsync',
                '-avz',
                '--remove-source-files',
                '-e', f'ssh {ssh_opts}',
                f'{self.ssh_user}@{self.ssh_host}:{remote_dir}/',
                str(local_base / "")
            ]
            
            logger.info(f"   rsync: {remote_dir.name}/ → {local_base}")
            
            # Führe rsync aus
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 Min Timeout
            )
            
            if result.returncode == 0:
                logger.info(f"   ✅ rsync erfolgreich")
                return True
            else:
                logger.error(f"   ❌ rsync Error: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"   ❌ rsync Timeout (Datei zu groß?)")
            return False
        except Exception as e:
            logger.error(f"   ❌ Sync Exception: {e}")
            return False


class CameraPipeline:
    """
    Übergeordnete Pipeline-Manager
    - Verwaltet alle Threads
    - Bietet Thread-sichere Queues
    - Handhabt Lifecycle (start/stop)
    """

    def __init__(self, ssh_manager):
        self.ssh = ssh_manager
        self.stop_event = threading.Event()
        
        # Sichere Queues für Thread-Kommunikation
        self.detection_queue = queue.Queue()
        self.recording_queue = queue.Queue()
        self.conversion_queue = queue.Queue()
        self.sync_queue = queue.Queue()
        
        # Threads
        self.detection_thread = None
        self.recording_thread = None
        self.conversion_thread = None
        self.sync_thread = None
        
        self.is_running = False

    def start(self):
        """Starte alle Threads"""
        if self.is_running:
            logger.warning("⚠️  Pipeline läuft bereits")
            return
        
        self.stop_event.clear()
        
        # Starte alle Threads
        self.detection_thread = DetectionThread(self.ssh, self.detection_queue, self.stop_event)
        self.recording_thread = RecordingThread(self.ssh, self.recording_queue, self.conversion_queue, self.stop_event)
        self.conversion_thread = ConversionThread(self.ssh, self.conversion_queue, self.sync_queue, self.stop_event)
        self.sync_thread = SyncThread(self.sync_queue, self.stop_event)
        
        self.detection_thread.start()
        self.recording_thread.start()
        self.conversion_thread.start()
        self.sync_thread.start()
        
        self.is_running = True
        logger.info("✅ CameraPipeline gestartet (alle Threads laufen)")

    def stop(self):
        """Stoppe alle Threads sauber"""
        if not self.is_running:
            logger.warning("⚠️  Pipeline läuft nicht")
            return
        
        logger.info("🛑 Stoppe CameraPipeline...")
        self.stop_event.set()
        
        # Warte auf Threads (mit Timeout)
        threads = [
            self.detection_thread,
            self.recording_thread,
            self.conversion_thread,
            self.sync_thread
        ]
        
        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=10)
        
        self.is_running = False
        logger.info("✅ CameraPipeline gestoppt")

    def request_recording(self, job: RecordingJob):
        """Fordere Aufnahme an"""
        self.recording_queue.put(job)
        logger.info(f"📝 Aufnahme angefordert: {job.job_id}")

    def get_stats(self) ->Dict[str, Any]:
        """Gebe Statistiken der Queues zurück"""
        return {
            'detection_queue_size': self.detection_queue.qsize(),
            'recording_queue_size': self.recording_queue.qsize(),
            'conversion_queue_size': self.conversion_queue.qsize(),
            'sync_queue_size': self.sync_queue.qsize(),
            'is_running': self.is_running,
        }
