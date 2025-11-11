# Legacy Skripte (Archiv)

**Status:** ⚠️ VERALTET - Nur zur Referenz

Diese Skripte wurden durch das **Unified Camera Monitor System** ersetzt und werden nicht mehr aktiv verwendet.

## 📦 Archivierte Dateien

### Remote-Steuerungs-Skripte (v1.x)

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

4. **`config.py`**
   - Zweck: Zentrale Konfiguration für SSH, Pfade, Remote-Hosts
   - Ersetzt durch: Command-line Parameter in `unified-camera-monitor.py`
   - Nicht mehr benötigt: SSH-Aufrufe entfallen

5. **`.env.example`**
   - Zweck: Umgebungsvariablen-Template für SSH-Konfiguration
   - Nicht mehr benötigt: Keine .env Dateien im neuen System

## 🔄 Migration zum Unified System

### Was hat sich geändert?

**Vorher (v1.x):**
```
Client-PC → SSH → Raspberry Pi → libcamera-vid
                                → arecord
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

### Vorteile des neuen Systems

✅ **Keine Kamera-Konflikte** - Ein einziger Prozess kontrolliert alles
✅ **Schnellere Reaktionszeit** - Kein SSH-Overhead
✅ **Einfachere Konfiguration** - Alles über CLI-Parameter
✅ **Besseres Monitoring** - Echtzeit-Status mit Traffic Lights
✅ **Automatische Aufnahme** - Bei Vogel-Erkennung direkt Recording

### Migration Guide

Falls Sie von den alten Skripten migrieren:

**Alt:**
```bash
python3 ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
  --duration 3 --width 4096 --height 2160 --ai-modul on
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
