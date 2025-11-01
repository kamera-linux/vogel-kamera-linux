# 🐦 Kamera Auto-Trigger System

> ⚠️ **Trixie Version (v1.3.0-dev):** Diese Dokumentation gilt für Raspberry Pi OS Trixie (Debian 13).  
> 📘 **Für Bookworm:** Verwenden Sie [main-Branch v1.2.x](https://github.com/kamera-linux/vogel-kamera-linux/tree/main)

Automatisches Vogel-Erkennungs- und Aufnahme-System mit KI-Unterstützung für Raspberry Pi.

## 📋 Übersicht

Das Auto-Trigger-System überwacht kontinuierlich einen **MediaMTX RTSP-Stream** vom Raspberry Pi und startet automatisch HD-Aufnahmen, wenn ein Vogel erkannt wird. Es nutzt YOLOv8 für die Echtzeit-Objekterkennung über Netzwerk.

### ✨ Features

- 🐦 **Automatische Vogel-Erkennung** mit YOLOv8 AI
- 📡 **RTSP-Stream über Netzwerk** (MediaMTX, 640x480@5fps) - **NEU in Trixie**
- 🎥 **HD-Aufnahmen** (bis zu 4K, nur bei Erkennung)
- 📊 **System-Monitoring** (CPU, Temperatur, RAM, Festplatte)
- 🔄 **Cooldown-System** (verhindert Duplikate)
- 🛑 **Sicheres Beenden** (Strg+C, automatisches Cleanup)
- ⚙️ **Konfigurierbar** (Threshold, Aufnahme-Dauer, Cooldown)
- 🎯 **Optimierte Trigger-Logik** (1.0s Duration, 0.5s Toleranz) - **NEU in v1.3.0**

## 🚀 Quick Start

### 1. Voraussetzungen

> 📘 **Vollständige Installation:** Siehe [docs/INSTALLATION-TRIXIE.md](../docs/INSTALLATION-TRIXIE.md)

**Raspberry Pi (MediaMTX RTSP-Server):**
```bash
# MediaMTX installieren (einmalig)
# Siehe: docs/INSTALLATION-TRIXIE.md

# MediaMTX Status prüfen
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had
sudo systemctl status mediamtx
# Sollte: "active (running)"

# MediaMTX läuft im On-Demand Modus:
# - Stream startet automatisch bei Client-Verbindung
# - Stoppt automatisch nach ~10s ohne Client
# - Keine manuelle Verwaltung nötig!
```

**Client-PC (AI-Verarbeitung):**
```bash
# Dependencies installieren (einmalig)
pip install -r requirements.txt

# ODER in venv:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Firewall konfigurieren (einmalig, falls UFW/iptables aktiv):**
```bash
# Auf Client-PC (falls nötig)
cd kamera-auto-trigger
sudo ./setup-firewall-client-pc.sh

# Auf Raspberry Pi: Port 8554 öffnen
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had
sudo ufw allow 8554/tcp comment 'MediaMTX RTSP'
```

### 2. System starten

**Option A: Mit Komfort-Wrapper (empfohlen)**
```bash
cd kamera-auto-trigger

# Standard-Modus: Aufnahme OHNE KI (schnell, weniger CPU-Last)
./start-vogel-beobachtung.sh

# Mit KI-Aufnahme: Objekterkennung während Aufnahme
./start-vogel-beobachtung.sh --with-ai

# Zeitlupen-Modus: 120fps für spektakuläre Aufnahmen
./start-vogel-beobachtung.sh --slowmo
```

**Modi erklärt:**

| Modus | Trigger | Aufnahme | Auflösung | FPS | CPU-Last | Verwendung |
|-------|---------|----------|-----------|-----|----------|------------|
| Standard | 🤖 MIT KI | 📹 OHNE KI | 4096x2160 | 30 | Niedrig | Längere Sessions, schnelle Aufnahmen |
| `--with-ai` | 🤖 MIT KI | 🤖 MIT KI | 4096x2160 | 30 | Höher | Objekt-Analyse während Aufnahme |
| `--slowmo` | 🤖 MIT KI | 🎬 ZEITLUPE | 1536x864 | 120 | Mittel | Spektakuläre Zeitlupen-Aufnahmen |

**Option B: Manuell mit Parametern**
```bash
cd kamera-auto-trigger

# Ohne KI-Aufnahme (Standard, nutzt neue Defaults)
./run-auto-trigger.sh --trigger-duration 2

# Mit KI-Aufnahme
./run-auto-trigger.sh --trigger-duration 2 --recording-ai

# Mit Custom-Schwellenwert (wenn nötig)
./run-auto-trigger.sh --trigger-duration 2 --trigger-threshold 0.45
```

### 3. Beenden

Drücke **Strg+C** im Terminal - das System beendet sich sauber und räumt auf.

## ⚙️ Konfiguration

### Wichtige Parameter

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `--trigger-duration` | 2 | Aufnahme-Dauer in Minuten |
| `--trigger-threshold` | 0.40 | AI-Erkennungs-Schwelle (0.0-1.0) CPU-optimiert |
| `--cooldown` | 30 | Pause nach Aufnahme (Sekunden) |
| `--preview-fps` | 4 | Preview-Stream FPS (CPU/Performance Balance) |
| `--preview-width` | 400 | Preview-Breite (CPU-optimiert) |
| `--preview-height` | 300 | Preview-Höhe (CPU-optimiert) |
| `--recording-ai` | false | Aufnahme MIT KI (Flag, kein Wert) |
| `--recording-ai-model` | bird-species | AI-Modell für Aufnahme (nur mit --recording-ai) |
| `--recording-slowmo` | false | Zeitlupen-Aufnahme 120fps (Flag, überschreibt AI-Modus) |
| `--width` | 4096 | HD-Auflösung Breite (außer Zeitlupe: 1536) |
| `--height` | 2160 | HD-Auflösung Höhe (außer Zeitlupe: 864) |
| `--ai-model` | bird-species | AI-Model für Trigger (yolov8/bird-species/custom) |

### Beispiele

```bash
# Standard mit CPU-optimierten Defaults (4fps @ 400x300, threshold 0.40)
./run-auto-trigger.sh --trigger-duration 2

# Höhere Präzision (weniger false positives)
./run-auto-trigger.sh --trigger-threshold 0.55

# Niedrigere Schwelle (mehr Trigger, aber ggf. mehr false positives)
./run-auto-trigger.sh --trigger-threshold 0.35

# Full HD statt 4K (kleinere Dateien)
./run-auto-trigger.sh --width 1920 --height 1080

# Längere Aufnahmen mit mehr Cooldown
./run-auto-trigger.sh --trigger-duration 5 --cooldown 60

# Aufnahme MIT KI-Analyse (Objekterkennung während Aufnahme)
./run-auto-trigger.sh --recording-ai --recording-ai-model bird-species

# Zeitlupen-Aufnahme (120fps, 1536x864)
./run-auto-trigger.sh --recording-slowmo --trigger-duration 1

# Performance-Tuning: Höhere FPS für bessere Erkennung (mehr CPU-Last)
./run-auto-trigger.sh --preview-fps 5 --preview-width 480 --preview-height 360

# Performance-Tuning: Niedrigere FPS für weniger CPU-Last
./run-auto-trigger.sh --preview-fps 3 --preview-width 320 --preview-height 240
```

## 📁 Verzeichnisstruktur

```
kamera-auto-trigger/
├── scripts/
│   ├── ai-had-kamera-auto-trigger.py  # Haupt-Skript
│   └── stream_processor.py             # Stream-Verarbeitung & AI
├── docs/
│   ├── AUTO-TRIGGER-DOKUMENTATION.md   # Vollständige Dokumentation
│   ├── PREVIEW-STREAM-SETUP.md         # Stream-Setup
│   ├── QUICKSTART-AUTO-TRIGGER.md      # Schnellstart-Anleitung
│   └── FIREWALL-SETUP-SUMMARY.md       # Firewall-Konfiguration
├── tests/                               # Test-Skripte
├── run-auto-trigger.sh                  # Wrapper-Skript
├── run-stream-test.sh                   # Stream-Test
├── start-vogel-beobachtung.sh           # Komfort-Starter
├── requirements.txt                     # Python-Dependencies
└── README.md                            # Diese Datei

../config/
└── models/
    └── yolov8n.pt                       # YOLOv8 Nano Model (6.3MB)
```

### 🤖 AI-Modell-Verwaltung

Das YOLOv8-Modell wird im zentralen `config/models/` Verzeichnis gespeichert und von allen Skripten verwendet. Dies verhindert mehrfaches Herunterladen:

- **Speicherort:** `../config/models/yolov8n.pt`
- **Größe:** 6.3 MB (Nano-Variante für schnelle Inferenz)
- **Automatik:** Falls das Modell nicht vorhanden ist, wird es automatisch von Ultralytics heruntergeladen
- **Versionierung:** Das Modell wird im Git-Repository versioniert

## 🎯 Workflow

1. **Preview-Stream** läuft kontinuierlich auf Raspberry Pi (640x480@5fps)
2. **Client-PC** verbindet sich und analysiert Stream mit YOLOv8
3. **Vogel erkannt?** → Trigger HD-Aufnahme (4K, 2 Minuten)
4. **Cooldown** (10 Sekunden) → Zurück zu Schritt 2

## 📊 System-Status

Das System zeigt alle 5 Sekunden einen Status-Report:

```
📊 STATUS-REPORT
⏱️  Laufzeit: 2h 34min
🎬 Aufnahmen getriggert: 17
🕐 Letzte Aufnahme: vor 3 Minuten

🖥️  Remote-Host (raspberrypi-5-ai-had):
   🌡️  CPU-Temp: 42.3°C 🟢
   ⚡ CPU-Load: 0.45 🟢
   💾 Festplatte: 12% belegt 🟢
   💭 RAM: 1.2Gi / 7.9Gi
```

## 🔍 Troubleshooting

### Stream verbindet nicht

```bash
# Prüfe ob Stream läuft
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had './start-rtsp-stream.sh --status'

# Prüfe Firewall
sudo ufw status | grep 8554
```

### Zu viele Fehlerkennungen

```bash
# Erhöhe Threshold
./run-auto-trigger.sh --trigger-threshold 0.55
```

### Zu wenig Erkennungen

```bash
# Senke Threshold
./run-auto-trigger.sh --trigger-threshold 0.35
```

## 📚 Weitere Dokumentation

- **[AUTO-TRIGGER-DOKUMENTATION.md](docs/AUTO-TRIGGER-DOKUMENTATION.md)** - Vollständige Dokumentation
- **[PREVIEW-STREAM-SETUP.md](docs/PREVIEW-STREAM-SETUP.md)** - Stream-Setup & Troubleshooting
- **[QUICKSTART-AUTO-TRIGGER.md](docs/QUICKSTART-AUTO-TRIGGER.md)** - 5-Minuten Schnellstart
- **[FIREWALL-SETUP-SUMMARY.md](docs/FIREWALL-SETUP-SUMMARY.md)** - Firewall-Konfiguration

## 📝 Lizenz

Siehe [LICENSE](../LICENSE) im Hauptverzeichnis.

## 🤝 Beitragen

Issues und Pull Requests sind willkommen!

---

**Version:** 1.2.0  
**Zuletzt aktualisiert:** 1. Oktober 2025
