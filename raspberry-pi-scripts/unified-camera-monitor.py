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
        recording_duration: int = 60,
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
            debug: Debug-Modus aktivieren
        """
        self.camera_num = camera_num
        self.threshold = threshold
        self.cooldown = cooldown
        self.trigger_duration = trigger_duration
        self.recording_duration = recording_duration
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
            
            # Dual-Stream Konfiguration für Preview + Encoding
            # main: Haupt-Stream für Encoding (H264)
            # lores: Low-Res Stream für Preview/AI-Analyse
            config = self.picam2.create_video_configuration(
                main={
                    "size": (self.recording_width, self.recording_height),
                    "format": "YUV420"  # Für H264-Encoding
                },
                lores={
                    "size": (self.preview_width, self.preview_height),
                    "format": "RGB888"  # Für AI-Analyse
                },
                encode="main"  # Aktiviere Encode-Stream für main
            )
            
            self.picam2.configure(config)
            
            # Setze Kamera-Parameter
            self.picam2.set_controls({
                "FrameRate": self.recording_fps,  # Haupt-Stream FPS
                "ExposureTime": 10000,  # Auto
                "AnalogueGain": 1.0
            })
            
            logger.info("✅ Picamera2 konfiguriert (Dual-Stream mit Encoding)")
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
                # Stoppe laufende Aufnahme falls aktiv
                if self.is_recording:
                    try:
                        self.picam2.stop_recording()
                        logger.info("Aufnahme gestoppt")
                    except:
                        pass
                
                # Stoppe Kamera
                if self.picam2.started:
                    self.picam2.stop()
                    logger.info("Kamera gestoppt")
                
                # Schließe Kamera
                self.picam2.close()
                logger.info("✅ Kamera geschlossen")
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
                
                print(f"🎥 Starte Aufnahme: {video_file.name}")
                logger.info(f"🎥 Starte Aufnahme: {video_file}")
                
                # Starte Encoder für Haupt-Stream
                encoder = H264Encoder()
                output = FileOutput(str(video_file))
                
                self.picam2.start_recording(encoder, output)
                
                self.is_recording = True
                self.recordings_triggered += 1
                
                # Aufnahme-Thread mit Statusbalken
                def recording_with_progress():
                    start_time = time.time()
                    duration = self.recording_duration
                    
                    while time.time() - start_time < duration:
                        elapsed = time.time() - start_time
                        percent = int((elapsed / duration) * 100)
                        bar_length = 20
                        filled = int((elapsed / duration) * bar_length)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        print(f"\r🎥 Aufnahme läuft... {bar} {percent}% ({int(elapsed)}/{duration}s)", end='', flush=True)
                        time.sleep(1)
                    
                    print()  # Neue Zeile nach Fortschrittsbalken
                    self._stop_recording()
                
                threading.Thread(target=recording_with_progress, daemon=True).start()
                
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
                print(f"✅ Aufnahme beendet - Cooldown: {self.cooldown}s")
                logger.info("✅ Aufnahme beendet")
                logger.info(f"⏳ Cooldown: {self.cooldown} Sekunden")
                
            except Exception as e:
                logger.error(f"Fehler beim Stoppen der Aufnahme: {e}")
    
    def run(self):
        """Hauptloop für Camera Monitoring."""
        logger.info("🔍 Überwache Vogelhaus... (Strg+C zum Beenden)\n")
        
        frame_count = 0
        last_status_time = time.time()
        last_heartbeat_time = time.time()
        status_interval = 300  # 5 Minuten
        heartbeat_interval = 30  # 30 Sekunden
        
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
                    
                    current_time = time.time()
                    
                    # Herzschlag alle 30 Sekunden
                    if current_time - last_heartbeat_time >= heartbeat_interval:
                        logger.info(f"[✓] Monitor aktiv - {self.frames_processed} Frames verarbeitet, aktuell aufgenommen: {self.is_recording}")
                        last_heartbeat_time = current_time
                    
                    # Status-Report alle 5 Minuten
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
        
        # Load: Grün <1.0, Gelb 1.0-2.0, Rot >2.0
        if load_1min < 1.0:
            load_icon = "🟢"
        elif load_1min < 2.0:
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
        
        # WARNUNG bei hoher Load (>2.0 kritisch für Zeitlupe)
        if load_1min >= 2.0:
            logger.warning(f"⚠️  CPU-Last kritisch: {load_1min:.2f} (Limit: 2.0)")
        
        # WARNUNG bei kritischer Festplatte
        if disk_percent >= 95:
            logger.warning(f"⚠️  Festplatte kritisch: Nur noch {disk_free_gb:.1f} GB frei!")


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
    parser.add_argument('--recording-width', type=int, default=4096, help='Aufnahme-Breite (default: 4096 - Cinema 4K)')
    parser.add_argument('--recording-height', type=int, default=2160, help='Aufnahme-Höhe (default: 2160 - Cinema 4K)')
    parser.add_argument('--recording-fps', type=int, default=30, help='Aufnahme-FPS (default: 30)')
    parser.add_argument('--recording-duration', type=int, default=60, help='Aufnahme-Dauer in Sekunden (default: 60)')
    parser.add_argument('--slowmo', action='store_true', help='Zeitlupen-Modus (1536x864 @ 120fps, überschreibt Auflösung/FPS)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    
    args = parser.parse_args()
    
    # Banner im klassischen Format
    print("\n" + "=" * 70)
    print("🐦 UNIFIED CAMERA MONITOR - Vogel-Kamera-Linux")
    print("=" * 70 + "\n")
    
    # Zeitlupen-Modus: Überschreibe Auflösung und FPS
    if args.slowmo:
        print("=" * 70)
        print("🎬 ZEITLUPEN-MODUS AKTIVIERT")
        print(f"📹 Auflösung: {1536}x{864} @ {120}fps")
        print("=" * 70 + "\n")
        args.recording_width = 1536
        args.recording_height = 864
        args.recording_fps = 120
    
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
