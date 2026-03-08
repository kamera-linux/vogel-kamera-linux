# 📋 CHANGELOG - Vogel-Kamera-Linux

## [2.1.0] - 8. März 2026 🎙️ **Audio/Video-Synchronisation**

### 🎙️ Major Features
- **Thread-basierte Audio/Video-Synchronisation**
  - Video + Audio starten parallel in separaten Threads
  - Beide Streams laufen für exakt gleiche Duration
  - Eliminierung aller Timing-Fehler beim MP4-Merge
  
- **USB-Audio-Stick Integration**
  - Automatische Geräte-Erkennung (hw:0,0, hw:1,0-3,0)
  - arecord: 44.1kHz Mono, S16_LE WAV
  - Fallback-Mechanismus bei nicht gefundenem Gerät
  
- **rpicam-vid Native Integration**
  - Ersetzt libcamera/picamera2 für bessere Codec-Kontrolle
  - Alle Parameter verfügbar: Rotation, Codec, HDR, Autofokus, ROI
  - **4096x2160 Cinema 4K** @ 30fps als Standard
  
- **Manual Recording Mode**
  - Direkte N-Sekunden Aufnahmen ohne AI-Watchdog
  - `--manual-record --recording-duration 60` Syntax
  - Mit oder ohne Audio

### ✨ Improvements
- Rotation 180° als Default (Vogelbild oben, nicht kopfüber)
- ffmpeg Merge mit `-fflags +genpts` für korrekte Timestamps
- Enhanced parameter logging (zeigt alle Einstellungen)
- Slow-Motion Support (60fps statt 30fps)
- Auto-Detection von Audio-Device beim Start

### 🔧 Technical Changes
- Python Threading statt sequenzielle Ausführung
- ffmpeg Parameter: `-fflags +genpts -r {fps}` (KEINE `-shortest` Flag)
- rpicam-vid Command-Building mit vollständigen Parametern
- Dynamic USB Audio Device Search mit mehreren Fallbacks

### 🗑️ Removed
- ❌ `raspberry-pi-scripts/setup-unified-monitor.sh` (veraltet)
- ❌ `raspberry-pi-scripts/start-unified-monitor.sh` (veraltet)
- ❌ picamera2 Abhängigkeit (nicht mehr nötig)

### 📚 Documentation
- ✅ `raspberry-pi-scripts/UNIFIED-MONITOR-README.md` - Komplett neu
- ✅ `releases/v2.1.0/RELEASE_NOTES_v2.1.0.md` - Detaillierte Notes
- ✅ `README.md` - v2.1.0 Highlights
- ✅ Alle Verweise auf gelöschte .sh Dateien entfernt

### ✅ Known Working
- Parallel Video + Audio Aufnahme (5s, 60s+ getestet)
- Perfect MP4 Merge mit durchgehörendem Audio
- Auto-Transfer via rsync zum Client-PC
- AI-Watchdog Modus (mit Einschränkungen)

### ⚠️ Known Limitations
- Watchdog-Modus: Keine Parallelisierung mit Live-Preview möglich
- Multi-Camera: Nur `--camera 0` oder `--camera 1` (noch nicht optimiert)

### 🔗 Related
- Audio-Integration Changelog: [AUDIO-FIX-CHANGELOG.md](AUDIO-FIX-CHANGELOG.md)

---

## [2.0.2] - 2025-11-11 🔧 Maintenance Release

### Features
- YOLO26 Migration (yolo26n.pt statt yolov8n.pt)
- Verbesserte Erkennungsgenauigkeit
- ultralytics>=26.0.0 Support

### Fixes
- CPU/RAM-Anzeige-Fehler (falsche PID, Locale-Komma)
- Kamera-Start-Konflikt durch rpicam-vid-Watchdog
- SSH-Timeout-Verbesserungen

### Documentation
- Trixie (Debian 13) Migration Guide
- Updated Hardware Requirements

---

## [2.0.1] - 2025-09-15 📸 rpicam-vid Integration

### Features
- rpicam-vid statt libcamera direkt
- Improved reliability
- Better codec support

### Fixes
- Stream stability improvements
- Connection handling

---

## [2.0.0] - 2025-08-01 🚀 Major Rewrite

### Breaking Changes
- Unified Camera Monitor System
- New Python architecture
- Debian Trixie requirement

### Major Features
- YOLOv8 Integration
- Real-time bird detection
- Automatic recording trigger

---

## [1.2.5] - 2025-06-15 🎥 Bookworm Legacy Release

### Status
- Last Bookworm (Debian 12) version
- Legacy branch support continues
- See: bookworm-legacy branch

---

## Installation der aktuellen Version

```bash
# Clone repository
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux

# Update to v2.1.0
git checkout main
git pull origin main

# Install dependencies
sudo apt install -y rpicam-apps alsa-utils ffmpeg
pip install ultralytics opencv-python numpy

# Test
cd raspberry-pi-scripts/
python3 unified-camera-monitor.py --manual-record --recording-duration 5
```

---

**Aktuelle Version:** v2.1.0 (Stable) ✅  
**Entwicklungszustand:** Produktionsreif, getestet auf RPi5 + Trixie  
**Nächste Major-Version:** v2.2.0 (Web-Dashboard, WebRTC-Stream)
