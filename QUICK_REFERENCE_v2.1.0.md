# 🎬 Vogel-Kamera v2.1.0 - Quick Reference (ARCHIV)

**Version:** 2.1.0 | **Datum:** 8. März 2026 | **Status:** Veraltet ⚠️  
**→ Nutze stattdessen:** [v2.1.1 Quick Reference](QUICK_REFERENCE_v2.1.1.md)

---

## 🚀 Start (Schnellste Lösung)

```bash
# SSH zum Raspberry Pi
ssh <your-username>@your-raspberry-pi

# Direkt starten: 60s Aufnahme mit Audio
python3 ~/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor.py \
  --manual-record \
  --recording-duration 60 \
  --rotation 180 \
  --enable-audio
```

**Ergebnis:** MP4 im Ordner `/home/<your-username>/Videos/Vogelhaus/`

---

## 🎙️ Audio/Video Sync (Das Kernfeature)

### Warum v2.1.0?
**v2.0.x Problem:** Audio und Video wurden sequenziell → Keine Sync  
**v2.1.0 Lösung:** Parallel Threads → Perfekte Sync

```
v2.1.0 Ablauf:
┌─────────────────────────────────────────┐
│ t=0s: Video-Thread & Audio-Thread START │
├─────────────────────────────────────────┤
│ t=0-60s: PARALLEL (beide gleichzeitig) │
├─────────────────────────────────────────┤
│ t=60s: Video + Audio enden GLEICHZEITIG │
├─────────────────────────────────────────┤
│ ffmpeg Merge → MP4 perfekt sync! ✅   │
└─────────────────────────────────────────┘
```

---

## 🎥 Recording Modi

### 1️⃣ Manual Recording (NEU!)
```bash
# 30 Sekunden
python3 unified-camera-monitor.py --manual-record --recording-duration 30

# Mit allen Parametern
python3 unified-camera-monitor.py \
  --manual-record \
  --recording-duration 60 \
  --rotation 180 \
  --codec h264 \
  --autofocus-mode continuous \
  --hdr off \
  --enable-audio
```

### 2️⃣ AI-Watchdog (Automatische Vogel-Erkennung)
```bash
# Standard
python3 unified-camera-monitor.py --enable-audio

# Mit Zeitlupe (60fps)
python3 unified-camera-monitor.py --slowmo --enable-audio

# Custom Schwelle
python3 unified-camera-monitor.py \
  --threshold 0.3 \
  --cooldown 10 \
  --enable-audio
```

---

## 🎙️ Audio Parameter

| Parameter | Default | Beispiel |
|-----------|---------|----------|
| `--enable-audio` | false | Aktiviert USB-Audio-Aufnahme |
| (Auto-Detect) | hw:0,0 | Sucht hw:0,0 → hw:1,3 sequenziell |
| Sample-Rate | 44.1kHz | 44100 Hz (ALSA standard) |
| Format | S16_LE | 16-bit Signed LE (standard) |
| Channels | Mono | 1 Channel (sparsam) |

### Hardware-Check
```bash
# Audio-Device prüfen
arecord -l

# Lautsprecher testen
aplay /usr/share/sounds/freedesktop/stereo/complete.oga
```

---

## 📷 Kamera Parameter

| Parameter | Default | Options |
|-----------|---------|---------|
| `--rotation` | **180** | 0, 90, 180, 270 |
| `--codec` | h264 | h264, libx264 |
| `--hdr` | off | auto, off |
| `--autofocus-mode` | continuous | continuous, manual, once |
| `--autofocus-range` | macro | normal, macro |
| `--camera` | 0 | 0, 1 (falls 2 Kameras) |
| `--recording-width` | 4096 | 1920, 2560, 4096, ... |
| `--recording-height` | 2160 | 1080, 1440, 2160, ... |
| `--recording-fps` | 30 | 15, 24, 30, 60 (mit --slowmo) |

### Beispiele
```bash
# Full HD 60fps (Zeitlupe)
python3 unified-camera-monitor.py --manual-record --recording-duration 30 --slowmo

# 4K 30fps (Standard)
python3 unified-camera-monitor.py --manual-record --recording-duration 60

# 1080p für Tests (schneller)
python3 unified-camera-monitor.py --manual-record --recording-duration 5 \
  --recording-width 1920 --recording-height 1080
```

---

## ✅ Verifizierung

### Nach Aufnahme
```bash
# Überprüfe Dateien
ls -lh ~/Videos/Vogelhaus/*/vogel_*.mp4 | tail -1

# Prüfe Video+Audio Streams
ffprobe ~/Videos/Vogelhaus/[DATUM]/vogel_*.mp4

# Erwartet:
# Stream #0:0: Video: h264 (High) 4096x2160, 29.94 fps
# Stream #0:1: Audio: aac (LC) 44100 Hz, mono
# Duration: 00:01:00.00
```

### Audio-Device Erkannt?
```
✅ USB-Audio-Gerät gefunden (arecord): hw:0,0
```

### Logs
```bash
# Bei Parameter-Parsing
2026-03-08 20:15:30 - INFO - Rotation: 180°
2026-03-08 20:15:30 - INFO - Autofokus: continuous (macro)
2026-03-08 20:15:30 - INFO - HDR: off

# Bei Recording
2026-03-08 20:15:31 - INFO - 🎬 Video-Thread startet
2026-03-08 20:15:31 - INFO - 🎤 Audio-Thread startet
2026-03-08 20:16:31 - INFO - ✅ Audio-Thread erfolgreich
2026-03-08 20:16:32 - INFO - ✅ Video-Thread erfolgreich
```

---

## 🐛 Troubleshooting

### Problem: Kamera nicht erkannt
```bash
rpicam-hello --list-cameras
rpicam-hello -t 2000
```

### Problem: Audio-Device nicht gefunden
```bash
arecord -l
lsusb | grep -i audio
```

### Problem: MP4 hat kein Audio
```bash
# Überprüfe ob beide Dateien erstellt wurden
ls /tmp/vogel_*.h264 /tmp/vogel_*.wav

# Überprüfe Duration
ffprobe -v error -show_entries format=duration <video.h264>
ffprobe -v error -show_entries format=duration <audio.wav>
# Sollten identisch sein!
```

### Problem: Video steht auf dem Kopf
```bash
# Überprüfe Rotation-Parameter wurde übergeben
python3 unified-camera-monitor.py --manual-record --rotation 180 --debug
```

---

## 📦 Dependencies

```bash
# System
sudo apt install -y rpicam-apps alsa-utils ffmpeg

# Python
pip install ultralytics opencv-python numpy
```

---

## 🔄 Client-PC (Download)

### Auto-Transfer Setup (optional)
Videos werden automatisch via rsync übertragen zum lokalen PC:
```bash
# Im unified-monitor-client konfigurieren
python3 unified-monitor-client/setup_environment.py
```

### Manueller Download
```bash
# Einzelnes Video
scp <your-username>@your-raspberry-pi:~/Videos/Vogelhaus/*/vogel_*.mp4 ~/Videos/

# Alle Videos
rsync -avz <your-username>@your-raspberry-pi:~/Videos/Vogelhaus/ ~/Videos/Vogelhaus/
```

---

## 📊 Performance

| Metrik | Wert |
|--------|------|
| **CPU (4K@30fps)** | 30-40% |
| **RAM (4K@30fps)** | ~25% |
| **Disk (4K@30fps)** | ~50MB/s (write) |
| **File Size (1min 4K)** | ~300MB |
| **Thread Overhead** | <1% |

---

## 🎯 Häufige Befehle

```bash
# Test: 5 Sekunden
python3 unified-camera-monitor.py --manual-record --recording-duration 5

# Produktion: 60 Sekunden mit Audio
python3 unified-camera-monitor.py --manual-record --recording-duration 60 --enable-audio

# AI-Mode: Automatische Erkennung
python3 unified-camera-monitor.py --threshold 0.4 --enable-audio

# Zeitlupe: 60fps
python3 unified-camera-monitor.py --slowmo --recording-duration 30

# FullHD Test: Schneller (1080p)
python3 unified-camera-monitor.py --manual-record --recording-width 1920 --recording-height 1080
```

---

## 📖 Weitere Infos

- 📘 **Full Docs:** [UNIFIED-MONITOR-README.md](raspberry-pi-scripts/UNIFIED-MONITOR-README.md)
- 📘 **Release Notes:** [releases/v2.1.0/RELEASE_NOTES_v2.1.0.md](releases/v2.1.0/RELEASE_NOTES_v2.1.0.md)
- 📘 **Audio Changelog:** [AUDIO-FIX-CHANGELOG.md](AUDIO-FIX-CHANGELOG.md)
- 📘 **Hauptprojekt:** [README.md](README.md)

---

**Version:** 2.1.0 | **Status:** Production Ready ✅ | **Getestet:** RPi5 + Debian Trixie
