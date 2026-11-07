# 📋 CHANGELOG - Vogel-Kamera-Linux

## [Unreleased]

### 🔧 Bug Fixes
- Erkennungsziel Hund, Katze oder „alle vier“ wurde nach einem Neustart auf „Vogel“ zurückgesetzt

## [2.4.1] - 7. November 2026 🔒 **Security-Audit**

### 🔒 Security-Audit ([Bericht](docs/SECURITY-AUDIT-2026-11.md))
- **Sync-Ziele:** Host/Benutzer/Pfad werden geprüft, `--` vor ssh/rsync-Zielen – vorher war
  mit Login Befehlsausführung als root über einen präparierten Benutzernamen möglich
- **Host-Key-Prüfung** bei Video-Übertragung (`accept-new` + `/etc/pi-daemon/known_hosts`)
  statt `StrictHostKeyChecking=no`
- **Neue Ansible-Rolle `hardening`** (bei `--install` und `--update`): `/etc/pi-daemon` nicht mehr
  für alle beschreibbar, TLS-Schlüssel nicht mehr für alle lesbar, SSH nur mit Schlüssel und ohne
  root-Login, veraltete Firewall-Regeln (8554, 5201) entfernt, Video-Verzeichnis nicht world-writable
- **Feste Paketversionen** in `requirements_daemon.txt` (Supply-Chain-Schutz)
- **Web-GUI:** Security-Header (CSP, `X-Frame-Options`, `nosniff`), vollständiges HTML-Escaping,
  Dateinamen nicht mehr in `onclick`-Code
- SSH-Keys werden direkt mit `0600` geschrieben; ungültige Zahlen führen nicht mehr zu HTTP 500
- 22 neue Sicherheitstests (`tests/test_security.py`)

### 📚 Dokumentation
- `docs/SECURITY.md` neu: aktuelle Versionen, Architektur, Schutzmaßnahmen, akzeptierte Risiken
- Screenshot der Powerbank-Anzeige in README und Release Notes v2.4.0

## [2.4.0] - 7. November 2026 🔋 **Powerbank-Überwachung**

### 🔋 Neu: Powerbank-Überwachung
- **Anker Prime Power Bank (27K, 250W) per Bluetooth:** Der pi-daemon liest alle 60 s
  Akkustand, Leistung je Port, Ladeleistung und Temperatur aus (Protokoll nach
  [atc1441](https://github.com/atc1441/Anker_Prime_BLE_hacking), kein Anker-Konto nötig).
  Neue Kartengruppe „Powerbank“ im Webinterface, Feld `powerbank` in `/api/status`.
- **Akku-Schutz:** Gotify-Warnung bei ≤ 10 %, bei ≤ 5 % (zwei Messungen, nicht am Laden)
  werden Detection/Aufnahme beendet und der Pi über systemd-logind heruntergefahren.
- Aktivierung über `PI_POWERBANK_MAC` in `ansible/.env`; Container bindet dafür
  `/run/dbus/system_bus_socket` ein. Neue Abhängigkeiten: `bleak`, `cryptography`.

### 🔧 Bug Fixes
- `--update` schrieb die Umgebungsvariablen nach `/opt/pi-daemon/.env`, der Container liest
  aber `/etc/pi-daemon/app.env` – neue Variablen kamen nur bei einer Erstinstallation an.
  `update.yml` aktualisiert jetzt `app.env`.

## [2.3.9] - 6. November 2026 🔒 **Sicherheit, Code-Struktur & CI**

### 🔒 Sicherheit
- **Login-Token nicht mehr in der URL:** `/api/download` und `/api/snapshot` akzeptieren das
  JWT nur noch im `Authorization`-Header (vorher auch `?token=`, das in Server-Logs und im
  Browser-Verlauf landen konnte). Die Web-GUI schickt den Header mit.
- Pfadprüfung bei Download/Löschen auf `Path.is_relative_to` umgestellt

### 🏗️ Code-Struktur
- **`pi_daemon_secure.py` aufgeteilt** (2400 Zeilen → Paket `unified-monitor-client/pi_daemon/`
  mit `config`, `runtime`, `settings`, `hailo`, `monitoring`, `sync`, `camera`, `api`, `main`).
  `pi_daemon_secure.py` bleibt als Startpunkt, Docker-Entrypoint unverändert.
- Dockerfile kopiert `pi_daemon/`; `--hotpatch` überträgt das Paket mit

### ✅ CI & Tests
- Neuer Workflow `ci.yml`: ruff, shellcheck und 28 pytest-Tests für den pi-daemon
  (Login/TOTP, Rate-Limit, JWT, Path Traversal, Einstellungen → Kamera)
- YouTube-Workflow: feste Paketversionen, kein täglicher Fallback-Branch mehr
- Actions auf `checkout@v7` / `setup-python@v7` (Node 24)

### 🔧 Bug Fixes
- `release_workflow.py`: GitHub-Release-Notes werden korrekt übernommen (`--notes-file`),
  Standardversion aus `VERSION`, Commit-Nachrichten sicher gequotet
- `git_automation.py`: Commit-Nachrichten sicher gequotet
- `test_full_automation.py` pusht keinen Test-Commit mehr (`git push --dry-run`)

### 📚 Dokumentation & Aufräumen
- CHANGELOG zusammengeführt (falsch datierte Alt-Einträge korrigiert, 1.3.2/2.3.6/2.3.7 ergänzt)
- git-automation-Doku zusammengeführt, Audio-Doku ins Archiv `releases/v2.3.4/`
- Versehentlich committete Dateien entfernt, ungenutzte Imports/Variablen bereinigt

Details: [releases/v2.3.9](releases/v2.3.9/RELEASE_NOTES_v2.3.9.md)

---

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

## [2.3.7] - 27. Juli 2026 🏥 **Health-Check Resilience & Proactive Monitoring**

### 🔧 Bug Fixes
- **Container fälschlich `unhealthy` bei Lastspitzen** (Incident 27.07.2026, ~1,5 h)
  - Docker-`HEALTHCHECK`: `--timeout` 5s → 10s, `--start-period` 20s → 30s
  - urllib-Timeout im Health-Check 4s → 12s

### ✨ Features
- **Proaktives Health-Monitoring per systemd-Timer** (alle 30 s)
  - `pi-daemon-health-check.service` / `.timer`, Logs via `journalctl -u pi-daemon-health-check.service`
  - Status-Wechsel (healthy ↔ unhealthy) werden geloggt
  - Wird bei `build_and_deploy.sh --deploy` / `--update` automatisch installiert

### 📦 Neue Dateien
- `scripts/container_health_monitor.py`, `scripts/docker_health_monitor.py`
- `ansible/playbooks/setup_pi_daemon_health_monitoring.yml`
- `ansible/playbooks/templates/pi-daemon-health-check.{service,timer}.j2`

Details: [releases/v2.3.7](releases/v2.3.7/RELEASE_NOTES_v2.3.7.md)

---

## [2.3.6] - 27. Juli 2026 🐧 **Ansible Toolchain Verbesserung**

### 🔧 Bug Fixes
- **Ansible-Tool-Lookup priorisiert lokale Venvs** – veraltete Installationen in
  `~/.local/bin/` überlagern die Playbooks nicht mehr. Reihenfolge:
  `ansible-venv-local/bin/` → `.venv/bin/` → `~/ansible-venv/bin/` → `PATH` → `~/.local/bin/`

Details: [releases/v2.3.6](releases/v2.3.6/RELEASE_NOTES_v2.3.6.md)

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

---

## [2.0.2] - 2026-03-06 🤖 YOLO26 & Monitoring Improvements

### ✨ Hinzugefügt
- **🤖 YOLO26 Migration:**
  - Wechsel von YOLOv8n auf YOLO26n für verbesserte Erkennungsgenauigkeit
  - Neues Modell: `yolo26n.pt` (5.3 MB, ~gleiche Größe wie YOLOv8n)
  - `ultralytics>=26.0.0` als Mindestanforderung
  - API vollständig kompatibel mit YOLOv8 (kein Code-Änderungsaufwand)

### 🐛 Behoben
- **CPU/RAM-Anzeige im Monitoring:**
  - `pgrep -f` lieferte Bash-Wrapper-PID statt Python-Prozess-PID
  - Fix: `ps aux | grep 'python3.*unified-camera-monitor' | grep -v 'bash|grep'`
  - Korrekte Werte: z.B. 151% CPU, 5.6% RAM statt 0.0%
  - Locale-Fix: `LC_ALL=C` für `ps`-Ausgaben (deutsches Komma-Format verhindert korrektes Parsen)
- **Kamera-Start-Konflikt:**
  - `rpicam-vid` blockierte Kamera-Init (`__init__ sequence did not complete`)
  - Ursache: `start-tcp-preview-watchdog.sh` respawnte `rpicam-vid` beim Start
  - Fix: Watchdog + rpicam-vid + libcamera werden vor Monitor-Start beendet

### 🔧 Verbessert
- **SSH-Stabilität im Monitoring-Skript:**
  - Timeout erhöht: 2s/3s → 5s/8s für zuverlässigere Pi-Kommunikation
  - Warnung erst nach 3 aufeinanderfolgenden Fehlversuchen (war: 1)
- **Status-Reporter aktiviert:**
  - Alle 5 Minuten CPU/RAM/Temperatur-Ausgabe im Terminal
  - War vorher nicht aktiv (Sleep 3600s ohne Ausgabe)
- **Submodule aktualisiert:**
  - `ai-training-tools/vogel-model-trainer` auf v0.1.28

### 🔗 Commits
```
912b0ae - feat: YOLO26 Migration und Monitoring-Verbesserungen
```

---

## [2.0.1] - 2025-11-16 🐛 Stability & CLI Enhancements

### ✨ Hinzugefügt
- **🎬 Cinema 4K Mode:**
  - Cinema 4K Unterstützung: 4096x2160 @ 25fps (DCI 4K statt UHD)
  - Professionelle Framerate für filmische Aufnahmen
  - Start: `./start-unified-monitoring.sh 4k`
  
- **🎤 AI-HAD Mode:**
  - Audio-Erkennung Integration (Kombination Video + Audio Detection)
  - Konfigurierbar über `--audio-threshold` Parameter
  - Start: `./start-unified-monitoring.sh ai-had`
  
- **⚙️ Complete CLI Parameter Support:**
  - Help-Funktion: `--help` oder `-h` für alle verfügbaren Parameter
  - `--threshold VALUE` - Erkennungs-Schwellenwert (Standard: 0.5)
  - `--cooldown SECONDS` - Cooldown zwischen Aufnahmen (Standard: 15)
  - `--trigger SECONDS` - Trigger-Dauer für Erkennung (Standard: 1.0)
  - `--audio-threshold VALUE` - Audio-Schwellenwert (Standard: 0.3)
  - Beispiel: `./start-unified-monitoring.sh slowmo --threshold 0.7 --cooldown 5`
  
- **📹 Auto Video Sync:**
  - Videos werden sofort nach Konvertierung übertragen (Event-driven)
  - Trigger bei "Konvertierung abgeschlossen" Log-Message
  - Keine Polling-Verzögerung mehr (vorher: 15s Intervall)

### 🐛 Behoben
- **SSH Connection Stability (CRITICAL):**
  - Client-Skript terminierte nach Video-Transfer durch `pipefail` in Process Substitution
  - `set -o pipefail` temporär deaktiviert für SSH tail-Befehle
  - Automatische Wiederverbindung nach SSH-Fehlern (10 Versuche à 3s)
  - Timeout reduziert: 21s → 2s für Monitoring-Calls
  - Graceful Degradation mit User-Warnings
  
- **Calendar Week Calculation:**
  - Falsche Kalenderwochen (KW 45 statt KW 46)
  - Fix: `strftime("%W")` → `strftime("%V")` (ISO 8601)
  - Videos landen nun in korrekter Wochenstruktur
  
- **Video Path Extraction:**
  - Videos in falscher Verzeichnisstruktur (2025/2025/ statt 2025/46/)
  - Fix: `grep -oP` → `awk`-basierte Pfad-Extraktion
  - Vermeidet mehrfache Matches in Dateinamen
  
- **Video Sync Timing:**
  - Videos nicht automatisch übertragen, watch_for_videos unreliable
  - Fix: Event-driven sync statt Polling
  - Sofortige Übertragung nach Conversion

### 🔧 Verbessert
- **Enhanced Error Handling:**
  - SSH-Fehler-Tracking mit Failure-Counter
  - Warning nach 5 konsekutiven Fehlversuchen
  - 30s Cooldown bei persistenten Verbindungsproblemen
  - Keine unerwarteten Skript-Terminierungen mehr
  
- **Mode Support:**
  - `remote-unified-control.sh` unterstützt alle 4 Modi: `normal`, `slowmo`, `4k`, `ai-had`
  - `--restart [MODE]` akzeptiert optionalen Modus-Parameter
  - Hilfe-Text mit vollständiger Modus-Dokumentation

### 📧 Geändert
- **Contact Email Update:**
  - Alte Adressen ersetzt: `kamerawagen.linux@gmail.com`, `vogel-kamera.linux@gmail.com`
  - Neue Adresse: `kamera-linux@mailbox.org`
  - Betrifft: SECURITY.md, CONTRIBUTING.md

### 🔗 Commits
```
f793e96 - feat: Change 4K mode to Cinema 4K (4096x2160 @ 25fps)
5d3f5bb - feat: Add proper CLI parameters and support for 4k and ai-had modes
a6210c1 - fix: Disable pipefail for SSH tail command to prevent script termination
30fb966 - fix: Auto-reconnect SSH after connection loss during monitoring
b012eb4 - fix: Prevent follow_event_log from hanging on SSH failures
86e89ac - fix: Correct year/week extraction in sync_video()
ce107b9 - fix: Use ISO week number (%V) instead of %W
2a64e60 - feat: Auto-sync videos immediately after conversion
17655ed - feat: Show conversion progress in live monitor
321cf35 - fix: Remove duplicate logs, fix video sync timing, improve SSH stability
403b624 - fix: Remove duplicate video conversion and fix progress bar
```

---

## [2.0.0] - 2025-11-11 🚀 MAJOR RELEASE

### ⚠️ BREAKING CHANGES
- **Unified Camera Monitor System:**
  - Alte Remote-Control-Skripte (`ai-had-*.py`) sind jetzt DEPRECATED
  - Neue Hauptmethode: `unified-camera-monitor.py` läuft direkt auf Raspberry Pi
  - SSH-Overhead eliminiert durch Single-Process-Architektur
  - Legacy-Skripte nach `legacy/` verschoben mit vollständigem Migration Guide
- **Neue Standard-Aufnahmedauer:**
  - Recordings jetzt standardmäßig 60 Sekunden (war variabel)
  - Konfigurierbar via `--recording-duration` Parameter
- **Neues CLI-Interface:**
  - CLI-Parameter ersetzen `.env`-Dateien für On-Pi Betrieb
  - 13 konfigurierbare Parameter (camera, threshold, cooldown, recording-*, etc.)

### ✨ Hinzugefügt
- **🎯 Unified Camera Monitor System (v2.0):**
  - Single-Process Kamera-System ohne SSH-Latenz
  - Läuft direkt auf Raspberry Pi für maximale Performance
  - Kombiniert Preview, AI-Detection und Recording in einem Prozess
  - Wrapper-Script `start-unified-monitoring.sh` für Client-PC Komfort
  
- **🚦 Traffic Light Health Monitoring:**
  - Real-time System-Überwachung mit Ampel-Visualisierung
  - **CPU-Temperatur:** 🟢 <55°C | 🟡 55-65°C | 🔴 >65°C | ⛔ STOP >75°C
  - **CPU-Load:** 🟢 <1.0 | 🟡 1.0-2.0 | 🔴 >2.0
  - **RAM-Nutzung:** 🟢 <75% | 🟡 75-90% | 🔴 >90%
  - **Disk-Space:** 🟢 <90% | 🟡 90-95% | 🔴 >95%
  - Live-Status alle 5 Minuten im Log
  
- **🔒 Auto-Shutdown System:**
  - Emergency-Stop bei kritischer CPU-Temperatur >75°C
  - Warnung bei kritischer CPU-Load oder Disk-Space
  - Hardware-Schutz für Raspberry Pi 5
  
- **⏱️ Konfigurierbare Aufnahmedauer:**
  - 60 Sekunden Standard, anpassbar via `--recording-duration`
  - Optimiert für Vogelbeobachtung (vollständige Szenen)
  - Kombiniert mit Cooldown für intelligente Trigger-Steuerung
  
- **📊 Live-Monitoring-Output:**
  - Heartbeat alle 30 Sekunden: `[✓] Monitor aktiv - XXX Frames verarbeitet`
  - Status-Report alle 5 Minuten mit allen Systemwerten
  - Echtzeit-Feedback mit `print()` + `logger` parallel
  
- **🌐 Multilingual Documentation:**
  - Vollständige README in 3 Sprachen: English, Deutsch, Japanisch
  - Neue Struktur: `docs/i18n/` mit README.md, README.de.md, README.ja.md
  - Language Selector in allen Dokumenten
  - Internationaler Zugang für globale Community
  
- **🔧 Automated Setup Script:**
  - `raspberry-pi-scripts/setup-unified-monitor.sh` für 1-Click-Installation
  - Automatische apt-Paket-Installation (PEP 668 konform)
  - YOLOv8 Installation via pip --break-system-packages
  - Verzeichnis-Setup und Permission-Management
  - OS-Erkennung und Trixie-Validierung

### 🔧 Geändert
- **Projekt-Reorganisation:**
  - Legacy-Scripts in `legacy/` mit umfassendem Migration Guide
  - `legacy/README.md` dokumentiert alle Änderungen und Migrationsschritte
  - Alte `.env`-basierte Konfiguration weiterhin in legacy/ verfügbar
  
- **README-Struktur aktualisiert:**
  - Language Selector prominent am Anfang
  - "Unified Camera Monitor System" als Hauptfeature
  - Legacy-Section mit Hinweis auf Deprecation
  - Vollständige Parameter-Tabelle (13 CLI-Parameter)
  - Traffic Light Thresholds dokumentiert
  - Installation-Section mit Setup-Script-Anleitung
  
- **Version-Management:**
  - scripts/version.py auf v2.0.0 mit neuen Feature-Flags
  - `unified_camera_monitor`, `traffic_light_monitoring`, `auto_shutdown`, `multilingual_docs`
  - Release-Name: "Unified Camera Monitor & Multilingual Documentation"
  - Release-Type: "major" wegen Breaking Changes

### 📦 Legacy-Archivierung
Folgende Skripte wurden nach `legacy/` verschoben:
- `ai-had-audio-remote-param-vogel-libcamera-single.py` → Audio-Only-Aufnahmen
- `ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py` → Video+AI Remote
- `ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py` → Slowmo Remote
- `config.py` → Config-System für Legacy-Scripts
- `.env.example` → Template für Legacy-Config

**Migration Path:**
1. Für neue Projekte: Verwenden Sie `unified-camera-monitor.py`
2. Für bestehende Setups: Legacy-Scripts funktionieren weiterhin aus `legacy/`
3. Migration Guide: `legacy/README.md` enthält vollständige Anleitung

### 🐛 Behoben
- **Emoji-Kompatibilität:**
  - Wechsel von 👁️ (Eye) zu [✓] (ASCII Checkmark) für Heartbeat
  - Funktioniert in allen Terminal-Emulationen
  
- **Deployment-Path-Bug:**
  - Korrektur: Deploy nach `~/vogel-kamera-linux/raspberry-pi-scripts/` statt `~/`
  - Verhindert "Script nicht gefunden"-Fehler beim Wrapper-Aufruf
  
- **Config-Pfad-Bug:**
  - Fix: `self.config.video_path` → `self.video_base_path` in unified-camera-monitor.py
  - AttributeError behoben

### 📚 Dokumentation
- **Neue Dokumentation erstellt:**
  - `docs/i18n/README.md` (English) - 350+ Zeilen
  - `docs/i18n/README.de.md` (German) - 794 Zeilen (vollständig)
  - `docs/i18n/README.ja.md` (Japanese) - 350+ Zeilen
  - `legacy/README.md` - Umfassender Migration Guide
  - `raspberry-pi-scripts/requirements-pi.txt` - Pi-spezifische Dependencies
  
- **README.md Hauptdatei:**
  - +176 Zeilen neue Dokumentation
  - Language Selector hinzugefügt
  - Unified Camera Monitor Section (vollständig)
  - Legacy Scripts Section mit Deprecation-Hinweis
  - Traffic Light Thresholds Tabelle
  - Installation mit Setup-Script dokumentiert

### 🎯 Migration für Benutzer
**Für neue Installationen:**
```bash
# Setup-Script ausführen
bash raspberry-pi-scripts/setup-unified-monitor.sh

# System starten
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo
```

**Für bestehende Installationen:**
```bash
# Option 1: Auf neues System migrieren (empfohlen)
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo

# Option 2: Alte Scripts weiter nutzen
python legacy/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 --width 1920 --height 1080 --ai-modul on
```

Siehe `legacy/README.md` für vollständigen Migration Guide.

### 🔖 Release-Informationen
- **Version:** 2.0.0 (Major Release - Breaking Changes)
- **Datum:** 11. November 2025
- **Branch:** feature/unified-camera-process → main
- **Commits:** 10+ Commits mit umfassenden Änderungen
- **Breaking Changes:** Ja - Legacy-Scripts deprecated
- **Migration Required:** Optional - Legacy weiter nutzbar

---

## [1.3.2] - 2025-11-10 🔍 Video-Analyse-Tool

### ✨ Hinzugefügt
- **Video-Analyse-Tool** `tools/analyze_video_bird_content.py` (YOLOv8)
  - Erkennt Vogel-Anteil und zusammenhängende Vogel-Segmente in aufgezeichneten Videos
  - Konfigurierbare Sample-Rate (jeder n-te Frame, Standard: 5)
  - JSON-Export, optionales Löschen von Videos ohne Vogelinhalt (`--delete`), Logging
- `tools/requirements.txt` und `tools/README.md`

### 🐛 Behoben
- Defekte Emojis in `tools/README.md`

> Das Tool wurde später als eigenständiges Paket ausgelagert:
> [vogel-video-analyzer](python-toolbox/vogel-video-analyzer) (Git-Submodul).

Details: [releases/v1.3.2](releases/v1.3.2/RELEASE_NOTES_v1.3.2.md)

---

## [1.3.1] - 2025-11-05

### ✨ Hinzugefügt
- **Live-Progressbar während Aufnahmen:**
  - Custom Single-Line Progressbar für alle Aufnahmemodi
  - Echtzeit-Updates mit visueller Darstellung: `[████████████░░░░░░] 67% (40/60s, noch 20s)`
  - Funktioniert für Zeitlupe, 4K-Video und Audio-Aufnahmen
- **Detaillierte Trigger-Informationen:**
  - Frame-Count und Konsistenz-Rate in Trigger-Meldungen
  - Beispiel: `✅ TRIGGER! Vogel konsistent erkannt (1.9s, 100% Rate, 5/5 Frames)`
  - Hilft bei Debugging und Parameter-Optimierung

### 🔧 Geändert
- **Optimierte Trigger-Parameter für WLAN-Betrieb:**
  - Trigger-Duration: 0.8s → 1.5s (mehr Frames für bessere Statistik)
  - Konsistenz-Rate: 65% → 60% (WLAN-optimiert)
  - Threshold: 0.5 → 0.4 (ausgewogen zwischen Sensitivität und False Positives)
  - FPS: 5 → 8 (Preview-Stream für optimale Performance)
- **Python Unbuffered Mode:**
  - `python -u` Flag in run-auto-trigger.sh für Echtzeit-Debug-Output
  - Alle Debug-Meldungen erscheinen sofort statt gebuffert
- **SSH Output Handling:**
  - Wechsel von `stdout.readline()` zu `stdout.read()` für saubere Progressbar
  - Video-Aufnahme mit `show_output=False` Parameter (keine Remote-Ausgabe während Aufnahme)
- **Version Bumps:**
  - Release-Datum auf 2025-11-05 aktualisiert
  - Build-Number auf 20251105-1

### 🐛 Behoben
- **TCP Stream Watchdog Hardening:**
  - Fehlertolerante Loop mit `set +e` und `|| true`
  - Auto-Restart mit 5 Sekunden Cooldown zwischen Restarts
  - Automatisches Process-Cleanup für Zombie-Prozesse
  - Robuste Behandlung von "Connection reset by peer"
- **Cleanup-System verbessert:**
  - SIGTERM → SIGKILL Cascade mit 10s Timeout
  - PID-Tracking für saubere Prozessverwaltung
  - Remote-Cleanup stoppt Watchdog und rpicam-vid auf dem Pi
  - Keine "Getötet"-Meldungen durch `2>/dev/null` in wait-Kommandos
- **Progressbar-Darstellung:**
  - tqdm-Buffering-Problem durch Custom Progressbar gelöst
  - Verwendung von `\r`, `flush=True` und `stdout.read()` für Live-Updates
  - Remote-Output überschreibt nicht mehr die lokale Progressbar
- **Stream-Timing optimiert:**
  - Differenziertes Timing: 5s bei laufendem Watchdog, 20s bei Neustart
  - Watchdog-Status-Check vor Stream-Initialisierung
  - Längere Wartezeiten für WLAN-Stabilität

### 📊 Performance
- **Gemessene Werte:**
  - Real FPS: ~4 FPS (245ms Inferenz-Zeit statt angestrebter 8 FPS)
  - 1.5s × 4 FPS = ~6 Frames Analysezeitraum
  - 60% Konsistenz = ~4 positive Frames von 6 nötig
  - WLAN Quality: 56/70 (80%), Signal -54 dBm, 227 Packet Retries
- **Trigger-Algorithmus:**
  - Mehr Frames für bessere Statistik, weniger False Positives
  - Konsistenz-Berechnung berücksichtigt echte Frame-Rate

### 📝 Bekannte Einschränkungen
- **Frame-Rate:** Real ~4 FPS statt 8 FPS (AI-Inferenz-Zeit: 245ms)
- **WLAN-Stabilität:** Gelegentliche "Connection refused" bei schlechter Verbindung
- **Progressbar:** Funktioniert nur mit direktem stdout (nicht über SSH-Redirect)
- **Trigger-Konsistenz:** Nur 3-6 Frames bei 1.5s Duration (wegen echter 4 FPS)

### 🔄 Migration
- ✅ Keine Breaking Changes - v1.3.0 Konfigurationen bleiben kompatibel
- ✅ Parameter automatisch angepasst - Neue Trigger-Duration und Konsistenz aktiv
- ✅ Cleanup verbessert - Sauberes Beenden ohne manuelle Anpassung

---

## [1.3.0] - 2025-11-01

> ⚠️ **BREAKING CHANGES:** Diese Version ist **NUR** für Raspberry Pi OS Trixie (Debian 13).  
> 📘 **Für Bookworm:** Verwenden Sie [bookworm-legacy-Branch v1.2.x](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)

### 🔴 BREAKING CHANGES
- **FFmpeg 7.1.2:** TCP-Streaming mit `tcp://...?listen=1` nicht mehr unterstützt
  - Migration zu MediaMTX RTSP-Server erforderlich
  - Alte TCP-basierte Skripte funktionieren NICHT auf Trixie
- **Python PEP 668:** Externally-Managed Environment
  - `pip install` blockiert → `apt-get install python3-*` erforderlich
  - Betrifft: python3-scp, python3-paramiko, python3-opencv
- **libcamera Limitierung:** Nur 1 Kamera-Session gleichzeitig
  - On-Demand Streaming erforderlich für Dual-Kamera-Betrieb

### ✨ Hinzugefügt
- **MediaMTX RTSP-Server Integration:**
  - Native rpiCamera-Unterstützung für IMX708
  - On-Demand Modus für Kamera-Zugriff-Sharing
  - Systemd-Service Management
  - Konfiguration: 640x480 @ 5fps, 1Mbps Bitrate
- **Dual-Kamera-Strategie:**
  - Kamera 1 (i2c@80000): Preview/Trigger-Stream
  - Kamera 0 (i2c@88000): High-Quality Aufnahmen
  - Automatisches Umschalten via On-Demand
- **Stream-Processor Optimierungen:**
  - GStreamer-Backend deaktiviert (blockiert RTSP)
  - FFMPEG-Timeouts erhöht: 30s (open), 60s (read)
  - Retry-Logik: Bis zu 10 Versuche für ersten Frame
  - Output-Buffering gelöst: print() + sys.stdout.flush()
  - H.264-Fehler-Unterdrückung via Environment
- **Trigger-Logik Verbesserungen:**
  - Duration reduziert: 2.0s → 1.0s (responsive für Bewegung)
  - Toleranz-Fenster: 0.5s Gap erlaubt ohne Timer-Reset
  - last_detection_time Tracking für präzise Gap-Messung
- **Trixie-Dokumentation:**
  - `docs/TRIXIE-MIGRATION.md` - Vollständiger Migration-Guide
  - README.md aktualisiert mit Trixie-Requirements
  - MediaMTX Setup-Anleitung
  - Branch-Strategie dokumentiert

### 🔧 Geändert
- **run-auto-trigger.sh:**
  - MediaMTX systemd-Check statt TCP-Port-Probe
  - `systemctl is-active mediamtx` Validierung
- **ai-had-kamera-auto-trigger.py:**
  - UI-Label korrigiert: "120fps, OHNE Audio" (Zeitlupe)
  - trigger_duration=1.0 (war 2.0)
- **start-vogel-beobachtung.sh:**
  - Help-Text Audio-Status korrigiert

### 🐛 Behoben
- **Stream-Processor sys-Import:** Fehlte, verursachte Crashes
- **GStreamer RTSP-Blockade:** Backend deaktiviert
- **Trigger-Timer zu strikt:** 0% Toleranz → 0.5s Fenster
- **Output-Buffering:** Logging verzögert → Sofortiger Print
- **python3-scp Installation:** pip blockiert → apt-get Lösung

### 📦 Abhängigkeiten (Raspberry Pi)
- MediaMTX v1.9.1+
- FFmpeg 7.1.2+
- rpicam-apps v1.9.1+
- Python 3.13.5+
- python3-scp (via apt)
- python3-paramiko (via apt)

### 🧪 Tests
- ✅ MediaMTX On-Demand Modus funktional
- ✅ RTSP-Stream stabil (rtsp://host:8554/cam)
- ✅ Auto-Trigger verbindet und erkennt Vögel
- ✅ Dual-Kamera-Betrieb (sequenziell)
- ✅ Manual-Trigger: 5 Videos erfolgreich
- ✅ Trigger-Logik: 1.0s Duration, 0.5s Toleranz

### ⚠️ Bekannte Probleme
- Hailo AI HAT nicht funktional (Trixie DKMS fehlt)
- H.264 stderr Warnungen (kosmetisch, funktioniert)
- Paralleler Kamera-Betrieb nicht möglich (libcamera Limit)

### 📚 Ressourcen
- [MediaMTX GitHub](https://github.com/bluenviron/mediamtx)
- [Raspberry Pi OS Trixie](https://www.raspberrypi.com/software/operating-systems/)
- [FFmpeg 7.x Release Notes](https://ffmpeg.org/download.html)

---

## [1.2.0] - 2025-10-03
### Hinzugefügt
- **🎬 Zeitlupen-Modus:** Neuer `--slowmo` Parameter für 120fps Slow-Motion Aufnahmen
  - Auflösung: 1536x864 @ 120fps für flüssige Zeitlupen
  - Integration mit `ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py`
  - Eigener Banner und Startup-Meldungen im Wrapper-Skript
  - Audio-Aufnahme mit 44.1kHz Mono parallel zur Zeitlupe
- **🚀 Git-Automation Branch-Support:** Vollständige Branch-Verwaltung (v1.2.0)
  - `--branch` Parameter für alle Operationen (--commit, --release, --push)
  - Automatischer Branch-Checkout bei Angabe von --branch
  - Workflow-Beispiele für Feature-Branches (devel-v1.2.0)
  - GIT_AUTOMATION_README.md mit Branch-Workflows erweitert
- **🏗️ Architektur-Dokumentation:** Umfassende ARCHITEKTUR.md mit Mermaid-Diagrammen
  - Detaillierte Kommunikationsflüsse (PC ↔ Raspberry Pi)
  - Sequenzdiagramme für Systemstart, Stream-Analyse, Aufnahme-Trigger
  - CPU-Optimierungs-Visualisierung (107% → 40%)
  - Video- und Audio-Pipeline-Diagramme
  - SSH-Kommunikation im Detail
  - Erkennungs-Workflow und Fehlerbehandlung
- **🎤 Audio-Dokumentation:** Klarstellung Audio-Aufnahme in allen Modi
  - Help-Text aktualisiert: Alle Modi zeigen "+ Audio"
  - Audio-Spezifikationen: 44.1kHz Mono WAV
  - Hinweis-Block für USB-Mikrofon-Anforderung
  - Startup-Banner zeigt Audio-Status konsistent

### Geändert
- **⚡ CPU-Optimierung:** Drastische Reduktion der Systemlast (107% → ~40%)
  - **Stage 1:** Thread-Limiting (OMP/BLAS/MKL_NUM_THREADS=2) → 82.5% CPU
  - **Stage 2:** FPS-Reduktion (5fps → 3fps) → 82.5% CPU
  - **Stage 3:** Preview-Auflösung (640x480 → 320x240) → 92% CPU
  - **Stage 4 (DURCHBRUCH!):** YOLO imgsz=320 Parameter → 39-43% CPU ✅
  - Automatische CPU-Optimierung in allen Modi via Environment-Variablen
- **🔧 Wrapper-Skript:** Erweiterte `start-vogel-beobachtung.sh` mit expliziten Parametern
  - Alle Modi: --preview-fps 3, --preview-width 320, --preview-height 240
  - Zeitlupe: --preview-fps 2 (noch schonender)
  - Überarbeite Help-Ausgabe mit Audio-Informationen
  - Modi-Beschreibungen: "Video + Audio" statt "nur Video"
- **🎯 Auto-Trigger Recording-Modi:** Konsistente Output-Texte
  - Standard: "📹 Ohne KI (Video + Audio)"
  - Mit KI: "🤖 Mit KI + Audio"
  - Zeitlupe: "🎬 Zeitlupe (120fps + Audio)"
  - Alle Modi zeigen explizit, dass Audio aufgenommen wird
- **📊 Git-Automation:** Version 1.1.4 → 1.2.0
  - Enhanced branch support für alle Git-Operationen
  - Beispiele mit Feature-Branch-Workflows

### Verbessert
- **🚀 Performance:** 63% CPU-Reduktion ermöglicht stabilen Dauerbetrieb
- **📖 Dokumentation:** Umfassende Architektur-Dokumentation mit Visualisierungen
- **🎛️ Benutzerfreundlichkeit:** Klarere Output-Texte, Audio-Status transparent
- **🔄 Git-Workflow:** Flexiblere Branch-Verwaltung für parallele Entwicklung

### Behoben
- **🐛 Inkonsistente Audio-Dokumentation:** Help-Text vs. Startup-Banner synchronisiert
- **⚙️ YOLO-Inferenz-Größe:** imgsz=320 Parameter fehlte, führte zu unnötiger CPU-Last
- **📝 Missverständliche Ausgaben:** "nur Video" → "Video + Audio" korrigiert

### Technische Details
**CPU-Optimierung Breakdown:**
```
Baseline:   107% CPU (vor Optimierung)
Stage 1:     82.5% CPU (Thread-Limits)
Stage 2:     82.5% CPU (FPS 3)
Stage 3:     92% CPU (Auflösung 320x240)
Stage 4:     40% CPU (imgsz=320) ← Schlüssel-Optimierung
Reduktion:   -63% (107% → 40%)
```

**Modi-Übersicht v1.2.0:**
| Modus | FPS | Auflösung | Audio | Parameter |
|-------|-----|-----------|-------|-----------|
| Standard | 25 | 1920x1080 | ✅ 44.1kHz | (default) |
| Mit KI | 25 | 1920x1080 | ✅ 44.1kHz | --with-ai |
| Zeitlupe | 120 | 1536x864 | ✅ 44.1kHz | --slowmo |

## [1.1.9] - 2025-09-30
### Hinzugefügt
- **📊 System-Monitoring:** Umfassende Überwachung für alle Kamera-Skripte
  - `get_remote_system_status()` - Echtzeit System-Status mit farbcodierten Indikatoren
  - `check_system_readiness()` - Kritische System-Validierung vor Aufnahmestart
  - CPU-Temperatur-Überwachung mit Warnstufen (>60°C Warnung, >70°C Kritisch)
  - Festplatten-Auslastung mit automatischen Warnungen (>80% Warnung, >90% Kritisch)
  - Arbeitsspeicher-Anzeige (verwendet/gesamt/verfügbar)
  - CPU-Load Average mit Performance-Auswirkungen
- **⚡ Performance-Optimierung:** Load-Balancing für verschiedene Aufnahmemodi
  - Standard AI-Modus: Load > 2.0 = Warnung, Load > 1.0 = Beobachtung
  - Zeitlupe-Modus: Load > 1.0 = Kritisch (strengere Anforderungen für 120fps)
  - Audio-Modus: Load-Monitoring für optimale Audioqualität
- **🔧 Monitoring-Tools:** Neue Tools im Verzeichnis für System-Überwachung
  - `remote_system_monitor.py` - Umfassendes System-Monitoring mit JSON-Export
  - `quick_system_check.py` - Schnelle System-Checks mit Watch-Modus
- **🚨 Benutzer-Interaktion:** Automatische Bestätigungsabfragen bei kritischen Systemwerten
- **🌡️ Erweiterte Features:** Spezialisierte Schwellenwerte für verschiedene Kamera-Modi

### Geändert
- **🔄 Alle Python-Skripte:** Integration von System-Monitoring in alle drei Hauptskripte
  - `ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py`
  - `ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py`
  - `ai-had-audio-remote-param-vogel-libcamera-single.py`
- **📊 Version Updates:** Konsistente v1.1.9 über alle Komponenten
  - `scripts/version.py` mit neuen Feature-Flags
  - `python-skripte/__version__.py` Fallback-Version aktualisiert
- **📚 Dokumentation:** Erweiterte README.md und AI-MODELLE-VOGELARTEN.md mit Monitoring-Features

### Verbessert
- **🎯 Aufnahmequalität:** Proaktive System-Checks verhindern Performance-Probleme
- **📈 Systemstabilität:** Frühzeitige Warnung bei kritischen Systemzuständen
- **🔍 Transparenz:** Vollständige Sichtbarkeit der System-Performance vor jeder Aufnahme

## [1.1.8] - 2025-09-29
### Hinzugefügt
- **🏗️ Vollständige Projekt-Reorganisation:** Professionelle Verzeichnisstruktur nach Open-Source-Standards
- **🤖 Erweiterte AI-Funktionen:** Flexible AI-Modell-Auswahl (YOLOv8, eigene Modelle)
- **📚 AI-Training-Toolkit:** Komplettes ai-training-tools/ Verzeichnis mit 4 professionellen Tools
- **📖 Umfassende Dokumentation:** 300+ Zeilen AI-Training-Anleitung für deutsche Gartenvögel
- **🔧 Neue Verzeichnisstruktur:** config/, docs/, scripts/, tools/ für bessere Organisation

### Geändert
- **🔄 Versionsverwaltung:** Konsistente v1.1.8 über alle Komponenten
- **📁 Dateien-Migration:** Alle Dateien in logische Verzeichnisse verschoben
- **🐛 UTF-8 Encoding:** Alle Python-Dateien mit korrekten Encoding-Headern

## [1.1.7] - 2025-09-28
### Hinzugefügt
- **🔧 3D-Konstruktion:** Neues `3d-konstruktion/` Verzeichnis mit versionierten CAD-Dateien
  - STP-Dateien für Vogelhaus mit Kamera-Integration
  - Komplette Konstruktionsdokumentation mit Druck-Parametern
  - Versionierte Struktur für zukünftige Konstruktions-Updates
- **📚 Wiki-Sidebar:** Benutzerdefinierte `_Sidebar.md` für verbesserte Navigation
  - Strukturierte 7-Kategorien Navigation im GitHub Wiki
  - Externe Links zu Repository, YouTube und Community
  - Automatische Anzeige auf allen Wiki-Seiten
- **📖 Erweiterte Dokumentation:** 
  - 3D-Druck Anleitungen mit Material-Empfehlungen
  - Technische Spezifikationen für PETG/ABS Outdoor-Einsatz
  - Wiki-Navigation für 25+ Dokumentationsseiten

### Verbessert
- **📂 Projektstruktur:** README.md mit 3D-Konstruktions-Integration erweitert
- **🔄 Versionsverwaltung:** Konsistente v1.1.8 über alle Komponenten
- **📱 Benutzerfreundlichkeit:** Intuitive Wiki-Navigation für Desktop und Mobile

## [1.1.6] - 2025-09-27
### Hinzugefügt
- **📚 Wiki-Sync-System:** Neues `wiki-sync/` Verzeichnis für Wiki-Synchronisation
- **🔧 Reorganisiertes Skript:** Überarbeitetes `wiki_sync.py` mit verbesserter Pfad-Behandlung
- **🐍 Virtual Environment Integration:** Standardisierte venv-Setup-Anweisungen in aller Dokumentation
- **📖 Erweiterte Dokumentation:** Umfassende README für Wiki-Synchronisations-Workflow
- **💻 Verbesserte CLI:** Enhanced Command-Line-Interface mit besserer Fehlerbehandlung

### Verbessert
- **Installation-Guide.md** - Umfassende venv-Setup-Anweisungen hinzugefügt
- **AI-Configuration.md** - Virtual Environment Workflow integriert  
- **FAQ.md** - Enhanced Troubleshooting mit venv-Überlegungen
- **Git-Automation.md** - Aktualisiert mit modernen Python-Umgebungs-Praktiken

## [1.1.5] - 2025-09-25
### Hinzugefügt
- **🎤 Veranstaltungsmanagement:** Neuer `veranstaltungen/` Ordner für Vorträge und Präsentationen
- **🐧 LinuxDay.at Integration:** Vollständige Vorbereitung für LinuxDay.at 2025 Vortrag
- **📱 QR-Code Generator:** Automatische Erstellung von QR-Codes für Veranstaltungslinks
- **📋 Präsentationsstruktur:** Organisierte Ordner für slides/ und resources/
- **📄 Veranstaltungsdokumentation:** README-Dateien mit eingebetteten QR-Codes
- **🗓️ Event-Tracking:** Strukturiertes System für vergangene und zukünftige Veranstaltungen

### Verbessert  
- **📂 Repository-Organisation:** Bessere Strukturierung für öffentliche Präsentationen
- **🔗 Externe Integration:** Direkte Links zu Veranstaltungswebsites
- **📖 Dokumentation:** Erweiterte Anleitungen für Vortragsvorbereitung

## [1.1.4] - 2025-09-24
### Hinzugefügt
- **🔐 Sichere Git-Automatisierung:** Vollständig automatisierte Git-Operationen
- **🗂️ Modulare Struktur:** Git-Automation in separaten `git-automation/` Ordner
- **🔑 SSH-Credential-Management:** AES-256-CBC verschlüsselte SSH-Passphrases
- **🚀 Automatischer SSH-Agent:** Keine manuelle Passphrase-Eingabe mehr
- **🛡️ Master-Password-Schutz:** PBKDF2 Key-Derivation mit 100.000 Iterationen
- **🧪 Umfassende Test-Suite:** Automatisierte Tests für SSH-Agent und Git-Integration
- **📚 Detaillierte Dokumentation:** Setup-Anleitungen und Sicherheitsrichtlinien

### Verbessert
- **🏗️ Repository-Organisation:** Bessere Trennung von Features und Tools
- **🔒 Sicherheitsstandards:** Eliminierung von Klartext-Credentials
- **⚡ Developer Experience:** Einmalige Einrichtung für dauerhaft automatisierte Workflows

### Sicherheit
- **❌ Entfernt:** Unsichere `.git_secrets.json` mit Klartext-Passphrases
- **✅ Hinzugefügt:** AES-verschlüsselte Credential-Speicherung
- **🛡️ Verbessert:** `.gitignore` für neue Git-Automation Struktur

## [1.1.3] - 2025-09-24
### Hinzugefügt
- **💬 GitHub Discussions Integration:** Community-Diskussionsbereich aktiviert
- **🤝 Community & Diskussionen Sektion:** Neue README-Sektion für Nutzer-Interaktion
- **📋 Erweiterte Support-Optionen:** Discussions für Fragen, Issues für Bugs
- **🎯 Strukturierte Community-Bereiche:** Q&A, Ideen, Hardware-Tipps, Aufnahmen teilen

### Verbessert
- **📞 Support-Bereich:** Klare Trennung zwischen Discussions und Issues
- **🔗 Navigation:** Direkte Links zu Community-Features
- **🏷️ Badge-System:** GitHub Discussions Badge hinzugefügt
- **📖 Dokumentation:** Deutsche Übersetzung der Discussions-Willkommensnachricht

### Technisch
- README.md erweitert um Community & Diskussionen Sektion
- Support-Bereich reorganisiert für bessere Nutzerführung
- Version auf v1.1.3 aktualisiert in allen relevanten Dateien

## [1.1.2] - 2025-09-23
### Hinzugefügt
- **🔧 GitHub Issue Templates:** Deutsche Bug Report und Feature Request Templates
- **📋 Repository-spezifische Anpassungen:** Hardware-spezifische Abschnitte für Pi/Kamera
- **🤝 Community-Engagement:** Strukturierte Nutzen-Bewertung und Akzeptanzkriterien
- **📁 .gitignore Update:** Wiki-Content Verzeichnis ausgeschlossen für besseres Repository-Management

### Verbessert
- **📝 Issue Template Struktur:** Emoji-Icons und bessere Kategorisierung
- **🎯 Feature Request Process:** Priorisierung und Implementierungs-Bereitschaft
- **🐛 Bug Report Qualität:** Detaillierte System-Informationen und Reproduktionsschritte
- **🌍 Lokalisierung:** Vollständige deutsche Übersetzung aller Templates

### Technisch
- Neue .github/ISSUE_TEMPLATE/ Struktur implementiert
- Repository-spezifische Anpassungen für Vogel-Kamera-Linux
- Automatische Label-Zuweisung für Issues
- Verbesserte Community-Beitrag-Workflows

## [1.1.1] - 2025-09-23
### Behoben
- **🔧 Kritischer Bugfix:** .env-Datei wird jetzt korrekt geladen
- **📦 Dependencies:** Fehlende python-dotenv Abhängigkeit hinzugefügt
- **🛠️ Konfigurationssystem:** Vollständig funktionsfähig gemacht
- **✅ Skript-Funktionalität:** Alle Skripte getestet und lauffähig

### Hinzugefügt
- **📦 requirements.txt** für einfache Dependency-Installation
- **🔧 Verbesserte Installationsanweisungen** in README.md
- **✅ Konfigurationsvalidierung** funktioniert korrekt

### Technisch
- python-dotenv>=1.0.0 als neue Abhängigkeit
- Automatisches Laden der .env-Datei beim Import
- Verbesserte Fehlerbehandlung im Konfigurationssystem

## [1.1.0] - 2025-09-23
### Hinzugefügt
- **🎬 YouTube-Integration:**
  - YouTube-Kanal Sektion in README.md
  - QR-Code für mobilen Zugriff auf Videos
  - Video-Tutorial Verweise in der Dokumentation
  - Automatischer QR-Code Generator (`generate_qr_codes.py`)

- **📱 QR-Code System:**
  - Hauptkanal QR-Code (`qr-youtube-channel.png`)
  - Playlists QR-Code (`qr-playlists.png`) 
  - Abonnieren QR-Code (`qr-subscribe.png`)
  - QR-Code Anleitung (`QR-CODE-ANLEITUNG.md`)

- **🔧 Konfigurationsverbesserungen:**
  - Zentrales Konfigurationssystem implementiert
  - Sichere `.env`-basierte Konfiguration
  - Automatische Konfigurationsvalidierung
  - Entfernung aller hardcodierten persönlichen Daten

- **📚 Dokumentation:**
  - Erweiterte README.md mit YouTube-Integration
  - Vollständige Projektstruktur dokumentiert
  - Video-Tutorial Verweise hinzugefügt
  - Konfigurationsanleitung verbessert

### Geändert
- Alle Python-Skripte verwenden jetzt das zentrale Konfigurationssystem
- SSH-Verbindungsdetails über Umgebungsvariablen konfigurierbar
- Pfade für Video/Audio-Speicherung konfigurierbar
- .gitignore erweitert um `.venv/` und weitere Python-Dateien

### Sicherheit
- **🔒 Sichere Veröffentlichung:** Alle persönlichen Daten entfernt
- Konfiguration über `.env`-Dateien (nicht im Repository)
- SSH-Schlüssel-Pfade konfigurierbar
- Validierung warnt vor fehlender Konfiguration

## [1.0.0] - 2025-09-23
### Hinzugefügt
- **Hauptfunktionalitäten:**
  - 🎥 Hochauflösende Videoaufnahme (bis 4K) mit Raspberry Pi 5
  - 🎵 Synchrone Audioaufnahme über USB-Mikrofon
  - 🤖 KI-Objekterkennung mit YOLOv8 für Vogelerkennung
  - 🌐 SSH-basierte Remote-Steuerung
  - 📁 Automatische Dateiorganisation nach Jahr/Kalenderwoche

- **Drei spezialisierte Skripte:**
  - `ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py` - Haupt-Aufnahmeskript mit KI
  - `ai-had-audio-remote-param-vogel-libcamera-single.py` - Spezialisierte Audio-Aufnahme
  - `ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py` - Zeitlupe-Aufnahmen (120fps+)

- **Konfigurationssystem:**
  - Zentrales `config.py` für alle Einstellungen
  - `.env.example` Vorlage für sichere Konfiguration
  - Automatische Konfigurationsvalidierung
  - Umgebungsvariablen-Support

- **Sicherheit & Best Practices:**
  - Keine hardcodierten persönlichen Daten
  - MIT-Lizenz mit Haftungsausschluss
  - Vollständige `.gitignore` für sensible Dateien
  - SSH-Schlüssel-Authentifizierung

- **Benutzerfreundlichkeit:**
  - Kommandozeilen-Interface mit umfassenden Parametern
  - Fortschrittsanzeige während Aufnahme (tqdm)
  - Versionsinformationen (`--version`)
  - Umfassende Fehlerbehandlung
  - Signal-Handler für sauberes Beenden (Ctrl+C)

- **Technische Features:**
  - Multi-Threading für parallele Video/Audio-Verarbeitung
  - Automatische FFmpeg-Konvertierung zu MP4
  - USB-Audio-Gerät Auto-Erkennung
  - Flexible Auflösungs- und Codec-Unterstützung
  - ROI (Region of Interest) Support
  - HDR-Modi und erweiterte Kamera-Einstellungen

### Dokumentation
- Vollständige README.md mit Setup-Anweisungen
- Parameter-Übersichtstabelle
- Troubleshooting-Sektion
- SSH-Konfigurationsanleitung
- Projektstruktur-Dokumentation

### Technische Spezifikationen
- **Python:** >= 3.8
- **Betriebssystem:** Linux, Raspberry Pi OS
- **Hardware:** Raspberry Pi 5 + Kamera-Modul + USB-Mikrofon
- **Abhängigkeiten:** paramiko, scp, tqdm, ffmpeg
- **Kamera-Software:** libcamera/rpicam-vid

### Dateiorganisation
```
~/Videos/Vogelhaus/
├── AI-HAD/        # KI-gestützte Aufnahmen
├── Audio/         # Reine Audio-Aufnahmen  
└── Zeitlupe/      # Slow-Motion Videos
    └── YYYY/MM/Wochentag__YYYY-MM-DD__HH-MM-SS/
```

---

**Aktuelle Version:** siehe [`VERSION`](VERSION) · Installation & Update: [README.md](README.md) · Release-Notes je Version: [`releases/`](releases/)

Versionierung nach [Semantic Versioning](https://semver.org/lang/de/): Major = Breaking Changes, Minor = neue Features, Patch = Bugfixes.
