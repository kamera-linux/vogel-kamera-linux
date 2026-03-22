# 🔭 Release v2.2.5 - Vollständige Kamera-Kontrolle (10 Parameter)

**Datum:** 21. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAD+ · Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.5** erweitert die Kamera-Steuerung um **insgesamt 8 Schieberegler/Selektoren** (+ 2 bestehende = 10 Parameter Gesamt):

### 📷 Basis-Schieberegler (v2.2.4):
1. **🔭 Fokus-Slider (Lens Position):** (0.5 – 10.0) – Manuelle Fokus-Kontrolle

### ☀️ Belichtungs- & Farbeinstellungen (neu in v2.2.5):
2. **☀️ EV-Slider (Exposure Value):** (-2.0 bis +2.0) – Kamera-native Belichtungsregelung
3. **💡 AWB-Selector (Auto White Balance):** 6 Modi – Weißabgleich-Auswahl

### 🎨 Bildqualität-Einstellungen (neu in v2.2.5):
4. **🌞 Brightness:** (-1.0 bis +1.0) – digitale Helligkeit
5. **⚪ Contrast:** (0.5 bis 2.0) – Kontrastverhältnis (0.5 = soft, 2.0 = hart)
6. **🌈 Saturation:** (0.0 bis 2.0) – Farbintensität (0.0 = Graustufen)
7. **✨ Sharpness:** (0.0 bis 2.0) – digitales Sharpening/Weichzeichnen
8. **🔆 Gain:** (1.0 bis 8.0) – ISO-äquivalente Verstärkung (1.0 = normal, 8.0 = extreme Verstärkung)

Alle 8 Einstellungen werden persistent in `/config/camera-settings.json` gespeichert, sofort an alle laufenden und neuen Aufnahmen übergeben und sind im Web-GUI synchronisiert.

### 🎯 Kernziele erreicht:
- ✅ **EV-Slider:** Bereich -2.0 bis +2.0, Live-Anpassung der Belichtung
- ✅ **AWB-Selector:** 6 vordefinierte Weißabgleich-Modi
- ✅ **5 Bildqualität-Regler:** Brightness, Contrast, Saturation, Sharpness, Gain – REMOTE GETESTET ✅
  - ✅ brightness -0.5 (Verdunkelung bei Gegenlicht)
  - ✅ contrast 1.5 (erhöhte Kontraste)
  - ✅ saturation 0.8 (natürlichere Farben)
  - ✅ sharpness 1.2 (mehr Details)
  - ✅ gain 2.0 (Lowlight-Verstärkung)
- ✅ **Erweiterter API-Endpunkt:** `/api/camera-settings` unterstützt jetzt alle 8 Parameter
- ✅ **Persistenz:** Alle Werte in `/config/camera-settings.json`, robuste Fallbacks
- ✅ **rpicam-vid Integration:** `--ev`, `--awb`, `--brightness`, `--contrast`, `--saturation`, `--sharpness`, `--gain` an alle Aufnahme-Kommandos
- ✅ **GUI-Sync:** Alle Sliders/Selektoren werden beim Login befüllt und während Polling synchron gehalten
- ✅ **Dokumentation:** Online-Hilfe mit Kombinationstipps für verschiedene Lichtsituationen

---

## ✨ Neue Features: Vollständige Bildqualität-Kontrolle

### Problem vorher
Die Kamera arbeitete mit fixen Belichtungs-, Weißabgleich-, Kontrast-, Farb- und Schärfe-Werten. Bei unterschiedlichen Lichtsituationen konnte der Kameraoperator nicht optimal einstellen. Lowlight-Szenarien oder überbelichtete Szenen waren schwierig zu korrigieren.

### Lösung: 8 Parameter Kamera-Steuerung

`rpicam-vid` unterstützt:

#### Belichtung & Farbe:
- `--ev <wert>`: Exposure Value im Bereich **-2.0 bis +2.0**
  - Negative Werte dunkeln das Bild ab
  - Positive Werte hellen das Bild auf
  - Standard (0.0) = normale Belichtung

- `--awb <modus>`: Auto White Balance Modi
  - `auto`, `daylight`, `cloudy`, `tungsten`, `fluorescent`, `indoor`

#### Bildqualität (Brightness, Contrast, Saturation, Sharpness, Gain):
- `--brightness <wert>`: -1.0 bis +1.0
  - Standard: 0.0 (keine Änderung)
  - Negative Werte: Abdunkelung (z.B. -0.5 bei Gegenlicht)
  - Positive Werte: Aufhellung (z.B. +0.5 bei Schattenbereichen)

- `--contrast <wert>`: 0.5 bis 2.0
  - Standard: 1.0 (normaler Kontrast)
  - Unter 1.0: Weicheres Bild, weniger Schatten (z.B. 0.8 für sanfte Übergänge)
  - Über 1.0: Schärfere Unterschiede (z.B. 1.5 für dramatisches Aussehen)

- `--saturation <wert>`: 0.0 bis 2.0
  - Standard: 1.0 (normale Farben)
  - 0.0: Komplett entsättigt (Schwarzweiß)
  - 0.8: Gedämpfte, natürlichere Farben
  - 1.2+: Kräftige, lebendige Farben (ideal für Vogelplumage)

- `--sharpness <wert>`: 0.0 bis 2.0
  - Standard: 1.0 (normale digitale Schärfe)
  - Unter 1.0: Weiches Bild, Rauschreduktion (z.B. 0.8 bei ISO-hohen Einstellungen)
  - Über 1.0: Verstärktes Sharpening (z.B. 1.2 für mehr Details, kostet aber Rausch)

- `--gain <wert>`: 1.0 bis 8.0
  - Standard: 1.0 (keine digitale Verstärkung)
  - **Lowlight-Szenarien:** 2.0-4.0 für dunkle Räume / schattigen Vogelkasten
  - **Extreme Dunkelheit:** 4.0-8.0, verstärkt aber auch Rauschen
  - Komplementär zu EV: EV steuert Sensor-Belichtung, Gain ist post-Sensor-Verstärkung

### Web-GUI: 8 Regler + 1 Select

#### EV-Slider (Belichtung)
```html
<!-- EV-Slider (Exposure Value) -->
<div style="margin-bottom:0.75rem;display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;">
  <label for="ev-slider" style="font-size:0.85rem;color:var(--muted);">☀️ Belichtung (EV):</label>
  <input type="range" id="ev-slider" min="-2.0" max="2.0" step="0.5" value="0.0"
         style="width:160px;accent-color:var(--accent,#2563eb);"
         oninput="updateEVLabel(this.value)"
         onchange="saveEVSetting(this.value)">
  <span id="ev-val" style="font-size:0.85rem;min-width:3rem;">0.0</span>
  <span style="font-size:0.75rem;color:var(--muted);">(-2=dunkel … +2=hell)</span>
  <span id="ev-status" style="font-size:0.8rem;color:var(--muted);"></span>
</div>
```

#### AWB-Selector (Weißabgleich)
```html
<!-- AWB-Einstellung (Auto White Balance) -->
<div style="margin-bottom:0.75rem;display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;">
  <label for="awb-select" style="font-size:0.85rem;color:var(--muted);">💡 Weißabgleich (AWB):</label>
  <select id="awb-select" style="height:32px;padding:0.25rem 0.4rem;background:var(--bg,#1e1e1e);border:1px solid var(--border,#333);border-radius:4px;color:var(--text,#e0e0e0);font-size:0.85rem;"
          onchange="saveAWBSetting(this.value)">
    <option value="auto">Auto</option>
    <option value="daylight">Tageslicht</option>
    <option value="cloudy">Bewölkt</option>
    <option value="tungsten">Glühbirne</option>
    <option value="fluorescent">Leuchtstoffröhre</option>
    <option value="indoor">Innen</option>
  </select>
  <span id="awb-status" style="font-size:0.8rem;color:var(--muted);"></span>
</div>
```

#### 5 neue Bildqualität-Regler (Brightness, Contrast, Saturation, Sharpness, Gain)
```html
<!-- Folgen demselben Pattern wie EV-Slider, mit entsprechenden Bereichen und Beschriftungen -->
<!-- updateBrightnessLabel(), loadBrightnessSetting(), saveBrightnessSetting() etc. -->
```

- `oninput` → aktualisiert die Anzeige live während des Ziehens
- `onchange` → speichert via `POST /api/camera-settings`
- Status-Anzeige: `…` → `✓ gespeichert` (2,5 s) oder `✗ Fehler`

### Backend: Erweiterte `/api/camera-settings` Endpunkte

```python
@app.route('/api/camera-settings', methods=['GET', 'POST'])
@require_auth
def api_camera_settings():
    """
    GET  → { "lens_position": 3.0, "ev": 0.0, "awb": "auto", "brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "sharpness": 1.0, "gain": 1.0 }
    POST { "brightness": -0.5 } ↔ { "contrast": 1.5 } ↔ { "saturation": 0.8, "sharpness": 1.2, "gain": 2.0 }
    """
```

- **GET**: gibt alle 8 aktuellen Einstellungen zurück
- **POST**: akzeptiert beliebige Kombination:
  - Nur einen Parameter ändern? OK!
  - Mehrere gleichzeitig? Auch OK!
- Validierung:
  - `brightness`: float, -1.0 bis +1.0 (geclampt)
  - `contrast`: float, 0.5 bis 2.0 (geclampt)
  - `saturation`: float, 0.0 bis 2.0 (geclampt)
  - `sharpness`: float, 0.0 bis 2.0 (geclampt)
  - `gain`: float, 1.0 bis 8.0 (geclampt)
- Fehler bei ungültigen Werten: `400 Bad Request`

### Persistenz: `camera-settings.json`

```json
{
  "lens_position": 3.0,
  "ev": 0.0,
  "awb": "auto",
  "brightness": 0.0,
  "contrast": 1.0,
  "saturation": 1.0,
  "sharpness": 1.0,
  "gain": 1.0
}
```

- Wird beim Daemon-Start geladen
- Fallback: Standard-Werte bei fehlender/unlesbarer Datei
- Alle Werte werden mit min/max-Clamping validiert

### Aufnahme-Kommandos

In **beiden** Aufnahme-Modus-Pfaden werden nun übergeben (Slowmotion + Normal mit Audio):

```bash
rpicam-vid \
  --lens-position 3.0 \
  --ev 0.0 \
  --awb auto \
  --brightness 0.0 \
  --contrast 1.0 \
  --saturation 1.0 \
  --sharpness 1.0 \
  --gain 1.0 \
  # ... weitere Parameter
```

### GUI-Synchronisation

- Beim Dashboard-Load: `loadBrightnessSetting()`, `loadContrastSetting()`, `loadSaturationSetting()`, `loadSharpnessSetting()`, `loadGainSetting()` füllen die Sliders
- Polling (2 s Interval): `updateStatus()` synchronisiert alle 8 Werte, ohne den Fokus zu stören

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|---------|
| `unified-monitor-client/web/index.html` | 5 neue Bildqualität-Slider (brightness, contrast, saturation, sharpness, gain), 25 neue JavaScript-Funktionen, Online-Hilfe erweitert |
| `unified-monitor-client/pi_daemon_secure.py` | `_load_camera_settings()` um 5 Params, Globale Vars, `api_camera_settings()` erweitert, rpicam-vid Flags, `/api/status` erweitert |
| `VERSION` | 2.2.4 → 2.2.5 |
| `raspberry-pi-scripts/VERSION` | 2.2.4 → 2.2.5 |
| `unified-monitor-client/VERSION` | 2.2.4 → 2.2.5 |

---

## 🔄 Upgrade-Hinweise

Kein Migrations-Aufwand erforderlich. Beim ersten Start nach dem Update:
- `/config/camera-settings.json` wird mit den neuen 5 Parametern erweitert
- Bestehende `lens_position`, `ev`, `awb` Einstellungen werden beibehalten
- Neue Parameter erhalten Standard-Fallback-Werte

### Deploy
```bash
cd ansible && export PATH="$HOME/.local/bin:$PATH" && bash build_and_deploy.sh --update
```
  - Nur `lens_position` ändern? Kein Problem!
  - Nur `ev`? Auch ok!
  - Nur `awb`? Alles unterstützt!
  - Mehrere gleichzeitig? Natürlich!
- Validierung:
  - `ev`: float, -2.0 bis 2.0 (geclampt)
  - `awb`: string, einer der 6 erlaubten Modi (default: 'auto')
- Fehler bei ungültigen Werten: `400 Bad Request`

### Persistenz: `camera-settings.json`

```json
{
  "lens_position": 3.0,
  "ev": 0.0,
  "awb": "auto"
}
```

- Wird beim Daemon-Start geladen
- Fallback: `lens_position=3.0, ev=0.0, awb='auto'` bei fehlender oder unlesbarer Datei
- EV wird auf `-2.0 bis 2.0` geclampt
- AWB wird vom Daemon validiert

### Aufnahme-Kommandos

In **beiden** Aufnahme-Modus-Pfaden von `CameraManager.record()` wird nun übergeben:

#### Zeitlupe (Slowmotion – h264)
```python
video_cmd = [
    'rpicam-vid',
    '--width', str(w), '--height', str(h),
    '--framerate', str(fps),
    '--bitrate', str(bitrate * 1000),
    '-o', str(video_file),
    '--rotation', '0',
    '--autofocus-mode', 'manual',
    '--lens-position', str(_lens_position),
    '--ev', str(_ev),           # ← NEU
    '--awb', _awb,              # ← NEU
    '--timeout', str(duration * 1000),
]
```

#### Normal mit Audio (libav/mp4)
```python
video_cmd = [
    'rpicam-vid', '-n',
    '--width', str(w), '--height', str(h),
    '--framerate', str(fps),
    '--rotation', '0',
    '--autofocus-mode', 'manual',
    '--lens-position', str(_lens_position),
    '--ev', str(_ev),           # ← NEU
    '--awb', _awb,              # ← NEU
    '--codec', 'libav',
    '--libav-format', 'mp4',
    '--libav-audio',
    # ... weitere Audio-Parameter
    '--timeout', str(duration * 1000),
    '-o', str(video_file),
]
```

### GUI-Synchronisation

- `loadEVSetting()` und `loadAWSetting()` werden bei `showDashboard()` aufgerufen → füllen Slider/Select beim Login
- In `updateStatus()` (Polling alle 2 s) werden `data.ev` und `data.awb` ausgewertet:
  - EV-Slider wird nur aktualisiert, wenn er **nicht aktiv angefasst** wird (`:active`-Check)
  - AWB-Selectbox wird synchronisiert, ohne Fokus zu verlieren
  - Verhindert Jitter wenn GUI und Polling gleichzeitig aktiv sind

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|---------|
| `unified-monitor-client/web/index.html` | EV-Slider UI, AWB-Selector UI, `updateEVLabel()`, `loadEVSetting()`, `saveEVSetting()`, `loadAWBSetting()`, `saveAWBSetting()`, Polling-Sync |
| `unified-monitor-client/pi_daemon_secure.py` | `_load_camera_settings()` erweitert um ev/awb, Globale `_ev`, `_awb` Variablen, `api_camera_settings()` erweitert, `--ev` und `--awb` in rpicam-vid Commands (beide Pfade), `/api/status` um ev/awb erweitert |
| `VERSION` | 2.2.4 → 2.2.5 |
| `raspberry-pi-scripts/VERSION` | 2.2.4 → 2.2.5 |
| `unified-monitor-client/VERSION` | 2.2.4 → 2.2.5 |
| `scripts/__version__.py` | 2.2.4 → 2.2.5 |
| `scripts/version.py` | 2.2.4 → 2.2.5, Release-Name zu "EV & AWB Sliders", RELEASE_TYPE zu "minor" |

---

## 🔄 Upgrade-Hinweise

Kein Migrations-Aufwand erforderlich. Beim ersten Start nach dem Update:
- `/config/camera-settings.json` existiert noch nicht oder enthält nur `lens_position` → Fallback `ev=0.0, awb='auto'` wird verwendet
- Beim ersten Speichern über die Slider/Select werden alle Felder angelegt
- Bestehende `lens_position` Einstellungen werden beibehalten

### Deploy
```bash
cd ansible && export PATH="$HOME/.local/bin:$PATH" && bash build_and_deploy.sh --update
```

---

## 📊 Statistiken

- **Commits:** 1 (EV & AWB Feature)
- **Dateien geändert:** 2 (index.html, pi_daemon_secure.py)
- **Zeilen hinzugefügt:** ~120
- **Zeilen entfernt:** ~2

---

## ✅ Tipps zur Nutzung

### EV-Slider in der Praxis
- **Zu dunkel?** → EV auf +0.5 bis +1.5 erhöhen
- **Zu hell / überbelichtet?** → EV auf -0.5 bis -1.5 senken
- **Gegenlicht-Situation?** → EV auf +1.0 bis +2.0 stellen (Vogel hebt sich ab)
- **Nachts / schwach beleuchtet?** → EV auf +1.5 bis +2.0 (max)

### AWB-Selector in der Praxis
- **Tagsüber außen:** `Tageslicht` oder `Auto`
- **Bewölkt / grauer Himmel:** `Bewölkt`
- **Drinnen mit normalen Glühbirnen:** `Glühbirne` oder `Innen`
- **Drinnen mit LED-Neonröhren:** `Leuchtstoffröhre`
- **Sich unsicher?** `Auto` ist meist ein guter Standard

---

## 🔚 Fazit

v2.2.5 gibt Benutzern **volle Kontrolle über Belichtung und Weißabgleich**, ohne die Autofokus-Stabilität des manuellen Fokus-Sliders (v2.2.4) zu beeinflussen. Die Einstellungen sind persistent, einfach zu bedienen und sofort wirksam.
