#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DETECT-ONLY Monitor für Vogel-Kamera-Linux
============================================

Schlanker Detection-only Prozess der:
- KEINE Videos speichert
- NUR Vogel-Erkennung durchführt (YOLO)
- Loggt Erkennungen
- Sauber bei Signal beendet werden kann

Verwendung:
    python3 unified-camera-monitor-detect-only.py --threshold 0.4 --cooldown 15 --trigger-duration 1.0

Features:
- Minimal-CPU-Last (nur Detection, kein Video-Encoding)
- Schnelle Vogel-Erkennung
- Clean shutdown mit SIGTERM
- Einfaches Log-Interface für Client-Seite
"""

import argparse
import cv2
import numpy as np
import time
import os
import sys
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import logging

# Picamera2 Import
try:
    from picamera2 import Picamera2
    from libcamera import Transform
    HAS_PICAMERA2 = True
except ImportError:
    HAS_PICAMERA2 = False
    print("❌ picamera2 nicht installiert!")
    sys.exit(1)

# YOLO Import
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("❌ Ultralytics YOLO nicht installiert!")
    sys.exit(1)

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


class DetectionOnlyMonitor:
    """
    Schlanker Detection-only Monitor - KEINE Video-Speicherung!
    """
    
    def __init__(
        self,
        camera_num: int = 0,
        threshold: float = 0.4,
        cooldown: int = 15,
        trigger_duration: float = 1.0,
        model_path: Optional[str] = None,
        preview_width: int = 640,
        preview_height: int = 480,
        preview_fps: int = 6,
        debug: bool = False
    ):
        """Initialisiert Detection-only Monitor."""
        self.camera_num = camera_num
        self.threshold = threshold
        self.cooldown = cooldown
        self.trigger_duration = trigger_duration
        self.preview_width = preview_width
        self.preview_height = preview_height
        self.preview_fps = preview_fps
        self.debug = debug
        
        # Picamera2 Setup
        self.picam2: Optional[Picamera2] = None
        
        # AI Model
        self.model: Optional[YOLO] = None
        self.model_path = model_path
        
        # Detection State
        self.detection_history = []
        self.first_detection_time = None
        self.last_trigger_time = 0
        
        # Statistics
        self.frames_processed = 0
        self.birds_detected = 0
        self.start_time = time.time()
        
        # Shutdown Signal
        self.stop_event = False
        
        logger.info("DetectionOnlyMonitor initialisiert")
        logger.info(f"  Threshold: {threshold}")
        logger.info(f"  Cooldown: {cooldown}s")
        logger.info(f"  Trigger-Duration: {trigger_duration}s")
    
    def _setup_signal_handlers(self):
        """Setup für SIGTERM/SIGINT Handling."""
        def signal_handler(signum, frame):
            logger.info(f"\n⚠️  Signal {signum} empfangen - fahre herunter...")
            self.stop_event = True
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def _load_model(self) -> bool:
        """Lädt YOLO-Model für Vogel-Erkennung."""
        try:
            if self.model_path and Path(self.model_path).exists():
                logger.info(f"📦 Lade Custom Model: {self.model_path}")
                self.model = YOLO(self.model_path)
            else:
                logger.info("📦 Lade YOLO26n (Standard-Model)")
                self.model = YOLO("yolo26n.pt")
            
            logger.info("✅ YOLO-Model geladen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Models: {e}")
            return False
    
    def _setup_camera(self) -> bool:
        """Initialisiert Picamera2 mit Preview (KEIN Encode Output!)."""
        try:
            self.picam2 = Picamera2(self.camera_num)
            
            # MINIMAL Config: Nur für Preview/Analyse, kein Encoding
            config = self.picam2.create_video_configuration(
                main={
                    "size": (self.preview_width, self.preview_height),
                    "format": "RGB888"  # Direkt RGB für schnelle Analyse
                },
                transform=Transform(hflip=1, vflip=1)  # 180° Rotation
            )
            
            self.picam2.configure(config)
            
            # Setze minimale Kamera-Parameter
            self.picam2.set_controls({
                "FrameRate": self.preview_fps,
                "ExposureTime": 10000,  # Auto
                "AnalogueGain": 1.0
            })
            
            logger.info(f"✅ Picamera2 konfiguriert (Preview-only: {self.preview_width}x{self.preview_height}@{self.preview_fps}fps)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Kamera-Setup Fehler: {e}")
            return False
    
    def start(self) -> bool:
        """Startet Detection Monitor."""
        logger.info("🚀 Starte DETECTION-ONLY Monitor (kein Video-Speicherung)...")
        
        # Setup Signal Handling
        self._setup_signal_handlers()
        
        # Lade Model
        if not self._load_model():
            logger.error("❌ Model konnte nicht geladen werden")
            return False
        
        # Setup Kamera
        if not self._setup_camera():
            logger.error("❌ Kamera-Setup fehlgeschlagen")
            return False
        
        # Starte Kamera
        try:
            self.picam2.start()
            logger.info("✅ Kamera gestartet")
            print("🎥 DETECTION-ONLY MONITOR LÄUFT - Überwache auf Vögel...")
            time.sleep(1)  # Stabilisierungszeit
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Kamera: {e}")
            return False
    
    def stop(self):
        """Stoppt Monitor sauber."""
        logger.info("🛑 Stoppe Detection Monitor...")
        
        if self.picam2:
            try:
                if self.picam2.started:
                    self.picam2.stop()
                    logger.info("Kamera gestoppt")
                
                self.picam2.close()
                logger.info("✅ Kamera geschlossen")
            except Exception as e:
                logger.error(f"Fehler beim Stoppen: {e}")
    
    def _detect_bird(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Führt Vogel-Erkennung durch (COCO class 14 = bird).
        
        Args:
            frame: Frame für Analyse (RGB888)
            
        Returns:
            (bird_detected, max_confidence)
        """
        if not self.model:
            return False, 0.0
        
        try:
            # YOLO Inference (sehr schnell auf RPi mit yolo26n)
            results = self.model(frame, verbose=False, conf=self.threshold)
            
            # Prüfe auf Vögel (COCO class 14)
            max_confidence = 0.0
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Class 14 = bird in COCO dataset
                        if class_id == 14 and confidence >= self.threshold:
                            max_confidence = max(max_confidence, confidence)
            
            return max_confidence > 0, max_confidence
            
        except Exception as e:
            logger.warning(f"Fehler bei Detection: {e}")
            return False, 0.0
    
    def _check_trigger(self, bird_detected: bool, confidence: float = 0.0) -> bool:
        """
        Prüft ob Trigger-Bedingungen erfüllt sind (mit Konsistenz-Check).
        
        Args:
            bird_detected: Ob Vogel im Frame erkannt wurde
            confidence: Erkennungs-Konfidenz (0.0-1.0)
            
        Returns:
            True wenn Trigger bedingt sind, False sonst
        """
        current_time = time.time()
        
        # Cooldown-Check
        if current_time - self.last_trigger_time < self.cooldown:
            remaining = self.cooldown - (current_time - self.last_trigger_time)
            if self.frames_processed % 30 == 0:  # Log alle 30 Frames (~5 Sekunden)
                logger.debug(f"⏳ Cooldown aktiv - noch {remaining:.0f}s")
            return False
        
        if bird_detected:
            # Erste Erkennung?
            if self.first_detection_time is None:
                self.first_detection_time = current_time
                logger.info(f"🐦 Vogel erkannt! (Confidence: {confidence*100:.0f}%) - Warte {self.trigger_duration}s...")
            
            # Füge zur History hinzu
            self.detection_history.append((current_time, True, confidence))
            
            # Prüfe ob Dauer erfüllt ist
            duration = current_time - self.first_detection_time
            
            if duration >= self.trigger_duration:
                # Prüfe Konsistenz (60% der Frames müssen Vogel enthalten)
                recent = [d for t, d, _ in self.detection_history if t >= current_time - self.trigger_duration]
                if len(recent) > 0:
                    consistency = sum(recent) / len(recent)
                    
                    if consistency >= 0.6:
                        avg_confidence = np.mean([c for t, d, c in self.detection_history if d])
                        print(f"🎥 TRIGGER! Vogel erkannt: {duration:.1f}s @ {avg_confidence*100:.0f}% Confidence")
                        logger.info(f"✅ TRIGGER-BEDINGUNGEN ERFÜLLT!")
                        logger.info(f"   - Dauer: {duration:.1f}s")
                        logger.info(f"   - Konsistenz: {consistency*100:.0f}%")
                        logger.info(f"   - Avg Confidence: {avg_confidence*100:.0f}%")
                        
                        self.birds_detected += 1
                        self.first_detection_time = None
                        self.detection_history = []
                        self.last_trigger_time = current_time
                        return True
        else:
            # Vogel verloren
            if self.first_detection_time is not None:
                duration = current_time - self.first_detection_time
                if duration > 0.5:  # Nur loggen wenn längere Zeit erkannt
                    logger.debug(f"❌ Vogel-Erkennung beendet (war {duration:.1f}s)")
                self.first_detection_time = None
                self.detection_history = []
        
        # Bereinige alte Einträge aus History
        self.detection_history = [(t, d, c) for t, d, c in self.detection_history if t >= current_time - self.trigger_duration]
        
        return False
    
    def run(self) -> bool:
        """
        Hauptschleife: Kontinuierliche Detection bis Signal.
        
        Returns:
            True wenn Vogel erkannt wurde, False wenn abgebrochen
        """
        logger.info("🔄 Starte Detection-Schleife...")
        
        try:
            while not self.stop_event:
                try:
                    # Capture Frame
                    frame = self.picam2.capture_array()
                    self.frames_processed += 1
                    
                    # Detection
                    bird_detected, confidence = self._detect_bird(frame)
                    
                    # Trigger-Check
                    if self._check_trigger(bird_detected, confidence):
                        logger.info("✅ Beende Detection - Vogel erkannt!")
                        return True
                    
                    # Status-Output alle 300 Frames (~50 Sekunden)
                    if self.frames_processed % 300 == 0:
                        elapsed = time.time() - self.start_time
                        fps = self.frames_processed / elapsed
                        logger.info(f"📊 Status: {self.frames_processed} Frames, {fps:.1f} FPS, {self.birds_detected} Trigger(s)")
                    
                    # Kleine Pause um CPU nicht zu überlasten
                    time.sleep(0.01)
                
                except KeyboardInterrupt:
                    logger.info("🛑 Benutzer-Interrupt")
                    return False
                except Exception as e:
                    logger.error(f"Fehler in Detection-Schleife: {e}")
                    time.sleep(1)
                    continue
        
        finally:
            self.stop()
        
        return False


def main():
    """Hauptfunktion mit CLI."""
    parser = argparse.ArgumentParser(
        description="DETECTION-ONLY Monitor - Fokussiert auf Vogel-Erkennung ohne Video"
    )
    parser.add_argument('--threshold', type=float, default=0.4, help='Erkennungs-Schwelle (0.0-1.0)')
    parser.add_argument('--cooldown', type=int, default=15, help='Cooldown zwischen Triggern (Sekunden)')
    parser.add_argument('--trigger-duration', type=float, default=1.0, help='Mindest-Dauer für Trigger (Sekunden)')
    parser.add_argument('--camera', type=int, default=0, help='Kamera-Nummer (0 oder 1)')
    parser.add_argument('--model', type=str, default=None, help='Pfad zu Custom YOLO Model')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    
    args = parser.parse_args()
    
    # Erstelle Monitor
    monitor = DetectionOnlyMonitor(
        camera_num=args.camera,
        threshold=args.threshold,
        cooldown=args.cooldown,
        trigger_duration=args.trigger_duration,
        model_path=args.model,
        debug=args.debug
    )
    
    # Starte
    if not monitor.start():
        logger.error("❌ Monitor konnte nicht gestartet werden")
        sys.exit(1)
    
    # Hauptschleife
    try:
        bird_found = monitor.run()
        
        if bird_found:
            print("\n✅ VOGEL ERKANNT - Beende Detection")
            sys.exit(0)
        else:
            print("\n🛑 Detection beendet ohne Erkennung")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Benutzer-Abort")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
