# 🐍 Python Toolbox

Python-basierte Tools und Packages für das vogel-kamera-linux Projekt.

## 📦 Verfügbare Tools

### 🔍 Vogel Video Analyzer

YOLOv8-basiertes Tool zur automatischen Analyse von Video-Aufnahmen auf Vogelinhalte.

**Git Submodule:** Dieses Verzeichnis enthält `vogel-video-analyzer` als Git Submodule.

**Standalone Package:** Das Tool ist auch als separates PyPI-Package verfügbar:
- **PyPI:** https://pypi.org/project/vogel-video-analyzer/ *(coming soon)*
- **GitHub:** https://github.com/kamera-linux/vogel-video-analyzer
- **Dokumentation:** [vogel-video-analyzer/README.md](vogel-video-analyzer/README.md)

---

## 🚀 Installation

### Option 1: PyPI Package (Empfohlen für Endnutzer)

```bash
# Einfache Installation via pip
pip install vogel-video-analyzer

# Verwendung
vogel-analyze video.mp4
```

### Option 2: Git Submodule (Für Entwickler)

```bash
# Repository mit Submodules clonen
git clone --recursive https://github.com/kamera-linux/vogel-kamera-linux.git

# Oder Submodules nachträglich initialisieren
git submodule update --init --recursive

# Dependencies installieren
pip install -r python-toolbox/requirements.txt

# Verwendung
python -m vogel_video_analyzer video.mp4
# oder direkt aus dem Submodule:
cd python-toolbox/vogel-video-analyzer
python -m src.vogel_video_analyzer video.mp4
```

### Option 3: Direkte Dependencies (Ohne PyPI)

Falls `vogel-video-analyzer` noch nicht auf PyPI ist:

```bash
# Nur die direkten Dependencies installieren
pip install opencv-python>=4.8.0 ultralytics>=8.0.0 numpy>=1.24.0

# Tool direkt aus Submodule nutzen
cd python-toolbox/vogel-video-analyzer
python src/vogel_video_analyzer/cli.py video.mp4
```

---

## 📖 Verwendung

### Basis-Analyse
```bash
# Mit PyPI Package
vogel-analyze video.mp4

# Mit Submodule
python -m vogel_video_analyzer video.mp4
```

### Erweiterte Optionen
```bash
# Schnellere Analyse (jeden 10. Frame)
vogel-analyze --sample-rate 10 video.mp4

# Custom Threshold
vogel-analyze --threshold 0.4 video.mp4

# JSON Export
vogel-analyze --output report.json video.mp4

# Auto-Delete für 0% Bird Content
vogel-analyze --delete --sample-rate 5 *.mp4
```

---

## 🔄 Submodule Updates

```bash
# Submodule auf neueste Version aktualisieren
cd python-toolbox/vogel-video-analyzer
git pull origin main

# Oder aus Root:
git submodule update --remote python-toolbox/vogel-video-analyzer
```

---

## 📚 Weitere Informationen

- **Video-Analyse-Tool Dokumentation:** [vogel-video-analyzer/README.md](vogel-video-analyzer/README.md)
- **Hauptprojekt:** [../README.md](../README.md)
- **PyPI Package:** https://pypi.org/project/vogel-video-analyzer/ *(coming soon)*

---

## 🤝 Contributing

Contributions zum Video-Analyzer bitte im separaten Repository:
- https://github.com/kamera-linux/vogel-video-analyzer

Für Verbesserungen an der Integration hier:
- https://github.com/kamera-linux/vogel-kamera-linux
