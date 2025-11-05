# 🔧 Installation auf Raspberry Pi OS Trixie (Debian 13)

**Version:** v1.3.1  
**Branch:** main  
**Target:** Raspberry Pi 5 mit Trixie

## 📋 Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Raspberry Pi Setup](#raspberry-pi-setup)
- [MediaMTX Installation](#mediamtx-installation)
- [Python-Pakete](#python-pakete)
- [Client-PC Setup](#client-pc-setup)
- [Konfiguration](#konfiguration)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)

---

## 🛠️ Voraussetzungen

### Hardware
- **Raspberry Pi 5** (empfohlen: 8GB RAM)
- **IMX708 Camera Module 3 Wide** (oder kompatibel)
- Optional: 2× Kameras für Dual-Setup
- **USB-Mikrofon** für Audio-Aufnahmen
- **Gigabit LAN** (empfohlen) oder WiFi 6
- **32GB+ microSD-Karte** (Class 10, A2)

### Software
- **Raspberry Pi OS Trixie (Debian 13)** - 64-bit
- SSH-Zugriff aktiviert
- Feste IP-Adresse oder Hostname

---

## 📦 Raspberry Pi Setup

### 1. Betriebssystem installieren

```bash
# Raspberry Pi Imager verwenden:
# - Raspberry Pi OS (64-bit) Trixie
# - SSH aktivieren
# - Hostname: raspberrypi-5-ai-had (oder eigener)
# - Netzwerk konfigurieren
```

### 2. System aktualisieren

```bash
sudo apt-get update
sudo apt-get full-upgrade -y
sudo apt-get autoremove -y
sudo reboot
```

### 3. Kamera-Module prüfen

```bash
# Liste alle Kameras:
rpicam-hello --list-cameras

# Erwartete Ausgabe (Dual-Kamera):
# Available cameras
# -----------------
# 0 : imx708_wide [4608x2592 10-bit RGGB] (/base/axi/pcie@120000/rp1/i2c@88000/imx708@1a)
# 1 : imx708_wide [4608x2592 10-bit RGGB] (/base/axi/pcie@120000/rp1/i2c@80000/imx708@1a)

# Test Kamera 1 (Preview/Trigger):
rpicam-hello --camera 1 --timeout 5000
```

### 4. FFmpeg prüfen

```bash
ffmpeg -version
# Erwartete Version: 7.1.2 oder höher
```

---

## 🎬 MediaMTX Installation

### Download & Installation

```bash
# MediaMTX v1.9.1 herunterladen
cd /tmp
wget https://github.com/bluenviron/mediamtx/releases/download/v1.9.1/mediamtx_v1.9.1_linux_arm64v8.tar.gz

# Entpacken
tar -xzf mediamtx_v1.9.1_linux_arm64v8.tar.gz

# Installieren
sudo mv mediamtx /usr/local/bin/
sudo chmod +x /usr/local/bin/mediamtx

# Version prüfen
/usr/local/bin/mediamtx --version
# Ausgabe: v1.9.1
```

### Konfiguration erstellen

```bash
# Konfigurationsverzeichnis
sudo mkdir -p /etc/mediamtx

# Konfigurationsdatei erstellen
sudo nano /etc/mediamtx/mediamtx.yml
```

**Inhalt von `/etc/mediamtx/mediamtx.yml`:**

```yaml
# MediaMTX Konfiguration für vogel-kamera-linux
# Version: 1.3.0-dev (Trixie)

# Logging
logLevel: info
logDestinations: [stdout]
logFile: /var/log/mediamtx.log

# API (optional)
api: yes
apiAddress: :9997

# Protokoll-Adressen
rtspAddress: :8554
rtmpAddress: :1935
hlsAddress: :8888
webrtcAddress: :8889

# Pfade
paths:
  # Preview-Stream für Auto-Trigger
  cam:
    source: rpiCamera
    sourceOnDemand: yes  # ⚡ WICHTIG: On-Demand für Dual-Kamera
    
    # Kamera-Einstellungen
    rpiCameraWidth: 640
    rpiCameraHeight: 480
    rpiCameraFPS: 5
    rpiCameraBitrate: 1000000  # 1 Mbps
    
    # Kamera-Auswahl
    rpiCameraCamID: 1  # Kamera 1 für Preview/Trigger
    
    # Optional: Rotation/Flip
    # rpiCameraFlipHorizontal: no
    # rpiCameraFlipVertical: no
    
    # Optional: Autofocus
    # rpiCameraAfMode: continuous
    
  # Weitere Pfade können hier definiert werden
```

**Wichtige Parameter:**

- `sourceOnDemand: yes` - Startet/stoppt Kamera automatisch
- `rpiCameraCamID: 1` - Verwendet Kamera 1 (i2c@80000)
- `640x480 @ 5fps` - Optimiert für CPU-Last und Netzwerk
- `1 Mbps Bitrate` - Ausreichend für Preview, niedrige Bandbreite

### Systemd Service einrichten

```bash
# Service-Datei erstellen
sudo nano /etc/systemd/system/mediamtx.service
```

**Inhalt von `/etc/systemd/system/mediamtx.service`:**

```ini
[Unit]
Description=MediaMTX RTSP Server für vogel-kamera-linux
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=roimme  # Anpassen an eigenen User!
Group=roimme
ExecStart=/usr/local/bin/mediamtx /etc/mediamtx/mediamtx.yml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Sicherheit
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**

```bash
# Systemd neu laden
sudo systemctl daemon-reload

# Service aktivieren (Autostart)
sudo systemctl enable mediamtx

# Service starten
sudo systemctl start mediamtx

# Status prüfen
sudo systemctl status mediamtx
# Erwartete Ausgabe: "active (running)"

# Logs ansehen
sudo journalctl -u mediamtx -f
```

### MediaMTX testen

```bash
# Von Raspberry Pi:
ffplay rtsp://localhost:8554/cam

# Von Client-PC (IP anpassen):
ffplay rtsp://192.168.178.59:8554/cam

# Mit VLC:
vlc rtsp://192.168.178.59:8554/cam
```

**Erwartete Ausgabe:**
- Stream startet automatisch (On-Demand)
- 640x480 @ 5fps Video
- Kamera-LED leuchtet
- Stream stoppt nach ~10s wenn kein Client

---

## 🐍 Python-Pakete

> ⚠️ **PEP 668:** Auf Trixie ist die Python-Umgebung "externally-managed".  
> → **Verwenden Sie `apt-get`, NICHT `pip`!**

### Basis-Pakete installieren

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-full \
    python3-pip \
    python3-venv \
    python3-scp \
    python3-paramiko \
    python3-opencv \
    python3-numpy \
    python3-scipy \
    python3-matplotlib \
    python3-pil
```

### YOLO (optional, für lokale Tests)

```bash
# Ultralytics YOLO (falls gewünscht):
# ACHTUNG: Benötigt viel Speicher und Zeit!
pip3 install ultralytics --break-system-packages
# Oder in venv:
python3 -m venv ~/yolo-env
source ~/yolo-env/bin/activate
pip install ultralytics
```

### Audio-Tools

```bash
# ALSA & PulseAudio (falls noch nicht installiert)
sudo apt-get install -y \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils
```

### SSH-Key-Authentifizierung

```bash
# Auf Client-PC:
# SSH-Key generieren (falls noch nicht vorhanden)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_ai-had -C "ai-had-camera"

# Public Key auf Raspberry Pi kopieren
ssh-copy-id -i ~/.ssh/id_rsa_ai-had.pub roimme@192.168.178.59

# SSH-Config auf Client-PC (optional)
nano ~/.ssh/config
```

**Inhalt `~/.ssh/config`:**

```
Host raspberrypi-5-ai-had
    HostName 192.168.178.59
    User roimme
    IdentityFile ~/.ssh/id_rsa_ai-had
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

**Test:**

```bash
# SSH-Verbindung testen
ssh -i ~/.ssh/id_rsa_ai-had roimme@192.168.178.59

# Ohne Config:
ssh raspberrypi-5-ai-had
```

---

## 💻 Client-PC Setup

### 1. Repository klonen

```bash
# feat/trixie-support Branch klonen
git clone -b feat/trixie-support https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
```

### 2. Virtuelle Umgebung erstellen

```bash
# venv erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r config/requirements.txt
```

### 3. Konfiguration erstellen

```bash
# .env-Vorlage kopieren
cp python-skripte/.env.example python-skripte/.env

# Anpassen
nano python-skripte/.env
```

**Mindest-Konfiguration `.env`:**

```bash
# SSH-Verbindung
SSH_HOST=192.168.178.59
SSH_USER=roimme
SSH_KEY_PATH=/home/imme/.ssh/id_rsa_ai-had

# MediaMTX Stream (NEU für Trixie!)
STREAM_PROTOCOL=rtsp
STREAM_HOST=192.168.178.59
STREAM_PORT=8554
STREAM_PATH=/cam

# Kamera-Einstellungen
CAMERA_ID=0  # Aufnahme-Kamera (Kamera 0)
PREVIEW_CAMERA_ID=1  # Preview-Kamera (Kamera 1)

# Lokale Speicher-Pfade
LOCAL_MEDIA_PATH=/media/imme/ENCRYPTSSD/daten/vogel-kamera-aufnahmen
```

### 4. Konfiguration testen

```bash
python python-skripte/config.py

# Erwartete Ausgabe:
# ✅ Konfiguration erfolgreich geladen
# SSH: roimme@192.168.178.59
# Stream: rtsp://192.168.178.59:8554/cam
# ...
```

---

## ✅ Tests

### 1. MediaMTX Status prüfen

```bash
# Auf Raspberry Pi:
sudo systemctl status mediamtx

# Stream-Test:
ffplay rtsp://localhost:8554/cam
```

### 2. Auto-Trigger testen

```bash
# Auf Client-PC:
cd vogel-kamera-linux
source venv/bin/activate

# Wrapper-Skript:
./kamera-auto-trigger/start-vogel-beobachtung.sh

# Oder direkt:
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-duration 1.0 \
    --preview-fps 3 \
    --preview-width 320 \
    --preview-height 240
```

**Erwartete Ausgabe:**

```
🔍 Prüfe MediaMTX auf raspberrypi-5-ai-had...
✅ MediaMTX läuft
🎬 Starte RTSP-Stream-Analyse...
📡 Verbinde zu rtsp://192.168.178.59:8554/cam
✅ Stream-Verbindung erfolgreich
📊 Stream-Eigenschaften:
   - Auflösung: 640x480
   - FPS: 5.0
🔍 Starte Vogel-Erkennung mit YOLOv8n...
🐦 VOGEL ERKANNT! Konfidenz: 0.52, Trigger in 1.0s
```

### 3. Manuelle Aufnahme testen

```bash
# Zeitlupe (120fps, OHNE Audio):
python python-skripte/ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py \
    --duration 5 \
    --width 1536 \
    --height 864

# HD mit KI (30fps + Audio):
python python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 \
    --width 1920 \
    --height 1080 \
    --ai-modul on \
    --no-stream-restart
```

---

## 🐛 Troubleshooting

### MediaMTX startet nicht

```bash
# Logs prüfen:
sudo journalctl -u mediamtx -n 50

# Häufige Ursachen:
# - Port 8554 bereits belegt: sudo lsof -i :8554
# - Kamera nicht erkannt: rpicam-hello --list-cameras
# - User-Rechte: sudo chown roimme:roimme /etc/mediamtx/mediamtx.yml
```

### Stream-Verbindung schlägt fehl

```bash
# 1. MediaMTX läuft?
sudo systemctl status mediamtx

# 2. Port erreichbar?
nc -zv 192.168.178.59 8554

# 3. Firewall-Regel (falls UFW aktiv):
sudo ufw allow 8554/tcp

# 4. Stream direkt testen:
ffplay rtsp://192.168.178.59:8554/cam
```

### Kamera bereits in Benutzung (Exit 139)

```bash
# Problem: Nur 1 libcamera-Session erlaubt
# Lösung: On-Demand aktiviert?

# MediaMTX Config prüfen:
grep sourceOnDemand /etc/mediamtx/mediamtx.yml
# Sollte: sourceOnDemand: yes

# Kamera-Prozesse prüfen:
ps aux | grep -E 'rpicam|libcamera|mtxrpicam'

# Falls hängend, killen:
sudo pkill -9 mtxrpicam
```

### python3-scp Installation schlägt fehl

```bash
# Problem: "Unable to locate package python3-scp"
# Lösung: Repositories aktualisieren

sudo apt-get update
sudo apt-cache search python3-scp
sudo apt-get install -y python3-scp

# Falls immer noch fehlt:
pip3 install scp --break-system-packages
# Oder in venv verwenden
```

### H.264 Fehler beim Stream-Start

```bash
# Problem: stderr-Warnungen "[h264 @ ...]"
# Status: Kosmetisch, funktioniert trotzdem

# Filter in Scripts bereits implementiert:
# - stream_processor.py: os.environ FFmpeg-Filter
# - run-auto-trigger.sh: stderr-Filterung

# Test ohne Filter:
export FFREPORT=level=quiet
ffplay rtsp://192.168.178.59:8554/cam
```

### Auto-Trigger erkennt keine Vögel

```bash
# 1. YOLO-Modell vorhanden?
ls -lh ~/.cache/ultralytics/

# 2. Confidence zu hoch?
# → In ai-had-kamera-auto-trigger.py:
# confidence_threshold=0.3  # Niedriger = sensitiver

# 3. Test mit eigenem Video:
python tools/test_ai_features.py --video-path test.mp4

# 4. CPU-Last prüfen:
python python-skripte/remote_system_monitor.py
# CPU > 80% = YOLO zu langsam
```

---

## 📚 Weitere Ressourcen

- **Migration-Guide:** [TRIXIE-MIGRATION.md](TRIXIE-MIGRATION.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md) - v1.3.1
- **Architektur:** [ARCHITEKTUR.md](ARCHITEKTUR.md)
- **Auto-Trigger Doku:** [../kamera-auto-trigger/README.md](../kamera-auto-trigger/README.md)

---

## 🆘 Support

**Bei Problemen:**

1. Logs prüfen: `sudo journalctl -u mediamtx -n 100`
2. GitHub Issues: [vogel-kamera-linux/issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
3. Diskussionen: [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)

---

**Installation abgeschlossen!** 🎉

Nächster Schritt: [Auto-Trigger Quickstart](../kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md)
