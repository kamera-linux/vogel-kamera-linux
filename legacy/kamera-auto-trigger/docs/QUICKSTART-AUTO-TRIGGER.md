# 🚀 Quick Start: Auto-Trigger System v1.2.0

Schnellstart-Anleitung für das automatische Vogel-Erkennungs- und Aufnahme-System mit KI-Unterstützung.

**Neu in v1.2.0:**
- 🎬 Zeitlupen-Modus (120fps)
- ⚡ CPU-Optimierung (107% → 40%)
- 🎤 Audio in allen Modi
- 🚀 Wrapper-Skript für einfache Bedienung

## 📋 Checkliste

- [ ] Raspberry Pi 5 mit Camera Module 3 (IMX708)
- [ ] Client-PC mit Python 3.11+ (oder 3.8+)
- [ ] Netzwerk-Verbindung zwischen beiden (LAN empfohlen)
- [ ] SSH-Zugriff auf Raspberry Pi konfiguriert (SSH-Key!)
- [ ] Optional: USB-Mikrofon für Audio-Aufnahmen

## ⚡ 3-Minuten-Setup (v1.2.0)

### 1️⃣ Repository klonen

```bash
# Repository klonen
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux

# Optional: Development-Branch für neueste Features
git checkout devel-v1.2.0
```

### 2️⃣ Virtual Environment einrichten

```bash
# venv erstellen (einmalig)
python3 -m venv .venv

# venv aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# YOLOv8 installieren (für KI-Erkennung)
pip install ultralytics opencv-python

# SSH-Bibliothek
pip install paramiko
```

**Hinweis:** Das Wrapper-Skript `start-vogel-beobachtung.sh` aktiviert die venv automatisch!

### 3️⃣ SSH-Zugriff einrichten

```bash
# SSH-Key generieren (falls noch nicht vorhanden)
ssh-keygen -t ed25519 -C "vogel-kamera"

# Public Key auf Raspberry Pi kopieren
ssh-copy-id pi@raspberrypi-5-ai-had

# SSH-Agent starten (einmalig pro Session)
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Verbindung testen
ssh pi@raspberrypi-5-ai-had "echo SSH funktioniert!"
```

**Hinweis:** Das Wrapper-Skript `start-vogel-beobachtung.sh` startet den SSH-Agent automatisch!

### 4️⃣ Konfiguration erstellen

```bash
# Config-Datei erstellen
mkdir -p kamera-auto-trigger/config
cat > kamera-auto-trigger/config/config.py << 'EOF'
# Remote-Host Konfiguration
REMOTE_HOST = "raspberrypi-5-ai-had"
REMOTE_USER = "pi"
REMOTE_VIDEOS_DIR = "Videos"

# RTSP Stream URL
RTSP_URL = f"rtsp://{REMOTE_HOST}:8554/preview"
EOF
```

### 5️⃣ Auto-Trigger starten! 🚀

```bash
# Standard-Modus (1920x1080 @ 25fps + Audio)
./kamera-auto-trigger/start-vogel-beobachtung.sh

# ODER: Mit KI-Metadaten
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai

# ODER: Zeitlupen-Modus (120fps Slow-Motion!)
./kamera-auto-trigger/start-vogel-beobachtung.sh --slowmo
```

**Erwartete Ausgabe:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐦 Vogel-Beobachtung mit KI gestartet
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aufnahme-Modus: 🤖 Mit KI + Audio (yolov8n.pt)
Preview: 320x240 @ 3 FPS
Recording: 1920x1080 @ 25 FPS + 44.1kHz Mono
CPU-Optimierung: OMP_NUM_THREADS=2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ SSH Verbindung hergestellt
✓ RTSP Stream aktiv: rtsp://raspberrypi-5-ai-had:8554/preview
✓ YOLOv8 Modell geladen

🎯 Überwache Vogelhaus... (Strg+C zum Beenden)
```

🎉 **Fertig!** Das System überwacht jetzt automatisch und startet Aufnahmen bei Vogel-Erkennung.

## 🎬 Modi-Übersicht

### 📹 Standard-Modus
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh
```
- **Auflösung:** 1920x1080 @ 25fps
- **Audio:** 44.1kHz Mono (automatisch)
- **CPU-Last:** ~40% (optimiert!)
- **Verwendung:** Normale HD-Aufnahmen

### 🤖 KI-Modus
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai
```
- **Auflösung:** 1920x1080 @ 25fps
- **Audio:** 44.1kHz Mono
- **Zusätzlich:** KI-Metadaten im Filename
- **CPU-Last:** ~40%
- **Verwendung:** Aufnahmen mit AI-Analyse

### 🎬 Zeitlupen-Modus
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --slowmo
```
- **Auflösung:** 1536x864 @ 120fps
- **Audio:** 44.1kHz Mono
- **Besonderheit:** 10 Sek Pre-Recording
- **CPU-Last:** ~40% (PC), ~75% (RaspPi)
- **Verwendung:** Spektakuläre Slow-Motion!

## 🧪 Testen

### RTSP-Stream ansehen

```bash
# Mit VLC
vlc rtsp://raspberrypi-5-ai-had:8554/preview

# Mit FFplay
ffplay rtsp://raspberrypi-5-ai-had:8554/preview

# Mit mpv
mpv rtsp://raspberrypi-5-ai-had:8554/preview
```

### Vogel-Erkennung simulieren

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

**In v1.2.0 bereits optimiert!** Die Standard-Einstellungen sind CPU-schonend (320x240@3fps).

Falls dennoch Probleme:
- LAN statt WLAN verwenden (empfohlen)
- Raspberry Pi näher am Router platzieren
- Netzwerk-Auslastung prüfen

### ⚡ Hohe CPU-Last (>80%)

**In v1.2.0 gelöst!** CPU-Last wurde von 107% auf ~40% reduziert.

Falls weiterhin hoch:
```bash
# Prüfen: Läuft venv?
which python  # sollte .venv/bin/python zeigen

# Wrapper-Skript nutzt automatisch optimierte Einstellungen
./kamera-auto-trigger/start-vogel-beobachtung.sh
```

### 🎤 Kein Audio in Aufnahmen

**Lösung:**
```bash
# Auf Raspberry Pi prüfen:
arecord -l  # Zeigt alle Audio-Devices

# USB-Mikrofon sollte erscheinen:
# card 2: Device [USB PnP Sound Device]
```

Ohne USB-Mikrofon: System funktioniert trotzdem (nur Video)!

## 📊 Empfohlene Einstellungen v1.2.0

### ⭐ Standard (empfohlen) - Bereits optimal!
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh
```
- Preview: 320x240 @ 3fps
- Recording: 1920x1080 @ 25fps
- Audio: 44.1kHz Mono
- CPU: ~40%

### 🎬 Für spektakuläre Aufnahmen
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --slowmo
```
- Preview: 320x240 @ 2fps
- Recording: 1536x864 @ 120fps (Slow-Motion!)
- Audio: 44.1kHz Mono
- CPU: ~40% (PC), ~75% (RaspPi)

### 🤖 Für detaillierte Analysen
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai
```
- Preview: 320x240 @ 3fps
- Recording: 1920x1080 @ 25fps + KI-Metadaten
- Audio: 44.1kHz Mono
- CPU: ~40%

## 🔄 Als Service einrichten (Optional)

### Client-PC: Auto-Start Auto-Trigger mit Wrapper

```bash
# Auf Client-PC:
sudo nano /etc/systemd/system/vogel-auto-trigger.service
```

Inhalt:
```ini
[Unit]
Description=Vogel-Kamera Auto-Trigger v1.2.0
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/vogel-kamera-linux
Environment="PATH=/path/to/vogel-kamera-linux/.venv/bin:/usr/bin"
ExecStart=/path/to/vogel-kamera-linux/kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vogel-auto-trigger
sudo systemctl start vogel-auto-trigger

# Status prüfen:
sudo systemctl status vogel-auto-trigger

# Logs ansehen:
sudo journalctl -u vogel-auto-trigger -f
```

## 📚 Weitere Dokumentation

- **[../../docs/ARCHITEKTUR.md](../../docs/ARCHITEKTUR.md)** - 🏗️ Detaillierte Architektur mit Mermaid-Diagrammen (NEU in v1.2.0!)
- **[AUTO-TRIGGER-DOKUMENTATION.md](AUTO-TRIGGER-DOKUMENTATION.md)** - Vollständige Feature-Dokumentation
- **[AUTO-TRIGGER-OVERVIEW.md](AUTO-TRIGGER-OVERVIEW.md)** - Konzepte und Übersicht
- **[../../README.md](../../README.md)** - Haupt-Dokumentation
- **[../../docs/CHANGELOG.md](../../docs/CHANGELOG.md)** - Version v1.2.0 Details

## 💡 Tipps & Tricks v1.2.0

### Cooldown zwischen Aufnahmen anpassen

```bash
# Standard: 5 Sekunden
./kamera-auto-trigger/start-vogel-beobachtung.sh

# Mit Parameter: 10 Sekunden Pause
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-cooldown 10
```

### Erkennungs-Schwelle anpassen

```bash
# Weniger false positives (höhere Schwelle)
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --preview-threshold 0.6

# Mehr Erkennungen (niedrigere Schwelle)
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --preview-threshold 0.4
```

### Verschiedene YOLOv8-Modelle testen

```bash
# Größeres Modell (genauer, aber langsamer)
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai yolov8s.pt

# Kleineres Modell (schneller, standard)
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai yolov8n.pt
```

**Hinweis:** Auch mit größeren Modellen bleibt CPU bei ~40% dank imgsz=320!

## 🎯 Nächste Schritte

Nach erfolgreichem Setup:

1. ✅ **Teste alle drei Modi** (Standard, KI, Zeitlupe)
2. 📊 **Überwache CPU-Last** - sollte ~40% sein
3. 🎤 **Audio-Test** - USB-Mikrofon funktioniert?
4. 🎬 **Zeitlupen-Aufnahmen** ansehen - spektakulär!
5. 💾 **Backup einrichten** für Videos-Verzeichnis
6. 🔄 **Systemd-Service** für 24/7-Betrieb (optional)
7. 📖 **[docs/ARCHITEKTUR.md](../../docs/ARCHITEKTUR.md)** lesen - verstehe das System im Detail!

## 🚀 Performance-Highlights v1.2.0

```
CPU-Optimierung:   107% → 40% (-63%)  ✅
Preview-FPS:       5 → 3 (CPU-schonend) ✅
Preview-Auflösung: 640x480 → 320x240   ✅
YOLO-Inferenz:     imgsz=320 (Schlüssel!) ✅
Audio:             Alle Modi (44.1kHz)  ✅
Modi:              3 (Standard/KI/Zeitlupe) ✅
```

Viel Erfolg bei der Vogel-Beobachtung! 🐦🎥🎬
