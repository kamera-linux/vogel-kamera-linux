# 📝 Auto-Trigger System - Übersicht v1.2.0

## ✅ Vollständige Implementierung & CPU-Optimiert

Das Auto-Trigger-System mit echter AI-basierter Vogel-Erkennung ist **vollständig implementiert**, produktionsreif und in v1.2.0 massiv optimiert:

- 🎬 **Drei Aufnahme-Modi:** Standard (1920x1080@25fps), KI-Metadaten, Zeitlupe (120fps)
- ⚡ **CPU-Optimierung:** 107% → 40% CPU-Last (-63% Reduktion!)
- 🎤 **Audio in allen Modi:** 44.1kHz Mono (automatisch wenn USB-Mikrofon vorhanden)
- 🚀 **Wrapper-Skript:** Einfache Bedienung mit System-Checks
- 🏗️ **Architektur-Dokumentation:** Mit Mermaid-Diagrammen

## 📦 Neue Dateien

### Python-Skripte

1. **`python-skripte/ai-had-kamera-auto-trigger.py`** (460+ Zeilen)
   - Haupt-Skript für automatische Vogel-Erkennung
   - Integriert StreamProcessor für echte AI-Inferenz
   - Ressourcen-Monitoring und automatischer Shutdown
   - Status-Reports alle 15 Minuten (konfigurierbar)
   - Cooldown-System zwischen Aufnahmen

2. **`python-skripte/stream_processor.py`** (400+ Zeilen)
   - Klasse für Video-Stream-Verarbeitung
   - OpenCV/GStreamer Frame-Grabbing
   - YOLOv8-Integration für Echtzeit-Erkennung
   - bird-species Model-Support
   - Standalone-Test-Funktion

### Raspberry Pi Skripte

3. **`raspberry-pi-scripts/start-preview-stream.sh`** (250+ Zeilen)
   - Bash-Skript für TCP/H.264 Preview-Stream
   - Start/Stop/Status Funktionen
   - Konfigurierbare Parameter (Auflösung, FPS, Bitrate, Rotation)
   - Farbige Output-Messages
   - PID-Management für sauberes Handling

### Dokumentation

4. **`docs/AUTO-TRIGGER-DOKUMENTATION.md`**
   - Vollständige Feature-Dokumentation
   - Parameter-Übersicht
   - Workflow-Diagramm
   - Tipps & Troubleshooting
   - Optimale Einstellungen für verschiedene Szenarien

5. **`docs/PREVIEW-STREAM-SETUP.md`**
   - Detaillierte Setup-Anleitung
   - Installation von Dependencies (OpenCV, GStreamer, Ultralytics)
   - Raspberry Pi und Client-PC Konfiguration
   - Performance-Optimierung
   - Troubleshooting-Guide
   - Systemd-Service-Setup

6. **`docs/QUICKSTART-AUTO-TRIGGER.md`**
   - 5-Minuten Quick-Start
   - Checkliste
   - Schritt-für-Schritt-Anleitung
   - Häufige Probleme und Lösungen
   - Empfohlene Einstellungen

7. **`docs/AUTO-TRIGGER-OVERVIEW.md`** (diese Datei)
   - Übersicht über alle Komponenten
   - Architektur-Beschreibung
   - Verwendungs-Beispiele

### Dependencies

8. **`requirements.txt`**
   - Core-Dependencies für Basis-System
   - paramiko, scp, python-dotenv, tqdm

9. **`requirements-autotrigger.txt`**
   - Extended Dependencies für Auto-Trigger
   - opencv-contrib-python, ultralytics, numpy
   - Anleitung für System-Pakete

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     Auto-Trigger System                         │
└─────────────────────────────────────────────────────────────────┘

    Raspberry Pi 5                                 Client-PC
┌──────────────────────┐                    ┌──────────────────────┐
│                      │                    │                      │
│  📹 Camera Module 3  │                    │  🧠 StreamProcessor  │
│        ↓             │                    │        ↓             │
│  rpicam-vid          │  TCP/H.264 Stream  │  OpenCV/GStreamer    │
│  TCP-Server          │ ═════════════════> │  Frame-Grabbing      │
│  Port 8554           │   640x480 @ 5fps   │        ↓             │
│                      │                    │  YOLOv8 Inference    │
│  start-preview-      │                    │  bird-species Model  │
│  stream.sh           │                    │        ↓             │
│                      │                    │  🎯 Bird Detection?  │
│                      │                    │        ↓             │
│                      │ <═════════════════ │  ✅ Trigger!         │
│                      │  Start HD-Record   │                      │
│  🎬 HD-Aufnahme      │                    │  ai-had-kamera-      │
│  4096x2160           │                    │  auto-trigger.py     │
│  + Audio             │                    │                      │
│  ↓                   │                    │  📊 Monitoring:      │
│  💾 Video-Datei      │  SCP Transfer      │  - CPU Temp          │
│                      │ ══════════════════>│  - CPU Load          │
│                      │                    │  - Disk Space        │
│                      │                    │  - Status-Reports    │
└──────────────────────┘                    └──────────────────────┘
```

## 🔄 Workflow

1. **Preview-Stream starten** (Raspberry Pi)
   - `./start-preview-stream.sh` startet Low-Res Stream
   - TCP-Server auf Port 8554
   - H.264-encoded, 640x480, 5fps

2. **Auto-Trigger starten** (Client-PC)
   - `ai-had-kamera-auto-trigger.py` verbindet zum Stream
   - Initialisiert StreamProcessor mit YOLOv8
   - Startet Monitoring-Loop

3. **Kontinuierliche Überwachung**
   - Jeder Frame wird von YOLOv8 analysiert
   - bird-species Model erkennt nur Vögel (COCO class 14)
   - Konfidenz-Schwelle: 0.45 (konfigurierbar)

4. **Bei Vogel-Erkennung**
   - Trigger HD-Aufnahme über SSH
   - Ruft Haupt-Skript auf: `ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py`
   - Aufnahme-Dauer: 2 Minuten (konfigurierbar)

5. **Cooldown-Phase**
   - 30 Sekunden Wartezeit (konfigurierbar)
   - Verhindert zu viele Aufnahmen nacheinander

6. **Ressourcen-Monitoring**
   - Prüft jede Minute: CPU-Temp, Load, Disk
   - Automatischer Shutdown bei Überlastung
   - Status-Report alle 15 Minuten

## 🚀 Verwendung v1.2.0

### ⭐ Schnellstart mit Wrapper-Skript (empfohlen)

```bash
# Standard-Modus (1920x1080 @ 25fps + Audio)
./kamera-auto-trigger/start-vogel-beobachtung.sh

# Mit KI-Metadaten
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai

# Zeitlupen-Modus (120fps Slow-Motion!)
./kamera-auto-trigger/start-vogel-beobachtung.sh --slowmo

# Help anzeigen
./kamera-auto-trigger/start-vogel-beobachtung.sh --help
```

**Vorteile des Wrappers:**
- ✅ Automatische System-Checks (SSH-Agent, venv, Netzwerk)
- ✅ Optimierte CPU-Parameter (bereits eingebaut!)
- ✅ Übersichtliche Banner und Status
- ✅ Einfache Modus-Auswahl

### 🔧 Direkter Python-Aufruf (für Experten)

```bash
# Standard-Modus
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py

# Mit KI-Metadaten
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --recording-ai \
    --recording-ai-model yolov8n.pt

# Zeitlupen-Modus
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --recording-slowmo
```

### Stream-Test (Standalone)

```bash
# Teste StreamProcessor ohne Auto-Trigger
python python-skripte/stream_processor.py \
    --host raspberrypi-5-ai-had \
    --model bird-species \
    --threshold 0.45 \
    --duration 60 \
    --debug
```

## 📊 Features im Detail

### Auto-Trigger (`ai-had-kamera-auto-trigger.py`)

| Feature | Beschreibung | Parameter |
|---------|--------------|-----------|
| AI-Erkennung | YOLOv8-basierte Vogel-Erkennung | `--ai-model`, `--trigger-threshold` |
| Trigger-Dauer | Länge der HD-Aufnahme | `--trigger-duration` (Minuten) |
| Cooldown | Wartezeit zwischen Aufnahmen | `--cooldown` (Sekunden) |
| Preview-Stream | Resolution und FPS | `--preview-width/height/fps` |
| CPU-Monitoring | Max. Temperatur und Load | `--max-cpu-temp`, `--max-cpu-load` |
| Status-Reports | Intervall für Berichte | `--status-interval` (Minuten) |
| HD-Aufnahme | Auflösung für Trigger | `--width`, `--height` |

### StreamProcessor (`stream_processor.py`)

| Feature | Beschreibung |
|---------|--------------|
| Multi-Backend | GStreamer (Primary), FFMPEG (Fallback) |
| TCP/RTSP | Unterstützt beide Protokolle |
| YOLOv8 | Nano-Model für schnelle Inferenz |
| bird-species | Nur Vögel (COCO class 14) |
| Statistics | Frames, Detections, Inference-Time |
| Threading | Thread-safe mit Lock |
| Context Manager | `with`-Syntax unterstützt |

### Preview-Stream (`start-preview-stream.sh`)

| Feature | Beschreibung | Parameter |
|---------|--------------|-----------|
| Start/Stop | Service-Kontrolle | `--stop`, `--status` |
| Auflösung | Konfigurierbar | `--width`, `--height` |
| FPS | Frame-Rate | `--fps` |
| Bitrate | Stream-Qualität | `--bitrate` (kbps) |
| Rotation | Video-Rotation | `--rotation` (0/90/180/270) |
| Port | TCP-Port | `--port` |
| PID-Management | Sauberes Handling | Automatisch |

## 🎯 Optimale Einstellungen

### Szenario 1: Standard (ausgewogen)
```bash
# Preview-Stream (Raspberry Pi)
./start-preview-stream.sh --width 640 --height 480 --fps 5

# Auto-Trigger (Client-PC)
python ai-had-kamera-auto-trigger.py \
    --trigger-threshold 0.45 --cooldown 30
```
- **Gut für:** Normaler Betrieb, stabile Netzwerk-Verbindung
- **Performance:** ~45ms Inferenz-Zeit, ~5% CPU-Last

### Szenario 2: Hohe Genauigkeit
```bash
# Preview-Stream
./start-preview-stream.sh --width 800 --height 600 --fps 10

# Auto-Trigger
python ai-had-kamera-auto-trigger.py \
    --trigger-threshold 0.50 --cooldown 60
```
- **Gut für:** Seltene Vögel, weniger false positives
- **Performance:** ~80ms Inferenz-Zeit, ~10% CPU-Last

### Szenario 3: Schwache Netzwerk-Verbindung
```bash
# Preview-Stream
./start-preview-stream.sh --width 480 --height 360 --fps 3 --bitrate 500

# Auto-Trigger
python ai-had-kamera-auto-trigger.py \
    --preview-fps 3 --trigger-threshold 0.40
```
- **Gut für:** WLAN, langsame Verbindung
- **Performance:** ~30ms Inferenz-Zeit, niedrige Bandbreite

### Szenario 4: Viele Vögel
```bash
# Auto-Trigger
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 1 \
    --cooldown 15 \
    --trigger-threshold 0.40
```
- **Gut für:** Futterstelle mit häufigen Besuchen
- **Vorsicht:** Mehr Aufnahmen = mehr Speicherplatz!

## 🐛 Troubleshooting

Siehe detaillierte Guides:
- **[PREVIEW-STREAM-SETUP.md](PREVIEW-STREAM-SETUP.md)** - Setup-Probleme
- **[AUTO-TRIGGER-DOKUMENTATION.md](AUTO-TRIGGER-DOKUMENTATION.md)** - Feature-Probleme
- **[QUICKSTART-AUTO-TRIGGER.md](QUICKSTART-AUTO-TRIGGER.md)** - Quick-Fixes

### Häufigste Probleme

| Problem | Lösung |
|---------|--------|
| Keine Stream-Verbindung | `./start-preview-stream.sh --status` prüfen |
| ImportError: cv2 | `pip install opencv-contrib-python` |
| ImportError: ultralytics | `pip install ultralytics` |
| GStreamer fehlt | System-Pakete installieren (siehe PREVIEW-STREAM-SETUP.md) |
| Zu viele false positives | `--trigger-threshold` erhöhen auf 0.55 |
| Stream laggt | Auflösung/FPS reduzieren, Bitrate senken |
| Hohe CPU-Last | Kleineres Model, niedrigere FPS |

## 📈 Performance-Metriken v1.2.0

**🎯 CPU-Optimierung Breakthrough:**

```
Baseline (vor v1.2.0):    107% CPU  ❌
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stage 1 (Thread-Limits):   82.5% CPU
Stage 2 (FPS 5→3):          82.5% CPU
Stage 3 (Auflösung):        92% CPU
Stage 4 (imgsz=320):        40% CPU   ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gesamt-Reduktion:          -63% CPU
```

**Aktuelle Werte (YOLOv8n, 320x240@3fps, imgsz=320):**

| Metrik | v1.1.x | v1.2.0 | Verbesserung |
|--------|--------|--------|--------------|
| CPU-Last (Client) | 107% | 40% | -63% ✅ |
| Preview-FPS | 5 | 3 | CPU-schonend |
| Preview-Auflösung | 640x480 | 320x240 | -75% Pixel |
| YOLO imgsz | default (640) | 320 | -75% Inferenz |
| Inferenz-Zeit | ~80ms | ~30ms | -62% |
| RAM | 180MB | 180MB | Gleich |

**Modi-Performance:**

| Modus | Auflösung | FPS | CPU (PC) | CPU (RaspPi) |
|-------|-----------|-----|----------|--------------|
| Standard | 1920x1080 | 25 | ~40% | ~50% |
| Mit KI | 1920x1080 | 25 | ~40% | ~50% |
| Zeitlupe | 1536x864 | 120 | ~40% | ~75% |

**Hinweis:** Preview-Stream (320x240@3fps) ist für alle Modi gleich!

## 🔜 Geplante Erweiterungen

- [ ] Web-UI für Monitoring
- [ ] Mehrere Kameras gleichzeitig
- [ ] Custom-Model-Training
- [ ] Cloud-Upload der Aufnahmen
- [ ] Telegram-Benachrichtigungen
- [ ] Statistik-Dashboard

## 📚 Dokumentation

| Datei | Inhalt |
|-------|--------|
| [QUICKSTART-AUTO-TRIGGER.md](QUICKSTART-AUTO-TRIGGER.md) | 5-Minuten Quick-Start |
| [PREVIEW-STREAM-SETUP.md](PREVIEW-STREAM-SETUP.md) | Detaillierte Setup-Anleitung |
| [AUTO-TRIGGER-DOKUMENTATION.md](AUTO-TRIGGER-DOKUMENTATION.md) | Feature-Dokumentation |
| [AUTO-TRIGGER-OVERVIEW.md](AUTO-TRIGGER-OVERVIEW.md) | Architektur-Übersicht |

## 🤝 Beitragen

Verbesserungen willkommen! Besonders:
- Performance-Optimierungen
- Weitere AI-Modelle
- UI/Dashboard
- Tests

## 📝 Changelog

### v1.2.0 (2025-10-03) - CPU-Optimierung & Drei Modi

**🚀 Hauptfeatures:**
- 🎬 **Zeitlupen-Modus:** 120fps Slow-Motion mit --slowmo
- ⚡ **CPU-Optimierung:** 107% → 40% (-63% Reduktion!)
- 🎤 **Audio in allen Modi:** 44.1kHz Mono (automatisch)
- 🚀 **Wrapper-Skript:** start-vogel-beobachtung.sh mit System-Checks
- 🏗️ **Architektur-Dokumentation:** [docs/ARCHITEKTUR.md](../../docs/ARCHITEKTUR.md) mit Mermaid-Diagrammen
- 🔄 **Git-Automation:** Branch-Support (v1.2.0)

**⚡ CPU-Optimierungen:**
- Thread-Limits: OMP/BLAS/MKL_NUM_THREADS=2
- Preview-FPS: 5fps → 3fps
- Preview-Auflösung: 640x480 → 320x240
- **BREAKTHROUGH:** YOLO imgsz=320 (Schlüssel-Optimierung!)

**🎬 Drei Aufnahme-Modi:**
1. **Standard:** 1920x1080@25fps + Audio
2. **Mit KI:** 1920x1080@25fps + Audio + KI-Metadaten
3. **Zeitlupe:** 1536x864@120fps + Audio

**📊 Performance-Verbesserungen:**
- CPU-Last: 107% → 40% ✅
- Inferenz-Zeit: ~80ms → ~30ms ✅
- Stabiler Dauerbetrieb möglich ✅

**📚 Neue/Aktualisierte Dateien:**
- `docs/ARCHITEKTUR.md` (NEU - verschoben von kamera-auto-trigger/)
- `docs/PROJEKT-REORGANISATION.md` (verschoben in docs/)
- `kamera-auto-trigger/start-vogel-beobachtung.sh` (Enhanced)
- `kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py` (Optimiert)
- `kamera-auto-trigger/scripts/stream_processor.py` (imgsz=320)
- `docs/CHANGELOG.md` (v1.2.0)
- `kamera-auto-trigger/docs/AUTO-TRIGGER-DOKUMENTATION.md` (Aktualisiert)
- `kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md` (Aktualisiert)
- `git-automation/git_automation.py` (v1.2.0)
- `requirements-autotrigger.txt`

## 📄 Lizenz

Siehe [LICENSE](../LICENSE)
