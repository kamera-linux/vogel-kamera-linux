# 🔭 Release v2.2.4 - Manueller Fokus-Slider

**Datum:** 20. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAD+ · Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.4** führt einen **manuellen Fokus-Schieberegler** im Web-GUI ein. Die `lens_position` (0.5–10.0) kann direkt im Browser eingestellt werden und wird sofort an alle Aufnahme-Kommandos (`rpicam-vid`) weitergegeben. Der Wert wird persistent in `/config/camera-settings.json` gespeichert und überlebt Daemon-Neustarts.

### 🎯 Kernziele erreicht:
- ✅ **Manueller Fokus-Slider:** Bereich 0.5 – 10.0, Echtzeit-Abstandsanzeige in cm
- ✅ **Neuer Backend-Endpunkt:** `GET/POST /api/camera-settings`
- ✅ **Persistenz:** `/config/camera-settings.json`, Fallback `lens_position=3.0`
- ✅ **Aufnahme-Kommandos:** `--autofocus-mode manual --lens-position <wert>` in allen rpicam-vid-Commando-Arrays
- ✅ **GUI-Sync:** Slider wird beim Login befüllt und während des Pollings synchron gehalten

---

## ✨ Neues Feature: Manueller Fokus-Slider

### Problem vorher
Die Kamera nutzte immer den Autofokus (`--autofocus-mode auto`). Bei Aufnahmen am Vogelhäuschen konnte es zu Fokus-Drift kommen — der Autofokus fokussierte auf Hintergrundobjekte statt auf den Nahbereich des Häuschens. Es gab keine Möglichkeit, den Fokus manuell einzustellen.

### Lösung: `lens_position`-Parameter
`rpicam-vid` unterstützt `--autofocus-mode manual --lens-position <wert>` wobei der Wert in **Dioptrien** (1/Meter) angegeben wird:

| lens_position | Entfernung |
|--------------|------------|
| 0.5          | ≈ 200 cm   |
| 1.0          | ≈ 100 cm   |
| 2.0          | ≈  50 cm   |
| 3.0          | ≈  33 cm   |
| 5.0          | ≈  20 cm   |
| 10.0         | ≈  10 cm   |

### Web-GUI: Fokus-Slider

```html
<!-- Fokus-Einstellung -->
<div style="margin-bottom:0.75rem;display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;">
  <label for="lens-pos">🔭 Fokus:</label>
  <input type="range" id="lens-pos" min="0.5" max="10.0" step="0.5" value="3.0"
         oninput="updateLensLabel(this.value)"
         onchange="saveLensPosition(this.value)">
  <span id="lens-pos-val">3.0 (≈ 33 cm)</span>
  <span>(0.5=2m … 10=10cm)</span>
  <span id="lens-status"></span>
</div>
```

- `oninput` → aktualisiert die Abstandsanzeige live während des Ziehens
- `onchange` (fires on mouseup/touchend) → speichert via `POST /api/camera-settings`
- Status-Anzeige: `…` → `✓ gespeichert` (2,5 s) oder `✗ Fehler`

### Backend: `/api/camera-settings`

```python
@app.route('/api/camera-settings', methods=['GET', 'POST'])
@require_auth
def api_camera_settings():
    """
    GET  → { "lens_position": 3.0 }
    POST { "lens_position": 3.0 }
    """
```

- **GET**: gibt aktuellen `_lens_position`-Wert zurück
- **POST**: validiert (0.0–10.0), setzt `_lens_position`, schreibt `/config/camera-settings.json`
- Fehler bei ungültigem Typ: `400 { "error": "lens_position muss eine Zahl zwischen 0.0 und 10.0 sein" }`

### Persistenz: `camera-settings.json`

```json
{
  "lens_position": 3.0
}
```

- Wird beim Daemon-Start geladen (`_load_camera_settings()`)
- Fallback: `lens_position = 3.0` bei fehlender oder unlesbarer Datei
- Wert wird auf `0.0–10.0` geclampt

### Aufnahme-Kommandos

In **beiden** Aufnahme-Modus-Pfaden von `CameraManager.record()` wird nun übergeben:

```python
'--autofocus-mode', 'manual',
'--lens-position', str(_lens_position),
```

- H.264-Aufnahmen (`libcamera-vid` direkt)
- libav/MP4-Aufnahmen (Codec `libav`, Format `mp4`)

### GUI-Synchronisation

- `loadLensPosition()` wird bei `showDashboard()` aufgerufen → befüllt Slider beim Login
- In `updateStatus()` (Polling alle 2 s) wird `data.lens_position` ausgewertet:
  - Slider wird nur aktualisiert, wenn er **nicht aktiv angefasst** wird (`:active`-Check)
  - Verhindert jitter wenn GUI und Polling gleichzeitig aktiv sind

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|---------|
| `unified-monitor-client/web/index.html` | Fokus-Slider-UI, `updateLensLabel()`, `loadLensPosition()`, `saveLensPosition()`, Polling-Sync |
| `unified-monitor-client/pi_daemon_secure.py` | `_load/save_camera_settings()`, `_lens_position`, `--lens-position` in rpicam-vid, `/api/camera-settings`, `/api/status` |
| `VERSION` | 2.2.3 → 2.2.4 |
| `raspberry-pi-scripts/VERSION` | 2.2.3 → 2.2.4 |
| `unified-monitor-client/VERSION` | 2.2.3 → 2.2.4 |
| `scripts/__version__.py` | 2.2.3 → 2.2.4 |
| `scripts/version.py` | 2.2.3 → 2.2.4 |

---

## 🔄 Upgrade-Hinweise

Kein Migrations-Aufwand erforderlich. Beim ersten Start nach dem Update:
- `/config/camera-settings.json` existiert noch nicht → Fallback `lens_position=3.0` wird verwendet
- Beim ersten Speichern über den Slider wird die Datei automatisch angelegt

### Deploy
```bash
cd ansible && export PATH="$HOME/.local/bin:$PATH" && bash build_and_deploy.sh --update
```

---

## 📊 Statistiken

- **Commits:** 1 (Fokus-Feature)
- **Dateien geändert:** 2 (index.html, pi_daemon_secure.py)
- **Zeilen hinzugefügt:** ~101
- **Zeilen entfernt:** ~1
