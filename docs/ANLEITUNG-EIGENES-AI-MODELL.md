# Schritt-für-Schritt Anleitung: Eigenes Vogelarten-AI-Modell erstellen

## 📋 Übersicht

Diese Anleitung führt Sie durch den kompletten Prozess der Erstellung eines eigenen AI-Modells für die Erkennung spezifischer Vogelarten in Ihrem Vogelhaus.

## 🎯 Ziel

- **Eingabe**: Bilder/Videos von Ihrem Vogelhaus
- **Ausgabe**: Präzise Erkennung von 8-15 häufigen Vogelarten
- **Format**: Hailo-optimiertes Modell für Raspberry Pi 5

---

## 📱 Phase 1: Datensammlung (2-4 Wochen)

### 1.1 Bilder sammeln aus Ihrem Vogelhaus

```bash
# Sammeln Sie mindestens 100-200 Bilder pro Vogelart
mkdir -p ~/bird_training_data/{raw_images,annotated_images}
```

**Empfohlene Vogelarten für Deutschland:**
- ✅ **Häufig**: Amsel, Blaumeise, Kohlmeise, Rotkehlchen
- ✅ **Mittelhäufig**: Buchfink, Grünfink, Haussperling, Star  
- ✅ **Optional**: Elster, Rabenkrähe, Eichelhäher, Feldsperling

### 1.2 Automatische Bildextraktion

```python
# extract_frames.py - Frames aus Videos extrahieren
import cv2
import os

def extract_frames(video_path, output_dir, interval=30):
    """Extrahiert alle X Sekunden ein Frame"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval)
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            filename = f"frame_{saved_count:04d}.jpg"
            cv2.imwrite(os.path.join(output_dir, filename), frame)
            saved_count += 1
            
        frame_count += 1
    
    cap.release()
    print(f"Extrahiert: {saved_count} Frames")

# Verwendung
extract_frames("vogelhaus_video.mp4", "raw_images/", interval=10)
```

---

## 🏷️ Phase 2: Annotation (1-2 Wochen)

### 2.1 Annotation-Tool installieren

```bash
# Option A: CVAT (empfohlen für Teams)
# Web-basiert, professionell
# https://cvat.ai/

# Option B: LabelImg (empfohlen für Einzelpersonen)
pip install labelImg
labelImg
```

### 2.2 Annotation durchführen

**Pro Bild annotieren Sie:**
1. **Bounding Box** um jeden Vogel
2. **Klassenlabel** (z.B. "Blaumeise")
3. **Qualitäts-Check**: Sind alle Vögel markiert?

**Annotation-Tipps:**
- ✅ Tight Bounding Boxes (eng um den Vogel)
- ✅ Auch teilweise verdeckte Vögel markieren
- ✅ Bei mehreren Vögeln: jeden einzeln markieren
- ❌ Keine zu kleinen Vögel (< 32x32 Pixel)

### 2.3 Dataset-Struktur erstellen

```bash
bird_dataset/
├── images/
│   ├── train/           # 80% der Bilder
│   └── val/             # 20% der Bilder
├── labels/
│   ├── train/           # YOLO-Format Labels
│   └── val/
└── data.yaml           # Dataset-Konfiguration
```

---

## 🧠 Phase 3: Modell-Training (1-3 Tage)

### 3.1 Training-Umgebung einrichten

```bash
# Python-Umgebung
python3 -m venv bird_training
source bird_training/bin/activate

# YOLOv8 installieren
pip install ultralytics
pip install torch torchvision
```

### 3.2 Dataset-Konfiguration

```yaml
# data.yaml
path: ./bird_dataset
train: images/train
val: images/val

# Anzahl der Klassen
nc: 8

# Klassennamen (anpassen an Ihre Vögel!)
names: 
  0: Amsel
  1: Blaumeise  
  2: Kohlmeise
  3: Rotkehlchen
  4: Buchfink
  5: Grünfink
  6: Haussperling
  7: Star
```

### 3.3 Training-Skript

```python
# train_bird_model.py
from ultralytics import YOLO
import torch

def train_bird_model():
    # GPU prüfen
    print(f"CUDA verfügbar: {torch.cuda.is_available()}")
    
    # Basis-Modell laden (pre-trained)
    model = YOLO('yolov8n.pt')  # nano = schnell, yolov8s.pt = genauer
    
    # Training starten
    results = model.train(
        data='data.yaml',           # Dataset-Konfiguration
        epochs=100,                 # Anzahl Epochen
        imgsz=640,                  # Bildgröße
        batch=16,                   # Batch-Größe (anpassen an RAM)
        device='cpu',               # Oder 'cuda' für GPU
        project='bird_training',     # Ausgabe-Ordner
        name='bird_detector_v1',    # Experiment-Name
        save=True,                  # Modell speichern
        plots=True,                 # Training-Plots erstellen
        val=True,                   # Validierung aktiviert
        patience=20,                # Early stopping
        workers=4                   # Parallel workers
    )
    
    print("Training abgeschlossen!")
    print(f"Bestes Modell: {model.trainer.best}")

if __name__ == "__main__":
    train_bird_model()
```

### 3.4 Training ausführen

```bash
# Training starten (kann 4-24h dauern)
python train_bird_model.py

# Training überwachen
tensorboard --logdir bird_training/bird_detector_v1
```

---

## 🔄 Phase 4: Modell-Konvertierung für Raspberry Pi

### 4.1 Export für Raspberry Pi

```python
# export_model.py
from ultralytics import YOLO

# Trainiertes Modell laden
model = YOLO('bird_training/bird_detector_v1/weights/best.pt')

# Export für verschiedene Formate
model.export(format='onnx')        # ONNX (universell)
model.export(format='tflite')      # TensorFlow Lite
model.export(format='ncnn')        # NCNN (mobil)

print("Export abgeschlossen!")
```

### 4.2 Hailo-Konvertierung (für Raspberry Pi 5 mit Hailo)

```bash
# Hailo AI Suite installieren (auf Development-PC)
# https://hailo.ai/developer-zone/

# ONNX zu Hailo HEF konvertieren
hailo optimize \
  --onnx best.onnx \
  --hw-arch hailo8 \
  --output-dir ./hailo_model/ \
  --batch-size 1

# Quantisierung für bessere Performance
hailo quantize \
  --model-path hailo_model/optimized.har \
  --dataset-path bird_dataset/images/val/ \
  --output-dir ./quantized_model/
```

---

## 🚀 Phase 5: Integration in Ihr System

### 5.1 Modell auf Raspberry Pi kopieren

```bash
# Modell-Dateien übertragen
scp quantized_model/bird_detector.hef pi@raspberry-pi:/usr/share/rpi-camera-assets/
scp bird_inference_config.json pi@raspberry-pi:/usr/share/rpi-camera-assets/
```

### 5.2 Inference-Konfiguration erstellen

```json
{
  "model_name": "bird_species_detector",
  "model_path": "/usr/share/rpi-camera-assets/bird_detector.hef",
  "classes": [
    "Amsel", "Blaumeise", "Kohlmeise", "Rotkehlchen",
    "Buchfink", "Grünfink", "Haussperling", "Star"
  ],
  "confidence_threshold": 0.5,
  "nms_threshold": 0.4,
  "input_size": [640, 640],
  "preprocessing": {
    "normalize": true,
    "mean": [0.485, 0.456, 0.406],
    "std": [0.229, 0.224, 0.225]
  }
}
```

### 5.3 Integration in Ihr Kamera-Skript

```bash
# Mit Ihrem eigenen Modell
python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 \
  --ai-modul on \
  --ai-model custom \
  --ai-model-path /usr/share/rpi-camera-assets/bird_inference_config.json
```

---

## 📊 Phase 6: Testing & Optimierung

### 6.1 Model-Performance testen

```python
# test_model_performance.py
from ultralytics import YOLO
import time

def test_performance():
    model = YOLO('best.pt')
    
    # Test-Bilder
    test_images = ['test1.jpg', 'test2.jpg', 'test3.jpg']
    
    for img in test_images:
        start_time = time.time()
        results = model(img)
        inference_time = time.time() - start_time
        
        print(f"Bild: {img}")
        print(f"Inferenz-Zeit: {inference_time:.3f}s")
        
        # Detektionen anzeigen
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls)
                    conf = float(box.conf)
                    print(f"  Klasse: {model.names[cls]}, Konfidenz: {conf:.2f}")

if __name__ == "__main__":
    test_performance()
```

### 6.2 Optimierungstipps

**Bei schlechter Erkennungsrate:**
- ✅ Mehr Trainingsdaten sammeln
- ✅ Confidence Threshold senken (0.3-0.4)
- ✅ Längeres Training (200+ Epochen)
- ✅ Größeres Modell (yolov8s statt yolov8n)

**Bei langsamer Performance:**
- ✅ Kleineres Modell (yolov8n)
- ✅ Niedrigere Auflösung (320x320)
- ✅ Hailo-Optimierung nutzen

---

## 🛠️ Praktische Hilfsskripte

### 6.3 Automatische Dataset-Aufteilung

```python
# split_dataset.py
import os
import shutil
import random
from pathlib import Path

def split_dataset(image_dir, label_dir, train_ratio=0.8):
    """Teilt Dataset in Training/Validation auf"""
    
    # Alle Bilder finden
    images = list(Path(image_dir).glob('*.jpg'))
    random.shuffle(images)
    
    # Aufteilung berechnen
    train_count = int(len(images) * train_ratio)
    train_images = images[:train_count]
    val_images = images[train_count:]
    
    # Verzeichnisse erstellen
    for split in ['train', 'val']:
        os.makedirs(f'bird_dataset/images/{split}', exist_ok=True)
        os.makedirs(f'bird_dataset/labels/{split}', exist_ok=True)
    
    # Dateien kopieren
    for images_list, split in [(train_images, 'train'), (val_images, 'val')]:
        for img_path in images_list:
            # Bild kopieren
            shutil.copy(img_path, f'bird_dataset/images/{split}/')
            
            # Entsprechendes Label kopieren
            label_path = Path(label_dir) / f"{img_path.stem}.txt"
            if label_path.exists():
                shutil.copy(label_path, f'bird_dataset/labels/{split}/')
    
    print(f"Training: {len(train_images)} Bilder")
    print(f"Validation: {len(val_images)} Bilder")

# Verwendung
split_dataset('annotated_images/', 'annotations/', train_ratio=0.8)
```

---

## 📈 Erwartete Zeitaufwände

| Phase | Zeitaufwand | Aufwand |
|-------|-------------|---------|
| Datensammlung | 2-4 Wochen | ⭐⭐⭐ |
| Annotation | 1-2 Wochen | ⭐⭐⭐⭐ |
| Training | 1-3 Tage | ⭐⭐ |
| Konvertierung | 1-2 Tage | ⭐⭐⭐ |
| Integration | 1 Tag | ⭐ |

**Gesamt: 4-6 Wochen** für ein produktionsreifes Modell

---

## ⚡ Schnellstart-Alternative

Wenn Sie sofort loslegen möchten:

```bash
# 1. Vortrainiertes Basis-Modell verwenden
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# 2. Mit wenigen Bildern (50 pro Klasse) fine-tunen
python train_bird_model.py

# 3. Direkt testen
python3 ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 1 --ai-modul on --ai-model custom --ai-model-path ./best.pt
```

Diese Anleitung führt Sie durch jeden Schritt - von der ersten Bildaufnahme bis zum fertigen AI-Modell! 🐦🤖