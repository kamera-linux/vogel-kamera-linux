# 🚀 Release Notes v1.3.0-dev (Trixie Development)

**Release-Datum:** In Entwicklung  
**Branch:** feat/trixie-support  
**Target:** Raspberry Pi OS Trixie (Debian 13)

> ⚠️ **BREAKING CHANGES - Trixie Only!**  
> Diese Version ist **NICHT** kompatibel mit Raspberry Pi OS Bookworm (Debian 12).  
> Für Bookworm verwenden Sie bitte [v1.2.x vom main-Branch](https://github.com/kamera-linux/vogel-kamera-linux/tree/main).

---

## 📋 Zusammenfassung

Version 1.3.0-dev bringt **vollständige Unterstützung für Raspberry Pi OS Trixie (Debian 13)** mit grundlegenden Architektur-Änderungen:

- **MediaMTX RTSP-Server** ersetzt TCP-Streaming (FFmpeg 7.1.2 Breaking Change)
- **On-Demand Stream-Modus** für Dual-Kamera-Betrieb
- **Optimierte Trigger-Logik** (1.0s Duration, 0.5s Toleranz)
- **Verbesserte Stream-Stabilität** mit erweiterten Timeouts und Retry-Logik
- **Umfassende Trixie-Dokumentation**

---

## 🔴 BREAKING CHANGES

### 1. FFmpeg 7.1.2 - TCP-Streaming entfernt

**Problem:**
```bash
# Funktioniert NICHT mehr auf Trixie:
rpicam-vid -o tcp://0.0.0.0:8888?listen=1
```

**Fehlermeldung:**
```
tcp://0.0.0.0:8888?listen=1: Invalid argument
```

**Lösung:**
```bash
# MediaMTX RTSP-Server verwenden:
rtsp://192.168.178.59:8554/cam
```

**Migration:** Alle TCP-basierten Skripte wurden auf RTSP migriert.

---

### 2. Python PEP 668 - Externally-Managed Environment

**Problem:**
```bash
pip3 install scp
# error: externally-managed-environment
```

**Lösung:**
```bash
# Stattdessen apt verwenden:
sudo apt-get install python3-scp python3-paramiko
```

**Betroffen:** Alle Python-Pakete auf Raspberry Pi müssen via `apt-get` installiert werden.

---

### 3. libcamera Limitierung - Nur 1 Session

**Problem:**
- Raspberry Pi 5 kann nur **eine** libcamera-Session gleichzeitig ausführen
- Paralleler Betrieb: Preview + Aufnahme = Exit Code 139

**Lösung:**
```yaml
# MediaMTX On-Demand Modus:
sourceOnDemand: yes  # Stream stoppt automatisch ohne Client
```

**Resultat:** Kamera wird freigegeben für Aufnahmen wenn kein Stream-Client verbunden.

---

## ✨ Neue Features

### MediaMTX RTSP-Server Integration

**Installation:**
```bash
wget https://github.com/bluenviron/mediamtx/releases/download/v1.9.1/mediamtx_v1.9.1_linux_arm64v8.tar.gz
sudo mv mediamtx /usr/local/bin/
sudo systemctl enable mediamtx
```

**Konfiguration:**
```yaml
paths:
  cam:
    source: rpiCamera
    sourceOnDemand: yes
    rpiCameraWidth: 640
    rpiCameraHeight: 480
    rpiCameraFPS: 5
    rpiCameraCamID: 1  # Preview-Kamera
```

**Vorteile:**
- ✅ Native Raspberry Pi Camera-Unterstützung
- ✅ Automatisches On-Demand Streaming
- ✅ Systemd-Integration
- ✅ Niedriger CPU-Overhead

---

### Dual-Kamera-Strategie

**Konzept:**
- **Kamera 1** (i2c@80000): MediaMTX Preview/Trigger
- **Kamera 0** (i2c@88000): High-Quality Aufnahmen

**Workflow:**
1. Auto-Trigger verbindet → MediaMTX startet Kamera 1
2. Vogel erkannt → Trigger aktiviert
3. Kein Client mehr → MediaMTX stoppt Kamera 1
4. Aufnahme-Script startet Kamera 0

**Resultat:** Keine Konflikte durch On-Demand Modus!

---

### Optimierte Trigger-Logik

**Alte Version (v1.2.x):**
```python
trigger_duration = 2.0  # 10 Frames @ 5fps
tolerance = 0.0  # Keine Lücken erlaubt
```

**Problem:** Timer resettet bei jeder Frame-Lücke → Trigger nie erreicht bei beweglichen Vögeln

**Neue Version (v1.3.0-dev):**
```python
trigger_duration = 1.0  # 5 Frames @ 5fps (responsive!)
tolerance = 0.5  # 2-3 Frames dürfen fehlen
```

**Resultat:**
- ✅ Trigger funktioniert bei beweglichen Vögeln
- ✅ Schnellere Reaktionszeit (1.0s statt 2.0s)
- ✅ Robuster gegen Frame-Drops

---

### Stream-Processor Verbesserungen

**sys-Import hinzugefügt:**
```python
import sys  # Kritischer Fix!
```

**GStreamer-Backend deaktiviert:**
```python
# GStreamer blockiert bei RTSP
backends = [
    (cv2.CAP_FFMPEG, self.stream_url),  # Nur FFMPEG
]
```

**Erweiterte Timeouts:**
```python
self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 30000)  # 30s
self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 60000)  # 60s
```

**Retry-Logik:**
```python
for attempt in range(10):  # Bis zu 10 Versuche
    ret, frame = self.cap.read()
    if ret and frame is not None:
        break
    time.sleep(1)
```

**Output-Buffering gelöst:**
```python
print("✅ Stream-Verbindung erfolgreich")
sys.stdout.flush()  # Sofortiger Output!
```

---

## 🔧 Geänderte Dateien

### kamera-auto-trigger/scripts/stream_processor.py
- **+** `import sys` (Line 33)
- **+** H.264-Fehler-Unterdrückung via Environment
- **~** GStreamer-Backend deaktiviert (Lines 210-212)
- **~** FFMPEG-Timeouts erhöht (Lines 222-225)
- **+** Retry-Logik für ersten Frame (Lines 228-242)
- **~** `logger.info()` → `print() + flush()` (Lines 233-241)
- **+** `last_detection_time` Tracking (Line 113)
- **~** `trigger_duration = 1.0` (Line 739)
- **+** 0.5s Toleranz-Fenster (Lines 472-481)

### kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py
- **~** UI-Label: "120fps, OHNE Audio" (Line 177)
- **~** `trigger_duration=1.0` (Line 739)

### kamera-auto-trigger/run-auto-trigger.sh
- **~** MediaMTX systemd-Check statt TCP-Port (Lines 24-36)

### kamera-auto-trigger/start-vogel-beobachtung.sh
- **~** Help-Text Audio-Status korrigiert (Line 54)

---

## 📦 Abhängigkeiten

### Raspberry Pi (Trixie)
```bash
# System-Pakete (via apt):
sudo apt-get install -y \
    python3-scp \
    python3-paramiko \
    python3-opencv \
    python3-numpy
```

### Client-PC
```bash
# Python-Pakete (via pip in venv):
pip install -r config/requirements.txt
```

### MediaMTX
- **Version:** v1.9.1+
- **Download:** https://github.com/bluenviron/mediamtx/releases

---

## 🧪 Tests durchgeführt

### ✅ MediaMTX Funktionalität
- On-Demand Modus funktioniert
- Stream startet/stoppt automatisch
- RTSP-Verbindung stabil

### ✅ Auto-Trigger System
- Stream-Verbindung erfolgreich
- Vogel-Erkennung funktioniert (Confidence 0.50-0.59)
- Trigger aktiviert nach 1.0s

### ✅ Dual-Kamera-Betrieb
- Kamera 1: Preview-Stream (MediaMTX)
- Kamera 0: Aufnahmen (rpicam-vid)
- Sequenzieller Betrieb funktioniert

### ✅ Manuelle Aufnahmen
- 5 Zeitlupen-Videos erfolgreich
- Transfer via SCP funktioniert
- Audio-Synchronisation OK

### ✅ Trigger-Logik
- 1.0s Duration funktioniert
- 0.5s Toleranz verhindert Timer-Resets
- Responsive bei beweglichen Vögeln

---

## ⚠️ Bekannte Probleme

### 1. Hailo AI HAT nicht funktional
**Status:** Trixie DKMS-Treiber fehlt  
**Impact:** Mittel  
**Workaround:** CPU-basiertes YOLO funktioniert

### 2. H.264 stderr Warnungen
**Status:** Kosmetisch, funktioniert trotzdem  
**Impact:** Niedrig  
**Workaround:** `grep -v '\[h264'` in Scripts

### 3. Paralleler Kamera-Betrieb unmöglich
**Status:** libcamera-Limitierung (by design)  
**Impact:** Niedrig  
**Lösung:** On-Demand Modus implementiert

---

## 📚 Neue Dokumentation

### docs/TRIXIE-MIGRATION.md
Vollständiger Migration-Guide:
- Breaking Changes erklärt
- MediaMTX Setup-Anleitung
- Dual-Kamera-Strategie
- Code-Änderungen dokumentiert
- Rollback-Anleitung

### docs/INSTALLATION-TRIXIE.md
Schritt-für-Schritt Installation:
- Hardware-Requirements
- Raspberry Pi Setup
- MediaMTX Installation & Konfiguration
- Python-Pakete (apt statt pip)
- Client-PC Setup
- Test-Checkliste
- Troubleshooting

### README.md Updates
- Trixie-Warning im Header
- Version-Badge: v1.3.0-dev
- MediaMTX Requirements hinzugefügt
- Installation-Steps aktualisiert
- Branch-Strategie erklärt

### docs/CHANGELOG.md
- v1.3.0-dev Sektion mit Breaking Changes
- Alle Features dokumentiert
- Fixes und Tests aufgelistet

### kamera-auto-trigger/README.md
- RTSP statt TCP dokumentiert
- MediaMTX-Voraussetzungen
- On-Demand Modus erklärt

---

## 🔄 Migration von Bookworm (v1.2.x)

### Schritt 1: Branch wechseln
```bash
git checkout feat/trixie-support
git pull origin feat/trixie-support
```

### Schritt 2: Raspberry Pi neu aufsetzen
```bash
# Raspberry Pi OS Trixie installieren
# Siehe: docs/INSTALLATION-TRIXIE.md
```

### Schritt 3: MediaMTX installieren
```bash
# Vollständige Anleitung in:
# docs/INSTALLATION-TRIXIE.md
```

### Schritt 4: Python-Pakete via apt
```bash
sudo apt-get install python3-scp python3-paramiko
```

### Schritt 5: Tests durchführen
```bash
# MediaMTX Status:
sudo systemctl status mediamtx

# Auto-Trigger Test:
./kamera-auto-trigger/start-vogel-beobachtung.sh
```

---

## 🎯 Roadmap für v1.3.0 (Stable)

- [ ] Produktions-Tests mit echten Vögeln
- [ ] Performance-Optimierung (CPU-Last)
- [ ] Hailo AI HAT Support (wartet auf DKMS)
- [ ] Merge zu main-Branch
- [ ] bookworm-legacy Branch erstellen
- [ ] Release v1.3.0 taggen

---

## 🆘 Support

**Bei Problemen mit Trixie:**

1. **Logs prüfen:**
   ```bash
   sudo journalctl -u mediamtx -n 100
   ```

2. **Migration-Guide:**
   [docs/TRIXIE-MIGRATION.md](../docs/TRIXIE-MIGRATION.md)

3. **Installation-Guide:**
   [docs/INSTALLATION-TRIXIE.md](../docs/INSTALLATION-TRIXIE.md)

4. **GitHub Issues:**
   https://github.com/kamera-linux/vogel-kamera-linux/issues

---

## 📊 Statistiken

**Geänderte Dateien:** 9
- 4 Scripts aktualisiert
- 5 Dokumentations-Dateien erstellt/aktualisiert

**Zeilen-Änderungen:**
- stream_processor.py: ~60 Zeilen
- ai-had-kamera-auto-trigger.py: ~10 Zeilen
- run-auto-trigger.sh: ~15 Zeilen
- Dokumentation: ~800 Zeilen neu

**Tests:** 6 Kategorien
- ✅ MediaMTX: Funktional
- ✅ Auto-Trigger: Funktional
- ✅ Dual-Kamera: Funktional
- ✅ Manuelle Aufnahmen: Funktional
- ✅ Trigger-Logik: Optimiert
- ⚠️ Hailo HAT: Nicht funktional (bekannt)

---

## 🙏 Credits

**Entwickelt von:** kamera-linux Team  
**Testing:** Produktiv-Einsatz im Vogelhaus  
**Dokumentation:** Vollständig, step-by-step  
**Community:** GitHub Issues & Discussions

---

## 📝 Lizenz

MIT License - siehe [LICENSE](../LICENSE)

---

**v1.3.0-dev - Trixie Support**  
*Branch: feat/trixie-support*  
*Datum: 1. November 2025*
