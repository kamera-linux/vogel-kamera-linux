# Unified Monitor Client (Python)

**Python-Replacement** für die alte Bash-basierte `start-unified-monitoring.sh`. Vollständige Orchestrierung der Vogel-Kamera-Überwachung mit **Triple-Mode Support**.

## 🎯 Drei Modi - Eine Lösung

### 🆕 **DETECT-AND-RECORD MODE** (Zwei-Phasen - EMPFOHLEN!)
- **Phase 1 - Detection:** Schnelle Vogelerkennung ohne Video-Speicherung
- **Phase 2 - Recording:** Nach Trigger → Volle Aufnahme mit Audio
- **Vorteile:** 
  - Verhindert Time-Lapse/beschleunigte Vorschau-Probleme
  - CPU-effizient: Detection-Overhead nur bis Vogel erkannt
  - Saubere Prozess-Trennung zwischen Detection und Recording
- **Parameter:** `--threshold`, `--cooldown`, `--trigger`, `--duration`, `--bitrate`
- **Befehl:** `python3 unified_monitor_client.py normal --detect-and-record --repeat`
- **Beispiel:** `python3 unified_monitor_client.py normal --detect-and-record --threshold 0.4 --duration 30 --repeat`

### 🔍 **AUTO-RECORD MODE** (Vogelerkennung mit picamera2)
- **Backend:** picamera2 mit Dual-Stream (Recording + Preview)
- **AI-Erkennung:** YOLOv26n für automatische Vogelerkennung
- **Funktion:** Kontinuierliche Überwachung mit automatischer Aufnahme bei Vogel-Erkennung
- **Parameter:** `--threshold`, `--cooldown`, `--trigger-duration`
- **Befehl:** `python3 unified_monitor_client.py normal --auto-record`
- **⚠️ Hinweis:** Kann zu beschleunigter Video-Verarbeitung führen. Nutze `--detect-and-record` für bessere Ergebnisse.

### 📹 **MANUAL-RECORD MODE** (Reine Aufnahme mit rpicam-vid)
- **Backend:** rpicam-vid für stabile H264-Encoding
- **Funktion:** Direkte Video-Aufnahme ohne AI-Overhead
- **Parameter:** `--duration`, `--fps`, `--resolution`, `--bitrate`
- **Befehl:** `python3 unified_monitor_client.py normal --manual-record --duration 60`

## Features

✅ **Dual-Architecture:** Wähle zwischen KI-Monitoring oder reiner Aufnahme  
✅ **SSH-Management** mit Retry-Logik (paramiko)  
✅ **Automatische Versionskontrolle** & Remote-Skript-Sync  
✅ **Robustes Log-Tailing** (keine grep-Fehler!)  
✅ **Video-Watching & Sync** mit rsync  
✅ **Status-Reporting** (5-minütige Berichte)  
✅ **CLI-Interface** mit Click (typsicher)  
✅ **Threading** für gleichzeitige Operationen  
✅ **Strukturiertes Logging** (Farben & Timestamps)  

## 📊 Mode Selection Guide

### Welchen Modus soll ich nutzen?

| Aspekt | AUTO-RECORD | MANUAL-RECORD |
|--------|-------------|---------------|
| **Use Case** | Vogel-Monitoring mit automatischer Aufnahme | Reine Video-Aufnahmen, vorhersehbare Zeiten |
| **Backend** | picamera2 (Dual-Stream) | rpicam-vid (Single-Stream) |
| **Erkennung** | ✅ YOLO26n Vogelerkennung | ❌ Keine AI-Verarbeitung |
| **CPU-Last** | ~50-70% (+ YOLO26 AI) | ~200% H264-Encoding |
| **Speicher** | ~200MB | ~150MB |
| **Best für** | 📹 Kontinuierliches Monitoring | 🎥 Geplante Aufnahmen |
| **Trigger** | Vogel erkannt → Auto-Recording | Manuelles Start/Stop |
| **Beispiel** | Von Frühling bis Herbst 24/7 | Tägliche 10-Minuten-Sessions |

### Schnell-Entscheidung

- **"Ich will, dass die Kamera automatisch aufnimmt, wenn Vögel kommen"** → `--auto-record`
- **"Ich will gezielt Videos aufnehmen (z.B. täglich 1 Stunde)"** → `--manual-record --duration 3600`

## Installation

### Abhängigkeiten installieren

```bash
cd unified-monitor-client
pip install -r requirements.txt
```

**Abhängigkeiten:**
- `paramiko >= 2.11.0` – SSH-Verbindungen
- `click >= 8.0` – CLI-Arguments
- Python 3.8+

### SSH-Konfiguration

Das Skript benötigt SSH-Zugriff auf deinen Raspberry Pi. Die SSH-Einstellungen werden automatisch aus einer `.env`-Datei geladen.

**Einrichtung (einmalig):**

1. Kopiere `.env.example` zu `.env`:
```bash
cp .env.example .env
```

2. Öffne `.env` und ersetze die Werte mit deinen SSH-Einstellungen:
```bash
# ~./unified-monitor-client/.env

SSH_KEY=~/.ssh/your_ssh_key          # Dein SSH Private-Key
SSH_USER=your_pi_user                # Benutzername auf deinem Pi
SSH_HOST=your_pi_hostname            # Hostname oder IP des Pi
```

3. Überprüfe die Berechtigungen:
```bash
chmod 600 .env  # Schütze .env vor lesenden Zugriffen
```

**Beispiel:**
```bash
SSH_KEY=~/.ssh/your-ssh-key
SSH_USER=<your-username>
SSH_HOST=your-raspberry-pi
```

**Sicherheit:**
- `.env` wird **NICHT** in Git versioniert (siehe `.gitignore`)
- Deine SSH-Daten bleiben lokal auf deinem Rechner
- Nur `.env.example` wird geteilt (als Vorlage)

## Verwendung

### 🆕 DETECT-AND-RECORD Modus (EMPFOHLEN!) ⭐

Zwei-Phasen-Modus: Erst Vogelerkennung ohne Video (schnell), dann automatische Aufnahme beim Trigger.

```bash
# Standard: Einmalige Session mit Vogelekennung
python3 unified_monitor_client.py normal --detect-and-record \
  --threshold 0.4 --duration 30

# Mit Schleife: Endloses Monitoring
python3 unified_monitor_client.py normal --detect-and-record \
  --threshold 0.4 --cooldown 15 --trigger 1.0 --duration 30 --repeat

# Schneller Threshold (sensibel): 0.3
python3 unified_monitor_client.py normal --detect-and-record \
  --threshold 0.3 --duration 30 --repeat

# Hoher Threshold (nur sichere Erkennungen): 0.7
python3 unified_monitor_client.py normal --detect-and-record \
  --threshold 0.7 --duration 60 --repeat

# Slowmo-Modus für bessere Qualität
python3 unified_monitor_client.py slowmo --detect-and-record \
  --threshold 0.4 --duration 30 --repeat

# 4K With Detect-and-Record
python3 unified_monitor_client.py 4k --detect-and-record \
  --threshold 0.4 --duration 30 --repeat
```

**Vorteile:**
- ✅ Verhindert Time-Lapse/beschleunigte Vorschau-Probleme
- ✅ CPU-effizient: Detection-Overhead nur bis Vogel erkannt
- ✅ Saubere Prozess-Trennung zwischen Detection und Recording

---

### 🔍 AUTO-RECORD Modus (Legacy - veraltet ⚠️)

⚠️ **Hinweis:** Kann zu beschleunigter Video-Verarbeitung führen. Nutze stattdessen `--detect-and-record`.

```bash
# Standard: Kontinuierlich überwachen, bei Vogel-Erkennung aufnehmen
python3 unified_monitor_client.py normal --auto-record

# Mit Parametern: 0.5 Sekunden Cooldown, 20 Sekunden Aufnahmedauer
python3 unified_monitor_client.py normal --auto-record --cooldown 0.5 --trigger-duration 20

# Höherer Schwellenwert (nur sichere Erkennungen aufnehmen)
python3 unified_monitor_client.py normal --auto-record --threshold 0.7

# Slowmo-Modus mit AI-Monitoring (60fps @ 1536x864)
python3 unified_monitor_client.py slowmo --auto-record
```

### 📹 MANUAL-RECORD Modus (Reine Aufnahmen)

```bash
# 5 Sekunden Test-Aufnahme
python3 unified_monitor_client.py normal --manual-record --duration 5

# 10 Minuten kontinuierliche Aufnahme
python3 unified_monitor_client.py normal --manual-record --duration 600

# 4K Cinema-Modus, 30 Sekunden
python3 unified_monitor_client.py 4k --manual-record --duration 30

# Slowmo mit hohen FPS (60fps @ 1536x864), 2 Minuten
python3 unified_monitor_client.py slowmo --manual-record --duration 120
```

### Basis-Befehle (Standard-Modi ohne Auto/Manual)

```bash
# Test-Modus: 5 Sekunden (zum Testen der Verbindung)
python3 unified_monitor_client.py test

# Standard-Modus (1920x1080 @ 30fps + Audio)
python3 unified_monitor_client.py normal

# Zeitlupe-Modus (60fps @ 1536x864)
python3 unified_monitor_client.py slowmo

# Cinema 4K (4096x2160 @ 30fps + Audio, rpicam-vid)
python3 unified_monitor_client.py 4k
```

### Mit zusätzlichen Parametern

```bash
# Detect-and-Record mit Loop
python3 unified_monitor_client.py normal --detect-and-record --repeat

# Kürzerer Cooldown zwischen Aufnahmen
python3 unified_monitor_client.py slowmo --detect-and-record --cooldown 5 --repeat

# Benutzerdefinierte Aufnahmedauer
python3 unified_monitor_client.py 4k --manual-record --duration 60

# Höherer Erkennungs-Schwellenwert
python3 unified_monitor_client.py normal --detect-and-record --threshold 0.7 --repeat

# Verbose-Logging für Debugging
python3 unified_monitor_client.py 4k --detect-and-record --verbose
```

### Hilfe anzeigen

```bash
python3 unified_monitor_client.py --help
```

---

## 🛑 Graceful Shutdown (Neu in v2.1.1)

Drücke **Ctrl+C** um eine Session sauber zu beenden:

```bash
# Starten
$ python3 unified_monitor_client.py normal --detect-and-record --repeat

# Ctrl+C drücken:
# 🛑 Abgebrochen vom Benutzer (Ctrl+C)
# 🧹 Räume auf und killen alle Remote-Prozesse...
#    ✅ Status-Reporter beendet
#    ✅ Detection-Prozess beendet
#    ✅ Remote-Prozesse gekilled
#    ✅ SSH-Verbindung geschlossen
# ✅ Cleanup complete - Auf Wiedersehen!
```

**Vorteile:**
- ✅ Keine Zombie-Prozesse
- ✅ V4L2-Device-Lock wird freigegeben
- ✅ Sauber für sofortigen Neustart

---

## 🔧 Process Management Verbesserungen (v2.1.1)

### 3-stufige Cleanup-Strategie

Die neue Cleanup-Logik ist intelligenter und schonender:

1. **SIGTERM** - Normales Beenden (respektiert Cleanup)
2. **Warten** - 5 Sekunden für höfliches Shutdown
3. **SIGKILL** - Nur wenn SIGTERM nicht hilft

**Vorteil:** Verhindert "Device or resource busy" Fehler beim Neustart

### Diagnostik vor Cleanup

Automatisch vor dem Cleanup angezeigt:
```
=== LAUFENDE PROZESSE ===
=== OFFENE FILE HANDLES ===
=== V4L2 DEVICES ===
```

Hilft bei der Fehlersuche von Hardware-Fehlern.

## Architektur

```
unified-monitor-client/
├── unified_monitor_client.py    # Hauptskript (CLI-Interface)
├── config.py                    # Konfiguration & Konstanten
├── ssh_manager.py              # SSH-Wrapper mit paramiko
├── version_manager.py          # Version-Control & Skript-Sync
├── monitors.py                 # Log-Tailing, Video-Watching, Status-Reporting
├── requirements.txt            # Python-Abhängigkeiten
├── VERSION                     # Versionsnummer (v2.1.1)
└── README.md                   # Diese Datei
```

### Module

#### `config.py`
- SSH-Konfiguration (Host, User, Key)
- Remote & Lokale Pfade
- Recording-Modi Definition
- Monitor-Parameter (Threshold, Cooldown, etc.)

#### `ssh_manager.py`
Robuste SSH-Verwaltung mit:
- Automatische Retry-Logik
- Fehlerbehandlung
- Datei-Übertragung (SCP/SFTP)
- MD5-Hash-Abfragen

#### `version_manager.py`
- Versionsprüfung (Lokal vs. Remote)
- MD5-basierte Skript-Synchronisation
- Semantische Versionsvergleiche

#### `monitors.py`
Drei parallele Monitoring-Threads mit v2.1.1 Features:

1. **LogMonitor** – Live-Log-Tailing
   - Zeigt wichtige Events in Echtzeit (Audio/Video Sync Status)
   - Filtert nach Recording-Status mit ffmpeg-Integration
   - Verfolgt Audio/Video Merge-Operationen
   - rpicam-vid Parameter-Verarbeitung (4K, Rotation, Codec)

2. **VideoWatcher** – Video-Synchronisation
   - Scannt Remote-Verzeichnisse auf neue MP4-Dateien
   - Synchronisiert komplette Aufnahmen via rsync
   - Robust gegen fehlende/unvollständige Aufnahmen
   - Wartet auf ffmpeg-Finalisierung vor Transfer

3. **StatusReporter** – Periodische Berichte (5 Minuten)
   - Unified-Monitor-Prozess Status und Thread-Info
   - CPU/RAM/Disk-Nutzung auf Raspberry Pi
   - Letzte 5 Log-Zeilen mit Timestamps

## Python Client vs. Bash (Legacy)

**Die Python-Version ersetzt die alte Bash-basierte `start-unified-monitoring.sh`:**

| Feature | Bash (Legacy) | Python (v2.1.1) |
|---------|------|--------|
| **Log-Parsing** | ❌ Fehleranfällig (Whitespace-Verlust) | ✅ Robustes String-Parsing mit Regex |
| **SSH-Fehlerbehandlung** | ⚠️ Einfache Retries | ✅ Strukturierte Retry-Logik mit Exponential Backoff |
| **Audio/Video Sync Detection** | ❌ Nicht sichtbar | ✅ Zeigt ffmpeg -fflags +genpts Integration |
| **Threading/Parallelisierung** | ⚠️ BGP + Race Conditions | ✅ Sichere Threading mit Locks |
| **Performance** | ⚠️ Viele Subshells | ✅ Direkte Prozess-Verwaltung |
| **Graceful Shutdown** | ❌ Killall (Zombie-Prozesse) | ✅ 3-stufige Cleanup (SIGTERM → Warten → SIGKILL) |
| **Fehler-Debugging** | 😰 Shell-Stack-Traces unlesbar | ✅ Klare Python Exceptions + Logging |
| **Typ-Sicherheit** | ❌ Dynamisch, keine Validierung | ✅ Type-Hints für IDE-Support |
| **rpicam-vid Parameter** | ⚠️ Limited (nur basic Optionen) | ✅ Alle Parameter (4K, Rotation 180°, Codec, etc.) |
| **Video-Transfer** | 🔄 rsync mit einfacher Logik | ✅ rsync mit Completion-Checks |
| **Detect-and-Record** | ❌ Nicht vorhanden | ✅ Zwei-Phasen Mode (Detection → Recording) |
| **remote-unified-control.sh** | 🔄 Legacy Shell-Wrapper | ✅ Vollständige Python-Integration |

## Debugging

### Debug-Mode aktivieren

```python
# In unified_monitor_client.py:
logging.basicConfig(level=logging.DEBUG)  # Statt INFO
```

### SSH-Verbindung testen

```bash
python3 -c "
from ssh_manager import get_ssh_manager
ssh = get_ssh_manager()
if ssh.connect():
    print('✅ SSH-Verbindung OK')
    success, out, _ = ssh.exec_command('uname -a')
    print(f'Remote System: {out}')
else:
    print('❌ SSH-Verbindung fehlgeschlagen')
"
```

### Version-Check testen

```bash
python3 -c "
from version_manager import VersionManager
vm = VersionManager()
print(f'Lokal: v{vm.local_version}')
print(f'Remote: v{vm.get_remote_version()}')
print(f'Update nötig: {not vm.compare_versions()}')
"
```

## Deployment auf Pi

### 1. Kopiere Skript auf Pi

```bash
scp -i ~/.ssh/id_rsa_pi -r unified-monitor-client/ \
  pi_user@raspberry-pi-monitor:/home/pi_user/vogel-kamera-linux/
```

### 2. Installiere Dependencies auf Pi (falls nötig)

```bash
ssh -i ~/.ssh/id_rsa_pi pi_user@raspberry-pi-monitor \
  "cd ~/vogel-kamera-linux/unified-monitor-client && pip install -r requirements.txt"
```

### 3. Starte den Client von deinem Rechner aus

```bash
# Der Python-Client läuft auf DEINEM PC/Laptop, nicht auf dem Pi!
# Er orchestriert nur die Remote-Aufnahme auf dem Pi
cd unified-monitor-client

# Empfohlen: Detect-and-Record mit Schleife
python3 unified_monitor_client.py normal --detect-and-record \
  --threshold 0.4 --duration 30 --repeat

# oder nur kurze Session
python3 unified_monitor_client.py 4k --detect-and-record --duration 30

# oder klassisch Manual
python3 unified_monitor_client.py slowmo --manual-record --duration 60
```

## Migration: Bash → Python (v2.1.1)

**Alte Bash-basierte Methode (gelöscht):**
```bash
./auto-start-kamera/start-unified-monitoring.sh 4k  # ⛔ NICHT MEHR VORHANDEN
```

**Neue Python-basierte Methode (aktiv in v2.1.1):**
```bash
cd unified-monitor-client
# Empfohlen: Mit Detect-and-Record & Schleife
python3 unified_monitor_client.py normal --detect-and-record \
  --threshold 0.4 --duration 30 --repeat

# Oder einfach Manual
python3 unified_monitor_client.py 4k --manual-record --duration 60  # ✅ EMPFOHLEN
```

**Status (v2.1.1):**
- ✅ `unified-monitor-client/` – Aktiv & vollständig
- ✅ `unified-monitor-client/unified_monitor_client.py` – Haupt-Client mit Detect-and-Record
- ✅ `unified-monitor-client/setup_environment.py` – Automatisiertes Setup
- ✅ `unified-monitor-client/diagnose_remote_system.py` – System-Diagnose
- ✅ **Graceful Shutdown (Ctrl+C)** – Saubere Process-Cleanup
- ✅ **Improved Process Management** – 3-stufige Cleanup
- ❌ `auto-start-kamera/start-unified-monitoring.sh` – Gelöscht
- ❌ `auto-start-kamera/remote-unified-control.sh` – Gelöscht (Funktionalität in Python integriert)

## Häufige Fehler

**`SSH-Verbindung fehlgeschlagen`**
```bash
# Prüfe SSH-Key
ls -la ~/.ssh/id_rsa_pi

# Teste manuell
ssh -i ~/.ssh/id_rsa_pi pi_user@raspberry-pi-monitor 'echo OK'

# Prüfe /etc/ssh/ssh_config oder ~/.ssh/config
```

**`ModuleNotFoundError: No module named 'paramiko'`**
```bash
pip install -r unified-monitor-client/requirements.txt
```

**`Monitor-Prozess nicht aktiv`**
```bash
# Prüfe Remote-Logs
ssh -i ~/.ssh/id_rsa_pi pi_user@raspberry-pi-monitor \
  'tail -50 /tmp/unified-camera-monitor.log'

# Prüfe Camera-Fehler
ssh -i ~/.ssh/id_rsa_pi pi_user@raspberry-pi-monitor \
  'dmesg | grep -i camera'
```

## Performance

- **CPU-Last:** ~0-5% während Monitoring
- **RAM-Usage:** ~20-30 MB Python-Prozess
- **Netzwerk:** Minimal (nur Events & neue Videos)
- **Video-Sync:** Nutzt rsync (resumes incomplete transfers)

## Lizenz

Same as parent project (Vogel-Kamera-Linux)

## Technischer Support

### Diagnose-Tools

```bash
# 1. System-Diagnose (Remote-Check)
python3 diagnose_remote_system.py
# → Zeigt Kamera-Status, Audio-Devices, Abhängigkeiten, etc.

# 2. Remote Logs prüfen
ssh -i ~/.ssh/your-ssh-key <your-username>@your-raspberry-pi 'tail -50 /tmp/unified-camera-monitor.log'

# 3. SSH-Verbindung testen
ssh -i ~/.ssh/your-ssh-key <your-username>@your-raspberry-pi 'echo OK && uname -a'

# 4. Kamera & rpicam-vid testen
ssh -i ~/.ssh/your-ssh-key <your-username>@your-raspberry-pi 'rpicam-hello -t 2 --verbose'

# 5. Audio-Devices prüfen
ssh -i ~/.ssh/your-ssh-key <your-username>@your-raspberry-pi 'arecord -l'
```

### Debug-Mode

```bash
# Verbose Output aktivieren
python3 unified_monitor_client.py 4k --verbose

# oder in der Python Shell
import logging
logging.basicConfig(level=logging.DEBUG)
```
