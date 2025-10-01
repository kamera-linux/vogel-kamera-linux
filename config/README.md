# 📁 Konfiguration & Modelle

Dieses Verzeichnis enthält allgemeine Konfigurationsdateien und AI-Modelle.

## 📂 Struktur

```
config/
├── models/
│   └── yolov8n.pt          # YOLOv8 Nano Model (6.3MB)
├── ssh-config.sh           # SSH-Konfiguration für Raspberry Pi
└── requirements.txt        # System-weite Python-Dependencies
```

## 🤖 AI-Modelle

### YOLOv8n (Nano)
- **Datei:** `models/yolov8n.pt`
- **Größe:** 6.3 MB
- **Verwendung:** Basis-Objekterkennung für Auto-Trigger System
- **80 Klassen:** COCO Dataset (inkl. "bird" als Klasse 14)
- **Vorteil:** Zentraler Speicherort verhindert mehrfaches Herunterladen

### Verwendung

Das Model wird automatisch von den Python-Skripten geladen:

```python
from pathlib import Path
from ultralytics import YOLO

# Pfad relativ zum Projekt-Root
project_root = Path(__file__).parent.parent
model_path = project_root / "config" / "models" / "yolov8n.pt"
model = YOLO(str(model_path))
```

### Warum ein zentrales Verzeichnis?

**Problem:** YOLO sucht standardmäßig im aktuellen Verzeichnis nach `yolov8n.pt`. Wenn das Modell fehlt, wird es automatisch heruntergeladen - jedes Mal wenn das Skript aus einem anderen Verzeichnis gestartet wird.

**Lösung:** Zentraler Speicherort in `config/models/` mit expliziten Pfaden in allen Skripten. So wird das Modell:
- Nur einmal heruntergeladen
- Von allen Skripten verwendet
- Im Git-Repository versioniert
- Nicht versehentlich gelöscht

## 🔧 SSH-Konfiguration

Die `ssh-config.sh` enthält SSH-Einstellungen für die Verbindung zum Raspberry Pi:

```bash
# Verwendung
source config/ssh-config.sh
```

## 📦 Dependencies

Die `requirements.txt` enthält system-weite Python-Dependencies für alle Projekt-Komponenten.

**Installation:**
```bash
pip install -r config/requirements.txt
```

---

**Hinweis:** Für spezifische Auto-Trigger Dependencies siehe `kamera-auto-trigger/requirements.txt`.
