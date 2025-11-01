# 🔄 Migration zu Raspberry Pi OS Trixie (Debian 13)

**Version:** v1.3.0-dev  
**Datum:** 1. November 2025  
**Status:** In Entwicklung

## 📋 Überblick

Dieses Dokument beschreibt die Migration von Raspberry Pi OS Bookworm (Debian 12) zu Trixie (Debian 13) und die notwendigen Anpassungen am Vogel-Kamera-System.

## ⚠️ Breaking Changes

### 1. **FFmpeg 7.1.2 - TCP-Streaming nicht mehr unterstützt**

**Problem:**
```bash
# Funktioniert NICHT mehr auf Trixie:
rpicam-vid --codec h264 -o tcp://0.0.0.0:8888?listen=1
```

**Fehlermeldung:**
```
tcp://0.0.0.0:8888?listen=1: Invalid argument
```

**Ursache:** FFmpeg 7.1.2 hat das `listen=1` TCP-Format entfernt.

**Lösung:** Migration zu MediaMTX RTSP Server (siehe unten)

---

### 2. **Python Externally-Managed Environment**

**Problem:**
```bash
pip3 install scp
# error: externally-managed-environment
```

**Lösung:**
```bash
# Stattdessen apt verwenden:
sudo apt-get install python3-scp python3-paramiko
```

---

### 3. **libcamera Limitierung - Nur 1 Kamera-Session**

**Problem:** Raspberry Pi 5 mit 2 Kameras kann nur **eine** libcamera-Session gleichzeitig ausführen.

**Lösung:** On-Demand Stream-Modus (siehe MediaMTX Konfiguration)

---

## 🚀 MediaMTX RTSP Server Setup

### Installation

```bash
# MediaMTX v1.9.1 herunterladen
wget https://github.com/bluenviron/mediamtx/releases/download/v1.9.1/mediamtx_v1.9.1_linux_arm64v8.tar.gz
tar -xzf mediamtx_v1.9.1_linux_arm64v8.tar.gz
sudo mv mediamtx /usr/local/bin/
sudo chmod +x /usr/local/bin/mediamtx
```

### Konfiguration

**Datei:** `/etc/mediamtx/mediamtx.yml`

```yaml
logLevel: info
logDestinations: [stdout]
logFile: /var/log/mediamtx.log

rtspAddress: :8554
rtmpAddress: :1935
hlsAddress: :8888
webrtcAddress: :8889

paths:
  cam:
    source: rpiCamera
    sourceOnDemand: yes  # ⚡ WICHTIG: On-Demand für Dual-Kamera-Betrieb
    
    # Kamera-Einstellungen
    rpiCameraWidth: 640
    rpiCameraHeight: 480
    rpiCameraFPS: 5
    rpiCameraBitrate: 1000000
    rpiCameraCamID: 1  # Kamera 1 für Preview/Trigger
```

### Systemd Service

**Datei:** `/etc/systemd/system/mediamtx.service`

```ini
[Unit]
Description=MediaMTX RTSP Server
After=network.target

[Service]
Type=simple
User=roimme
ExecStart=/usr/local/bin/mediamtx /etc/mediamtx/mediamtx.yml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mediamtx
sudo systemctl start mediamtx
sudo systemctl status mediamtx
```

---

## 🎯 Dual-Kamera-Strategie

### Konzept

**Problem:** libcamera erlaubt nur 1 aktive Session.

**Lösung:** 
- **Kamera 1** (i2c@80000): MediaMTX Preview-Stream (On-Demand)
- **Kamera 0** (i2c@88000): High-Quality Aufnahmen (rpicam-vid)

### Funktionsweise

1. **Monitoring läuft:**
   - Auto-Trigger verbindet zu `rtsp://192.168.178.59:8554/cam`
   - MediaMTX startet `mtxrpicam` für Kamera 1
   - YOLO analysiert Preview-Frames (640x480 @ 5fps)

2. **Vogel erkannt:**
   - Trigger aktiviert sich nach 1.0s konsistenter Erkennung
   - Stream läuft weiter (andere Kamera!)
   - Aufnahme-Script startet `rpicam-vid` mit Kamera 0

3. **Aufnahme läuft:**
   - Kamera 0: 1536x864 @ 120fps (Zeitlupe)
   - Kamera 1: Stream bleibt aktiv für Monitoring
   - **ABER:** Nur eine kann tatsächlich aktiv sein!

4. **MediaMTX On-Demand:**
   - Kein Client verbunden → mtxrpicam stoppt automatisch
   - Kamera-Zugriff freigegeben für Aufnahmen
   - Client verbindet → mtxrpicam startet automatisch

---

## 🔧 Code-Änderungen

### stream_processor.py

**Wichtige Fixes:**

1. **sys-Import hinzugefügt:**
```python
import os
import sys  # NEU: Für sys.stdout.flush()
```

2. **GStreamer deaktiviert:**
```python
# GStreamer-Backend überspringen (blockiert bei RTSP)
backends = [
    # (cv2.CAP_GSTREAMER, gst_pipeline),  # Deaktiviert
    (cv2.CAP_FFMPEG, self.stream_url),
]
```

3. **FFMPEG-Timeouts erhöht:**
```python
self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 30000)  # 30s statt 10s
```

4. **Frame-Retry-Logik:**
```python
for attempt in range(10):  # Bis zu 10 Versuche
    ret, frame = self.cap.read()
    if ret and frame is not None:
        break
    time.sleep(1)
```

5. **Output-Buffering gelöst:**
```python
print("✅ Stream-Verbindung erfolgreich")
sys.stdout.flush()  # Sofortiger Output
```

### ai-had-kamera-auto-trigger.py

**Trigger-Optimierung:**

```python
trigger_duration=1.0,  # 1.0s statt 2.0s (responsive für bewegliche Vögel)
```

**Toleranz-Fenster:**
```python
# Erlaube 0.5s Lücke ohne Timer-Reset
if gap_since_last > 0.5:
    self.first_detection_time = None
```

### run-auto-trigger.sh

**MediaMTX-Check:**

```bash
# Prüfe MediaMTX systemd statt TCP-Port
if ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
   'sudo systemctl is-active mediamtx' 2>/dev/null; then
    echo "✅ läuft"
fi
```

---

## 📦 Python-Abhängigkeiten

### Auf Raspberry Pi (Trixie)

```bash
# System-Pakete statt pip:
sudo apt-get install -y \
    python3-scp \
    python3-paramiko \
    python3-opencv \
    python3-numpy
```

### Auf Client-PC

```bash
# Wie gehabt, venv verwenden:
pip install scp paramiko opencv-python ultralytics
```

---

## ✅ Test-Checkliste

- [ ] MediaMTX läuft: `sudo systemctl status mediamtx`
- [ ] RTSP-Stream erreichbar: `ffplay rtsp://192.168.178.59:8554/cam`
- [ ] Auto-Trigger verbindet: Stream-Processor zeigt "✅ Stream-Verbindung erfolgreich"
- [ ] Trigger-Logik: 1.0s Erkennungsdauer, 0.5s Toleranz
- [ ] Aufnahmen funktionieren: Kamera 0 startet wenn MediaMTX stoppt
- [ ] On-Demand: mtxrpicam stoppt automatisch wenn kein Client

---

## 🔄 Rollback zu Bookworm

Falls Trixie nicht funktioniert:

```bash
# 1. Zu main-Branch wechseln (v1.2.x)
git checkout main

# 2. Raspberry Pi neu aufsetzen mit Bookworm
# https://www.raspberrypi.com/software/operating-systems/

# 3. Alte Konfiguration wiederherstellen
# TCP-Stream statt MediaMTX funktioniert auf Bookworm
```

---

## 📚 Weitere Ressourcen

- [MediaMTX Dokumentation](https://github.com/bluenviron/mediamtx)
- [Raspberry Pi OS Trixie Release Notes](https://www.raspberrypi.com/news/)
- [FFmpeg 7.x Breaking Changes](https://ffmpeg.org/download.html)
- [libcamera Dokumentation](https://libcamera.org/)

---

## 🐛 Bekannte Probleme

### 1. Hailo AI HAT nicht funktional
**Status:** Trixie-DKMS fehlt  
**Workaround:** CPU-basiertes YOLO (funktioniert)

### 2. H.264-Fehler beim Stream-Start
**Status:** Kosmetisch, funktioniert trotzdem  
**Filter:** `grep -v '\[h264'` in Scripts

### 3. Paralleler Kamera-Betrieb nicht möglich
**Status:** libcamera-Limitierung  
**Lösung:** On-Demand Modus

---

**Kontakt:** Bei Fragen → GitHub Issues
