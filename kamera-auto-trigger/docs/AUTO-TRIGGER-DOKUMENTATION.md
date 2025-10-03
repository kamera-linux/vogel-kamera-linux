# 🐦 Auto-Trigger Vogel-Kamera Dokumentation

## Übersicht

Das Auto-Trigger System überwacht kontinuierlich das Vogelhaus mit KI-gestützter Echtzeit-Analyse und startet automatisch HD-Aufnahmen, wenn ein Vogel erkannt wird. Version 1.2.0 bietet drei Aufnahmemodi und ist CPU-optimiert für stabilen Dauerbetrieb.

## 🎬 Drei Aufnahme-Modi

### 📹 Standard-Modus (Default)
- **Auflösung:** 1920x- USB-Mikr- USB-Mikrofon angeschlossen? Auf R**Hinweis:** Preview-Stream (320x240@3fps) ist für alle Modi gleich → gleiche CPU-Last auf PC!

## 📚 Siehe auch

- **[../../docs/ARCHITEKTUR.md](../../docs/ARCHITEKTUR.md)** - 🏗️ Detaillierte Architektur mit Mermaid-Diagrammen (NEU in v1.2.0!) prüfen: `arecord -l`
- Audio-Device wird automatisch erkannt (hw:X,0)
- Ohne Mikrofon: "nur Video"-Modus (funktioniert trotzdem)

## 📊 Performance-Metriken (v1.2.0)

### CPU-Optimierung Breakdowngeschlossen? Auf RaspPi prüfen: `arecord -l`
- Audio-Device wird automatisch erkannt (hw:X,0)
- Ohne Mikrofon: "nur Video"-Modus (funktioniert trotzdem)

## 📊 Performance-Metriken (v1.2.0)

### CPU-Optimierung Breakdown25fps
- **Audio:*## 📚**Hinweis:** Preview-Stream (320x240@3fps) ist für alle Modi gleich → gleiche CPU-Last auf PC!

## 📚 Siehe auch

- **[../../docs/ARCHITEKTUR.md](../../docs/ARCHITEKTUR.md)** - 🏗️ Detaillierte Architektur mit Mermaid-Diagrammen (NEU in v1.2.0!)e auch

- **[../../docs/ARCHITEKTUR.md](../../docs/ARCHITEKTUR.md)** - 🏗️ Detaillierte Architektur mit Mermaid-Diagrammen (NEU in v1.2.0!)
- **[QUICKSTART-AUTO-TRIGGER.md](QUICKSTART-AUTO-TRIGGER.md)** - Schnellstart-Anleitung
- **[AUTO-TRIGGER-OVERVIEW.md](AUTO-TRIGGER-OVERVIEW.md)** - Übersicht und Konzepte
- **[../../docs/AI-MODELLE-VOGELARTEN.md](../../docs/AI-MODELLE-VOGELARTEN.md)** - AI-Modell-Dokumentation
- **[../../README.md](../../README.md)** - Haupt-Dokumentation
- **[../../docs/CHANGELOG.md](../../docs/CHANGELOG.md)** - Versions-Historie mit v1.2.0 Detailsz Mono (automatisch wenn USB-Mikrofon vorhanden)
- **Verwendung:** Normale HD-Aufnahmen für Dokumentation
- **CPU-Last:** ~40% (optimiert)

### 🤖 KI-Modus (--with-ai)
- **Auflösung:** 1920x1080 @ 25fps
- **Audio:** 44.1kHz Mono
- **Zusätzlich:** KI-Metadaten und Erkennungs-Informationen
- **Verwendung:** Aufnahmen mit detaillierten AI-Analysen
- **CPU-Last:** ~40% (optimiert)

### 🎬 Zeitlupen-Modus (--slowmo)
- **Auflösung:** 1536x864 @ 120fps
- **Audio:** 44.1kHz Mono
- **Verwendung:** Flügelschlag-Analyse, spektakuläre Slow-Motion
- **CPU-Last:** ~40% (Preview), RaspPi übernimmt 120fps-Encoding
- **Besonderheit:** 10 Sekunden Pre-Recording Buffer

## ✨ Features v1.2.0

### 🎯 Automatischer Trigger
- Kontinuierliche Überwachung mit YOLOv8-Objekterkennung
- Automatischer Start von HD-Aufnahmen bei Vogel-Erkennung
- Drei konfigurierbare Aufnahme-Modi (Standard, KI, Zeitlupe)
- Audio-Aufnahme in **allen Modi** (44.1kHz Mono)

### ⚡ CPU-Optimierung (NEU in v1.2.0)
- **Drastische Reduktion:** 107% → 40% CPU-Last (-63%)
- **Thread-Limiting:** OMP/BLAS/MKL_NUM_THREADS=2
- **Optimierte Preview:** 320x240 @ 3fps (statt 640x480 @ 5fps)
- **YOLO imgsz=320:** Effiziente AI-Inferenz ohne Qualitätsverlust
- **Stabiler Dauerbetrieb:** Auch auf weniger leistungsstarker Hardware

### 📊 Ressourcen-Monitoring
- Überwachung von CPU-Temperatur, Load und Festplatte
- Automatisches Beenden bei kritischen Werten
- Status-Report alle 15 Minuten (konfigurierbar)

### 🔄 Cooldown-System
- Verhindert zu viele Aufnahmen hintereinander
- Konfigurierbare Wartezeit zwischen Aufnahmen (default: 5 Sekunden)

### 🛑 Sauberes Beenden
- Strg+C für kontrollierten Shutdown
- Automatisches Cleanup aller Remote-Prozesse
- Finaler Status-Report beim Beenden

## 🚀 Verwendung

### ⭐ Empfohlen: Wrapper-Skript (v1.2.0)

Das Wrapper-Skript `start-vogel-beobachtung.sh` ist die einfachste Methode und beinhaltet:
- Automatische System-Checks (SSH-Agent, venv, Netzwerk)
- Optimierte CPU-Parameter (--preview-fps 3, --preview-width 320, --preview-height 240)
- Übersichtliche Banner und Status-Ausgaben
- Einfache Modus-Auswahl

```bash
# Standard-Modus (1920x1080 @ 25fps + Audio)
./kamera-auto-trigger/start-vogel-beobachtung.sh

# Mit KI-Metadaten
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai

# Zeitlupen-Modus (120fps + Audio)
./kamera-auto-trigger/start-vogel-beobachtung.sh --slowmo

# Help anzeigen
./kamera-auto-trigger/start-vogel-beobachtung.sh --help
```

### 🔧 Direkter Python-Aufruf

Für erweiterte Kontrolle über Parameter:

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

# Mit Custom-Einstellungen
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --preview-fps 3 \
    --preview-width 320 \
    --preview-height 240 \
    --recording-ai \
    --recording-ai-model yolov8n.pt
```

### Alle Parameter

#### 🎬 Aufnahme-Modi
| Parameter | Beschreibung | Standard | Beispiel |
|-----------|--------------|----------|----------|
| `--recording-ai` | KI-Modus mit Metadaten aktivieren | False | --recording-ai |
| `--recording-ai-model` | YOLOv8 Modell für KI-Modus | yolov8n.pt | --recording-ai-model yolov8s.pt |
| `--recording-slowmo` | Zeitlupen-Modus (120fps) aktivieren | False | --recording-slowmo |

#### 🖼️ Preview-Stream (CPU-Optimiert in v1.2.0)
| Parameter | Beschreibung | Standard | Beispiel |
|-----------|--------------|----------|----------|
| `--preview-fps` | FPS für Monitoring | 3 | --preview-fps 5 |
| `--preview-width` | Breite für Preview | 320 | --preview-width 640 |
| `--preview-height` | Höhe für Preview | 240 | --preview-height 480 |
| `--preview-threshold` | AI-Erkennungs-Schwelle | 0.5 | --preview-threshold 0.6 |

#### 🎯 Trigger-Verhalten
| Parameter | Beschreibung | Standard | Beispiel |
|-----------|--------------|----------|----------|
| `--trigger-cooldown` | Wartezeit zwischen Aufnahmen (Sekunden) | 5 | --trigger-cooldown 10 |

#### 🖥️ Remote-System
| Parameter | Beschreibung | Standard | Beispiel |
|-----------|--------------|----------|----------|
| `--remote-host` | Raspberry Pi Hostname/IP | (aus config) | --remote-host raspi5 |
| `--remote-user` | SSH-Benutzer | (aus config) | --remote-user pi |
| `--remote-videos-dir` | Zielverzeichnis für Videos | Videos | --remote-videos-dir Aufnahmen |

#### ⚠️ Legacy-Parameter (nicht mehr empfohlen)
Die folgenden Parameter existieren noch aus Kompatibilitätsgründen, werden aber durch die Modi-Parameter ersetzt:
- `--trigger-duration`, `--ai-model`, `--ai-model-path`, `--cooldown`, `--trigger-threshold`
- `--width`, `--height`, `--rotation`, `--cam`

## 📊 Status-Report

Alle 15 Minuten (oder konfigurierbar) zeigt das Skript einen detaillierten Status-Report:

```
======================================================================
📊 STATUS-REPORT - 2025-10-01 14:30:15
======================================================================
⏱️  Laufzeit: 2h 35min
🎬 Aufnahmen getriggert: 8
🕐 Letzte Aufnahme: vor 12 Minuten

🖥️  Remote-Host (raspberrypi-5-ai-had):
   🌡️  CPU-Temp: 52.3°C 🟢
   ⚡ CPU-Load: 0.85 🟢
   💾 Festplatte: 75% belegt 🟢
   💭 RAM: 2.1G / 7.8G
======================================================================
```

## 🛑 Beenden

### Normales Beenden
```bash
Strg+C
```
Führt sauberes Shutdown durch:
1. Stoppt Monitoring-Loop
2. Gibt finalen Status-Report aus
3. Beendet alle Remote-Prozesse
4. Cleanup und Exit

### Automatisches Beenden

Das Skript beendet sich automatisch, wenn:
- **CPU-Temperatur** > `--max-cpu-temp` (default: 70°C)
- **CPU-Load** > `--max-cpu-load` (default: 3.0)

Beispiel-Ausgabe:
```
🚨 KRITISCH: System-Ressourcen überschritten!
   🌡️  CPU-Temp: 72.5°C (Max: 70.0°C)
   ⚡ CPU-Load: 3.2 (Max: 3.0)

⛔ Beende Auto-Trigger aus Sicherheitsgründen...
```

## ⚠️ Wichtige Hinweise

### 🔧 Implementierungs-Status

**✅ Vollständig implementiert!**

Das System ist produktionsreif und enthält:

1. **✅ Preview-Stream vom Raspberry Pi**
   - TCP/H.264-Server mit `rpicam-vid`
   - Start-Skript: `raspberry-pi-scripts/start-preview-stream.sh`
   - Konfigurierbare Auflösung, FPS, Bitrate

2. **✅ Frame-Grabbing über Netzwerk**
   - OpenCV mit GStreamer-Support
   - Automatischer Fallback auf FFMPEG
   - StreamProcessor-Klasse: `python-skripte/stream_processor.py`

3. **✅ AI-Inferenz auf Preview-Frames**
   - Ultralytics YOLOv8 Integration
   - bird-species Model (nur Vögel)
   - Echtzeit-Objekterkennung mit konfigurierbaren Schwellen

### 📝 Setup erforderlich

Das System ist fertig, benötigt aber einmalige Einrichtung:

**Schritt 1: Dependencies installieren**
```bash
# Auf Client-PC:
pip install -r requirements.txt
pip install -r requirements-autotrigger.txt

# System-Pakete (Ubuntu/Debian):
sudo apt install python3-opencv libgstreamer1.0-dev gstreamer1.0-plugins-base
```

**Schritt 2: Preview-Stream auf Raspberry Pi starten**
```bash
# SSH zum Raspberry Pi:
ssh user@raspberrypi-5-ai-had

# Stream-Skript kopieren (einmalig):
# (wird vom Client-PC aus gemacht, siehe PREVIEW-STREAM-SETUP.md)

# Stream starten:
./start-preview-stream.sh
```

**Schritt 3: Auto-Trigger starten**
```bash
# Auf Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species
```

Siehe **[PREVIEW-STREAM-SETUP.md](PREVIEW-STREAM-SETUP.md)** für die vollständige Anleitung!

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Start: ai-had-kamera-auto-trigger.py                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  System-Check          │
        │  - Verbindung testen   │
        │  - Status-Report       │
        └────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Ressourcen-Monitor        │◄─── Status-Report alle 15 Min
    │  (separater Thread)        │
    │  - CPU-Temp prüfen         │
    │  - CPU-Load prüfen         │
    │  - Auto-Shutdown bei Limit │
    └────────────────────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Monitoring-Loop       │
        │  - Preview-Stream      │
        │  - AI-Erkennung        │
        │  - Cooldown-Check      │
        └────┬──────────┬────────┘
             │          │
     Kein Vogel    Vogel erkannt!
             │          │
             │          ▼
             │     ┌─────────────────────────┐
             │     │  Trigger HD-Aufnahme    │
             │     │  - Haupt-Skript starten │
             │     │  - X Minuten aufnehmen  │
             │     └───────────┬─────────────┘
             │                 │
             │                 ▼
             │           ┌──────────────┐
             │           │  Cooldown    │
             │           │  X Sekunden  │
             │           └──────┬───────┘
             │                  │
             └──────────────────┘
                     │
            (Loop wiederholt sich)
```

## 💡 Tipps & Tricks

### Optimale Einstellungen (v1.2.0)

**Für häufige Vogelbesuche:**
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh \
    --trigger-cooldown 5 \
    --preview-threshold 0.45
```

**Für seltene Vögel (weniger false positives):**
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai \
    --trigger-cooldown 10 \
    --preview-threshold 0.6
```

**Für spektakuläre Aufnahmen:**
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --slowmo
# 120fps für Flügelschlag-Analyse in Zeitlupe!
```

**Für maximale CPU-Schonung (bereits optimal in v1.2.0):**
```bash
# Die Standard-Einstellungen sind bereits CPU-optimiert:
# - Preview: 320x240 @ 3fps
# - Thread-Limits: OMP/BLAS/MKL=2
# - YOLO imgsz=320
# Ergebnis: ~40% CPU-Last statt 107%!
```

### Monitoring im Hintergrund

Als Systemd-Service (empfohlen für 24/7 Betrieb):
```bash
# Siehe: docs/SYSTEMD-SERVICE-SETUP.md (folgt)
```

### Log-Ausgabe in Datei
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh --with-ai \
    2>&1 | tee auto-trigger-$(date +%Y%m%d-%H%M%S).log
```

## 🐛 Troubleshooting

### Problem: Skript startet nicht
```
❌ Keine Verbindung zu raspberrypi-5-ai-had
```
**Lösung:**
- SSH-Verbindung testen: `ssh user@host`
- SSH-Agent läuft? `ssh-add -l`
- Netzwerk-Verbindung checken: `ping raspberrypi-5-ai-had`
- Wrapper-Skript macht automatische Checks!

### Problem: "Ultralytics YOLO nicht verfügbar"
```
⚠️ Ultralytics YOLO nicht verfügbar
```
**Lösung:**
- Virtual Environment aktiviert? Wrapper macht das automatisch
- Dependencies installiert? `pip install -r requirements.txt`
- Wrapper-Skript verwenden: `./kamera-auto-trigger/start-vogel-beobachtung.sh`

### Problem: Zu viele false positives
```
🐦 Vogel erkannt! (aber es war keiner)
```
**Lösung:**
- Schwelle erhöhen: `--preview-threshold 0.6`
- KI-Modus verwenden: `--with-ai` (detailliertere Analyse)

### Problem: Hohe CPU-Last (>80%)
```
CPU: 92% - zu hoch!
```
**Lösung in v1.2.0:**
- **Bereits gelöst!** Standard-Einstellungen sind CPU-optimiert (~40%)
- Falls immer noch hoch: Preview-FPS weiter reduzieren `--preview-fps 2`
- Prüfen: Läuft venv? `which python` sollte `.venv/bin/python` zeigen

### Problem: Kein Audio in Aufnahmen
```
⚠️ Kein USB-Audio-Gerät gefunden
```
**Lösung:**
- USB-Mikrofon angeschlossen? Auf RaspPi prüfen: `arecord -l`
- Audio-Device wird automatisch erkannt (hw:X,0)
- Ohne Mikrofon: "nur Video"-Modus (funktioniert trotzdem)

## 📊 Performance-Metriken (v1.2.0)

### CPU-Optimierung Breakdown

```
Baseline (vor v1.2.0):    107% CPU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stage 1 (Thread-Limits):   82.5% CPU  ↓ 23%
Stage 2 (FPS 5→3):          82.5% CPU  ↓ 0%
Stage 3 (Auflösung):        92% CPU    ↑ 10% (!)
Stage 4 (imgsz=320):        40% CPU    ↓ 63% ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gesamt-Reduktion:          -63% CPU
```

**Schlüssel-Optimierung:** YOLO `imgsz=320` Parameter reduziert AI-Inferenz um ~75%

### Modi-Vergleich

| Modus | Auflösung | FPS | Audio | CPU (PC) | CPU (RaspPi) |
|-------|-----------|-----|-------|----------|--------------|
| Standard | 1920x1080 | 25 | ✅ 44.1kHz | ~40% | ~50% |
| Mit KI | 1920x1080 | 25 | ✅ 44.1kHz | ~40% | ~50% |
| Zeitlupe | 1536x864 | 120 | ✅ 44.1kHz | ~40% | ~75% |

**Hinweis:** Preview-Stream (320x240@3fps) ist für alle Modi gleich → gleiche CPU-Last auf PC!

## 📚 Siehe auch

- **[ARCHITEKTUR.md](../ARCHITEKTUR.md)** - Detaillierte Architektur mit Mermaid-Diagrammen (NEU in v1.2.0!)
- **[QUICKSTART-AUTO-TRIGGER.md](QUICKSTART-AUTO-TRIGGER.md)** - Schnellstart-Anleitung
- **[AUTO-TRIGGER-OVERVIEW.md](AUTO-TRIGGER-OVERVIEW.md)** - Übersicht und Konzepte
- **[../../docs/AI-MODELLE-VOGELARTEN.md](../../docs/AI-MODELLE-VOGELARTEN.md)** - AI-Modell-Dokumentation
- **[../../README.md](../../README.md)** - Haupt-Dokumentation
- **[../../docs/CHANGELOG.md](../../docs/CHANGELOG.md)** - Versions-Historie mit v1.2.0 Details

## 🤝 Beitragen

Verbesserungen und Pull Requests sind willkommen!

**v1.2.0 Status:**
- ✅ Preview-Stream (RTSP mit libcamera-vid)
- ✅ AI-Inferenz-Optimierung (imgsz=320)
- ✅ Drei Aufnahme-Modi (Standard/KI/Zeitlupe)
- ✅ CPU-Optimierung (107% → 40%)
- ✅ Audio in allen Modi
- 🔄 Systemd-Service-Setup (in Arbeit)
- 🔄 Web-Dashboard (geplant)
