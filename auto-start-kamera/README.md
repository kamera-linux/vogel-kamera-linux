# 🚀 Auto-Start Kamera - v2.0.0 Unified Monitoring

Dieser Ordner enthält die Haupt-Startskripte für das v2.0.0 Unified Camera Monitor System.

## 📁 Inhalt

### `start-unified-monitoring.sh`
**Hauptskript für Client PC** - Startet das komplette Monitoring-System:
- Remote Monitor auf Raspberry Pi
- Lokale Überwachung und Status-Anzeige
- Automatische Video-Übertragung
- Heartbeat-Monitoring

**Verwendung:**
```bash
cd ~/vogel-kamera-linux/auto-start-kamera
./start-unified-monitoring.sh [normal|slowmo]
```

**Modi:**
- `normal` - Standard-Aufnahme (1920x1080 @ 30fps)
- `slowmo` - Zeitlupen-Aufnahme (1536x864 @ 120fps)

**Features:**
- ✅ Automatischer System-Check (SSH, Scripts, Network)
- 📊 Live-Monitoring mit Traffic Light System
- 🎥 Automatische Video-Übertragung vom Pi zum Client
- 💓 Heartbeat-Überwachung
- 🔄 Auto-Shutdown Protection

### `remote-unified-control.sh`
**Remote Control Tool** - Steuert den Monitor auf dem Raspberry Pi:

**Befehle:**
```bash
./remote-unified-control.sh --start [normal|slowmo]  # Monitor starten
./remote-unified-control.sh --stop                   # Monitor stoppen
./remote-unified-control.sh --restart                # Monitor neustarten
./remote-unified-control.sh --status                 # Status anzeigen
./remote-unified-control.sh --logs [N]               # Logs anzeigen
./remote-unified-control.sh --follow-logs            # Live-Logs
./remote-unified-control.sh --list-videos            # Videos auflisten
```

## 🔧 Konfiguration

### Umgebungsvariablen
```bash
# SSH-Konfiguration
export SSH_KEY="~/.ssh/id_rsa_ai-had"
export SSH_USER="roimme"
export SSH_HOST="raspberrypi-5-ai-had"

# Traffic Light Thresholds
export THRESHOLD_RED="75"       # CPU/Temp kritisch
export THRESHOLD_YELLOW="60"    # CPU/Temp Warnung
export THRESHOLD_GREEN="45"     # CPU/Temp OK
```

## 📊 Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT PC (start-unified-monitoring.sh)  │
│                                                             │
│  ┌──────────────┐  SSH   ┌────────────────────────────┐   │
│  │ System-Check │───────>│ Raspberry Pi 5             │   │
│  └──────────────┘        │                            │   │
│         │                │  unified-camera-monitor.py │   │
│         │                │  - picamera2               │   │
│         v                │  - YOLOv8 Detection        │   │
│  ┌──────────────┐        │  - Traffic Light Monitor   │   │
│  │ Start Remote │        │  - Auto-Shutdown           │   │
│  │   Monitor    │───────>│                            │   │
│  └──────────────┘        └────────────────────────────┘   │
│         │                         │                        │
│         v                         │ Video Files            │
│  ┌──────────────┐                 │                        │
│  │ Live Monitor │<────────────────┘                        │
│  │ - Status     │                                          │
│  │ - Heartbeat  │  rsync                                   │
│  │ - Logs       │<──────────── Videos/Vogelhaus/          │
│  └──────────────┘                                          │
│         │                                                  │
│         v                                                  │
│  ┌──────────────┐                                          │
│  │ Video-Sync   │                                          │
│  │ (automatisch)│                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## 🆚 vs. Legacy System

| Feature | v2.0.0 (dieser Ordner) | v1.x (legacy/) |
|---------|------------------------|----------------|
| **Architektur** | Unified Single Process | Separate Scripts |
| **Monitoring** | Integriert (Traffic Lights) | Extern |
| **Kamera-API** | picamera2 (native) | libcamera-vid (wrapper) |
| **AI-Detection** | YOLOv8 (direkt) | Separate Prozesse |
| **Performance** | ~8% CPU | ~25% CPU |
| **Wartung** | 1 Prozess | 5+ Prozesse |
| **Auto-Shutdown** | ✅ Integriert | ❌ Nicht vorhanden |

## 📚 Dokumentation

Vollständige Dokumentation im Wiki:
- **[Unified Monitor](https://github.com/kamera-linux/vogel-kamera-linux/wiki/Unified-Monitor)** - Hauptdokumentation
- **[Installation Guide](https://github.com/kamera-linux/vogel-kamera-linux/wiki/Installation-Guide)** - Setup
- **[CLI Parameter](https://github.com/kamera-linux/vogel-kamera-linux/wiki/Unified-Monitor#cli-parameter)** - Parameter-Referenz
- **[Troubleshooting](https://github.com/kamera-linux/vogel-kamera-linux/wiki/Troubleshooting)** - Problemlösungen

## 🔗 Migration von v1.x

Wenn du von Legacy-Scripts migrierst:
```bash
# Alt (v1.x)
cd ~/vogel-kamera-linux/legacy/kamera-auto-trigger
./start-vogel-beobachtung.sh --with-ai

# Neu (v2.0.0)
cd ~/vogel-kamera-linux/auto-start-kamera
./start-unified-monitoring.sh normal
```

**Parameter-Mapping:**
- `--with-ai` → immer aktiv (YOLOv8 integriert)
- `--threshold` → Traffic Light System
- `--cooldown` → `--record-cooldown`
- `--quality` → nicht mehr nötig (native API)

Siehe: [Legacy Systems Wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki/Legacy-Systems)

## ⚠️ Wichtig

- **Nur ein Monitoring-System gleichzeitig** - v1.x und v2.0.0 nicht parallel starten!
- **SSH-Setup erforderlich** - `~/.ssh/id_rsa_ai-had` muss konfiguriert sein
- **Raspberry Pi 5** - Optimiert für RPi 5 Hardware
- **Python 3.11+** - picamera2 benötigt aktuelle Python-Version

## 🆘 Hilfe

Bei Problemen:
1. `./remote-unified-control.sh --status` - Systemstatus prüfen
2. `./remote-unified-control.sh --logs 100` - Letzte Logs anzeigen
3. [Troubleshooting Wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki/Troubleshooting)
4. [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
