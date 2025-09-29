# 🐦 Vogel-Kamera-Linux

[![Version](https://img.shields.io/badge/Version-v1.1.7-brightgreen)](https://github.com/roimme65/vogel-kamera-linux/releases/tag/v1.1.7)
[![GitHub Issues](https://img.shields.io/github/issues/roimme65/vogel-kamera-linux)](https://github.com/roimme65/vogel-kamera-linux/issues)
[![GitHub PRs](https://img.shields.io/github/issues-pr/roimme65/vogel-kamera-linux)](https://github.com/roimme65/vogel-kamera-linux/pulls)
[![License](https://img.shields.io/github/license/roimme65/vogel-kamera-linux)](LICENSE)

![Komplettes Vogel-Kamera System](assets/vogelhaus-kamera-komplett.png)

**Professionelles Vogelhaus mit integrierter Raspberry Pi Kamera - Komplettsystem bereit für den Einsatz**

Ferngesteuerte Kameraüberwachung für Vogelhäuser mit KI-gestützter Objekterkennung.

### Basis-Aufnahme
```bash
python python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 \
    --width 1920 \
    --height 1080 \
    --ai-modul on
```

> 📺 **Beispielaufnahmen verfügbar:** [Vogel-Kamera Aufnahmen](https://www.youtube.com/@vogel-kamera-linux) - Echte Aufnahmen mit der Kamera

## 📖 Überblick

Dieses Projekt ermöglicht die Fernsteuerung von Raspberry Pi-Kameras zur Überwachung von Vogelhäusern. Es bietet hochauflösende Video- und Audioaufnahmen mit KI-basierter Objekterkennung (YOLOv8) und automatischer Dateiorganisation.

### 🎬 YouTube-Kanal & Beispielaufnahmen

[![YouTube Channel](https://img.shields.io/badge/📺_YouTube_Kanal-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@vogel-kamera-linux)

**📱 QR-Code für mobilen Zugriff:**

![YouTube QR Code](assets/qr-youtube-channel.png)

| Beispielaufnahmen | Beschreibung |
|-------------------|--------------|
| 🐦 **Vogelerkennung Live** | Echte KI-Objekterkennung in Aktion |
| ⚡ **Zeitlupe-Aufnahmen** | 120fps Slow-Motion Beispiele |
| 🎥 **4K Aufnahmen** | Hochauflösende Vogelhaus-Videos |
| 🎵 **Audio-Aufnahmen** | Synchrone Vogel-Audio Beispiele |

> 💡 **Hinweis:** Tutorial-Videos sind in Planung - aktuell zeigen wir echte Aufnahmen unserer Vogel-Kamera!

## ✨ Features

- 🎥 **Hochauflösende Videoaufnahme** (bis zu 4K)
- 🎵 **Synchrone Audioaufnahme** über USB-Mikrofon
- 🤖 **KI-Objekterkennung** mit YOLOv8 und eigenen Vogelarten-Modellen
- 🌐 **Remote-Steuerung** über SSH
- 📁 **Automatische Dateiorganisation** nach Jahr/Woche
- ⚙️ **Flexible Konfiguration** über .env-Dateien
- 📊 **Fortschrittsanzeige** während der Aufnahme
- 🔄 **Automatische Video-/Audio-Synchronisation**
- 📱 **YouTube-Integration** mit QR-Codes für mobile Nutzer
- 🔧 **Einfache Installation** mit config/requirements.txt
- ✅ **Automatische Konfigurationsvalidierung**
- 🎯 **Eigene AI-Modelle** trainierbar für spezifische Vogelarten

## 📸 Hardware-Galerie

**Modulare Kamera-Lösung:**
![Einzelnes Vogelhaus](assets/vogelhaus-kamera-solo.png)
*Flexible Platzierung für optimale Aufnahmen*

**Live-Aufnahmen & Community:**
![YouTube Kanal Impression](assets/Youtube-Kanal.png) 
*Echte Vogelbeobachtungen auf YouTube*

> 💡 **3D-Konstruktions-Dateien verfügbar!** Alle CAD-Dateien für den Nachbau finden Sie im [`3d-konstruktion/`](3d-konstruktion/) Verzeichnis

## 🤖 KI-Objekterkennung & Vogelarten-AI

### Sofort verfügbar: Standard-Objekterkennung
```bash
# YOLOv8 mit allgemeiner Vogelerkennung
python3 ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model yolov8
```

### Erweitert: Eigene Vogelarten-Modelle trainieren
Das System unterstützt das Training eigener AI-Modelle für spezifische Vogelarten:

🎯 **Häufige deutsche Gartenvögel**: Amsel, Blaumeise, Kohlmeise, Rotkehlchen, Buchfink...

📋 **Vollständige Anleitung**: [`docs/ANLEITUNG-EIGENES-AI-MODELL.md`](docs/ANLEITUNG-EIGENES-AI-MODELL.md)

🛠️ **Training-Tools**: [`ai-training-tools/`](ai-training-tools/) - Komplettes Toolkit für eigene Modelle

```bash
# Eigenes Modell verwenden
python3 ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model custom \
  --ai-model-path /pfad/zu/eigenem/modell.json
```

## 🛠️ Voraussetzungen

### Hardware
- Raspberry Pi 5 mit Kamera-Modul
- USB-Mikrofon für Audioaufnahme
- Stabile Netzwerkverbindung

### Software
- Python 3.8+
- SSH-Zugang zum Raspberry Pi
- libcamera/rpicam-vid auf dem Raspberry Pi

### Python-Abhängigkeiten

**Empfohlen: Virtuelle Umgebung verwenden**
```bash

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r config/requirements.txt
```

**Oder manuell:**
```bash
pip install paramiko scp tqdm python-dotenv qrcode[pil]
```

> 💡 **Hinweis:** Die Verwendung einer virtuellen Umgebung (`venv`) wird empfohlen, um Konflikte mit anderen Python-Projekten zu vermeiden.

### Konfiguration laden
Die Skripte laden automatisch Konfigurationsdaten aus der `.env`-Datei:
```bash
# 1. Kopieren Sie die Beispiel-Konfiguration
cp python-skripte/.env.example python-skripte/.env

# 2. Bearbeiten Sie die .env-Datei mit Ihren Daten  
nano python-skripte/.env

# 3. Testen Sie die Konfiguration
python python-skripte/config.py
```

## 📂 Projektstruktur

```
vogel-kamera-linux/
├── README.md                                                     # Hauptdokumentation
├── LICENSE                                                       # MIT Lizenz
├── RELEASE_NOTES_v1.1.7.md                                      # Aktuelle Release-Dokumentation
├── .gitignore                                                    # Git-Ignore-Regeln
├── config/                                                       # 🔧 Konfigurationsdateien
│   └── requirements.txt                                          # Python-Abhängigkeiten
├── scripts/                                                      # 🔧 Build/Deploy-Skripte  
│   ├── version.py                                               # Zentrale Versionsverwaltung
│   ├── release_workflow.py                                     # Release-Automatisierung
│   └── update_version.py                                       # Versions-Update-Skript
├── docs/                                                         # 📚 Dokumentation
│   ├── CHANGELOG.md                                             # Versionshistorie
│   ├── SECURITY.md                                              # Sicherheitsrichtlinien
│   ├── AI-MODELLE-VOGELARTEN.md                                 # AI-Modell-Dokumentation
│   └── ANLEITUNG-EIGENES-AI-MODELL.md                          # AI-Training-Anleitung
├── tools/                                                        # 🛠️ Test & Entwicklungstools
│   ├── automation_test.txt                                      # Automatisierungs-Tests
│   └── test_ai_features.py                                      # AI-Feature Tests
├── releases/                                                     # 📋 Release-Dokumentation
│   ├── README.md                                                # Release-Übersicht
│   └── vX.X.X/                                                  # Versionierte Release-Archive
│       └── RELEASE_NOTES_vX.X.X.md                              # Archivierte Release-Notes
├── assets/                                                       # 📸 QR-Codes & Medien
│   ├── qr-youtube-channel.png                                   # YouTube-Kanal QR-Code
│   ├── qr-playlists.png                                         # Playlists QR-Code  
│   ├── qr-subscribe.png                                         # Abonnieren QR-Code
│   ├── generate_qr_codes.py                                     # QR-Code Generator
│   └── QR-CODE-ANLEITUNG.md                                     # QR-Code Dokumentation
├── git-automation/                                              # 🔐 Git-Automatisierung
│   ├── git_automation.py                                        # Sichere Git-Operationen mit AES-256
│   ├── setup_ssh_credentials.py                                 # SSH-Credentials Setup
│   ├── test_*.py                                                # Umfassende Test-Suite
│   ├── .git_secrets_encrypted.json                             # Verschlüsselte SSH-Secrets
│   └── README.md                                                # Git-Automation Dokumentation
├── wiki-sync/                                                   # 📚 Wiki-Synchronisation
│   ├── wiki_sync.py                                            # Automatische Wiki-GitHub-Sync
│   └── README.md                                                # Wiki-Sync Dokumentation
├── 3d-konstruktion/                                            # 🔧 3D-Konstruktions-Dateien
│   ├── README.md                                                # 3D-Konstruktions-Dokumentation
│   └── YYYY-MM-DD/                                             # Versionierte Konstruktions-Ordner
│       ├── README.md                                            # Version-spezifische Dokumentation
│       └── stp-dateien/                                        # STEP-Konstruktionsdateien (*.stp)
│           └── *.stp                                           # 3D-CAD Dateien für Hardware
├── veranstaltungen/                                             # 🎤 Event-Management
│   ├── README.md                                                # Event-Übersicht
│   └── YYYY-MM-DD-eventname/                                   # Event-spezifische Ordner
│       ├── README.md                                            # Event-Details
│       ├── slides/                                              # Präsentationsmaterialien
│       │   ├── README.md                                        # Slide-Dokumentation
│       │   └── *.pdf/*.pptx                                    # Präsentationsdateien
│       └── resources/                                           # Event-Ressourcen
│           ├── README.md                                        # Resource-Dokumentation
│           ├── generate_qr_codes.py                            # Event-QR-Codes
│           └── *.png                                           # QR-Code Bilder
└── python-skripte/                                             # 🐍 Haupt-Python-Module
    ├── config.py                                                # Konfigurationssystem
    ├── __version__.py                                           # Modul-Versionsverwaltung
    ├── .env.example                                             # Konfigurationsvorlage
    ├── .env                                                     # Lokale Konfiguration (nicht im Git)
    ├── ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py  # 🤖 Hauptskript mit KI
    ├── ai-had-audio-remote-param-vogel-libcamera-single.py            # 🎵 Audio-Aufnahme
    └── ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py         # ⚡ Zeitlupe-Aufnahmen
```

## 🚀 Schnellstart

### 1. Installation
```bash
# Repository klonen
git clone https://github.com/roimme65/vogel-kamera-linux.git
cd vogel-kamera-linux

# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r config/requirements.txt
```

### 2. Konfiguration
```bash
# Konfiguration kopieren und anpassen
cp python-skripte/.env.example python-skripte/.env
nano python-skripte/.env

# Konfiguration testen
python python-skripte/config.py
```

### 3. Erste Aufnahme
```bash
# Audio-Test (1 Minute)
python python-skripte/ai-had-audio-remote-param-vogel-libcamera-single.py --duration 1

# Video mit KI (1 Minute, HD)
python python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py --duration 1 --width 1920 --height 1080 --ai-modul on
```

### 4. Version prüfen
```bash
python python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py --version
# Ausgabe: Vogel-Kamera-Linux v1.1.7
```

### Basis-Aufnahme (ohne KI)
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 \
    --width 1920 \
    --height 1080
```

### Mit KI-Objekterkennung
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 \
    --width 1920 \
    --height 1080 \
    --ai-modul on
```

### Erweiterte Konfiguration
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 10 \
    --width 4096 \
    --height 2160 \
    --codec h264 \
    --autofocus_mode continuous \
    --rotation 180 \
    --fps 30 \
    --cam 0 \
    --ai-modul on
```

### Parameter-Übersicht

| Parameter | Beschreibung | Standard | Optionen |
|-----------|--------------|----------|----------|
| `--duration` | Aufnahmedauer in Minuten | **erforderlich** | 1-∞ |
| `--width` | Video-Breite | 4096 | 640-4096 |
| `--height` | Video-Höhe | 2160 | 480-2160 |
| `--codec` | Video-Codec | h264 | h264, h265 |
| `--autofocus_mode` | Autofokus-Modus | continuous | continuous, manual |
| `--autofocus_range` | Autofokus-Bereich | macro | macro, full |
| `--hdr` | HDR-Modus | off | auto, off |
| `--rotation` | Bildrotation | 180 | 0, 90, 180, 270 |
| `--fps` | Bildrate | 15 | 1-60 |
| `--cam` | Kamera-ID | 0 | 0, 1 |
| `--ai-modul` | KI-Objekterkennung | off | on, off |
| `--roi` | Region of Interest | - | x,y,w,h |

## 🔐 Git-Automatisierung

Das Projekt bietet jetzt eine **sichere Git-Automatisierung** für entwickelnde Beitragende:

### ✨ Features
- **🔑 Verschlüsselte SSH-Credentials:** AES-256-CBC mit Master-Password
- **🚀 Automatischer SSH-Agent:** Keine manuelle Passphrase-Eingabe
- **🛡️ Sichere Speicherung:** PBKDF2 Key-Derivation mit 100.000 Iterationen
- **🧪 Umfassende Tests:** Automatisierte Validierung aller Komponenten

### 🚀 Schnellstart Git-Automation
```bash
cd git-automation/

# Abhängigkeiten installieren
pip install -r git_automation_requirements.txt

# SSH-Credentials einrichten (einmalig)
python3 setup_ssh_credentials.py

# System testen
python3 test_full_automation.py
```

### 💻 Verwendung
```python
import sys
sys.path.append('git-automation/')
from git_automation import SecureGitAutomation

# Automatisierte Git-Operationen
automation = SecureGitAutomation()
automation.run_command("git add .")
automation.run_command('git commit -m "Automatischer Commit"')
automation.run_command("git push")
```

> 📚 **Vollständige Dokumentation:** [`git-automation/README.md`](git-automation/README.md)

## ⚙️ SSH-Konfiguration

### 1. Umgebungsvariablen konfigurieren
```bash
# Kopieren Sie die Beispiel-Konfiguration
cp python-skripte/.env.example python-skripte/.env

# Bearbeiten Sie die .env-Datei mit Ihren Daten
nano python-skripte/.env
```

Beispiel `.env`-Datei:
```bash
RPI_HOSTNAME=your-raspberry-pi-hostname
RPI_USERNAME=pi
SSH_KEY_PATH=~/.ssh/id_rsa_rpi
BASE_VIDEO_PATH=~/Videos/Vogelhaus
REMOTE_VIDEO_PATH=/home/pi/Videos/Vogelhaus
REMOTE_AUDIO_PATH=/home/pi/Audio/Kamerawagen
```

> 📺 **Beispielaufnahmen:** [Vogel-Kamera Setup](https://www.youtube.com/@vogel-kamera-linux) - Siehe die Kamera in Aktion

### 2. **SSH-Schlüssel generieren** (falls noch nicht vorhanden):
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_rpi
```

### 3. **Öffentlichen Schlüssel auf Raspberry Pi kopieren**:
```bash
ssh-copy-id -i ~/.ssh/id_rsa_rpi.pub pi@your-raspberry-pi-hostname
```

### 4. **Hostname in /etc/hosts eintragen** (optional):
```bash
echo "192.168.1.XXX your-raspberry-pi-hostname" | sudo tee -a /etc/hosts
```

## 📁 Dateiorganisation

Die aufgenommenen Videos werden automatisch organisiert:
```
~/Videos/Vogelhaus/
├── AI-HAD/        # Hauptskript mit KI-Erkennung
├── Audio/         # Reine Audio-Aufnahmen  
└── Zeitlupe/      # Slow-Motion Videos
    └── 2025/
        └── 38/  # Kalenderwoche
            └── Montag__2025-09-23__14-30-15/
                └── Montag__2025-09-23__14-30-15__4096x2160.mp4
```

## 🤖 KI-Objekterkennung

Das Hauptskript nutzt YOLOv8 für die Echtzeit-Objekterkennung:
- **Automatische Vogelerkennung** während der Aufnahme
- **Optimierte Inferenz** auf Raspberry Pi 5
- **Konfigurierbare Erkennungsparameter**

## 🔧 Problembehandlung

### Konfigurationsprobleme
```bash
# Konfiguration überprüfen
python python-skripte/config.py

# Fehlermeldung: "Hostname nicht konfiguriert"
# → Bearbeiten Sie python-skripte/.env mit Ihren Werten
```

### Audio-Gerät nicht gefunden
```bash
# Auf dem Raspberry Pi prüfen:
arecord -l
```

### SSH-Verbindungsprobleme
```bash
# Verbindung testen:
ssh -i ~/.ssh/id_rsa_rpi pi@your-raspberry-pi-hostname

# Konfiguration validieren:
python python-skripte/config.py

# .env-Datei überprüfen:
cat python-skripte/.env
```

### Dependency-Probleme
```bash
# Alle Abhängigkeiten neu installieren
pip install -r config/requirements.txt

# Einzelne Pakete installieren  
pip install paramiko scp tqdm python-dotenv qrcode[pil]
```

### Kamera-Probleme
```bash
# Kamera-Status prüfen:
rpicam-hello --list-cameras
```

## 📄 Lizenz

Siehe [LICENSE](LICENSE) Datei für Details.

## 🤝 Beitragen

1. Fork des Repositories
2. Feature-Branch erstellen
3. Änderungen commiten
4. Pull Request erstellen

## 👥 Community & Diskussionen

[![GitHub Discussions](https://img.shields.io/github/discussions/roimme65/vogel-kamera-linux)](https://github.com/roimme65/vogel-kamera-linux/discussions)

Tauschen Sie sich mit anderen Nutzern aus:
- 🙋 **Fragen stellen** zu Installation und Konfiguration  
- 💡 **Ideen teilen** für neue Features
- 📸 **Aufnahmen zeigen** aus Ihrem Vogelhaus
- 🔧 **Hardware-Tipps** diskutieren

## 📞 Support

Bei Fragen oder Problemen:
- 💬 **Diskussionen starten** in [GitHub Discussions](https://github.com/roimme65/vogel-kamera-linux/discussions)
- 🐛 **Bugs melden** über [GitHub Issues](https://github.com/roimme65/vogel-kamera-linux/issues)

## 📋 Changelog

Alle Änderungen werden in [docs/CHANGELOG.md](docs/CHANGELOG.md) dokumentiert.

### 🆕 Neu in v1.1.2 (23. September 2025)
- 🔧 **GitHub Issue Templates:** Deutsche Bug Report und Feature Request Templates
- 🏗️ **Repository-Verbesserungen:** Hardware-spezifische Support-Abschnitte
- 🤝 **Community-Engagement:** Strukturierte Nutzen-Bewertung und Akzeptanzkriterien
- 🛡️ **Security Policy:** Comprehensive SECURITY.md mit Vulnerability-Reporting
- 📊 **Version-Tracking:** Programmatische Versionsinformationen (version.py)
- 📋 **Release-Dokumentation:** Vollständige Release Notes und CHANGELOG-Updates

### 🎬 Neu in v1.1.0
- YouTube-Integration mit QR-Codes
- Zentrales Konfigurationssystem  
- Sicherheitsverbesserungen (keine hardcodierten Daten)

## 🔖 Versionen

- **Aktuelle Version:** v1.1.7
- **Entwicklungszweig:** `devel`
- **Stabile Releases:** [GitHub Releases](../../releases) | [Tags](../../tags)
