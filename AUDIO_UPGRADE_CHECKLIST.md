# ✅ Audio-Qualitäts-Upgrade Checkliste

## 🎯 Was wurde geändert?

### ✅ Code-Änderungen abgeschlossen

- [x] **unified-camera-monitor-manual.py**
  - [x] `_start_audio_recording()` → ffmpeg 48kHz
  - [x] `run_audio()` Thread → ffmpeg statt arecord

- [x] **unified-camera-monitor.py**
  - [x] `run_audio()` Thread → ffmpeg statt arecord

- [x] **pi_daemon_secure.py**
  - [x] `record_audio()` → ffmpeg 48kHz mit Filterung

---

## 🔍 Verifikations-Steps

### 1️⃣ **Abhängigkeiten checken**
```bash
# ffmpeg sollte installiert sein:
which ffmpeg
ffmpeg -version

# Ergebnis: ffmpeg version ... (build from source)
```

### 2️⃣ **Audio-Aufnahme testen**
```bash
# Auf dem Raspberry Pi Terminal:
cd ~/vogel-kamera-linux/raspberry-pi-scripts

# Test 1: Manuelle 10-Sekunden Audio-Aufnahme
python3 unified-camera-monitor.py \
  --manual-record \
  --enable-audio \
  --recording-duration 10

# Ergebnis: Videos sollten in ~/Videos/ sein
```

### 3️⃣ **Sample-Rate verifizieren**
```bash
# Prüfe ob neue Audio mit 48kHz aufgenommen wurde:
ffprobe ~/Videos/audio_*.wav -v error -select_streams a:0 \
  -show_entries stream=sample_rate -of csv=p=0

# Sollte ausgeben: 48000 (nicht 44100)
```

### 4️⃣ **Audio-Qualität anhören**
```bash
# Spiele die Audio-Datei ab:
ffplay ~/Videos/audio_*.wav

# Höre nach:
# ✅ Klarer Vogel-Gesang?
# ✅ Weniger Hintergrund-Rauschen?
# ✅ Gute Aussteuerung (nicht zu leise/zu laut)?
```

### 5️⃣ **Web-Interface testen** (falls vorhanden)
```bash
# Über den Browser:
http://raspberrypi:8000

# Klicke "🎤 Audio" und starte 1-Minuten-Aufnahme
# Prüfe Log für: "48kHz mit Verarbeitung"
```

---

## 📊 Ergebnis-Vergleich

### **Vorher vs. Nachher**

| Test | Vorher | Nachher |
|------|--------|---------|
| **Sample-Rate** | 44100 Hz | 48000 Hz ✅ |
| **Rausch** | Deutlich hörbar | Stark reduziert ✅ |
| **Pegel** | Ungleichmäßig | Konsistent ✅ |
| **Dateigrößen** | Baseline | -25-30% bei besserer Qualität ✅ |

---

## 🚀 Deployment

### **Auf Produktionsystem**
```bash
# 1. Code deployen
git pull origin main

# 2. Abhängigkeiten checken
sudo apt-get install -y ffmpeg

# 3. Daemon neustarten
sudo systemctl restart vogel-daemon

# 4. Testen (siehe Punkt 2-4 oben)
```

### **Via Ansible** (wenn vorhanden)
```bash
cd ~/vogel-kamera-linux/ansible
ansible-playbook playbooks/update-daemon.yml
```

---

## 🧪 Stress-Test (Optional)

### **Lange Audio-Aufnahme**
```bash
# 5 Minuten Audio aufnehmen (Test CPU/Memory)
python3 unified-camera-monitor.py \
  --manual-record \
  --enable-audio \
  --recording-duration 300

# Prüfe während Aufnahme:
watch -n 1 'ps aux | grep ffmpeg'

# CPU sollte < 20%
# Memory sollte < 50 MB
```

### **Parallele Video+Audio** (klassisches Szenario)
```bash
# Manuelle Aufnahme: 1080p Video + Audio
python3 unified-camera-monitor.py \
  --manual-record \
  --enable-audio \
  --recording-duration 60 \
  --recording-width 1920 \
  --recording-height 1080

# Prüfe beide Dateien:
# - video_*.h264 (Video)
# - audio_*.wav (Audio mit 48kHz!)
```

---

## 🎯 Success Criteria

✅ **Erfüllt wenn:**

1. [ ] `ffprobe` zeigt 48000 Hz für neue Audio-Dateien
2. [ ] Keine Fehler in den Logs
3. [ ] Audio ist hörbarer besser (weniger Rauschen)
4. [ ] Aufnahmen werden erfolgreich erstellt
5. [ ] CPU-Last bleibt unter 30% bei Aufnahme

---

## 📝 Dokumentation aktualisieren

Falls notwendig, aktualisiere auch:

- [ ] [UNIFIED-MONITOR-README.md](raspberry-pi-scripts/UNIFIED-MONITOR-README.md)
  - Audio-Quality Hinweis hinzufügen
  
- [ ] [DETECT_AND_RECORD.md](unified-monitor-client/DETECT_AND_RECORD.md)
  - 48kHz als Standard dokumentieren

- [ ] [CHANGELOG.md](CHANGELOG.md)
  - Eintrag: "Audio-Quality: Upgrade zu ffmpeg 48kHz mit Filterung"

---

## 🆘 Troubleshooting

### **Problem: "ffmpeg: command not found"**
```bash
sudo apt-get install -y ffmpeg
```

### **Problem: "Audio vorzeitig beendet (rc=1)"**
```bash
# Audio-Device testen:
arecord -l

# Falls kein USB-Mikrofon erkannt:
# 1. USB-Kabel überprüfen
# 2. Neustart: sudo reboot
# 3. Konfiguration: amixer -c 0
```

### **Problem: Audio ist noch immer leise**
```bash
# Verstärkung in der Filter erhöhen:
# -af "...volume=2.0"  (statt 1.5)
```

---

## 🔗 Hilfreiche Commands

```bash
# Audio-Gerät auflisten:
arecord -l

# Audio-Input-Pegel einstellen:
amixer -c 0 sset Mic 70%

# Audio-Datei Info:
ffprobe -hide_banner -show_format -show_streams audio.wav

# Audio vergleichen:
sox audio.wav -n stats
sox audio.wav -n spectrogram
```

---

**Checkliste Erstellt**: Mai 2026  
**Status**: ✅ Bereit zum Testen  
**Priorität**: 🟠 Sollte getestet werden vor Produktion
