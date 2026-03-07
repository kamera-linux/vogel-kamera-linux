# Unified Monitor Client (Python)

**Python-Replacement** für die alte Bash-basierte `start-unified-monitoring.sh`. Vollständige Orchestrierung der Vogel-Kamera-Überwachung ohne Shell-Parsing-Fehler.

## Features

✅ **SSH-Management** mit Retry-Logik (paramiko)  
✅ **Automatische Versionskontrolle** & Remote-Skript-Sync  
✅ **Robustes Log-Tailing** (keine grep-Fehler!)  
✅ **Video-Watching & Sync** mit rsync  
✅ **Status-Reporting** (5-minütige Berichte)  
✅ **CLI-Interface** mit Click (typsicher)  
✅ **Threading** für gleichzeitige Operationen  
✅ **Strukturiertes Logging** (Farben & Timestamps)  

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
SSH_KEY=~/.ssh/id_rsa_ai-had
SSH_USER=roimme
SSH_HOST=raspberrypi-5-ai-had
```

**Sicherheit:**
- `.env` wird **NICHT** in Git versioniert (siehe `.gitignore`)
- Deine SSH-Daten bleiben lokal auf deinem Rechner
- Nur `.env.example` wird geteilt (als Vorlage)

## Verwendung

### Grundlegende Befehle

```bash
# Standard-Modus (1920x1080 @ 30fps + Audio)
./unified_monitor_client.py normal

# Zeitlupe-Modus (1536x864 @ 120fps)
./unified_monitor_client.py slowmo

# Cinema 4K (4096x2160 @ 25fps + Audio)
./unified_monitor_client.py 4k

# AI-HAD mit Audio-Erkennung (1920x1080 @ 30fps)
./unified_monitor_client.py ai-had
```

### Mit Parametern

```bash
# Kürzerer Cooldown zwischen Aufnahmen
./unified_monitor_client.py slowmo --cooldown 5

# Höherer Erkennungs-Schwellenwert
./unified_monitor_client.py 4k --threshold 0.7

# Audio-Erkennung mit niedrigerem Schwellenwert
./unified_monitor_client.py ai-had --audio-threshold 0.2

# Alle Parameter kombiniert
./unified_monitor_client.py ai-had \
  --threshold 0.6 \
  --cooldown 10 \
  --trigger 1.5 \
  --audio-threshold 0.25
```

### Hilfe anzeigen

```bash
./unified_monitor_client.py --help
```

## Architektur

```
unified-monitor-client/
├── unified_monitor_client.py    # Hauptskript (CLI-Interface)
├── config.py                    # Konfiguration & Konstanten
├── ssh_manager.py              # SSH-Wrapper mit paramiko
├── version_manager.py          # Version-Control & Skript-Sync
├── monitors.py                 # Log-Tailing, Video-Watching, Status-Reporting
├── requirements.txt            # Python-Abhängigkeiten
├── VERSION                     # Versionsnummer (v2.1.0)
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
Drei parallele Monitoring-Threads:

1. **LogMonitor** – Live-Log-Tailing
   - Zeigt wichtige Events in Echtzeit
   - Filtert nach Recording-Status
   - Verfolgt Video-Konvertierungen

2. **VideoWatcher** – Video-Synchronisation
   - Scannt Remote-Verzeichnisse
   - Synchronisiert neue Videos via rsync
   - Robust gegen fehlende/unvollständige Aufnahmen

3. **StatusReporter** – Periodische Berichte
   - Monitor-Prozess Status
   - CPU/RAM/Disk-Nutzung
   - Letzte Log-Zeilen

## Unterschiede zu Bash-Version

| Feature | Bash | Python |
|---------|------|--------|
| **grep-Parsing** | ❌ Fehleranfällig (Whitespace/Newlines) | ✅ Robustes String-Parsing |
| **SSH-Fehlerbehandlung** | ⚠️ Einfache Retries | ✅ Strukturierte Retry-Logik |
| **Versionsvergleich** | 🔄 Shell-basiert | ✅ Semantisch korrekt |
| **Threading** | 🔄 BGP + race conditions | ✅ Thread-sicher mit `threading` |
| **Performance** | ⚠️ Viele Subshells | ✅ Direkte Ausführung |
| **Fehler-Debugging** | 😰 Shell-Traces schwer zu lesen | ✅ Strukturiertes Logging |
| **Typ-Sicherheit** | ❌ Keine | ✅ Python Type-Hints |

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

### 3. Führe direkt vom Client aus

```bash
# Der Python-Client läuft auf DEINEM Rechner, nicht auf dem Pi!
# Es orchestriert nur den Remote-Monitor
python3 unified-monitor-client/unified_monitor_client.py 4k
```

## Migration von Bash zu Python

### Alte Struktur (deprecated)
```bash
./auto-start-kamera/start-unified-monitoring.sh 4k
```

### Neue Struktur (aktiv)
```bash
./unified-monitor-client/unified_monitor_client.py 4k
```

**Nach Validierung:**
- `auto-start-kamera/start-unified-monitoring.sh` – Löschen
- `auto-start-kamera/remote-unified-control.sh` – Löschen
- Bash-Helper-Scripts – Löschen

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

1. Prüfe Logs: `tail -100 /tmp/unified-camera-monitor.log`
2. Aktiviere Debug-Mode: `logging.basicConfig(level=logging.DEBUG)`
3. Teste SSH manuell: `ssh pi_user@raspberry-pi-monitor 'echo OK'`
4. Prüfe Kamera: `ssh pi_user@raspberry-pi-monitor 'libcamera-hello'`
