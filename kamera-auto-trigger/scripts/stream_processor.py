#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stream Processor für Auto-Trigger System
=========================================

Verarbeitet Preview-Stream vom Raspberry Pi und führt Echtzeit-Objekterkennung durch.

Features:
- TCP/RTSP Stream-Verarbeitung
- OpenCV/GStreamer Frame-Grabbing
- YOLOv8-Integration
- bird-species Model Support
- Multi-Threading für Performance

Verwendung:
    from stream_processor import StreamProcessor
    
    processor = StreamProcessor(
        host="raspberrypi-5-ai-had",
        port=8554,
        model_type="bird-species",
        threshold=0.45
    )
    
    if processor.connect():
        bird_detected = processor.process_frame()
        if bird_detected:
            print("🐦 Vogel erkannt!")
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import logging

# Conditional imports
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("⚠️  Ultralytics YOLO nicht installiert. Installiere mit: pip install ultralytics")

# Logger setup
logger = logging.getLogger(__name__)


class StreamProcessor:
    """
    Verarbeitet Video-Stream vom Raspberry Pi mit AI-Objekterkennung.
    """
    
    def __init__(
        self,
        host: str,
        port: int = 8554,
        model_type: str = "bird-species",
        model_path: Optional[str] = None,
        threshold: float = 0.45,
        width: int = 640,
        height: int = 480,
        fps: int = 5,
        timeout: int = 10,
        trigger_duration: float = 2.0,
        debug: bool = False
    ):
        """
        Initialisiert StreamProcessor.
        
        Args:
            host: Hostname oder IP des Raspberry Pi
            port: TCP-Port für Stream
            model_type: AI-Model-Typ (yolov8, bird-species, custom)
            model_path: Pfad zu Custom-Model (nur bei model_type=custom)
            threshold: Erkennungs-Schwelle (0.0 - 1.0)
            width: Stream-Breite
            height: Stream-Höhe
            fps: Erwartete Framerate
            timeout: Timeout für Stream-Verbindung (Sekunden)
            trigger_duration: Mindest-Dauer in Sekunden für Trigger (default: 2.0)
            debug: Debug-Modus aktivieren
        """
        self.host = host
        self.port = port
        self.model_type = model_type
        self.model_path = model_path
        self.threshold = threshold
        self.width = width
        self.height = height
        self.fps = fps
        self.timeout = timeout
        self.trigger_duration = trigger_duration
        self.debug = debug
        
        # Stream-Verbindung
        self.cap: Optional[cv2.VideoCapture] = None
        self.connected = False
        self.stream_url = f"tcp://{host}:{port}"
        
        # Detection History für Trigger-Dauer
        self.detection_history = []  # Liste von (timestamp, detected) Tuples
        self.first_detection_time = None
        
        # AI-Model
        self.model: Optional[Any] = None
        self.model_loaded = False
        
        # Statistics
        self.frames_processed = 0
        self.birds_detected = 0
        self.last_detection_time = 0
        self.avg_inference_time = 0
        
        # Threading
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        
        logger.info(f"StreamProcessor initialisiert: {self.stream_url}")
    
    def _load_model(self) -> bool:
        """
        Lädt AI-Model für Objekterkennung.
        
        Returns:
            True wenn erfolgreich, sonst False
        """
        if not HAS_YOLO:
            logger.error("Ultralytics YOLO nicht verfügbar")
            return False
        
        try:
            # Bestimme Modell-Pfad relativ zum Script-Verzeichnis
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            model_file = project_root / "config" / "models" / "yolov8n.pt"
            
            if not model_file.exists():
                logger.error(f"Model-File nicht gefunden: {model_file}")
                logger.info("Fallback: Lade von Ultralytics (wird heruntergeladen)...")
                model_file = "yolov8n.pt"
            else:
                logger.info(f"Verwende lokales Model: {model_file}")
            
            if self.model_type == "bird-species":
                logger.info("Lade bird-species Model (COCO class 14: bird)...")
                self.model = YOLO(str(model_file))  # Nano-Model für Performance
                self.bird_class_id = 14  # COCO class ID für "bird"
                
            elif self.model_type == "yolov8":
                logger.info("Lade YOLOv8 Model...")
                self.model = YOLO(str(model_file))
                self.bird_class_id = 14
                
            elif self.model_type == "custom" and self.model_path:
                logger.info(f"Lade Custom Model: {self.model_path}...")
                if not Path(self.model_path).exists():
                    logger.error(f"Model-File nicht gefunden: {self.model_path}")
                    return False
                self.model = YOLO(self.model_path)
                self.bird_class_id = None  # Custom model kann andere IDs haben
                
            else:
                logger.error(f"Ungültiger Model-Typ: {self.model_type}")
                return False
            
            # Test-Inferenz für Model-Initialisierung
            dummy = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            _ = self.model(dummy, verbose=False)
            
            self.model_loaded = True
            logger.info("✅ AI-Model erfolgreich geladen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Models: {e}")
            return False
    
    def connect(self) -> bool:
        """
        Verbindet mit Preview-Stream.
        
        Returns:
            True wenn erfolgreich, sonst False
        """
        try:
            logger.info(f"Verbinde mit Stream: {self.stream_url}...")
            logger.info(f"   Timeout: {self.timeout}s")
            
            # GStreamer-Pipeline für TCP-Stream
            gst_pipeline = (
                f"tcpclientsrc host={self.host} port={self.port} timeout={self.timeout * 1000000} ! "
                "h264parse ! "
                "avdec_h264 ! "
                "videoconvert ! "
                "appsink drop=1 sync=0"
            )
            
            # Versuche verschiedene Backends
            backends = [
                (cv2.CAP_GSTREAMER, gst_pipeline),
                (cv2.CAP_FFMPEG, self.stream_url),
            ]
            
            logger.info("   Versuche Backend: GStreamer...")
            for backend, source in backends:
                try:
                    self.cap = cv2.VideoCapture(source, backend)
                    
                    # Warte kurz auf Verbindung
                    import time
                    time.sleep(1)
                    
                    if self.cap.isOpened():
                        logger.info(f"   VideoCapture geöffnet, lese Test-Frame...")
                        # Test-Frame lesen mit Timeout
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            logger.info(f"✅ Stream-Verbindung erfolgreich (Backend: {backend})")
                            logger.info(f"   Frame-Size: {frame.shape[1]}x{frame.shape[0]}")
                            self.connected = True
                            
                            # AI-Model laden
                            if not self.model_loaded:
                                if not self._load_model():
                                    logger.warning("Model konnte nicht geladen werden, verwende Fallback")
                            
                            return True
                        else:
                            logger.warning(f"   Kein Frame empfangen von Backend {backend}")
                            self.cap.release()
                            
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Backend {backend} fehlgeschlagen: {e}")
                    logger.info(f"   Backend {backend} nicht verfügbar, versuche nächstes...")
                    continue
            
            logger.error("❌ Konnte keine Verbindung zum Stream herstellen")
            logger.error("   Geprüfte Backends: GStreamer, FFMPEG")
            return False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Verbinden: {e}")
            return False
    
    def disconnect(self):
        """
        Trennt Stream-Verbindung.
        """
        self.stop_event.set()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.connected = False
        logger.info("Stream-Verbindung getrennt")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Liest einen Frame vom Stream.
        
        Returns:
            (success, frame) Tuple
        """
        if not self.connected or not self.cap:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                logger.warning("Konnte Frame nicht lesen")
                return False, None
            
            return True, frame
            
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Frames: {e}")
            return False, None
    
    def detect_objects(self, frame: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """
        Führt Objekterkennung auf Frame durch.
        
        Args:
            frame: Input-Frame (BGR-Format)
            
        Returns:
            (bird_detected, detection_info) Tuple
        """
        if not self.model_loaded or not self.model:
            return False, {}
        
        start_time = time.time()
        
        try:
            # YOLOv8-Inferenz mit CPU-Optimierung
            results = self.model(
                frame,
                verbose=False,
                conf=self.threshold,
                iou=0.45,
                max_det=5,  # Limitiere Detektionen für Performance
                imgsz=320   # CPU-Optimierung: Kleinere Inferenz-Auflösung (statt 640)
            )
            
            inference_time = time.time() - start_time
            
            # Update durchschnittliche Inferenz-Zeit
            if self.avg_inference_time == 0:
                self.avg_inference_time = inference_time
            else:
                self.avg_inference_time = 0.9 * self.avg_inference_time + 0.1 * inference_time
            
            # Parse Ergebnisse
            bird_detected = False
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Prüfe ob Vogel (bird-species: nur class 14)
                    if self.model_type == "bird-species" and cls_id != self.bird_class_id:
                        continue
                    
                    # Bei YOLOv8: auch nur Vögel
                    if self.model_type == "yolov8" and cls_id != self.bird_class_id:
                        continue
                    
                    bird_detected = True
                    
                    # Bounding Box
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    detections.append({
                        "class_id": cls_id,
                        "class_name": result.names[cls_id],
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })
            
            detection_info = {
                "bird_detected": bird_detected,
                "num_detections": len(detections),
                "detections": detections,
                "inference_time": inference_time,
                "timestamp": time.time()
            }
            
            if bird_detected:
                self.birds_detected += 1
                self.last_detection_time = time.time()
            
            return bird_detected, detection_info
            
        except Exception as e:
            logger.error(f"Fehler bei Objekterkennung: {e}")
            return False, {}
    
    def process_frame(self) -> bool:
        """
        Verarbeitet einen Frame: Lesen + Objekterkennung.
        Trigger nur wenn Vogel für mindestens trigger_duration Sekunden erkannt wurde.
        
        Returns:
            True wenn Vogel konsistent erkannt (Trigger-Bedingung erfüllt), sonst False
        """
        with self.lock:
            # Frame lesen
            ret, frame = self.read_frame()
            
            if not ret or frame is None:
                return False
            
            self.frames_processed += 1
            current_time = time.time()
            
            # Objekterkennung
            bird_detected, info = self.detect_objects(frame)
            
            # Aktualisiere Detection-History
            self.detection_history.append((current_time, bird_detected))
            
            # Bereinige alte Einträge (älter als trigger_duration)
            self.detection_history = [
                (t, d) for t, d in self.detection_history 
                if current_time - t <= self.trigger_duration
            ]
            
            # Prüfe ob Vogel konsistent erkannt wurde
            if bird_detected:
                # Erste Erkennung? Starte Timer
                if self.first_detection_time is None:
                    self.first_detection_time = current_time
                    if self.debug:
                        logger.debug(f"🐦 Vogel erkannt (Start)! Warte {self.trigger_duration}s für Trigger...")
                    return False  # Noch nicht lange genug
                
                # Prüfe ob Vogel lange genug erkannt wurde
                detection_duration = current_time - self.first_detection_time
                
                if detection_duration >= self.trigger_duration:
                    # Prüfe Konsistenz: Mindestens 65% der letzten Frames müssen Vogel zeigen
                    # (Reduziert von 70% auf 65% für bessere Performance bei CPU-Limitierung)
                    recent_detections = [d for t, d in self.detection_history]
                    if len(recent_detections) > 0:
                        detection_rate = sum(recent_detections) / len(recent_detections)
                        
                        if detection_rate >= 0.65:  # 65% Konsistenz (optimiert)
                            if self.debug:
                                logger.debug(f"✅ TRIGGER! Vogel konsistent erkannt ({detection_duration:.1f}s, {detection_rate*100:.0f}% Rate)")
                            
                            # Reset für nächsten Trigger
                            self.first_detection_time = None
                            self.detection_history.clear()
                            return True
                    
                    return False
                else:
                    if self.debug and int(detection_duration) != int(detection_duration - 0.2):
                        logger.debug(f"🐦 Vogel erkannt... {detection_duration:.1f}/{self.trigger_duration}s")
                    return False
            
            else:
                # Kein Vogel mehr erkannt - Reset Timer
                if self.first_detection_time is not None:
                    if self.debug:
                        logger.debug(f"❌ Vogel-Erkennung verloren (war {current_time - self.first_detection_time:.1f}s)")
                    self.first_detection_time = None
                
                return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        uptime = time.time() - (self.last_detection_time if self.last_detection_time > 0 else time.time())
        
        return {
            "connected": self.connected,
            "model_loaded": self.model_loaded,
            "frames_processed": self.frames_processed,
            "birds_detected": self.birds_detected,
            "avg_inference_time": self.avg_inference_time,
            "last_detection": self.last_detection_time,
            "uptime": uptime
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Standalone-Test
if __name__ == "__main__":
    import argparse
    import signal
    import sys
    
    # Global flag für sauberes Beenden
    running = True
    
    def signal_handler(sig, frame):
        """Handler für Strg+C"""
        global running
        print("\n\n⛔ Beende durch Benutzer...")
        running = False
    
    # Signal-Handler registrieren
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Stream Processor Test")
    parser.add_argument("--host", default="raspberrypi-5-ai-had", help="Raspberry Pi Host")
    parser.add_argument("--port", type=int, default=8554, help="Stream Port")
    parser.add_argument("--model", default="bird-species", help="AI Model Type")
    parser.add_argument("--threshold", type=float, default=0.45, help="Detection Threshold")
    parser.add_argument("--duration", type=int, default=60, help="Test Duration (seconds)")
    parser.add_argument("--debug", action="store_true", help="Debug Mode")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🐦 Stream Processor Test")
    print("=" * 70)
    print(f"Host: {args.host}:{args.port}")
    print(f"Model: {args.model}")
    print(f"Threshold: {args.threshold}")
    print(f"Duration: {args.duration}s")
    print("=" * 70)
    print()
    
    processor = StreamProcessor(
        host=args.host,
        port=args.port,
        model_type=args.model,
        threshold=args.threshold,
        debug=args.debug
    )
    
    if processor.connect():
        print("✅ Stream verbunden, starte Erkennung...")
        print("   (Strg+C zum Beenden)\n")
        
        start_time = time.time()
        
        try:
            while running and (time.time() - start_time < args.duration):
                bird_detected = processor.process_frame()
                
                if bird_detected:
                    print(f"🐦 Vogel erkannt! (Frame {processor.frames_processed})")
                
                time.sleep(0.1)  # 10 FPS Processing
                
        except KeyboardInterrupt:
            print("\n⛔ Abgebrochen durch Benutzer")
        
        finally:
            processor.disconnect()
            
            print("\n" + "=" * 70)
            print("📊 Statistiken")
            print("=" * 70)
            stats = processor.get_statistics()
            print(f"Frames verarbeitet: {stats['frames_processed']}")
            print(f"Vögel erkannt: {stats['birds_detected']}")
            if stats['avg_inference_time'] > 0:
                print(f"Durchschn. Inferenz-Zeit: {stats['avg_inference_time']*1000:.1f}ms")
            print("=" * 70)
    else:
        print("❌ Konnte nicht mit Stream verbinden")
        print("\n💡 Troubleshooting:")
        print("   1. Läuft der Preview-Stream auf dem Raspberry Pi?")
        print("      ssh {args.host}")
        print("      ./start-preview-stream.sh --status")
        print("\n   2. Ist die Verbindung erreichbar?")
        print(f"      telnet {args.host} {args.port}")
        print("\n   3. Dependencies installiert?")
        print("      pip install opencv-contrib-python ultralytics")
        exit(1)
