# 🐦 Vogel-Kamera-Linux

> 🌐 **Multi-Language Documentation:** This README is available in multiple languages!  

![Vogel-Kamera-Linux Banner](docs/pictures/Vogelhaus-Raspberry-Pi-Backround.jpg)

## Release v2.1.0 — Audio/Video-Synchronisation & Professionelle Aufnahmen

- **Version:** v2.1.0 (März 2026)
- **🎙️ Highlights:** 
  - **Audio/Video-Synchronisation** mit Thread-basierter Parallel-Aufnahme
  - **USB-Audio-Stick** Integration (arecord, hw:0,0 Auto-Detection)
  - **rpicam-vid statt libcamera** für bessere Codec-Kontrolle
  - **Perfekte MP4-Merge** mit ffmpeg `-fflags +genpts`
  - **Rotation 180°** Default (Vogelbild oben)
  - **Cinema 4K** (4096x2160 @ 30fps)
  - **Manual Recording** ohne AI für direkte Aufnahmen
- **Wichtige Features:**
  - ✅ Beide Streams (Video + Audio) exakt synchron
  - ✅ Automatische USB-Audio-Erkennung
  - ✅ Alle rpicam-vid Parameter konfigurierbar
  - ✅ Slow-Motion Support (60fps)
  - ✅ rsync Auto-Transfer zum Client

**Vollständige Release-Notes:** [`releases/v2.1.0/RELEASE_NOTES_v2.1.0.md`](releases/v2.1.0/RELEASE_NOTES_v2.1.0.md)  
**Audio-Integration Changelog:** [`AUDIO-FIX-CHANGELOG.md`](AUDIO-FIX-CHANGELOG.md)

[![Version](https://img.shields.io/badge/Version-v2.1.0-brightgreen)](https://github.com/kamera-linux/vogel-kamera-linux/releases/tag/v2.1.0)
[![Audio Integration](https://img.shields.io/badge/Feature-Audio%20%2B%20Video%20Sync-informational)]()
[![Trixie Support](https://img.shields.io/badge/Debian-Trixie%20(13)-informational)](docs/TRIXIE-MIGRATION.md)
[![License](https://img.shields.io/github/license/kamera-linux/vogel-kamera-linux)](LICENSE)

> ⚠️ **Raspberry Pi OS Trixie (Debian 13):** Diese Version ist für **Trixie** optimiert.  
> 📘 **Für Bookworm (Debian 12):** Verwenden Sie den [bookworm-legacy-Branch (v1.2.x)](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)  
> 📖 **Migration-Guide:** [TRIXIE-MIGRATION.md](docs/TRIXIE-MIGRATION.md)

![Komplettes Vogel-Kamera System](assets/vogelhaus-kamera-komplett.png)

**🐦 Professionelles Vogel-Beobachtungssystem mit KI-gestützter Objekterkennung**

`vogel-kamera-linux` ist ein **Open-Source-Projekt** zur ferngesteuerten Überwachung von Vogelhäusern mittels Raspberry Pi 5 Kamera. Das System kombiniert hochauflösende Video-/Audio-Aufnahmen mit **YOLO26n KI-Erkennung** für automatische Vogelerkennung und -aufzeichnung.

### 🚀 Quickstart
```bash
# 🎯 EMPFOHLEN: Unified Monitor Client (vom lokalen PC)
cd unified-monitor-client
python3 unified_monitor_client.py 4k      # Cinema 4K mit Audio
python3 unified_monitor_client.py normal  # Standard HD
python3 unified_monitor_client.py slowmo  # Zeitlupe 120fps
```

> 📺 **Live-Demo:** [YouTube-Kanal](https://www.youtube.com/@vogel-kamera-linux) - Echte Aufnahmen vom vogel-kamera-linux System!

## 📖 Überblick

**vogel-kamera-linux** ist ein vollständiges Remote-Kamera-System für Naturbeobachtung, entwickelt für **Raspberry Pi 5** mit Python 3.13+. Das Projekt kombiniert moderne Kamera-Hardware (IMX708) mit spezialisierter KI-Objekterkennung (YOLO26n) für automatische Vogelerkennung.

**🎯 Hauptanwendung:** Ferngesteuerte Vogelhaus-Überwachung mit automatischer Aufnahme bei Vogel-Erkennung, inklusive HD-Video (bis 4K), Zeitlupe (120fps) und synchroner Audio-Aufzeichnung über USB-Mikrofon.

### 📺 Live-Beispiele & YouTube-Kanal

[![YouTube Channel](https://img.shields.io/badge/📺_YouTube_Kanal-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@vogel-kamera-linux)

**Echte Aufnahmen vom vogel-kamera-linux System** - Live-Vogelerkennung, Zeitlupen-Aufnahmen, 4K-Videos!

<!-- YOUTUBE_VIDEOS_START -->
**📺 Aktuelle Videos:**

| 🎬 Video | 📅 Datum | ⏱️ Dauer | 👁️ Views | 👍 Likes | 💬 Komm. |
|----------|----------|----------|----------|----------|---------|
| [**🐦 Vogel-Beobachtung von einem Star am Futterhaus**](https://www.youtube.com/watch?v=0bNoF5cutnc) | 06.03.2026 | 2:33 | 21 | 1 | 0 |
| [**🐦 Vogel-Beobachtung mit KI: Meisen, Rotkehlchen un...**](https://www.youtube.com/watch?v=1Mrq4oIzckI) | 30.11.2025 | 2:38 | 156 | 1 | 2 |
| [**3 Vogelarten live am Futterhaus - KI erkennt Kohlm...**](https://www.youtube.com/watch?v=uZm4Ao9JHoo) | 24.11.2025 | 3:10 | 164 | 5 | 1 |
| [**🐦 Wunderschönes Rotkehlchen beim Fressen \| 4K Voge...**](https://www.youtube.com/watch?v=rWkWFUeVK0o) | 31.10.2025 | 1:58 | 58 | 5 | 0 |
| [**🐦 Blaumeise beim Fressen \| KI-Kamera 120fps Zeitlu...**](https://www.youtube.com/watch?v=ew3l12TSn5k) | 28.10.2025 | 2:25 | 95 | 8 | 0 |
| [**🐦 Sumpfmeise in Zeitlupe \| Futtersuche im Vogelhau...**](https://www.youtube.com/watch?v=dORu9qs8KSA) | 20.10.2025 | 2:46 | 51 | 6 | 1 |
| [**5 Vogelarten mit Aufnahme (120fps) \| Automatische ...**](https://www.youtube.com/watch?v=k3tS0oJX7YE) | 06.10.2025 | 3:24 | 66 | 6 | 5 |
| [**🤖 KI-gesteuerte Vogelkamera \| Automatische Erkennu...**](https://www.youtube.com/watch?v=5WeZb_YVe0s) | 02.10.2025 | 5:51 | 108 | 6 | 1 |
| [**Vogelhaus mit Kleiber  (Futtersuche in Zeitlupe)**](https://www.youtube.com/watch?v=QALijFTA_s8) | 29.09.2025 | 5:07 | 77 | 7 | 2 |
| [**Vogelhaus mit junge Haussperlinge**](https://www.youtube.com/watch?v=3na90KiJ-J8) | 06.06.2025 | 3:11 | 58 | 6 | 0 |
| [**Vogelhaus mit Kohlmeise  (Am Futterspender in Zeit...**](https://www.youtube.com/watch?v=kFXR03Lv0X0) | 30.05.2025 | 7:23 | 41 | 6 | 0 |
| [**Vogelhaus mit Kohlmeisen  (Fütterung Jungtiere mit...**](https://www.youtube.com/watch?v=sqvd99Pbubc) | 18.05.2025 | 3:22 | 53 | 6 | 1 |
| [**Vogelhaus mit Kohlmeise  (Fütterung Jungtier mit 2...**](https://www.youtube.com/watch?v=vXWDleJ-18Q) | 17.05.2025 | 2:44 | 21 | 6 | 0 |
| [**Vogelhaus mit Kernbeißer (2 Kameras)**](https://www.youtube.com/watch?v=dvCXPdMdNCg) | 27.04.2025 | 2:12 | 86 | 8 | 2 |
| [**Vogelhaus mit Kernbeißer und Blaumeise (Vogel-Paar...**](https://www.youtube.com/watch?v=61Szkcp9hcM) | 23.04.2025 | 2:59 | 57 | 6 | 2 |
| [**Vogelhaus mit Blaumeise, Kernbeißer und Kohlmeise ...**](https://www.youtube.com/watch?v=kElfd64dWrY) | 21.04.2025 | 4:16 | 110 | 7 | 0 |
| [**Vogelhaus mit Blaumeise, Haussperling und Kohlmeis...**](https://www.youtube.com/watch?v=hjrYji0A9Hs) | 18.04.2025 | 3:04 | 68 | 6 | 0 |
| [**Vogelhaus mit Blaumeise und Kohlmeise (Zeitlupe)**](https://www.youtube.com/watch?v=lshb68RrF_A) | 13.04.2025 | 5:11 | 79 | 7 | 0 |
| [**Vogelhaus mit Blaumeisen, Rotkehlchen, Kernbeißer ...**](https://www.youtube.com/watch?v=6-OFxA__GL8) | 10.04.2025 | 5:06 | 113 | 7 | 0 |
| [**Vogelhaus mit Kernbeißer, Blaumeise, Rotkehlchen, ...**](https://www.youtube.com/watch?v=MKb3yUKS_ww) | 09.04.2025 | 4:28 | 87 | 7 | 0 |

*Automatisch aktualisiert: 08.03.2026 07:07 Uhr (Winterzeit (MEZ))*
<!-- YOUTUBE_VIDEOS_END -->

## ✨ Features

- 🎥 **Hochauflösende Videoaufnahme** (bis zu 4K)
- 🎵 **Synchrone Audioaufnahme** über USB-Mikrofon
- 🤖 **KI-Objekterkennung** mit YOLO26n spezialisiert auf deutsche Vogelarten
- 🎯 **Auto-Trigger System** mit automatischer Vogelerkennung *(Neu in v1.2.0)*
- 📺 **Preview-Stream** (RTSP) für Live-Überwachung *(Neu in v1.2.0)*
- 🌐 **Netzwerk-Diagnostics** für Performance-Analyse *(Neu in v1.2.0)*
- 📊 **System-Monitoring** mit CPU-Load und Temperaturüberwachung *(Seit v1.1.9)*
- ⚡ **Performance-Optimierung** für verschiedene Aufnahmemodi *(Seit v1.1.9)*
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

## 🤖 KI-Objekterkennung mit YOLO26

### Standard: YOLO26n Vogelarten-Erkennung
```bash
# Automatische Integration in unified-monitor-client:
cd unified-monitor-client
python3 unified_monitor_client.py 4k
```

**YOLO26n Features:**
- ✅ Spezialisiert auf deutsche Vogelarten
- ✅ Hohe Genauigkeit (>90% für häufige Arten)
- ✅ Optimiert für Raspberry Pi 5
- ✅ Automatische Modellerstellung
- ✅ Fokus nur auf Vogel-Klasse (COCO 14)
- ⚡ Temporaler Filter für stabile Erkennungen

### Erweitert: Eigene Vogelarten-Modelle trainieren
Das System unterstützt das Training eigener AI-Modelle für spezifische Vogelarten:

🎯 **Häufige deutsche Gartenvögel**: Amsel, Blaumeise, Kohlmeise, Rotkehlchen, Buchfink...

#### 🚀 Erweiterte KI-Training (Optional)

Für spezialisierte Vogelarten-Modelle:
- 📦 **vogel-model-trainer:** [PyPI](https://pypi.org/project/vogel-model-trainer/) - Professionelles Training-Tool
- 📋 **Anleitung:** [`docs/ANLEITUNG-EIGENES-AI-MODELL.md`](docs/ANLEITUNG-EIGENES-AI-MODELL.md)

#### 🤖 **Vortrainierte Vogelarten-Modelle**

**Empfohlene Hugging Face Modelle für deutsche Vogelarten:**

🔗 **[kamera-linux/german-bird-classifier-v2](https://huggingface.co/kamera-linux/german-bird-classifier-v2)** ⭐ **Empfohlen**
- Neueste Version mit verbesserter Genauigkeit
- Trainiert auf 8 häufigen deutschen Vogelarten
- Optimiert für Vogelfütterungen

🔗 **[kamera-linux/german-bird-classifier](https://huggingface.co/kamera-linux/german-bird-classifier)** (v1, Legacy)
- Erste Version des Modells
- Weiterhin funktional, aber v2 wird empfohlen

```bash
# Verwendung mit vogel-model-trainer
vogel-trainer classify --species-model kamera-linux/german-bird-classifier-v2 ~/images/

# Verwendung mit vogel-video-analyzer
pip install vogel-video-analyzer
vogel-analyze --identify-species --species-model kamera-linux/german-bird-classifier-v2 video.mp4
```

Mehr Informationen: [`docs/AI-MODELLE-VOGELARTEN.md`](docs/AI-MODELLE-VOGELARTEN.md)

#### 📋 **Alternative: Lokale Training-Tools (Legacy)**

📋 **Manuelle Anleitung**: [`docs/ANLEITUNG-EIGENES-AI-MODELL.md`](docs/ANLEITUNG-EIGENES-AI-MODELL.md)

🛠️ **Basis-Tools**: [`ai-training-tools/`](ai-training-tools/) - Legacy Training-Scripts für fortgeschrittene Nutzer

#### 🎯 **Eigenes Modell verwenden**

```bash
# Eigenes Modell verwenden
python3 ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model custom \
  --ai-model-path /pfad/zu/eigenem/modell.json
```

## 🛠️ Voraussetzungen

### Hardware
- Raspberry Pi 5 mit Kamera-Modul (IMX708 Wide empfohlen)
- USB-Mikrofon für Audioaufnahme
- Stabile Netzwerkverbindung (Gigabit LAN empfohlen)

### Software
- **Raspberry Pi OS Trixie (Debian 13)** - ERFORDERLICH
- **Python 3.13+** auf beiden Systemen
- **rpicam-apps v1.9.1+**, **FFmpeg 7.1.2+**, **ALSA** (Raspberry Pi)
- **SSH-Zugang** konfiguriert

### Client-PC Setup
```bash
# 1. Virtuelle Umgebung
python3 -m venv venv
source venv/bin/activate  # Linux/macOS oder venv\Scripts\activate (Windows)

# 2. Dependencies
pip install -r config/requirements.txt

# 3. Konfiguration (Hostname, User, SSH-Key)
cd unified-monitor-client
python3 setup_environment.py
```

## 📂 Projektstruktur

```
vogel-kamera-linux/
├── README.md                                                     # Hauptdokumentation
├── LICENSE                                                       # MIT Lizenz
├── .gitignore                                                    # Git-Ignore-Regeln
├── config/                                                       # 🔧 Konfigurationsdateien
│   └── requirements.txt                                          # Python-Abhängigkeiten
├── scripts/                                                      # 🔧 Build/Deploy-Skripte  
│   ├── version.py                                               # Zentrale Versionsverwaltung
│   ├── release_workflow.py                                     # Release-Automatisierung
│   └── update_version.py                                       # Versions-Update-Skript
├── docs/                                                         # 📚 Dokumentation
│   ├── CHANGELOG.md                                             # Versionshistorie (v2.0.2)
│   ├── ARCHITEKTUR.md                                           # 🏗️ Systemarchitektur mit Mermaid-Diagrammen *(v1.2.0)*
│   ├── PROJEKT-REORGANISATION.md                                # Projekt-Reorganisations-Dokumentation
│   ├── TRIXIE-MIGRATION.md                                      # Trixie Migration Guide
│   ├── SECURITY.md                                              # Sicherheitsrichtlinien
│   ├── DOKUMENTATION-UEBERSICHT.md                              # Dokumentations-Index
│   ├── AI-MODELLE-VOGELARTEN.md                                 # AI-Modell-Dokumentation
│   ├── ANLEITUNG-EIGENES-AI-MODELL.md                          # AI-Training-Anleitung
│   ├── i18n/                                                    # 🌐 Multilingual Documentation *(v2.0)*
│   │   ├── README.md                                            # 🇬🇧 English Documentation
│   │   ├── README.de.md                                         # 🇩🇪 Deutsche Dokumentation
│   │   └── README.ja.md                                         # 🇯🇵 日本語ドキュメント
│   └── legacy/                                                  # 📦 Archivierte Dokumente *(v2.0)*
│       ├── README.md                                            # Legacy-Docs Migration Guide
│       ├── AUTO-TRIGGER-PERFORMANCE-OPTIMIZATION.md             # Obsolet (in README integriert)
│       ├── AUTO-TRIGGER-STREAM-RESTART.md                       # Obsolet (Unified System)
│       ├── FIX-API-KEY-ZUGRIFF.md                               # Obsolet
│       ├── FIX-PREVIEW-STREAM-RESTART.md                        # Obsolet
│       ├── PARAMETER-NO-STREAM-RESTART.md                       # Obsolet
│       ├── README-IMPROVEMENTS.md                               # Obsolet (implementiert)
│       ├── SYSTEM-READY.md                                      # Obsolet
│       ├── UNIFIED-MONITORING-SYSTEM.md                         # In README integriert
│       └── INSTALLATION-TRIXIE.md                               # In TRIXIE-MIGRATION.md
├── python-toolbox/                                             # 🐍 Python Packages & Tools *(v1.3.2)*
│   ├── vogel-video-analyzer/                                   # Video-Analyse-Tool (Git Submodule)
│   ├── requirements.txt                                         # Python-Dependencies
│   └── README.md                                                # Python-Toolbox Dokumentation
├── tools/                                                        # 🛠️ Test & Entwicklungstools
│   ├── check_emojis.py                                          # Emoji-Validator für Markdown
│   ├── automation_test.txt                                      # Automatisierungs-Tests
│   ├── test_ai_features.py                                      # AI-Feature Tests
│   └── README.md                                                # Tools-Dokumentation
├── auto-start-kamera/                                           # 🚀 Auto-Start Skripte *(v2.0)*
│   ├── start-unified-monitoring.sh                              # Remote-Wrapper für Unified Monitor
│   ├── remote-unified-control.sh                                # Remote Control Tool
│   └── README.md                                                # Auto-Start Dokumentation
├── raspberry-pi-scripts/                                        # 🍓 Raspberry Pi Skripte *(v2.0)*
│   ├── unified-camera-monitor.py                                # ⭐ HAUPT-SYSTEM: Vereinheitlichter Kamera-Monitor
│   ├── UNIFIED-MONITOR-README.md                                # Unified Monitor Dokumentation
│   └── requirements-pi.txt                                      # Python-Dependencies für Raspberry Pi
├── releases/                                                     # 📋 Release-Dokumentation
│   ├── README.md                                                # Release-Übersicht
│   └── vX.X.X/                                                  # Versionierte Release-Archive
│       └── RELEASE_NOTES_vX.X.X.md                              # Archivierte Release-Notes (v2.0.2, v2.0.1, v2.0.0, ...)
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
├── legacy/                                                      # 📦 Archivierte Skripte & Docs *(v2.0)*
│   ├── README.md                                                # Legacy Migration Guide
│   ├── kamera-auto-trigger/                                     # 🎯 Altes Auto-Trigger System (v1.2.0)
│   │   ├── start-vogel-beobachtung.sh                          # Interaktiver Wrapper (obsolet)
│   │   ├── scripts/ai-had-kamera-auto-trigger.py               # Auto-Trigger mit Legacy-Skripten (obsolet)
│   │   ├── docs/                                                # Auto-Trigger Dokumentation
│   │   └── README.md                                            # Auto-Trigger Dokumentation
│   ├── network-tools/                                           # 🌐 Netzwerk-Diagnose (v1.2.0, obsolet)
│   │   ├── test-network-quality.py                             # TCP-Stream-Diagnostik (obsolet)
│   │   └── README.md                                            # Network-Tools Dokumentation
│   ├── raspberry-pi-scripts/                                    # 🍓 Alte Stream-Skripte (v1.2.0, obsolet)
│   │   ├── start-preview-stream.sh                             # Preview-Stream (obsolet)
│   │   ├── start-preview-stream-v2.sh                          # Preview-Stream v2 (obsolet)
│   │   ├── start-preview-stream-watchdog.sh                    # Stream-Watchdog (obsolet)
│   │   ├── start-rtsp-stream.sh                                # RTSP-Stream (obsolet)
│   │   ├── start-tcp-preview-stream.sh                         # TCP-Stream (obsolet)
│   │   ├── start-tcp-preview-watchdog.sh                       # TCP-Watchdog (obsolet)
│   │   └── audio-monitor.sh                                     # Audio-Monitor (obsolet)
│   ├── ai-had-audio-remote-param-vogel-libcamera-single.py     # Audio-Aufnahme (veraltet)
│   ├── ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py  # Video+AI (veraltet)
│   ├── ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py  # Zeitlupe (veraltet)
│   ├── config.py                                                # Config-System (veraltet)
│   └── .env.example                                             # Env-Template (veraltet)
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
    ├── __version__.py                                           # Modul-Versionsverwaltung
    ├── check_ai_models.py                                       # 🔍 AI-Modell-Validierung
    ├── quick_system_check.py                                    # ⚡ Schnelle System-Checks *(v1.1.9)*
    ├── remote_system_monitor.py                                 # 📊 Umfassendes System-Monitoring *(v1.1.9)*
    └── .env                                                     # Lokale Konfiguration (nicht im Git)
```

## 🚀 Schnellstart: 3 Schritte

### 1️⃣ Repository klonen & Setup
```bash
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
python3 -m venv venv && source venv/bin/activate
pip install -r config/requirements.txt
```

### 2️⃣ Unified Monitor Client konfigurieren
```bash
cd unified-monitor-client
python3 setup_environment.py
# → Raspberry Pi Hostname, Benutzer, SSH-Key eingeben
```

### 3️⃣ Erste Aufnahme starten
```bash
# Test: 5 Sekunden
python3 unified_monitor_client.py test

# Standard: 4K Cinema mit Audio
python3 unified_monitor_client.py 4k

# Zeitlupe: 120fps
python3 unified_monitor_client.py slowmo
```


---

## 📚 Weitere Dokumentation

- **[unified-monitor-client/README.md](unified-monitor-client/README.md)** - Haupttool Dokumentation
- **[unified-monitor-client/SETUP_GUIDE.md](unified-monitor-client/SETUP_GUIDE.md)** - Detailliertes Setup
- **[CHANGELOG.md](CHANGELOG.md)** - Vollständige Versionshistorie
- **[QUICK_REFERENCE_v2.1.0.md](QUICK_REFERENCE_v2.1.0.md)** - Schnelle Befehlsreferenz
- **[raspberry-pi-scripts/UNIFIED-MONITOR-README.md](raspberry-pi-scripts/UNIFIED-MONITOR-README.md)** - Remote-System
- **[docs/TRIXIE-MIGRATION.md](docs/TRIXIE-MIGRATION.md)** - Trixie Setup-Guide
- **[docs/SECURITY.md](docs/SECURITY.md)** - Sicherheitsrichtlinien

## 📁 Dateiorganisation

Videos werden automatisch organisiert:
```
~/Videos/Vogelhaus/
├── AI-HAD/        # Hauptaufnahmen mit AI
└── Zeitlupe/      # Slow-Motion Videos
```

## 🔧 Troubleshooting

```bash
# Diagnose
cd unified-monitor-client && python3 diagnose_remote_system.py

# SSH Test
ssh -i ~/.ssh/id_rsa_rpi roimme@raspberrypi-5-ai-had

# Audio-Devices
arecord -l
```

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 🤝 Beitragen

1. Fork Repository
2. Feature-Branch erstellen  
3. Pull Request erstellen

## 📞 Support

- 💬 [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)
- 🐛 [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
- 📺 [YouTube Channel](https://www.youtube.com/@vogel-kamera-linux)

---

**Version:** v2.1.0 (März 2026) | **Status:** Produktionsreif ✅  
**Raspberry Pi 5 + Debian Trixie (13) | Audio/Video-Synchronisation | YOLO26n KI-Erkennung**
