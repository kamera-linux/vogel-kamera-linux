# 📋 CHANGELOG - Vogel-Kamera-Linux

## [2.3.8] - 22. August 2026 🔧 **Ansible Toolchain & E2E Testing Improvements**

### ✨ Features
- **Ansible Python-Interpreter explizit konfiguriert**
  - Warnung bei `Gathering Facts` eliminiert
  - `interpreter_python = /usr/bin/python3.13` in `ansible.cfg` gesetzt
  - Verhindert Ansible-Warnungen bei zukünftigen Deployments

- **E2E-Test Fehlerbehandlung verbessert**
  - Bessere TOTP-Code-Generierung mit Fallback-Support
  - Präzisere Fehlermeldungen (welches Tool fehlt: `oathtool` oder `pyotp`)
  - Optional: `pyotp` in venv für lokale E2E-Tests

### 🔧 Technische Änderungen
- `ansible/ansible.cfg` → `interpreter_python` explizit gesetzt
- `ansible/build_and_deploy.py` → pyotp-Import optimiert (globale HAS_PYOTP-Flag)
- `ansible/build_and_deploy.py` → `_generate_totp()` Fehlerbehandlung verfeinert
- `VERSION`, `raspberry-pi-scripts/VERSION` → 2.3.8
- `unified-monitor-client/VERSION` → 2.3.8
- `scripts/__version__.py`, `scripts/version.py` → 2.3.8

### 🧪 Testing
- ✅ E2E-Test mit TOTP funktioniert (wenn pyotp installiert)
- ✅ Ansible-Warnungen eliminiert
- ✅ Deployment erfolgreich mit `--update --no-cache --e2e`

### 🔗 Abhängigkeiten
- Optional: `pip install pyotp` für vollständige E2E-Tests

---

## [2.3.5] - 5. Mai 2026 🎬 **Slow-Motion Upgrade · High-Performance Recording**

### ✨ Features
- **Zwei Zeitlupen-Modi** mit optimalen Einstellungen
  - `slowmo` (HQ): **2304×1296 @ 56fps** → 1.9× langsamer (bessere Qualität, empfohlen)
  - `slowmo_fast`: **1536×864 @ 120fps** → 4× langsamer (ultra-highspeed)
  
- **Kamera-Optimierungen**
  - Automatische Auflösungswahl basierend auf FPS-Anforderung
  - Bessere CPU-Auslastung bei höheren Framerates
  - Profile im Web-Dashboard wählbar

### 🔧 Technische Änderungen
- `pi_daemon_secure.py` RECORDING_PROFILES erweitert
  - `slowmo_720p` → `slowmo_720p` (HQ): 2304×1296 @ 56fps
  - `slowmo_1080p` → `slowmo_1080p` (120fps): 1536×864 @ 120fps
- Resolution Map aktualisiert mit `slowmo_hq` & `slowmo_fast`
- Legacy Scripts: `--slowmo` und `--slowmo-fast` Flags
- Wiki-Dokumentation: Recording-Modes.md aktualisiert

### 📊 Performance-Vergleich (Neu)

| Modus | Auflösung | FPS | Verlangsamung | CPU | Qualität |
|-------|-----------|-----|--------------|-----|----------|
| **slowmo** (neu) | 2304×1296 | **56** | 1.9× | ~60% | ⭐⭐⭐⭐⭐ |
| slowmo_fast | 1536×864 | 120 | 4× | ~75% | ⭐⭐⭐⭐ |
| Alt: slowmo | 1920×1080 | 60 | 2× | ~50% | ⭐⭐⭐⭐ |

---

## [2.3.4] - 5. Mai 2026 🎤 **Audio-Qualität Upgrade · Professional Recording**

### ✨ Features
- **Professionelle Audio-Aufnahme mit ffmpeg** (`unified-monitor-client/pi_daemon_secure.py`)
  - Migration von `arecord` zu `ffmpeg` mit 48kHz Sample-Rate (statt 44.1kHz)
  - Audio-Filter: `highpass=f=80` (Brummtöne weg) + `volume=1.5` (bessere Aussteuerung)
  - Einheitliche Audio-Qualität: **Video+Audio und Audio-only nutzen jetzt die gleiche Pipeline**
  - Non-blocking stderr-Lesen → keine Deadlocks
  - Automatisches Fallback auf `arecord` mit 48kHz wenn ffmpeg fehlt

- **Audio-Filterung für alle Modi** (legacy scripts aktualisiert)
  - `legacy/raspberry-pi-scripts/unified-camera-monitor-manual.py` → ffmpeg Threads aktualisiert
  - `legacy/raspberry-pi-scripts/unified-camera-monitor.py` → ffmpeg Threads aktualisiert
  - `_start_audio_recording()` Methode → robustere Fehlerbehandlung
  - Alle Audio-Aufnahmen nutzen einheitlich 48kHz

### 🐛 Bugfixes
- **Audio-Datei nicht erstellt Fehler behoben**
  - Symptom: `Error opening output file /videos/2026_19_05_093547_audio_1min.wav`
  - Ursache: Complex ffmpeg-Filter `anoisremove=om=o:om=o:r=0.001,acompressor=...` zu fehleranfällig
  - Fix: Vereinfachte Filter (highpass + volume), besseres Error-Handling
  - Logging auf `warning` Level für bessere Diagnostik

- **Robuste Fehlerbehandlung bei Audio-Prozessen**
  - Nicht-blockierendes stderr-Lesen → verhindert Deadlocks
  - Explizites Process-Timeout + Kill-Group-Management
  - Fehler-Details in Logs und Web-UI sichtbar

### 📚 Dokumentation
- **AUDIO_QUALITY_IMPROVEMENTS.md** — Kurze Übersicht + Technische Details
- **AUDIO_UPGRADE_CHECKLIST.md** — Test-Checkliste + Troubleshooting
- **Release-Notes erweitert** → Audio-Wissenschaft (Warum 48kHz? Hochpass @ 80Hz?)

### 🔧 Geänderte Dateien
- `unified-monitor-client/pi_daemon_secure.py` → `record_audio()` komplett überarbeitet + `shutil` Import
- `legacy/raspberry-pi-scripts/unified-camera-monitor-manual.py` → `_start_audio_recording()` + `run_audio()` Thread
- `legacy/raspberry-pi-scripts/unified-camera-monitor.py` → `run_audio()` Thread aktualisiert
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/pi_daemon_secure.py` → 2.3.4
- `AUDIO_QUALITY_IMPROVEMENTS.md` (neu)
- `AUDIO_UPGRADE_CHECKLIST.md` (neu)
- `releases/v2.3.4/RELEASE_NOTES_v2.3.4.md` (neu)

### 🧪 Testing
- ✅ ffmpeg mit 48kHz nutzen (nicht 44.1kHz)
- ✅ Fallback zu arecord bei ffmpeg-Fehler
- ✅ Audio-Datei > 4KB nach Aufnahme
- ✅ Besseres Logging in Docker-Logs
- ✅ Deployment via hotpatch + update erfolgreich

### 🚀 Verwendung (Automatisch)
```bash
# Keine neuen Parameter erforderlich!
# Audio-Aufnahme nutzt automatisch:
# - ffmpeg mit 48kHz + Filter (Standard)
# - oder arecord mit 48kHz (Fallback)

# Web-UI 🎤 Audio Button
# - Startet Audio-Aufnahme mit verbesserter Qualität
# - Logs zeigen "48kHz" und Filterung-Status
```

### 📊 Qualitäts-Vergleich

| Aspekt | v2.3.3 | v2.3.4 |
|--------|--------|--------|
| **Sample-Rate** | 44.1 kHz | **48 kHz** |
| **Video-Sync** | Mismatch | **Perfekt** |
| **Rausch-Reduktion** | Keine | **Highpass @ 80Hz** |
| **Aussteuerung** | Variabel | **Optimiert (1.5x)** |
| **Fehlermeldung** | Vage | **Detailliert** |

---

## [2.3.3] - 4. Mai 2026 🏥 **Health-Check System · Daemon Resilience**

### ✨ Features
- **Unauthentifizierter /api/health Endpoint** (`unified-monitor-client/pi_daemon_secure.py`)
  - Neuer Endpoint: `GET /api/health` (vollständig ohne JWT/TOTP)
  - Response enthält: Status, Version, Uptime, CPU/Memory-Nutzung, Timestamp
  - Ideal für Docker HEALTHCHECK und Prometheus-Integration
  - Response-Zeit: ~50ms lokal, ~200ms remote
  - Keine Rate-Limiting, blockiert auch bei Last nicht

- **Health-Check Service und Monitor-Script** (Ansible)
  - Neue Datei: `pi-daemon-healthcheck.service` — Systemd-Service für kontinuierliche Überwachung
  - Neue Datei: `health-check-monitor.sh` — Bash-Script mit Auto-Restart bei Ausfall
  - Docker-Compose `healthcheck` erweitert mit neuen Check-Parametern
  - Docker-Dockerfile: `HEALTHCHECK` aktualisiert mit `/api/health`

### 📚 Dokumentation
- **Health-Check System komplett dokumentiert** (4 neue Dateien)
  - `docs/README-HEALTH-CHECK-SYSTEM.md` — Übersicht und Navigation (Alle)
  - `docs/HEALTHCHECK-CHEATSHEET.md` — Schnell-Referenz (Ops/DevOps)
  - `docs/HEALTHCHECK-OPTIMIZATION.md` — Detaillierte Architektur (Entwickler)
  - `docs/HEALTHCHECK-MERMAID.md` — 7 visuelle Diagramme (Architektur)

### 🔧 Geänderte Dateien
- `unified-monitor-client/pi_daemon_secure.py` → `/api/health` Endpoint + Resilience-Verbesserungen
- `docker/Dockerfile` → HEALTHCHECK-Instruction aktualisiert
- `ansible/roles/pi-daemon/templates/docker-compose.yml.j2` → healthcheck-Config
- `ansible/roles/pi-daemon/templates/pi-daemon.service.j2` → Graceful Shutdown
- `VERSION`, `scripts/version.py`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → 2.3.3
- `README.md` → Health-Check-Navigation hinzugefügt

### 🧪 Testing
- ✅ Health-Check Response-Zeit stabil (<50ms lokal, <200ms remote)
- ✅ Docker HEALTHCHECK funktioniert ohne Authentifizierung
- ✅ Service Restart bei Ausfall automatisch ✅ CPU/Memory-Overhead <0.5%
- ✅ Getestet auf Gentoo + Raspberry Pi 5

---

## [2.3.2] - 3. Mai 2026 🔧 **Gentoo Docker-Buildx-Fix · QEMU binfmt-Handler**

### 🐛 Bugfixes
- **Docker Buildx gRPC-Fehler auf Gentoo behoben** (v2.3.1 Regression)
  - Symptom: `error reading server preface: http2: frame too large` bei `docker buildx create --name pi-builder`
  - Ursache: QEMU aarch64 Segfault unter Gentoo's Hardened-Kernel (ASLR-Patches)
  - Betroffen: buildx v0.19.0–v0.21.2, nur auf Gentoo mit randomize_va_space=2
  - **Fix (Primary):** Fallback auf stabilen `default` docker-driver Builder statt `docker-container`-Driver
  - **Fix (Secondary):** Automatische tonistiigi/binfmt-Handler-Aktualisierung mit Workarounds

### ✨ Features
- **Automatische QEMU binfmt-Handler-Aktualisierung** (`ansible/build_and_deploy.py`)
  - Neue Funktion: `ensure_qemu_binfmt_handlers()` — wird vor jedem Build ausgeführt
  - `docker run --privileged tonistiigi/binfmt --install all` mit neuesten QEMU-Patches
  - Docker-Daemon wird automatisch neu gestartet nach Handler-Update
  - Manuell jederzeit testbar via `--setup-host`

- **Robuste Builder-Auswahl für Cross-Compilation**
  - Alt: `docker buildx create --name pi-builder --use` (gRPC-fehleranfällig)
  - Neu: `docker buildx use default` (stabil auf allen Linux-Distributionen)

### 📚 Dokumentation
- **Ansible README erweitert** (`ansible/README.md`)
  - Neue Sektion: "QEMU binfmt-Handler · Laufzeit-Updates"
  - Gentoo Kernel-Parameter (mmap_rnd_bits, randomize_va_space)
  - Manuelle binfmt-Handler-Aktualisierung
  - ASLR-Konfiguration für Gentoo

### 🔧 Geänderte Dateien
- `ansible/build_and_deploy.py` → `ensure_qemu_binfmt_handlers()` + `docker buildx use default`
- `ansible/README.md` → Neue Sektion über QEMU binfmt-Handler
- `VERSION`, `scripts/version.py`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → 2.3.2

### 🧪 Testing
- ✅ Mehrfache erfolgreiche ARM64-Builds auf Gentoo (kein gRPC-Fehler)
- ✅ Build-Zeit: ~760 Sekunden für vollständigen Dockerimage-Build
- ✅ Deployment + Ansible + E2E-Test bestanden

---

## [2.3.1] - 6. April 2026 🐛 **Hailo-Deadlock-Fix · Container-Status-Kachel**

### 🐛 Bugfixes
- **Hailo-Temp Deadlock behoben** (`pi_daemon_secure.py`) — kritischer Fix
  - Wenn `rpicam-hello` `/dev/hailo0` hielt, ging `Device()` in D-State (Uninterruptible Sleep)
  - SIGKILL nach Timeout half nicht (D-State-Prozesse ignorieren Signale)
  - `communicate()` blockierte im HTTP-Request-Thread → Web-Server fror komplett ein
  - 20+ hängende `python3`-Prozesse akkumulierten sich, Container wurde `unhealthy`
  - **Fix:** Hailo-Temp-Fetching aus HTTP-Thread ausgelagert → Background-Daemon-Thread
  - `subprocess.Popen` + `start_new_session=True` + `os.killpg` ohne zweites `communicate()`
  - HTTP-Handler liest nur noch aus `_hailo_temp_bg`-Dict (nie blockierend)

### ✨ Features
- **Container-Status-Kachel im Dashboard** (`pi_daemon_secure.py`, `web/index.html`)
  - Neue Kachel „Container Status" im System-Bereich
  - `✓ Healthy` (grün) wenn API antwortet, `✗ Unhealthy` (rot) bei Verbindungsabbruch
  - `apiFetch()` um `try/catch` erweitert: gibt `null` bei Netzwerkfehler zurück (kein unbehandelter Promise-Rejection-Fehler)

### 🔧 Geänderte Dateien
- `unified-monitor-client/pi_daemon_secure.py` → Background-Thread `_hailo_temp_updater()` + `APP_VERSION` 2.3.1
- `unified-monitor-client/web/index.html` → Container-Status-Kachel + `apiFetch()` try/catch
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION`, `scripts/__version__.py`, `scripts/version.py` → 2.3.1

---

## [2.3.0] - 5. April 2026 🚀 **NPU Throttle-Level · Dashboard Stats · Favicon**

### ✨ Features

#### 🔬 NPU Throttle-Level Anzeige (Dashboard)
- **Throttle-Level statt Zone:** Dashboard-Kachel zeigt nun `– Normal` (grün) oder `L0–L3` mit aktueller Taktfrequenz in MHz (orange/rot) statt einer abstrakten Zone-Nummer
- **Farbkodierung:** Normal = grün, L0 = orange (104 °C Schwelle), L1–L3 = rot (108/112/116 °C)
- **Hailo-8 Throttle-Tabelle:**
  - L0: 104 °C → 350 MHz | L1: 108 °C → 300 MHz | L2: 112 °C → 250 MHz | L3: 116 °C → 200 MHz
- **Backend:** `_HAILO_TEMP_SCRIPT` liefert jetzt 5 CSV-Felder (neu: `current_temperature_throttling_level`)
- **Label:** „Throttle-Zone" → „Throttle-Level"

#### 📊 Dashboard-Erweiterungen (System & Netzwerk)
- **Uptime seit Neustart:** Neue Kachel „Uptime" zeigt laufende Betriebszeit des Pi (z. B. `2 Tage 14:32`)
- **Container RAM:** neue Kachel zeigt RSS-Speicherverbrauch des `pi-daemon`-Prozesses (`psutil`)
- **Netzwerk I/O:** zwei Kacheln „Empfangen" und „Gesendet" (kumulativer Netzwerkdurchsatz seit Boot, `eth0`/`wlan0`)
- **4 semantische Gruppen** im Dashboard: 🎯 Kamera & Erkennung · 🔬 NPU · 🖥️ System · 🌐 Netzwerk

#### ❓ Online-Hilfe vollständig überarbeitet
- Hilfe-Modal spiegelt jetzt die 4 Dashboard-Gruppen 1:1 wider
- **NPU-Abschnitt** mit detaillierter Throttle-Level-Erklärung (Temperaturgrenzen + MHz je Stufe)
- **System-Abschnitt** mit Load Avg, Uptime, Container RAM und Netzwerk I/O
- Veraltete Einträge entfernt

#### 🌐 Browser Favicon / Tray-Icon
- Vorhandenes `logo.png` wird nun als Browser-Tab-Icon eingebunden (`<link rel="icon">`)
- `<link rel="apple-touch-icon">` für iOS-Homescreen-Icon (Seite zum Homescreen hinzufügen)
- Kein separates `.ico`-File nötig

### 🔧 Geänderte Dateien
- `unified-monitor-client/pi_daemon_secure.py` → `_HAILO_TEMP_SCRIPT` (5 Felder), `throttle_level`-Cache, Uptime, Container RAM, Netz-I/O
- `unified-monitor-client/web/index.html` → Throttle-Level-JS, 4 Gruppen, neue Kacheln, Favicon-Links, überarbeitetes Hilfe-Modal
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION`, `scripts/__version__.py`, `scripts/version.py` → 2.3.0

---

## [2.2.6] - 31. März 2026 🐛 **Bugfix: Detection-Prozess & Aufnahmen-Tageszähler**

### 🐛 Bugfixes
- **Detection-Prozess-Race-Condition behoben** (`pi_daemon_secure.py`)
  - Sequenz: Stop Detection → manuelle Aufnahme → Detection-Mode aktivieren startete zwei `rpicam-hello`-Prozesse gleichzeitig
  - Beide konkurrierten um die Kamera und crashten mit `rc=1`
  - Fix: Explizites Killen des vorhandenen Detection-Prozesses + 1s Wartezeit für libcamera-Freigabe in `start_detection_mode()`

### ✨ Features
- **Aufnahmen-Tageszähler im Web-Dashboard** (`pi_daemon_secure.py`, `web/index.html`)
  - Neue Funktion `_count_today_recordings()` zählt `.mp4`-Dateien mit heutigem mtime in `VIDEO_BASE_DIR`
  - Neues API-Feld `today_recordings` in `/api/status`
  - Dashboard-Karte umbenannt von „Objekte aufgenommen" zu „Aufnahmen heute"
  - Datum wird neben der Anzahl angezeigt (flexbox, baseline-aligned)
  - Persistent nach Container-Neustart (basiert auf Dateisystem, nicht Session)
- **Ansible Hotpatch-Infrastruktur** (`ansible/playbooks/hotpatch.yml`, `build_and_deploy.py`)
  - Neues Playbook `hotpatch.yml`: Kopiert geänderte Dateien direkt in laufenden Container
  - `python3 build_and_deploy.py --hotpatch` ohne Docker-Build/Transfer
  - Ansible `README.md` mit Hotpatch-Dokumentation erweitert

### 🔧 Geänderte Dateien
- `unified-monitor-client/pi_daemon_secure.py` → Bugfix + `_count_today_recordings()` + `today_recordings` im API
- `unified-monitor-client/web/index.html` → „Aufnahmen heute"-Karte mit Datum
- `ansible/playbooks/hotpatch.yml` → **NEU**
- `ansible/build_and_deploy.py` → `--hotpatch`-Argument
- `ansible/README.md` → Hotpatch-Dokumentation
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION`, `scripts/__version__.py`, `scripts/version.py` → 2.2.6

---

## [2.2.5] - 21. März 2026 ☀️ **EV, AWB & Bildqualität-Sliders**

### ✨ Features
- **EV-Slider (Exposure Value / Belichtung) im Web-GUI**
  - Neuer Schieberegler „☀️ Belichtung (EV)" im Aufnahme-Bereich (Bereich: -2.0 bis +2.0)
  - Standard: **0.0** (normale Belichtung)
  - Negative Werte abdunkeln das Bild, positive Werte hellen auf
  - Live-Anzeige während des Ziehens, Speicherung via `POST /api/camera-settings`
  - Status-Anzeige: `…` → `✓ gespeichert` (2,5 s) oder `✗ Fehler`
  - Slider wird beim Login automatisch mit dem gespeicherten Wert befüllt (`loadEVSetting()`)
  - Polling-Schleife hält Slider synchron (nur wenn Slider nicht aktiv angefasst wird)

- **AWB-Selector (Auto White Balance / Weißabgleich)**
  - Neue Selectbox „💡 Weißabgleich (AWB)" mit 6 vordefinierten Modi:
    - `Auto` (Standard) – automatischer Weißabgleich, vielseitig einsetzbar
    - `Daylight` – optimiert für Sonnenlicht außen
    - `Cloudy` – für bewölkten Himmel
    - `Tungsten` – für warme Glühbirnenbeleuchtung
    - `Fluorescent` – für LED/Neon-Beleuchtung
    - `Indoor` – allgemeine Innenbeleuchtung
  - OnChange-Handler speichert sofort via `POST /api/camera-settings`
  - Status-Anzeige für Benutzerfeedback
  - Selectbox wird beim Login automatisch mit dem gespeicherten Wert befüllt (`loadAWBSetting()`)
  - Polling-Schleife hält Selectbox synchron

- **🎨 Bildqualität-Regler (Brightness, Contrast, Saturation, Sharpness, Gain)**
  - Neue 5 Schieberegler im Web-GUI für erweiterte Bildqualität-Kontrolle:
    - **🌞 Brightness** (-1.0 bis +1.0, Standard: 0.0) – gezieltes Abdunkeln/Aufhellen
    - **⚪ Contrast** (0.5 bis 2.0, Standard: 1.0) – Kontrolle über Kontrastverhältnis
    - **🌈 Saturation** (0.0 bis 2.0, Standard: 1.0) – Farbintensität (0.0 = Graustufenbild)
    - **✨ Sharpness** (0.0 bis 2.0, Standard: 1.0) – digitales Sharpening / Weichzeichnen
    - **🔆 Gain** (1.0 bis 8.0, Standard: 1.0) – digitale Verstärkung für Lowlight (ISO-äquivalent)
  - Alle Parameter folgen EV/AWB-Pattern: Live-Label, Status-Anzeige, persistente Speicherung
  - Globale Variablen: `_brightness`, `_contrast`, `_saturation`, `_sharpness`, `_gain`
  - ✅ Remote-Tests bestätigt alle 5 Parameter sind funktional und produktionsreif:
    - ✅ brightness -0.5 (verdunkelung bei Gegenlicht)
    - ✅ contrast 1.5 (erhöhte Kontraste für bessere Definition)
    - ✅ saturation 0.8 (natürlichere Farben)
    - ✅ sharpness 1.2 (digitales Sharpening für mehr Details)
    - ✅ gain 2.0 (digitale Verstärkung für Lowlight-Szenarien)

- **Backend: Erweiterte `/api/camera-settings` Endpunkte**
  - `GET /api/camera-settings` → `{ "lens_position": 3.0, "ev": 0.0, "awb": "auto", "brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "sharpness": 1.0, "gain": 1.0 }`
  - `POST /api/camera-settings` mit beliebiger Kombination aller 8 Parameter möglich
  - Validierung: float-Ranges mit min/max-Clamping (brightness -1.0..+1.0, contrast 0.5..2.0, saturation 0.0..2.0, sharpness 0.0..2.0, gain 1.0..8.0)
  - Fehler-Response `400 Bad Request` bei ungültigen Werten

- **rpicam-vid Parameters für alle 8 Kamera-Einstellungen**
  - `--lens-position`, `--ev`, `--awb`, `--brightness`, `--contrast`, `--saturation`, `--sharpness`, `--gain`
  - Beide Aufnahme-Modi (H.264 Slowmo + libav/MP4 Normal) erhalten alle Parameter
  - Parameter werden sofort auf alle neuen Aufnahmen angewendet

- **Persistenz: `/config/camera-settings.json` erweitert**
  - `_load_camera_settings()` / `_save_camera_settings()` unterstützen alle 8 Parameter
  - Fallback-Defaults: brightness=0.0, contrast=1.0, saturation=1.0, sharpness=1.0, gain=1.0
  - `/api/status` liefert alle 8 Parameter im Response-Body mit

- **Online-Hilfe erweitert**
  - Abschnitt „📷 Kamera-Einstellungen" mit allen 3 Grundparametern (Fokus, EV, AWB)
  - **NEUER Abschnitt:** „🎨 Bildqualität-Einstellungen" mit detaillierten Erklärungen aller 5 neuen Parameter
  - Kombinationstipps für verschiedene Aufnahmeszenarien:
    - Bright outdoor daylight
    - Overexposed (Gegenlicht)
    - Shady bird feeder
    - Very dark (Lowlight)
    - High contrast scenes

### 📁 Files Changed
- `unified-monitor-client/web/index.html` → 5 neue Bildqualität-Slider (brightness, contrast, saturation, sharpness, gain), 25 neue JavaScript-Funktionen, Online-Hilfe erweitert um neuen Abschnitt
- `unified-monitor-client/pi_daemon_secure.py` → `_load_camera_settings()` erweitert um 5 Parameter, Globale Variablen `_brightness`, `_contrast`, `_saturation`, `_sharpness`, `_gain`, `api_camera_settings()` erweitert, rpicam-vid Parameter für beide Aufnahme-Pfade, `/api/status` um 5 Parameter erweitert
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → 2.2.5 (nicht verändert, da bereits v2.2.5)

---

## [2.2.4] - 20. März 2026 🔭 **Manueller Fokus-Slider**

### ✨ Features
- **Manueller Fokus-Slider im Web-GUI**
  - Neuer Schieberegler „🔭 Fokus" im Aufnahme-Bereich (Bereich: 0.5 – 10.0)
  - Echtzeit-Abstandsanzeige: `lens_position` wird in Zentimeter umgerechnet (z. B. `3.0 (≈ 33 cm)`)
  - Hilfslabel `(0.5=2m … 10=10cm)` für Orientierung
  - Onchange-Handler speichert sofort via `POST /api/camera-settings`
  - Status-Anzeige: `…` → `✓ gespeichert` (2,5 s) oder `✗ Fehler`
  - Slider wird beim Login automatisch mit dem gespeicherten Wert befüllt (`loadLensPosition()`)
  - Polling-Schleife hält Slider synchron (nur wenn Slider nicht aktiv angefasst wird)

- **Backend: `/api/camera-settings` Endpunkt**
  - `GET /api/camera-settings` → `{ "lens_position": 3.0 }`
  - `POST /api/camera-settings` `{ "lens_position": <0.0–10.0> }` → setzt `_lens_position`, persistiert in `/config/camera-settings.json`
  - Validierung: `max(0.0, min(10.0, lp))`, Fehler-Response bei ungültigem Typ

- **`--lens-position` in Aufnahme-Kommandos**
  - Alle `rpicam-vid`-Aufrufe (H.264 und libav/MP4) erhalten `--autofocus-mode manual --lens-position <wert>`
  - Fokus bleibt damit über Aufnahmen hinweg reproduzierbar statt autofocus-drift

- **Persistenz: `/config/camera-settings.json`**
  - `_load_camera_settings()` / `_save_camera_settings()` analog zu Detection-Settings
  - Fallback: `lens_position = 3.0` (≈ 33 cm) wenn Datei fehlt oder unlesbar
  - `/api/status` liefert `lens_position` im Response-Body mit

### 📁 Files Changed
- `unified-monitor-client/web/index.html` → Fokus-Slider-UI, `updateLensLabel()`, `loadLensPosition()`, `saveLensPosition()`, Polling-Sync
- `unified-monitor-client/pi_daemon_secure.py` → `_load/save_camera_settings()`, `_lens_position`, `--lens-position` in rpicam-vid, `/api/camera-settings`, `/api/status`-Erweiterung
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → 2.2.4
- `scripts/__version__.py`, `scripts/version.py` → 2.2.4

---

## [2.2.3] - 17. März 2026 🎯 **Aufnahmedauer-Fix & Dashboard-Korrekturen**

### 🐛 Bugfixes
- **Aufnahmedauer wird im Detection-Modus nicht gespeichert**
  - `rec-dur`-Slider feuerte kein `change`-Event zum persistenten Speichern
  - Beim Schieben auf z. B. 3 min wurde `/api/rec-settings` nicht aufgerufen
  - Folge: Watchdog startete Aufnahme immer mit alter / Default-Dauer (15 s)
  - Fix: `durEl.addEventListener('change', saveRecSettings)` ergänzt — Speichern bei Slider-Release

- **Backend-Maximalwert für Aufnahmedauer zu niedrig**
  - `min(..., 300)` kappte Aufnahmen bei 5 Minuten, Slider zeigte aber bis 10 min
  - Fix: Limit auf 600 s (10 min) erhöht — in `/api/rec-settings` und `/api/record`

- **Broken HTML-Struktur der Dashboard-Kacheln**
  - Nach Einführung der „Erkennungsziel"-Kachel fehlten `<div class="card">` und `<div class="label">` Wrapper der „Hailo NPU"-Kachel
  - Fix: Korrekte Card-Struktur wiederhergestellt

### ✨ Features (aus 2.2.2-Session, jetzt als eigenständige Version gebündelt)
- **Neue Erkennungsziele: Hund, Katze, Alle 4**
  - `TARGET_CLASSES` in `unified-camera-monitor-hailo.py` um `dog`, `cat`, `all4` erweitert
  - Backend-Whitelist in `pi_daemon_secure.py` entsprechend erweitert
  - GUI: 5 Radio-Buttons `🐦 Vogel | 🧍 Mensch | 🐕 Hund | 🐈 Katze | 🐦🧍🐕🐈 Alle 4`

- **Neue Status-Kacheln im Dashboard**
  - „Hailo NPU" — Aktiv/Inaktiv-Pill je nach laufendem Prozess
  - „Objekt erkannt" — letzte erkannte Klasse + Konfidenz + Uhrzeit
  - „Erkennungsziel" — aktuell konfiguriertes Ziel mit Icon und Konfidenzschwelle
  - Hailo-Script schreibt `/tmp/last-detection.json`, Daemon liest es via `_read_last_detection()`

- **Detection-Modus-Lebenszyklus-Fixes**
  - Detection-Prozess startet nach Aufnahme automatisch neu (Watchdog-Fix)
  - `start_detection_mode()` early-return-Guard: `detection_mode AND detection_running` statt nur `detection_mode`
  - `birds_recorded` wird nur beim ersten Aktivieren der Session zurückgesetzt

### 📁 Files Changed
- `unified-monitor-client/web/index.html` → Slider-change-Event, neue Kacheln, Hund/Katze/Alle-4-Radios, HTML-Strukturfix
- `unified-monitor-client/pi_daemon_secure.py` → Aufnahmedauer-Caps 300→600 s, Whitelist dog/cat/all4, `_read_last_detection()`, Detection-Modus-Fixes
- `raspberry-pi-scripts/unified-camera-monitor-hailo.py` → dog/cat/all4 TARGET_CLASSES, `/tmp/last-detection.json`
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → 2.2.3
- `scripts/__version__.py`, `scripts/version.py` → 2.2.3

---

## [2.2.2] - 16. März 2026 🔬 **Hailo-NPU Detection & Engine-Switcher**

### ✨ Features
- **Hailo-8 NPU Detection via `rpicam-hello`**
  - Neues Script `unified-camera-monitor-hailo.py` für Hailo-NPU-Betrieb
  - YOLOv8 HEF-Inferenz direkt auf der Hailo-8 NPU (26 TOPS), 25 fps, < 5 % CPU
  - `rpicam-hello --post-process-file hailo_yolov8_inference.json` als Subprocess
  - 3 Startversuche mit 2 s Pause, 5 s Wartezeit zwischen den Durchläufen
  - Watchdog ist Hailo-bewusst: kein imx708-Reset bei rpicam-hello-Fehlern

- **Detection-Engine-Switcher**
  - `DETECTION_ENGINES`-Registry in `pi_daemon_secure.py` (`hailo`, `cpu_yolo`)
  - Persistenz: aktive Engine wird in `/config/detection-engine.json` gespeichert
  - Laufzeit-Umschaltung via `POST /api/detection-engine` ohne Daemon-Neustart
  - `/api/status` liefert neues Feld `active_engine`
  - Web-GUI: Dropdown „Detection Engine" im Detection-Panel
  - `cpu_yolo` in der GUI als `disabled` markiert (kein `picamera2` im Container)

- **Live-Vorschau UX bei Hailo-Detection**
  - Bei HTTP 503 + laufender Detection: sofortige Meldung „🔬 Hailo-NPU Detection läuft – kein Live-Frame verfügbar"
  - Kein irreführendes „Kein Bild" nach 40 Polling-Versuchen mehr
  - `_detectionRunning`-Variable im JS wird aus `fetchStatus()` synchronisiert

### 🐛 Bugfixes
- **Watchdog-String-Check:** `'hailo' in DETECTION_SCRIPT` → `_active_engine == 'hailo'`
- **Ansible:** `pi_detection_script` in `group_vars/all/vars.yml` auf `unified-camera-monitor-hailo.py` (war: `detect-only.py`) — verhindert `.env`-Überschreibung beim `--update`

### 📁 Files Changed
- `unified-monitor-client/pi_daemon_secure.py` → APP_VERSION, DETECTION_ENGINES, Engine-API, Watchdog-Fix
- `unified-monitor-client/web/index.html` → `_detectionRunning`, Hailo-UX-Meldung, Engine-Dropdown
- `ansible/group_vars/all/vars.yml` → `pi_detection_script` → hailo
- `raspberry-pi-scripts/unified-camera-monitor-hailo.py` → Neues Hailo-Detection-Script
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → 2.2.2
- `scripts/__version__.py` → 2.2.2

---

## [2.2.1] - 15. März 2026 🖥️ **Web-GUI Verbesserungen & HTTPS-Komfort**

### ✨ Features
- **Versions-Badge in der Topbar**
  - `APP_VERSION = '2.2.1'` Konstante in `pi_daemon_secure.py`
  - `/api/status` liefert jetzt `"version"` Feld
  - JS-Badge `<small id="gui-version">` wird beim ersten Status-Poll befüllt

- **Projekt-Logo in der Web-GUI**
  - Login-Bildschirm: Logo 220 px zentriert über dem Formular
  - Topbar: Logo 32 px (ersetzt 🐦-Emoji)
  - Neue Route `GET /web/<filename>` via `send_from_directory`

- **HTTPS-Zertifikat: Download & Chrome-Importanleitung**
  - Neue Route `GET /cert.pem` (keine Auth) — liefert Zertifikat als Download
  - Login-Seite: direkter Download-Link + schrittweise Chrome-Anleitung
  - SSL SAN erweitert: `DNS:localhost`, Pi-IP, `IP:127.0.0.1`, CN dynamisch

- **Hilfe-Modal vervollständigt**
  - `🎤 Audio-Only Aufnahme` Sektion hinzugefügt
  - `📷 Live-Vorschau` Sektion hinzugefügt

### 🐛 Bugfixes
- **E2E-Test:** Profilname `"FHD"` → `"normal_hd"` in `build_and_deploy.sh` (HTTP 400 Fix)
- **Dockerfile:** `--platform` aus `FROM`-Zeile entfernt (Warnung `RedundantTargetPlatform`)

### 📁 Files Changed
- `unified-monitor-client/pi_daemon_secure.py` → APP_VERSION, version-API, /web/, /cert.pem
- `unified-monitor-client/web/index.html` → Logo, Version-Badge, Cert-Hinweis, Hilfe-Modal
- `unified-monitor-client/web/logo.png` → Neu: Projekt-Logo
- `ansible/build_and_deploy.sh` → E2E-Profil Fix
- `ansible/roles/ssl/tasks/main.yml` → erweiterter SAN
- `docker/Dockerfile` → `FROM python:3.13-slim-bookworm` (kein --platform)
- `VERSION` → 2.2.1

---

## [2.2.0] - 13. März 2026 🐳 **Docker & Ansible Build-Infrastruktur**

### 🐳 Major Features
- **Ansible Build-Host Rolle (Gentoo)**
  - Neue Rolle `ansible/roles/build-host/` richtet lokalen Rechner ein
  - Installiert Docker CE, QEMU (aarch64 User-Space), docker-buildx via `emerge`
  - Persistente `binfmt_misc`-Registrierung via `/etc/local.d/qemu-binfmt.start`
  - Idempotent: kann mehrfach ausgeführt werden ohne unbeabsichtigte Änderungen

- **Neuer `--setup-host` Befehl**
  - `./ansible/build_and_deploy.sh --setup-host` richtet Gentoo Build-Rechner ein
  - Läuft vollständig lokal (kein Pi-Zugriff nötig)
  - Interaktive `sudo`-Passwort-Abfrage via `--ask-become-pass`

- **Ansible Playbook für Build-Host**
  - `ansible/playbooks/setup-build-host.yml` targets `localhost`
  - `build_host_user` wird automatisch aus `$USER` ermittelt

### ✨ Improvements
- `ansible/README.md`: Neue vollständige Ansible-Dokumentation hinzugefügt
- `docker/README.md`: Ansible-Tipp-Box für automatische Einrichtung ergänzt
- `ansible/group_vars/all/vars.yml`: `build_host_user` Variable hinzugefügt
- `build_and_deploy.sh --help`: Alle vier Befehle dokumentiert

### 📁 Files Added
- `ansible/README.md` → neue Dokumentation
- `ansible/playbooks/setup-build-host.yml` → neues Playbook
- `ansible/roles/build-host/tasks/main.yml` → neue Rolle
- `docker/README.md` → Gentoo Cross-Compilation Anleitung

### 📁 Files Updated
- `VERSION` → 2.2.0
- `unified-monitor-client/VERSION` → 2.2.0
- `raspberry-pi-scripts/VERSION` → 2.2.0
- `scripts/__version__.py` → 2.2.0
- `ansible/build_and_deploy.sh` → `--setup-host` Flag ergänzt
- `ansible/group_vars/all/vars.yml` → `build_host_user` ergänzt

---

## [2.1.2] - 11. März 2026 🔒 **Sichere Konfiguration & Datenschutz**

### 🔐 Major Features & Security
- **Sichere Konfigurationsverwaltung**
  - `config.py` und `.env` in `.gitignore` - persönliche Daten werden nicht synced
  - Template-Dateien: `config.example.py` und `.env.example` für öffentliches Repo
  - Neutrale Platzhalter in Example-Dateien für neue Benutzer
  - Realistische Defaults in produktiven Dateien (lokal)

- **Flexible SSH-Konfiguration**
  - SSH-Werte nach Priorität geladen: `.env` → Fallback-Defaults
  - Dynamische Path-Konstruktion: `/home/{SSH_USER}/..` statt hardcoded `/home/roimme/`
  - Support für Custom-SSH-Keys, Usernames, Hostnames
  - SSH_PORT Konfiguration hinzugefügt

- **Datenschutz im Repo**
  - `.gitignore` schützt: `.env`, `config.py`, `unified-monitor-client/.env`, `unified-monitor-client/config.py`
  - `.example`-Dateien as Dokumentation & Setup-Vorlage
  - KEINE hardcoded persönlichen Daten in Skripten

### ✨ Improvements
- `monitors.py`: Dynamische `PI_HOME` statt hardcoded `/home/roimme`
- `unified-monitor-client/`: Vollständige Konfigurationsstruktur mit Beispielen
- Klar gekennzeichnete Example-Dateien mit ausführlicher Setup-Anleitung
- Version-Vollständigkeit: alle Komponenten auf 2.1.2 synchronisiert

### 🔧 Technical Changes
- `config.py` liest `.env` via `python-dotenv`
- Fallback-System ermöglicht Scripts ohne `.env` (mit Defaults)
- Alle Remote-Pfade basieren auf `SSH_USER` Variable
- Robuste Handling von fehlenden Umgebungsvariablen

### 📁 Files Updated
- `VERSION` → 2.1.2
- `unified-monitor-client/VERSION` → 2.1.2
- `raspberry-pi-scripts/VERSION` → 2.1.2
- `scripts/__version__.py` → 2.1.2
- `.gitignore` → erweitert mit config-Dateien
- `.env` → reale Werte
- `config.py` → reale Defaults + dotenv-Integration
- `.env.example` → neutrale Platzhalter
- `config.example.py` → Template für neue Nutzer
- `monitors.py` → dynamische Pfade statt hardcoded

## [2.1.1] - 10. März 2026 🧹 **Graceful Shutdown & Process Management**

### 🛑 Major Features
- **Graceful Ctrl+C Shutdown**
  - Sauberes Cleanup aller Remote-Prozesse bei Ctrl+C
  - Sequenzielle Shutdown-Phasen: StatusReporter → Detection → Remote → SSH
  - Globale Variablen für Signal-Handler-Zugriff auf Ressourcen
  - Try/Exception-Handling für jede Cleanup-Phase

- **Process Diagnostics & Monitoring**
  - `diagnose_remote_processes()` zeigt blockierende Prozesse VOR Cleanup
  - Sichtbarkeit in: laufende Prozesse, offene File-Handles, V4L2-Devices
  - Hilft bei Debugging von "Device or resource busy" Fehlern

- **Improved Process Cleanup**
  - 3-stagige Cleanup statt aggressivem Kill-All
  - Stage 1: Gezielte SIGTERM zu Camera-Prozessen (2s Warte)
  - Stage 2: Aggressive SIGKILL nur zu Zielprozessen (NICHT alle python3!)
  - Stage 3: V4L2-Device-Locks freigeben + Log-Files cleanup
  - Verification: Zählt verbleibende Prozesse nach Cleanup

- **🆕 Detect-and-Record Mode** (Zwei-Phasen-Betrieb)
  - **Phase 1 - Detection:** Fokussierte Vogelerkennung (KEIN Video-Speichern)
    - Schnelle YOLO-Inference ohne Overhead
    - Minimale CPU/RAM (nur Erkennung, kein Encoding)
  - **Phase 2 - Recording:** Nach Trigger → Volle Aufnahme mit Audio
    - Sequenzieller Betrieb: erst erkennen, dann aufnehmen
    - Verhindert Time-Lapse/beschleunigte Vorschau-Probleme
  - `--detect-and-record --repeat` für Endlosschleife

### ✨ Improvements
- SSH-Connection bleibt über beide Phasen erhalten
- StatusReporter läuft während Detection-Phase
- Bessere Log-Ausgaben bei Cleanup-Fehlern
- Video wird erst nach Vogel-Erkennung geschrieben (Speicher-effizient)
- Globale Fehlerbehandlung mit Fallback-Verhalten

### 🔧 Technical Changes
- Globale Variablen: `_global_ssh`, `_global_status_reporter`, `_cleanup_on_exit`
- Signal-Handler mit vollständigem Cleanup-Orchester
- Remote-Prozess-Diagnostik für Fehlersuche
- Targeted Process-Killing statt Wildcard-Kill
- Try/Except-Wrapper um alle Critical Operations

### 🗂️ Architecture
- `unified_monitor_client.py`: Hauptprogramm mit Signal-Handler + Cleanup
- `config.py`: Konfiguration & Konstanten
- `ssh_manager.py`: SSH-Verbindungsmanagement
- `monitors.py`: Log-, Video-, Status-Monitoring
- `version_manager.py`: Versionsprüfung & Remote-Sync

---

## [2.1.0] - 8. März 2026 🎙️ **Audio/Video-Synchronisation**

### 🎙️ Major Features
- **Thread-basierte Audio/Video-Synchronisation**
  - Video + Audio starten parallel in separaten Threads
  - Beide Streams laufen für exakt gleiche Duration
  - Eliminierung aller Timing-Fehler beim MP4-Merge
  
- **USB-Audio-Stick Integration**
  - Automatische Geräte-Erkennung (hw:0,0, hw:1,0-3,0)
  - arecord: 44.1kHz Mono, S16_LE WAV
  - Fallback-Mechanismus bei nicht gefundenem Gerät
  
- **rpicam-vid Native Integration**
  - Ersetzt libcamera/picamera2 für bessere Codec-Kontrolle
  - Alle Parameter verfügbar: Rotation, Codec, HDR, Autofokus, ROI
  - **4096x2160 Cinema 4K** @ 30fps als Standard
  
- **Manual Recording Mode**
  - Direkte N-Sekunden Aufnahmen ohne AI-Watchdog
  - `--manual-record --recording-duration 60` Syntax
  - Mit oder ohne Audio

### ✨ Improvements
- Rotation 180° als Default (Vogelbild oben, nicht kopfüber)
- ffmpeg Merge mit `-fflags +genpts` für korrekte Timestamps
- Enhanced parameter logging (zeigt alle Einstellungen)
- Slow-Motion Support (60fps statt 30fps)
- Auto-Detection von Audio-Device beim Start

### 🔧 Technical Changes
- Python Threading statt sequenzielle Ausführung
- ffmpeg Parameter: `-fflags +genpts -r {fps}` (KEINE `-shortest` Flag)
- rpicam-vid Command-Building mit vollständigen Parametern
- Dynamic USB Audio Device Search mit mehreren Fallbacks

### 🗑️ Removed
- ❌ `raspberry-pi-scripts/setup-unified-monitor.sh` (veraltet)
- ❌ `raspberry-pi-scripts/start-unified-monitor.sh` (veraltet)
- ❌ picamera2 Abhängigkeit (nicht mehr nötig)

### 📚 Documentation
- ✅ `raspberry-pi-scripts/UNIFIED-MONITOR-README.md` - Komplett neu
- ✅ `releases/v2.1.0/RELEASE_NOTES_v2.1.0.md` - Detaillierte Notes
- ✅ `README.md` - v2.1.0 Highlights
- ✅ Alle Verweise auf gelöschte .sh Dateien entfernt

### ✅ Known Working
- Parallel Video + Audio Aufnahme (5s, 60s+ getestet)
- Perfect MP4 Merge mit durchgehörendem Audio
- Auto-Transfer via rsync zum Client-PC
- AI-Watchdog Modus (mit Einschränkungen)

### ⚠️ Known Limitations
- Watchdog-Modus: Keine Parallelisierung mit Live-Preview möglich
- Multi-Camera: Nur `--camera 0` oder `--camera 1` (noch nicht optimiert)

### 🔗 Related
- Audio-Integration Changelog: [AUDIO-FIX-CHANGELOG.md](AUDIO-FIX-CHANGELOG.md)

---

## [2.0.2] - 2025-11-11 🔧 Maintenance Release

### Features
- YOLO26 Migration (yolo26n.pt statt yolov8n.pt)
- Verbesserte Erkennungsgenauigkeit
- ultralytics>=26.0.0 Support

### Fixes
- CPU/RAM-Anzeige-Fehler (falsche PID, Locale-Komma)
- Kamera-Start-Konflikt durch rpicam-vid-Watchdog
- SSH-Timeout-Verbesserungen

### Documentation
- Trixie (Debian 13) Migration Guide
- Updated Hardware Requirements

---

## [2.0.1] - 2025-09-15 📸 rpicam-vid Integration

### Features
- rpicam-vid statt libcamera direkt
- Improved reliability
- Better codec support

### Fixes
- Stream stability improvements
- Connection handling

---

## [2.0.0] - 2025-08-01 🚀 Major Rewrite

### Breaking Changes
- Unified Camera Monitor System
- New Python architecture
- Debian Trixie requirement

### Major Features
- YOLOv8 Integration
- Real-time bird detection
- Automatic recording trigger

---

## [1.2.5] - 2025-06-15 🎥 Bookworm Legacy Release

### Status
- Last Bookworm (Debian 12) version
- Legacy branch support continues
- See: bookworm-legacy branch

---

## Installation der aktuellen Version

```bash
# Clone repository
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux

# Update to v2.1.0
git checkout main
git pull origin main

# Install dependencies
sudo apt install -y rpicam-apps alsa-utils ffmpeg
pip install ultralytics opencv-python numpy

# Test
cd raspberry-pi-scripts/
python3 unified-camera-monitor.py --manual-record --recording-duration 5
```

---

**Aktuelle Version:** v2.1.0 (Stable) ✅  
**Entwicklungszustand:** Produktionsreif, getestet auf RPi5 + Trixie  
**Nächste Major-Version:** v2.2.0 (Web-Dashboard, WebRTC-Stream)
