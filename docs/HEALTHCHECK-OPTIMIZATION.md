# 🏥 Health-Check Optimierung – Robustheit gegen Stuck Daemon

## Übersicht

Das System wurde optimiert, um **automatisch zu erkennen und zu reagieren** wenn der Pi-Daemon "stuck" wird (blockiert/reagiert nicht auf HTTP-Requests).

### Was wurde verbessert?

| Komponente | Alt | Neu | Nutzen |
|-----------|-----|-----|--------|
| **Docker Restart** | `always` | `on-failure:5` | Verhindert Restart wenn Docker-Fehler (z.B. OOM) vorhanden |
| **Health-Check Test** | HTTP GET auf `/` | HTTP GET auf `/api/status` + JSON-Validierung | Prüft ob API wirklich funktioniert, nicht nur HTTP 200 |
| **Health-Check Interval** | 30s | 30s (unverändert) | – |
| **Health-Check Retries** | 3 Versuche | 3 Versuche | – |
| **Systemd Restart** | `on-failure` | `always` | Startet auch wenn `docker compose` stuck ist |
| **Systemd Start-Limit** | Keine | 5 Starts pro 5 Min | Verhindert Endlosschleife bei fundamentalen Fehlern |
| **Monitoring** | Keine | Health-Check Monitor Script (optional) | Logs + zusätzliche Alerts |

---

## 🔄 Wie funktioniert das Restart-System?

### Quick Mermaid Flowchart:

```mermaid
graph TD
    A[("🏥 Health-Check<br/>alle 30 Sekunden")]
    B["HTTP GET<br/>localhost:8443/api/status"]
    C{{"Response OK<br/>+ JSON Valid?"}}
    C_yes["✅ Status: healthy<br/>FailingStreak: 0"]
    C_no["❌ FailingStreak + 1"]
    
    D{{"FailingStreak<br/>≥ 3?"}}
    D_no["Warte 30s<br/>Nächster Check"]
    D_yes["🔴 Status: unhealthy"]
    
    E["🐳 Docker Restart<br/>on-failure:5"]
    F["Container-Restart<br/>versucht"]
    F_count{{"Versuch<br/>≤ 5?"}}
    F_yes["Starte Container neu<br/>+30s Wartezeit"]
    F_no["Docker gibt auf<br/>Systemd übernimmt"]
    
    G["📦 Container startet<br/>Hailo Detection aktiv"]
    G_ok["✅ Health-Check OK<br/>Status: healthy"]
    
    H["⚙️ Systemd Watchdog<br/>Restart: always"]
    H_stuck{{"docker compose<br/>process stuck?"}}
    H_yes["Systemd startet<br/>Service neu"]
    
    I{{"StartLimitBurst<br/>überschritten?<br/>5 pro 5 Min"}}
    I_no["✅ Restart erfolgreich"]
    I_yes["🔴 Service stoppt<br/>⚠️ Manual Recovery"]
    
    J["📊 Optional:<br/>Health-Check Monitor"]
    J_check["Überwacht alle 60s<br/>Docker Health-Status"]
    
    A --> B --> C
    C -->|OK| C_yes --> D
    C -->|Fehler| C_no --> D
    D -->|Nein| D_no --> A
    D -->|Ja| D_yes --> E --> F --> F_count
    F_count -->|Ja| F_yes --> G --> G_ok -->|30s später| A
    F_count -->|Nein| F_no --> H
    
    H --> H_stuck
    H_stuck -->|Nein| I
    H_stuck -->|Ja| H_yes --> I
    I -->|Nein| I_no
    I -->|Ja| I_yes
    
    D_yes -.->|Optional| J --> J_check
    
    style A fill:#90EE90,stroke:#228B22,stroke-width:3px,color:#000
    style D_yes fill:#FFB6C6,stroke:#FF1493,stroke-width:2px,color:#000
    style G_ok fill:#87CEEB,stroke:#4169E1,stroke-width:2px,color:#000
    style I_yes fill:#FF6B6B,stroke:#DC143C,stroke-width:3px,color:#fff
    style J fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000
```

---

## 🎯 Zustandsübergänge (State Diagram)

```mermaid
stateDiagram-v2
    [*] --> Healthy: Container startet<br/>1. Health-Check OK
    
    Healthy --> FailingStreak1: Health-Check<br/>Fehler #1
    FailingStreak1 --> Healthy: Health-Check OK
    
    FailingStreak1 --> FailingStreak2: Health-Check<br/>Fehler #2
    FailingStreak2 --> Healthy: Health-Check OK
    
    FailingStreak2 --> Unhealthy: Health-Check<br/>Fehler #3
    Unhealthy --> ContainerRestarting: Docker Restart<br/>triggered
    Unhealthy --> Healthy: Health-Check OK
    
    ContainerRestarting --> Healthy: Container OK<br/>Health-Check bestanden
    ContainerRestarting --> SystemdRestarting: Docker Restart<br/>max 5× erreicht
    
    SystemdRestarting --> Healthy: Systemd Restart<br/>erfolgreich
    SystemdRestarting --> ManualRecovery: StartLimitBurst<br/>überschritten
    
    ManualRecovery --> [*]: systemctl reset-failed
    
    note right of Healthy
        ✅ System OK
        WebUI antwortet
        Videos funktionieren
    end note
    
    note right of Unhealthy
        🔴 Daemon stuck
        HTTP-Requests scheitern
    end note
    
    note right of ManualRecovery
        ⚠️ Zu viele Neustarts
        Admin-Eingriff
    end note
```

---

## ⏱️ Zeitliche Abfolge (bei Stuck-Daemon)

```mermaid
gantt
    title Health-Check Recovery Timeline
    dateFormat HH:mm:ss
    
    section Normal
    Normalbetrieb           :done, normal, 00:00:00, 02:00:00
    
    section Fehler
    Daemon stuck            :crit, stuck, 02:00:00, 03:00:00
    Health-Check #1 FAIL    :active, hc1, 02:00:00, 02:00:05
    Health-Check #2 FAIL    :active, hc2, 02:00:30, 02:00:35
    Health-Check #3 FAIL    :active, hc3, 02:01:00, 02:01:05
    Status unhealthy        :crit, unhealthy, 02:01:05, 02:02:00
    
    section Docker Restart
    Docker Restart Trigger  :restart, restart1, 02:02:00, 02:02:30
    Warte 30s               :crit, wait, 02:02:30, 02:03:00
    Container Restart       :restart, restart2, 02:03:00, 02:03:30
    Container Startup       :active, startup, 02:03:30, 02:03:45
    Health-Check OK         :ok, hc_ok, 02:03:45, 02:03:50
    
    section Recovery
    Status healthy          :ok, healthy, 02:03:50, 04:00:00
    WebUI antwortet         :ok, webui, 02:03:50, 04:00:00
    
    section Milestones
    🔴 Stuck                :crit, milestone, m1, 02:00:00, 1m
    ⚠️ Unhealthy            :crit, milestone, m2, 02:01:05, 1m
    🔄 Restart              :milestone, m3, 02:02:00, 1m
    ✅ Recovered            :ok, milestone, m4, 02:03:50, 1m
```

**Total Recovery: ~180 Sekunden** ohne manuelle Aktion!

---

## 🏗️ Komponenten-Architektur

```mermaid
graph LR
    subgraph Docker["🐳 Docker Layer"]
        HC["Health-Check<br/>alle 30s"]
        HCTEST["HTTP GET<br/>/api/status<br/>JSON Valid"]
        RESTART["Restart:<br/>on-failure:5<br/>max 5×"]
    end
    
    subgraph Container["📦 Pi-Daemon Container"]
        PY["Python Daemon<br/>Flask API"]
        HAILO["Hailo-Detection<br/>rpicam-hello"]
        VIDEO["Video Recording<br/>rpicam-vid"]
    end
    
    subgraph Systemd["⚙️ Systemd Layer"]
        SERVICE["pi-daemon.service<br/>Restart: always"]
        LIMIT["StartLimitBurst<br/>5 pro 5 Min"]
        WATCHDOG["docker compose<br/>Watchdog"]
    end
    
    subgraph Optional["📊 Optional"]
        MONITOR["health-check-monitor.sh"]
        LOGS["/var/log/<br/>pi-daemon-health.log"]
    end
    
    Client["👤 Web Browser<br/>Client"]
    
    HC --> HCTEST
    HCTEST -->|OK| PY
    HCTEST -->|Fehler| RESTART
    
    RESTART --> Container
    Container --> PY
    PY --> HAILO
    HAILO --> VIDEO
    
    PY -->|HTTPS 8443| Client
    
    SERVICE --> RESTART
    LIMIT --> SERVICE
    WATCHDOG --> SERVICE
    
    MONITOR -.->|Überwacht| HC
    MONITOR --> LOGS
    
    style Docker fill:#2E90E6,color:#fff,stroke-width:2px
    style Container fill:#50C878,color:#fff,stroke-width:2px
    style Systemd fill:#FF6B6B,color:#fff,stroke-width:2px
    style Optional fill:#FFE4B5,color:#000,stroke-width:2px
    style Client fill:#87CEEB,color:#000,stroke-width:2px
```

---

## 🚨 Fehler-Szenaricos

```mermaid
flowchart TD
    S1["❌ Szenario 1:<br/>Daemon stuck nach Stunden"]
    S1_R["Recovery:<br/>Docker Restart<br/>~180 Sekunden"]
    S1_OUT["✅ WebUI antwortet<br/>Videos funktionieren"]
    
    S2["❌ Szenario 2:<br/>Container crasht"]
    S2_R["Recovery:<br/>Systemd Restart<br/>~30 Sekunden"]
    S2_OUT["✅ Service läuft<br/>Alles normal"]
    
    S3["❌ Szenario 3:<br/>Restart-Schleife"]
    S3_R["Recovery:<br/>Manual Intervention<br/>systemctl reset-failed"]
    S3_OUT["✅ Service läuft<br/>Logs prüfen"]
    
    S4["❌ Szenario 4:<br/>Hailo-Hardware defekt"]
    S4_R["Recovery:<br/>Camera-Reset<br/>oder Pi-Reboot"]
    S4_OUT["⚠️ Hardware-Fehler<br/>Admin nötig"]
    
    S1 --> S1_R --> S1_OUT
    S2 --> S2_R --> S2_OUT
    S3 --> S3_R --> S3_OUT
    S4 --> S4_R --> S4_OUT
    
    style S1 fill:#FFB6C6,stroke:#FF1493
    style S2 fill:#FFB6C6,stroke:#FF1493
    style S3 fill:#FF6B6B,stroke:#DC143C,color:#fff
    style S4 fill:#FF4500,stroke:#8B0000,color:#fff
    
    style S1_OUT fill:#90EE90,stroke:#228B22
    style S2_OUT fill:#90EE90,stroke:#228B22
    style S3_OUT fill:#FFE4B5,stroke:#FF8C00
    style S4_OUT fill:#FF6B6B,stroke:#DC143C,color:#fff
```

---

## 📊 Restart-Strategien: Alt vs. Neu

```mermaid
graph TD
    subgraph Old["❌ Alt: restart: always (no limits)"]
        O1["Startet immer neu<br/>egal bei OOM, Config-Fehler"]
        O2["Keine Limits<br/>Endlosschleife möglich"]
        O3["Systemd: only on-failure<br/>Stuck Daemon bleibt stuck"]
        O4["Resultat: Unzuverlässig"]
    end
    
    subgraph New["✅ Neu: 3-Schichten System"]
        N1["Layer 1: Docker<br/>on-failure:5<br/>Health-Check basiert"]
        N2["Layer 2: Systemd<br/>always<br/>+ StartLimitBurst"]
        N3["Layer 3: Optional<br/>Health-Monitor<br/>zusätzliche Alerts"]
        N4["Resultat: Auto-Recovery<br/>in 2-3 Minuten"]
    end
    
    Old -->|verbessert zu| New
    
    style Old fill:#FF6B6B,color:#fff,stroke:#DC143C,stroke-width:3px
    style New fill:#50C878,color:#fff,stroke:#228B22,stroke-width:3px
    style N4 fill:#90EE90,color:#000,stroke-width:2px
```

---

## 📋 Deployment

Alle Dateien werden von Ansible automatisch installiert:

```bash
# Template → Actual File
docker-compose.yml.j2      → /opt/pi-daemon/docker-compose.yml
pi-daemon.service.j2       → /etc/systemd/system/pi-daemon.service
health-check-monitor.sh.j2 → /usr/local/bin/health-check-monitor.sh (optional)
pi-daemon-healthcheck.service.j2 → /etc/systemd/system/pi-daemon-healthcheck.service (optional)
```

**Nach der Installation:**

```bash
# Systemd neu laden
sudo systemctl daemon-reload

# Services neu starten
sudo systemctl restart pi-daemon

# Optional: Health-Check Monitor starten
sudo systemctl start pi-daemon-healthcheck
sudo systemctl enable pi-daemon-healthcheck
```

---

## 🔍 Monitoring & Debugging

### Status prüfen

```bash
# Docker Health-Status
docker inspect pi-daemon --format='{{json .State.Health}}'

# Systemd Service Status
systemctl status pi-daemon

# Logs anschauen
journalctl -u pi-daemon -f                          # Live
journalctl -u pi-daemon -n 100                      # Letzte 100
tail -f /var/log/pi-daemon-health.log               # Health-Monitor
```

### Health-Check manuell testen

```bash
docker exec pi-daemon python3 -c "
import urllib.request, ssl, sys, json
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    resp = urllib.request.urlopen('https://localhost:8443/api/status', context=ctx, timeout=4)
    data = json.loads(resp.read())
    print('✅ Health-Check OK:', data.get('version'))
except Exception as e:
    print('❌ Health-Check FEHLER:', e)
    sys.exit(1)
"
```

---

## 🎯 Zusammenfassung

| Komponente | Verhalten |
|-----------|-----------|
| **Health-Check** | Alle 30s, HTTP GET auf `/api/status` |
| **Docker Restart** | Nach 3× unhealthy (90s), max 5 Versuche |
| **Systemd Restart** | Immer, wenn Service beendet |
| **Restart-Pause** | 30s zwischen Versuchen |
| **Start-Limit** | Max 5 Starts pro 5 Min |
| **Recovery Time** | **~180 Sekunden** ohne manuelle Intervention |

**System ist jetzt selbstheilend!** ✅
