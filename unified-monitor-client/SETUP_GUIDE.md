# 🚀 Unified Monitor Client - Setup Guide v2.1.0

Automatisiertes Setup-Skript für Remote Raspberry Pi und lokalen Client mit Audio/Video-Synchronisation.

## ✨ Features

Das Setup-Skript automatisiert:

✅ **Remote Pi Setup:**
- System-Updates (apt-get)
- rpicam-apps + ffmpeg + ALSA (Audio/Video Sync)
- Python-Abhängigkeiten (paramiko, python-dotenv)
- Repository klonen/updaten

✅ **Lokaler Client Setup:**
- Virtuelle Python-Umgebung (venv)
- Python-Module installieren (paramiko, click, dotenv)
- Skripte ausführbar machen

✅ **Verifikation:**
- SSH-Verbindung testen
- rpicam-vid + ffmpeg Verfügbarkeit prüfen
- Audio-Devices prüfen
- Python-Versionen validieren

## 📋 Voraussetzungen

### Remote Raspberry Pi:
- Raspberry Pi OS Trixie (Debian 13) oder Bookworm (Debian 12)
- SSH-Zugang aktiviert
- Internetverbindung

### Lokaler Client:
- Python 3.8+
- `python3-pip` und `python3-venv`
- SSH-Client
- Git (für Repository klonen)

### SSH-Setup:
```bash
# 1. SSH-Schlüssel generieren (falls noch nicht vorhanden)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_pi

# 2. Öffentlichen Schlüssel auf Pi kopieren
ssh-copy-id -i ~/.ssh/id_rsa_pi.pub pi@raspberry-pi.local

# 3. Verbindung testen
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "echo 'SSH OK'"
```

## 🚀 Quick Start

### 1. Konfiguration vorbereiten
```bash
cd unified-monitor-client

# .env-Datei erstellen
cp .env.example .env

# Werte anpassen (Hostname, SSH-Key, etc.)
nano .env
```

### 2. Setup ausführen
```bash
# Option A: Shell-Skript (empfohlen)
chmod +x setup_environment.sh
./setup_environment.sh

# Option B: Direkt Python
python3 setup_environment.py
```

### 3. Bestätigung
```
Dieses Skript wird:
   • System-Pakete auf dem Remote Pi aktualisieren (apt-get)
   • Python-Abhängigkeiten installieren
   • Das Repository auf den Remote Pi klonen/updaten
   • Lokale venv und Dependencies installieren

Möchten Sie fortfahren? (ja/nein): ja
```

## 📊 Was wird installiert

### Remote Raspberry Pi
```
System-Updates & Tools:
✓ build-essential, python3-dev
✓ rpicam-apps (v1.9.1+) - Moderne Kamera-Control statt libcamera
✓ ffmpeg (7.1.2+) - Video-Merge & Audio-Sync
✓ alsa-utils (arecord) - Audio-Aufnahme, hw:0,0 Auto-Detection

Python-Abhängigkeiten:
✓ python3-pip, python3-venv
✓ paramiko - SSH-Remote-Komm
✓ python-dotenv - Environment-Konfiguration
```

### Lokaler Client
```
Python Packages (venv):
✓ paramiko   - SSH-Remote-Befehle
✓ click      - CLI-Framework mit Typsicherheit
✓ python-dotenv - .env Konfiguration laden
```

## 🔧 Konfiguration (.env)

```bash
# SSH-Verbindung
SSH_KEY=~/.ssh/id_rsa_pi
SSH_USER=pi
SSH_HOST=raspberry-pi.local

# Remote Pfade
REMOTE_REPO_DIR=/home/pi/vogel-kamera-linux
REMOTE_SCRIPT_DIR=/home/pi/vogel-kamera-linux/raspberry-pi-scripts
REMOTE_VIDEO_BASE=/home/pi/Videos/Vogelhaus

# Parameter
DEFAULT_THRESHOLD=0.5
DEFAULT_COOLDOWN=15
DEFAULT_TRIGGER_DURATION=1.0
```

## ✔️ Verifikation nach Setup

```bash
# SSH-Verbindung testen
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "uname -a"

# Remote Python-Version prüfen
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "python3 --version"

# Lokales venv testen
source ../venv/bin/activate
python3 --version
pip list | grep paramiko
```

## 🚀 Nach dem Setup

### Unified Monitor Client starten
```bash
# Aktiviere venv (falls noch nicht aktiv)
source ../venv/bin/activate

# Starte Client mit verschiedenen Modi:
python3 unified_monitor_client.py test       # 5 Sekunden Test
python3 unified_monitor_client.py normal     # Standard 1920x1080
python3 unified_monitor_client.py slowmo     # Zeitlupe 120fps
python3 unified_monitor_client.py 4k         # Cinema 4K mit Audio
```

### System-Diagnose
```bash
# Remote-System überprüfen
python3 diagnose_remote_system.py
# → Prüft Kamera, Audio-Devices, rpicam-apps, ffmpeg, etc.
```

### Remote-Monitoring direkt auf Raspberry Pi
```bash
# SSH-Zugriff auf den Pi
ssh -i ~/.ssh/id_rsa_rpi roimme@raspberrypi-5

# System-Service überprüfen
systemctl status unified-monitor || echo "Service nicht aktiv"

# Logs anschauen
tail -50 /tmp/unified-camera-monitor.log
```

## 🐛 Troubleshooting

### SSH-Verbindung erfolglos
```bash
# 1. .env-Werte prüfen
cat .env

# 2. SSH-Key prüfen
ls ~/.ssh/id_rsa_pi
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "echo 'OK'"

# 3. Ping prüfen
ping -c 1 raspberry-pi.local

# 4. SSH-Debug
ssh -vvv -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local
```

### Python-Module fehlen (Remote)
```bash
# Manuell installieren (falls Setup fehlschlägt)
ssh -i ~/.ssh/id_rsa_rpi roimme@raspberrypi-5 << 'EOF'
# Basis-Python
sudo apt-get install -y python3-pip python3-venv

# SSH-Kommunikation
python3 -m pip install --upgrade paramiko python-dotenv

# rpicam-apps (moderne Kamera-Control)
sudo apt-get install -y rpicam-apps ffmpeg alsa-utils
EOF
```

### Lokales venv beschädigt
```bash
# Neue venv erstellen
rm -rf ../venv
python3 -m venv ../venv
source ../venv/bin/activate
pip install paramiko click python-dotenv qrcode[pil]
```

### Setup unterbrochen
```bash
# Erneut ausführen (es ist sicher, doppelt zu installieren)
./setup_environment.sh
```

## �️ Deinstallation / Cleanup

Wenn Sie alle Komponenten entfernen möchten:

```bash
# Option 1: Via Wrapper (empfohlen)
./setup_environment.sh --uninstall

# Option 2: Direkt mit Python
python3 setup_environment.py --uninstall
```

### Was wird gelöscht?

**Remote (Raspberry Pi):**
- ✓ Python Virtual Environment und Dependencies (paramiko, dotenv, etc.)
- ✓ YOLO und andere Pakete
- ⚠️ Repository (optional, wird nachgefragt)

**Lokal (Client-PC):**
- ✓ Python Virtual Environment (.venv)
- ✓ Alle installierten Abhängigkeiten
- ✓ Python Cache (__pycache__)
- ✗ NICHT gelöscht: .env (bleibt für späteren Re-Setup)

### Beispiel Deinstallation:

```
🗑️  UNIFIED MONITOR CLIENT - Deinstallation
======================================================================

⚠️  WARNUNG - Dies wird folgende Daten LÖSCHEN:
   REMOTE (Raspberry Pi):
   • Python Virtual Environment und Abhängigkeiten
   • Optional: Repository

   LOKAL (Client-PC):
   • Python Virtual Environment (.venv)
   • Alle installierten Abhängigkeiten
   • NICHT gelöscht: .env und Konfigurationsdatei
======================================================================

Sind Sie sicher? (ja/nein): ja

✓ Remote Dependencies entfernt
Repository 'home/pi/vogel-kamera-linux' löschen? (ja/nein): nein
✓ Remote Cleanup abgeschlossen

✓ venv gelöscht
✓ 3 Caches gelöscht
✓ Lokales Cleanup abgeschlossen

✨ Deinstallation abgeschlossen!
```

### Nach Deinstallation

**Verbleibende Dateien:**
- `.env` - Konfigurationsdatei (bleibt für späteren Re-Setup)
- Source-Code und Dokumentation
- Remote Dateien (Videos, Logs) auf dem Pi

**Neu installieren:**
```bash
./setup_environment.sh
```

**Manueller Cleanup:**
```bash
# Nur venv löschen
rm -rf venv

# Kompletter Cleanup (ohne Deinstallations-Menü)
rm -rf venv
find . -type d -name __pycache__ -exec rm -r {} +
```

## �📚 Dokumentation

- **[README.md](README.md)** - Unified Monitor Client Dokumentation
- **[config.py](config.py)** - Konfiguration und Konstanten
- **[.env.example](.env.example)** - Environment-Template
- **[setup_environment.py](setup_environment.py)** - Setup-Skript-Code
- **[setup_environment.sh](setup_environment.sh)** - Shell-Wrapper

## 📝 Logs

Das Setup-Skript gibt detaillierte Logs aus. Für Debugging:

```bash
# Vollständigen Output speichern
./setup_environment.sh > setup.log 2>&1

# Log anschauen
cat setup.log
```

---

**Version:** v2.1.0  
**Aktualisiert:** März 2026  
**Lizenz:** MIT

## 🌐 Weitere Ressourcen

- **[README.md](README.md)** - Hauptdokumentation Unified Monitor Client
- **[../raspberry-pi-scripts/UNIFIED-MONITOR-README.md](../raspberry-pi-scripts/UNIFIED-MONITOR-README.md)** - Remote System Docs
- **[../QUICK_REFERENCE_v2.1.0.md](../QUICK_REFERENCE_v2.1.0.md)** - Schnelle Befehlsreferenz
- **[../docs/TRIXIE-MIGRATION.md](../docs/TRIXIE-MIGRATION.md)** - Trixie Setup-Guide
- **[config.py](config.py)** - Konfiguration und Konstanten
- **[.env.example](.env.example)** - Environment-Template
