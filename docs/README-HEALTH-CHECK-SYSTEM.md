# 🏥 Health-Check System – Überblick & Dokumentation

## 📚 Dokumentations-Übersicht

Dieses Projekt wurde mit einem **3-Schichten selbstheilenden Restart-System** ausgestattet, um Stuck-Daemons automatisch zu erkennen und zu beheben.

### 📖 Verfügbare Dokumentationen:

| Datei | Zielgruppe | Inhalt |
|-------|-----------|--------|
| **[HEALTHCHECK-CHEATSHEET.md](HEALTHCHECK-CHEATSHEET.md)** | ⚡ Schnell-Referenz | TL;DR, Kommandos, Debugging, Fehlersuche |
| **[HEALTHCHECK-OPTIMIZATION-V2.md](HEALTHCHECK-OPTIMIZATION-V2.md)** | 👨‍💻 Entwickler | Detaillierte Erklärung mit Mermaid-Diagrammen |
| **[HEALTHCHECK-MERMAID.md](HEALTHCHECK-MERMAID.md)** | 📊 Visuell | 7 umfassende Mermaid-Diagramme |
| **[HEALTHCHECK-OPTIMIZATION.md](HEALTHCHECK-OPTIMIZATION.md)** | 📚 Detailliert | Umfassende technische Dokumentation (alt) |

---

## 🎯 Quick Start – Was wurde geändert?

### Drei Ebenen des Restart-Systems:

```
┌─────────────────────────────────────────────────────────┐
│ 🐳 EBENE 1: Docker (schnell, lokal)                    │
│  • Health-Check alle 30 Sekunden                        │
│  • Test: HTTP GET /api/status + JSON valid              │
│  • Aktion: Container Restart (max 5×)                   │
│  • Recovery: ~90-180 Sekunden                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ ⚙️ EBENE 2: Systemd (Fallback, OS-Level)               │
│  • Überwacht docker compose Prozess                     │
│  • Aktion: Service Restart (unlimited, aber mit Limit)  │
│  • Limit: 5 Starts pro 5 Minuten                       │
│  • Recovery: ~30-60 Sekunden                            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 📊 EBENE 3: Health-Monitor (optional, zusätzlich)      │
│  • Unabhängiges Monitoring Script                       │
│  • Prüft Docker Health Status alle 60 Sekunden          │
│  • Logs + optionale externe Alerts (Webhooks)           │
│  • Recovery: sofort wenn Monitor triggered              │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Was wurde optimiert?

| Komponente | **ALT** | **NEU** | **Effekt** |
|-----------|--------|--------|----------|
| Docker Restart | `always` | `on-failure:5` | ✨ Intelligenter, verhindert endlose Schleifen |
| Health-Check Test | HTTP GET `/` | HTTP GET `/api/status` + JSON | ✨ Prüft ob API wirklich funktioniert |
| Health-Check Interval | 30s | 30s (unverändert) | – |
| Health-Check Retries | 3 | 3 (unverändert) | – |
| Systemd Restart | `on-failure` | `always` | ✨ Reagiert auch auf docker compose stuck |
| Systemd Start-Limit | ❌ Keine | ✅ 5 pro 5 Min | ✨ Verhindert Endlosschleifen |
| Monitoring | ❌ Keine | ✅ Optional Monitor | ✨ Zusätzliche Transparenz |

---

## 🔄 Wie funktioniert es praktisch?

### Szenario: Daemon wird stuck nach mehreren Stunden

```
00:00 - Daemon startet, alles OK
02:00 - Daemon wird blockiert (z.B. Hailo-Temp stuck)
        ↓
02:30 - Health-Check #1: FAIL (FailingStreak: 1)
        ↓
03:00 - Health-Check #2: FAIL (FailingStreak: 2)
        ↓
03:30 - Health-Check #3: FAIL (FailingStreak: 3 ≥ 3)
        → Status: unhealthy
        → Docker Restart triggered
        ↓
04:00 - Warte 30 Sekunden
        ↓
04:30 - Container neu gestartet
        Hailo lädt neu
        Detection aktiv
        ↓
05:00 - Health-Check OK
        Status: healthy
        ↓
05:30 - WebUI antwortet wieder
        Videos funktionieren
        
TOTAL RECOVERY: ~180 Sekunden (3 Minuten)
```

---

## 🚀 Installation

Nach Ansible-Run sind alle Dateien automatisch installiert:

```bash
# 1. Systemd neu laden
sudo systemctl daemon-reload

# 2. Service neustarten
sudo systemctl restart pi-daemon

# 3. Status überprüfen
systemctl status pi-daemon
docker inspect pi-daemon --format='{{.State.Health.Status}}'

# 4. Optional: Health-Monitor starten
sudo systemctl enable pi-daemon-healthcheck.service
sudo systemctl start pi-daemon-healthcheck.service
```

---

## 🔍 Wichtige Dateien

### Geändert:
- ✅ **`ansible/roles/pi-daemon/templates/docker-compose.yml.j2`**
  - `restart: on-failure:5`
  - Detaillierte Health-Check Definition
  - Logging Labels

- ✅ **`ansible/roles/pi-daemon/templates/pi-daemon.service.j2`**
  - `Restart: always`
  - StartLimitBurst: 5
  - KillMode: mixed (robustes Shutdown)
  - Logging zu systemd journal

- ✅ **`docker/Dockerfile`**
  - Health-Check verbessert (prüft `/api/status` + JSON)

### Neu erstellt:
- ✨ **`ansible/roles/pi-daemon/templates/health-check-monitor.sh.j2`**
  - Optionales Monitoring-Script
  - Logs + Alerts

- ✨ **`ansible/roles/pi-daemon/templates/pi-daemon-healthcheck.service.j2`**
  - Systemd-Service für Health-Monitor

- 📚 **`docs/HEALTHCHECK-OPTIMIZATION-V2.md`**
  - Dokumentation mit Mermaid-Diagrammen

- 📚 **`docs/HEALTHCHECK-MERMAID.md`**
  - 7 umfassende Mermaid-Diagramme

- ⚡ **`docs/HEALTHCHECK-CHEATSHEET.md`**
  - Schnell-Referenz für tägliche Nutzung

---

## 📊 Mermaid-Diagramme

Das System ist mit **7 verschiedenen Mermaid-Diagrammen** dokumentiert:

1. **Flowchart** – Restart-Flow mit allen Details
2. **State Diagram** – Zustandsübergänge
3. **Sequence Diagram** – Zeitliche Abfolge
4. **Gantt Chart** – Stuck-Szenario Timeline
5. **Architecture** – Komponenten & Beziehungen
6. **Error Scenarios** – Recovery-Strategien
7. **Comparison** – Alt vs. Neu

👉 **Alle Diagramme in:** [HEALTHCHECK-MERMAID.md](HEALTHCHECK-MERMAID.md)

---

## 🎯 Zusammenfassung: Zahlen & Fakten

| Metric | Wert |
|--------|------|
| **Health-Check Interval** | 30 Sekunden |
| **Health-Check Timeout** | 5 Sekunden |
| **Unhealthy Threshold** | 3 Fehler |
| **Zeit bis Status unhealthy** | ~90 Sekunden |
| **Docker Restart Versuche** | Max 5× |
| **Docker Restart Wartezeit** | 30 Sekunden |
| **Systemd Restart Versuche** | Max 5 pro 5 Min |
| **Systemd Restart Wartezeit** | 30 Sekunden |
| **Shutdown Timeout** | 20 Sekunden |
| **Total Recovery Time** | **~180 Sekunden (3 Min)** |

---

## ❓ FAQ

### F: Was ist der Unterschied zwischen Docker und Systemd Restart?
**A:** 
- **Docker** reagiert auf Health-Check Fehler → schnell (90-180s)
- **Systemd** reagiert wenn `docker compose` Prozess beendet → Fallback (~30-60s)
- **Zusammen** = doppelte Sicherheit

### F: Warum `on-failure:5` statt `always`?
**A:** `always` würde auch bei konfigurierten Fehlern (z.B. OOM) endlos neustarten. `on-failure:5` ist intelligenter.

### F: Kann ich das Interval kürzer machen?
**A:** Ja, aber Vorsicht: Kürzere Intervalle = höhere CPU-Last. Empfohlen: 15-30 Sekunden.

### F: Was wenn 5 Restarts in 5 Minuten nicht reichen?
**A:** Das ist ein fundamentaler Fehler → Admin-Intervention nötig. Log prüfen mit `journalctl -u pi-daemon -n 200 | less`

### F: Wie deaktiviere ich das Health-Check System?
**A:** **Nicht empfohlen**, aber:
```yaml
# docker-compose.yml
healthcheck:
  disable: true
```
Dann: `docker-compose up -d`

---

## 🔧 Troubleshooting

### Problem: Health-Check schlägt fehl, aber WebUI lädt
```bash
# Diagnose
curl -k https://localhost:8443/api/status

# Wenn SSL-Fehler:
docker logs pi-daemon | grep -i ssl

# Wenn Timeout:
# → docker-compose.yml: timeout: 10s (erhöhen)
```

### Problem: Container läuft, aber Dashboard antwortet nicht
```bash
# Check Health Status
docker inspect pi-daemon --format='{{.State.Health.Status}}'

# Wenn "unhealthy":
docker restart pi-daemon

# Warten bis "healthy"
watch 'docker inspect pi-daemon --format="{{.State.Health.Status}}"'
```

### Problem: Service in Restart-Schleife
```bash
# StartLimitBurst reset
sudo systemctl reset-failed pi-daemon

# Dann Logs prüfen
journalctl -u pi-daemon -n 100 | grep -i error

# Service neustarten
sudo systemctl start pi-daemon
```

👉 **Vollständiges Debugging:** [HEALTHCHECK-CHEATSHEET.md](HEALTHCHECK-CHEATSHEET.md)

---

## 📞 Support

### Wo findet man was?

**Schnelle Antwort brauchen?**
→ [HEALTHCHECK-CHEATSHEET.md](HEALTHCHECK-CHEATSHEET.md)

**Detaillierte Technische Erklärung?**
→ [HEALTHCHECK-OPTIMIZATION-V2.md](HEALTHCHECK-OPTIMIZATION-V2.md)

**Grafiken/Diagramme ansehen?**
→ [HEALTHCHECK-MERMAID.md](HEALTHCHECK-MERMAID.md)

**Alles im Detail?**
→ [HEALTHCHECK-OPTIMIZATION.md](HEALTHCHECK-OPTIMIZATION.md)

---

## ✨ Ergebnis

Das System ist jetzt **selbstheilend**! 🔧

Wenn der Daemon nach langer Zeit stuck wird:
- ✅ Docker erkennt es automatisch
- ✅ Container wird neu gestartet
- ✅ Hailo-Detection lädt neu
- ✅ Videos funktionieren weiter
- ✅ WebUI aktualisiert sich wieder
- ✅ **Alles in ~3 Minuten, ohne manuelle Intervention**

**Viel Erfolg!** 🐦🎥
