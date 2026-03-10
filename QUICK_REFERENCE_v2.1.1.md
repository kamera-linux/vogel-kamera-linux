# 🎬 Vogel-Kamera v2.1.1 - Quick Reference

**Version:** 2.1.1 | **Datum:** 10. März 2026 | **Status:** Stabil ✅

---

## 🚀 Start (Empfohlene Lösung - Detect-and-Record!)

```bash
# SSH zum Raspberry Pi
ssh -i ~/.ssh/your-ssh-key <your-username>@your-raspberry-pi

# Empfohlen: Zwei-Phasen Detection → Recording (mit Repeat)
cd ~/vogel-kamera-linux/unified-monitor-client
python3 unified_monitor_client.py normal \
  --detect-and-record \
  --threshold 0.4 \
  --cooldown 15 \
  --trigger 1.0 \
  --duration 30 \
  --repeat
```

**Ablauf:**
1. 🔍 **Phase 1:** Vogelerkennung (schnell, kein Video)
2. 🎥 **Phase 2:** Nach Vogel → 30s Aufnahme mit Audio
3. 🔄 **Repeat:** Zurück zu Phase 1, wieder auf Vogel warten

**Ergebnis:** MP4 im Ordner `~/Videos/Vogelhaus/`

---

## 🆕 Was ist Neu in v2.1.1?

### ✨ Graceful Ctrl+C Shutdown
```bash
# Starte Monitoring
python3 unified_monitor_client.py normal --detect-and-record --repeat

# Drücke Ctrl+C →
# 🛑 Abgebrochen vom Benutzer (Ctrl+C)
# 🧹 Räume auf und killen alle Remote-Prozesse...
#    ✅ Status-Reporter beendet
#    ✅ Detection-Prozess beendet
#    🧹 Remote-Cleanup läuft...
#    ✅ Remote-Prozesse gekilled
#    ✅ SSH-Verbindung geschlossen
# ✅ Cleanup complete - Auf Wiedersehen!
```
**Sauber:** Keine Zombie-Prozesse mehr!

### 🔍 Diagnose vor Cleanup
```bash
# Automatisch vor Cleanup angezeigt:
# === LAUFENDE PROZESSE ===
# === OFFENE FILE HANDLES ===
# === V4L2 DEVICES ===
```
**Hilft bei:** Debugging von "Device or resource busy" Fehlern

### 🔧 Verbessertes Process Management
- **3-stagige Cleanup** (nicht mehr aggressive Kill-All)
- **SIGTERM → Warten → SIGKILL** (nur wenn nötig)
- **V4L2-Device-Lock** freigeben
- **Targeted Killing** (nicht alle python3 prozesse!)

---

## 🎯 Drei Modi Übersicht

### 1️⃣ **DETECT-AND-RECORD** (EMPFOHLEN!)
```bash
python3 unified_monitor_client.py normal \
  --detect-and-record \
  --threshold 0.4 \
  --cooldown 15 \
  --trigger 1.0 \
  --duration 30 \
  --repeat
```
**Vorteile:**
- ✅ Verhindert Time-Lapse/beschleunigte Vorschau
- ✅ CPU-effizient bis Vogel erkannt
- ✅ Saubere Prozess-Trennung
- ✅ Mit `--repeat` für Endlosschleife

---

### 2️⃣ **AUTO-RECORD** (Legacy - veraltet)
```bash
python3 unified_monitor_client.py normal \
  --auto-record \
  --threshold 0.4 \
  --cooldown 15
```
**⚠️ Hinweis:** Kann zu beschleunigter Verarbeitung führen.  
**Nutze stattdessen:** `--detect-and-record`

---

### 3️⃣ **MANUAL-RECORD** (Direkte Aufnahmen)
```bash
# 60 Sekunden Video ohne AI
python3 unified_monitor_client.py normal \
  --manual-record \
  --duration 60 \
  --resolution 1080p \
  --fps 30 \
  --bitrate 5000
```

**Para Beispiele:**
```bash
# 4K Cinema
--manual-record --duration 30 --resolution 4k --bitrate 8000

# Slow-Mo (120fps)
--manual-record --duration 20 --fps 120 --resolution 1080p

# Nur Audio
--manual-record --duration 300 --audio-only
```

---

## 🔧 Parameter Reference

### Detection Parameter
```
--threshold FLOAT      Erkennungs-Schwelle 0.0-1.0 (default: 0.5)
                       → 0.3 = sensibel, 0.7 = nur sicher
--cooldown INT        Sekunden zwischen Triggern (default: 15)
                       → Zeit zum "Luftholen" nach Aufnahme
--trigger FLOAT       Erkennungs-Dauer in Sekunden (default: 1.0)
                       → Wie lange Vogel sichtbar sein muss
```

### Recording Parameter
```
--duration INT        Aufnahmedauer in Sekunden (default: 10)
--fps INT            Frames per Second: 15, 24, 30, 60, 120
--resolution STR     480p, 720p, 1080p, 2k, 4k
--bitrate INT        Bitrate in kbps (z.B. 5000, 10000)
--audio-only         Nur Audio ohne Video
```

### Modi-spezifische Parameter
```
--detect-and-record  Zwei-Phasen: Detection → Recording
--repeat             Endlosschleife (mit --detect-and-record)
--auto-record        Legacy Vogelerkennung (kontinuierlich)
--manual-record      Reine Aufnahme ohne AI
```

---

## 📊 Empfehlung nach Use-Case

| Szenario | Befehl | Parameter |
|----------|--------|-----------|
| **Default Vogel-Monitoring** | `--detect-and-record` | `--threshold 0.4 --duration 30 --repeat` |
| **Geplante tägliche Session** | `--manual-record` | `--duration 3600 --resolution 1080p` |
| **4K Cinema Aufnahme** | `--manual-record` | `--duration 60 --resolution 4k --bitrate 8000` |
| **Slow-Motion ohne Budget** | `--manual-record` | `--fps 120 --duration 20` |
| **Nur Vogelgesang** | `--detect-and-record` | `--audio-only --duration 15 --repeat` |

---

## 🛑 Shutdown (Clean/Safe)

```bash
# Pressing Ctrl+C:
# - 🛑 Beendet Detection/Recording
# - 🧹 Räumt Remote-Prozesse sauber auf
# - 🔌 Schließt SSH-Verbindung
# - ✅ Sicher für soführen Neustart

# Beispiel: Nach Session stoppen
$ Ctrl+C
🛑 Abgebrochen vom Benutzer (Ctrl+C)
🧹 Räume auf und killen alle Remote-Prozesse...
   ✅ Status-Reporter beendet
   ✅ Detection-Prozess beendet
   ✅ Remote-Prozesse gekilled
   ✅ SSH-Verbindung geschlossen
✅ Cleanup complete - Auf Wiedersehen!
```

---

## 🐛 Troubleshooting

### "Device or resource busy"
**Problem:** Camera wird verwendet von vorherigem Prozess  
**Lösung:** 
```bash
# Diagnose wird automatisch vor Cleanup angezeigt
# Manuell checken:
ps aux | grep unified-camera
ps aux | grep rpicam
lsof | grep /dev/video

# Cleanup starten (Ctrl+C mit `--repeat` aktiviert)
```

### "Detection-Prozess läuft nicht"
**Problem:** Status-Reporter oder SSH-Fehler  
**Check:**
```bash
# SSH-Verbindung testen
ssh -i ~/.ssh/your-ssh-key <your-username>@your-raspberry-pi -c "ps aux | grep python"

# Remote Script checken
ssh ... -c "ls -la /home/<your-username>/vogel-kamera-linux/raspberry-pi-scripts/"
```

---

## 📂 Dateistruktur

```
unified-monitor-client/
├── unified_monitor_client.py     ← Hauptprogramm
├── config.py                     ← Konfiguration
├── ssh_manager.py               ← SSH-Remote-Exec
├── monitors.py                  ← Log/Video/Status-Monitoring
├── version_manager.py           ← Version-Sync
├── requirements.txt             ← Dependencies
├── VERSION                       ← Aktuelle Version (2.1.1)
├── .env                         ← SSH-Credentials (lokal)
└── README.md                    ← Ausführliche Doku
```

---

## 🔗 Weitere Dokumentation

- [README.md](README.md) - Ausführliche Dokumentation aller Modi
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Ersteinrichtung & Konfiguration
- [DETECT_AND_RECORD.md](DETECT_AND_RECORD.md) - Zwei-Phasen-Modus Details
- [../CHANGELOG.md](../CHANGELOG.md) - Vollständige Release-Historie

---

**Made with ❤️ for Bird Lovers** 🐦  
Version: 2.1.1 | Stable
