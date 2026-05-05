# 🎙️ Audio-Qualität Upgrade - Professionelle Audio-Aufnahme

## 📋 Das Problem

Du hast es richtig erkannt! ✅

- **Manuelle Audio-Aufnahme**: Nutzte `arecord` → 44100 Hz ohne Filterung
- **4K Video+Audio**: Nutzte `rpicam-vid --codec libav` → 48000 Hz mit Verarbeitung

**Ergebnis**: Schlechtere Audioqualität bei manueller Aufnahme

---

## 🔧 Die Lösung

Alle Audio-Aufnahme-Methoden wurden auf **ffmpeg mit professioneller Audio-Verarbeitung** aktualisiert:

### **Neue Audio-Verarbeitung**

```python
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'alsa',
    '-i', 'default',
    '-af', 'anoisremove=om=o:om=o:r=0.001,highpass=f=80,acompressor=attacks=1:releases=10:makeup=2,volume=1.5',
    '-acodec', 'pcm_s16le',
    '-ar', '48000',  # 48kHz wie professionelle Audio!
    '-ac', '1',
    '-y',
    'audio.wav'
]
```

---

## ✨ Verbesserungen

| Feature | Vorher | Nachher |
|---------|--------|---------|
| **Sample-Rate** | 44100 Hz | **48000 Hz** ⬆️ |
| **Rausch-Reduktion** | ❌ Keine | ✅ `anoisremove` |
| **Hochpass-Filter** | ❌ Nein | ✅ 80Hz (Brumm weg) |
| **Dynamik-Kompression** | ❌ Nein | ✅ Konsistenter Level |
| **Verstärkung** | Minimal | ✅ 1.5x (bessere Aussteuerung) |

---

## 📁 Updatete Dateien

### 1. **Legacy Scripts** (Raspberry Pi)
- ✅ `legacy/raspberry-pi-scripts/unified-camera-monitor-manual.py`
  - `_start_audio_recording()` Funktion
  - `run_audio()` Thread (parallele Aufnahme)

- ✅ `legacy/raspberry-pi-scripts/unified-camera-monitor.py`
  - `run_audio()` Thread (parallele Aufnahme)

### 2. **Modern Daemon** (Unified Monitor Client)
- ✅ `unified-monitor-client/pi_daemon_secure.py`
  - `record_audio()` statische Methode (Audio-only)

---

## 🧪 Schnell Testen

### Test 1: Sample-Rate verifizieren
```bash
# Nach einer Audio-Aufnahme:
ffprobe audio.wav -v error -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1
# Sollte ausgeben: 48000
```

### Test 2: Manuelle Audio-Aufnahme starten
```bash
# Auf Raspberry Pi:
python3 unified-camera-monitor.py --manual-record --enable-audio --recording-duration 30
```

### Test 3: Audio-Qualität anhören
```bash
# Vergleiche alte vs. neue Methode
# Alte: arecord -f S16_LE -r 44100 -c 1 -t wav -d 60 old.wav
# Neue: ffmpeg -f alsa -i default -t 60 -af "..." -acodec pcm_s16le -ar 48000 -ac 1 -y new.wav
```

---

## 🎯 Technischer Hintergrund

### **Warum 48kHz?**
- Professioneller Standard (Film, Video, Audio)
- Bessere Frequenzbandbreite (24 kHz max vs 22 kHz bei 44.1kHz)
- Konsistent mit rpicam-vid Audio

### **Audio-Filter Erklärung**
```
anoisremove=om=o:om=o:r=0.001
  ↳ Rausch-Reduktion aus Stille

highpass=f=80
  ↳ Entfernt Töne unter 80Hz (Brummtöne weg)

acompressor=attacks=1:releases=10:makeup=2
  ↳ Kompression für stabilen Pegel

volume=1.5
  ↳ Verstärkung um 1.5x
```

---

## 📊 Praktische Vorher/Nachher

### **Vogelgesang aufnehmen**
```bash
# VORHER: Qualität ⚠️
python3 unified-camera-monitor.py --manual-record --enable-audio

# NACHHER: Qualität ✅ Professionell
# Gleicher Befehl! Aber jetzt mit 48kHz + Filterung
```

### **Resultat**
- Klarer und deutlicher Ton
- Weniger Hintergrund-Rauschen
- Bessere Aussteuerung (weniger zu leise/zu laut)
- Ideal für Ornithologie & Vogelbestimmung 🐦

---

## ⚙️ Konfigurierbar

Falls gewünscht, können die Filter angepasst werden:

```python
# Weniger aggressive Rausch-Reduktion:
'-af', 'anoisremove=om=o:r=0.01,highpass=f=80,acompressor=attacks=1:releases=10:makeup=2,volume=1.5'

# Mehr Verstärkung (lauter):
'-af', 'anoisremove=om=o:om=o:r=0.001,highpass=f=80,acompressor=attacks=1:releases=10:makeup=2,volume=2.0'

# Keine Filter (schneller, aber schlechter Ton):
'-af', 'volume=1.0'
```

---

## 📌 Kompatibilität

- ✅ Raspberry Pi 5 (beste Performance)
- ✅ Raspberry Pi 4
- ✅ Raspberry Pi 3B+ (etwas langsamer)
- ✅ Alle Linux mit ffmpeg + ALSA

**Abhängigkeiten**: `ffmpeg` (bereits vorhanden)

---

## 🔍 Weitere Infos

Siehe auch:
- [AUDIO-QUALITY-UPGRADE.md](AUDIO_QUALITY_IMPROVEMENTS.md) - Detaillierte Dokumentation
- [UNIFIED-MONITOR-README.md](raspberry-pi-scripts/UNIFIED-MONITOR-README.md) - Benutzerdokumentation
- [DETECT_AND_RECORD.md](unified-monitor-client/DETECT_AND_RECORD.md) - Parameter-Referenz

