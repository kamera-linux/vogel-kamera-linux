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
from datetime import datetime
from pathlib import Path
import threading
import logging
from typing import Optional, Tuple, Dict, Any

# Picamera2 Import
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, Quality
    from picamera2.outputs import FileOutput
    HAS_PICAMERA2 = True
except ImportError:
    HAS_PICAMERA2 = False
    print("⚠️  picamera2 nicht installiert. Installiere mit: pip install picamera2")
    sys.exit(1)

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
        video_base_path: str = "/home/roimme/Videos/Vogelhaus",
        model_path: Optional[str] = None,
        preview_width: int = 640,
        preview_height: int = 480,
        preview_fps: int = 6,
        recording_width: int = 1920,
        recording_height: int = 1080,
        recording_fps: int = 30,
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
            debug: Debug-Modus aktivieren
        """
        self.camera_num = camera_num
        self.threshold = threshold
        self.cooldown = cooldown
        self.trigger_duration = trigger_duration
        self.video_base_path = Path(video_base_path)
        self.preview_width = preview_width
        self.preview_height = preview_height
        self.preview_fps = preview_fps
        self.recording_width = recording_width
        self.recording_height = recording_height
        self.recording_fps = recording_fps
        self.debug = debug
        
        # Picamera2 Setup
        self.picam2: Optional[Picamera2] = None
        
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
                logger.info("Lade YOLOv8n (Standard)")
                self.model = YOLO("yolov8n.pt")
            
            logger.info("✅ YOLO-Model geladen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Models: {e}")
            return False
    
    def _setup_camera(self) -> bool:
        """Initialisiert Picamera2 mit Dual-Stream Config."""
        try:
            self.picam2 = Picamera2(self.camera_num)
            
            # Dual-Stream Konfiguration
            # Stream 0: Haupt-Stream für Aufnahme (hohe Qualität)
            # Stream 1: Low-Res Stream für Preview/AI-Analyse
            config = self.picam2.create_video_configuration(
                main={
                    "size": (self.recording_width, self.recording_height),
                    "format": "RGB888"
                },
                lores={
                    "size": (self.preview_width, self.preview_height),
                    "format": "RGB888"
                },
                display=None,
                encode=None
            )
            
            self.picam2.configure(config)
            
            # Setze Kamera-Parameter
            self.picam2.set_controls({
                "FrameRate": self.preview_fps,
                "ExposureTime": 10000,  # Auto
                "AnalogueGain": 1.0
            })
            
            logger.info("✅ Picamera2 konfiguriert (Dual-Stream)")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Setup der Kamera: {e}")
            return False
    
    def start(self) -> bool:
        """Startet Camera Monitor."""
        logger.info("🎬 Starte Unified Camera Monitor...")
        
        # Lade Model
        if not self._load_model():
            logger.warning("⚠️  Fahre ohne AI-Model fort (Fallback-Modus)")
        
        # Setup Kamera
        if not self._setup_camera():
            logger.error("❌ Kamera-Setup fehlgeschlagen")
            return False
        
        # Starte Kamera
        try:
            self.picam2.start()
            logger.info("✅ Kamera gestartet")
            time.sleep(2)  # Stabilisierungszeit
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Kamera: {e}")
            return False
    
    def stop(self):
        """Stoppt Camera Monitor."""
        logger.info("🛑 Stoppe Camera Monitor...")
        self.stop_event.set()
        
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
                logger.info("✅ Kamera gestoppt")
            except Exception as e:
                logger.error(f"Fehler beim Stoppen: {e}")
    
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
        Startet Video-Aufnahme.
        
        Returns:
            Pfad zur Video-Datei oder None bei Fehler
        """
        with self.recording_lock:
            if self.is_recording:
                logger.warning("⚠️  Aufnahme läuft bereits")
                return None
            
            # Prüfe Cooldown
            current_time = time.time()
            if current_time - self.last_recording_time < self.cooldown:
                remaining = self.cooldown - (current_time - self.last_recording_time)
                logger.info(f"⏳ Cooldown aktiv - noch {remaining:.0f}s")
                return None
            
            try:
                # Erstelle Dateinamen
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_file = self.video_base_path / f"vogel_{timestamp}.h264"
                
                logger.info(f"🎥 Starte Aufnahme: {video_file}")
                
                # Starte Encoder für Haupt-Stream
                encoder = H264Encoder()
                output = FileOutput(str(video_file))
                
                self.picam2.start_recording(encoder, output)
                
                self.is_recording = True
                self.recordings_triggered += 1
                
                # Aufnahme-Thread starten (30 Sekunden)
                def stop_recording_after_delay():
                    time.sleep(30)
                    self._stop_recording()
                
                threading.Thread(target=stop_recording_after_delay, daemon=True).start()
                
                return str(video_file)
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Starten der Aufnahme: {e}")
                self.is_recording = False
                return None
    
    def _stop_recording(self):
        """Stoppt laufende Aufnahme."""
        with self.recording_lock:
            if not self.is_recording:
                return
            
            try:
                self.picam2.stop_recording()
                self.is_recording = False
                self.last_recording_time = time.time()
                logger.info("✅ Aufnahme beendet")
                logger.info(f"⏳ Cooldown: {self.cooldown} Sekunden")
                
            except Exception as e:
                logger.error(f"Fehler beim Stoppen der Aufnahme: {e}")
    
    def run(self):
        """Hauptloop für Camera Monitoring."""
        logger.info("🔍 Überwache Vogelhaus... (Strg+C zum Beenden)\n")
        
        frame_count = 0
        last_status_time = time.time()
        status_interval = 300  # 5 Minuten
        
        try:
            while not self.stop_event.is_set():
                try:
                    # Hole Low-Res Frame für AI-Analyse
                    frame = self.picam2.capture_array("lores")
                    
                    if frame is None:
                        logger.warning("⚠️  Kein Frame empfangen")
                        time.sleep(0.1)
                        continue
                    
                    # Vogel-Erkennung
                    bird_detected, confidence = self._detect_bird(frame)
                    
                    # Prüfe Trigger
                    if self._check_trigger(bird_detected):
                        # Cooldown prüfen und Aufnahme starten
                        video_file = self._start_recording()
                        if video_file:
                            logger.info(f"📹 Aufnahme gestartet: {video_file}")
                    
                    # Statistiken
                    self.frames_processed += 1
                    frame_count += 1
                    
                    # Status-Report alle 5 Minuten
                    current_time = time.time()
                    if current_time - last_status_time >= status_interval:
                        self._print_status()
                        last_status_time = current_time
                    
                    # Warte für nächsten Frame (FPS-Kontrolle)
                    time.sleep(1.0 / self.preview_fps)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Fehler im Monitoring-Loop: {e}")
                    time.sleep(1)
        
        finally:
            self.stop()
    
    def _print_status(self):
        """Gibt Status-Informationen aus."""
        runtime = time.time() - self.start_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        
        logger.info("=" * 70)
        logger.info(f"📊 STATUS-REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        logger.info(f"⏱️  Laufzeit: {hours}h {minutes}min")
        logger.info(f"🎬 Aufnahmen getriggert: {self.recordings_triggered}")
        logger.info(f"🖼️  Frames verarbeitet: {self.frames_processed}")
        logger.info(f"📊 FPS: {self.frames_processed / runtime:.1f}")
        logger.info("=" * 70 + "\n")


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description='Unified Camera Monitor für Vogel-Kamera-Linux',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--camera', type=int, default=0, help='Kamera-Nummer (0 oder 1)')
    parser.add_argument('--threshold', type=float, default=0.4, help='AI-Erkennungs-Schwelle (default: 0.4)')
    parser.add_argument('--cooldown', type=int, default=15, help='Cooldown zwischen Aufnahmen in Sekunden (default: 15)')
    parser.add_argument('--trigger-duration', type=float, default=1.0, help='Mindest-Dauer für Trigger in Sekunden (default: 1.0)')
    parser.add_argument('--video-path', type=str, default='/home/roimme/Videos/Vogelhaus', help='Basis-Pfad für Videos')
    parser.add_argument('--model', type=str, help='Pfad zum YOLO-Model (optional)')
    parser.add_argument('--preview-fps', type=int, default=6, help='Preview FPS (default: 6)')
    parser.add_argument('--recording-width', type=int, default=1920, help='Aufnahme-Breite (default: 1920)')
    parser.add_argument('--recording-height', type=int, default=1080, help='Aufnahme-Höhe (default: 1080)')
    parser.add_argument('--recording-fps', type=int, default=30, help='Aufnahme-FPS (default: 30)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    
    args = parser.parse_args()
    
    # Banner
    print("\n" + "="*70)
    print("🐦 Unified Camera Monitor - Vogel-Kamera-Linux")
    print("="*70 + "\n")
    
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
