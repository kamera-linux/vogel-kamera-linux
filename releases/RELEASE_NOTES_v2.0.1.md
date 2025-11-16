# 🐦 Vogel-Kamera-Linux v2.0.1 - Stability & CLI Enhancements

**Release Date:** 16. November 2025  
**Type:** Patch Release  
**Status:** ✅ Stable

---

## 📋 Overview

v2.0.1 ist ein Stability- und Enhancement-Release, das kritische Bugfixes für die SSH-Verbindungsstabilität, vollständige CLI-Parameter-Unterstützung und neue Aufnahme-Modi (Cinema 4K, AI-HAD) bringt.

---

## ✨ New Features

### 🎬 Cinema 4K Mode
- **Cinema 4K Unterstützung:** 4096x2160 @ 25fps (DCI 4K statt UHD)
- Professionelle Framerate für filmische Aufnahmen
- Start: `./start-unified-monitoring.sh 4k`

### 🎤 AI-HAD Mode
- **Audio-Erkennung Integration:** Kombination aus Video + Audio Detection
- Konfigurierbar über `--audio-threshold` Parameter
- Start: `./start-unified-monitoring.sh ai-had`

### ⚙️ Complete CLI Parameter Support
- **Help-Funktion:** `--help` oder `-h` für alle Parameter
- **Threshold Configuration:** `--threshold VALUE` (Standard: 0.5)
- **Cooldown Configuration:** `--cooldown SECONDS` (Standard: 15)
- **Trigger Duration:** `--trigger SECONDS` (Standard: 1.0)
- **Audio Threshold:** `--audio-threshold VALUE` (Standard: 0.3)

**Beispiele:**
```bash
# Zeitlupe mit höherem Threshold
./start-unified-monitoring.sh slowmo --threshold 0.7 --cooldown 5

# Cinema 4K mit angepassten Parametern
./start-unified-monitoring.sh 4k --threshold 0.6 --trigger 0.3

# AI-HAD mit Audio-Erkennung
./start-unified-monitoring.sh ai-had --audio-threshold 0.25
```

### 📹 Auto Video Sync
- **Immediate Sync:** Videos werden sofort nach Konvertierung übertragen
- **Event-Driven:** Trigger bei "Konvertierung abgeschlossen" Log-Message
- Keine Polling-Verzögerung mehr (vorher: 15s Intervall)

---

## 🐛 Critical Bug Fixes

### SSH Connection Stability
**Problem:** Client-Skript terminierte nach Video-Transfer durch `pipefail` in Process Substitution

**Fixes:**
- `set -o pipefail` temporär deaktiviert für SSH tail-Befehle
- Automatische Wiederverbindung nach SSH-Fehlern (10 Versuche à 3s)
- Graceful Degradation mit User-Warnings
- Timeout reduziert: 21s → 2s für Monitoring-Calls

**Commits:**
- `b012eb4` - Prevent follow_event_log from hanging on SSH failures
- `30fb966` - Auto-reconnect SSH after connection loss
- `a6210c1` - Disable pipefail for SSH tail command

### Calendar Week Calculation
**Problem:** Falsche Kalenderwochen-Berechnung (KW 45 statt KW 46)

**Fix:**
- `strftime("%W")` → `strftime("%V")` (ISO 8601 Calendar Week)
- Videos landen nun in korrekter Wochenstruktur

**Commit:** `ce107b9`

### Video Path Extraction
**Problem:** Videos in falscher Verzeichnisstruktur (2025/2025/ statt 2025/46/)

**Fix:**
- `grep -oP` → `awk`-basierte Pfad-Extraktion
- Vermeidet mehrfache Matches in Dateinamen

**Commit:** `86e89ac`

### Video Sync Timing
**Problem:** Videos nicht automatisch übertragen, watch_for_videos unreliable

**Fix:**
- Event-driven sync statt Polling
- Trigger auf "Konvertierung abgeschlossen" Log-Message
- Sofortige Übertragung nach Conversion

**Commit:** `2a64e60`

---

## 🔧 Improvements

### Enhanced Error Handling
- SSH-Fehler-Tracking mit Failure-Counter
- Warning nach 5 konsekutiven Fehlversuchen
- 30s Cooldown bei persistenten Verbindungsproblemen
- Keine unerwarteten Skript-Terminierungen mehr

### Mode Support in remote-unified-control.sh
- Alle 4 Modi unterstützt: `normal`, `slowmo`, `4k`, `ai-had`
- `--restart [MODE]` akzeptiert optionalen Modus-Parameter
- Hilfe-Text mit vollständiger Modus-Dokumentation

### Contact Email Update
- Alte Adressen ersetzt: `kamerawagen.linux@gmail.com`, `vogel-kamera.linux@gmail.com`
- Neue Adresse: `kamera-linux@mailbox.org`
- Betrifft: SECURITY.md, CONTRIBUTING.md

---

## 📊 Technical Details

### Commits Since v2.0.0
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

### Feature Flags (New in v2.0.1)
```python
"cli_parameters": True      # Full CLI parameter support
"cinema_4k": True           # Cinema 4K (4096x2160 @ 25fps)
"ai_had_mode": True         # AI-HAD with audio detection
"auto_video_sync": True     # Immediate video sync
"ssh_resilience": True      # Enhanced SSH error handling
```

---

## 🚀 Upgrade Instructions

### From v2.0.0 → v2.0.1

**No breaking changes!** v2.0.1 ist vollständig rückwärtskompatibel.

**Empfohlene Schritte:**

1. **Stoppe laufende Instanzen:**
   ```bash
   cd auto-start-kamera
   ./remote-unified-control.sh --stop
   ```

2. **Pull Updates:**
   ```bash
   git pull origin main
   ```

3. **Deploy zu Raspberry Pi:**
   ```bash
   scp -i ~/.ssh/id_rsa_ai-had \
       auto-start-kamera/*.sh \
       roimme@raspberrypi-5-ai-had:~/vogel-kamera-linux/auto-start-kamera/
   ```

4. **Restart mit neuem Modus (optional):**
   ```bash
   # Zeitlupe (wie bisher)
   ./start-unified-monitoring.sh slowmo
   
   # ODER: Cinema 4K ausprobieren
   ./start-unified-monitoring.sh 4k
   
   # ODER: AI-HAD mit Audio
   ./start-unified-monitoring.sh ai-had
   ```

**Keine Config-Änderungen erforderlich!**

---

## 📝 Known Issues

### Minor Issues
- **Audio-Detection (AI-HAD):** Noch nicht vollständig implementiert (Stub vorhanden)
- **4K Performance:** Sehr hohe CPU-Last auf Pi 5, evtl. Thermal Throttling

### Workarounds
- **AI-HAD:** Aktuell nur Video-Detection aktiv (Audio folgt in v2.1.0)
- **4K Throttling:** `--cooldown 30` für längere Pausen zwischen Aufnahmen

---

## 🔗 Links

- **Full Changelog:** [docs/CHANGELOG.md](../docs/CHANGELOG.md)
- **Wiki:** [https://github.com/kamera-linux/vogel-kamera-linux/wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki)
- **Issues:** [https://github.com/kamera-linux/vogel-kamera-linux/issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)

---

## 👥 Contributors

- **kamera-linux Team** - Development, Testing, Documentation
- **Community Testers** - Bug Reports, Feature Requests

---

## 📞 Support

**Fragen oder Probleme?**
- 📧 Email: kamera-linux@mailbox.org
- 🐛 Bug Reports: [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)

---

**Danke für die Nutzung von Vogel-Kamera-Linux!** 🐦🎥

*Built with ❤️ on Raspberry Pi 5*
