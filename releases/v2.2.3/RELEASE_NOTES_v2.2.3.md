# 🎯 Release v2.2.3 - Aufnahmedauer-Fix & Dashboard-Korrekturen

**Datum:** 17. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAD+ · Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.3** behebt einen kritischen Bug, bei dem die im GUI eingestellte **Aufnahmedauer im Detection-Modus ignoriert** wurde — die Aufnahme startete immer mit der alten/Default-Dauer (15 s), unabhängig vom Slider. Dazu werden mehrere neue Features aus der 2.2.2-Session (neue Erkennungsziele, neue Dashboard-Kacheln) sowie ein Dashboard-HTML-Strukturfehler als eigenständige stabile Version gebündelt.

### 🎯 Kernziele erreicht:
- ✅ **Aufnahmedauer-Bug behoben:** Slider-`change`-Event ergänzt → Dauer wird bei Release persistiert
- ✅ **Backend-Limit:** 300 s → 600 s (5 min → 10 min)
- ✅ **Dashboard-Strukturfix:** „Hailo NPU"-Kachel erhält korrekte Card-Wrapper zurück
- ✅ **Neue Erkennungsziele:** Hund (`dog`), Katze (`cat`), Alle 4 (`all4`)
- ✅ **3 neue Dashboard-Kacheln:** Hailo NPU · Objekt erkannt · Erkennungsziel
- ✅ **Detection-Modus-Neustart** nach Aufnahme zuverlässig implementiert

---

## 🐛 Bugfixes

### Bug 1: Aufnahmedauer im Detection-Modus wird ignoriert

**Problem:**  
Der Dauer-Schieberegler (`rec-dur`) feuerte beim Loslassen kein `change`-Event, das die Einstellung an `/api/rec-settings` schickt. Nur das **Profil-Dropdown** hatte einen `change`-Handler. Folge: Die gespeicherte Dauer blieb immer auf dem alten Wert (oder dem Fallback-Default 15 s). Der Watchdog las beim Auslösen einer Aufnahme diese veraltete Dauer — unabhängig davon, was im GUI angezeigt wurde.

**Ursache:**
```javascript
// ALT — nur Profil-Änderung wurde gespeichert:
sel.addEventListener('change', () => {
  apiFetch('/api/rec-settings', 'POST', { profile: sel.value, duration: parseInt(dur) * 60 });
});
```

**Fix:**
```javascript
// NEU — gemeinsame saveRecSettings()-Funktion:
function saveRecSettings() {
  apiFetch('/api/rec-settings', 'POST', { profile: sel.value, duration: parseInt(durEl.value) * 60 });
}
sel.addEventListener('change', saveRecSettings);
durEl.addEventListener('change', saveRecSettings);  // fires on mouseup/touchend
```

### Bug 2: Backend kappte Aufnahmedauer bei 5 Minuten

**Problem:**  
Beide API-Endpunkte hatten `min(max(int(...), 3), 300)` — der Maximalwert 300 s (5 min) stimmte nicht mit dem Slider-Maximum (10 min) überein. Eine eingestellte Dauer von 6–10 min wurde still auf 5 min reduziert.

**Fix:** Limit auf `600` (10 min) erhöht in:
- `POST /api/rec-settings`
- `POST /api/record`

### Bug 3: „Hailo NPU"-Kachel verlor Card-Wrapper

**Problem:**  
Nach dem Multi-Replace beim Hinzufügen der „Erkennungsziel"-Kachel war der `<div class="card">` und `<div class="label">`-Wrapper der „Hailo NPU"-Kachel verloren gegangen — nur `<div class="value" id="s-hailo">` blieb übrig als semantisch falsch positioniertes Element außerhalb des Card-Grids.

**Fix:** Korrekte Wrapper-Struktur wiederhergestellt:
```html
<div class="card">
  <div class="label">Hailo NPU</div>
  <div class="value" id="s-hailo">–</div>
</div>
```

---

## ✨ Neue Features

### 1. Neue Erkennungsziele: Hund, Katze, Alle 4

Neben `bird` (Vogel) und `person` (Mensch) stehen jetzt drei weitere Erkennungsziele zur Verfügung:

| Ziel | Klasse | Icon |
|------|--------|------|
| `bird` | Vogel | 🐦 |
| `person` | Mensch | 🧍 |
| `dog` | Hund | 🐕 |
| `cat` | Katze | 🐈 |
| `all4` | Alle vier | 🐦🧍🐕🐈 |

**Hailo-Script (`unified-camera-monitor-hailo.py`):**
```python
TARGET_CLASSES: dict = {
    'bird':   {'bird'},
    'person': {'person'},
    'dog':    {'dog'},
    'cat':    {'cat'},
    'all4':   {'bird', 'person', 'dog', 'cat'},
}
```

**Backend-Whitelist** (`pi_daemon_secure.py`):
```python
if target not in ('bird', 'person', 'dog', 'cat', 'all4'):
```

**GUI** — 5 Radio-Buttons:
```
Erkennen: 🐦 Vogel | 🧍 Mensch | 🐕 Hund | 🐈 Katze | 🐦🧍🐕🐈 Alle 4
```

### 2. Drei neue Dashboard-Kacheln

#### „Hailo NPU"
Zeigt als Pill-Badge ob der Hailo-Detection-Prozess aktiv ist:
- `🔬 Aktiv` (grün) — wenn `detection_running == true` und `active_engine == 'hailo'`
- `Inaktiv` (grau) — sonst

#### „Objekt erkannt"
Zeigt den letzten Detection-Treffer aus `/tmp/last-detection.json`:
```
🐦 bird  0.87
12:34:56
```
Hailo-Script schreibt bei jedem Treffer:
```python
Path('/tmp/last-detection.json').write_text(json.dumps({
    'class': class_name,
    'conf':  round(confidence, 3),
    'time':  datetime.now().strftime('%H:%M:%S'),
}))
```
Daemon liest es via `_read_last_detection()` und gibt es in `/api/status` als `last_detection` zurück.

#### „Erkennungsziel"
Zeigt das aktuell konfigurierte Erkennungsziel mit Icon, Namen und Konfidenzschwelle:
```
🐕 Hund
45% Konfidenz
```

### 3. Detection-Modus-Lebenszyklus-Fixes

#### start_detection_mode() early-return-Fix
```python
# ALT — verhinderte Neustart wenn detection_mode=True aber Prozess schon beendet:
if state.detection_mode:
    return True

# NEU — Prozess muss tatsächlich laufen:
if state.detection_mode and state.detection_running:
    return True
```

#### birds_recorded wird korrekt zurückgesetzt
Reset nur beim ersten Aktivieren der Session, nicht bei jedem Process-Restart nach Aufnahme.

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `unified-monitor-client/web/index.html` | Slider-`change`-Event, 3 neue Kacheln, dog/cat/all4-Radios, HTML-Strukturfix |
| `unified-monitor-client/pi_daemon_secure.py` | `APP_VERSION = '2.2.3'`, Aufnahmedauer-Cap 300→600 s, Whitelist dog/cat/all4, `_read_last_detection()`, `last_detection` in Status, Detection-Modus-Fixes |
| `raspberry-pi-scripts/unified-camera-monitor-hailo.py` | dog/cat/all4 TARGET_CLASSES, target_icon erweitert, `/tmp/last-detection.json` schreiben |
| `VERSION` | 2.2.2 → 2.2.3 |
| `raspberry-pi-scripts/VERSION` | 2.2.2 → 2.2.3 |
| `unified-monitor-client/VERSION` | 2.2.2 → 2.2.3 |
| `scripts/__version__.py` | `__version__` → 2.2.3 |
| `scripts/version.py` | `__version__`, `RELEASE_NAME`, `GIT_TAG` → 2.2.3 |
| `CHANGELOG.md` | Neuer 2.2.3-Eintrag |
| `docs/CHANGELOG.md` | Neuer 2.2.3-Eintrag |
| `README.md` | Aktueller Release-Abschnitt auf 2.2.3 |
| `docs/i18n/README.de.md` | Version-Badge + Kurzüberblick auf 2.2.3 |

---

## 🔄 Upgrade von v2.2.2

Kein Breaking Change. Einfaches Update genügt:

```bash
cd ansible && bash build_and_deploy.sh --update
```

**Nach dem Deploy:** Slider auf gewünschte Dauer schieben und loslassen — Einstellung wird sofort gespeichert. Kontrollieren via:

```bash
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "docker exec pi-daemon cat /config/rec-settings.json"
# Erwartet z.B.: {"profile": "normal_hd", "duration": 180}  (= 3 min)
```

---

## 📊 Versionsübersicht

| Komponente | Version |
|-----------|---------|
| Gesamt | 2.2.3 |
| pi_daemon_secure.py | 2.2.3 |
| unified-monitor-client | 2.2.3 |
| raspberry-pi-scripts | 2.2.3 |
| Docker Base Image | python:3.13-slim-bookworm |
| Hailo NPU | Hailo-8 (26 TOPS) |
| YOLOv8 HEF | hailo_yolov8_inference.json |
| Raspberry Pi OS | Trixie (Debian 13) |
