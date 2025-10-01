# 🚀 Quick Start: Auto-Trigger System

Schnellstart-Anleitung für das automatische Vogel-Erkennungs- und Aufnahme-System.

## 📋 Checkliste

- [ ] Raspberry Pi 5 mit Camera Module 3
- [ ] Client-PC mit Python 3.8+
- [ ] Netzwerk-Verbindung zwischen beiden
- [ ] SSH-Zugriff auf Raspberry Pi konfiguriert

## ⚡ 5-Minuten-Setup

### 1️⃣ Client-PC vorbereiten

```bash
# Repository klonen (falls noch nicht geschehen)
git clone https://github.com/your-repo/vogel-kamera-linux.git
cd vogel-kamera-linux

# Core-Dependencies installieren
pip install -r requirements.txt

# Auto-Trigger-Dependencies installieren
pip install -r requirements-autotrigger.txt

# System-Pakete (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3-opencv libgstreamer1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-libav

# .env konfigurieren
cp .env.example .env
nano .env
# REMOTE_HOST=raspberrypi-5-ai-had
# REMOTE_USER=pi
# SSH_KEY_PATH=/home/user/.ssh/id_rsa
```

### 2️⃣ Raspberry Pi einrichten

```bash
# Stream-Skript auf Raspberry Pi kopieren
scp raspberry-pi-scripts/start-preview-stream.sh \
    pi@raspberrypi-5-ai-had:~/

# SSH zum Raspberry Pi
ssh pi@raspberrypi-5-ai-had

# Skript ausführbar machen
chmod +x ~/start-preview-stream.sh

# Preview-Stream starten
./start-preview-stream.sh
```

**Erwartete Ausgabe:**
```
✅ Preview-Stream gestartet (PID: 12345)
ℹ️  Stream-URL: tcp://192.168.1.100:8554
```

### 3️⃣ Auto-Trigger starten

```bash
# Zurück auf Client-PC
# In vogel-kamera-linux Verzeichnis:

python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species
```

**Erwartete Ausgabe:**
```
╔══════════════════════════════════════════════════════════════╗
║  🐦 Vogel-Kamera Auto-Trigger v1.2.0                         ║
╚══════════════════════════════════════════════════════════════╝

✅ Verbindung zu raspberrypi-5-ai-had erfolgreich
✅ Preview-Stream verbunden
🔍 Überwache Vogelhaus... (Strg+C zum Beenden)
```

🎉 **Fertig!** Das System überwacht jetzt automatisch und startet Aufnahmen bei Vogel-Erkennung.

## 🧪 Testen

### Stream-Test (ohne AI)

```bash
# Stream mit VLC ansehen
vlc tcp://raspberrypi-5-ai-had:8554

# Oder mit FFplay
ffplay tcp://raspberrypi-5-ai-had:8554
```

### AI-Erkennung testen

```bash
# Standalone-Test des StreamProcessors
python python-skripte/stream_processor.py \
    --host raspberrypi-5-ai-had \
    --model bird-species \
    --duration 30
```

## 🛠️ Troubleshooting

### ❌ "Konnte nicht mit Preview-Stream verbinden"

**Lösung 1:** Stream läuft auf Raspberry Pi?
```bash
ssh pi@raspberrypi-5-ai-had
./start-preview-stream.sh --status
```

**Lösung 2:** Firewall?
```bash
# Auf Raspberry Pi:
sudo ufw allow 8554/tcp
```

**Lösung 3:** Netzwerk-Verbindung?
```bash
ping raspberrypi-5-ai-had
telnet raspberrypi-5-ai-had 8554
```

### ❌ "ImportError: No module named cv2"

**Lösung:**
```bash
pip install opencv-contrib-python
```

### ❌ "ImportError: No module named ultralytics"

**Lösung:**
```bash
pip install ultralytics
```

### ⚠️ "GStreamer: NO" bei OpenCV-Check

**Lösung:**
```bash
# System-Pakete installieren
sudo apt install libgstreamer1.0-dev gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad

# OpenCV neu installieren
pip install --upgrade --force-reinstall opencv-contrib-python

# Prüfen
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep GStreamer
```

### 🐌 Stream laggt

**Lösung 1:** Auflösung reduzieren
```bash
# Auf Raspberry Pi:
./start-preview-stream.sh --stop
./start-preview-stream.sh --width 480 --height 360 --fps 3
```

**Lösung 2:** LAN statt WLAN verwenden

**Lösung 3:** Bitrate reduzieren
```bash
./start-preview-stream.sh --bitrate 500
```

## 📊 Empfohlene Einstellungen

### Standard (ausgewogen)
```bash
# Raspberry Pi:
./start-preview-stream.sh \
    --width 640 --height 480 --fps 5

# Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --trigger-threshold 0.45 \
    --cooldown 30
```

### Hohe Genauigkeit
```bash
# Raspberry Pi:
./start-preview-stream.sh \
    --width 800 --height 600 --fps 10

# Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-threshold 0.50 \
    --cooldown 60
```

### Schwache Netzwerk-Verbindung
```bash
# Raspberry Pi:
./start-preview-stream.sh \
    --width 480 --height 360 --fps 3 --bitrate 500

# Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --preview-fps 3 \
    --trigger-threshold 0.40
```

## 🔄 Als Service einrichten (Optional)

### Raspberry Pi: Auto-Start Preview-Stream

```bash
# Auf Raspberry Pi:
sudo nano /etc/systemd/system/preview-stream.service
```

Inhalt:
```ini
[Unit]
Description=Vogel-Kamera Preview-Stream
After=network-online.target

[Service]
Type=forking
User=pi
WorkingDirectory=/home/pi
ExecStart=/home/pi/start-preview-stream.sh
ExecStop=/home/pi/start-preview-stream.sh --stop
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable preview-stream
sudo systemctl start preview-stream
```

### Client-PC: Auto-Start Auto-Trigger

```bash
# Auf Client-PC:
sudo nano /etc/systemd/system/vogel-auto-trigger.service
```

Inhalt:
```ini
[Unit]
Description=Vogel-Kamera Auto-Trigger
After=network-online.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/vogel-kamera-linux
ExecStart=/usr/bin/python3 python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 --ai-model bird-species
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vogel-auto-trigger
sudo systemctl start vogel-auto-trigger

# Logs ansehen:
sudo journalctl -u vogel-auto-trigger -f
```

## 📚 Weitere Dokumentation

- **[PREVIEW-STREAM-SETUP.md](docs/PREVIEW-STREAM-SETUP.md)** - Detaillierte Setup-Anleitung
- **[AUTO-TRIGGER-DOKUMENTATION.md](docs/AUTO-TRIGGER-DOKUMENTATION.md)** - Feature-Dokumentation
- **[README.md](README.md)** - Haupt-Dokumentation

## 💡 Tipps

### Status-Reports anpassen

```bash
# Status alle 10 Minuten statt 15
python python-skripte/ai-had-kamera-auto-trigger.py \
    --status-interval 10
```

### CPU-Temperatur-Limit anpassen

```bash
# Beende bei 65°C statt 70°C
python python-skripte/ai-had-kamera-auto-trigger.py \
    --max-cpu-temp 65
```

### Längere Aufnahmen bei Erkennung

```bash
# 5 Minuten statt 2 Minuten
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 5
```

### Mehrere Erkennungen schneller nacheinander

```bash
# Nur 10 Sekunden Cooldown
python python-skripte/ai-had-kamera-auto-trigger.py \
    --cooldown 10
```

## 🎯 Nächste Schritte

Nach erfolgreichem Setup:

1. **Teste verschiedene Schwellen-Werte** für optimale Erkennungs-Rate
2. **Überwache CPU-Temperatur** auf Raspberry Pi
3. **Prüfe Festplatten-Speicher** regelmäßig
4. **Backup der Aufnahmen** einrichten
5. **Systemd-Services aktivieren** für 24/7-Betrieb

Viel Erfolg! 🐦🎥
