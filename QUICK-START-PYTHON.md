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

## Verwendung

### Normal-Modus (1080p @ 30fps)
```bash
python3 unified-monitor-client/unified_monitor_client.py normal
```

### Zeitlupe (1536x864 @ 120fps)
```bash
python3 unified-monitor-client/unified_monitor_client.py slowmo
```

### Cinema 4K (4096x2160 @ 25fps)
```bash
python3 unified-monitor-client/unified_monitor_client.py 4k
```

### AI-HAD mit Audio-Erkennung
```bash
python3 unified-monitor-client/unified_monitor_client.py ai-had
```

### Mit Parametern
```bash
# Kürzerer Cooldown
python3 unified-monitor-client/unified_monitor_client.py slowmo --cooldown 5

# Höherer Threshold
python3 unified-monitor-client/unified_monitor_client.py 4k --threshold 0.7

# Alle Parameter
python3 unified-monitor-client/unified_monitor_client.py ai-had \
  --threshold 0.6 \
  --cooldown 10 \
  --trigger 1.5 \
  --audio-threshold 0.25
```

## Was passiert?

1. **System-Check** (SSH, Versionen, Skripte)
2. **Remote Monitor startet** auf dem Pi
3. **Log-Tailing** zeigt Events in Echtzeit
4. **Video-Watching** synchronisiert Videos automatisch (rsync)
5. **Status-Reporter** gibt Berichte alle 5 Minuten

## Ctrl+C zum Stoppen

Das System stoppt sauber alle Threads und Prozesse.

## Probleme?

**SSH-Fehler: "SSH-Key nicht gefunden"**
```bash
# 1. Stelle sicher, dass die Umgebungsvariablen gesetzt sind:
echo $SSH_KEY $SSH_USER $SSH_HOST

# 2. Teste SSH manuell:
ssh -i $SSH_KEY $SSH_USER@$SSH_HOST 'echo OK'

# 3. Überprüfe ob dein SSH-Key existiert:
ls -la $SSH_KEY
```

**Remote-Monitor Logs**
```bash
ssh -i $SSH_KEY $SSH_USER@$SSH_HOST 'tail -50 /tmp/unified-camera-monitor.log'
```

**Dependencies prüfen**
```bash
pip list | grep -E "paramiko|click"
```

## Umgebungsvariablen (WICHTIG!)

Du **MUSST** diese mit deinen echten SSH-Einstellungen konfigurieren:

Die einfachste Methode ist, die `.env` Datei zu editieren:

```bash
nano unified-monitor-client/.env

# Dann einfach nächstes Mal aufrufen:
python3 unified-monitor-client/unified_monitor_client.py normal
```

Die `.env` Datei wird **automatisch geladen** und deine SSH-Daten sind sicher (nicht in Git)!

---

**Alte Bash-Skripte sind gelöscht!** ✅  
**Status:** Production-Ready
