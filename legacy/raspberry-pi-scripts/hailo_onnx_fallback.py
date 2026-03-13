#!/usr/bin/env python3
"""
Intelligenter Hybrid-Fallback Detector
======================================

Startet mit Hailo, wechselt automatisch zu pure ONNX wenn:
- Nach 5 Sekunden: 0 Hailo-Detektionen
- Keine Performance = Hailo wahrscheinlich offline

Hybrid-Modus:
  1. Versuche Hailo + ONNX (25+ fps wenn funktioniert)
  2. Nach 5s: Checke ob Hailo liefert
  3. Wenn 0: Wechsel automatisch zu pure ONNX (12.4 fps garantiert)
  4. Weiterhin Vo gelklassifizierung mit ONNX!
"""

import subprocess
import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("IntelligentFallback")


def run_hailo_detector(duration: int, hailo_threshold: float = 0.5, 
                       onnx_threshold: float = 0.3, frame_skip: int = 1) -> bool:
    """Versucht Hailo + ONNX Hybrid"""
    logger.info("🚀 START: Hailo + ONNX Hybrid (25+ fps target)")
    logger.info(f"   thresholds: hailo={hailo_threshold}, onnx={onnx_threshold}, skip={frame_skip}")
    
    # Nutze vollständigen Pfad
    script_dir = Path(__file__).parent
    script_path = script_dir / "hailo_onnx_perf.py"
    
    # Starte Hailo Detector
    cmd = [
        "python3", str(script_path),
        "--hailo-threshold", str(hailo_threshold),
        "--onnx-threshold", str(onnx_threshold),
        "--frame-skip", str(frame_skip),
        "--duration", str(duration)
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Warte 5 Sekunden
    time.sleep(5)
    
    # Prüfe aktuelle Stats
    try:
        stats_file = Path("/tmp/bird_detections_perf.json")
        if stats_file.exists():
            with open(stats_file) as f:
                stats = json.load(f)
                hailo_dets = stats.get("hailo_detections", 0)
                
                if hailo_dets > 0:
                    logger.info(f"✅ Hailo funktioniert: {hailo_dets} detections")
                    # Lasse Hailo weiterlaufen
                    proc.wait()
                    return True
                else:
                    logger.warning("⚠️  Hailo antwortet nicht (0 detections nach 5s)")
                    # Stoppe Hailo und fallback zu ONNX
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except:
                        proc.kill()
                    return False
    except Exception as e:
        logger.warning(f"⚠️  Fehler beim Prüfen: {e}")
        
    # Fallback auf Fehler
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
    return False


def run_onnx_detector(duration: int) -> bool:
    """Fallback: Pure ONNX (guaranteed 12.4 fps)"""
    logger.info("⚡ FALLBACK: Pure ONNX Bird Detector (12.4 fps guaranteed)")
    
    # Nutze vollständigen Pfad
    script_dir = Path(__file__).parent
    script_path = script_dir / "yolo_bird_detector.py"
    
    cmd = [
        "python3", str(script_path),
        "--duration", str(duration)
    ]
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligenter Hybrid Fallback Detector")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--hailo-threshold", type=float, default=0.5)
    parser.add_argument("--onnx-threshold", type=float, default=0.3)
    parser.add_argument("--frame-skip", type=int, default=1)
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🐦 INTELLIGENTER HYBRID-FALLBACK DETECTOR")
    logger.info("=" * 70)
    logger.info("")
    
    # Versuche Hailo
    success = run_hailo_detector(
        args.duration,
        args.hailo_threshold,
        args.onnx_threshold,
        args.frame_skip
    )
    
    # Fallback wenn Hailo nicht funktioniert
    if not success:
        logger.info("")
        logger.info("🔄 Wechsel zu garantiertem Fallback...")
        logger.info("")
        run_onnx_detector(args.duration)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ DETEKTOR BEENDET")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
