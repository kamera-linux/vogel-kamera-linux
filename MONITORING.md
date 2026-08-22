# 📊 Pi-Daemon Health Monitoring

Container läuft stabil. Diese Dokumentation zeigt wie du regelmäßig den Status prüfst.

---

## ✅ Status quo (22. August 2026)

**Deployed Features:**
- ✅ Thread-Monitoring Daemon
- ✅ Health-Cache (nie blockierend)
- ✅ Optimierte Timeouts (60s interval, 10s timeout)
- ✅ Automatic Recovery bei Fehlern
- ⏸️ Gotify-Alerting (Code vorhanden, später aktivierbar)

**Container Status:**
- Container: healthy
- Health-Checks: alle erfolgreich
- Failing-Streak: 0
- Uptime: stabil

---

## 🔍 Schnelle Status-Checks

### **Terminal - Live Check**
```bash
# Schnell prüfen:
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "docker inspect pi-daemon --format='Health: {{.State.Health.Status}} | State: {{.State.Status}} | Streak: {{.State.Health.FailingStreak}}'"
```

### **API Health-Endpoint**
```bash
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "curl -sk https://localhost:8443/api/health | python3 -m json.tool"
```

Beispiel-Response:
```json
{
  "cached_at": 2557.265686883,
  "status": "ok",
  "system": {
    "disk_free_gb": 294.6,
    "mem_total_mb": 8062,
    "mem_used_mb": 513
  },
  "threads_active": 5,
  "version": "2.3.8"
}
```

---

## 🤖 Automated Monitoring

### **Option A: Bash-Script (täglich manuell)**

```bash
# Mach das Script ausführbar:
chmod +x check_health.sh

# Manuell ausführen:
./check_health.sh

# Oder in Cron: jede 5 Minuten
# crontab -e
# */5 * * * * /path/to/check_health.sh
```

Logs werden in `~/.pi-daemon-monitor.log` gespeichert.

### **Option B: Systemd Timer (automatisch)**

**Datei:** `/etc/systemd/system/pi-daemon-monitor.service`

```ini
[Unit]
Description=Pi-Daemon Health Monitor
After=network-online.target

[Service]
Type=oneshot
User=$USER
ExecStart=/home/imme/vogel-kamera-linux/check_health.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Datei:** `/etc/systemd/system/pi-daemon-monitor.timer`

```ini
[Unit]
Description=Pi-Daemon Health Monitor Timer
Requires=pi-daemon-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=1s

[Install]
WantedBy=timers.target
```

**Aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pi-daemon-monitor.timer

# Status prüfen:
sudo systemctl status pi-daemon-monitor.timer
sudo journalctl -u pi-daemon-monitor -f  # Live logs
```

---

## 📝 Health-History Log (auf Raspi)

```bash
# Alle Health-Events von heute:
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "tail -100 /var/log/pi-daemon/health_history.json | python3 -m json.tool | grep -E '(timestamp|status|reason)' | head -50"

# Unhealthy-Events filtern:
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "python3 << 'PYTHON_EOF'
import json
with open('/var/log/pi-daemon/health_history.json', 'r') as f:
    events = json.load(f)
unhealthy = [e for e in events if e.get('status') in ['unhealthy', 'exited', 'stopped']]
for e in unhealthy[-10:]:  # Letzten 10
    print(f\"{e.get('timestamp', '')}: {e.get('status')} - {e.get('details', {}).get('reason', '')}\")
PYTHON_EOF"
```

---

## 🚨 Wenn Container unhealthy wird

### **Schritt 1: Sofort Info sammeln**
```bash
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had

# Container Status
docker inspect pi-daemon --format='{{json .State.Health}}' | python3 -m json.tool

# Letzte Logs
docker logs pi-daemon --tail 50

# System Status
docker exec pi-daemon python3 -c "import psutil; print(f'Mem: {psutil.virtual_memory()}'); print(f'Disk: {psutil.disk_usage(\"/\")}')"

# Thread-Dump (falls Deadlock)
docker exec pi-daemon kill -USR1 1
docker logs pi-daemon --tail 100 | grep -A 20 "Thread-Status"
```

### **Schritt 2: Automatischer Recovery**
```bash
# Container neu starten:
docker restart pi-daemon

# System neu starten (falls nötig):
sudo systemctl restart pi-daemon
```

---

## 🎯 Monitoring-Checkliste

**Täglich (manuell oder automatisch):**
- [ ] Health-Status prüfen (sollte: `healthy`)
- [ ] FailingStreak sollte: `0` sein
- [ ] Letzte Logs prüfen (keine ERROR-Meldungen)

**Wöchentlich:**
- [ ] Health-History-Log prüfen (`/var/log/pi-daemon/health_history.json`)
- [ ] Container-Uptime prüfen (`docker ps`)
- [ ] Disk-Platz prüfen (Video-Verzeichnis wächst!)

**Monatlich:**
- [ ] Log-Rotation prüfen
- [ ] Health-Cache-Performance checken

---

## 🔮 Zukünftig: Gotify Alerts

Wenn Docker-Registry wieder funktioniert:

```bash
# Gotify auf Raspi starten
docker run -d -p 8081:80 -v /home/roimme/gotify/data:/app/data gotify/gotify-server:latest

# Dann in docker-compose.yml:
GOTIFY_URL=http://192.168.178.75:8081
GOTIFY_TOKEN=<API-Token>

# Deploy:
cd ansible && bash build_and_deploy.sh --update
```

Gotify-Code ist bereits in `pi_daemon_secure.py` vorhanden, einfach nur deaktiviert.

---

## 📊 Logs im Überblick

| Log-Datei | Ort | Inhalt |
|-----------|-----|--------|
| **Container Logs** | `docker logs pi-daemon` | Flask-App Logs |
| **Health-History** | `/var/log/pi-daemon/health_history.json` | Alle Health-Check Events (JSON) |
| **Monitor Script** | `~/.pi-daemon-monitor.log` | Check-Script Ausgabe |
| **systemd Journal** | `journalctl -u pi-daemon` | systemd-Service Logs |
| **Health-Alerts** | `/var/log/pi-daemon/health_alerts.log` | Nur Fehler (wenn Alerting aktiv) |

---

## 💡 Tips

- **Log-Größe explodiert?** → Health-History rotatieren:
  ```bash
  ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
    "sudo logrotate -f /etc/logrotate.d/pi-daemon"
  ```

- **Container hängt?** → Stack-Dump anfordern:
  ```bash
  ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
    "docker exec pi-daemon kill -USR1 1 && sleep 2 && docker logs pi-daemon | tail -50"
  ```

- **Health-Checks debuggen?** → Timeout erhöhen:
  ```yaml
  # In docker-compose.yml:
  healthcheck:
    timeout: 15s  # von 10s erhöht
  ```

---

**Stand:** 22. August 2026
**Container:** Stabil & Healthy
**Nächstes Review:** Bei Bedarf oder Fehlern
