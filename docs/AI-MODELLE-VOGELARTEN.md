# AI-Modell Konfiguration für Vogelarten-Erkennung

## Verfügbare AI-Modelle

### 1. Standard YOLOv8 (allgemeine Objekterkennung)
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model yolov8
```
- **Erkennt**: Allgemeine Objekte inkl. "bird" (Vogel)
- **Datei**: `/usr/share/rpi-camera-assets/hailo_yolov8_inference.json`

### 2. Vogelarten-spezifisches Modell (experimentell)
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model bird-species
```
- **Erkennt**: Verschiedene Vogelarten (wenn verfügbar)
- **Datei**: `/usr/share/rpi-camera-assets/hailo_bird_species_inference.json`

### 3. Benutzerdefiniertes Modell
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model custom \
  --ai-model-path /path/to/your/custom_bird_model.json
```

## Vogelarten-Modelle einrichten

### Option 1: Existierende Modelle finden
Prüfen Sie verfügbare Hailo-Modelle auf Ihrem Raspberry Pi:

```bash
# Auf dem Raspberry Pi ausführen
ls -la /usr/share/rpi-camera-assets/
find /usr/share/rpi-camera-assets/ -name "*bird*" -o -name "*aves*"

# Prüfen Sie auch andere Verzeichnisse
find /opt -name "*bird*" -o -name "*aves*" 2>/dev/null
```

### Option 2: Eigenes Vogelarten-Modell trainieren

1. **Dataset vorbereiten**:
   - Sammeln Sie Bilder verschiedener Vogelarten
   - Annotieren Sie diese mit Bounding Boxes und Artennamen
   - Empfohlene Datasets: iNaturalist Birds, eBird

2. **YOLOv8 für Vogelarten trainieren**:
```bash
pip install ultralytics
```

```python
from ultralytics import YOLO

# Laden des Basis-Modells
model = YOLO('yolov8n.pt')

# Training mit Vogeldataset
model.train(data='bird_species.yaml', epochs=100, imgsz=640)

# Export für Hailo
model.export(format='onnx')
```

3. **Konvertierung für Hailo**:
```bash
# ONNX zu Hailo HEF konvertieren
hailo optimize --onnx model.onnx --hw-arch hailo8 --output-dir ./optimized/
```

### Option 3: Vortrainierte Vogelarten-Modelle

**Beliebte Vogelarten-Erkennungsmodelle**:
- **BirdNET**: Speziell für Vogelarten entwickelt
- **Merlin Bird ID**: Cornell Lab's AI-Modell  
- **iNaturalist Vision**: Unterstützt viele Vogelarten

## Beispiel-Konfigurationsdatei erstellen

Erstellen Sie eine Vogelarten-spezifische Inferenz-Datei:

```json
{
  "model_name": "bird_species_detection",
  "classes": [
    "Amsel", "Blaumeise", "Rotkehlchen", "Kohlmeise", 
    "Buchfink", "Grünfink", "Star", "Haussperling",
    "Feldsperling", "Elster", "Rabenkrähe", "Eichelhäher"
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

## Empfohlener Workflow

1. **Testen Sie zuerst das Standard-Modell**:
   ```bash
   python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
     --duration 1 --ai-modul on --ai-model yolov8
   ```

2. **Prüfen Sie verfügbare Vogelarten-Modelle**:
   ```bash
   ssh pi@raspberry-pi "ls -la /usr/share/rpi-camera-assets/"
   ```

3. **Bei Bedarf eigenes Modell entwickeln**:
   - Sammeln Sie lokale Vogeldaten aus Ihrem Vogelhaus
   - Trainieren Sie ein spezifisches Modell für Ihre häufigsten Besucher
   - Konvertieren Sie es für Hailo-Optimierung

## Troubleshooting

- **Modell nicht gefunden**: Prüfen Sie den Pfad mit `ls -la`
- **Niedrige Erkennungsrate**: Justieren Sie `confidence_threshold`
- **Zu viele Falscherkennungen**: Erhöhen Sie `confidence_threshold`
- **Performance-Probleme**: Verwenden Sie kleinere Eingabeauflösungen

## Performance-Tipps

- Verwenden Sie Region of Interest (`--roi`) für den Futterplatz
- Optimale Auflösung für AI: 640x640 oder 1280x720
- Testen Sie verschiedene Confidence-Schwellwerte (0.3-0.7)