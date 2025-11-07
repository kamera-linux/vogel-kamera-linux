# 🎬 Unified Camera Monitor

## Überblick

Der **Unified Camera Monitor** ist ein neuer Ansatz für das Vogel-Kamera-System, der alle Kamera-Operationen in einem einzigen Prozess vereint.

## Problem mit dem alten System

Das bisherige System hatte mehrere Probleme:

1. **Zwei separate Prozesse:**
   - Preview-Stream (TCP Watchdog) für Monitoring
   - Aufnahme-Script für Video-Recording
   
2. **Kamera-Konflikte:**
   - Beim Wechsel zwischen Preview und Aufnahme musste die Kamera gestoppt/gestartet werden
   - Stream-Unterbrechungen führten zu Connection-Problemen
   - Reconnect-Logik war komplex und fehleranfällig

3. **TCP-Stream-Probleme:**
   - `listen=1` Modus akzeptiert nur eine Verbindung
   - Nach Client-Disconnect muss Stream neu gestartet werden
   - Watchdog-Neustart dauert 10-20 Sekunden

## Lösung: Unified Camera Monitor

Ein einziger Python-Prozess auf dem Raspberry Pi, der:

- ✅ **Kontinuierlich die Kamera nutzt** (kein Stop/Start)
- ✅ **Dual-Stream mit picamera2:**
  - Low-Res Stream (640x480 @ 6fps) für AI-Analyse
  - High-Res Stream (1920x1080 @ 30fps) für Aufnahme
- ✅ **Direkte AI-Analyse** vor Ort
- ✅ **Sofortige Aufnahme** bei Trigger (keine SSH-Latenz)
- ✅ **Keine Kamera-Konflikte**

## Architektur

```
Raspberry Pi:
└── unified-camera-monitor.py
    ├── picamera2 (Dual-Stream)
    │   ├── lores: 640x480 @ 6fps → AI-Analyse
    │   └── main: 1920x1080 @ 30fps → Recording
    ├── YOLOv8 (Vogel-Erkennung)
    ├── Trigger-Logik (1.0s, 60% Konsistenz)
    └── H264-Encoder → Video-Datei
```

## Features

### 🎯 Kernfunktionen

- **Echtzeit-Monitoring:** Kontinuierliche Vogel-Erkennung mit YOLOv8
- **Automatische Aufnahme:** Bei Trigger-Bedingungen (Dauer + Konsistenz)
- **Cooldown-Management:** Konfigurierbare Wartezeit zwischen Aufnahmen
- **Dual-Stream:** Gleichzeitig Preview und High-Quality Recording
- **Keine Kamera-Konflikte:** Ein Prozess = Ein Kamera-Zugriff

### ⚙️ Konfigurierbar

- AI-Schwelle (threshold)
- Cooldown-Zeit
- Trigger-Dauer
- Aufnahme-Auflösung & FPS
- Preview-FPS
- Video-Speicher-Pfad

## Installation

### Voraussetzungen

```bash
# Auf Raspberry Pi:
sudo apt update
sudo apt install -y python3-picamera2
pip install ultralytics opencv-python numpy
```

### Setup

```bash
# Script kopieren
scp raspberry-pi-scripts/unified-camera-monitor.py roimme@raspberrypi-5-ai-had:~/vogel-kamera-linux/raspberry-pi-scripts/
scp raspberry-pi-scripts/start-unified-monitor.sh roimme@raspberrypi-5-ai-had:~/vogel-kamera-linux/raspberry-pi-scripts/

# Ausführbar machen
ssh roimme@raspberrypi-5-ai-had "chmod +x ~/vogel-kamera-linux/raspberry-pi-scripts/start-unified-monitor.sh ~/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor.py"
```

## Verwendung

### Basic Start

```bash
# Auf Raspberry Pi:
cd ~/vogel-kamera-linux/raspberry-pi-scripts
./start-unified-monitor.sh
```

### Mit Parametern

```bash
./start-unified-monitor.sh \
    --camera 0 \
    --threshold 0.4 \
    --cooldown 15 \
    --trigger-duration 1.0 \
    --preview-fps 6 \
    --recording-width 1920 \
    --recording-height 1080 \
    --recording-fps 30
```

### Als Systemd Service

```bash
# Service-Datei erstellen
sudo nano /etc/systemd/system/vogel-camera-monitor.service
```

```ini
[Unit]
Description=Vogel Camera Monitor
After=network.target

[Service]
Type=simple
User=roimme
WorkingDirectory=/home/roimme/vogel-kamera-linux/raspberry-pi-scripts
ExecStart=/home/roimme/vogel-kamera-linux/raspberry-pi-scripts/start-unified-monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable vogel-camera-monitor
sudo systemctl start vogel-camera-monitor

# Status prüfen
sudo systemctl status vogel-camera-monitor

# Logs anzeigen
sudo journalctl -u vogel-camera-monitor -f
```

## Parameter

| Parameter | Beschreibung | Default |
|-----------|--------------|---------|
| `--camera` | Kamera-Nummer (0 oder 1) | 0 |
| `--threshold` | AI-Erkennungs-Schwelle (0.0-1.0) | 0.4 |
| `--cooldown` | Wartezeit zwischen Aufnahmen (Sekunden) | 15 |
| `--trigger-duration` | Mindest-Dauer für Trigger (Sekunden) | 1.0 |
| `--video-path` | Basis-Pfad für Video-Speicherung | `/home/roimme/Videos/Vogelhaus` |
| `--preview-fps` | FPS für Preview/AI-Analyse | 6 |
| `--recording-width` | Aufnahme-Breite | 1920 |
| `--recording-height` | Aufnahme-Höhe | 1080 |
| `--recording-fps` | Aufnahme-FPS | 30 |
| `--model` | Pfad zum YOLO-Model (optional) | - |
| `--debug` | Debug-Modus aktivieren | false |

## Vorteile gegenüber altem System

### Performance

| Aspekt | Alt (Dual-Prozess) | Neu (Unified) |
|--------|-------------------|---------------|
| Stream-Stabilität | ⚠️ Reconnect-Probleme | ✅ Kontinuierlich |
| Trigger-Latenz | ~2-5s (SSH + Restart) | ~0.1s (direkt) |
| Kamera-Zugriff | ⚠️ Konflikte | ✅ Exklusiv |
| Wartungsaufwand | ⚠️ Hoch (2 Systeme) | ✅ Niedrig (1 System) |

### Zuverlässigkeit

- ✅ **Keine Stream-Unterbrechungen** mehr
- ✅ **Keine Reconnect-Probleme**
- ✅ **Keine Watchdog-Neustarts**
- ✅ **Schnellerer Trigger**
- ✅ **Einfachere Fehlersuche**

## Logs & Debugging

```bash
# Live-Logs auf Raspberry Pi
tail -f /tmp/unified-camera-monitor.log

# Status-Reports
# Werden automatisch alle 5 Minuten ausgegeben

# Debug-Modus
./start-unified-monitor.sh --debug
```

## Troubleshooting

### Kamera nicht gefunden

```bash
# Prüfe verfügbare Kameras
libcamera-hello --list-cameras

# Prüfe Kamera-Zugriff
libcamera-hello -t 2000
```

### Permissions-Probleme

```bash
# User zur video-Gruppe hinzufügen
sudo usermod -a -G video $USER

# Neu einloggen oder:
newgrp video
```

### YOLO-Model wird nicht gefunden

```bash
# YOLOv8 wird beim ersten Start automatisch heruntergeladen
# Oder manuell ein Model angeben:
./start-unified-monitor.sh --model ~/models/yolov8n.pt
```

## Migration vom alten System

1. **Stoppe altes System:**
   ```bash
   # Stoppe Auto-Trigger auf Client
   # Stoppe TCP-Watchdog auf Raspberry Pi
   ssh roimme@raspberrypi-5-ai-had "~/vogel-kamera-linux/raspberry-pi-scripts/start-tcp-preview-watchdog.sh --stop"
   ```

2. **Starte neues System:**
   ```bash
   ssh roimme@raspberrypi-5-ai-had "cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-unified-monitor.sh"
   ```

3. **Teste:**
   - Videos sollten in `/home/roimme/Videos/Vogelhaus` erscheinen
   - Logs in `/tmp/unified-camera-monitor.log`

## Zukünftige Erweiterungen

- [ ] Remote-Monitoring via WebSocket
- [ ] Live-Preview-Stream (optional)
- [ ] Telegram-Benachrichtigungen
- [ ] Zeitlupe-Modus Support
- [ ] Multi-Camera Support
- [ ] Cloud-Upload

## Lizenz

MIT License - siehe [LICENSE](../LICENSE)
