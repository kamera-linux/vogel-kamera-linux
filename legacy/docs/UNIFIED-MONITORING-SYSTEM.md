# Unified Monitoring System - Komplettlösung

## Übersicht

Das Unified Monitoring System ist eine vollständige Lösung für Vogel-Beobachtung mit:
- ✅ Remote-Kamera-Monitor auf Raspberry Pi
- ✅ Automatische Video-Übertragung und Konvertierung
- ✅ System-Monitoring (CPU, Temp, RAM)
- ✅ AI-HAD Audio-Integration
- ✅ Live-Logs
- ✅ Sauberer Cleanup beim Beenden

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│  CLIENT PC (start-unified-monitoring.sh)                │
│  ├─ Remote Monitor Steuerung                            │
│  ├─ Video-Watcher (automatische Übertragung)            │
│  ├─ FFmpeg-Konvertierung (5/10/20/30/120 FPS)           │
│  ├─ Status-Reporter (alle 5 Min)                        │
│  └─ Audio-Monitor (optional)                            │
│                                                          │
│                      SSH                                 │
│                       │                                  │
│  RASPBERRY PI                                            │
│  ├─ unified-camera-monitor.py                           │
│  │   ├─ picamera2 (Kamera)                              │
│  │   ├─ YOLOv8n (AI-Erkennung)                          │
│  │   └─ Automatische Aufnahme                           │
│  │                                                       │
│  └─ audio-monitor.sh (AI-HAD, optional)                 │
│      ├─ Audio-Level-Erkennung                           │
│      └─ Event-Logging                                   │
└─────────────────────────────────────────────────────────┘
```

## Installation

### 1. Auf Raspberry Pi

```bash
# Scripts kopieren
cd ~/vogel-kamera-linux/raspberry-pi-scripts

# Setup ausführen (nur einmalig)
./setup-unified-monitor.sh

# Audio-Monitor ausführbar machen
chmod +x audio-monitor.sh
```

### 2. Auf Client PC

```bash
# Keine spezielle Installation nötig
# SSH-Key muss bereits konfiguriert sein
```

## Verwendung

### Standard-Modus (30 FPS)

```bash
./kamera-auto-trigger/start-unified-monitoring.sh normal
```

### Zeitlupen-Modus (120 FPS)

```bash
./kamera-auto-trigger/start-unified-monitoring.sh slowmo
```

### Mit Audio-Monitoring (AI-HAD)

```bash
ENABLE_AUDIO=true ./kamera-auto-trigger/start-unified-monitoring.sh slowmo
```

## Features

### Automatische Video-Verarbeitung

Nach jeder Aufnahme:
1. ✅ Video wird vom Pi zum Client PC übertragen
2. ✅ FFmpeg konvertiert zu verschiedenen FPS
   - **Zeitlupe**: 5, 10, 20, 30, 120 FPS
   - **Normal**: 30 FPS
3. ✅ Ordnerstruktur: `~/Videos/Vogelhaus/[Zeitlupe|Normal]/YYYY/WW/Timestamp/`
4. ✅ Original bleibt auf Pi (optional löschbar)

### System-Monitoring

Alle 5 Minuten:
- 🌡️ CPU-Temperatur (Pi + Client)
- ⚡ CPU-Last
- 💾 Festplatten-Nutzung
- 💭 RAM-Nutzung

### Live-Logs

Echtzeit-Anzeige aller Ereignisse:
- 🐦 Vogel-Erkennungen
- 🎬 Aufnahme-Start/-Ende
- ⚠️ Fehler und Warnungen
- 📊 Status-Updates

### AI-HAD Audio-Integration

Nutzt den AI-HAD USB-Audio-Adapter:
- 🎤 Kontinuierliche Audio-Überwachung
- 🔊 Event-Erkennung bei lauten Geräuschen
- 💾 Kurze Audio-Clips bei Events
- 📝 Event-Log für Analyse

## Beenden

**Strg+C** im Terminal:
- Stoppt alle lokalen Prozesse
- Stoppt Remote Monitor auf Pi
- Sauberer Cleanup aller Dienste

## Konfiguration

### Umgebungsvariablen

```bash
# SSH-Konfiguration
export SSH_KEY=~/.ssh/id_rsa_ai-had
export SSH_USER=roimme
export SSH_HOST=raspberrypi-5-ai-had

# Audio
export ENABLE_AUDIO=true
export AUDIO_THRESHOLD=0.3

# Video-Pfade
export CLIENT_VIDEO_BASE=~/Videos/Vogelhaus
```

### Parameter im Script anpassen

Editiere `start-unified-monitoring.sh`:

```bash
THRESHOLD="0.5"          # AI-Erkennungs-Schwelle
COOLDOWN="15"            # Sekunden zwischen Aufnahmen
STATUS_INTERVAL="300"    # Sekunden zwischen Status-Reports
```

## Troubleshooting

### Monitor startet nicht

```bash
# Prüfe SSH-Verbindung
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had

# Prüfe Scripts auf Pi
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
    'ls -la ~/vogel-kamera-linux/raspberry-pi-scripts/'
```

### Videos werden nicht übertragen

```bash
# Prüfe Video-Verzeichnis auf Pi
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
    'ls -lh /home/roimme/Videos/Vogelhaus/'

# Prüfe Logs
./kamera-auto-trigger/remote-unified-control.sh --logs 100
```

### Audio funktioniert nicht

```bash
# Prüfe AI-HAD Device auf Pi
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
    'arecord -l'

# Teste Audio-Aufnahme
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
    'arecord -D plughw:5,0 -d 5 -f S16_LE test.wav'
```

## Vorteile gegenüber altem System

| Feature | Altes System | Unified System |
|---------|--------------|----------------|
| TCP-Stream | ❌ Buffer-Probleme | ✅ Kein TCP-Stream |
| Kamera-Konflikte | ❌ Dual-Process | ✅ Single-Process |
| CPU-Last Client | ❌ 51% (Stream-Decoding) | ✅ <5% (nur Monitoring) |
| Stream-Stabilität | ❌ Bricht nach 1-2 Aufnahmen ab | ✅ Stabil |
| AI-Performance | ❌ Netzwerk-Latenz | ✅ Lokal, keine Latenz |
| Video-Übertragung | ✅ Automatisch | ✅ Automatisch |
| FFmpeg-Konvertierung | ✅ Automatisch | ✅ Automatisch |
| Audio-Integration | ❌ Nicht vorhanden | ✅ AI-HAD Support |
| Remote-Steuerung | ❌ Manuell | ✅ Automatisch |

## Dateistruktur

```
kamera-auto-trigger/
├── start-unified-monitoring.sh    # Haupt-Wrapper (Client PC)
├── remote-unified-control.sh       # Remote-Steuerung
└── ...

raspberry-pi-scripts/
├── unified-camera-monitor.py       # Kamera-Monitor
├── start-unified-monitor.sh        # Start-Script
├── setup-unified-monitor.sh        # Setup
├── audio-monitor.sh                # Audio-Monitoring (AI-HAD)
└── UNIFIED-MONITOR-README.md       # Dokumentation

Videos/
└── Vogelhaus/
    ├── Normal/              # 30 FPS Aufnahmen
    │   └── YYYY/WW/Timestamp/
    │       └── *.mp4
    └── Zeitlupe/            # 120 FPS Aufnahmen
        └── YYYY/WW/Timestamp/
            ├── *_5fps.mp4
            ├── *_10fps.mp4
            ├── *_20fps.mp4
            ├── *_30fps.mp4
            ├── *_120fps.mp4
            └── *.h264 (original)
```

## Beispiel-Session

```bash
# Starte Zeitlupen-Monitoring mit Audio
$ ENABLE_AUDIO=true ./kamera-auto-trigger/start-unified-monitoring.sh slowmo

╔══════════════════════════════════════════════════════════════════╗
║   🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung              ║
╚══════════════════════════════════════════════════════════════════╝

🎬 Modus: Zeitlupe (1536x864 @ 120fps)

🔍 System-Check...
📡 SSH-Verbindung zu raspberrypi-5-ai-had... ✅
📄 Remote Scripts... ✅

✅ System-Check erfolgreich

🚀 Starte Remote Monitor...
✅ Remote Monitor gestartet

📊 Starte lokale Monitoring-Dienste...
✅ Video-Watcher gestartet (PID: 12345)
✅ Status-Reporter gestartet (PID: 12346)
✅ Audio-Monitor gestartet (PID: 12347)

====================================================================
🔍 Live-Logs vom Remote Monitor
====================================================================

2025-11-11 10:00:00,000 - INFO - 🐦 Vogel erkannt!
2025-11-11 10:00:01,200 - INFO - ✅ TRIGGER! Starte Aufnahme...
2025-11-11 10:01:01,200 - INFO - ✅ Aufnahme abgeschlossen
📥 Übertrage: vogel_2025-11-11_10-00-01.h264
✅ Video übertragen
🎬 Konvertiere zu 5 FPS...
   ✅ 5 FPS fertig
🎬 Konvertiere zu 10 FPS...
   ✅ 10 FPS fertig
...

# Beenden mit Strg+C
^C
🛑 Beende Unified Monitoring System...
📡 Stoppe Remote Monitor...
✅ Alle Prozesse beendet
```
