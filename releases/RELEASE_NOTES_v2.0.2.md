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

---

## 🐛 Bug Fixes

### CPU/RAM-Anzeige im Monitoring (KRITISCH)
- `pgrep -f` lieferte Bash-Wrapper-PID → CPU/RAM immer 0.0%
- Fix: `ps aux | grep 'python3.*unified-camera-monitor' | grep -v 'bash|grep'`
- Locale-Fix: `LC_ALL=C` für korrekte Dezimalzahlen (deutsches Komma)

### Kamera-Start-Konflikt
- `rpicam-vid`-Watchdog blockierte Kamera-Initialisierung
- Fix: Watchdog + rpicam-vid + libcamera vor Monitor-Start beendet

---

## 🔧 Improvements

- SSH-Timeout erhöht (2s→5s), Warnung erst nach 3 Fehlversuchen
- Status-Reporter alle 5 Minuten aktiv (CPU/RAM/Temperatur)
- `vogel-model-trainer` Submodule auf v0.1.28

---

## 🔗 Commits

```
912b0ae - feat: YOLO26 Migration und Monitoring-Verbesserungen
```
