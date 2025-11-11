# Legacy Skripte & Systeme (Archiv)

**Status:** ⚠️ VERALTET - Nur zur Referenz

Diese Skripte und Systeme wurden durch das **Unified Camera Monitor System (v2.0)** ersetzt und werden nicht mehr aktiv verwendet.

## 📦 Archivierte Komponenten

### 🎯 Auto-Trigger System (kamera-auto-trigger/, v1.2.0)

**Archivierungsdatum:** 11. November 2025 (v2.0.0)

Das alte Auto-Trigger System verwendete:
- TCP-Stream über Netzwerk (Client-seitige AI-Erkennung)
- Separate Preview- und Recording-Prozesse
- SSH-basierte Fernsteuerung
- Komplexe Wrapper-Skripte

**Ersetzt durch:** `unified-camera-monitor.py` mit integrierter AI-Erkennung

**Archivierte Dateien:**
- `start-vogel-beobachtung.sh` - Interaktiver Wrapper
- `scripts/ai-had-kamera-auto-trigger.py` - Python Auto-Trigger
- `run-auto-trigger.sh` - Legacy-Trigger-System
- `docs/` - Alte Auto-Trigger Dokumentation

**Migration:**
```bash
# Alt (v1.2.0): Client-seitiges Auto-Trigger
./kamera-auto-trigger/start-vogel-beobachtung.sh

# Neu (v2.0.0): Unified Monitor auf Raspberry Pi
python3 raspberry-pi-scripts/unified-camera-monitor.py --threshold 0.4
```

---

### 🌐 Network-Tools (network-tools/, v1.2.0)

**Archivierungsdatum:** 11. November 2025 (v2.0.0)

Netzwerk-Diagnose-Tools für TCP-Stream-Qualitätsprüfung.

**Ersetzt durch:** Nicht mehr benötigt (kein Netzwerk-Stream)

**Archivierte Dateien:**
- `test-network-quality.py` - TCP-Stream-Diagnostik
- `README.md` - Network-Tools Dokumentation

**Obsolet weil:** Unified Monitor läuft lokal, kein Netzwerk-Stream erforderlich

---

### 🍓 Raspberry Pi Stream-Skripte (raspberry-pi-scripts/, v1.2.0-1.3.x)

**Archivierungsdatum:** 11. November 2025 (v2.0.0)

Legacy-Skripte für Preview-Streams und RTSP-Streaming.

**Ersetzt durch:** `unified-camera-monitor.py` mit integrierter picamera2-Vorschau

**Archivierte Dateien:**
- `start-preview-stream.sh` - Altes FFmpeg-basiertes Preview
- `start-preview-stream-v2.sh` - Preview v2
- `start-preview-stream-watchdog.sh` - Stream-Watchdog
- `start-rtsp-stream.sh` - RTSP-Streaming
- `start-tcp-preview-stream.sh` - TCP-basierter Preview
- `start-tcp-preview-watchdog.sh` - TCP-Watchdog
- `audio-monitor.sh` - Audio-Monitoring

**Migration:**
```bash
# Alt: Separater Preview-Stream
./raspberry-pi-scripts/start-preview-stream-v2.sh

# Neu: Integrated Preview im Unified Monitor
python3 raspberry-pi-scripts/unified-camera-monitor.py --preview-fps 6
```

---

### 🐍 Remote-Steuerungs-Skripte (v1.x)

1. **`ai-had-audio-remote-param-vogel-libcamera-single.py`**
   - Zweck: Audio-Aufnahme via SSH auf Remote-Raspberry Pi
   - Ersetzt durch: `unified-camera-monitor.py` (integrierte Audio-Unterstützung)
   - Letzte Version: v1.3.x

2. **`ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py`**
   - Zweck: 4K Video-Aufnahme mit optionaler AI-Objekterkennung via SSH
   - Ersetzt durch: `unified-camera-monitor.py` (direkte Kamera-Kontrolle)
   - Letzte Version: v1.3.x

3. **`ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py`**
   - Zweck: Zeitlupen-Aufnahmen (120fps) via SSH
   - Ersetzt durch: `unified-camera-monitor.py` mit `--slowmo` Flag
   - Letzte Version: v1.3.x

### Konfigurations-Dateien

### Konfigurations-Dateien

4. **`config.py`**
   - Zweck: Zentrale Konfiguration für SSH, Pfade, Remote-Hosts
   - Ersetzt durch: Command-line Parameter in `unified-camera-monitor.py`
   - Nicht mehr benötigt: SSH-Aufrufe entfallen

5. **`.env.example`**
   - Zweck: Umgebungsvariablen-Template für SSH-Konfiguration
   - Nicht mehr benötigt: Keine .env Dateien im neuen System

---

## 🔄 Komplette Migration zum Unified System (v2.0)

### Architektur-Vergleich

**Vorher (v1.x - v1.3.x):**
```
Client-PC → SSH → Raspberry Pi → libcamera-vid
                                → arecord
                ← SCP ← Dateien kopieren

PLUS: Auto-Trigger über TCP-Stream
Client-PC → TCP-Stream ← Raspberry Pi
  ↳ AI-Analyse
  ↳ SSH-Trigger bei Erkennung
```

**Jetzt (v2.0):**
```
Raspberry Pi: unified-camera-monitor.py
  ↳ picamera2 (Kamera-Zugriff)
  ↳ YOLOv8 (AI-Analyse lokal)
  ↳ Automatische Aufnahme bei Trigger
  ↳ Traffic Light Monitoring
  ↳ Kein SSH/Netzwerk erforderlich
```
                ← SCP ← Dateien kopieren
```

**Jetzt (v2.x):**
```
Raspberry Pi: unified-camera-monitor.py
  ↳ Direkte picamera2 Kontrolle
  ↳ AI-Analyse lokal
  ↳ Aufnahme bei Trigger
  ↳ Keine SSH-Overhead
```

### Vorteile des neuen Systems (v2.0)

✅ **Keine Kamera-Konflikte** - Ein einziger Prozess kontrolliert alles
✅ **Schnellere Reaktionszeit** - Kein SSH/TCP-Overhead
✅ **Einfachere Konfiguration** - Alles über CLI-Parameter
✅ **Besseres Monitoring** - Echtzeit-Status mit Traffic Lights (🟢🟡🔴)
✅ **Automatische Aufnahme** - Bei Vogel-Erkennung direkt Recording
✅ **Auto-Shutdown** - Bei kritischer Temperatur (>75°C)
✅ **Kein Netzwerk benötigt** - Alles läuft lokal auf dem Pi

### Migrations-Matrix

| Legacy-System | v2.0 Equivalent | CLI-Parameter |
|---------------|-----------------|---------------|
| `ai-had-kamera-remote-param...py --duration 5` | `unified-camera-monitor.py` | `--recording-duration 300` |
| `ai-had-kamera-auto-trigger.py` | `unified-camera-monitor.py` | (automatisch aktiviert) |
| `start-preview-stream.sh` | Integriert | `--preview-fps 6` |
| TCP-Stream über Netzwerk | Lokale AI-Analyse | `--threshold 0.4` |
| `.env` Konfiguration | CLI-Parameter | `--help` |
| SSH-basierte Remote-Control | `start-unified-monitoring.sh` | Remote-Wrapper |

### Quick Migration Examples

**Beispiel 1: Standard 4K-Aufnahme mit AI**

Alt (v1.3.x):
```bash
python3 ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 3 --width 4096 --height 2160 --ai-modul on
```

Neu (v2.0):
```bash
python3 raspberry-pi-scripts/unified-camera-monitor.py \
  --recording-duration 180
```

**Beispiel 2: Auto-Trigger für Vogelerkennung**

Alt (v1.2.0):
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh
```

Neu (v2.0):
```bash
python3 raspberry-pi-scripts/unified-camera-monitor.py --threshold 0.4
# Oder vom Client-PC:
./start-unified-monitoring.sh
```

**Beispiel 3: Zeitlupen-Aufnahme**

Alt (v1.3.x):
```bash
python3 ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py \
  --duration 2 --width 1536 --height 864 --fps 120
```

Neu (v2.0):
```bash
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo
```

**Neu:**
```bash
# Direkt auf Raspberry Pi
python3 raspberry-pi-scripts/unified-camera-monitor.py \
  --recording-duration 180 --resolution 4096x2160 --ai-threshold 0.4

# Oder via Wrapper vom Client-PC
./kamera-auto-trigger/start-unified-monitoring.sh
```

## 📝 Warum archiviert?

**Datum:** 11. November 2025
**Branch:** feature/unified-camera-process
**Commit:** 9638f24

Die alten Remote-Steuerungs-Skripte hatten folgende Probleme:
- Komplexe SSH-Orchestrierung mit paramiko/SCP
- Kamera-Konflikte zwischen Preview und Recording
- Langsame Reaktionszeiten durch Netzwerk-Latenz
- Schwierige Fehlersuche bei SSH-Problemen
- Doppelte Konfiguration (Client + Server)

Das neue `unified-camera-monitor.py` löst alle diese Probleme durch:
- Direkten Zugriff auf die Kamera (picamera2)
- Single-Process Architektur
- Lokale AI-Analyse ohne Latenz
- Einfache CLI-Parameter statt .env Dateien
- Integriertes Health-Monitoring mit Auto-Shutdown

## 🔍 Für Entwickler

Falls Sie die alten Skripte als Referenz benötigen:
- Alle Dateien bleiben im Git-History erhalten
- Commit vor Archivierung: 69b790e
- Branch: feature/unified-camera-process

Bei Fragen: GitHub Issues erstellen

---

**Hinweis:** Diese Skripte wurden **nicht gelöscht**, sondern **archiviert** für zukünftige Referenz und Dokumentationszwecke.
