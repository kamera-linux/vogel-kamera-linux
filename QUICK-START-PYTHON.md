# Quick Start - Unified Monitor Client (Python)

**Ersatz für die alte Bash-basierte `start-unified-monitoring.sh`**

## Vorbereitungen (einmalig)

### 1. SSH-Konfiguration erstellen

Das Skript benötigt deine SSH-Zugangsdaten. Diese werden aus einer `.env`-Datei geladen:

```bash
cd unified-monitor-client

# Kopiere die .env.example zu .env
cp .env.example .env

# Editiere .env und füge DEINE SSH-Daten ein:
nano .env
```

Beispiel `.env`:
```bash
SSH_KEY=~/.ssh/id_rsa_ai-had
SSH_USER=roimme
SSH_HOST=raspberrypi-5-ai-had
```

**Wichtig:** `.env` wird **NICHT** in Git versioniert und bleibt lokal bei dir!

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

**Alte Bash-Skripte sind gelöscht!** ✅  
**Status:** Production-Ready (v2.1.0) mit Dual-Architecture  
**Testing:** ✅ AUTO-RECORD (YOLO26) validiert ✅ MANUAL-RECORD (rpicam-vid) validiert

## Verwendung

### 🎯 Zwei Architektur-Modi

Das System hat zwei spezialisierte Backend-Modi - wähle je nach Anwendungsfall:

#### 🔍 **AUTO-RECORD**: Automatische Vogel-Erkennung mit YOLO26n

Für unbeaufsichtigtes, ereignisgesteuertes Monitoring:

```bash
# Standard: Kontinuierlich überwachen, bei Vogel-Erkennung aufnehmen
python3 unified-monitor-client/unified_monitor_client.py normal --auto-record

# Mit erhöhtem Schwellenwert und längerer Aufnahmedauer
python3 unified-monitor-client/unified_monitor_client.py normal --auto-record \
  --threshold 0.7 \
  --trigger-duration 20

# Slowmo-Modus (60fps) mit automatischer Vogel-Erkennung
python3 unified-monitor-client/unified_monitor_client.py slowmo --auto-record
```

**Verfügbare Parameter für AUTO-RECORD:**
- `--threshold` – Erkennungs-Konfidenz (0.0-1.0, Standard: 0.5)
- `--cooldown` – Sekunden zwischen Erkennungen (Standard: 2.0)
- `--trigger-duration` – Aufnahme-Länge pro Erkennung (Standard: 10s)

#### 📹 **MANUAL-RECORD**: Reine Video-Aufnahmen ohne AI-Overhead

Für geplante, gezielte Aufnahme-Sessions:

```bash
# 10 Sekunden Test-Aufnahme
python3 unified-monitor-client/unified_monitor_client.py normal --manual-record --duration 10

# 5 Minuten kontinuierliche Aufnahme
python3 unified-monitor-client/unified_monitor_client.py normal --manual-record --duration 300

# 4K Cinema, 30 Sekunden
python3 unified-monitor-client/unified_monitor_client.py 4k --manual-record --duration 30

# Slowmo (60fps), 2 Minuten
python3 unified-monitor-client/unified_monitor_client.py slowmo --manual-record --duration 120
```

**Verfügbare Parameter für MANUAL-RECORD:**
- `--duration` – Aufnahme-Dauer in Sekunden (Standard: 30)

### Recording-Modi (Bildformat)

```bash
# 1080p @ 30fps (Standard)
python3 unified-monitor-client/unified_monitor_client.py normal --auto-record

# 1536x864 @ 60fps (Zeitlupe)
python3 unified-monitor-client/unified_monitor_client.py slowmo --manual-record --duration 60

# 4096x2160 @ 30fps (Cinema 4K)
python3 unified-monitor-client/unified_monitor_client.py 4k --auto-record

# 1024x576 @ 30fps (Test/Schnell-Check)
python3 unified-monitor-client/unified_monitor_client.py test
```

## Was passiert bei der Ausführung?

1. **SSH-Verbindung** zu Raspberry Pi wird etabliert
2. **System-Check** prüft Versionen und Abhängigkeiten
3. **Remote-Monitor** startet auf dem Pi (Background-Prozess)
4. **Log-Tailing** zeigt Live-Events:
   - AUTO-RECORD: Vogel-Erkennungen (YOLO26n), Trigger-Events, Aufnahme-Start/Stop
   - MANUAL-RECORD: ffmpeg Encoding-Status, rsync Upload-Progress
5. **Video-Watching** überwacht Pi-Verzeichnisse auf neue MP4-Dateien
6. **rsync Transfer** lädt fertige Videos automatisch herunter
7. **Status-Reports** alle 5 Minuten (CPU, RAM, Disk-Nutzung)

Ausgaben sehen so aus:
```
[INFO] SSH-Connection: OK
[INFO] Remote Monitor v2.1.0 startet...
[AUTO EVENT] Vogel erkannt (Conf: 0.82) → Aufnahme startet (20s)
[VIDEO] new_recording_2025_01_15.mp4 (45.2 MB) heruntergeladen
[STATUS] CPU: 58% | RAM: 245MB | Disk: 78%
```

## Ctrl+C zum Stoppen

Das System beendet alle Prozesse sauber:
- Stoppt Remote-Monitor auf dem Pi
- Wartet auf ffmpeg zu finalisieren  
- Synchronisiert letzte Videos herunter
- Schließt SSH-Verbindung

## Troubleshooting

**SSH-Fehler: "Connection refused"**
```bash
# Teste SSH-Verbindung manuell:
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had echo OK

# Überprüfe SSH-Key:
ls -la ~/.ssh/id_rsa_ai-had
```

**"No module named paramiko"**
```bash
# Stelle sicher, dass requirements installiert sind:
pip install -r unified-monitor-client/requirements.txt
```

**Remote-Monitor Logs ansehen**
```bash
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  tail -n 50 /tmp/unified-camera-monitor.log
```

**AUTO-RECORD startet nicht**
```bash
# Überprüfe ob picamera2 auf Pi installiert ist:
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  python3 -c "import picamera2; print('OK')"
```

## Environment-Variablen Setup

Die `.env` Datei wird **automatisch geladen** beim Start:

```bash
# Falls nicht vorhanden, erstellen:
cp unified-monitor-client/.env.example unified-monitor-client/.env

# Konfigurieren mit deinem SSH-Setup:
nano unified-monitor-client/.env

# Bei nächstem Start wird .env automatisch verwendet!
```

`.env` wird **NICHT** in Git versioniert - deine Zugangsdaten bleiben privat! ✅
