# AI-Training-Tools für Vogelarten-Erkennung

Dieses Verzeichnis enthält alle Tools zum Erstellen Ihres eigenen AI-Modells für die Erkennung spezifischer Vogelarten.

## 🚀 Schnellstart

```bash
# 1. Setup (einmalig)
python3 setup_ai_training.py

# 2. Frames aus Videos extrahieren  
python3 extract_frames.py video.mp4 frames/ --interval 10

# 3. Dataset aufteilen (nach Annotation)
python3 split_dataset.py images/ labels/ bird_dataset/

# 4. Training starten
python3 train_bird_model.py bird_dataset/data.yaml
```

## 📁 Enthaltene Tools

### `setup_ai_training.py`
**Zweck**: Installiert alle benötigten Python-Pakete für das AI-Training

**Verwendung**:
```bash
# Standard-Installation
python3 setup_ai_training.py

# Mit Virtual Environment
python3 setup_ai_training.py --venv

# Nur Import-Tests
python3 setup_ai_training.py --test-only
```

**Installiert**:
- PyTorch (Deep Learning)
- YOLOv8/Ultralytics
- OpenCV (Computer Vision)  
- PyYAML, NumPy, Matplotlib

---

### `extract_frames.py`
**Zweck**: Extrahiert Einzelbilder aus Vogelhaus-Videos für Training-Daten

**Verwendung**:
```bash
# Einzelnes Video, alle 10 Sekunden ein Frame
python3 extract_frames.py video.mp4 output_frames/ --interval 10

# Alle Videos in einem Ordner
python3 extract_frames.py videos/ frames/ --batch --interval 5 --max-frames 100

# Hochfrequente Extraktion für Action-Szenen
python3 extract_frames.py feeding_time.mp4 frames/ --interval 1 --max-frames 200
```

**Optionen**:
- `--interval`: Sekunden zwischen Frames (default: 30)
- `--max-frames`: Maximum Anzahl Frames pro Video
- `--batch`: Verarbeite alle Videos im Verzeichnis

---

### `split_dataset.py`  
**Zweck**: Teilt annotierte Bilder in Training/Validation Sets auf

**Verwendung**:
```bash
# Standard-Aufteilung 80/20
python3 split_dataset.py images/ labels/ bird_dataset/

# Custom-Aufteilung 70/30
python3 split_dataset.py images/ labels/ bird_dataset/ --train-ratio 0.7 --val-ratio 0.3

# Dataset nur analysieren
python3 split_dataset.py images/ labels/ --analyze-only
```

**Erstellt**:
- `bird_dataset/images/train/` - Training-Bilder
- `bird_dataset/images/val/` - Validation-Bilder  
- `bird_dataset/labels/train/` - Training-Labels
- `bird_dataset/labels/val/` - Validation-Labels
- `bird_dataset/data.yaml` - YOLO-Konfiguration

---

### `train_bird_model.py`
**Zweck**: Trainiert YOLOv8-Modell für Vogelarten-Erkennung

**Verwendung**:
```bash
# Standard-Training
python3 train_bird_model.py bird_dataset/data.yaml

# Schnelles Test-Training
python3 train_bird_model.py data.yaml --epochs 50 --model-size n

# High-Quality Training
python3 train_bird_model.py data.yaml --epochs 200 --model-size s --batch-size 8

# Nur Requirements prüfen
python3 train_bird_model.py data.yaml --check-only
```

**Modell-Größen**:
- `n` (nano): Schnell, weniger genau (~6MB)
- `s` (small): Ausgewogen (~22MB)
- `m` (medium): Genauer, langsamer (~50MB)
- `l` (large): Sehr genau (~87MB)

## 📋 Workflow: Von Video zu AI-Modell

### Phase 1: Datensammlung (2-4 Wochen)

```bash
# 1. Videos aus Ihrem Vogelhaus sammeln
mkdir -p raw_videos/

# 2. Frames extrahieren (alle 10-30 Sekunden)
python3 extract_frames.py raw_videos/ raw_frames/ --batch --interval 15

# Ziel: 100-200 Bilder pro Vogelart
```

### Phase 2: Annotation (1-2 Wochen)

```bash
# 1. Annotation-Tool installieren
pip install labelImg

# 2. Bilder annotieren
labelImg raw_frames/

# 3. Annotierte Daten organisieren
mkdir -p annotated_data/{images,labels}
# Bilder nach annotated_data/images/, Labels nach annotated_data/labels/
```

### Phase 3: Dataset-Vorbereitung

```bash
# 1. Dataset aufteilen
python3 split_dataset.py annotated_data/images/ annotated_data/labels/ bird_dataset/

# 2. data.yaml anpassen
nano bird_dataset/data.yaml
# Klassennamen an Ihre Vögel anpassen!
```

### Phase 4: Training

```bash
# 1. Requirements installieren
python3 setup_ai_training.py

# 2. Training starten (kann 4-24h dauern)
python3 train_bird_model.py bird_dataset/data.yaml --epochs 100

# 3. Training überwachen
tensorboard --logdir bird_training/
```

### Phase 5: Integration

```bash
# Trainiertes Modell verwenden
python3 ../python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model custom \
  --ai-model-path ./bird_training/bird_detector_*/weights/best.pt
```

## 🎯 Empfohlene Vogelarten für Deutschland

**Häufige Gartenvögel** (hohe Erkennungsrate zu erwarten):
- ✅ **Amsel** - Groß, markant, häufig
- ✅ **Blaumeise** - Klein, charakteristische Farben
- ✅ **Kohlmeise** - Größte Meise, gut erkennbar
- ✅ **Rotkehlchen** - Markante rote Brust

**Mittelhäufige Arten**:
- 🟡 **Buchfink** - Männchen farbig, Weibchen unauffällig  
- 🟡 **Grünfink** - Grünliche Färbung
- 🟡 **Haussperling** - Braun-grau, häufig in Gruppen
- 🟡 **Star** - Schillerndes Gefieder

**Schwierigere Arten** (ähnlich aussehend):
- 🔴 **Feldsperling vs Haussperling** - Sehr ähnlich
- 🔴 **Verschiedene Finken** - Schwer unterscheidbar
- 🔴 **Jungvögel** - Andere Färbung als adulte Tiere

## 💡 Performance-Tipps

### Für bessere Erkennungsrate:
- ✅ Mindestens 100 Bilder pro Art sammeln
- ✅ Verschiedene Posen, Blickwinkel, Lichtverhältnisse
- ✅ Tight Bounding Boxes (eng um den Vogel)
- ✅ Auch teilweise verdeckte Vögel annotieren

### Für schnellere Inference:
- ⚡ Nano-Modell verwenden (`--model-size n`)
- ⚡ Niedrigere Auflösung (`--imgsz 320`)
- ⚡ ROI verwenden (`--roi x,y,w,h` im Kamera-Skript)

### Für höhere Genauigkeit:
- 🎯 Mehr Trainingsdaten sammeln
- 🎯 Längeres Training (`--epochs 200`)
- 🎯 Größeres Modell (`--model-size s`)
- 🎯 Data Augmentation aktiviert (automatisch in YOLOv8)

## 🔧 Troubleshooting

### Import-Fehler
```bash
# Prüfen Sie die Installation
python3 setup_ai_training.py --test-only

# Manual installation
pip install torch torchvision ultralytics opencv-python
```

### Wenig Trainingsdaten
```bash
# Mehr Frames extrahieren
python3 extract_frames.py video.mp4 frames/ --interval 5

# Data Augmentation wird automatisch von YOLOv8 verwendet
```

### Langsames Training
```bash
# GPU-Beschleunigung prüfen
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Kleineres Modell verwenden
python3 train_bird_model.py data.yaml --model-size n --batch-size 32
```

### Schlechte Erkennungsrate
```bash
# Confidence-Threshold senken im Kamera-Skript
# Mehr Trainingsdaten sammeln
# Längeres Training mit größerem Modell
```

## 📚 Weiterführende Ressourcen

- **Vollständige Anleitung**: `../ANLEITUNG-EIGENES-AI-MODELL.md`
- **YOLOv8 Dokumentation**: https://docs.ultralytics.com/
- **Annotation-Tools**: https://github.com/heartexlabs/labelImg
- **Vogelarten-Datenbanken**: eBird, iNaturalist, NABU

## ⏱️ Erwarteter Zeitaufwand

| Phase | Dauer | Aufwand |
|-------|-------|---------|
| Setup | 1-2 Stunden | ⭐ |
| Datensammlung | 2-4 Wochen | ⭐⭐⭐ |
| Annotation | 1-2 Wochen | ⭐⭐⭐⭐ |
| Training | 1-3 Tage | ⭐⭐ |
| Integration | 1 Tag | ⭐ |

**Gesamt**: 4-6 Wochen für produktionsreifes Modell