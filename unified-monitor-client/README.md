# Unified Monitor Client — Docker Web API

**Vogel-Kamera-Überwachungssystem v2.2** — Flask-HTTPS-Daemon mit Web-GUI, JWT-Authentifizierung und TOTP-2FA, läuft als Docker-Container auf dem Raspberry Pi 5.

## Architektur

```
Browser  →  https://<pi-host>:8443/  (HTTPS, selbstsigniertes Zertifikat)
                    ↓  JWT + TOTP-2FA
        pi_daemon_secure.py  (Flask, im Docker-Container)
                    ↓
  unified-camera-monitor-detect-only.py  (Subprocess im Container)
                    ↓
    rpicam-vid + arecord  →  H264 + WAV  →  ffmpeg Merge  →  SSH-Sync
```

Der **lokale Python-Client** (`unified_monitor_client.py`) aus älteren Versionen ist in `legacy/unified-monitor-client/` archiviert. Die Steuerung erfolgt jetzt vollständig über den Browser.

---

## Inhalt dieses Verzeichnisses

```
unified-monitor-client/
├── pi_daemon_secure.py      ⭐ HAUPT-SYSTEM: Startpunkt des Flask HTTPS-Daemons
├── pi_daemon/               # Code des Daemons, aufgeteilt nach Aufgaben
│   ├── config.py            # Umgebungsvariablen, Logging
│   ├── runtime.py           # Gemeinsamer Zustand (_lock, state)
│   ├── settings.py          # Engine-, Detection-, Kamera-, Aufnahme-Einstellungen
│   ├── storage.py           # Atomares Schreiben der Einstellungsdateien
│   ├── camera.py            # Detection-Prozess, Aufnahme, Nachbearbeitung (Konvertierung + Transfer), Watchdog
│   ├── api.py               # Flask-App: Login (Passwort + TOTP → JWT) und alle Routen
│   ├── hailo.py             # Hailo-NPU Hardware-Info
│   ├── monitoring.py        # Health-Cache, Gotify-Alerts
│   ├── metrics.py           # Prometheus-Endpunkt /metrics
│   ├── powerbank.py         # Anker-Powerbank per Bluetooth, Akku-Warnung + Shutdown
│   ├── sync.py              # Sync-Ziele (rsync)
│   └── main.py              # Start: Threads + HTTPS-Server
├── tests/                   # pytest (läuft in CI, ohne Pi/Kamera)
├── web/                     # Web-GUI
│   ├── index.html           # Aufbau der Seite und Online-Hilfe (kein Inline-Skript)
│   ├── app.js               # gesamte Logik; Knöpfe sind über data-action angebunden
│   ├── app.css              # Gestaltung
│   ├── logo.webp            # Logo der Login-Seite
│   └── icon.png             # Favicon / Kopfzeile
├── requirements_daemon.txt  # Python-Dependencies im Container
├── README.md                # Diese Datei
├── SETUP_GUIDE.md           # Deployment-Anleitung (Ansible)
├── DETECT_AND_RECORD.md     # Detect-and-Record Modus
└── VERSION                  # Versionsnummer
```

---

## Authentifizierung

Der Daemon verlangt **JWT + TOTP**:

1. **TOTP-Code** (6-stellig, z. B. Google Authenticator / andOTP) → wird beim Login eingegeben
2. **JWT-Token** → wird vom Server ausgestellt, bleibt für die Session gültig

Der TOTP-Seed wird beim Installationsplaybook erzeugt und in einem Ansible Vault gespeichert. Der QR-Code für die Authenticator-App erscheint einmalig beim `--install`-Lauf.

---

## Web-GUI — Funktionen

| Schaltfläche / Funktion | Beschreibung |
|-------------------------|--------------|
| **Detection-Modus starten / stoppen** | Ein Knopf: startet das Detection-Skript (Hailo-NPU) und nimmt bei Erkennung automatisch auf, oder beendet es |
| **Erkennungsziel und Confidence** | Vogel, Mensch, Hund, Katze oder alle vier; Schwelle 0.10–0.95 |
| **Aufnahme / Audio** | Manuelle Aufnahme mit Profil und Dauer (10 s bis 10 min); gesperrt, solange der Detection-Modus läuft |
| **Bildeinstellungen** | Fokus, Belichtung, Weißabgleich, Helligkeit, Kontrast, Sättigung, Schärfe, Gain |
| **Konvertieren** | H264 → MP4 via `ffmpeg` im Container (läuft auch automatisch) |
| **Übertragen** | rsync der MP4-Dateien zu den Sync-Zielen (läuft nach jeder Aufnahme automatisch im Hintergrund) |
| **▶ Abspielen / ⬇ Download / 🗑 Löschen** | je Aufnahme in der Liste |
| **⚙ Einstellungen** | Sync-Ziele mit SSH-Key verwalten und testen |
| **📈 Monitoring** | öffnet das Grafana-Dashboard (nur wenn eingerichtet, siehe [monitoring/README.md](../monitoring/README.md)) |

Die Oberfläche fragt den Status alle 5 Sekunden ab, solange der Tab sichtbar ist.

---

## API-Endpunkte (REST)

Alle Endpunkte unter `/api/` außer `login`, `health` und `file` erfordern
`Authorization: Bearer <jwt>` im Header.

**Anmeldung und Status**

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `POST` | `/api/login` | Passwort + TOTP-Code → JWT (max. 5 Versuche pro Minute) |
| `GET` | `/api/health` | ohne Login: Version, RAM, freier Speicher – für den Docker-Health-Check |
| `GET` | `/api/status` | Gesamtstatus: Detection, Aufnahme, System, Hailo, Powerbank, Kamera-Einstellungen, `pending`, `recordings_rev`, `last_detection`, `seen_detection` |
| `GET` | `/metrics` | Prometheus-Format; eigenes Token (`PI_DAEMON_METRICS_TOKEN`), ohne Token-Konfiguration 404 |

**Erkennung**

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `POST` | `/api/detection/mode/start` · `/stop` | Detection-Modus (Automatik) starten / stoppen |
| `POST` | `/api/detection/start` · `/stop` | Detection-Prozess ohne Auto-Aufnahme starten / stoppen |
| `GET` `POST` | `/api/detection-settings` | Erkennungsziel und Confidence-Schwelle |
| `GET` `POST` | `/api/detection-engine` | Engine wählen (`hailo`, `cpu_yolo`) |

**Aufnahme**

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/api/profiles` | Aufnahme-Profile |
| `GET` `POST` | `/api/rec-settings` | gespeichertes Profil und Dauer (3–600 s) |
| `GET` `POST` | `/api/camera-settings` | Fokus, Belichtung, Weißabgleich, Helligkeit, Kontrast, Sättigung, Schärfe, Gain |
| `POST` | `/api/record` | Videoaufnahme starten (`{"profile": "normal_hd", "duration": 30}`) |
| `POST` | `/api/record/audio` | reine Audio-Aufnahme starten |
| `POST` | `/api/record/kill` | hängenden Aufnahme-Prozess beenden |
| `POST` | `/api/convert` | ausstehende H264-Dateien konvertieren |
| `POST` | `/api/transfer` | vorhandene MP4s an die Sync-Ziele übertragen |

**Dateien**

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/api/recordings` | die 100 neuesten Aufnahmen |
| `GET` | `/api/pending` | Anzahl H264-Dateien ohne MP4 |
| `GET` | `/api/download?p=<pfad>` | Datei herunterladen (mit JWT im Header) |
| `POST` | `/api/download-ticket` | `{"p": "<pfad>"}` → kurzlebiger Link für genau diese Datei |
| `GET` | `/api/file?t=<ticket>` | Datei zum Ticket, mit Range-Unterstützung (Player); `&dl=1` als Download |
| `POST` | `/api/delete` | `{"p": "<pfad>"}` – Datei samt zugehöriger H264/WAV löschen |
| `GET` | `/api/snapshot` | letztes Bild der Detection (nur CPU-YOLO-Engine) |

**Sync-Ziele**

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/api/settings` | Sync-Ziele lesen |
| `POST` | `/api/settings/targets` | Sync-Ziele speichern (optional mit SSH-Key) |
| `POST` | `/api/settings/test` | Verbindung zu einem Ziel testen |

**Statische Dateien:** `/` (Web-GUI), `/web/<datei>`, `/cert.pem` (öffentliches Zertifikat).

---

## Deployment

Der Daemon wird über Ansible gebaut und deployed. Kein manuelles Setup nötig.

```bash
# Einmalig: Konfiguration anlegen
cp ansible/.env.example ansible/.env
nano ansible/.env     # PI_HOST, PI_USER, PI_SSH_KEY, VAULT_PASS_FILE

# Erstinstallation
./ansible/build_and_deploy.sh --install

# Nach Code-Änderungen
./ansible/build_and_deploy.sh --update
```

→ Detaillierte Anleitung: [`SETUP_GUIDE.md`](SETUP_GUIDE.md)

---

## Konfiguration

Der Container liest seine Einstellungen aus Umgebungsvariablen (`/etc/pi-daemon/app.env`, erzeugt
von Ansible aus `ansible/.env`, `ansible/group_vars/all/vars.yml` und dem Vault).

| In `ansible/.env` bzw. `vars.yml` | Im Container | Beschreibung |
|---|---|---|
| Vault: `vault_pi_daemon_*` | `PI_DAEMON_JWT_SECRET`, `…_TOTP_SECRET`, `…_PASSWORD_HASH` | Pflicht: Login |
| `pi_daemon_port` | `PI_DAEMON_PORT` | HTTPS-Port (Standard `8443`) |
| `pi_video_dir` | `PI_DAEMON_VIDEO_DIR` | Verzeichnis für Aufnahmen (Volume) |
| `pi_token_expiry_h` | `PI_DAEMON_TOKEN_EXPIRY_HOURS` | Gültigkeit des Logins (Standard 8 h) |
| `pi_min_free_gb` | `PI_DAEMON_MIN_FREE_GB` | älteste Aufnahmen löschen, wenn weniger GB frei sind (`0` = aus) |
| `PI_POWERBANK_MAC` | `PI_DAEMON_POWERBANK_MAC` | Powerbank per Bluetooth (leer = aus) |
| `PI_MONITORING`, `PI_GRAFANA_ADMIN_PASSWORD` | `PI_DAEMON_METRICS_TOKEN`, `PI_DAEMON_GRAFANA_PORT` | Prometheus + Grafana auf dem Pi |
| `PI_METRICS_TOKEN`, `PI_GRAFANA_URL` | `PI_DAEMON_METRICS_TOKEN`, `PI_DAEMON_GRAFANA_URL` | nur für Monitoring auf einem anderen Rechner |
| `pi_daemon_gotify_url` / `_token` | `GOTIFY_URL`, `GOTIFY_TOKEN` | Push-Meldungen |

Sync-Ziele, Erkennungsziel, Kamera- und Aufnahme-Einstellungen werden in der Web-GUI gesetzt und
liegen als JSON unter `/etc/pi-daemon/` auf dem Pi.

---

## Fehlerbehebung

**Seite nicht erreichbar:**
```bash
# Container-Status prüfen
ssh <PI_USER>@<PI_HOST> "docker ps | grep vogel"

# Container-Logs
ssh <PI_USER>@<PI_HOST> "docker logs vogel-pi --tail 50"
```

**TOTP-Code ungültig:**
- Systemzeit auf dem Pi prüfen: `ssh <pi> "date"`
- TOTP funktioniert nur bei synchronisierter Uhrzeit (NTP)

**Detection startet nicht:**
```bash
# Logs aus dem Container
ssh <PI_USER>@<PI_HOST> "docker exec vogel-pi tail -50 /tmp/detect.log"

# Kamera verfügbar?
ssh <PI_USER>@<PI_HOST> "docker exec vogel-pi rpicam-hello -t 1000"
```

**Konvertierung schlägt fehl:**
```bash
# FFmpeg-Fehler aus Container-Log
ssh <PI_USER>@<PI_HOST> "docker logs vogel-pi 2>&1 | grep -i ffmpeg"
```

---

## Lizenz

Gleiche Lizenz wie das Hauptprojekt (MIT). Siehe [LICENSE](../LICENSE).

