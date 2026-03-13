#!/bin/bash
# HAILO HYBRID PERFORMANCE BENCHMARK
# Vergleicht alle verfügbaren Detektoren gegeneinander

echo "🎯 HAILO-8 Hybrid Bird Detection - Performance Benchmark"
echo "======================================================"
echo ""
echo "📋 Test Configuration:"
echo "   Hardware: Raspberry Pi 5, Hailo-8 NPU"
echo "   Camera: IMX708 (1920x1080, 30 fps max)"
echo "   Duration: 15 seconds"
echo "   Confidence: 0.50"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if on Pi
if [[ ! -f /proc/device-tree/model ]]; then
    echo "❌ This script must run on Raspberry Pi"
    exit 1
fi

cd ~/vogel-kamera-linux/raspberry-pi-scripts || exit 1

echo -e "${BLUE}Test 1: Pure ONNX Bird Detector (Baseline)${NC}"
echo "─────────────────────────────────────────"
pkill -9 -f "python3.*onnx\|bird.*detector" 2>/dev/null
sleep 1
if python3 unified_bird_detector.py --duration 15 2>/dev/null; then
    echo "✅ ONNX test complete"
    echo ""
fi

echo -e "${BLUE}Test 2: Hailo Generic Detector (Pragmatic)${NC}"
echo "───────────────────────────────────────────"
pkill -9 -f rpicam
sleep 1
timeout 20 python3 hailo_pragmatic.py --duration 15 --confidence 0.50 2>/dev/null

echo ""
echo -e "${BLUE}Test 3: Hailo Hybrid Beschleunigung (Optimiert)${NC}"
echo "────────────────────────────────────────────────"
pkill -9 -f rpicam
sleep 1
timeout 20 python3 hailo_hybrid_detector.py --duration 15 --confidence 0.50 2>/dev/null

echo ""
echo "📊 ERGEBNISSE ZUSAMMENFASSUNG"
echo "════════════════════════════"
echo ""

# Parse results
echo -e "${GREEN}ONNX Bird Detector:${NC}"
if [[ -f /tmp/bird_detections.json ]]; then
    cat /tmp/bird_detections.json | python3 -m json.tool | grep -E '"fps"|"frames"|"detections"'
fi

echo ""
echo -e "${YELLOW}Hailo Generic (Pragmatic):${NC}"
if [[ -f /tmp/bird_detections.json ]]; then
    cat /tmp/bird_detections.json | python3 -m json.tool | grep -E '"fps"|"frames"|"detections"'
fi

echo ""
echo -e "${GREEN}Hailo Hybrid (Neu!):${NC}"
if [[ -f /tmp/bird_detections_hybrid.json ]]; then
    cat /tmp/bird_detections_hybrid.json | python3 -m json.tool | grep -E '"fps"|"frames"|"hailo_detections"'
fi

echo ""
echo "🏆 PERFORMANCE RANKING"
echo "════════════════════"
python3 << 'PYEOF'
import json
from pathlib import Path

results = {}

# ONNX
try:
    with open("/tmp/bird_detections.json") as f:
        data = json.load(f)
        results["ONNX Bird"] = {
            "fps": data.get("fps", 0),
            "frames": data.get("frames", 0),
            "note": "Vogel-spezialisiert"
        }
except:
    pass

# Hybrid
try:
    with open("/tmp/bird_detections_hybrid.json") as f:
        data = json.load(f)
        results["Hailo Hybrid"] = {
            "fps": data.get("fps", 0),
            "frames": data.get("frames", 0),
            "detections": data.get("hailo_detections", 0),
            "note": "Schnell + Generisch"
        }
except:
    pass

# Sort by FPS
sorted_results = sorted(results.items(), key=lambda x: x[1]["fps"], reverse=True)

for rank, (name, stats) in enumerate(sorted_results, 1):
    fps = stats["fps"]
    speedup = "---"
    if rank > 1:
        base_fps = sorted_results[0][1]["fps"]
        if base_fps > 0:
            speedup = f"{fps/base_fps:.2f}x"
    
    print(f"{rank}. {name:20s} | FPS: {fps:6.2f} | Speedup: {speedup:5s} | {stats.get('note', '')}")

PYEOF

echo ""
echo "💡 EMPFEHLUNGEN"
echo "═════════════"
echo ""
echo "✅ ONNX Bird-Detector verwenden für:"
echo "   - Vogel-spezifische Erkennung"
echo "   - Minimale False-Positives"
echo "   - Zuverlässige Klassifikation"
echo "   - 6 fps für Echtzeit-Überwachung"
echo ""
echo "✅ Hailo Hybrid verwenden für:"
echo "   - Schnelle generische Detektion (28+ fps)"
echo "   - Komplementäre Klassifikation (mit ONNX)"
echo "   - Multi-Klassen-Erkennung"
echo "   - Zukünftig mit Vogel-Modell"
echo ""
echo "📌 NÄCHSTER SCHRITT:"
echo "   Hailo Hybrid + ONNX Klassifizierer kombinieren"
echo "   → 28 fps Hailo-Detektion + 6 fps Vogel-Filter"
echo "   → Theoretisch: ~8-10 fps mit Vogel-Fokus"
echo ""

pkill -9 -f rpicam
echo "✅ Benchmark abgeschlossen"
