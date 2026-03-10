# 🎬 Unified Camera Monitor (v2.1.0)

## Überblick

Der **Unified Camera Monitor** ist das Kernystem für die Vogel-Kamera mit Audio/Video-Synchronisation, automatischer Vogel-Erkennung (YOLOv8) und professioneller Aufnahme in 4K Cinema-Format.

## Architektur (v2.1.0)

```
Raspberry Pi:
└── unified-camera-monitor.py
    ├── rpicam-vid (H264, Rotation 180°)
    │   └── 4096x2160 @ 30fps (Cinema 4K)
    ├── arecord (ALSA Audio)
    │   └── 44.1kHz Mono, hw:0,0 (USB-Stick)
    ├── ffmpeg (Merge & Konvertierung)
    │   └── -fflags +genpts für synchrone Timestamps
    ├── YOLOv8n (Vogel-Erkennung - optional)
    ├── Threading (Parallel Video + Audio)
    └── rsync (Transfer zum Client-PC)
```

## Neue Features in v2.1.0

- ✅ **Thread-basierte Audio/Video-Synchronisation** (Parallel-Aufnahme)
- ✅ **Perfekte Sync**: Beide Streams exakt gleiche Duration
- ✅ **USB-Audio-Stick** automatisch erkannt (hw:0,0, hw:1,0, etc.)
- ✅ **4K Cinema Format** (4096x2160 @ 30fps)
- ✅ **Alle rpicam-vid Parameter**: Rotation, Codec, HDR, Autofokus, ROI
- ✅ **Rotation 180°** als Default (Vogelbild oben)
- ✅ **Manual Recording Mode** (direkte Aufnahme ohne AI)
- ✅ **Auto-Transfer via rsync** zum Client-PC

## Features

### � Recording Modi

- **Manual Record**: Direkte N-Sekunden Aufnahme
  ```bash
  python3 unified-camera-monitor.py --manual-record --recording-duration 60
  ```

- **AI-Monitoring** (watchdog): Automatische Vogel-Erkennung (Watchdog-Modus)
  ```bash
  python3 unified-camera-monitor.py --enable-audio --slowmo
  ```

### 🎙️ Audio-Integration

- **Automatische USB-Audio-Erkennung**: Sucht hw:0,0, hw:1,0, hw:1,1, hw:1,2, hw:1,3
- **ALSA arecord**: 44.1kHz, S16_LE, Mono
- **ffmpeg Merge**: 
  - Mit Audio: `-fflags +genpts -r {fps} -i video -i audio -c:v copy -c:a aac output.mp4`
  - Ohne Audio: `-fflags +genpts -r {fps} -i video -c:v copy output.mp4`

### 📷 Kamera-Parameter

- **Auflösung**: 4096x2160 (Cinema 4K) oder konfigurierbar
- **FPS**: 30 @ Standard, höher mit Custom-Einstellung
- **Rotation**: 180° (Standard - Vogelbild oben)
- **Codec**: h264 (Standard)
- **Autofokus**: continuous, macro range (Standard)
- **HDR**: off (Standard)
- **ROI**: Optional für Region of Interest

### 🤖 YOLOv8 Integration (Optional)

- Echtzeit-Vogel-Erkennung
- Trigger bei Erkennung (1.0s Dauer, Konsistenz-Schwelle)
- Cooldown-Management zwischen Aufnahmen
- Automatisches Model-Download (yolov8n.pt)

## Installation

### System-Dependencies (auf Raspberry Pi)

```bash
# Essenzielle Packages
sudo apt update
sudo apt install -y rpicam-apps alsa-utils ffmpeg

# Python-Dependencies
pip install ultralytics opencv-python numpy
```

### Setup

1. **Code kopieren zum Raspberry Pi:**
   ```bash
   scp raspberry-pi-scripts/unified-camera-monitor.py <your-username>@your-raspberry-pi:~/vogel-kamera-linux/raspberry-pi-scripts/
   ```

2. **Testen ob Audio-Stick erkannt wird:**
   ```bash
   ssh <your-username>@your-raspberry-pi "
   lsusb
   arecord -l
   "
   ```

3. **Erste Test-Aufnahme (5 Sekunden):**
   ```bash
   ssh <your-username>@your-raspberry-pi "python3 ~/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor.py --manual-record --recording-duration 5 --rotation 180"
   ```

## Verwendung

### Manual Recording (Direkte Aufnahme)

```bash
# 60-Sekunden Aufnahme mit Audio (4K, Rotation 180°)
python3 unified-camera-monitor.py \
  --manual-record \
  --recording-duration 60 \
  --rotation 180 \
  --codec h264 \
  --autofocus-mode continuous

# Von Client-PC aus:
ssh <your-username>@your-raspberry-pi "python3 ~/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor.py --manual-record --recording-duration 60"
```

### AI-Monitoring mit Vogel-Erkennung

```bash
# Watchdog-Modus: Wartet auf Vogel, nimmt automatisch auf
python3 unified-camera-monitor.py \
  --threshold 0.4 \
  --cooldown 15 \
  --trigger-duration 1.0 \
  --enable-audio

# Mit Zeitlupe
python3 unified-camera-monitor.py \
  --slowmo \
  --threshold 0.4 \
  --enable-audio
```

### Parameter Reference

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `--manual-record` | - | Aktiviert direkten Aufnahme-Modus (ohne AI) |
| `--enable-audio` | false | Aktiviert Audio-Aufnahme (arecord) |
| `--slowmo` | false | Zeitlupen-Modus (60 fps statt 30) |
| `--recording-duration` | 60 | Aufnahme-Dauer in Sekunden |
| `--rotation` | 180 | Video-Rotation: 0, 90, 180, 270 |
| `--codec` | h264 | Video-Codec |
| `--hdr` | off | HDR-Modus: auto, off |
| `--autofocus-mode` | continuous | AF-Modus |
| `--autofocus-range` | macro | AF-Bereich |
| `--camera` | 0 | Kamera-Nummer (0 oder 1) |
| `--threshold` | 0.4 | YOLOv8 Erkennungs-Schwelle |
| `--cooldown` | 15 | Wartezeit zwischen Aufnahmen (Sekunden) |
| `--trigger-duration` | 1.0 | Mindest-Erkennungs-Dauer (Sekunden) |
| `--model` | yolov8n.pt | Pfad zum YOLO-Model |

## Systemd Service Setup

Optional: Systemd Service für Auto-Start:

```bash
# Service-Datei erstellen
sudo tee /etc/systemd/system/vogel-camera-monitor.service > /dev/null <<EOF
[Unit]
Description=Vogel Camera Monitor with Audio
After=network.target

[Service]
Type=simple
User=<your-username>
WorkingDirectory=/home/<your-username>/vogel-kamera-linux/raspberry-pi-scripts
ExecStart=/usr/bin/python3 /home/<your-username>/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor.py --enable-audio --threshold 0.4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable vogel-camera-monitor
sudo systemctl start vogel-camera-monitor

# Status prüfen
sudo systemctl status vogel-camera-monitor
sudo journalctl -u vogel-camera-monitor -f
```

## Audio/Video-Synchronisation Details

### Technisches Konzept (v2.1.0)

Die Audio- und Video-Aufnahmen laufen in **separaten Threads** parallel ab:

```
Zeit    Video-Thread              Audio-Thread
│       rpicam-vid                arecord
│       ----------                --------
T0  ├─► Startet                   ├─► Startet (GLEICHZEITIG!)
│   │   4096x2160 @ 30fps         │   44.1kHz, S16_LE, Mono
│   │                             │   hw:0,0 (USB-Auto-Detect)
│   │                             │
T+60├─► Endet nach 60s            │
│   │   Erzeugt: vogel_*.h264     │
│   │                             │
│   │                             ├─► Endet nach 60s
│   │                             │   Erzeugt: vogel_*.wav
│   │                             │
│   └─────────────────────────────┘
│
│   ffmpeg Merge (mit -fflags +genpts)
│   ────────────────────────────
└─► Output: vogel_*.mp4
    ✅ Video + Audio synchronisiert
    ✅ Beide Streams exakt gleiche Duration
```

### ffmpeg Parameter (Kritisch für Sync)

**Mit Audio:**
```bash
ffmpeg -fflags +genpts -r 30 \
  -i video.h264 -i audio.wav \
  -c:v copy -c:a aac \
  output.mp4
```

**Wichtig:**
- `-fflags +genpts` → Generiert korrekte Timestamps
- `-r 30` → FPS setzen für Zeitskalierung
- KEIN `-shortest` Flag (würde kürzeren Stream abschneiden)
- Beide Streams EXAKT gleiche Duration erforderlich

### Warum Thread-basiert?

**Falsch (alt):** Sequenzielle Ausführung
```python
# Video läuft 60 Sekunden
run_video(duration=60)  # Blockiert bis Sekunde 60

# Audio startet ERST nach Video-Ende!
run_audio(duration=60)  # Wartet bis Sekunde 120
→ ❌ Audio ist 60 Sekunden zu spät → Keine Sync möglich!
```

**Richtig (neu):** Parallele Ausführung mit Threading
```python
# Video startet in Thread 1
thread1 = Thread(video.start())  # t=0s, läuft bis t=60s
thread1.start()

# Audio startet GLEICHZEITIG in Thread 2  
thread2 = Thread(audio.start())  # t=0s, läuft bis t=60s
thread2.start()

# Warten auf beide
thread1.join()  # t=60s✓
thread2.join()  # t=60s✓
→ ✅ Perfekt synchronisiert!

## Logs & Debugging

### Live-Logs auf Raspberry Pi

```bash
# Log-Datei (wenn eingerichtet)
tail -f /tmp/unified-camera-monitor.log

# Direct Output (mit Debug-Modus)
python3 unified-camera-monitor.py --manual-record --recording-duration 5 --debug
```

### Häufige Log-Meldungen

```
✅ USB-Audio-Gerät gefunden (arecord): hw:0,0
🎬 Video-Thread startet: rpicam-vid --camera 0 --rotation 180 ...
🎤 Audio-Thread startet: arecord -D hw:0,0 -d 61 -f cd ...
✅ Audio-Thread erfolgreich beendet
✅ Video-Thread erfolgreich beendet
Duration: 00:00:60.00 ✓
```

## Troubleshooting

### Kamera nicht erkannt

```bash
# Prüfe Kamera mit libcamera
rpicam-hello --list-cameras

# Teste Kamera
rpicam-hello -t 2000
```

### Audio-Device nicht erkannt

```bash
# Liste alle Audio-Devices
arecord -l

# Suche nach USB-Devices
lsusb | grep -i audio

# Manuelle Aufnahme-Test
arecord -D hw:0,0 -f cd -d 5 /tmp/test.wav
aplay /tmp/test.wav
```

### ffmpeg Fehler beim Merge

**Problem:** "Protocol 'pipe' not found"
```bash
# Überprüfe ffmpeg Installation
which ffmpeg
ffmpeg -version
```

**Problem:** "Invalid argument" bei MP4-Output
```bash
# Überprüfe dass beide Input-Dateien existieren
ls -lh /tmp/vogel_*.h264 /tmp/vogel_*.wav 2>/dev/null

# Manuelle ffmpeg-Test
ffmpeg -fflags +genpts -r 30 -i video.h264 -i audio.wav -c:v copy -c:a aac output.mp4
```

### Rotation funktioniert nicht

```bash
# Überprüfe ob Parameter übergeben wurde
ls -lh ~/Videos/Vogelhaus/*/vogel_*.mp4 | tail -1
ffprobe -v error -select_streams v:0 -show_entries stream=width,height $(ls -t ~/Videos/Vogelhaus/*/vogel_*.mp4 | head -1)

# Erwartet: width=4096, height=2160 (rotiert von 2160x4096)
```

### Timing-Fehler "Duration mismatch"

**Ursache:** Video und Audio haben unterschiedliche Längen
```bash
# Überprüfe Durations
ffprobe -v error -show_entries format=duration <video.h264>
ffprobe -v error -show_entries format=duration <audio.wav>

# Sollten identisch sein! Unterschied = Sync-Problem
```

## Release-Notizen (v2.1.0)

### ✅ Implementiert

- ✅ Thread-basierte Audio/Video-Synchronisation
- ✅ USB-Audio-Stick Unterstützung (hw:0,0 Auto-Detection)
- ✅ rpicam-vid Integration mit allen Parametern
- ✅ ffmpeg Merge mit `-fflags +genpts` 
- ✅ Rotation 180° Default (Vogelbild oben)
- ✅ Manual Record Mode
- ✅ AI-Watchdog Mode (YOLOv8)
- ✅ Slow-Motion Support (60fps)
- ✅ rsync Auto-Transfer zum Client

### 🚀 Geplant (v2.2.0+)

- [ ] Web-Dashboard für Remote-Monitoring
- [ ] Live-Preview-Stream via WebRTC
- [ ] Telegram-Benachrichtigungen bei Vogel-Erkennung
- [ ] Erweiterte Multi-Camera-Unterstützung
- [ ] Cloud-Backup Integration
- [ ] Erweiterte Analytics (Vogelarten-Klassifizierung)

## Support & Dokumentation

- **Hauptdoku:** [README.md](../README.md)
- **Client-Tool:** [unified-monitor-client/README.md](../unified-monitor-client/README.md)
- **Audio-Integration Changelog:** [AUDIO-FIX-CHANGELOG.md](../AUDIO-FIX-CHANGELOG.md)

## Lizenz

MIT License - siehe [LICENSE](../LICENSE)
