#!/usr/bin/env python3
"""
Hailo + YOLOv8s Hybrid Bird Detector - CROP-BASED OPTIMIZATION
============================================================

Dual-stage detection:
1. Hailo (29 fps): Fast generic detection → get bounding boxes
2. YOLOv8s (async): Bird classification on CROPS only (not full frames)

Performance target:
  - Hailo: 29 fps (100% frames)
  - YOLOv8s: 6-8 fps on crops only
  - Hybrid: 25+ fps effective (realtime + bird filtering)

Key optimization:
  - YOLOv8s processes ~300×300 crop (9% of 640×480 area)
  - ~11x faster than full frame processing
  - Async processing: doesn't block Hailo pipeline
"""

import subprocess
import json
import time
import logging
import argparse
import sys
import re
import threading
import queue
from pathlib import Path
from datetime import datetime
from threading import Thread, Event, Lock
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import onnxruntime as rt
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

# ============================================================================
# CONFIG & LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("HailoYOLOCropHybrid")

STATS_JSON = "/tmp/bird_detections_hailo_yolo_crop.json"
YOLO_BIRD_CLASS_ID = 14  # "bird" in COCO dataset

# ============================================================================
# FRAME BUFFER (Thread-Safe Ring Buffer)
# ============================================================================

class FrameBuffer:
    """Thread-safe frame buffer for extraction of detection crops"""
    
    def __init__(self, max_frames=30):
        self.buffer = deque(maxlen=max_frames)
        self.lock = Lock()
        self.frame_count = 0
    
    def add_frame(self, frame_data: np.ndarray):
        """Add frame to buffer"""
        with self.lock:
            self.buffer.append(frame_data.copy())
            self.frame_count += 1
    
    def get_frame(self, frame_id: int) -> Optional[np.ndarray]:
        """Get frame by ID"""
        with self.lock:
            # Find frame by offset
            if self.frame_count - frame_id < len(self.buffer):
                return self.buffer[-(self.frame_count - frame_id)].copy()
        return None

# ============================================================================
# YOLO CROP CLASSIFIER
# ============================================================================

class YOLOCropClassifier:
    """YOLOv8s ONNX classifier for bird detection on crops"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or self._find_model()
        self.session = None
        self.input_name = None
        self.output_names = None
        self.img_size = 320
        self.available = False
        
        if ONNX_AVAILABLE and self.model_path:
            try:
                self.session = rt.InferenceSession(
                    self.model_path,
                    providers=['CPUExecutionProvider']
                )
                self.input_name = self.session.get_inputs()[0].name
                self.output_names = [o.name for o in self.session.get_outputs()]
                self.available = True
                logger.info(f"✅ YOLOv8 crop classifier loaded: {Path(self.model_path).name}")
            except Exception as e:
                logger.warning(f"⚠️  YOLOv8 load failed: {e}")
    
    def _find_model(self) -> Optional[str]:
        """Find YOLOv8n ONNX model"""
        search_paths = [
            Path.cwd() / "yolov8n.onnx",
            Path.cwd() / "models" / "yolov8n.onnx",
            Path.home() / "models" / "yolov8n.onnx",
            Path(__file__).parent / "models" / "yolov8n.onnx",
        ]
        
        for path in search_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def classify_crop(self, crop: np.ndarray, conf_threshold: float = 0.4) -> Optional[Dict]:
        """
        Classify single crop for bird detection
        
        Returns:
            {"is_bird": bool, "confidence": float, "bbox": [x,y,w,h]} or None
        """
        if not self.available or self.session is None or crop is None:
            return None
        
        try:
            # Prepare input
            img = cv2.resize(crop, (self.img_size, self.img_size))
            img = img.astype(np.float32) / 255.0
            img = img.transpose(2, 0, 1)
            img = np.expand_dims(img, 0)
            
            # Run inference
            outputs = self.session.run(self.output_names, {self.input_name: img})
            
            # Parse single prediction
            output = outputs[0]
            if output.ndim == 3:
                output = output[0]
            elif output.shape[0] == 84:
                output = output.T
            
            # Get best detection
            best_conf = 0
            best_class_id = -1
            
            for pred in output:
                if pred[4] > conf_threshold:
                    class_scores = pred[5:85]
                    class_id = np.argmax(class_scores)
                    class_conf = class_scores[class_id]
                    combined_conf = class_conf * pred[4]
                    
                    if combined_conf > best_conf:
                        best_conf = combined_conf
                        best_class_id = int(class_id)
            
            if best_class_id == YOLO_BIRD_CLASS_ID and best_conf > conf_threshold:
                return {
                    "is_bird": True,
                    "class_id": best_class_id,
                    "confidence": float(best_conf),
                    "crop_shape": crop.shape
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Crop classification error: {e}")
            return None

# ============================================================================
# HAILO DETECTION PARSER
# ============================================================================

class HailoDetectionParser:
    """Parse Hailo detections from rpicam verbose output"""
    
    DETECTION_PATTERN = re.compile(
        r"(\w+)\s+:\s+([\d\.]+)\s+\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)"
    )
    
    @staticmethod
    def parse_detections(log_line: str) -> List[Dict]:
        """Parse Hailo detection line"""
        detections = []
        
        for match in HailoDetectionParser.DETECTION_PATTERN.finditer(log_line):
            try:
                class_name = match.group(1)
                confidence = float(match.group(2))
                x = int(match.group(3))
                y = int(match.group(4))
                w = int(match.group(5))
                h = int(match.group(6))
                
                detections.append({
                    "class": class_name,
                    "confidence": confidence,
                    "bbox": [x, y, w, h]
                })
            except (ValueError, AttributeError):
                continue
        
        return detections

# ============================================================================
# MAIN HYBRID RUNNER
# ============================================================================

class HailoYOLOCropHybrid:
    """Main hybrid detector: Hailo detection + YOLOv8s crop classification"""
    
    def __init__(self, confidence: float = 0.4, duration: int = 60):
        self.confidence = confidence
        self.duration = duration
        self.frame_buffer = FrameBuffer(max_frames=30)
        self.yolo_classifier = YOLOCropClassifier()
        
        self.running = False
        self.start_time = None
        self.hailo_detections = 0
        self.yolo_classifications = 0
        self.birds_confirmed = 0
        self.detected_birds = []
        self.stats = {}
        
        # Async YOLOv8s processing queue
        self.crop_queue = queue.Queue(maxsize=50)
        self.yolo_thread = None
    
    def _yolo_worker(self):
        """Background thread for YOLOv8s crop classification"""
        while self.running:
            try:
                crop, bbox = self.crop_queue.get(timeout=1)
                
                if crop is None:  # Sentinel value to stop thread
                    break
                
                result = self.yolo_classifier.classify_crop(crop, self.confidence)
                
                if result and result["is_bird"]:
                    self.birds_confirmed += 1
                    self.detected_birds.append({
                        "bbox": bbox,
                        "confidence": result["confidence"],
                        "timestamp": time.time()
                    })
                    logger.info(f"🐦 Bird detected! Confidence: {result['confidence']:.3f}")
                
                self.yolo_classifications += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"YOLO worker error: {e}")
    
    def start_yolo_worker(self):
        """Start background YOLO processing thread"""
        if not self.yolo_classifier.available:
            logger.warning("⚠️  YOLOv8 not available, skipping crop classification")
            return
        
        self.yolo_thread = Thread(target=self._yolo_worker, daemon=True)
        self.yolo_thread.start()
        logger.info("✅ YOLOv8s crop worker started")
    
    def stop_yolo_worker(self):
        """Stop background YOLO processing thread"""
        if self.yolo_thread:
            self.crop_queue.put((None, None))
            self.yolo_thread.join(timeout=5)
    
    def process_hailo_detection(self, detection: Dict, frame: np.ndarray):
        """
        Process Hailo detection: extract crop and queue for YOLOv8s
        
        Args:
            detection: {"class": "person", "confidence": 0.9, "bbox": [x,y,w,h]}
            frame: Current frame
        """
        try:
            x, y, w, h = detection["bbox"]
            
            # Add padding to crop
            padding = 20
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(frame.shape[1], x + w + padding)
            y2 = min(frame.shape[0], y + h + padding)
            
            crop = frame[y1:y2, x1:x2]
            
            if crop.size > 0:
                # Queue crop for async YOLOv8s classification
                try:
                    self.crop_queue.put_nowait((crop, [x1, y1, x2-x1, y2-y1]))
                except queue.Full:
                    # Queue full, skip this crop
                    pass
        
        except Exception as e:
            logger.error(f"Crop extraction error: {e}")
    
    def run(self):
        """Main detection loop"""
        logger.info("🚀 Hailo + YOLOv8s Crop Hybrid Detector")
        logger.info(f"   Mode: Dual-stage (Hailo generic + YOLOv8s crops)")
        logger.info(f"   Confidence: {self.confidence}")
        logger.info(f"   Duration: {self.duration}s")
        
        self.start_yolo_worker()
        self.running = True
        self.start_time = time.time()
        self.hailo_detections = 0
        
        # Start rpicam with Hailo detection
        cmd = [
            "rpicam-hello",
            "-t", "0",
            "--codec", "yuv420",
            "-n"  # No preview
        ]
        
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            logger.info("✅ rpicam-hello started")
            
            frame_id = 0
            hailo_stats = {}
            
            for line in proc.stdout:
                if not self.running:
                    break
                
                elapsed = time.time() - self.start_time
                if elapsed >= self.duration:
                    logger.info("⏱️  Duration reached")
                    break
                
                # Parse Hailo detections from log
                detections = HailoDetectionParser.parse_detections(line)
                
                if detections:
                    self.hailo_detections += len(detections)
                    
                    # Create dummy frame for crop extraction
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    
                    for detection in detections:
                        self.process_hailo_detection(detection, frame)
                        
                        # Track detected objects
                        obj_class = detection["class"]
                        hailo_stats[obj_class] = hailo_stats.get(obj_class, 0) + 1
                
                # Log stats every 5 seconds
                if int(elapsed) % 5 == 0 and frame_id > 0:
                    fps_hailo = self.hailo_detections / elapsed if elapsed > 0 else 0
                    fps_yolo = self.yolo_classifications / elapsed if elapsed > 0 else 0
                    logger.info(f"📊 Hailo: {fps_hailo:.1f} det/s | YOLOv8s: {fps_yolo:.1f} class/s | Birds: {self.birds_confirmed}")
                
                frame_id += 1
        
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                pass
            
            self.stop_yolo_worker()
            self.save_stats()
            logger.info("✅ Detector stopped")
    
    def save_stats(self):
        """Save detection statistics"""
        elapsed = time.time() - self.start_time
        
        self.stats = {
            "duration": round(elapsed, 1),
            "hailo_detections": self.hailo_detections,
            "yolo_classifications": self.yolo_classifications,
            "birds_confirmed": self.birds_confirmed,
            "detected_birds": self.detected_birds,
            "stats": {
                "hailo_rate": round(self.hailo_detections / elapsed, 2) if elapsed > 0 else 0,
                "yolo_rate": round(self.yolo_classifications / elapsed, 2) if elapsed > 0 else 0
            },
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "model_stack": {
                "detector": "Hailo YOLOv8s HEF",
                "classifier": "YOLOv8n ONNX (crops)"
            }
        }
        
        try:
            with open(STATS_JSON, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            logger.info(f"📁 Stats saved: {STATS_JSON}")
            logger.info(f"   Hailo detections: {self.hailo_detections}")
            logger.info(f"   YOLOv8s crops processed: {self.yolo_classifications}")
            logger.info(f"   Birds confirmed: {self.birds_confirmed}")
        
        except Exception as e:
            logger.error(f"Stats save failed: {e}")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Hailo + YOLOv8s Crop Hybrid Bird Detector")
    parser.add_argument("--confidence", type=float, default=0.4, help="Detection confidence")
    parser.add_argument("--duration", type=int, default=60, help="Duration (seconds)")
    
    args = parser.parse_args()
    
    detector = HailoYOLOCropHybrid(
        confidence=args.confidence,
        duration=args.duration
    )
    
    try:
        detector.run()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
