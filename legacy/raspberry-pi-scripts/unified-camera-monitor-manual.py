#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Camera Monitor für Vogel-Kamera-Linux
==============================================

Vereinheitlichter Kamera-Prozess der:
- Kontinuierlich Preview-Stream bereitstellt
- AI-Analyse durchführt (lokal oder remote)
- Bei Vogel-Erkennung direkt aufnimmt
- KEINE Kamera-Konflikte durch einen einzigen Prozess

Features:
- picamera2 für direkte Kamera-Steuerung
- Dual-Stream: Preview (6 FPS, 640x480) + Recording (30 FPS, 4K)
- YOLOv8 Integration für Vogel-Erkennung
- Automatische Aufnahme bei Trigger
- Cooldown-Management
- System-Monitoring

Verwendung:
    python3 unified-camera-monitor.py --threshold 0.4 --cooldown 15
"""

import argparse
import cv2
import numpy as np
import time
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import threading
import logging
from typing import Optional, Tuple, Dict, Any

# rpicam-vid wird über subprocess aufgerufen (keine direkten Importe nötig)
# rpicam-vid ist Teil von libcamera-apps, bereits auf dem RPi installiert

# YOLO Import
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("⚠️  Ultralytics YOLO nicht installiert. Installiere mit: pip install ultralytics")

# Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/unified-camera-monitor.log')
    ]
)
logger = logging.getLogger(__name__)


def cleanup_old_processes():
    """Killt alte Monitor-Prozesse und Audio-Geräte, die blockieren."""
    logger.info("🧹 Cleanup: Suche nach älteren Monitor-Prozessen...")
    
    try:
        # 1. Killt alte unified-camera-monitor.py Prozesse
        result = subprocess.run(
            ["pgrep", "-f", "unified-camera-monitor.py"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            current_pid = os.getpid()
            
            for pid in pids:
                if pid and int(pid) != current_pid:
                    try:
                        logger.warning(f"🛑 Killen alter Monitor-Prozess: PID {pid}")
                        os.kill(int(pid), 9)  # SIGKILL für sofortiges Beenden
                        time.sleep(0.5)
                    except ProcessLookupError:
                        pass  # Prozess existiert nicht mehr
                    except Exception as e:
                        logger.warning(f"⚠️  Fehler beim Killen von PID {pid}: {e}")
            
            logger.info("✅ Alte Monitor-Prozesse beendet")
        
        # 2. Killt hängende arecord Prozesse (verhindert "Gerät belegt" Error)
        logger.info("🔊 Cleanup: Suche nach hängenden arecord-Prozessen...")
        result = subprocess.run(
            ["pgrep", "-f", "arecord"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        logger.warning(f"🛑 Killen hängendes arecord: PID {pid}")
                        os.kill(int(pid), 9)
                        time.sleep(0.3)
                    except ProcessLookupError:
                        pass
                    except Exception as e:
                        logger.warning(f"⚠️  Fehler beim Killen von arecord: {e}")
            logger.info("✅ arecord-Prozesse beendet")
        
        # 3. Killt hängende rpicam-vid Prozesse
        logger.info("🎬 Cleanup: Suche nach hängenden rpicam-vid-Prozessen...")
        result = subprocess.run(
            ["pgrep", "-f", "rpicam-vid"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        logger.warning(f"🛑 Killen hängendes rpicam-vid: PID {pid}")
                        os.kill(int(pid), 9)
                        time.sleep(0.3)
                    except ProcessLookupError:
                        pass
                    except Exception as e:
                        logger.warning(f"⚠️  Fehler beim Killen von rpicam-vid: {e}")
            logger.info("✅ rpicam-vid-Prozesse beendet")
    
    except Exception as e:
        logger.warning(f"⚠️  Cleanup-Fehler: {e}")


class UnifiedCameraMonitor:
    """
    Vereinheitlichter Kamera-Monitor für Preview + Recording
    """
    
    def __init__(
        self,
        camera_num: int = 0,
        threshold: float = 0.4,
        cooldown: int = 15,
        trigger_duration: float = 1.0,
        video_base_path: str = None,  # Will be set to ~/Videos/Vogelhaus if None
        model_path: Optional[str] = None,
        preview_width: int = 640,
        preview_height: int = 480,
        preview_fps: int = 6,
        recording_width: int = 1920,
        recording_height: int = 1080,
        recording_fps: int = 30,
        recording_duration: int = 60,
        rotation: int = 180,
        codec: str = "h264",
        hdr: str = "off",
        autofocus_mode: str = "continuous",
        autofocus_range: str = "macro",
        roi: Optional[str] = None,
        enable_audio: bool = False,
        manual_record: bool = False,
        skip_detection: bool = False,
        debug: bool = False
    ):
        """
        Initialisiert Unified Camera Monitor.
        
        Args:
            camera_num: Kamera-Nummer (0 oder 1)
            threshold: AI-Erkennungs-Schwelle (0.0 - 1.0)
            cooldown: Wartezeit zwischen Aufnahmen in Sekunden
            trigger_duration: Mindest-Dauer für Trigger in Sekunden
            video_base_path: Basis-Pfad für Video-Speicherung
            model_path: Pfad zum YOLO-Model (optional)
            preview_width: Breite des Preview-Streams
            preview_height: Höhe des Preview-Streams
            preview_fps: FPS des Preview-Streams
            recording_width: Breite der Aufnahme
            recording_height: Höhe der Aufnahme
            recording_fps: FPS der Aufnahme
            recording_duration: Dauer der Aufnahme in Sekunden
            rotation: Rotation (0, 90, 180, 270) - default 180 für Vogelbild oben
            codec: Video-Codec (default: h264)
            hdr: HDR-Modus (default: off)
            autofocus_mode: Autofokus-Modus (default: continuous)
            autofocus_range: Autofokus-Bereich (default: macro)
            roi: Region of Interest im Format x,y,w,h (optional)
            enable_audio: Audio-Aufnahme aktivieren
            manual_record: Manuelle Aufnahme
            skip_detection: Erkennung überspringen
            debug: Debug-Modus aktivieren
        """
        self.camera_num = camera_num
        self.threshold = threshold
        self.cooldown = cooldown
        self.trigger_duration = trigger_duration
        self.recording_duration = recording_duration
        
        # Set video_base_path with fallback to ~/Videos/Vogelhaus
        if video_base_path is None:
            video_base_path = os.path.expanduser('~/Videos/Vogelhaus')
        self.video_base_path = Path(video_base_path)
        self.preview_width = preview_width
        self.preview_height = preview_height
        self.preview_fps = preview_fps
        self.recording_width = recording_width
        self.recording_height = recording_height
        self.recording_fps = recording_fps
        self.rotation = rotation
        self.codec = codec
        self.hdr = hdr
        self.autofocus_mode = autofocus_mode
        self.autofocus_range = autofocus_range
        self.roi = roi
        self.enable_audio = enable_audio
        self.manual_record = manual_record
        self.skip_detection = skip_detection
        self.debug = debug
        
        # rpicam-vid nutzt subprocess - kein Picamera2 Objekt mehr
        self.camera_process: Optional[subprocess.Popen] = None
        
        # AI Model
        self.model: Optional[Any] = None
        self.model_path = model_path
        
        # Detection State
        self.detection_history = []
        self.first_detection_time = None
        self.is_recording = False
        self.last_recording_time = 0
        
        # Statistics
        self.frames_processed = 0
        self.recordings_triggered = 0
        self.start_time = time.time()
        
        # Threading
        self.stop_event = threading.Event()
        self.recording_lock = threading.Lock()
        
        # Erstelle Video-Verzeichnis
        self.video_base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("UnifiedCameraMonitor initialisiert")
        logger.info(f"  Kamera: {camera_num}")
        logger.info(f"  Preview: {preview_width}x{preview_height} @ {preview_fps}fps")
        logger.info(f"  Recording: {recording_width}x{recording_height} @ {recording_fps}fps")
        logger.info(f"  Threshold: {threshold}")
        logger.info(f"  Cooldown: {cooldown}s")
        logger.info(f"  Audio: {'aktiviert' if enable_audio else 'deaktiviert'}")
        
        # Audio-Device
        self.audio_device = None
        self.audio_process = None
    
    def _load_model(self) -> bool:
        """Lädt YOLO-Model für Vogel-Erkennung."""
        if not HAS_YOLO:
            logger.error("YOLO nicht verfügbar")
            return False
        
        try:
            # Verwende YOLOv8n für Performance
            if self.model_path and Path(self.model_path).exists():
                logger.info(f"Lade Model: {self.model_path}")
                self.model = YOLO(self.model_path)
            else:
                logger.info("Lade YOLO26n (Standard)")
                self.model = YOLO("yolo26n.pt")
            
            logger.info("✅ YOLO-Model geladen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Models: {e}")
            return False
    
    def _check_rpicam_vid(self) -> bool:
        """
        Prüft ob rpicam-vid verfügbar ist.
        
        rpicam-vid ist Teil von libcamera-apps und sollte auf allen modernen
        Raspberry Pi OS Installationen vorhanden sein.
        
        Returns:
            True wenn rpicam-vid gefunden, sonst False
        """
        try:
            result = subprocess.run(
                ['which', 'rpicam-vid'],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("✅ rpicam-vid gefunden")
                return True
            else:
                logger.error("❌ rpicam-vid nicht gefunden. Installiere: sudo apt install -y libcamera-apps")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Prüfen von rpicam-vid: {e}")
            return False
    
    def start(self) -> bool:
        """Startet Camera Monitor."""
        try:
            logger.info("🎬 Starte Unified Camera Monitor (rpicam-vid Version)...")
            
            # Cleanup alte Prozesse die die Kamera blockieren könnten
            cleanup_old_processes()
            time.sleep(1)  # Warte nach Cleanup
            
            # Prüfe rpicam-vid Verfügbarkeit
            if not self._check_rpicam_vid():
                logger.error("❌ rpicam-vid nicht verfügbar")
                return False
            
            # Lade Model
            if not self._load_model():
                logger.warning("⚠️  Fahre ohne AI-Model fort (Fallback-Modus)")
            
            logger.info("✅ Camera Monitor bereit")
            time.sleep(1)  # Stabilisierungszeit
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Monitors: {e}")
            return False
    
    def stop(self):
        """Stoppt Camera Monitor."""
        logger.info("🛑 Stoppe Camera Monitor...")
        self.stop_event.set()
        
        # Stoppe laufenden rpicam-vid Prozess
        if self.camera_process:
            try:
                self.camera_process.terminate()
                logger.info("rpicam-vid Prozess beendet")
                # Warte kurz auf graceful shutdown
                try:
                    self.camera_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.camera_process.kill()
                    logger.warning("rpicam-vid Prozess getötet (SIGKILL)")
            except Exception as e:
                logger.error(f"Fehler beim Stoppen von rpicam-vid: {e}")
        
        if self.is_recording:
            self.is_recording = False
            logger.info("Aufnahme-Flag zurückgesetzt")
        
        logger.info("✅ Camera Monitor gestoppt")
    
    def _find_usb_audio_device(self) -> Optional[str]:
        """
        Findet USB-Audio-Gerät für Aufnahme mit mehreren Strategien.
        
        Strategien (in Reihenfolge):
        1. arecord -l: Suche nach USB in der Liste (Englisch oder Deutsch)
        2. lsusb: Finde USB-Audio Device im System
        3. Fallback: Versuche Standard-Geräte (hw:0,0 / hw:1,0 / hw:2,0 / hw:3,0)
        
        Returns:
            Gerätepfad (z.B. 'hw:0,0') oder None wenn nicht gefunden
        """
        import re
        
        logger.info("🔍 Suche nach USB-Audio-Gerät...")
        
        # Strategie 1: arecord -l
        try:
            result = subprocess.run(
                ['arecord', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug(f"arecord -l Output:\n{result.stdout}")
                for line in result.stdout.splitlines():
                    # Suche nach USB-Geräten (funktioniert mit Deutsch und Englisch)
                    if 'USB' in line.upper():
                        # Parse: "Karte 0: ..." oder "card 0: ..."
                        # Regex: Match "Karte" or "card", dann Ziffer
                        match = re.search(r'(?:[Kk]arte|card)\s+(\d+)', line)
                        if match:
                            card_num = match.group(1)
                            device = f"hw:{card_num},0"
                            logger.info(f"✅ USB-Audio-Gerät gefunden (arecord): {device}")
                            return device
        except Exception as e:
            logger.debug(f"arecord -l Fehler: {e}")
        
        # Strategie 2: lsusb für USB-Audio Device Identifier
        try:
            result = subprocess.run(
                ['lsusb'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug(f"lsusb Output (gefiltert):")
                for line in result.stdout.splitlines():
                    if 'Audio' in line or 'audio' in line or 'Microphone' in line or 'microphone' in line:
                        logger.debug(f"  {line}")
                        # Jedes Audio-Device könnte unser Gerät sein
                        # Versuche als Standard-Kartenindex zu nutzen
        except Exception as e:
            logger.debug(f"lsusb Fehler: {e}")
        
        # Strategie 3: Fallback auf häufige USB-Audio Kartennummern
        # Typischerweise: hw:0,0 (erste ALSA-Karte), hw:1,0 oder hw:2,0 für erste USB-Geräte
        logger.debug("Fallback: Teste Geräte hw:0,0 bis hw:3,0...")
        for card_num in [0, 1, 2, 3]:
            device_path = f"hw:{card_num},0"
            
            # Prüfe ob Gerät existiert via arecord -D test
            try:
                # Kurzer Test: record 0.05 seconds
                result = subprocess.run(
                    ['arecord', '-D', device_path, '-c', '1', '-r', '8000', '-f', 'mu-law', '-t', 'raw', '/dev/null', '-d', '0.05'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ USB-Audio-Gerät gefunden (Fallback): {device_path}")
                    return device_path
                else:
                    logger.debug(f"  {device_path}: Rückgabecode {result.returncode}")
            except subprocess.TimeoutExpired:
                # Timeout ist ok - Gerät existiert und hat reagiert
                logger.info(f"✅ USB-Audio-Gerät gefunden (Fallback/Timeout): {device_path}")
                return device_path
            except Exception as e:
                logger.debug(f"  {device_path}: Fehler - {type(e).__name__}")
        
        logger.warning("⚠️  Kein USB-Audio-Gerät gefunden!")
        logger.warning("    Fallback: Nutze ALSA 'default' Gerät")
        
        # Strategie 4: Absoluter Fallback auf "default" ALSA-Gerät
        try:
            result = subprocess.run(
                ['arecord', '-D', 'default', '-c', '1', '-r', '8000', '-f', 'mu-law', '-t', 'raw', '/dev/null', '-d', '0.05'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                logger.info(f"✅ Nutze ALSA 'default' Audio-Gerät")
                return "default"
        except subprocess.TimeoutExpired:
            logger.info(f"✅ Nutze ALSA 'default' Audio-Gerät (Timeout ist ok)")
            return "default"
        except Exception as e:
            logger.debug(f"  default: Fehler - {type(e).__name__}")
        
        logger.warning("    Alternativ: arecord -l, alsamixer, pavucontrol")
        return None
    
    def _start_audio_recording(self, audio_file: Path, duration_seconds: int) -> bool:
        """
        Startet Audio-Aufnahme mit ffmpeg (parallel zu Video).
        Nutzt ffmpeg mit 48kHz und Audio-Verarbeitung (vereinfacht, robust).
        
        Args:
            audio_file: Pfad zur WAV-Datei
            duration_seconds: Aufnahmedauer in Sekunden
            
        Returns:
            True wenn erfolgreich gestartet, sonst False
        """
        if not self.enable_audio or not self.audio_device:
            return False
        
        try:
            # ffmpeg mit ROBUSTEREN Audio-Filtern (vereinfacht, weniger fehleranfällig)
            # -af: Audio-Filter chain:
            #   highpass=f=80: Hochpass-Filter (schneidet tiefe Rausch-Frequenzen)
            #   volume=1.5: 1.5x Verstärkung (bessere Aussteuerung)
            # 
            # WICHTIG: 48kHz wie professionelle Audio
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'warning',
                '-f', 'alsa',
                '-i', self.audio_device,
                '-t', str(duration_seconds),
                '-af', 'highpass=f=80,volume=1.5',  # Simplified: Highpass + Verstärkung
                '-acodec', 'pcm_s16le',
                '-ar', '48000',  # 48kHz wie professionelle Audio (nicht 44100)
                '-ac', '1',      # Mono
                '-y',
                str(audio_file)
            ]
            
            logger.info(f"🎤 Starte professionelle Audio-Aufnahme (ffmpeg 48kHz): {audio_file.name}")
            self.audio_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Audio-Aufnahme: {e}")
            return False
    
    def _wait_for_audio_completion(self, timeout: int = 300) -> bool:
        """
        Wartet bis Audio-Aufnahme fertig ist.
        
        Args:
            timeout: Timeout in Sekunden
            
        Returns:
            True wenn erfolgreich, sonst False
        """
        if not self.audio_process:
            return False
        
        try:
            stdout, stderr = self.audio_process.communicate(timeout=timeout)
            returncode = self.audio_process.returncode
            
            if returncode == 0:
                logger.info(f"✅ Audio-Aufnahme abgeschlossen")
                return True
            else:
                logger.error(f"❌ Audio-Aufnahme Fehler (Code {returncode}): {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Audio-Aufnahme Timeout")
            self.audio_process.kill()
            return False
        except Exception as e:
            logger.error(f"❌ Fehler beim Warten auf Audio: {e}")
            return False
        finally:
            self.audio_process = None
    
    def _detect_bird(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Führt Vogel-Erkennung durch.
        
        Args:
            frame: Frame für Analyse
            
        Returns:
            (bird_detected, confidence)
        """
        if not self.model:
            return False, 0.0
        
        try:
            # YOLO Inference
            results = self.model(frame, verbose=False)
            
            # Prüfe auf Vogel (COCO class 14)
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id == 14 and confidence >= self.threshold:
                        return True, confidence
            
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Fehler bei Vogel-Erkennung: {e}")
            return False, 0.0
    
    def _check_trigger(self, bird_detected: bool) -> bool:
        """
        Prüft ob Trigger-Bedingungen erfüllt sind.
        
        Args:
            bird_detected: Ob Vogel im aktuellen Frame erkannt wurde
            
        Returns:
            True wenn getriggert werden soll
        """
        current_time = time.time()
        
        if bird_detected:
            # Erste Erkennung?
            if self.first_detection_time is None:
                self.first_detection_time = current_time
                logger.info(f"🐦 Vogel erkannt (Start)! Warte {self.trigger_duration}s für Trigger...")
            
            # Füge zur History hinzu
            self.detection_history.append((current_time, True))
            
            # Prüfe Dauer
            duration = current_time - self.first_detection_time
            
            if duration >= self.trigger_duration:
                # Prüfe Konsistenz (60% der Frames müssen Vogel enthalten)
                recent_detections = [d for t, d in self.detection_history if t >= current_time - self.trigger_duration]
                if len(recent_detections) > 0:
                    consistency = sum(recent_detections) / len(recent_detections)
                    
                    if consistency >= 0.6:
                        print(f"🐦 Vogel erkannt! (Dauer: {duration:.1f}s, Konsistenz: {consistency*100:.0f}%)")
                        logger.info(f"✅ Trigger-Bedingungen erfüllt! (Dauer: {duration:.1f}s, Konsistenz: {consistency*100:.0f}%)")
                        # Reset für nächsten Trigger
                        self.first_detection_time = None
                        self.detection_history = []
                        return True
        else:
            # Vogel verloren
            if self.first_detection_time is not None:
                duration = current_time - self.first_detection_time
                logger.info(f"❌ Vogel-Erkennung verloren (war {duration:.1f}s)")
                self.first_detection_time = None
                self.detection_history = []
        
        # Bereinige alte Einträge aus History
        self.detection_history = [(t, d) for t, d in self.detection_history if t >= current_time - self.trigger_duration]
        
        return False
    def _start_recording(self) -> Optional[str]:
        """
        NICHT UNTERSTÜTZT mit rpicam-vid!
        
        rpicam-vid kann kein Live-Preview parallel zu H264-Encoding liefern.
        Nur manueller Aufnahmemodus (--manual-record) ist unterstützt.
        """
        logger.error("❌ Vogelerkennung + Auto-Aufnahme wird mit rpicam-vid nicht unterstützt!")
        logger.error("   Nutze stattdessen: --manual-record Modus")
        return None
    
    def _stop_recording(self):
        """NICHT UNTERSTÜTZT mit rpicam-vid"""
        pass
    
    def _start_recording_manual(self) -> tuple:
        """
        Startet PARALLELE Video+Audio Aufnahme wie die alte Lösung mit Threading.
        KRITISCH: Video und Audio müssen mit EXAKT gleicher Dauer gleichzeitig starten!
        
        Returns:
            (video_file_path, audio_file_path, stop_event)
            stop_event wird nach recording_duration automatisch gesetzt
        """
        try:
            # Info: Zeige verwendete Parameter
            logger.info(f"📹 Parameter:")
            logger.info(f"   - Kamera: {self.camera_num}")
            logger.info(f"   - Auflösung: {self.recording_width}x{self.recording_height}")
            logger.info(f"   - Framerate: {self.recording_fps} fps")
            logger.info(f"   - Rotation: {self.rotation}°")
            logger.info(f"   - Codec: {self.codec}")
            logger.info(f"   - Autofokus: {self.autofocus_mode} ({self.autofocus_range})")
            logger.info(f"   - HDR: {self.hdr}")
            logger.info(f"   - Dauer: {self.recording_duration}s (EXAKT für Video+Audio)")
            logger.info(f"   - Encoder: rpicam-vid + arecord (paralleles Dual-Recording)")
            
            # Erstelle Dateinamen
            now = datetime.now()
            weekday = now.strftime("%A")
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H-%M-%S")
            year = now.strftime("%Y")
            kw = now.strftime("%V")  # Kalenderwochen (01-53)
            
            weekday_map = {
                "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
                "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag",
                "Sunday": "Sonntag"
            }
            weekday_de = weekday_map.get(weekday, weekday)
            filename = f"{weekday_de}__{date_str}__{time_str}"
            
            # Erstelle Verzeichnis
            if self.recording_fps >= 100:
                subdir = "Zeitlupe"
            else:
                subdir = "AI-HAD"
            
            video_dir = self.video_base_path / subdir / year / kw / filename  # Kalenderwochen (KW) verwenden
            video_dir.mkdir(parents=True, exist_ok=True)
            
            video_file = video_dir / f"{filename}.h264"
            audio_file = video_dir / f"{filename}.wav" if self.enable_audio else None
            
            # WICHTIG: Duration MUSS exakt gleich sein für beide!
            duration_ms = int(self.recording_duration * 1000)  # rpicam-vid erwartet Millisekunden
            duration_s = self.recording_duration  # arecord erwartet Sekunden
            
            logger.info(f"🎬 Starte PARALLELE Aufnahme: {filename}")
            logger.info(f"   - Video: {video_file.name}")
            if audio_file:
                logger.info(f"   - Audio: {audio_file.name}")
            
            # Stop-Event für Timing
            stop_event = threading.Event()
            
            # ===== THREAD 1: Video mit rpicam-vid =====
            # Exakt wie alte Lösung: alle rpicam-vid Parameter übernehmen
            rpicam_cmd = [
                'rpicam-vid',
                '--camera', str(self.camera_num),
                '--codec', self.codec,
                '--width', str(self.recording_width),
                '--height', str(self.recording_height),
                '--framerate', str(self.recording_fps),
                '--rotation', str(self.rotation),  # WICHTIG: 180 für Vogelbild oben
                '--autofocus-mode', self.autofocus_mode,
                '--autofocus-range', self.autofocus_range,
                '--hdr', self.hdr,
                '--timeout', str(duration_ms),  # EXAKT: Duration in Millisekunden
                '--output', str(video_file)
            ]
            
            # Optional: ROI hinzufügen wenn gesetzt
            if self.roi:
                rpicam_cmd.extend(['--roi', self.roi])
            
            def run_video():
                logger.info(f"🎬 Video-Thread startet: rpicam-vid")
                try:
                    self.camera_process = subprocess.Popen(
                        rpicam_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = self.camera_process.communicate()
                    
                    if self.camera_process.returncode == 0:
                        logger.info(f"✅ Video-Thread erfolgreich")
                    else:
                        logger.error(f"❌ Video-Thread Fehler: {stderr}")
                except Exception as e:
                    logger.error(f"❌ Video-Thread Exception: {e}")
            
            # ===== THREAD 2: Audio mit ffmpeg (robuste Verarbeitung) =====
            def run_audio():
                if not self.enable_audio or not self.audio_device:
                    logger.info("ℹ️  Audio deaktiviert oder kein Device")
                    return
                
                logger.info(f"🎤 Audio-Thread startet: ffmpeg -i {self.audio_device}")
                try:
                    # ffmpeg mit ROBUSTEREN Audio-Filtern (vereinfacht, weniger fehleranfällig)
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-hide_banner',
                        '-loglevel', 'warning',
                        '-f', 'alsa',
                        '-i', self.audio_device,
                        '-t', str(duration_s),
                        '-af', 'highpass=f=80,volume=1.5',  # Simplified: Highpass + Verstärkung
                        '-acodec', 'pcm_s16le',
                        '-ar', '48000',  # 48kHz wie professionelle Audio (nicht 44100)
                        '-ac', '1',      # Mono
                        '-y',
                        str(audio_file)
                    ]
                    
                    audio_proc = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = audio_proc.communicate()
                    
                    if audio_proc.returncode == 0:
                        logger.info(f"✅ Audio-Thread erfolgreich (48kHz)")
                    else:
                        logger.error(f"❌ Audio-Thread Fehler: {stderr}")
                except Exception as e:
                    logger.error(f"❌ Audio-Thread Exception: {e}")
            
            # ===== THREAD 3: Fortschrittsanzeige =====
            def show_progress():
                start_time = time.time()
                while not stop_event.is_set():
                    elapsed = time.time() - start_time
                    if elapsed > self.recording_duration:
                        break
                    
                    percent = min(int((elapsed / self.recording_duration) * 100), 100)
                    bar_length = 24
                    filled = int((elapsed / self.recording_duration) * bar_length)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    
                    print(f"\r⏱️  {bar} {percent}% ({int(elapsed)}/{self.recording_duration}s)", end='', flush=True)
                    time.sleep(0.1)
                
                print()  # Neue Zeile
            
            # ===== STARTE ALLE THREADS GLEICHZEITIG =====
            logger.info("▶️  Starte parallele Aufnahme...")
            print(f"🎬 Aufnahme: {filename} ({self.recording_duration}s)")
            
            # Starte Video-Thread
            video_thread = threading.Thread(target=run_video, daemon=False)
            video_thread.start()
            
            # Starte Audio-Thread (gleichzeitig mit Video!)
            audio_thread = threading.Thread(target=run_audio, daemon=False)
            audio_thread.start()
            
            # Starte Progress-Thread
            progress_thread = threading.Thread(target=show_progress, daemon=True)
            progress_thread.start()
            
            # ===== WARTE AUF DURATION =====
            # Das ist der Schlüssel: Beide Threads laufen PARALLEL für exakt recording_duration
            time.sleep(self.recording_duration + 1)  # +1 zum Sicherstellen dass beide fertig sind
            
            # Setze Stop-Event
            stop_event.set()
            
            # Warte auf Thread-Abschluss
            logger.info("⏳ Warte auf Aufnahme-Threads...")
            video_thread.join(timeout=10)
            audio_thread.join(timeout=10)
            
            logger.info("✅ Alle Aufnahme-Threads abgeschlossen")
            
            # Prüfe ob Dateien erstellt wurden
            if video_file.exists() and video_file.stat().st_size > 0:
                size_mb = video_file.stat().st_size / (1024*1024)
                logger.info(f"✅ Video: {video_file.name} ({size_mb:.1f}MB)")
                print(f"✅ Aufnahme abgeschlossen")
                
                if audio_file and audio_file.exists():
                    size_kb = audio_file.stat().st_size / 1024
                    logger.info(f"✅ Audio: {audio_file.name} ({size_kb:.1f}KB)")
                
                return (str(video_file), str(audio_file) if audio_file and audio_file.exists() else None, stop_event)
            else:
                logger.error(f"❌ Video-Datei nicht erstellt: {video_file}")
                return (None, None, stop_event)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei paralleler Aufnahme: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return (None, None, stop_event)
    
    def _convert_h264_to_mp4_sync(self, h264_file: Path, audio_file: Optional[Path] = None):
        """
        Konvertiert H264 zu MP4 synchron (wartet bis fertig).
        Optional mit Audio-Merged (falls Audio vorhanden).
        
        Args:
            h264_file: Pfad zur H264-Datei
            audio_file: Pfad zur WAV-Audio-Datei (optional)
        """
        try:
            import subprocess
            
            # Bei Slowmo: mehrere FPS, sonst nur Recording-FPS
            if self.recording_fps >= 100:
                playback_fps_list = [5, 10, 20, 30, 120]
                logger.info(f"🔄 Konvertiere Zeitlupen-Video ({len(playback_fps_list)} Versionen)...")
            else:
                playback_fps_list = [self.recording_fps]
                logger.info(f"🔄 Konvertiere Video zu MP4...")
            
            # Prüfe ob Audio existiert und valid ist
            audio_valid = False
            if audio_file and audio_file.exists():
                audio_valid = True
                logger.info(f"✅ Audio gefunden: {audio_file.name}")
            elif audio_file:
                logger.warning(f"⚠️  Audio-Datei nicht gefunden: {audio_file}")
            
            success_count = 0
            for playback_fps in playback_fps_list:
                base_name = h264_file.stem
                mp4_file = h264_file.parent / f"{base_name}__{self.recording_width}x{self.recording_height}__{playback_fps}fps.mp4"
                
                print(f"🎬 Konvertiere: {mp4_file.name}{'🎤 (mit Audio)' if audio_valid else ''}")
                
                if audio_valid:
                    # Mit Audio: Video + Audio mergen
                    # WICHTIG: Exakt wie alte Lösung:
                    # -fflags +genpts: Korrekte Zeitstempel-Generierung
                    # -r {fps}: Framerate für Playback
                    # -af: Audio-Filter: volume=2.0 (sanftes Boost statt aggressive 4x)
                    # KEIN -shortest: Beide Streams bleiben vorhanden!
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-fflags', '+genpts',          # Richtige Zeitstempel generieren
                        '-r', str(playback_fps),       # Playback Framerate
                        '-i', str(h264_file),          # Video Input
                        '-i', str(audio_file),         # Audio Input
                        '-c:v', 'copy',                # Video codec: copy (no re-encode)
                        '-c:a', 'aac',                 # Audio codec: AAC
                        '-af', 'volume=2.0,loudnorm=I=-23',  # 2x sanfter Boost + Normalisierung
                        '-y', str(mp4_file)
                    ]
                    logger.debug(f"🎬 FFmpeg mit Audio (rausch-reduziert + 2x boost): {' '.join(ffmpeg_cmd)}")
                else:
                    # Nur Video mit FFmpeg Zeitstempel-Fix
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-fflags', '+genpts',          # Richtige Zeitstempel generieren
                        '-r', str(playback_fps),       # Playback Framerate
                        '-i', str(h264_file),
                        '-c:v', 'copy',
                        '-y', str(mp4_file)
                    ]
                    logger.debug(f"🎬 FFmpeg ohne Audio: {' '.join(ffmpeg_cmd)}")
                
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 Min Timeout pro Konvertierung
                )
                
                if result.returncode == 0:
                    size_mb = mp4_file.stat().st_size / (1024*1024)
                    logger.info(f"✅ {mp4_file.name} ({size_mb:.1f}MB)")
                    print(f"✅ {mp4_file.name} ({size_mb:.1f}MB)")
                    success_count += 1
                else:
                    logger.error(f"❌ Fehler: {result.stderr[:200]}")
                    print(f"❌ Konvertierung fehlgeschlagen")
            
            # Lösche H264 nur bei Erfolg
            if success_count > 0:
                h264_file.unlink()
                logger.info(f"✅ {success_count} MP4-Dateien erstellt, H264 gelöscht")
                print(f"✅ {success_count} MP4-Dateien erstellt")
                
                # Lösche Audio auch wenn erfolgreich
                if audio_valid:
                    try:
                        audio_file.unlink()
                        logger.info(f"✅ Audio-Datei gelöscht")
                    except:
                        pass
            else:
                logger.error("❌ Keine erfolgreichen Konvertierungen")
                print("❌ Konvertierung fehlgeschlagen")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Konvertierung hat zu lange gedauert (Timeout)")
            print("❌ Konvertierung: Timeout")
        except Exception as e:
            logger.error(f"❌ Fehler bei Konvertierung: {e}")
            print(f"❌ Konvertierungsfehler: {e}")
    
    def _convert_h264_to_mp4(self, h264_file: Path):
        """Konvertiert H264 zu MP4 mit verschiedenen Playback-Frameraten (für Zeitlupe)."""
        try:
            import subprocess
            
            # Bei Slowmo-Modus: Erstelle mehrere Versionen mit verschiedenen FPS
            # 120fps aufgenommen → verschiedene Playback-FPS für Zeitlupen-Effekte
            if self.recording_fps >= 100:  # Slowmo-Modus erkannt
                playback_fps_list = [5, 10, 20, 30, 120]  # Verschiedene Zeitlupen-Stufen
                logger.info(f"🔄 Konvertiere Zeitlupen-Video mit {len(playback_fps_list)} Frameraten...")
            else:
                playback_fps_list = [self.recording_fps]  # Nur Original-FPS
                logger.info(f"🔄 Konvertiere Video zu MP4...")
            
            success_count = 0
            for playback_fps in playback_fps_list:
                # Erstelle Dateinamen IMMER mit Auflösung und FPS-Info
                # Format: Dienstag__2025-11-14__09-40-46__1920x1080__30fps.mp4
                base_name = h264_file.stem  # Ohne .h264
                mp4_file = h264_file.parent / f"{base_name}__{self.recording_width}x{self.recording_height}__{playback_fps}fps.mp4"
                
                # ffmpeg-Befehl mit einfachen Copy-Codec (keine Framerate-Tricks!)
                # rpicam-vid erzeugt richtige H264 mit Metadaten
                result = subprocess.run(
                    ['ffmpeg', '-i', str(h264_file),
                     '-c:v', 'copy', '-y', str(mp4_file)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ {mp4_file.name} erstellt ({playback_fps}fps)")
                    success_count += 1
                else:
                    logger.error(f"❌ Fehler bei {playback_fps}fps: {result.stderr[:200]}")
            
            # Lösche H264 nur wenn mindestens eine MP4 erfolgreich erstellt wurde
            if success_count > 0:
                h264_file.unlink()
                logger.info(f"🗑️  H264-Datei gelöscht: {h264_file.name}")
                logger.info(f"✅ Konvertierung abgeschlossen: {success_count} MP4-Dateien erstellt")
            else:
                logger.error(f"❌ Keine erfolgreichen Konvertierungen - H264 behalten")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Konvertierung: {e}")
    
    def _sync_mp4_files_to_client(self, video_dir: Path) -> bool:
        """
        Synchronisiert alle MP4-Dateien vom Raspberry Pi zum lokalen Client.
        
        Versucht mehrere Export-Methoden (SMB, SSH, lokale Kopie).
        
        Args:
            video_dir: Verzeichnis mit MP4-Dateien
            
        Returns:
            True wenn erfolgreich, sonst False
        """
        try:
            # Ziel-Pfad auf Client: Gleiche Struktur wie auf Pi
            rel_path = video_dir.relative_to(self.video_base_path)
            client_base_path = "/home/imme/Videos/Vogelhaus"  # Lokale Client-Ziel
            dest_path = f"{client_base_path}/{rel_path}"
            
            logger.info(f"📤 Synchronisiere MP4-Dateien...")
            logger.info(f"   Quelle: {video_dir}")
            logger.info(f"   Ziel: {dest_path}")
            
            # Strategie 1: Versuche lokale Kopie (wenn Ziel über NFS/Samba gemountet ist)
            try:
                dest_path_obj = Path(dest_path)
                
                # Versuche Zielverzeichnis zu erstellen
                dest_path_obj.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Zielverzeichnis verfügbar: {dest_path}")
                
                # Kopiere alle MP4-Dateien
                import shutil
                mp4_files = list(video_dir.glob("*.mp4"))
                
                if not mp4_files:
                    logger.warning(f"⚠️  Keine MP4-Dateien im {video_dir} gefunden!")
                    return False
                
                for mp4_file in mp4_files:
                    dest_file = dest_path_obj / mp4_file.name
                    logger.info(f"  📋 Kopiere: {mp4_file.name}")
                    shutil.copy2(mp4_file, dest_file)
                
                logger.info(f"✅ {len(mp4_files)} MP4-Dateien erfolgreich kopiert!")
                print(f"✅ {len(mp4_files)} MP4-Dateien erfolgreich synchronisiert!")
                return True
                
            except (PermissionError, FileNotFoundError) as e:
                logger.warning(f"⚠️  Lokale Kopie fehlgeschlagen ({type(e).__name__}), versuche rsync...")
            
            # Strategie 2: rsync mit SSH als Fallback
            logger.info(f"🔄 Versuche rsync über SSH...")
            
            source_pattern = f"{str(video_dir)}/*.mp4"
            
            # rsync mit SSH-Syntax
            rsync_cmd = [
                'rsync',
                '-avz',
                '--remove-source-files',
                source_pattern,
                f"imme@localhost:{dest_path}/"
            ]
            
            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info(f"✅ rsync erfolgreich!")
                print(f"✅ rsync erfolgreich!")
                return True
            else:
                logger.error(f"❌ rsync fehlgeschlagen: {result.stderr[:200]}")
                print(f"⚠️  Dateiübertragung fehlgeschlagen - Videos sind lokal auf dem Pi verfügbar")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Dateiübertragung: {e}")
            print(f"⚠️  Dateiübertragung fehlgeschlagen: {e}")
            return False
    
    def _graceful_shutdown(self) -> None:
        """
        Graceful Shutdown: Beendet alle aktiven Prozesse sauber.
        
        1. SIGTERM an rpicam-vid (H264 wird korrekt finalisiert)
        2. SIGTERM an arecord (WAV wird geschlossen)
        3. Warte max 5 Sekunden
        4. SIGKILL als Fallback falls Prozesse hängen
        """
        logger.info("🧹 Starte graceful Shutdown...")
        
        # Killt rpicam-vid mit SIGTERM (graceful)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "rpicam-vid"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            logger.info(f"📺 Sende SIGTERM zu rpicam-vid (PID {pid})...")
                            os.kill(int(pid), 15)  # SIGTERM = graceful
                        except ProcessLookupError:
                            pass
        except Exception as e:
            logger.warning(f"⚠️  Fehler beim SIGTERM zu rpicam-vid: {e}")
        
        # Killt arecord mit SIGTERM (graceful)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "arecord"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            logger.info(f"🔊 Sende SIGTERM zu arecord (PID {pid})...")
                            os.kill(int(pid), 15)  # SIGTERM = graceful
                        except ProcessLookupError:
                            pass
        except Exception as e:
            logger.warning(f"⚠️  Fehler beim SIGTERM zu arecord: {e}")
        
        # Warte 3 Sekunden für graceful shutdown
        logger.info("⏳ Warte 3s für graceful Shutdown...")
        time.sleep(3)
        
        # Fallback: SIGKILL für Prozesse die immer noch laufen
        logger.info("🧹 Fallback: Prüfe auf hängende Prozesse...")
        try:
            result = subprocess.run(
                ["pgrep", "-f", "rpicam-vid"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            logger.warning(f"🛑 Sende SIGKILL zu rpicam-vid (PID {pid})...")
                            os.kill(int(pid), 9)  # SIGKILL = force
                        except ProcessLookupError:
                            pass
        except Exception as e:
            logger.warning(f"⚠️  Fehler beim SIGKILL zu rpicam-vid: {e}")
        
        try:
            result = subprocess.run(
                ["pgrep", "-f", "arecord"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            logger.warning(f"🛑 Sende SIGKILL zu arecord (PID {pid})...")
                            os.kill(int(pid), 9)  # SIGKILL = force
                        except ProcessLookupError:
                            pass
        except Exception as e:
            logger.warning(f"⚠️  Fehler beim SIGKILL zu arecord: {e}")
        
        logger.info("✅ Graceful Shutdown abgeschlossen")

    def run(self):
        """Hauptloop für Camera Monitoring oder manuelle Aufnahme."""
        
        # AUTOMATISCH AUDIO IM MANUELLEN MODUS AKTIVIEREN
        if self.manual_record:
            self.enable_audio = True
            logger.info("🎤 Audio automatisch aktiviert (Manueller Aufnahmemodus)")
        
        # Finde USB-Audio-Device wenn Audio aktiviert
        if self.enable_audio:
            self.audio_device = self._find_usb_audio_device()
            if not self.audio_device:
                logger.warning("⚠️  Audio aktiviert aber kein USB-Gerät gefunden - nur Video wird aufgenommen")
            else:
                logger.info("🎤 USB-Audio bereit für Aufnahme")
        
        # MANUELLER AUFNAHMEMODUS: Synchrone Aufnahme mit Konvertierung
        if self.manual_record or self.skip_detection:
            logger.info(f"🔴 MANUELLER AUFNAHMEMODUS: Starte PARALLELE Video+Audio Aufnahme ({self.recording_duration}s)...")
            print(f"\n======================================================================")
            print(f"🔴 MANUELLE AUFNAHME AKTIVIERT - VOGELERKENNUNG DEAKTIVIERT")
            print(f"======================================================================\n")
            
            # Starte PARALLELE Aufnahme (Video + Audio gleichzeitig mit exakter Dauer Synchronisation)
            video_file, audio_file, stop_event = self._start_recording_manual()
            
            if video_file:
                logger.info(f"✅ Aufnahme erfolgreich abgeschlossen")
                print(f"✅ Aufnahme erfolgreich abgeschlossen")
                print(f"🔄 Konvertiere zu MP4...{'🎤 (mit Audio)' if audio_file else ''}")
                
                # Konvertiere H264 zu MP4 (synchron - warte bis fertig)
                self._convert_h264_to_mp4_sync(Path(video_file), Path(audio_file) if audio_file else None)
                
                # Synchronisiere MP4-Dateien zum lokalen Client
                video_dir = Path(video_file).parent
                logger.info(f"📤 Synchronisiere MP4-Dateien...")
                self._sync_mp4_files_to_client(video_dir)
                
                logger.info("✅ Manueller Aufnahmemodus erfolgreich abgeschlossen")
                print("✅ Fertig - Video ist lokal verfügbar!")
                
                # Graceful Shutdown: Beende alle aktiven Prozesse sauber
                logger.info("🧹 Graceful Shutdown: Beende aktive Prozesse...")
                self._graceful_shutdown()
                
                time.sleep(1)
                sys.exit(0)  # Beende Script
            else:
                logger.error("❌ Konnte Aufnahme nicht starten")
                print("❌ Konnte Aufnahme nicht starten")
                
                # Graceful Shutdown auch bei Fehler
                logger.info("🧹 Graceful Shutdown nach Fehler...")
                self._graceful_shutdown()
                
                sys.exit(1)
        
        # STANDARD ÜBERWACHUNGSMODUS: Nicht mehr unterstützt mit rpicam-vid
        logger.error("❌ FEHLER: Überwachungsmodus (automatische Vogelerkennung) wird mit rpicam-vid nicht unterstützt!")
        logger.error("")
        logger.error("   rpicam-vid kann kein Live-Preview parallel zu H264-Encoding liefern.")
        logger.error("   Daher ist automatische Vogelerkennung bei Echtzeit-Aufnahme nicht möglich.")
        logger.error("")
        logger.error("   ✅ LÖSUNG: Nutze stattdessen den MANUELLEN AUFNAHMEMODUS:")
        logger.error("      python3 unified-camera-monitor.py --manual-record")
        logger.error("")
        logger.error("   Diese Version mit rpicam-vid behebt das Videodauer-Problem!")
        logger.error("   (Korrekte 60s H264 statt 35-36s mit picamera2)")
        logger.error("")
        
        print("❌ FEHLER: Überwachungsmodus nicht unterstützt!")
        print("   Nutze stattdessen: python3 unified-camera-monitor.py --manual-record")
        sys.exit(1)
    
    def _print_status(self):
        """Gibt Status-Informationen mit echten System-Werten und Ampeln aus."""
        runtime = time.time() - self.start_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        
        import subprocess
        import shutil
        
        # CPU-Temperatur (vcgencmd auf Raspberry Pi)
        try:
            temp_output = subprocess.check_output(['vcgencmd', 'measure_temp'], text=True, timeout=2)
            cpu_temp = float(temp_output.strip().split('=')[1].split("'")[0])
        except:
            cpu_temp = 0.0
        
        # CPU-Load Average (Load Average 1min)
        try:
            with open('/proc/loadavg', 'r') as f:
                load_1min = float(f.read().split()[0])
        except:
            load_1min = 0.0
        
        # RAM-Nutzung (aus /proc/meminfo)
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                mem_total = int([l for l in lines if 'MemTotal' in l][0].split()[1]) / 1024  # MB
                mem_available = int([l for l in lines if 'MemAvailable' in l][0].split()[1]) / 1024  # MB
                mem_used = mem_total - mem_available
                mem_percent = (mem_used / mem_total) * 100
        except:
            mem_percent = 0.0
        
        # Festplatten-Info
        disk_usage = shutil.disk_usage(str(self.video_base_path))
        disk_free_gb = disk_usage.free / (1024**3)
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Ampel-Logik (ZEITLUPEN-KRITERIEN)
        # Temperatur: Grün <55°C, Gelb 55-65°C, Rot >65°C
        if cpu_temp < 55:
            temp_icon = "🟢"
        elif cpu_temp < 65:
            temp_icon = "🟡"
        else:
            temp_icon = "🔴"
        
        # Load: Grün <1.5, Gelb 1.5-3.0, Rot >3.0
        if load_1min < 1.5:
            load_icon = "🟢"
        elif load_1min < 3.0:
            load_icon = "🟡"
        else:
            load_icon = "🔴"
        
        # RAM: Grün <75%, Gelb 75-90%, Rot >90%
        if mem_percent < 75:
            mem_icon = "🟢"
        elif mem_percent < 90:
            mem_icon = "🟡"
        else:
            mem_icon = "🔴"
        
        # Festplatte: Grün <90%, Gelb 90-95%, Rot >95%
        if disk_percent < 90:
            disk_icon = "🟢"
        elif disk_percent < 95:
            disk_icon = "🟡"
        else:
            disk_icon = "🔴"
        
        # Status mit echten Werten und Ampeln
        logger.info(f"Status: {hours}h {minutes}min | Aufnahmen: {self.recordings_triggered} | Frames: {self.frames_processed} | Temp: {temp_icon}{cpu_temp:.1f}°C | Load: {load_icon}{load_1min:.2f} | RAM: {mem_icon}{mem_percent:.0f}% | Disk: {disk_icon}{disk_free_gb:.1f}GB")
        
        # NOTFALL-STOPP bei kritischer Temperatur (>75°C)
        if cpu_temp >= 75:
            logger.critical(f"🔥 NOTFALL-STOPP: CPU-Temperatur {cpu_temp:.1f}°C überschreitet Limit von 75°C")
            print(f"\n� NOTFALL-STOPP: CPU-Temperatur kritisch ({cpu_temp:.1f}°C)!")
            self.stop()
            import sys
            sys.exit(1)
        
        # WARNUNG bei hoher Load (>3.0 kritisch für Zeitlupe)
        if load_1min >= 3.0:
            logger.warning(f"⚠️  CPU-Last kritisch: {load_1min:.2f} (Limit: 3.0)")
        
        # WARNUNG bei kritischer Festplatte
        if disk_percent >= 95:
            logger.warning(f"⚠️  Festplatte kritisch: Nur noch {disk_free_gb:.1f} GB frei!")


def main():
    """Hauptfunktion."""
    # SOFORTIGE CLEANUP vor allem anderen
    cleanup_old_processes()
    time.sleep(1)
    
    parser = argparse.ArgumentParser(
        description='Unified Camera Monitor für Vogel-Kamera-Linux',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--camera', type=int, default=0, help='Kamera-Nummer (0 oder 1)')
    parser.add_argument('--threshold', type=float, default=0.4, help='AI-Erkennungs-Schwelle (default: 0.4)')
    parser.add_argument('--cooldown', type=int, default=15, help='Cooldown zwischen Aufnahmen in Sekunden (default: 15)')
    parser.add_argument('--trigger-duration', type=float, default=1.0, help='Mindest-Dauer für Trigger in Sekunden (default: 1.0)')
    parser.add_argument('--video-path', type=str, default=None, help='Basis-Pfad für Videos (default: ~/Videos/Vogelhaus)')
    parser.add_argument('--model', type=str, help='Pfad zum YOLO-Model (optional)')
    parser.add_argument('--preview-fps', type=int, default=6, help='Preview FPS (default: 6)')
    parser.add_argument('--recording-width', type=int, default=4096, help='Aufnahme-Breite (default: 4096 - Cinema 4K)')
    parser.add_argument('--recording-height', type=int, default=2160, help='Aufnahme-Höhe (default: 2160 - Cinema 4K)')
    parser.add_argument('--recording-fps', type=int, default=30, help='Aufnahme-FPS (default: 30)')
    parser.add_argument('--recording-duration', type=int, default=60, help='Aufnahme-Dauer in Sekunden (default: 60)')
    parser.add_argument('--duration-seconds', type=int, default=None, help='Überschreibe Aufnahme-Dauer in Sekunden')
    
    # rpicam-vid spezifische Parameter (wie alte Lösung)
    parser.add_argument('--rotation', type=int, choices=[0, 90, 180, 270], default=180, help='Rotation des Videos (default: 180 - Vogelbild oben)')
    parser.add_argument('--codec', type=str, default='h264', help='Video-Codec (default: h264)')
    parser.add_argument('--hdr', type=str, choices=['auto', 'off'], default='off', help='HDR-Modus (default: off)')
    parser.add_argument('--autofocus-mode', type=str, default='continuous', help='Autofokus-Modus (default: continuous)')
    parser.add_argument('--autofocus-range', type=str, default='macro', help='Autofokus-Bereich (default: macro)')
    parser.add_argument('--roi', type=str, help='Region of Interest im Format x,y,w,h (optional)')
    
    parser.add_argument('--slowmo', action='store_true', help='Zeitlupen-Modus HQ (2304x1296 @ 56fps, überschreibt Auflösung/FPS)')
    parser.add_argument('--slowmo-fast', action='store_true', help='Zeitlupen-Modus Ultra-Highspeed (1536x864 @ 120fps, überschreibt Auflösung/FPS)')
    parser.add_argument('--enable-audio', action='store_true', help='Audio-Aufnahme aktivieren')
    parser.add_argument('--audio-only', action='store_true', help='Nur Audio aufnehmen (kein Video)')
    parser.add_argument('--manual-record', action='store_true', help='Manuelle Aufnahme ohne Trigger/Erkennung')
    parser.add_argument('--skip-detection', action='store_true', help='Vogelerkennung überspringen')
    parser.add_argument('--bitrate', type=str, default=None, help='Video-Bitrate (z.B. 5000k, 8000k)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    
    args = parser.parse_args()
    
    # Banner im klassischen Format
    print("\n" + "=" * 70)
    print("🐦 UNIFIED CAMERA MONITOR - Vogel-Kamera-Linux")
    print("=" * 70 + "\n")
    
    # Zeitlupen-Modus: Überschreibe Auflösung und FPS
    if args.slowmo:
        print("=" * 70)
        print("🎬 ZEITLUPEN-MODUS HQ AKTIVIERT (Bessere Qualität)")
        print(f"📹 Auflösung: {2304}x{1296} @ {56}fps")
        print("=" * 70 + "\n")
        args.recording_width = 2304
        args.recording_height = 1296
        args.recording_fps = 56
    
    if args.slowmo_fast:
        print("=" * 70)
        print("🎬 ZEITLUPEN-MODUS 120FPS AKTIVIERT (Ultra-Highspeed)")
        print(f"📹 Auflösung: {1536}x{864} @ {120}fps")
        print("=" * 70 + "\n")
        args.recording_width = 1536
        args.recording_height = 864
        args.recording_fps = 120
    
    # Überschreibe recording_duration mit duration-seconds, falls angegeben
    if args.duration_seconds is not None:
        args.recording_duration = args.duration_seconds
    
    # Manuelle Aufnahme: Hinweis
    if args.manual_record or args.skip_detection:
        print("=" * 70)
        print("🔴 MANUELLE AUFNAHME AKTIVIERT - VOGELERKENNUNG DEAKTIVIERT")
        print("=" * 70 + "\n")
        # Setze sehr hohen Threshold, damit Erkennung quasi nie triggert
        args.threshold = 0.99
        args.cooldown = 0
    
    # Erstelle Monitor
    monitor = UnifiedCameraMonitor(
        camera_num=args.camera,
        threshold=args.threshold,
        cooldown=args.cooldown,
        trigger_duration=args.trigger_duration,
        video_base_path=args.video_path,
        model_path=args.model,
        preview_fps=args.preview_fps,
        recording_width=args.recording_width,
        recording_height=args.recording_height,
        recording_fps=args.recording_fps,
        recording_duration=args.recording_duration,
        rotation=args.rotation,
        codec=args.codec,
        hdr=args.hdr,
        autofocus_mode=args.autofocus_mode,
        autofocus_range=args.autofocus_range,
        roi=args.roi,
        enable_audio=args.enable_audio,
        manual_record=args.manual_record,
        skip_detection=args.skip_detection,
        debug=args.debug
    )
    
    # Starte Monitor
    if monitor.start():
        try:
            monitor.run()
        except KeyboardInterrupt:
            logger.info("\n🛑 Beendet durch Benutzer")
        finally:
            monitor.stop()
    else:
        logger.error("❌ Konnte Monitor nicht starten")
        sys.exit(1)


if __name__ == "__main__":
    main()
