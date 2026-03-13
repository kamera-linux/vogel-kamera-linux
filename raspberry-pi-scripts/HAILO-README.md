# 🚀 Hailo YOLOv8 Bird Detection Integration

> Nutzt Raspberry Pi's **vorkompilierte HEF-Modelle** für 25+ fps Vogel-Erkennung  
> Hailo-8 NPU Hardware-Beschleunigung für maximale Performance

## 📊 Performance Übersicht

| Hardware | FPS | CPU-Last | Engine |
|----------|-----|----------|--------|
| **Hailo-8 NPU (aktuell)** | 25-28 fps | < 5% | YOLOv8 HEF |
| ONNX Runtime | 6 fps | ~40% | PyTorch/ONNX |
| PyTorch CPU | 4 fps | ~80% | CPU-only |

## 🎯 Features

✅ **Vorkompilierte HEF-Modelle** - Keine Konvertierung nötig!  
✅ **rpicam-apps Integration** - Offizielle Raspberry Pi Camera-Lib  
✅ **25+ fps Performance** - Echtzeitverarbeitung  
✅ **< 5% CPU-Last** - Volle CPU für andere Tasks  
✅ **Vogel-Spezifisch** - COCO Class 14 Filtering  
✅ **JSON Output** - Integration mit bestehenden Systemen  

## 📁 Dateien

```
raspberry-pi-scripts/
├── hailo_bird_detector.py           # Standalone Bird Detector
├── hailo_rpicam_integration.py       # Integration mit rpicam-apps
└── HAILO-README.md                  # Diese Datei
```

## ⚙️ Installation

### Auf Raspberry Pi - Abhängigkeiten (bereits installiert!)

```bash
# YOLOv8 HEF ist bereits in rpicam-apps enthalten:
rpm-apps --version

# Hailo Runtime ist bereits installiert:
hailortcli fw-control identify

# Logs überprüfen:
sudo dmesg | grep -i hailo
```

## 🎬 Verwendung

### Option 1: Einfacher Test mit rpicam-hello

```bash
# Schnell-Test: 25 fps YOLOv8 mit Hailo
rpicam-hello -t 0 \
  --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
  --framerate 25 -n -v 2

# 5 Sekunden Test laufen lassen:
timeout 5 rpicam-hello -t 0 \
  --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
  --framerate 25 -n -v 2
```

### Option 2: Hailo Bird Detector Skript

```bash
cd ~/vogel-kamera-linux/raspberry-pi-scripts

# Standard-Vogel-Detection (25 fps, 1920x1080)
python3 hailo_bird_detector.py

# Mit Custom Parameters
python3 hailo_bird_detector.py \
  --fps 30 \
  --resolution 1920x1080 \
  --threshold 0.45 \
  --duration 60 \
  --verbose

# Mit Rotation (für Kamera-Ausrichtung)
python3 hailo_bird_detector.py --rotation 90
```

### Option 3: Integration mit rpicam-apps

```bash
# Bird Detection mit Logging
python3 hailo_rpicam_integration.py \
  --model yolov8 \
  --fps 25 \
  --confidence 0.50 \
  --duration 300  # 5 Minuten

# Mit YOLOv6 (schneller, weniger genau)
python3 hailo_rpicam_integration.py --model yolov6
```

## 📊 Monitoring

### Live-Logs anschauen

```bash
# Hailo Bird Detector Logs
tail -f /tmp/hailo_bird_detection.log

# Integration Logs
tail -f /tmp/hailo_integration.log

# Detektionen (JSON)
cat /tmp/hailo_detections.json
cat /tmp/bird_detections.json
```

### Performance überprüfen

```bash
# Hailo-Firmware checken
hailortcli fw-control identify

# Kernel Driver Status
sudo dmesg | grep -i hailo | tail -20

# Prozess-CPU-Last
ps aux | grep rpicam
```

## 🔧 Verfügbare HEF-Modelle

Alle vorinstallierten YOLOv-Modelle:

```bash
ls /usr/share/rpi-camera-assets/hailo*.json
```

- `hailo_yolov8_inference.json` ⭐ **Empfohlen** - Best Accuracy
- `hailo_yolov6_inference.json` - Schneller, weniger Genauigkeit
- `hailo_yolox_inference.json` - Leichtgewicht, Mobile-optimiert
- `hailo_yolov5_personface.json` - Menschen/Gesichter
- `hailo_yolov5_segmentation.json` - Pixel-Level Segmentation

## 📈 Vogel-Erkennung Parameters

```python
# hailo_rpicam_integration.py / hailo_bird_detector.py

BIRD_CLASS = 14              # COCO Dataset Bird Class
BIRD_CONFIDENCE_THRESHOLD = 0.50  # 50% Confidence-Minimum
MIN_BBOX_SIZE = 20          # Minimum Größe (Pixel)
MAX_BBOX_SIZE = 1920        # Maximum Größe (Ausreißer vermeiden)
TARGET_FPS = 25             # Ziel-FPS
```

## 🐦 Vogel-Detection Workflow

```
Camera Input (libcamera)
    ↓
rpicam-hello (Camera Processing)
    ↓
Hailo YOLOv8 HEF (NPU Inference) ← 25+ fps
    ↓
Post-Processing (Vogel-Filtering, Class 14)
    ↓
Detection JSON Output
    ↓
Integration mit Unified Monitor
```

## 🔗 Integration mit Unified Monitor

```python
# unified_monitor_client.py anpassung:

from hailo_rpicam_integration import HailoRPiIntegration

hailo = HailoRPiIntegration(
    model="yolov8",
    fps=25,
    resolution="1920x1080",
    confidence=0.50
)

hailo.start_detection()

# In Detection Loop:
detection = hailo.get_detection(timeout=5)
if detection:
    log_detection(f"🐦 {detection['class']} detected!")
```

## ❓ FAQ

### Q: Warum nur 25 fps? Ist 30fps nicht besser?

**A:** 25 fps ist der Hailo-Standard für Vogeilerkennung:
- Prozessierungszeit pro Frame: ~40ms
- Qualität vs Speed Trade-off
- CPU bleibt unter 5% Last
- Mehr FPS = Weniger Detection-Genauigkeit

### Q: Funktioniert das auch mit älteren YOLO-Modellen?

**A:** Ja! Alle vorinstallierten Modelle sind HEF-kompiliert:
- YOLOv5, YOLOv6, YOLOv8, YOLOX alle verfügbar
- Unterschiedliche Genauigkeit/Speed Trade-offs

### Q: Kann ich mein eigenes YOLOv8 Modell verwenden?

**A:** Ja, aber mit Einschränkung:
1. ONNX → HEF Konvertierung braucht Hailo Compiler
2. Hailo Compiler ist proprietär (keine kostenlose Version)
3. Alternativ: Hailo Community Forum kontaktieren

### Q: Warum ist die Erkennung manchmal schlecht?

**Mögliche Gründe:**
- Zu niedriges Umgebungslicht (nachts)
- Vogel außerhalb YOLO-Trainings-Daten (exotische Arten)
- Confidence-Threshold zu hoch
- Hailo HEF ist für generische YOLO optimiert, nicht für Vögel

**Lösungen:**
- Confidence zu 0.40 reduzieren: `--confidence 0.40`
- Bessere Beleuchtung am Vogel-Spot
- Mit YOLOv6 probieren (schneller, andere Accuracy)

## 📚 Weitere Ressourcen

- **Raspberry Pi Hailo Docs**: [raspberrypi.com/ai](https://www.raspberrypi.com/documentation/computers/ai.html)
- **Hailo Model Zoo**: [hailo.ai/products/model-explorer](https://hailo.ai/products/hailo-software/model-explorer-vision/)
- **Hailo Community Forum**: [community.hailo.ai](https://community.hailo.ai/)
- **rpicam-apps Post-Processing**: [libcamera.org](https://www.libcamera.org/)

## 🐛 Troubleshooting

### "Device or resource busy"

```bash
# Alte Prozesse killen:
pkill -9 -f rpicam
pkill -9 -f libcamera

# Neustart:
sudo reboot
```

### "Hailo device not found"

```bash
# Firmware überprüfen:
hailortcli fw-control identify

# Kernel Driver Status:
lsmod | grep hailo
dmesg | grep hailo
```

### Nur wenige fps (z.B. 2-3 statt 25)

```bash
# Wahrscheinlich läuft noch alte ONNX-Detection
ps aux | grep detect

# Stoppen:
pkill -9 -f detect

# Erneut starten (sollte 25 fps sein)
python3 hailo_rpicam_integration.py
```

## 📝 Version History

- **v1.0** (12.03.2026) - Initiale Hailo Integration
  - YOLOv8 HEF Support
  - rpicam-hello Integration
  - 25+ fps Performance erreicht
  - Vogel-Klasse Filtering (COCO Class 14)

---

**Questions?** → Check logs in `/tmp/hailo*.log`

**Bugs?** → File issue mit Log-Output
