# 📦 Release v1.3.2

**Veröffentlichungsdatum:** 6. Januar 2025  
**Vorgängerversion:** [v1.3.1](RELEASE_NOTES_v1.3.1.md)

## 🎯 Überblick

Diese Version führt ein neues **Video-Analyse-Tool** ein, das aufgezeichnete Videos automatisch auf Vogelinhalte analysiert und detaillierte Statistiken liefert.

---

## ✨ Neue Features

### 🔍 Video-Analyse-Tool (`tools/analyze_video_bird_content.py`)

Ein leistungsfähiges Tool zur Nachbearbeitung von Video-Aufnahmen:

**Hauptfunktionen:**
- **YOLOv8 KI-Analyse:** Automatische Vogelerkennung in Videos
- **Segment-Erkennung:** Findet zusammenhängende Zeitabschnitte mit Vogel-Präsenz
- **Konfigurierbare Sample-Rate:** Analysiert jeden n-ten Frame (Standard: 5)
- **JSON-Export:** Detaillierte Statistiken und Zeitstempel
- **Auto-Delete:** Entfernt Videos ohne Vogelinhalt (0% Bird Content)
- **Logging:** Strukturierte Logs in `/var/log/vogel-kamera-linux/`

**Verwendung:**
```bash
# Einzelnes Video analysieren
python tools/analyze_video_bird_content.py video.mp4

# Mit angepasster Sample-Rate (jeden 10. Frame)
python tools/analyze_video_bird_content.py video.mp4 --sample-rate 10

# JSON-Export mit Auto-Delete
python tools/analyze_video_bird_content.py video.mp4 --output report.json --delete

# Verzeichnis analysieren
for video in /media/extern/aufnahmen/2025/KW01/*.mp4; do
    python tools/analyze_video_bird_content.py "$video" --sample-rate 5 --delete
done
```

**Ausgabe-Beispiel:**
```
🎬 Video Analysis Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 File: /media/extern/aufnahmen/2025/KW01/20250106_141523_vogel.mp4
📊 Total Frames: 450 (analyzed: 90)
⏱️  Duration: 15.0 seconds
🐦 Bird Frames: 72 (80.0%)
🎯 Bird Segments: 2

📍 Detected Segments:
  ┌ Segment 1: 00:00:02 - 00:00:08 (72% bird frames)
  └ Segment 2: 00:00:11 - 00:00:14 (89% bird frames)

✅ Status: Significant bird activity detected
```

**Model-Suche:**
1. `models/yolov8n.pt` (lokales Verzeichnis)
2. `config/models/yolov8n.pt` (Konfigurations-Verzeichnis)
3. Automatischer Download von Ultralytics (Fallback)

---

## 📦 Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `tools/analyze_video_bird_content.py` | Video-Analyse-Tool (496 Zeilen) |
| `tools/requirements.txt` | Python-Dependencies für Tools |
| `tools/README.md` | Dokumentation für Tools-Verzeichnis |

---

## 🔧 Dependencies

**Neue Anforderungen für `tools/`:**
```txt
opencv-python>=4.8.0
ultralytics>=8.0.0
numpy>=1.24.0
```

**Installation:**
```bash
pip install -r tools/requirements.txt
```

---

## 🐛 Behobene Probleme

- **Emoji-Korrekturen:** Defekte Emojis in `tools/README.md` behoben

---

## 📚 Dokumentation

- **tools/README.md:** Vollständige Dokumentation des Video-Analyse-Tools
- **Kommandozeilen-Hilfe:** `python tools/analyze_video_bird_content.py --help`

---

## 🔄 Migration von v1.3.1

Keine Breaking Changes. Einfach die neuen Dependencies installieren:

```bash
# Tools-Dependencies installieren
pip install -r tools/requirements.txt

# Video-Analyse testen
python tools/analyze_video_bird_content.py /pfad/zu/video.mp4
```

---

## 🎯 Anwendungsbeispiele

### 1️⃣ Batch-Analyse mit Auto-Delete
```bash
# Alle Videos eines Tages analysieren und leere Videos löschen
for video in /media/extern/aufnahmen/2025/KW01/*.mp4; do
    python tools/analyze_video_bird_content.py "$video" \
        --sample-rate 5 \
        --threshold 0.3 \
        --delete \
        --log
done
```

### 2️⃣ JSON-Berichte für Archivierung
```bash
# Detaillierte Berichte für alle Videos erstellen
python tools/analyze_video_bird_content.py video.mp4 \
    --output analysis_report.json \
    --log
```

### 3️⃣ Qualitätskontrolle nach Aufnahme
```bash
# Prüfen, ob Aufnahmen Vogelinhalt haben
python tools/analyze_video_bird_content.py latest_recording.mp4 \
    --threshold 0.5 \
    --delete
```

---

## 🔍 Technische Details

**Architektur:**
- **VideoAnalyzer Class:** Hauptklasse mit YOLOv8-Integration
- **analyze_video():** Frame-by-Frame Analyse mit konfigurierbarer Sample-Rate
- **_find_bird_segments():** Segment-Erkennung mit Lücken-Toleranz
- **print_report():** Formatierte Terminal-Ausgabe mit Emojis
- **save_report():** JSON-Export mit detaillierten Statistiken

**Performance:**
- Sample-Rate 5: ~20% der Frames analysiert (5x schneller)
- Sample-Rate 10: ~10% der Frames analysiert (10x schneller)
- Empfehlung: Sample-Rate 5-10 für 30fps Videos

---

## 🚀 Nächste Schritte

### Option 1: PyPI Package (Empfohlen)
```bash
# Sobald auf PyPI verfügbar:
pip install vogel-video-analyzer
vogel-analyze /pfad/zu/video.mp4
```

### Option 2: Git Submodule (Entwickler)
```bash
# Repository mit Submodules clonen
git clone --recursive https://github.com/kamera-linux/vogel-kamera-linux.git

# Oder Submodules nachträglich initialisieren
git submodule update --init --recursive

# Dependencies installieren
pip install -r python-toolbox/requirements.txt

# Video-Analyse nutzen
python -m vogel_video_analyzer /pfad/zu/video.mp4
```

Weitere Informationen: [python-toolbox/README.md](../python-toolbox/README.md)

---

## 🙏 Danksagungen

- **Ultralytics YOLOv8:** Leistungsfähige Objekterkennung
- **OpenCV:** Video-Processing Framework

---

**📥 Download:** [v1.3.2 Release auf GitHub](https://github.com/kamera-linux/vogel-kamera-linux/releases/tag/v1.3.2)

**🐛 Probleme melden:** [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)

**📖 Vollständige Dokumentation:** [README.md](../README.md)
