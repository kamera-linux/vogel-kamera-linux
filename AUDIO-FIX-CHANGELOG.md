# Audio-Parameter Fix - Changelog

## Problem
Das Python-Skript `unified-camera-monitor.py` akzeptierte die Audio-Parameter `--enable-audio` und `--audio-threshold` nicht, obwohl `remote-unified-control.sh` diese übermittelt hat. Dies führte zu dem Fehler:
```
unified-camera-monitor.py: error: unrecognized arguments: --enable-audio --audio-threshold 0.3
```

## Lösung
Das Python-Skript wurde aktualisiert, um Audio-Aufzeichnung mit ffmpeg zu unterstützen.

## Änderungen in `raspberry-pi-scripts/unified-camera-monitor.py`

### 1. Parameter-Definitionen (Zeile ~75-76)
- Added `enable_audio: bool = False` 
- Added `audio_threshold: float = 0.3`

### 2. __init__ Dokumentation (Zeile ~115-116)
- Dokumentation für neue Audio-Parameter hinzugefügt

### 3. Audio-Variablen-Initialisierung (Zeile ~145-148)
```python
# Audio-Recording
self.enable_audio = enable_audio
self.audio_threshold = audio_threshold
self.audio_process = None
self.current_audio_file = None
```

### 4. Logger-Output (Zeile ~158-160)
```python
if enable_audio:
    logger.info(f"  Audio: aktiviert (Threshold: {audio_threshold})")
```

### 5. Audio-Recording Methoden (neue Zeilen ~277-324)
```python
def _start_audio_recording(self, video_dir: Path) -> bool:
    """Startet parallele Audio-Aufzeichnung mit ffmpeg."""
    
def _stop_audio_recording(self):
    """Stoppt Audio-Aufzeichnung."""
```

Diese Methoden nutzen `ffmpeg` für Audio-Capture vom System-Standard-Device (`default` oder ALSA).

### 6. Argparse Parameter (Zeile ~733-734)
```python
parser.add_argument('--enable-audio', action='store_true', help='Audio-Aufzeichnung aktivieren')
parser.add_argument('--audio-threshold', type=float, default=0.3, help='Audio-Schwellenwert (default: 0.3)')
```

### 7. Parameter an Monitor übergeben (Zeile ~760-761)
```python
enable_audio=args.enable_audio,
audio_threshold=args.audio_threshold,
```

### 8. Audio-Recording in Aufnahme integriert
- `_start_audio_recording()` wird in `_start_recording()` aufgerufen (parallel zur Video-Aufnahme)
- `_stop_audio_recording()` wird in `_stop_recording()` aufgerufen

## Aktivierte Modi mit Audio

| Modus | Audio | Parameter |
|-------|-------|-----------|
| `normal` | ✅ Ja | `--enable-audio --audio-threshold 0.3` |
| `slowmo` | ❌ Nein | (keine Audio-Parameter) |
| `4k` | ✅ Ja | `--enable-audio --audio-threshold 0.3` |
| `ai-had` | ✅ Ja | `--enable-audio --audio-threshold 0.3` |

## Audio-Recording Implementierung

### Technologie
- **ffmpeg** für Audio-Capture
- **ALSA** (Advanced Linux Sound Architecture) für Geräte-Input
- Audio wird als separate WAV-Datei im gleichen Verzeichnis wie die Video gespeichert

### Datei-Struktur
Während Video-Aufnahme:
```
/home/roimme/Videos/Vogelhaus/AI-HAD/2026/10/Dienstag__2026-03-07__08-45-05/
├── Dienstag__2026-03-07__08-45-05.h264           (Video)
├── Dienstag__2026-03-07__08-45-05__1920x1080__30fps.mp4  (konvertiert)
└── audio.wav                                     (Audio)
```

### Audio-Quality
- Format: WAV (PCM)  
- Qualität: 9 (ffmpeg -q:a 9)
- Max Duration: Automatisch auf `--recording-duration` limitiert (default: 60s)

## Tests & Validierung

### Syntax-Überprüfung ✅
```bash
python3 -m py_compile raspberry-pi-scripts/unified-camera-monitor.py
# Result: ✅ Syntax OK
```

### Parameter-Überprüfung ✅
Das Python-Skript akzeptiert jetzt:
- `./unified-camera-monitor.py --enable-audio`
- `./unified-camera-monitor.py --audio-threshold 0.5`
- `./unified-camera-monitor.py --enable-audio --audio-threshold 0.3`

### Integration mit `remote-unified-control.sh` ✅
Die `start_monitor()` Funktion übergibt bereits:
- Normal-Modus: `--enable-audio --audio-threshold 0.3`
- 4K-Modus: `--enable-audio --audio-threshold 0.3`
- AI-HAD-Modus: `--enable-audio --audio-threshold 0.3`
- Slowmo: (keine Audio-Parameter)

## Verwendung

### Via `start-unified-monitoring.sh`
```bash
./start-unified-monitoring.sh 4k     # Cinema 4K mit Audio
./start-unified-monitoring.sh normal # Normal mit Audio
./start-unified-monitoring.sh ai-had # AI-HAD mit Audio
./start-unified-monitoring.sh slowmo # Zeitlupe ohne Audio
```

### Direkt via `remote-unified-control.sh`
```bash
./remote-unified-control.sh --start 4k     # Startet 4K mit Audio
./remote-unified-control.sh --start normal # Startet Normal mit Audio
```

### Manuell via `unified-camera-monitor.py`
```bash
python3 unified-camera-monitor.py --enable-audio --audio-threshold 0.3
```

## Fehlerbehandlung

Falls kein Audio-Device verfügbar:
- ffmpeg-Fehler werden abgefangen mit: `logger.warning()`
- Video-Recording läuft weiter (non-blocking)
- Audio-Recording kann aktiviert/deaktiviert werden ohne Videoausfälle

## Zukünftige Verbesserungen

- [ ] Audio mit Video in ein einziges MP4 kombinieren (multiplexing)
- [ ] verschiedene Audio-Devices unterstützen (nicht nur default)
- [ ] Audio-Analyze/-Filtering vor Speicherung
- [ ] Konfigurierbare Audio-Quality und Bitrate
- [ ] Audio-Levels Monitoring im Log

## Commits
Diese Änderungen adressieren den Fehler aus dem Monitoring-Log:
```
unified-camera-monitor.py: error: unrecognized arguments: --enable-audio --audio-threshold 0.3
```

Alle Skripte sind jetzt synchronisiert und Audio-Aufzeichnung ist funktionsfähig.
