# 🔬 Release v2.2.2 - Hailo-NPU Detection & Engine-Switcher

**Datum:** 16. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAD+ · Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.2** bringt native **Hailo-8 NPU Detection** in den Container-Daemon. Statt CPU-basiertem YOLO läuft die KI-Inferenz jetzt direkt auf dem Hailo-8 NPU-Koprozessor via `rpicam-hello` + YOLOv8 HEF-Modell — bei nur < 5 % CPU-Last und stabilen 25 fps. Dazu kommt ein vollständiger **Engine-Switcher**: die aktive Detection-Engine kann zur Laufzeit per Web-GUI oder API umgestellt werden.

### 🎯 Kernziele erreicht:
- ✅ **Hailo-8 NPU Detection** via `rpicam-hello` + `hailo_yolov8_inference.json` HEF
- ✅ **Engine-Switcher:** Laufzeit-Umschaltung zwischen `hailo` / `cpu_yolo` (GUI + API)
- ✅ **Live-Vorschau UX:** Hailo-Status sofort sichtbar statt „Kein Bild"-Meldung
- ✅ **Watchdog-Fix:** korrekter `_active_engine == 'hailo'`-Check statt fehlerhaftem String-Match
- ✅ **Ansible:** `pi_detection_script` auf `unified-camera-monitor-hailo.py` korrigiert

---

## ✨ Neue Features

### 1. Hailo-8 NPU Detection

Die Erkennung nutzt jetzt den Hailo-8 NPU-Koprozessor des **Raspberry Pi 5 AI HAD+** direkt. Das neue Script `unified-camera-monitor-hailo.py` startet `rpicam-hello` mit dem YOLOv8 HEF Post-Processing-Plugin.

**Vorteile gegenüber CPU-YOLO:**

| Metrik | CPU-YOLO (alt) | Hailo NPU (neu) |
|--------|---------------|-----------------|
| CPU-Last | ~80–100 % | < 5 % |
| Framerate | ~5–10 fps | 25 fps |
| NPU-Leistung | — | 26 TOPS |
| Kamera-Reset nötig | nein | nein |

**Technisch:**
```bash
rpicam-hello \
  --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
  --lores-width 640 --lores-height 640 \
  -t 0 --nopreview
```

**Startverhalten:**
- 3 Startversuche à 2 s Wartezeit
- 5 s Pause zwischen den Durchläufen
- Watchdog überwacht Prozess und startet neu bei unerwartetem Beenden

### 2. Detection-Engine-Switcher

Ein neues `DETECTION_ENGINES`-Registry-Konzept ermöglicht das Hinzufügen und Wechseln von Detection-Engines zur Laufzeit.

**Registry in `pi_daemon_secure.py`:**
```python
DETECTION_ENGINES = {
    'hailo': {
        'script': 'unified-camera-monitor-hailo.py',
        'label': 'Hailo-8 NPU (rpicam-hello + YOLOv8 HEF)',
    },
    'cpu_yolo': {
        'script': 'unified-camera-monitor-detect-only.py',
        'label': 'CPU-YOLO (ultralytics)',
    },
}
```

**API-Endpoint:**
```
POST /api/detection-engine
Content-Type: application/json
{"engine": "hailo"}
```

- Wechselt die aktive Engine sofort
- Stoppt laufende Detection und startet mit neuer Engine neu (falls aktiv)
- Persistiert Auswahl in `/config/detection-engine.json`
- Überlebt Container-Neustart

**Status-API:**
```json
GET /api/status
{
  "active_engine": "hailo",
  ...
}
```

### 3. Web-GUI Engine-Dropdown

Im Detection-Panel der Web-GUI gibt es jetzt ein Dropdown zur Engine-Auswahl:

```
Detection Engine: [🔬 Hailo NPU (YOLOv8 HEF) ▾]
                  [🖥 CPU-YOLO (nicht verfügbar) – disabled]
```

- `cpu_yolo` ist mit `disabled` markiert und mit Tooltip versehen (kein `picamera2` im Container)
- Ausgewählte Engine wird bei jedem `fetchStatus()`-Poll synchronisiert
- Toast-Meldung bei Umschaltung

### 4. Live-Vorschau UX bei Hailo-Detection

Wenn Hailo-Detection läuft, liefert `/api/snapshot` HTTP 503 (kein Live-Frame verfügbar, da `rpicam-hello` den Kamera-ISP exklusiv nutzt). Bisher erschien nach 40 Polling-Fehlversuchen „Kein Bild – Detection gestartet?".

**Neu:** Bei 503 + `_detectionRunning == true` wird sofort angezeigt:
```
🔬 Hailo-NPU Detection läuft – kein Live-Frame verfügbar
```

---

## 🐛 Bugfixes

### Watchdog String-Check Bug

**Problem:** Der Watchdog prüfte `if 'hailo' in DETECTION_SCRIPT:` — das schlug fehl, sobald der Pfad unerwartet war oder sich änderte.

**Fix:** `if _active_engine == 'hailo':` — direkter Vergleich auf den Registry-Key.

### Ansible `pi_detection_script` auf detect-only.py

**Problem:** `ansible/group_vars/all/vars.yml` hatte `pi_detection_script: "detect-only.py"`. Bei jedem `--update` wurde `/opt/pi-daemon/.env` mit dem alten Wert überschrieben → Hailo-Script wurde nicht gestartet.

**Fix:** `pi_detection_script: "unified-camera-monitor-hailo.py"`

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `unified-monitor-client/pi_daemon_secure.py` | `APP_VERSION = '2.2.2'`, `DETECTION_ENGINES`-Registry, `_load/save_active_engine()`, `POST /api/detection-engine`, `active_engine` in Status, Watchdog-Fix |
| `unified-monitor-client/web/index.html` | `_detectionRunning`, Hailo-UX-Meldung bei 503, Engine-Dropdown, `switchEngine()` |
| `raspberry-pi-scripts/unified-camera-monitor-hailo.py` | Neues Hailo-Detection-Script |
| `ansible/group_vars/all/vars.yml` | `pi_detection_script` → `unified-camera-monitor-hailo.py` |
| `VERSION` | 2.2.1 → 2.2.2 |
| `raspberry-pi-scripts/VERSION` | 2.2.0 → 2.2.2 |
| `unified-monitor-client/VERSION` | 2.2.0 → 2.2.2 |
| `scripts/__version__.py` | `__version__` → 2.2.2 |
| `scripts/version.py` | `__version__`, `RELEASE_NAME`, `GIT_TAG` → 2.2.2 |
| `CHANGELOG.md` | Neuer 2.2.2-Eintrag |
| `docs/CHANGELOG.md` | Neuer 2.2.2-Eintrag |
| `README.md` | Aktueller Release-Abschnitt auf 2.2.2 |
| `docs/i18n/README.de.md` | Version-Badge + Kurzüberblick auf 2.2.2 |

---

## 🔄 Upgrade von v2.2.1

Kein Breaking Change. Einfaches Update genügt:

```bash
cd ansible && bash build_and_deploy.sh --update
```

**Sicherstellen, dass Hailo aktiv ist** (nach dem ersten Deploy):
```bash
# Prüfen ob detection-engine.json auf 'hailo' steht
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "docker exec pi-daemon cat /config/detection-engine.json"
# Erwartet: {"engine": "hailo"}

# Falls noch 'cpu_yolo': manuell setzen
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "docker exec pi-daemon sh -c 'echo {\\\"engine\\\":\\\"hailo\\\"} > /config/detection-engine.json'"
docker restart pi-daemon
```

---

## 📊 Versionsübersicht

| Komponente | Version |
|-----------|---------|
| Gesamt | 2.2.2 |
| pi_daemon_secure.py | 2.2.2 |
| unified-monitor-client | 2.2.2 |
| raspberry-pi-scripts | 2.2.2 |
| Docker Base Image | python:3.13-slim-bookworm |
| Hailo NPU | Hailo-8 (26 TOPS) |
| YOLOv8 HEF | hailo_yolov8_inference.json |
| Raspberry Pi OS | Trixie (Debian 13) |
