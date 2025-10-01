# 🎬 Preview-Stream Setup für Auto-Trigger

Vollständige Anleitung zur Einrichtung des Preview-Streams für automatische Vogel-Erkennung.

## Übersicht

Das Auto-Trigger-System verwendet einen Low-Latency Preview-Stream vom Raspberry Pi, um kontinuierlich nach Vögeln zu suchen. Bei einer Erkennung wird automatisch eine HD-Aufnahme gestartet.

```
┌─────────────────┐     TCP/H.264      ┌──────────────────┐
│  Raspberry Pi 5 │ ══════════════════> │   Client-PC      │
│                 │   Preview-Stream    │                  │
│  rpicam-vid     │      640x480        │  AI-Erkennung    │
│  TCP-Server     │      @ 5fps         │  YOLOv8          │
│  Port 8554      │                     │  Auto-Trigger    │
└─────────────────┘                     └──────────────────┘
        │                                       │
        │                                       │
        └───────────── HD-Aufnahme ────────────┘
                    (bei Vogel-Erkennung)
```

## 📋 Voraussetzungen

### Raspberry Pi 5

- **Betriebssystem:** Raspberry Pi OS (Bookworm oder neuer)
- **libcamera:** Muss installiert sein (normalerweise vorinstalliert)
- **Netzwerk:** Stabile Verbindung zum Client-PC
- **Kamera:** Raspberry Pi Camera Module 3

Prüfen:
```bash
rpicam-hello --version
```

### Client-PC (Linux)

- **Python:** 3.8 oder neuer
- **OpenCV:** Mit GStreamer-Support
- **Ultralytics:** YOLOv8
- **Netzwerk:** Verbindung zum Raspberry Pi

## 🔧 Installation

### 1. Client-PC Dependencies

#### Option A: Mit GStreamer (empfohlen)

```bash
# System-Pakete
sudo apt update
sudo apt install -y \
    python3-opencv \
    libopencv-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools

# Python-Pakete
pip install opencv-contrib-python
pip install ultralytics

# Prüfe OpenCV-Build
python3 -c "import cv2; print('GStreamer:', 'YES' if cv2.getBuildInformation().find('GStreamer: YES') != -1 else 'NO')"
```

#### Option B: Nur FFMPEG (Fallback)

```bash
# Minimal-Installation
pip install opencv-python ultralytics
```

#### Prüfe Installation

```bash
# Python-Imports testen
python3 << EOF
import cv2
import numpy as np
from ultralytics import YOLO
print("✅ Alle Dependencies verfügbar")
print(f"   OpenCV: {cv2.__version__}")
print(f"   NumPy: {np.__version__}")
EOF
```

### 2. Raspberry Pi Setup

#### A) Skript auf Raspberry Pi kopieren

```bash
# Von deinem Client-PC aus:
scp raspberry-pi-scripts/start-preview-stream.sh \
    user@raspberrypi-5-ai-had:~/

# SSH zum Raspberry Pi
ssh user@raspberrypi-5-ai-had

# Skript ausführbar machen
chmod +x ~/start-preview-stream.sh
```

#### B) Manuelles Setup (Alternative)

Falls du das Skript nicht verwenden möchtest:

```bash
# Auf Raspberry Pi:
rpicam-vid \
    --camera 0 \
    --width 640 \
    --height 480 \
    --framerate 5 \
    --rotation 180 \
    --bitrate 1000000 \
    --inline \
    --listen \
    --codec h264 \
    --profile baseline \
    --level 4.2 \
    --flush \
    -t 0 \
    -o "tcp://0.0.0.0:8554" \
    --nopreview
```

## 🚀 Verwendung

### Schritt 1: Preview-Stream auf Raspberry Pi starten

```bash
# SSH zum Raspberry Pi
ssh user@raspberrypi-5-ai-had

# Preview-Stream starten (Standard-Einstellungen)
./start-preview-stream.sh

# Oder mit Custom-Einstellungen:
./start-preview-stream.sh \
    --width 800 \
    --height 600 \
    --fps 10 \
    --rotation 180 \
    --port 8554
```

**Ausgabe:**
```
ℹ️  Starte Preview-Stream...

  📹 Kamera: 0
  📐 Auflösung: 640x480
  🎬 FPS: 5
  🔄 Rotation: 180°
  📊 Bitrate: 1000 kbps
  🔌 Port: 8554

✅ Preview-Stream gestartet (PID: 12345)

ℹ️  Stream-URL: tcp://192.168.1.100:8554

ℹ️  Verwende auf dem Client-PC:
  python python-skripte/ai-had-kamera-auto-trigger.py \
      --trigger-duration 2 \
      --ai-model bird-species
```

### Schritt 2: Auto-Trigger auf Client-PC starten

```bash
# Auf deinem Client-PC:
cd /pfad/zu/vogel-kamera-linux

# Auto-Trigger starten
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species
```

**Ausgabe:**
```
╔══════════════════════════════════════════════════════════════╗
║  🐦 Vogel-Kamera Auto-Trigger v1.2.0                         ║
╠══════════════════════════════════════════════════════════════╣
║  Remote-Host: raspberrypi-5-ai-had                           ║
║  Trigger-Dauer: 2 Minuten                                    ║
║  AI-Model: bird-species                                      ║
║  Cooldown: 30 Sekunden                                       ║
╚══════════════════════════════════════════════════════════════╝

✅ Verbindung zu raspberrypi-5-ai-had erfolgreich

🎬 Initialisiere Stream-Verarbeitung...
📡 Verbinde mit Preview-Stream: tcp://raspberrypi-5-ai-had:8554...
✅ Preview-Stream verbunden
   AI-Model: bird-species
   Threshold: 0.45
   Resolution: 640x480 @ 5fps

👁️  Starte Vogel-Überwachung...
   Preview: 640x480 @ 5fps
   Schwelle: 0.45
   Cooldown: 30s zwischen Aufnahmen

🔍 Überwache Vogelhaus... (Strg+C zum Beenden)

🐦 Vogel erkannt!
🎬 TRIGGER! Starte 2-minütige Aufnahme...
   Zeitstempel: 2025-10-01_14-23-45
...
```

### Schritt 3: Stream-Status prüfen

```bash
# Auf Raspberry Pi:
./start-preview-stream.sh --status
```

**Ausgabe:**
```
✅ Preview-Stream läuft (PID: 12345)

ℹ️  Stream-URL: tcp://192.168.1.100:8554

ℹ️  Prozess-Info:
12345 1 2.5 0.8 00:15:32 rpicam-vid --camera 0 ...
```

### Schritt 4: Stream beenden

```bash
# Auf Raspberry Pi:
./start-preview-stream.sh --stop
```

## ⚙️ Konfiguration

### Stream-Parameter anpassen

```bash
# Höhere Auflösung für bessere Erkennung
./start-preview-stream.sh \
    --width 800 \
    --height 600 \
    --fps 10

# Niedrigere Auflösung für schwache Netzwerke
./start-preview-stream.sh \
    --width 480 \
    --height 360 \
    --fps 3 \
    --bitrate 500
```

### Auto-Trigger-Parameter anpassen

```bash
# Empfindlichere Erkennung
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-threshold 0.35 \
    --cooldown 60

# Weniger false positives
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-threshold 0.55 \
    --cooldown 30
```

### Optimale Einstellungen

| Szenario | Stream-FPS | Auflösung | Threshold | Cooldown |
|----------|-----------|-----------|-----------|----------|
| Standard | 5 | 640x480 | 0.45 | 30s |
| Hohe Genauigkeit | 10 | 800x600 | 0.50 | 60s |
| Niedrige Bandbreite | 3 | 480x360 | 0.40 | 30s |
| Seltene Vögel | 5 | 640x480 | 0.55 | 120s |
| Viele Vögel | 10 | 640x480 | 0.40 | 20s |

## 🐛 Troubleshooting

### Problem: Keine Verbindung zum Stream

**Symptom:**
```
❌ Konnte nicht mit Preview-Stream verbinden
```

**Lösungen:**

1. **Stream läuft auf Raspberry Pi?**
```bash
ssh user@raspberrypi-5-ai-had
./start-preview-stream.sh --status
```

2. **Firewall-Einstellungen**
```bash
# Auf Raspberry Pi: Port 8554 öffnen
sudo ufw allow 8554/tcp
```

3. **Netzwerk-Verbindung testen**
```bash
# Vom Client-PC:
telnet raspberrypi-5-ai-had 8554
```

4. **GStreamer fehlt?**
```bash
# OpenCV mit GStreamer neu installieren
pip install --upgrade --force-reinstall opencv-contrib-python
```

### Problem: Stream laggt oder stottert

**Lösungen:**

1. **Auflösung reduzieren**
```bash
./start-preview-stream.sh --width 480 --height 360 --fps 3
```

2. **Bitrate anpassen**
```bash
./start-preview-stream.sh --bitrate 500
```

3. **Netzwerk-Performance prüfen**
```bash
# Bandwidth-Test
iperf3 -c raspberrypi-5-ai-had
```

### Problem: Zu viele false positives

**Lösungen:**

1. **Threshold erhöhen**
```bash
python python-skripte/ai-had-kamera-auto-trigger.py --trigger-threshold 0.55
```

2. **bird-species Model verwenden**
```bash
# Erkennt nur Vögel (COCO class 14)
python python-skripte/ai-had-kamera-auto-trigger.py --ai-model bird-species
```

3. **Preview-Stream testen**
```bash
# Standalone-Test des Stream-Processors
python python-skripte/stream_processor.py \
    --host raspberrypi-5-ai-had \
    --port 8554 \
    --model bird-species \
    --duration 60
```

### Problem: Hohe CPU-Last auf Client-PC

**Lösungen:**

1. **FPS reduzieren**
```bash
python python-skripte/ai-had-kamera-auto-trigger.py --preview-fps 3
```

2. **Kleineres YOLOv8-Model**
```python
# In stream_processor.py:
# Statt yolov8n.pt (nano)
self.model = YOLO("yolov8n.pt")  # ✅ Schnellste Variante
# Andere Optionen:
# yolov8s.pt - Small (genauer, langsamer)
# yolov8m.pt - Medium (noch genauer, viel langsamer)
```

3. **GPU-Beschleunigung nutzen**
```bash
# CUDA-fähige GPU?
pip install ultralytics[gpu]
```

### Problem: Stream bricht ab

**Symptom:**
```
⚠️ Fehler bei Stream-Verarbeitung: Connection reset
```

**Lösungen:**

1. **Auto-Restart aktivieren**
```bash
# Systemd-Service für Preview-Stream (siehe unten)
```

2. **Timeout erhöhen**
```python
# In stream_processor.py:
StreamProcessor(..., timeout=30)
```

3. **Raspberry Pi überlastet?**
```bash
# CPU-Temperatur prüfen
ssh user@raspberrypi-5-ai-had
vcgencmd measure_temp

# Wenn > 70°C: Kühlung verbessern
```

## 🔄 Automatischer Start (Systemd)

### Preview-Stream als Service

Erstelle `/etc/systemd/system/preview-stream.service` auf dem Raspberry Pi:

```ini
[Unit]
Description=Vogel-Kamera Preview-Stream
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=pi
WorkingDirectory=/home/pi
ExecStart=/home/pi/start-preview-stream.sh
ExecStop=/home/pi/start-preview-stream.sh --stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable preview-stream
sudo systemctl start preview-stream

# Status prüfen
sudo systemctl status preview-stream
```

### Auto-Trigger als Service

Erstelle `/etc/systemd/system/vogel-auto-trigger.service` auf dem Client-PC:

```ini
[Unit]
Description=Vogel-Kamera Auto-Trigger
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/vogel-kamera-linux
ExecStart=/usr/bin/python3 python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

**Aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable vogel-auto-trigger
sudo systemctl start vogel-auto-trigger

# Logs anzeigen
sudo journalctl -u vogel-auto-trigger -f
```

## 📊 Performance-Tipps

### Netzwerk-Optimierung

1. **LAN statt WLAN verwenden**
   - Stabilere Verbindung
   - Niedrigere Latenz

2. **QoS für Stream-Port konfigurieren**
```bash
# Auf Router: Port 8554 priorisieren
```

### Raspberry Pi Optimierung

1. **GPU-Memory erhöhen**
```bash
# /boot/config.txt
gpu_mem=256
```

2. **Übertakten (optional)**
```bash
# /boot/config.txt
over_voltage=6
arm_freq=2400
```

3. **Kühlung verbessern**
   - Aktiver Lüfter
   - Kühlkörper

### Client-PC Optimierung

1. **YOLOv8 auf GPU ausführen**
```python
# Automatisch wenn CUDA verfügbar
model = YOLO("yolov8n.pt")
model.to('cuda')
```

2. **Frame-Skipping bei hoher Last**
```python
# Nur jeden N-ten Frame verarbeiten
if frame_count % 2 == 0:
    bird_detected = processor.process_frame()
```

## 📚 Weiterführende Dokumentation

- [AUTO-TRIGGER-DOKUMENTATION.md](AUTO-TRIGGER-DOKUMENTATION.md) - Auto-Trigger Features
- [AI-MODELLE-VOGELARTEN.md](AI-MODELLE-VOGELARTEN.md) - AI-Modell-Details
- [README.md](../README.md) - Haupt-Dokumentation

## 💡 Tipps

### Stream-Test ohne Auto-Trigger

```bash
# Test mit VLC (Client-PC)
vlc tcp://raspberrypi-5-ai-had:8554

# Test mit FFplay
ffplay -fflags nobuffer -flags low_delay tcp://raspberrypi-5-ai-had:8554

# Test mit GStreamer
gst-launch-1.0 tcpclientsrc host=raspberrypi-5-ai-had port=8554 ! \
    h264parse ! avdec_h264 ! videoconvert ! autovideosink
```

### StreamProcessor Standalone-Test

```bash
# Teste AI-Erkennung auf Stream
python python-skripte/stream_processor.py \
    --host raspberrypi-5-ai-had \
    --port 8554 \
    --model bird-species \
    --threshold 0.45 \
    --duration 60 \
    --debug
```

**Ausgabe:**
```
======================================================================
🐦 Stream Processor Test
======================================================================
Host: raspberrypi-5-ai-had:8554
Model: bird-species
Threshold: 0.45
Duration: 60s
======================================================================

✅ Stream verbunden, starte Erkennung...

🐦 Vogel erkannt! (Frame 123)
🐦 Vogel erkannt! (Frame 187)

======================================================================
📊 Statistiken
======================================================================
Frames verarbeitet: 300
Vögel erkannt: 2
Durchschn. Inferenz-Zeit: 45.2ms
======================================================================
```

## 🤝 Support

Bei Problemen:
1. Logs prüfen: `journalctl -u preview-stream -f`
2. Netzwerk testen: `ping raspberrypi-5-ai-had`
3. Issue erstellen: https://github.com/your-repo/issues
