# 🏥 Health-Check System – Mermaid Diagramme

## 1️⃣ Restart-System Flowchart

```mermaid
flowchart TD
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

## 2️⃣ Zustandsübergänge (State Machine)

```mermaid
stateDiagram-v2
    [*] --> Healthy: Container startet<br/>1. Health-Check OK
    
    Healthy --> FailingStreak1: Health-Check<br/>Fehler #1
    
    FailingStreak1 --> FailingStreak2: Health-Check<br/>Fehler #2
    FailingStreak1 --> Healthy: Health-Check OK
    
    FailingStreak2 --> Unhealthy: Health-Check<br/>Fehler #3
    FailingStreak2 --> Healthy: Health-Check OK
    
    Unhealthy --> ContainerRestarting: Docker Restart<br/>on-failure:5<br/>triggered
    Unhealthy --> Healthy: Health-Check OK
    
    ContainerRestarting --> Healthy: Container hochgefahren<br/>Health-Check OK
    ContainerRestarting --> SystemdRestarting: Docker Restart<br/>Max 5× erreicht<br/>Prozess beendet
    
    SystemdRestarting --> Healthy: Systemd Restart<br/>erfolgreich
    SystemdRestarting --> ManualRecovery: StartLimitBurst<br/>überschritten<br/>5 pro 5 Min
    
    ManualRecovery --> [*]: systemctl reset-failed<br/>+ systemctl start
    
    note right of Healthy
        ✅ Alles OK
        WebUI antwortet
        Videos funktionieren
    end note
    
    note right of Unhealthy
        🔴 Daemon stuck
        Health-Check fehlgeschlagen
    end note
    
    note right of ContainerRestarting
        ↻ Docker versucht
        Neustart (max 5×)
    end note
    
    note right of SystemdRestarting
        ⚙️ Systemd versucht
        Neustart (unbegrenzt)
    end note
    
    note right of ManualRecovery
        ⚠️ Zu viele Fehler
        Admin-Eingriff nötig
    end note
```

---

## 3️⃣ Zeitliche Abfolge (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User as Benutzer
    participant Docker as Docker Daemon
    participant Container as Pi-Daemon Container
    participant Hailo as Hailo-Detection
    participant WebUI as Web Dashboard
    participant Systemd as Systemd Service
    
    rect rgb(200, 255, 200)
    Note over Docker,WebUI: ✅ Normalbetrieb (Stunden später...)
    Docker->>Container: Health-Check (30s Interval)
    Container->>Docker: HTTP 200 OK + JSON
    Docker->>Docker: Status: healthy ✅
    end
    
    rect rgb(255, 200, 200)
    Note over Container,Hailo: ❌ Daemon wird stuck<br/>(z.B. Hailo-Temp blockiert)
    Container->>Container: Blockiert auf /dev/hailo0
    Docker->>Container: Health-Check #1 (30s)
    Container-xContainer: Timeout - keine Response
    Docker->>Docker: FailingStreak: 1
    end
    
    rect rgb(255, 200, 200)
    Note over Docker,WebUI: ⚠️ Health-Checks fehlgeschlagen
    Docker->>Container: Health-Check #2 (30s)
    Container-xDocker: TIMEOUT (5s)
    Docker->>Docker: FailingStreak: 2
    Docker->>Container: Health-Check #3 (30s)
    Container-xDocker: TIMEOUT (5s)
    Docker->>Docker: FailingStreak: 3 ≥ 3<br/>Status: unhealthy 🔴
    end
    
    rect rgb(255, 180, 150)
    Note over Docker,Container: 🐳 Docker Restart triggered
    Docker->>Docker: Restart: on-failure:5
    Docker->>Container: Sende SIGTERM
    Container->>Container: Cleanup...
    Container->>Docker: Container beendet
    Docker->>Docker: Warte 30 Sekunden
    Docker->>Container: Starte Container neu
    Container->>Hailo: Initialisiere Hailo
    Hailo->>Container: OK, Detection aktiv
    Container->>Docker: Port 8443 available
    end
    
    rect rgb(180, 220, 180)
    Note over Docker,WebUI: ✅ Recovery erfolgreich
    Docker->>Container: Health-Check OK
    Docker->>Docker: Status: healthy ✅
    Docker->>WebUI: Kann wieder /api/status abrufen
    WebUI->>User: Dashboard aktualisiert sich
    User->>WebUI: Kann wieder Videos starten
    end
    
    rect rgb(200, 200, 255)
    Note over Systemd,Docker: ⚙️ Systemd Watchdog Failsafe
    Note over Systemd,Docker: Falls docker compose stuck ist:<br/>ExecStop/ExecStart triggert Systemd
    Systemd->>Docker: docker compose down
    Systemd->>Docker: docker compose up
    end
```

---

## 4️⃣ Stuck-Scenario Zeitplan

```mermaid
gantt
    title Health-Check Restart Timeline (Stuck Daemon Szenario)
    dateFormat HH:mm:ss
    
    section Normal
    Normalbetrieb           :crit, normal1, 00:00:00, 02:00:00
    
    section Fehler
    Daemon stuck            :crit, stuck1, 02:00:00, 03:00:00
    Health-Check #1 FAIL    :active, hc1, 02:00:00, 02:00:05
    Health-Check #2 FAIL    :active, hc2, 02:00:30, 02:00:35
    Health-Check #3 FAIL    :active, hc3, 02:01:00, 02:01:05
    Status unhealthy        :crit, unhealthy, 02:01:05, 02:02:00
    
    section Docker Restart
    Docker Restart Trigger  :restart1, 02:02:00, 02:02:30
    Warte 30s               :crit, wait1, 02:02:30, 02:03:00
    Container Neustart      :restart1, 02:03:00, 02:03:30
    Container-Startup       :active, startup, 02:03:30, 02:03:45
    Health-Check OK         :ok, hc_ok, 02:03:45, 02:03:50
    
    section Recovery
    Status healthy          :ok, healthy, 02:03:50, 04:00:00
    WebUI antwortet        :ok, webui, 02:03:50, 04:00:00
    
    section Timeline
    🔴 T+0s: Stuck        :milestone, m1, 02:00:00, 0m
    ⚠️ T+90s: Unhealthy    :milestone, m2, 02:01:30, 0m
    🔄 T+120s: Restart     :milestone, m3, 02:02:00, 0m
    ✅ T+180s: Recovered   :milestone, m4, 02:03:00, 0m
```

---

## 5️⃣ Komponenten-Architektur

```mermaid
graph LR
    subgraph Docker["🐳 Docker"]
        HC["Health-Check<br/>alle 30s"]
        HCTEST["HTTP GET /api/status<br/>JSON Validierung"]
        RESTART["Restart: on-failure:5<br/>max 5 Versuche"]
    end
    
    subgraph Container["📦 Container (pi-daemon)"]
        PY["Python Daemon<br/>Flask API"]
        HAILO["Hailo Detection<br/>rpicam-hello"]
        VIDEO["Video Recording<br/>rpicam-vid"]
    end
    
    subgraph Systemd["⚙️ Systemd"]
        SERVICE["pi-daemon.service<br/>Restart: always"]
        LIMIT["StartLimitBurst: 5<br/>pro 5 Minuten"]
        WATCHDOG["Überwacht<br/>docker compose"]
    end
    
    subgraph Optional["📊 Optional"]
        MONITOR["health-check-monitor.sh<br/>systemd Service"]
        LOGS["Logs + Alerts<br/>/var/log/pi-daemon-health.log"]
    end
    
    Client["👤 Client<br/>Web Browser"]
    
    HC --> HCTEST
    HCTEST -->|OK| PY
    HCTEST -->|Fehler| RESTART
    
    RESTART --> Container
    Container --> PY
    PY --> HAILO
    HAILO --> VIDEO
    
    PY -->|HTTP 8443| Client
    
    SERVICE --> RESTART
    LIMIT --> SERVICE
    WATCHDOG --> SERVICE
    
    MONITOR -.->|Prüft| HC
    MONITOR --> LOGS
    
    style Docker fill:#2E90E6,color:#fff
    style Container fill:#50C878,color:#fff
    style Systemd fill:#FF6B6B,color:#fff
    style Optional fill:#FFE4B5,color:#000
    style Client fill:#87CEEB,color:#000
```

---

## 6️⃣ Restart-Strategien Vergleich

```mermaid
graph TD
    subgraph Old["❌ Alt: restart: always"]
        O1["Startet immer neu<br/>egal ob OOM, Config-Fehler"]
        O2["Keine Limits<br/>Endlosschleife möglich"]
        O3["Systemd: on-failure<br/>Nur bei Exit"]
        O4["Resultat:<br/>Stuck daemon bleibt stuck"]
    end
    
    subgraph New["✅ Neu: 3-Schichten-System"]
        N1["Docker: on-failure:5<br/>Health-Check basiert"]
        N2["Systemd: always<br/>+ StartLimitBurst"]
        N3["Monitor (optional)<br/>Zusätzliche Überwachung"]
        N4["Resultat:<br/>Auto-Recovery in 2-3 Min"]
    end
    
    Old -->|verbessert| New
    
    style Old fill:#FF6B6B,color:#fff,stroke:#DC143C,stroke-width:3px
    style New fill:#50C878,color:#fff,stroke:#228B22,stroke-width:3px
```

---

## 7️⃣ Fehler-Szenarios und Recovery

```mermaid
flowchart TD
    S1["❌ Szenario 1:<br/>Daemon stuck nach Stunden"]
    S1_R["Recovery:<br/>Docker Restart<br/>~180 Sekunden"]
    
    S2["❌ Szenario 2:<br/>Container crasht"]
    S2_R["Recovery:<br/>Systemd Restart<br/>~30 Sekunden"]
    
    S3["❌ Szenario 3:<br/>Restart-Schleife"]
    S3_R["Recovery:<br/>Manual Intervention<br/>systemctl reset-failed"]
    
    S4["❌ Szenario 4:<br/>Hailo-Hardware defekt"]
    S4_R["Recovery:<br/>Camera-Reset via sysfs<br/>oder Pi-Reboot"]
    
    S1 --> S1_R
    S2 --> S2_R
    S3 --> S3_R
    S4 --> S4_R
    
    S1_R --> OUT1["✅ WebUI antwortet<br/>Videos funktionieren"]
    S2_R --> OUT2["✅ Service läuft<br/>Alles normal"]
    S3_R --> OUT3["✅ Service läuft<br/>Logs prüfen"]
    S4_R --> OUT4["⚠️ Hardware-Fehler<br/>Admin-Aktion nötig"]
    
    style S1 fill:#FFB6C6,stroke:#FF1493
    style S2 fill:#FFB6C6,stroke:#FF1493
    style S3 fill:#FF6B6B,stroke:#DC143C,color:#fff
    style S4 fill:#FF4500,stroke:#8B0000,color:#fff
    
    style OUT1 fill:#90EE90,stroke:#228B22
    style OUT2 fill:#90EE90,stroke:#228B22
    style OUT3 fill:#FFE4B5,stroke:#FF8C00
    style OUT4 fill:#FF6B6B,stroke:#DC143C,color:#fff
```

---

## 🎯 Zusammenfassung: Was passiert beim Stuck-Daemon?

| Time | Event | Component | Status |
|------|-------|-----------|--------|
| **T+0s** | Daemon blockiert (z.B. Hailo stuck) | Container | 🔴 Stuck |
| **T+30s** | Health-Check #1 FAIL | Docker | ⚠️ FailingStreak: 1 |
| **T+60s** | Health-Check #2 FAIL | Docker | ⚠️ FailingStreak: 2 |
| **T+90s** | Health-Check #3 FAIL → **Unhealthy** | Docker | 🔴 Unhealthy |
| **T+120s** | **Docker Restart** triggered | Docker | ↻ Restarting |
| **T+150s** | Container stellt sich selbst wieder her | Container | 🟡 Startup |
| **T+180s** | **Recovery erfolgreich** ✅ | All | ✅ Healthy |

**Total Recovery Time:** **~3 Minuten** ohne manuelle Intervention!

---

## 📋 Mermaid Diagramme in Markdown

Diese Diagramme funktionieren in:
- ✅ GitHub README / Markdown
- ✅ Obsidian / Notion (mit Mermaid Plugin)
- ✅ GitLab Wiki
- ✅ Confluence (mit Mermaid Plugin)
- ✅ mkdocs-material

Zum Rendering benötigt: `mermaid` syntax highlighting oder ein Markdown-Viewer mit Mermaid-Support.
