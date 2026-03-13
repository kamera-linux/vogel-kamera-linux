# 📋 CHANGELOG - Vogel-Kamera-Linux

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
