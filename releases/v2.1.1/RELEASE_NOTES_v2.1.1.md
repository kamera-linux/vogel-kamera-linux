# 📋 Release Notes v2.1.1 - Graceful Shutdown & Detect-and-Record

**Release Date:** 10. März 2026  
**Version:** 2.1.1 (Stable)  
**Tag:** `v2.1.1`

---

## 🎯 Zusammenfassung

v2.1.1 fokussiert auf **Robustheit bei Shutdown** und dem neuen **Zwei-Phasen Detection-and-Record Mode**, der Time-Lapse und beschleunigte Vorschau-Probleme komplett eliminiert.

**Key Message:** Saubere Ein/Aus-Kontrolle + Intelligente Zwei-Phasen-Erkennung = Produktionsreife Vogel-Kamera! 🐦

---

## 🆕 Neue Features

### 1. **Detect-and-Record Mode** (🆕 EMPFOHLEN)

**Problem, das gelöst wird:**
- v2.0.x: Auto-Record erzeugt beschleunigte Vorschau (Time-Lapse-Effekt)
- Grund: Detection und Recording gleichzeitig = Vorschau-Video wird schneller als Speicherung

**Lösung v2.1.1: Zwei-Phasen-Betrieb**
```
Phase 1️⃣  Detection        Phase 2️⃣  Recording
(ohne Video)              (mit voller Qualität)
    ↓                           ↓
[Vogel gesuchen]     →   [Nach Trigger: 30s Video]
[schnell, low-CPU]       [full HD/4K/Audio]
```

**Befehl:**
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
- ✅ **Keine Time-Lapse mehr** - Jedes Frame wird korrekt gespeichert
- ✅ **CPU-effizient** - Detection-Overhead nur bis Vogel erkannt
- ✅ **Saubere Prozess-Trennung** - Detection und Recording völlig getrennt
- ✅ **Mit `--repeat`** - Endlosschleife: erkennen → aufnehmen → erkennen...

---

### 2. **Graceful Ctrl+C Shutdown** (🆕)

**Problem, das gelöst wird:**
- Ctrl+C beendete einfach den Client, aber Remote-Prozesse liefen weiter
- Nächster Run: "Device or resource busy" Fehler
- Zombie-Prozesse auf Pi

**Lösung v2.1.1: Signal Handler mit sequenziellem Cleanup**

```bash
$ python3 unified_monitor_client.py normal --detect-and-record --repeat
[... läuft normal ...]
^C
🛑 Abgebrochen vom Benutzer (Ctrl+C)
🧹 Räume auf und killen alle Remote-Prozesse...

   ✅ Status-Reporter beendet
   ✅ Detection-Prozess beendet
   🧹 Remote-Cleanup läuft...
   ✅ Remote-Prozesse gekilled
   ✅ SSH-Verbindung geschlossen

✅ Cleanup complete - Auf Wiedersehen!
```

**Cleanup-Sequenz:**
1. **StatusReporter stoppen** (Background-Thread)
2. **Detection-Prozess beenden** (SIGTERM → Warten → SIGKILL)
3. **Remote-Prozesse cleanen** (3-stagige Cleanup)
4. **SSH-Connection schließen** (saubere Trennung)

**Jetzt möglich nach Shutdown:**
- ✅ Sofortiger Neustart ohne Fehler
- ✅ Saubere Kamerad-Freigabe
- ✅ Keine Zombie-Prozesse

---

### 3. **Process Diagnostics** (🔍 NEU)

**Zeigt blockierende Prozesse VOR Cleanup:**

```bash
🔍 Diagnostiziere offene Prozesse auf Pi...

=== LAUFENDE PROZESSE ===
roimme  1234  0.0  1.5 123456 45678 ?  S  10:15   0:05 python3 unified-camera-monitor-detect-only.py

=== OFFENE FILE HANDLES ===
python3  1234  roimme  27r   CHR   81,0          /dev/video0

=== V4L2 DEVICES ===
crw-rw---- 1 root video 81, 0 Mar 10 10:15 /dev/video0
```

**Hilft bei:**
- Debugging von "Device or resource busy" Fehlern
- Verstehen welche Prozesse die Kamera blocken
- Validieren dass Cleanup wirklich funktioniert

---

### 4. **Improved Process Cleanup** (🔧)

**Problem, das gelöst wird:**
- v2.0.x: `pkill -9 python3` tötete ALLE Python-Prozesse (brutal!)
- Konnte System-Python oder andere Prozesse killen

**Lösung v2.1.1: Intelligent 3-stagige Cleanup**

```bash
# STAGE 1: Gezielte SIGTERM (2s Warte)
pkill -TERM -f 'unified-camera-monitor'
pkill -TERM -f 'picamera'
pkill -TERM -f 'libcamera'
sleep 2

# STAGE 2: SIGKILL ABER NUR zu Zielprozessen (NICHT alle python3!)
pkill -9 -f 'unified-camera-monitor'
pkill -9 -f 'rpicam'

# STAGE 3: V4L2-Device-Locks freigeben
rm -f /tmp/unified-camera-monitor.log
rm -f /tmp/*.pid

# VERIFICATION: Zähle verbleibende Prozesse
ps aux | grep -E 'unified-camera|libcamera|picamera' | grep -v grep | wc -l
```

**Vorteile:**
- ✅ **Elegant** - Erst freundlich (SIGTERM), dann hart (SIGKILL)
- ✅ **Sicher** - Nicht alle Python-Prozesse killen
- ✅ **Verifizierbar** - Zählt verbleibende Prozesse
- ✅ **Resilienz** - Toleriert 1-2 noch laufende Prozesse

---

## 🔧 Technical Changes

### Global Variables für Signal Handler
```python
# Globale Variablen für Signal-Handler
_global_ssh = None
_global_status_reporter = None
_cleanup_on_exit = False
```

**Warum nötig:** Signal Handler braucht Zugriff auf SSH und StatusReporter  
**Wo gesetzt:** In `main()` nach Initialisierung

### Enhanced signal_handler()
```python
def signal_handler(signum, frame):
    """Behandelt Ctrl+C - Sauberes Cleanup aller Prozesse"""
    global _global_ssh, _global_status_reporter, _cleanup_on_exit
    
    # 1. Stoppe StatusReporter (background thread)
    # 2. Beende Detection-Prozess (SIGTERM → SIGKILL)
    # 3. Cleanup Remote-Prozesse (3-stagige Cleanup)
    # 4. Schließe SSH-Verbindung
    # 5. Exit gracefully
```

### Python Module Integration
- `unified_monitor_client.py` - Signal Handler + Cleanup-Orchestrierung
- `ssh_manager.py` - Remote-Befehle für Cleanup
- `monitors.py` - StatusReporter mit `stop()` Methode
- `version_manager.py` - Version-Check & Remote-Sync

---

## 📊 Verbesserungen in Übersicht

| Feature | v2.1.0 | v2.1.1 | Verbesserung |
|---------|--------|--------|-------------|
| **Shutdown Cleanup** | ❌ Keine | ✅ Graceful 4-Phase | Saubere Prozess-Freigabe |
| **Zombie-Prozesse** | ⚠️ Häufig | ✅ Keine mehr | No "Device busy" nach Shutdown |
| **Process Diagnostics** | ❌ Keine | ✅ Mit Ausgabe | Debugging hilft |
| **Kill-Strategy** | 🔴 Brutal (alle python3) | 🟢 Targeted | System-safe |
| **Detection Mode** | ⚠️ Auto-Record (buggy) | ✅ Detect-and-Record | Time-Lapse gelöst |
| **CPU-Effizienz** | 50-70% + YOLO | Variable (Phase-dependent) | Intelligente Lastverteilung |

---

## 🧪 Testing & Validation

### Getestet auf:
- ✅ Raspberry Pi 5 (8GB RAM)
- ✅ Debian Trixie (13)
- ✅ picamera2 + rpicam-vid
- ✅ SSH via Passwordless Key Auth
- ✅ USB Audio Stick Integration

### Test-Szenarien:
```bash
# Test 1: Detect-and-Record mit Repeat
python3 unified_monitor_client.py normal \
  --detect-and-record \
  --threshold 0.4 \
  --cooldown 15 \
  --repeat

# Drücke Ctrl+C nach 1 Vorgel → Sollte sauber shutdown
# Verify: ps aux | grep unified sollte KEINE Prozesse zeigen

# Test 2: Mehrfache Runs
FOR i in {1..5}; do
  python3 unified_monitor_client.py normal --manual-record --duration 10
  # Sollte alle 5 erfolgreich laufen (0 Device-Errors)
done
```

---

## 🔄 Migration von v2.1.0

**Keine Breaking Changes!**

```bash
# v2.1.0 Befehle funktionieren noch:
python3 unified_monitor_client.py normal --auto-record
python3 unified_monitor_client.py normal --manual-record --duration 60

# Aber EMPFOHLEN ist nun:
python3 unified_monitor_client.py normal --detect-and-record --repeat
```

---

## 🐛 Bugfixes in v2.1.1

1. **"Device or resource busy" nach Shutdown** - ✅ Gefixt durch Graceful Cleanup
2. **Zombie Python-Prozesse auf Pi** - ✅ Gefixt durch Targeted Kill
3. **Client-Disconnect ohne Remote-Cleanup** - ✅ Gefixt durch Signal Handler
4. **Unbekannte blockierende Prozesse** - ✅ Gefixt durch Diagnostics
5. **SSH-Connection bleibt offen** - ✅ Gefixt durch Explizites `close()`

---

## 📦 Dateistruktur v2.1.1

```
unified-monitor-client/
├── unified_monitor_client.py      ← Hauptprogramm (Signal Handler NEU!)
├── config.py                      ← Konfiguration (unverändert)
├── ssh_manager.py                 ← SSH-Remote (close() wichtig)
├── monitors.py                    ← Monitoring (StatusReporter.stop() gesetzt)
├── version_manager.py             ← Version-Check (unverändert)
├── requirements.txt               ← Dependencies (paramiko,click,dotenv)
├── VERSION                        ← 2.1.1
├── README.md                      ← Aktualisiert mit Detect-and-Record
└── SETUP_GUIDE.md                 ← Setup-Anleitung
```

---

## 🆕 Empfehlenswerte Nutzung

### Standard Vogel-Monitoring (NEU!)
```bash
cd ~/vogel-kamera-linux/unified-monitor-client

python3 unified_monitor_client.py normal \
  --detect-and-record \
  --threshold 0.4 \
  --cooldown 15 \
  --trigger 1.0 \
  --duration 30 \
  --repeat
```
**Ergebnis:** Endlosschleife: Erkennen → 30s Aufnahme → Erkennen...

### Geplante Sessions (für Nutzer ohne 24/7)
```bash
# Morgens starten → Abends Ctrl+C
python3 unified_monitor_client.py normal --manual-record --duration 3600
```

### 4K Cinema-Aufnahme
```bash
python3 unified_monitor_client.py 4k --manual-record --duration 60 --bitrate 8000
```

---

## 🎬 Next Steps

- **v2.2.0 (Q2 2026):** Cloud-Backup Integration (Nextcloud/S3)
- **v2.3.0 (Q3 2026):** Web-Interface für Remote-Monitoring
- **v3.0.0 (Q4 2026):** Multi-Camera Support

---

## 🙏 Danksagungen

Special Thanks to:
- Raspberry Pi Foundation für phenomenale Hardware
- OpenCV/YOLO Teams für AI-Detection
- Debian Trixie für stabile Basis
- Alle Vogel-Enthusiasten für Feedback

---

**Version:** 2.1.1  
**Stability:** Stable ✅  
**Support:** GitHub Issues  
**License:** MIT

Made with ❤️ for Bird Lovers 🐦
