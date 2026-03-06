# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt befolgt [Semantic Versioning](https://semver.org/lang/de/).

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

## [Unreleased]
### Geplant
- GUI-Interface für einfachere Bedienung
- Automatische Backup-Funktionalität
- Erweiterte KI-Modelle (YOLOv9/v10)
- Web-Dashboard für Remote-Monitoring
- Hailo AI HAT Support für Trixie (wartet auf DKMS)

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

## Versionierungsschema

- **Major Version (X.0.0):** Breaking Changes, API-Änderungen
- **Minor Version (0.X.0):** Neue Features, rückwärtskompatibel  
- **Patch Version (0.0.X):** Bugfixes, kleine Verbesserungen

## Entwicklungsrichtlinien

### Für Mitwirkende
1. Fork des Repositories erstellen
2. Feature-Branch von `devel` erstellen
3. Änderungen implementieren und testen
4. CHANGELOG.md entsprechend aktualisieren
5. Pull Request gegen `devel` erstellen

### Release-Prozess
1. Version in `__version__.py` aktualisieren
2. CHANGELOG.md mit finalen Änderungen aktualisieren
3. Git-Tag erstellen: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. Tag pushen: `git push origin v1.0.0`
5. Release auf GitHub erstellen

---

**Hinweis:** Vor Version 1.0.0 können breaking changes in Minor-Versionen auftreten.