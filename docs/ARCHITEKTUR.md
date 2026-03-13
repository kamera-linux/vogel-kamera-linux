# 🏗️ Vogel-Kamera Architektur (v2.2)

## Überblick

Das System basiert auf einem **Docker-Container auf dem Raspberry Pi 5**, der über eine HTTPS-Web-API gesteuert wird. Kein lokaler Python-Client nötig — die Bedienung erfolgt vollständig über den Browser.

```
┌─────────────────────────────────────────────────────────┐
│  Lokaler Rechner (deploy-PC)                            │
│                                                         │
│  Browser  ──HTTPS──►  https://<pi-host>:8443/           │
│  Ansible  ──SSH──►    ./ansible/build_and_deploy.sh     │
└──────────────────────────┬──────────────────────────────┘
                           │ SSH / HTTPS
┌──────────────────────────▼──────────────────────────────┐
│  Raspberry Pi 5 (Trixie / ARM64)                        │
│                                                         │
│  ┌─────────────────────────────────────────────┐        │
│  │  Docker-Container: vogel-pi:latest          │        │
│  │                                             │        │
│  │  pi_daemon_secure.py (Flask, Port 8443)     │        │
│  │    ├─ JWT-Authentifizierung                 │        │
│  │    ├─ TOTP-2FA (PyOTP)                      │        │
│  │    ├─ HTTPS (selbstsigniertes Zertifikat)   │        │
│  │    └─ REST-API + Web-GUI (web/)             │        │
│  │              │                              │        │
│  │              ▼ subprocess                   │        │
│  │  unified-camera-monitor-detect-only.py      │        │
│  │    ├─ YOLO26n KI-Erkennung                  │        │
│  │    ├─ rpicam-vid (H264-Aufnahme)            │        │
│  │    ├─ arecord (WAV-Audio)                   │        │
│  │    └─ ffmpeg (H264 + WAV → MP4)             │        │
│  │              │                              │        │
│  │              ▼                              │        │
│  │  /videos (Container-Volume)                 │        │
│  │    └─ gemountet → ~/Videos/Vogelhaus        │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
│  Hardware:  IMX708-Kamera  │  USB-Mikrofon              │
└─────────────────────────────────────────────────────────┘
                           │ SSH-Sync
┌──────────────────────────▼──────────────────────────────┐
│  Zielsystem(e) — konfigurierbar in Ansible vars         │
│  (NAS, anderer PC, etc.)                                │
└─────────────────────────────────────────────────────────┘
```

---

## Komponenten

### pi_daemon_secure.py — Flask HTTPS-Daemon

**Aufgabe:** Zentraler API-Server im Container. Nimmt HTTP-Anfragen entgegen, startet/stoppt Subprozesse, verwaltet Dateien.

**Authentifizierung:**
- Login-Endpunkt `/api/login` erwartet TOTP-Code
- Bei Erfolg: JWT-Token (zeitlich begrenzt)
- Alle anderen Endpunkte erfordern `Authorization: Bearer <jwt>`

**Transport:**
- HTTPS auf Port `8443` mit selbstsigniertem Zertifikat
- Zertifikat wird beim Ansible-`--install` erzeugt und in den Container gemountet

**Subprozess-Management:**
- Detection-Skript wird als `subprocess.Popen` gestartet
- Graceful Shutdown: SIGTERM → Wartzeit → SIGKILL
- Status-Tracking über PID

### unified-camera-monitor-detect-only.py — Detection + Recording

**Aufgabe:** Läuft als Subprocess im Container, übernimmt KI-Erkennung und Aufnahme.

**Ablauf:**
1. `picamera2` + YOLO26n: Frames analysieren, auf Vogelerkennung warten
2. Bei Trigger: `rpicam-vid` starten → H264-Datei
3. Parallel: `arecord` → WAV-Datei
4. Nach Aufnahme: `ffmpeg` → H264 + WAV → MP4
5. Aufnahme in `/videos` abgelegt

**Parameter** (via Daemon übergeben):
- `--threshold` — Erkennungs-Schwellenwert (0.0–1.0)
- `--duration` — Aufnahmedauer in Sekunden
- `--cooldown` — Pause zwischen Aufnahmen

### web/ — Web-GUI

**Aufgabe:** Single-Page-Interface für die Bedienung über den Browser.

**Funktionen:**
- Login mit TOTP-Code
- Detection starten / stoppen
- Manuelle Aufnahmen starten
- Dateiliste mit Download und Löschen
- Transfer zu Zielsystemen anstoßen
- Echtzeit-Logs (Polling `/api/logs`)

### ansible/ — Deployment

**Aufgabe:** Baut das Docker-Image, installiert es auf dem Pi, verwaltet Secrets.

```
ansible/
├── .env.example              Vorlage (in git)
├── .env                      Persönliche Werte (gitignored!)
├── build_and_deploy.sh       Haupt-Skript (--install / --update)
├── ansible.cfg               SSH-Konfiguration
├── inventory/hosts.yml       Pi-Definition (liest aus group_vars)
└── group_vars/all/
    ├── vars.yml              Variablen (PI_HOST, PI_USER etc. aus .env)
    └── vault.yml             Verschlüsselte Secrets (TOTP-Seed)
```

---

## Datenfluss: Aufnahme-Session

```
1. User klickt "Detection starten" in der Web-GUI
        ↓
2. Browser  POST /api/detection/start  →  pi_daemon_secure.py
        ↓
3. Daemon startet subprocess:  unified-camera-monitor-detect-only.py
        ↓
4. Detect-Skript: picamera2 analysiert Frames mit YOLO26n
        ↓
5. Vogel erkannt (confidence ≥ threshold):
        ↓
6a. rpicam-vid  →  /videos/YYYY-MM-DD_HH-MM-SS.h264
6b. arecord     →  /videos/YYYY-MM-DD_HH-MM-SS.wav
        ↓
7. ffmpeg merge:  .h264 + .wav  →  .mp4  (Container-intern)
        ↓
8. MP4 liegt in /videos (= ~/Videos/Vogelhaus auf dem Pi)
        ↓
9. Optional: Transfer-Button → SSH-Sync zu Zielsystemen
```

---

## Deployment-Workflow

```
Lokaler Rechner
    │
    ├─ docker buildx build --platform linux/arm64  →  vogel-pi:latest
    │
    ├─ ansible-playbook site.yml (über SSH)
    │     ├─ Image auf Pi übertragen (docker load)
    │     ├─ TLS-Zertifikate erzeugen
    │     ├─ TOTP-Seed generieren (Vault)
    │     ├─ docker-compose oder docker run
    │     └─ systemd-Service aktivieren
    │
    └─ Container läuft dauerhaft auf Port 8443
```

---

## Sicherheitsmodell

| Aspekt | Maßnahme |
|--------|----------|
| Transport-Verschlüsselung | HTTPS (TLS 1.2+, selbstsigniertes Zertifikat) |
| Authentifizierung | JWT + TOTP (2-Faktor) |
| Secrets-Verwaltung | Ansible Vault (AES-256) |
| Persönliche Konfig | `ansible/.env` (gitignored, nie ins Repository) |
| Container-User | `appuser` (UID 999, nicht root) |
| Netzwerk | Nur Port 8443 exponiert, intern isoliert |

---

## Legacy-Architektur (< v2.2, archiviert)

Die alte Architektur mit SSH-basiertem Python-Client ist in `legacy/` archiviert.

```
# ALT (in legacy/unified-monitor-client/)
Lokaler PC
  └─ unified_monitor_client.py (Python)
       └─ SSH → Pi
            └─ unified-camera-monitor-auto.py (picamera2)
            └─ unified-camera-monitor-manual.py (rpicam-vid)
```

Alle zugehörigen Dateien (`config.py`, `ssh_manager.py`, `monitors.py`, `setup_environment.py` etc.) befinden sich in `legacy/unified-monitor-client/`.
