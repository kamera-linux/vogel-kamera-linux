# 🐦 Vogel-Kamera-Linux v2.0.2 - YOLO26 & Monitoring Improvements

**Release Date:** 6. März 2026
**Type:** Patch Release
**Status:** ✅ Stable

---

## 📋 Overview

v2.0.2 aktualisiert das KI-Erkennungsmodell auf YOLO26 für verbesserte Genauigkeit und behebt
kritische Fehler in der CPU/RAM-Anzeige und Kamera-Initialisierung des Monitoring-Skripts.

---

## ✨ New Features

### 🤖 YOLO26 Migration
- **Neues Modell:** `yolo26n.pt` ersetzt `yolov8n.pt`
- Verbesserte Erkennungsgenauigkeit bei ähnlicher Modellgröße (5.3 MB)
- `ultralytics>=26.0.0` als Mindestanforderung (war `>=8.0.0`)
- Vollständig rückwärtskompatibler API-Wechsel
- Modell-Download: automatisch beim ersten Start

---

## 🐛 Bug Fixes

### CPU/RAM-Anzeige im Monitoring (KRITISCH)
- **Problem:** PID-Erkennung lieferte Bash-Wrapper-PID statt Python-Prozess-PID → CPU/RAM immer 0.0%
- **Ursache:** `pgrep -f unified-camera-monitor` gibt den Bash-Wrapper (niedrigere PID) zurück
- **Fix:** `ps aux | grep 'python3.*unified-camera-monitor' | grep -v 'bash|grep'`
- **Ergebnis:** Korrekte Werte (Beispiel: 151% CPU, 5.6% RAM)

### Locale-Komma-Problem (PID Parsing)
- **Problem:** Deutsches Locale gibt `0,0` statt `0.0` für ps-Ausgaben aus
- **Fix:** `LC_ALL=C` vor allen `ps`-Befehlen

### Kamera-Start-Konflikt
- **Problem:** `__init__ sequence did not complete` beim Kamera-Start
- **Ursache:** `start-tcp-preview-watchdog.sh` hielt `rpicam-vid` aktiv und blockierte die Kamera
- **Fix:** Watchdog + rpicam-vid + libcamera vor Monitor-Start gezielt beendet

---

## 🔧 Improvements

### SSH-Stabilität
- Timeout erhöht: `ConnectTimeout=2` → `ConnectTimeout=5`, `timeout 3` → `timeout 8`
- Warnung erst nach 3 aufeinanderfolgenden Fehlversuchen (war: sofort)
- Reduziert Fehlalarme bei vorübergehend langsamer Pi-Antwort

### Status-Reporter
- Alle 5 Minuten aktiver Status mit CPU/RAM/Temperatur
- Zuvor: schlief nur (Sleep 3600s, keine Ausgabe)

### Submodule
- `ai-training-tools/vogel-model-trainer` auf v0.1.28 aktualisiert

---

## 📦 Installation / Update

### Raspberry Pi Update

```bash
# 1. Scripts synchronisieren (vom Client-PC)
rsync -avz -e "ssh -i ~/.ssh/id_rsa_ai-had" \
  raspberry-pi-scripts/ \
  roimme@raspberrypi-5-ai-had:~/vogel-kamera-linux/raspberry-pi-scripts/

# 2. ultralytics auf Pi upgraden
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "source ~/.venv/vogel-camera/bin/activate && pip install ultralytics --upgrade"

# 3. YOLO26-Modell herunterladen (automatisch beim ersten Start, oder manuell)
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "source ~/.venv/vogel-camera/bin/activate && \
   python3 -c \"from ultralytics import YOLO; YOLO('yolo26n.pt')\""
```

---

## 🔗 Changed Files

| Datei | Änderung |
|-------|----------|
| `raspberry-pi-scripts/unified-camera-monitor.py` | `yolov8n.pt` → `yolo26n.pt` |
| `raspberry-pi-scripts/requirements-pi.txt` | `ultralytics>=8.0.0` → `>=26.0.0` |
| `auto-start-kamera/start-unified-monitoring.sh` | PID-Fix, SSH-Timeout, Kamera-Cleanup, Status-Reporter |
| `scripts/version.py` | Version 2.0.2 |
| `ai-training-tools/vogel-model-trainer` | Submodule auf v0.1.28 |

---

## 🔗 Commits

```
912b0ae - feat: YOLO26 Migration und Monitoring-Verbesserungen
```

---

## 📊 Performance

| Metrik | Wert |
|--------|------|
| CPU-Auslastung (Pi 5) | ~151% (Multi-Core) |
| RAM-Nutzung | ~5.6% (~450 MB) |
| Frames verarbeitet | ~63 / 30 Sekunden |
| Modellgröße | 5.3 MB |
