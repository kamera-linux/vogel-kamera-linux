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
├── pi_daemon_secure.py      ⭐ HAUPT-SYSTEM: Flask HTTPS-Daemon
├── web/                     # Web-GUI (HTML/CSS/JS)
│   ├── index.html           # Single-Page-Oberfläche
│   ├── style.css            # Styling
│   └── app.js               # Frontend-Logik
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
| **Detection starten** | Startet `unified-camera-monitor-detect-only.py` als Subprocess; nimmt automatisch auf, wenn ein Vogel erkannt wird |
| **Detection stoppen** | Beendet den Subprocess sauber (SIGTERM → SIGKILL) |
| **Manuell aufnehmen** | Startet eine Aufnahme mit fester Dauer (ohne KI-Trigger) |
| **Konvertieren** | H264 + WAV → MP4 via `ffmpeg` direkt im Container |
| **Transfer** | SSH-Sync der MP4-Dateien zu konfigurierten Zielsystemen |
| **Download** | Browser-Download einzelner Aufnahmen |
| **Löschen** | Löscht ausgewählte Aufnahmen aus dem Container-Volume |

---

## API-Endpunkte (REST)

Alle Endpunkte erfordern `Authorization: Bearer <jwt>` im Header.

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `POST` | `/api/login` | Login mit TOTP-Code → gibt JWT zurück |
| `GET` | `/api/status` | Systemstatus (Daemon, Subprocess, Disk) |
| `POST` | `/api/detection/start` | Detection-Subprocess starten |
| `POST` | `/api/detection/stop` | Detection-Subprocess stoppen |
| `POST` | `/api/record` | Manuelle Aufnahme starten (`{"duration": 30}`) |
| `POST` | `/api/convert` | Konvertierung starten |
| `POST` | `/api/transfer` | SSH-Sync zu Zielsystemen |
| `GET` | `/api/files` | Liste der vorhandenen Aufnahmedateien |
| `GET` | `/api/download/<filename>` | Datei herunterladen |
| `DELETE` | `/api/files/<filename>` | Datei löschen |
| `GET` | `/api/logs` | Letzte Log-Zeilen des Detection-Subprozesses |

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

## Konfiguration (im Container)

Alle variablen Werte werden per Ansible-Variablen übergeben (`ansible/group_vars/all/vars.yml`):

| Variable | Beschreibung |
|----------|--------------|
| `pi_detection_script` | Pfad zum Detection-Skript im Container |
| `pi_video_dir` | Verzeichnis für Aufnahmen (gemountet als Volume) |
| `pi_sync_targets` | Liste der SSH-Zielsysteme für Transfer |
| `daemon_https_port` | HTTPS-Port (Standard: `8443`) |
| `totp_secret` | TOTP-Seed (via Ansible Vault verschlüsselt) |

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

