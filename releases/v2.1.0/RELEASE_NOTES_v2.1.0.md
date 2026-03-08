# 🎬 Version 2.1.0 - Audio/Video-Synchronisation & Professional Recording

**Release-Datum:** 8. März 2026  
**Vorherige Version:** v2.0.2  
**Status:** Stabil ✅

## 🎙️ Hauptchanges: Audio/Video-Synchronisation

### Problem (v2.0.x)
- Audio und Video wurden **sequenziell** aufgenommen
- Video startet, Audio startet ERST wenn Video endet
- Resultat: Keine Synchronisation möglich
- Merge-Versuche: Audio um 60+ Sekunden versetzt

### Lösung (v2.1.0)
- **Threading-basierte Parallel-Aufnahme**
- Video UND Audio starten **gleichzeitig**
- Beide Streams laufen für **exakt gleiche Dauer**
- ffmpeg Merge mit `-fflags +genpts` für korrekte Timestamps
- **Resultat:** Perfekt synchronisierte MP4-Dateien ✅

### Technische Implementierung
```python
# v2.1.0: Threading für Parallel-Aufnahme
video_thread = threading.Thread(target=run_video)
audio_thread = threading.Thread(target=run_audio)

video_thread.start()  # t=0s
audio_thread.start()  # t=0s (GLEICHZEITIG!)

time.sleep(duration + 1)  # Beide laufen parallel

video_thread.join()  # Wartet auf Video-Ende
audio_thread.join()  # Wartet auf Audio-Ende
```

## 🎯 Neue Features

### 1. USB-Audio-Stick Integration
- **Automatische Erkennung:** hw:0,0, hw:1,0, hw:1,1, hw:1,2, hw:1,3
- **arecord Parameter:** 44.1kHz, S16_LE, Mono
- **Fallback:** Automatische Suche bei nicht gefundenem Gerät
- **Status-Output:** Zeigt erkanntes Gerät beim Start

### 2. Manual Recording Mode
```bash
python3 unified-camera-monitor.py \
  --manual-record \
  --recording-duration 60 \
  --rotation 180
```
- Direkte N-Sekunden Aufnahmen ohne AI-Watchdog
- Perfekt für Tests und manuelle Vogelbeobachtung
- Mit oder ohne Audio

### 3. Professionelle Kamera-Parameter
Alle rpicam-vid-Parameter jetzt konfigurierbar:
- `--rotation` (0, 90, 180, 270) - **Default: 180** ✅
- `--codec` (h264, libx264, etc.) - **Default: h264**
- `--hdr` (auto, off) - **Default: off**
- `--autofocus-mode` (continuous, manual, once) - **Default: continuous**
- `--autofocus-range` (normal, macro) - **Default: macro**
- `--roi` (region of interest, optional)

### 4. Cinema 4K Format
- **4096 x 2160 pixels** @ 30fps (Standard)
- Höhere Auflösung als 1920x1080 (v2.0.x)
- Codec: H264 (rpicam-vid nativ)
- Bitrate: ~50-100 Mbps (abhängig von Szene)

### 5. ffmpeg Sync-Parameter
**Kritisch für Audio/Video-Sync:**
```bash
ffmpeg -fflags +genpts -r 30 \
  -i video.h264 \
  -i audio.wav \
  -c:v copy -c:a aac \
  output.mp4
```
- `-fflags +genpts` → Generiert korrekte Timestamps
- `-r 30` → FPS für Zeitskalierung
- **KEIN** `-shortest` Flag (würde kurzen Stream abschneiden)

## 🔧 Breaking Changes

### Gelöschte Dateien
- ✂️ `raspberry-pi-scripts/setup-unified-monitor.sh` (veraltet)
- ✂️ `raspberry-pi-scripts/start-unified-monitor.sh` (veraltet)

**Grund:** Waren obsolet durch neue Python-basierte Architektur

### Parameter Umbenennungen
- `--slowmo` bleibt unverändert (60fps statt 30fps)
- `--enable-audio` aktiviert USB-Audio-Aufnahme

### Dependencies (Neu)
```bash
# System-Packages
sudo apt install -y rpicam-apps alsa-utils ffmpeg

# Python (wie vorher)
pip install ultralytics opencv-python numpy
```

~~picamera2 ist nicht mehr erforderlich~~ ✅

## ✅ Tested & Verified

### Test-Szenarien
- ✅ **5-Sekunden Aufnahme:** Video 4096x2160 + Audio 44.1kHz → Sync ✓
- ✅ **60-Sekunden Aufnahme:** Komplette Dauer korrekt
- ✅ **Rotation 180°:** Video oberseite korrekt
- ✅ **USB-Audio-Erkennung:** hw:2,0 automatisch gefunden
- ✅ **ffmpeg Merge:** Beide Streams in MP4 ✓
- ✅ **rsync Transfer:** Automatischer Download zum Client

### Verifizierte Hardware
- Raspberry Pi 5 (8GB RAM)
- IMX708 Camera Module 3
- USB Audio-Stick (C-Media Electronics)
- Debian Trixie (13)

## 📊 Vergleich: v2.0.2 vs v2.1.0

| Feature | v2.0.2 | v2.1.0 |
|---------|--------|--------|
| **Audio/Video-Sync** | ❌ Sequenziell | ✅ Parallel (Threading) |
| **Audio-Unterstützung** | ❌ Keine | ✅ USB-Stick + arecord |
| **ffmpeg Merge** | ❌ Nicht funktional | ✅ Mit `-fflags +genpts` |
| **Kamera-API** | libcamera (picamera2) | rpicam-vid (native) |
| **Rotation Parameter** | ❌ Nicht vorhanden | ✅ 180° Default |
| **Cinema 4K** | ❌ 1920x1080 | ✅ 4096x2160 |
| **Manual Recording** | ⚠️ Via SSH Commands | ✅ Built-in `--manual-record` |
| **Parameter-Kontrolle** | Minimal | Vollständig (rpicam-vid) |

## 🐛 Known Issues/Limitations

### Watchdog-Modus
- **Status:** Funktional, aber begrenzt
- **Problem:** rpicam-vid kann keine Vorschau parallel zu Aufnahme erzeugen
- **Workaround:** Manual Recording oder Zeitbasierte Scans verwenden

### Performance
- **4K @ 30fps:** CPU ~30-40% (RPi5), RAM ~25%
- **Multi-Camera:** Noch nicht implementiert (nur `--camera 0` oder `--camera 1`)

## 🚀 Installation & Migration

### Von v2.0.2 zu v2.1.0

1. **Update durchführen:**
   ```bash
   git pull origin main
   ```

2. **Dependencies überprüfen:**
   ```bash
   sudo apt install -y rpicam-apps alsa-utils ffmpeg
   pip install --upgrade ultralytics opencv-python
   ```

3. **Test-Aufnahme:**
   ```bash
   cd raspberry-pi-scripts/
   python3 unified-camera-monitor.py --manual-record --recording-duration 5
   ```

4. **Überprüfen:**
   - Video sollte im Ordner erscheinen
   - Audio sollte synchron sein (ffprobe zeigt beide Streams)

### Neu von v2.1.0 aus?

1. Siehe [UNIFIED-MONITOR-README.md](../../raspberry-pi-scripts/UNIFIED-MONITOR-README.md)
2. Oder [unified-monitor-client/SETUP_GUIDE.md](../../unified-monitor-client/SETUP_GUIDE.md)

## 📝 Dokumentation Updates

- ✅ [UNIFIED-MONITOR-README.md](../../raspberry-pi-scripts/UNIFIED-MONITOR-README.md) - Komplett überarbeitet
- ✅ [README.md](../../README.md) - v2.1.0 Highlights
- ✅ [AUDIO-FIX-CHANGELOG.md](../../AUDIO-FIX-CHANGELOG.md) - Audio-Integration Details
- ✅ [raspberry-pi-scripts/](../../raspberry-pi-scripts/) - Veralteute .sh Dateien gelöscht

## 🙏 Thanks To

- **RPi Camera Hardware Team** für exzellente libcamera/rpicam-vid Tools
- **ALSA Community** für robustes Audio-Stack
- **ffmpeg Projekt** für Video-Verarbeitung
- **Ultralytics** für YOLOv8 ✨

## 🔗 Links

- **GitHub Repository:** https://github.com/kamera-linux/vogel-kamera-linux
- **Bug Reports:** https://github.com/kamera-linux/vogel-kamera-linux/issues
- **Pull Requests:** https://github.com/kamera-linux/vogel-kamera-linux/pulls
- **YouTube-Kanal:** https://www.youtube.com/@vogel-kamera-linux

---

**Status:** Stabil & produktionsreif ✅  
**Getestet auf:** Raspberry Pi 5 + Debian Trixie (13)  
**Nächste Version:** v2.2.0 (Web-Dashboard, WebRTC-Stream)
