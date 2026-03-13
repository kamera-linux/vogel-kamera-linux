#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEQUENTIAL Camera Pipeline - Lineare Verarbeitung für Vogel-Erkennung

Strategie:
1. Vogel erkannt (Detection-Thread läuft im Hintergrund)
2. WARTEN bis Aufnahme fertig (30 Sekunden)
3. WARTEN bis Konvertierung fertig (H364→MP4)
4. WARTEN bis Sync fertig (→ lokaler Host)
5. READY FOR NEXT BIRD (Loop von 1)

Kein Queue-Chaos, kein paralleles Warten - eine klare Sequenz!
"""

import subprocess
import queue
import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
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
    event_id: int
    bird_count: int
    confidence: float


@dataclass
class RecordingJob:
    """Aufnahme-Job (Singleton für aktuelle Aufnahme)"""
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
    Kontinuierliche Vogel-Erkennungs-Thread (läuft im Hintergrund)
    - Überwacht Pi Detection-Log (/tmp/hailo-detection.log)
    - Sends DetectionEvents in Queue, wenn Vogel erkannt
    """

    def __init__(self, ssh_manager, detection_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True, name="DetectionThread")
        self.ssh = ssh_manager
        self.detection_queue = detection_queue
        self.stop_event = stop_event
        self.event_counter = 0

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
                        # Suche nach Detection-Zeilen mit Vogel-Erkennungen
                        if 'Birds:' in line or '🐦' in line:
                            try:
                                self._parse_detection_line(line)
                            except Exception as e:
                                logger.debug(f"Parse error: {e}")
                
                time.sleep(2)  # Poll alle 2 Sekunden
                
            except Exception as e:
                logger.debug(f"DetectionThread Error: {e}")
                time.sleep(2)
        
        logger.info("✅ DetectionThread beendet")

    def _parse_detection_line(self, line: str):
        """Parse Detection-Log-Zeile und sende Event wenn Vogel erkannt"""
        try:
            # Erwartete Format-Varianten:
            # 1. "[INFO] 📊 Frame: 378 | Birds: 10 | FPS: 7.1"
            # 2. "🐦 VOGEL ERKANNT! Vögel: 3 | Konfidenz: 92.5%"
            
            bird_count = 0
            confidence = 0.8
            
            if 'Birds:' in line:
                # Format 1: "Frame: 378 | Birds: 10 | FPS: 7.1"
                birds_str = line.split('Birds:')[1].split('|')[0].strip()
                bird_count = int(birds_str)
                
            elif 'Vögel:' in line or 'Birds:' in line:
                # Format 2: "Vögel: 3 | Konfidenz: 92.5%"
                vögel_str = line.split('Vögel:')[1].split('|')[0].strip() if 'Vögel:' in line else \
                            line.split('Birds:')[1].split('|')[0].strip()
                bird_count = int(vögel_str)
                
                if 'Konfidenz:' in line:
                    conf_str = line.split('Konfidenz:')[1].split('%')[0].strip()
                    confidence = float(conf_str) / 100.0
            
            # Nur echte Erkennungen senden (bird_count > 0)
            if bird_count > 0:
                self.event_counter += 1
                event = DetectionEvent(
                    timestamp=datetime.now(),
                    event_id=self.event_counter,
                    bird_count=bird_count,
                    confidence=confidence
                )
                
                logger.info(f"🐦 Detection (Event #{self.event_counter}): {bird_count} Vogel @ {confidence*100:.0f}%")
                self.detection_queue.put(event)
        except Exception as e:
            logger.debug(f"Parse error: {e}")


class SequentialPipeline:
    """
    SEQUENTIAL Pipeline: Strikte Reihenfolge
    Vogel erkannt → Recording → Konvertierung → Sync → nächster Vogel
    """

    def __init__(self, ssh_manager, config_dict: dict):
        self.ssh = ssh_manager
        self.config = config_dict
        self.stop_event = threading.Event()
        self.detection_queue = queue.Queue()
        
        # Starte Detection-Thread im Hintergrund
        self.detection_thread = DetectionThread(self.ssh, self.detection_queue, self.stop_event)
        self.detection_thread.start()
        
        # WICHTIG: Stelle sicher, dass Detection-Prozess auf Pi läuft!
        logger.info("🚀 Initialisiert Detection auf Raspberry Pi...")
        self._start_detection_on_pi()
        
        logger.info("✅ Sequential Pipeline initialisiert")

    def process_detection(self, event: DetectionEvent, job: RecordingJob) -> bool:
        """
        Verarbeite Vogel-Detection sequenziell:
        1. Recording starten
        2. Recording fertig warten
        3. Konvertieren H364→MP4
        4. Sync zum Client
        5. Cleanup
        """
        
        logger.info(f"🐦 VOGEL ERKANNT (Event #{event.event_id})")
        logger.info(f"   Vögel: {event.bird_count}")
        logger.info(f"   Konfidenz: {event.confidence:.1f}%")
        
        # Phase 1: RECORDING
        logger.info(f"📹 PHASE 1: RECORDING (Dauer: {job.duration_seconds}s)")
        success, video_path, audio_path = self._record_on_pi(job)
        
        if not success or not video_path:
            logger.error(f"❌ Recording fehlgeschlagen: {job.job_id}")
            return False
        
        job.video_path = Path(video_path)
        job.audio_path = Path(audio_path) if audio_path else None
        job.status = JobStatus.COMPLETED
        logger.info(f"✅ Recording fertig: {job.video_path.name}")
        
        # Phase 2: KONVERTIERUNG
        logger.info(f"🔄 PHASE 2: KONVERTIERUNG (H364→MP4)")
        success, mp4_path = self._convert_h364_to_mp4(job)
        
        if not success or not mp4_path:
            logger.error(f"❌ Konvertierung fehlgeschlagen: {job.job_id}")
            return False
        
        job.mp4_path = Path(mp4_path)
        logger.info(f"✅ Konvertierung fertig: {job.mp4_path.name}")
        
        # Phase 3: SYNC ZUM CLIENT
        logger.info(f"📡 PHASE 3: SYNC ZUM CLIENT")
        success = self._sync_to_client(job)
        
        if not success:
            logger.error(f"❌ Sync fehlgeschlagen: {job.job_id}")
            return False
        
        logger.info(f"✅ Sync fertig: {job.mp4_path.name} → ~/Videos/Vogelhaus/AI-HAD/")
        
        # Phase 4: CLEANUP auf Pi
        logger.info(f"🧹 PHASE 4: CLEANUP")
        self._cleanup_files(job)
        logger.info(f"✅ Cleanup fertig")
        
        logger.info(f"✅✅✅ KOMPLETTER PIPELINE ERFOLGREICH ✅✅✅")
        logger.info("")
        return True

    def _stop_detection_on_pi(self) -> bool:
        """Stoppe Detection-Prozess auf Pi (evite libcamera Resource-Konflikte)"""
        try:
            logger.info(f"   🛑 Stoppe Detection-Prozess auf Pi...")
            cmd = (
                "bash ~/vogel-kamera-linux/unified-monitor-client/detection_manager.sh stop"
            )
            success, _, _ = self.ssh.exec_command(cmd, timeout=5)
            if success:
                logger.info(f"   ✅ Detection-Prozess gestoppt")
            time.sleep(1)  # Gebe libcamera time zum Release
            return True
        except Exception as e:
            logger.warning(f"   ⚠️  Konnte Detection-Prozess nicht stoppen: {e}")
            return False

    def _start_detection_on_pi(self) -> bool:
        """Starte Detection-Prozess auf Pi wieder"""
        try:
            logger.info(f"   🟢 Starte Detection-Prozess auf Pi wieder...")
            cmd = (
                "bash ~/vogel-kamera-linux/unified-monitor-client/detection_manager.sh start"
            )
            success, _, _ = self.ssh.exec_command(cmd, timeout=5)
            if success:
                logger.info(f"   ✅ Detection-Prozess gestartet")
                time.sleep(1)
            return success
        except Exception as e:
            logger.warning(f"   ⚠️  Konnte Detection-Prozess nicht starten: {e}")
            return False

    def _record_on_pi(self, job: RecordingJob) -> Tuple[bool, Optional[str], Optional[str]]:
        """Starte Remote Recording auf Pi - NICHT auf SSH-Output warten!"""
        try:
            # KRITISCH: Stoppe Detection-Prozess vor Recording (libcamera Resource-Konflikt!)
            self._stop_detection_on_pi()
            
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
            
            logger.info(f"   📹 Starte Recording-Prozess: {script}")
            logger.info(f"   ⏱️  Dauer: {job.duration_seconds}s")
            job.status = JobStatus.IN_PROGRESS
            job.started_at = datetime.now()
            
            # WICHTIG: Starte Recording im Hintergrund (nicht warten auf SSH-Output!)
            # Grund: rpicam-vid buffert output bis Fertigstellung
            import subprocess as sp
            
            ssh_host = f"roimme@raspberrypi-5-ai-had"
            ssh_cmd = [
                "ssh",
                "-i", str(Path.home() / ".ssh" / "id_rsa_vogel"),
                "-o", "LogLevel=ERROR",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "ConnectTimeout=10",
                ssh_host,
                cmd
            ]
            
            # Starte SSH in Hintergrund, nicht blockieren auf Output
            # WICHTIG: DEVNULL statt PIPE - dadurch keine Puffer-Blockierung!
            proc = sp.Popen(
                ssh_cmd,
                stdout=sp.DEVNULL,
                stderr=sp.DEVNULL
            )
            
            logger.info(f"   SSH PID: {proc.pid} (läuft im Hintergrund)")
            
            # Warte nur auf Aufnahmedauer + 20 Sekunden Puffer
            wait_time = job.duration_seconds + 20
            logger.info(f"   ⏳ Warte {wait_time}s auf Aufnahme-Fertigstellung...")
            
            try:
                proc.wait(timeout=wait_time)
                logger.info(f"   ✅ SSH-Prozess beendet (returncode: {proc.returncode})")
            except sp.TimeoutExpired:
                logger.warning(f"   ⚠️  SSH-Prozess-Timeout nach {wait_time}s (Aber Aufnahme läuft weiter)")
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except sp.TimeoutExpired:
                    proc.terminate()
            
            # Jetzt suche nach erstellten Video/Audio-Dateien
            logger.info(f"   🔍 Suche nach erstellten Video/Audio-Dateien...")
            
            timestamp_before = datetime.now() - timedelta(seconds=job.duration_seconds + 60)
            find_cmd = (
                "find ~/Videos/Vogelhaus/AI-HAD -type f \\( -name '*.h264' -o -name '*.h265' \\) "
                f"-cnewer /tmp 2>/dev/null | sort -r | head -1"
            )
            
            success_find, find_output, _ = self.ssh.exec_command(find_cmd, timeout=15)
            
            video_path = None
            audio_path = None
            
            if success_find and find_output.strip():
                video_path = find_output.strip()
                logger.info(f"   ✅ Video gefunden: {Path(video_path).name}")
                
                # Suche korrespondierendes Audio
                video_base = Path(video_path).stem
                video_dir = str(Path(video_path).parent)
                audio_cmd = f"find '{video_dir}' -name '{video_base}.wav' 2>/dev/null | head -1"
                
                success_audio, audio_output, _ = self.ssh.exec_command(audio_cmd, timeout=5)
                if success_audio and audio_output.strip():
                    audio_path = audio_output.strip()
                    logger.info(f"   ✅ Audio gefunden: {Path(audio_path).name}")
                
                # Starte Detection wieder
                self._start_detection_on_pi()
                return (True, video_path, audio_path)
            else:
                logger.warning(f"   ⚠️  Keine Video-Datei gefunden nach Aufnahme")
                # Starte Detection wieder (auch bei Fehler)
                self._start_detection_on_pi()
                return (False, None, None)
                
        except Exception as e:
            logger.error(f"   ❌ Recording Exception: {e}")
            # Starte Detection wieder (auch bei Exception!)
            self._start_detection_on_pi()
            return (False, None, None)

    def _convert_h364_to_mp4(self, job: RecordingJob) -> Tuple[bool, Optional[str]]:
        """Konvertiere H364→MP4 auf Pi und warte auf Fertigstellung"""
        try:
            h364_file = job.video_path
            audio_file = job.audio_path
            mp4_file = h364_file.with_suffix('.mp4')
            
            logger.info(f"   Input: {h364_file.name}")
            
            # ffmpeg Befehl mit oder ohne Audio
            if audio_file:
                ffmpeg_cmd = (
                    f'ffmpeg -fflags +genpts '
                    f'-i "{h364_file}" '
                    f'-i "{audio_file}" '
                    f'-c:v copy -c:a aac '
                    f'-af "volume=2.0,loudnorm=I=-23" '
                    f'-y "{mp4_file}" 2>&1'
                )
            else:
                ffmpeg_cmd = (
                    f'ffmpeg -fflags +genpts '
                    f'-i "{h364_file}" '
                    f'-c:v copy '
                    f'-y "{mp4_file}" 2>&1'
                )
            
            logger.info(f"   Starte ffmpeg Konvertierung...")
            
            # Timeout: grob 2-3x die Dauer des Videos
            timeout = max(120, job.duration_seconds * 3)
            success, output, err = self.ssh.exec_command(ffmpeg_cmd, timeout=timeout)
            
            if success and Path(mp4_file).exists():
                logger.info(f"   ✅ Konvertierung erfolgreich: {mp4_file.name}")
                return (True, str(mp4_file))
            else:
                logger.error(f"   ❌ Konvertierung fehlgeschlagen")
                if err:
                    logger.error(f"   Fehler: {err[:300]}")
                return (False, None)
                
        except Exception as e:
            logger.error(f"   ❌ Konvertierung Exception: {e}")
            return (False, None)

    def _sync_to_client(self, job: RecordingJob) -> bool:
        """Synchronisiere MP4-Datei zum lokalen Client (rsync)"""
        try:
            mp4_file = job.mp4_path
            local_dir = Path.home() / 'Videos' / 'Vogelhaus' / 'AI-HAD'
            
            logger.info(f"   Source: {mp4_file} (Pi)")
            logger.info(f"   Dest:   {local_dir} (lokal)")
            
            # Lokales Zielverzeichnis erstellen
            local_dir.mkdir(parents=True, exist_ok=True)
            
            # rsync command mit SSH
            ssh_options = (
                "-i ~/.ssh/id_rsa_vogel "
                "-o LogLevel=ERROR "
                "-o StrictHostKeyChecking=accept-new "
                "-o ConnectTimeout=10"
            )
            
            rsync_cmd = (
                f'rsync -avz '
                f'--rsh="ssh {ssh_options}" '
                f'roimme@raspberrypi-5-ai-had:"{mp4_file}" '
                f'"{local_dir}/"'
            )
            
            logger.info(f"   Starte rsync...")
            success, output, err = self.ssh.exec_command(f"bash -c '{rsync_cmd}'", timeout=300)
            
            if success:
                local_file = local_dir / mp4_file.name
                if local_file.exists():
                    size_mb = local_file.stat().st_size / (1024 * 1024)
                    logger.info(f"   ✅ Sync erfolgreich: {local_file.name} ({size_mb:.1f} MB)")
                    return True
                else:
                    logger.warning(f"   ⚠️  Datei auf Client nicht gefunden")
                    return False
            else:
                logger.error(f"   ❌ rsync fehlgeschlagen")
                if err:
                    logger.error(f"   Fehler: {err[:300]}")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ Sync Exception: {e}")
            return False

    def _cleanup_files(self, job: RecordingJob) -> None:
        """Lösche temporäre Dateien auf Pi nach erfolgreichem Sync"""
        try:
            files_to_delete = [job.video_path, job.audio_path]
            
            for file_path in files_to_delete:
                if file_path:
                    cmd = f'rm -f "{file_path}"'
                    self.ssh.exec_command(cmd, timeout=10)
                    logger.info(f"   🗑️  Gelöscht: {file_path.name}")
                    
        except Exception as e:
            logger.warning(f"   ⚠️  Cleanup Error: {e}")

    def stop(self):
        """Stoppe Pipeline gracefully"""
        logger.info("🛑 Stoppe Sequential Pipeline...")
        self._stop_detection_on_pi()  # Stoppe auch Pi Detection
        self.stop_event.set()
        self.detection_thread.join(timeout=5)
        logger.info("✅ Pipeline gestoppt")
