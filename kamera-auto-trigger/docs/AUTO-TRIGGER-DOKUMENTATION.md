# 🐦 Auto-Trigger Vogel-Kamera Dokumentation

## Übersicht

Das `ai-had-kamera-auto-trigger.py` Skript überwacht kontinuierlich das Vogelhaus und startet automatisch HD-Aufnahmen, wenn ein Vogel erkannt wird.

## ✨ Features

### 🎯 Automatischer Trigger
- Kontinuierliche Überwachung mit AI-Objekterkennung
- Automatischer Start von HD-Aufnahmen bei Vogel-Erkennung
- Konfigurierbare Aufnahme-Dauer

### 📊 Ressourcen-Monitoring
- Überwachung von CPU-Temperatur, Load und Festplatte
- Automatisches Beenden bei kritischen Werten
- Status-Report alle 15 Minuten (konfigurierbar)

### 🔄 Cooldown-System
- Verhindert zu viele Aufnahmen hintereinander
- Konfigurierbare Wartezeit zwischen Aufnahmen

### 🛑 Sauberes Beenden
- Strg+C für kontrollierten Shutdown
- Automatisches Cleanup aller Remote-Prozesse
- Finaler Status-Report beim Beenden

## 🚀 Verwendung

### Basis-Aufruf
```bash
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species
```

### Mit Custom-Einstellungen
```bash
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 3 \
    --cooldown 60 \
    --trigger-threshold 0.5 \
    --max-cpu-temp 65 \
    --status-interval 10
```

### Alle Parameter

| Parameter | Beschreibung | Standard | Beispiel |
|-----------|--------------|----------|----------|
| `--trigger-duration` | Aufnahmedauer bei Vogel-Erkennung (Minuten) | 2 | --trigger-duration 3 |
| `--ai-model` | AI-Modell für Erkennung | bird-species | --ai-model yolov8 |
| `--ai-model-path` | Pfad zu eigenem Modell | - | --ai-model-path /path/to/model.json |
| `--cooldown` | Wartezeit zwischen Aufnahmen (Sekunden) | 30 | --cooldown 60 |
| `--trigger-threshold` | AI-Erkennungs-Schwelle | 0.45 | --trigger-threshold 0.5 |
| `--preview-fps` | FPS für Monitoring | 5 | --preview-fps 10 |
| `--preview-width` | Breite für Preview | 640 | --preview-width 800 |
| `--preview-height` | Höhe für Preview | 480 | --preview-height 600 |
| `--max-cpu-temp` | Max. CPU-Temperatur (°C) | 70 | --max-cpu-temp 65 |
| `--max-cpu-load` | Max. CPU-Load | 3.0 | --max-cpu-load 2.5 |
| `--status-interval` | Status-Report Intervall (Minuten) | 15 | --status-interval 10 |
| `--width` | Breite für HD-Aufnahme | 4096 | --width 1920 |
| `--height` | Höhe für HD-Aufnahme | 2160 | --height 1080 |
| `--rotation` | Video-Rotation | 180 | --rotation 0 |
| `--cam` | Kamera-ID | 0 | --cam 1 |

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

### Optimale Einstellungen

**Für häufige Vogelbesuche:**
```bash
--trigger-duration 1 \
--cooldown 30 \
--trigger-threshold 0.5
```

**Für seltene Vögel (weniger false positives):**
```bash
--trigger-duration 3 \
--cooldown 60 \
--trigger-threshold 0.6
```

**Für schwache Raspberry Pi:**
```bash
--preview-fps 3 \
--preview-width 480 \
--preview-height 360 \
--max-cpu-temp 65
```

### Monitoring im Hintergrund

Als Systemd-Service (empfohlen für 24/7 Betrieb):
```bash
# Siehe: docs/SYSTEMD-SERVICE-SETUP.md (folgt)
```

### Log-Ausgabe in Datei
```bash
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species \
    2>&1 | tee auto-trigger.log
```

## 🐛 Troubleshooting

### Problem: Skript startet nicht
```
❌ Keine Verbindung zu raspberrypi-5-ai-had
```
**Lösung:**
- SSH-Verbindung testen: `ssh user@host`
- .env-Konfiguration prüfen
- Netzwerk-Verbindung checken

### Problem: Zu viele false positives
```
🐦 Vogel erkannt! (aber es war keiner)
```
**Lösung:**
- Schwelle erhöhen: `--trigger-threshold 0.6`
- AI-Modell wechseln: `--ai-model bird-species`

### Problem: System beendet sich zu oft
```
⛔ Beende Auto-Trigger aus Sicherheitsgründen...
```
**Lösung:**
- Limits erhöhen: `--max-cpu-temp 75 --max-cpu-load 3.5`
- System-Kühlung verbessern
- Preview-Auflösung reduzieren

## 📚 Siehe auch

- [AI-MODELLE-VOGELARTEN.md](AI-MODELLE-VOGELARTEN.md) - AI-Modell-Dokumentation
- [README.md](../README.md) - Haupt-Dokumentation
- [CHANGELOG.md](../docs/CHANGELOG.md) - Versions-Historie

## 🤝 Beitragen

Verbesserungen und Pull Requests sind willkommen!

Besonders gesucht:
- Preview-Stream-Implementierung
- AI-Inferenz-Optimierung
- Systemd-Service-Setup
- Performance-Verbesserungen
