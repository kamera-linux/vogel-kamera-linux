#!/bin/bash
# Hailo YOLOv8 Quick Test für Raspberry Pi 5
# Testet rpicam-hello + Hailo Integration (30 Sekunden)

set -e

echo "🚀 ============================================="
echo "   Hailo YOLOv8 Bird Detection Quick Test"
echo "============================================="
echo ""

# Prüfe Hailo Hardware
echo "📋 1️⃣  Hailo Hardware Check:"
if hailortcli fw-control identify &>/dev/null; then
    echo "   ✅ Hailo-8 erkannt!"
    hailortcli fw-control identify 2>/dev/null | grep -E "Board|Firmware|Architecture" || true
else
    echo "   ❌ Hailo nicht gefunden! Prüfe Kernel Driver..."
    sudo dmesg | grep -i hailo | tail -5
    exit 1
fi

echo ""
echo "📋 2️⃣  rpicam-apps & HEF Models Check:"
if rpicam-hello --version &>/dev/null; then
    VERSION=$(rpicam-hello --version 2>&1 | head -1)
    echo "   ✅ rpicam-hello v${VERSION#*build: }"
else
    echo "   ❌ rpicam-hello nicht gefunden"
    exit 1
fi

# Prüfe HEF Modelle
if [ -f "/usr/share/rpi-camera-assets/hailo_yolov8_inference.json" ]; then
    echo "   ✅ YOLOv8 HEF Model gefunden!"
else
    echo "   ❌ YOLOv8 HEF nicht gefunden"
    exit 1
fi

echo ""
echo "📋 3️⃣  Camera Check:"
if libcamera-hello --version &>/dev/null; then
    echo "   ✅ libcamera verfügbar"
    libcamera-hello -t 0.001 --info-text > /dev/null 2>&1 && echo "   ✅ Camera funktioniert!" || echo "   ⚠️  Camera-Test incomplete"
else
    echo "   ⚠️  libcamera nicht gefunden"
fi

echo ""
echo "============================================="
echo "🎬 4️⃣  Starte 30-Sekunden YOLOv8 Test..."
echo "============================================="
echo ""
echo "⚠️  Logs werden angezeigt. Betätigen Sie Ctrl+C zum Stoppen."
echo ""

# Starte rpicam-hello mit YOLOv8 HEF für 30 Sekunden
timeout 30 rpicam-hello -t 0 \
  --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
  --framerate 25 \
  -n -v 2 2>&1 | head -100 || true

echo ""
echo "============================================="
echo "✅ Test abgeschlossen!"
echo "============================================="
echo ""
echo "📊 Ergebnisse:"
echo "   • Die Ausgabe zeigt Frame-Verarbeitung"
echo "   • Diese sollte stabil laufen (keine Fehler)"
echo "   • Bei Detektionen würde 'Detection: ...' angezeigt"
echo ""
echo "🚀 Um wirkliche Vogel-Erkennung zu starten:"
echo ""
echo "   # Option 1: Einfacher Test"
echo "   python3 hailo_rpicam_integration.py --duration 60"
echo ""
echo "   # Option 2: Custom Parameters"
echo "   python3 hailo_rpicam_integration.py \\"
echo "     --model yolov8 --fps 25 --confidence 0.45 --duration 300"
echo ""
echo "   # Option 3: Standlone Bird Detector"
echo "   python3 hailo_bird_detector.py --fps 25 --threshold 0.45"
echo ""
echo "📚 Dokumentation: cat HAILO-README.md"
echo ""
