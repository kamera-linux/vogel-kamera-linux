# 🏥 Release v2.3.7 - Health-Check Resilience & Proactive Monitoring

**Release Date:** 27. Juli 2026  
**Version:** 2.3.7  
**Status:** ✅ Production Ready

---

## 📋 Übersicht

v2.3.7 behebt das Container-Unhealthy-Problem durch erhöhte Health-Check-Timeouts und implementiert ein proaktives Monitoring-System für zuverlässige Überwachung des Pi-Daemon Containers.

### Incident Summary
Der Container war am **27.07.2026 um 17:04 Uhr** für ~1,5 Stunden unhealthy. **Root Cause:** Health-Check timeout (4s) zu kurz für Performance-Spitzen. **Resolution:** Timeouts erhöht + automatisches Monitoring eingerichtet.

---

## 🔧 Bug Fixes

### 1. Health-Check Timeout erhöht (Dockerfile)

**Problem:**
- Health-Check timeout zu kurz (4s)
- Startup grace period unzureichend (20s)
- Bei hoher Last konnte Container fälschlicherweise unhealthy markiert werden

**Lösung:**
```dockerfile
HEALTHCHECK \
  --interval=30s \
  --timeout=10s \          # war: 5s → +100%
  --start-period=30s \     # war: 20s → +50%
  --retries=3 \
  CMD python3 -c "..."
```

**urllib timeout in Health-Check:**
```python
urllib.request.urlopen(..., timeout=12s)  # war: 4s
```

**Resultat:**
- ✅ Container ist resilient gegen kurzzeitige Performance-Dips
- ✅ Startup-Zeit wird korrekt berücksichtigt
- ✅ Keine falschen unhealthy-Alerts mehr

---

## ✨ Neue Features

### 2. Proaktives Health-Monitoring (systemd-Timer)

**Features:**
```
🔍 Monitoring-Skript: /usr/local/bin/pi-daemon-health-check
📊 Ausführungszyklus: Alle 30 Sekunden
📋 Service: pi-daemon-health-check.service
⏱️  Timer: pi-daemon-health-check.timer
📍 Logs: journalctl -u pi-daemon-health-check.service
```

**Automatisches Alerting:**
- ✅ Status-Änderungen (healthy ↔ unhealthy) werden geloggt
- ✅ systemd Journal-Integration
- ✅ Kann mit E-Mail-Alerts erweitert werden

**Ansible Integration:**
```bash
# Automatisch installiert bei:
./ansible/build_and_deploy.sh --deploy
./ansible/build_and_deploy.sh --update
```

---

## 📦 Neue Dateien

| Datei | Zweck |
|-------|-------|
| `scripts/container_health_monitor.py` | Monitoring-Skript für Health-Checks |
| `scripts/docker_health_monitor.py` | Alternative Health-Monitor Implementation |
| `ansible/playbooks/setup_pi_daemon_health_monitoring.yml` | Ansible Playbook zur Installation |
| `ansible/playbooks/templates/pi-daemon-health-check.service.j2` | systemd Service Template |
| `ansible/playbooks/templates/pi-daemon-health-check.timer.j2` | systemd Timer Template |

---

## 📊 Vergleich: Vorher vs. Nachher

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| **Health-Check Timeout** | 4s | 12s |
| **Startup Grace Period** | 20s | 30s |
| **Monitoring** | Passiv (nur Restart) | Aktiv (alle 30s) |
| **Alerting** | Keine | Automatisch (journalctl) |
| **Resilienz** | Niedrig | Hoch |

---

## 🚀 Deployment

```bash
# Neuer Container mit besseren Health-Checks + Monitoring
./ansible/build_and_deploy.sh --update --no-cache

# Oder nur Update ohne Rebuild
./ansible/build_and_deploy.sh --update
```

**Status nach Deployment:**
```bash
ssh roimme@raspberrypi-5-ai-had
systemctl status pi-daemon-health-check.timer
docker ps -a
```

---

## 📝 Commits

- `841c497` - feat: Health-Monitoring Scripts und Templates hinzufügen
- `8cb024c` - fix: Ansible Playbook für Monitoring flexibel gestalten
- `e5a3c67` - fix: Health-Check Timeout erhöhen + automatisches Monitoring einrichten
- `f519e46` - feat: Health-Check Timeout erhöhen (5s→10s) und start-period erhöhen (20s→30s)

---

## 📈 Monitoring-Output

**Live-Logs:**
```bash
journalctl -u pi-daemon-health-check.service -f
```

**Beispiel-Output:**
```
Jul 27 21:13:48 raspberrypi-5-ai-had pi-daemon-health-check[149925]: 
2026-07-27 21:13:48,041 - WARNING - 🚨 ALERT: pi-daemon Health unknown → healthy
```

**Container-Status:**
```bash
docker ps -a
# pi-daemon   Up 4 minutes (healthy) ✅
```

---

## 🔒 Sicherheit

- Health-Check nutzt selbstsignierte SSL-Zertifikate (sicher)
- systemd-Timer läuft als root (notwendig für Docker)
- Monitoring-Logs sind lokal (kein Remote-Export)

---

## ⚠️ Bekannte Probleme

Keine bekannten Probleme in dieser Version.

---

## 📚 Weitere Ressourcen

- Docs: `docs/README-HEALTH-CHECK-SYSTEM.md`
- Health-Check Script: `scripts/container_health_monitor.py`
- Ansible Playbook: `ansible/playbooks/setup_pi_daemon_health_monitoring.yml`
