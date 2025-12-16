# AI-Modell Konfiguration für Vogelarten-Erkennung

## Verfügbare AI-Modelle

### 1. Standard YOLOv8 (allgemeine Objekterkennung)
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model yolov8
```
- **Erkennt**: Allgemeine Objekte inkl. "bird" (Vogel)
- **Datei**: `/usr/share/rpi-camera-assets/hailo_yolov8_inference.json`

### 2. Vogelarten-spezifisches Modell (automatisch erstellt)
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model bird-species
```
- **Erkennt**: Vögel (COCO Klasse 14) mit optimierter Sensitivität
- **Datei**: `/usr/share/rpi-camera-assets/hailo_bird_species_inference.json`
- **Automatische Erstellung**: Wird bei Bedarf automatisch generiert
- **Optimierungen**: 
  - Niedrigere Schwelle (0.3) für bessere Vogelerkennung
  - Fokus nur auf Vogel-Klasse (class_filter: [14])
  - Temporaler Filter für stabilere Erkennungen

### 3. Benutzerdefiniertes Modell
```bash
python ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 5 --ai-modul on --ai-model custom \
  --ai-model-path /path/to/your/custom_bird_model.json
```

## Automatische bird-species Modellerstellung

**🔄 Automatische Funktion**: Das bird-species Modell wird automatisch erstellt, falls es nicht vorhanden ist!

### Funktionsweise
Wenn Sie `--ai-model bird-species` verwenden und das Modell nicht existiert:

1. **Automatische Erkennung**: Das Skript prüft die Verfügbarkeit des Modells
2. **Dynamische Erstellung**: Ein optimiertes bird-species Modell wird generiert
3. **Sofortige Verwendung**: Das neue Modell wird direkt verwendet

### Generierte Konfiguration
```json
{
    "rpicam-apps": {
        "lores": {
            "width": 640,
            "height": 640,
            "format": "rgb"
        }
    },
    "hailo_yolo_inference": {
        "hef_file_8L": "/usr/share/hailo-models/yolov8s_h8l.hef",
        "hef_file_8": "/usr/share/hailo-models/yolov8s_h8.hef",
        "max_detections": 10,
        "threshold": 0.3,
        "class_filter": [14],
        "temporal_filter": {
            "tolerance": 0.15,
            "factor": 0.8,
            "visible_frames": 8,
            "hidden_frames": 2
        }
    },
    "object_detect_draw_cv": {
        "line_thickness": 3,
        "font_thickness": 2
    }
}
```

### Optimierungen für Vogelerkennung
- **Niedrigere Schwelle**: `threshold: 0.3` (vs. 0.5 bei Standard YOLOv8)
- **Klassenfilter**: Nur COCO-Klasse 14 ("bird") wird erkannt
- **Temporaler Filter**: Stabilisiert Erkennungen über mehrere Frames
- **Optimierte Auflösung**: 640x640 für beste Performance mit Hailo-Chip

## Manuelle Vogelarten-Modelle einrichten

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

**Empfohlene Hugging Face Modelle**:
- 🔗 **[kamera-linux/german-bird-classifier-v2](https://huggingface.co/kamera-linux/german-bird-classifier-v2)** ⭐ **Empfohlen** - Neuestes Modell mit verbesserter Genauigkeit für deutsche Vogelarten
- 🔗 **[kamera-linux/german-bird-classifier](https://huggingface.co/kamera-linux/german-bird-classifier)** - Erste Version (Legacy)

**Weitere Vogelarten-Erkennungsmodelle**:
- **BirdNET**: Speziell für Vogelarten entwickelt
- **Merlin Bird ID**: Cornell Lab's AI-Modell  
- **iNaturalist Vision**: Unterstützt viele Vogelarten

## 📊 System-Monitoring für AI-Aufnahmen (v1.1.9)

**🆕 Automatische System-Überwachung**: Alle AI-Kamera-Skripte überwachen jetzt automatisch die System-Performance vor und während der Aufnahme.

### System-Status-Anzeige
Vor jeder AI-Aufnahme wird automatisch angezeigt:
- 🌡️ **CPU-Temperatur** mit Warnstufen (>60°C Warnung, >70°C Kritisch)
- 💾 **Festplattenspeicher** mit Auslastung (>80% Warnung, >90% Kritisch)
- 🧠 **Arbeitsspeicher** mit Verfügbarkeits-Info
- ⚡ **CPU-Load Average** mit Performance-Auswirkungen

### Performance-Optimierung
```bash
# Beispiel System-Status vor AI-Aufnahme:
📊 System-Status für pi@vogelkamera:
==================================================
🌡️ CPU-Temperatur: 58.4°C 🟢 OK
💾 Festplatte: 45G verwendet von 59G (79%) 🟢 OK  
🧠 Arbeitsspeicher: 2.1G verwendet von 7.8G (5.6G verfügbar)
⚡ CPU-Load (1min): 0.8 🟢 NIEDRIG
==================================================

✅ System bereit für AI-Aufnahme
```

### Load-Balancing für AI-Modi
- **Standard AI-Modus**: Load > 2.0 = Warnung, Load > 1.0 = Beobachtung
- **Zeitlupe-Modus**: Load > 1.0 = Kritisch (strengere Anforderungen)
- **Audio-Modus**: Load-Monitoring für optimale Audioqualität

Bei kritischen Werten erscheint eine Benutzer-Bestätigung:
```
⚠️ System-Warnung erkannt. Trotzdem fortfahren? (j/N):
```

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