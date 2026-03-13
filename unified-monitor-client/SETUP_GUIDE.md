# 🚀 Setup Guide — Docker-Deployment via Ansible

Dieses Dokument beschreibt die Installation und Aktualisierung des Vogel-Kamera-Systems.  
Das System läuft als **Docker-Container auf dem Raspberry Pi** und wird über einen Browser gesteuert.

---

## Voraussetzungen

### Lokaler Rechner (deploy-PC)

- **Docker** (für den Image-Build)
- **Ansible** (`ansible`, `ansible-playbook`)
- **SSH-Key** für den Raspberry Pi eingerichtet

```bash
# Prüfen ob alles vorhanden ist
docker --version
ansible --version
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "echo OK"
```

### Raspberry Pi

- **Raspberry Pi OS Trixie (Debian 13)** oder neuer
- SSH-Zugang mit Key-Authentifizierung aktiviert
- Kamera-Modul (IMX708 Wide) und USB-Mikrofon angeschlossen

---

## Einrichtung (einmalig)

### 1. Konfiguration anlegen

```bash
# Vorlage kopieren — die erzeugte .env-Datei wird NICHT versioniert
cp ansible/.env.example ansible/.env
```

Dann in `ansible/.env` die eigenen Werte eintragen:

```bash
PI_HOST=raspberry-pi.local       # Hostname oder IP des Raspberry Pi
PI_USER=pi                        # SSH-Benutzername auf dem Pi
PI_SSH_KEY=~/.ssh/id_rsa_pi      # Pfad zum lokalen SSH Private Key
VAULT_PASS_FILE=~/.pi-vault-pass  # Ansible Vault Passwort-Datei (wird erzeugt)
```

### 2. Vault-Passwort-Datei anlegen (für verschlüsselte Secrets)

```bash
# Sicheres Passwort in eine Datei schreiben (600-Rechte!)
echo "mein-sicheres-passwort" > ~/.pi-vault-pass
chmod 600 ~/.pi-vault-pass
```

> Der Vault wird beim `--install` automatisch erzeugt und enthält den TOTP-Seed.

### 3. Erstinstallation starten

```bash
./ansible/build_and_deploy.sh --install
```

Das Skript erledigt automatisch:
- ✅ Docker-Image bauen (ARM64, für Raspberry Pi 5)
- ✅ Image auf den Pi übertragen
- ✅ Docker auf dem Pi installieren (falls nötig)
- ✅ TLS-Zertifikate erzeugen (selbstsigniert)
- ✅ TOTP-Seed generieren und im Vault verschlüsseln
- ✅ Container starten und als Systemdienst einrichten
- ✅ QR-Code für Authenticator-App anzeigen (einmalig!)

### 4. Authenticator-App einrichten

Beim ersten `--install` wird ein QR-Code im Terminal angezeigt.  
Diesen **jetzt** mit einer TOTP-App einscannen (z. B. Google Authenticator, andOTP, Aegis):

```
⚠️  TOTP-QR-Code (einmalig — jetzt einscannen!):

  ██████████████  ██  ████  ██████████████
  ...
```

Der QR-Code wird nicht erneut angezeigt. Falls verloren: `--install` erneut ausführen (erzeugt neuen Seed).

### 5. Web-GUI öffnen

```
https://<PI_HOST>:8443/
```

Das Zertifikat ist selbstsigniert → Browser-Warnung einmalig bestätigen ("Trotzdem fortfahren").

---

## Aktualisierung

Nach Code-Änderungen an `pi_daemon_secure.py`, `web/` oder dem Detection-Skript:

```bash
./ansible/build_and_deploy.sh --update
```

Dieser Befehl:
- ✅ Baut das Docker-Image neu
- ✅ Überträgt nur geänderte Schichten (effizient)
- ✅ Startet den Container neu
- ⚠️ TOTP-Seed und Zertifikate bleiben unverändert

---

## Was läuft wo?

| Komponente | Ort | Beschreibung |
|------------|-----|--------------|
| `pi_daemon_secure.py` | Im Docker-Container | Flask HTTPS-Daemon, Port 8443 |
| `web/` | Im Docker-Container | Web-GUI (HTML/CSS/JS) |
| `unified-camera-monitor-detect-only.py` | Im Docker-Container | Detection-Subprocess |
| Aufnahmen | Container-Volume `/videos` | Persistentes Verzeichnis auf dem Pi (`/home/<user>/Videos`) |
| `ansible/.env` | Lokaler Rechner | Persönliche Konfiguration (gitignored!) |
| TLS-Zertifikat | Pi + Container | `/etc/pi-daemon/tls/` |
| TOTP-Seed | Ansible Vault | Verschlüsselt in `ansible/group_vars/all/vault.yml` |

---

## Ansible-Variablen

Alle anpassbaren Einstellungen in `ansible/group_vars/all/vars.yml`:

| Variable | Beschreibung | Standard |
|----------|--------------|---------|
| `pi_host` | Pi-Hostname (aus `PI_HOST` env) | — |
| `pi_user` | SSH-User (aus `PI_USER` env) | — |
| `pi_home` | Home-Verzeichnis | `/home/<pi_user>` |
| `pi_detection_script` | Pfad zum Detection-Skript im Container | `/app/detect.py` |
| `pi_video_dir` | Aufnahme-Verzeichnis auf dem Pi | `~/Videos/Vogelhaus` |
| `daemon_https_port` | HTTPS-Port des Daemons | `8443` |
| `pi_sync_targets` | Liste der SSH-Zielsysteme für Transfer | `[]` |

---

## Fehlerbehebung

### Ansible-Fehler: `.env` nicht gefunden

```
ERROR: ansible/.env not found. Copy ansible/.env.example to ansible/.env and fill in your values.
```

→ `cp ansible/.env.example ansible/.env` und Werte eintragen.

### SSH-Verbindung schlägt fehl

```bash
# SSH-Key auf Pi kopieren
ssh-copy-id -i ~/.ssh/id_rsa_pi.pub pi@raspberry-pi.local

# Verbindung testen
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "echo OK"
```

### Container startet nicht

```bash
# Container-Status auf dem Pi
ssh <PI_USER>@<PI_HOST> "docker ps -a | grep vogel"

# Container-Logs
ssh <PI_USER>@<PI_HOST> "docker logs vogel-pi --tail 100"

# Docker-Service neu starten
ssh <PI_USER>@<PI_HOST> "sudo systemctl restart docker"
```

### Kamera nicht verfügbar

```bash
# Kamera-Gruppe prüfen (appuser muss in 'video' sein)
ssh <PI_USER>@<PI_HOST> "docker exec vogel-pi id appuser"

# Kamera-Test direkt im Container
ssh <PI_USER>@<PI_HOST> "docker exec vogel-pi rpicam-hello -t 1000"
```

### TOTP-Code wird abgelehnt

1. Systemzeit auf Pi prüfen: `ssh <pi> "date"`
2. NTP aktiv: `ssh <pi> "systemctl status systemd-timesyncd"`
3. TOTP-Seed neu erzeugen: `./ansible/build_and_deploy.sh --install` (überschreibt Vault)

---

## Legacy: Alter SSH-basierter Python-Client

Der frühere `unified_monitor_client.py` (SSH-basiert, Python-Skript auf dem lokalen PC) ist in `legacy/unified-monitor-client/` archiviert und nicht mehr aktiv. Für Referenzzwecke oder Rollback ist er dort erhalten.

---

**Weiterführende Dokumentation:**
- [README.md](README.md) — Web-API und Container-Dokumentation
- [DETECT_AND_RECORD.md](DETECT_AND_RECORD.md) — Detection-Modus
- [../docs/ARCHITEKTUR.md](../docs/ARCHITEKTUR.md) — Systemarchitektur
- [../docs/SECURITY.md](../docs/SECURITY.md) — Sicherheitsrichtlinien
