# Ansible – Deployment für Vogel-Kamera

Automatisiert das Deployment des Vogel-Kamera Docker-Containers auf den Raspberry Pi 5
sowie die Einrichtung des lokalen Build-Rechners.

---

## Schnellstart

```bash
# 1. Persönliche Einstellungen anlegen (einmalig)
cp ansible/.env.example ansible/.env
nano ansible/.env

# 2. Vault-Passwort hinterlegen (einmalig)
echo 'MeinVaultPasswort' > ~/.pi-daemon-vault-pass && chmod 600 ~/.pi-daemon-vault-pass

# 3. Erstdeployment
./ansible/build_and_deploy.sh --install
```

---

## `build_and_deploy.sh` – Befehle

| Befehl | Beschreibung |
|--------|-------------|
| `--install` | Vollständiges Erstdeployment (Docker, SSL, Firewall, systemd) |
| `--update` | Nur Image + `.env` aktualisieren (schnell) |
| `--build` | Nur Docker-Image bauen, kein Deploy |
| `--setup-host` | Gentoo Build-Rechner einrichten (Docker, QEMU, buildx) |

---

## Verzeichnisstruktur

```
ansible/
├── .env                  ← Persönliche Werte (gitignoriert)
├── .env.example          ← Vorlage für .env
├── ansible.cfg
├── build_and_deploy.sh   ← Haupt-Skript für alle Aktionen
├── inventory/
│   └── hosts.yml         ← Raspberry Pi als Deploy-Ziel
├── group_vars/all/
│   ├── vars.yml          ← Variablen (aus .env via lookup('env'))
│   └── vault.yml         ← Verschlüsselt: TOTP-Secret
├── playbooks/
│   ├── deploy.yml        ← Erstdeployment auf dem Pi
│   ├── update.yml        ← Image-Update auf dem Pi
│   └── setup-build-host.yml  ← Build-Rechner einrichten (Gentoo)
└── roles/
    ├── docker/           ← Docker CE auf dem Pi installieren
    ├── ssl/              ← Self-signed TLS-Zertifikat
    ├── firewall/         ← UFW-Regeln
    ├── pi-daemon/        ← Container deployen, systemd-Service
    └── build-host/       ← Lokaler Gentoo-Rechner: Docker, QEMU, buildx
```

---

## Einmalige Einrichtung

### `.env` anlegen

Alle persönlichen Werte (Pi-Hostname, SSH-Key, Vault-Passwort-Pfad) werden
**nicht** ins Git eingecheckt und landen nur in `ansible/.env`:

```bash
cp ansible/.env.example ansible/.env
```

Wichtige Felder:

| Variable | Bedeutung | Beispiel |
|----------|-----------|---------|
| `PI_HOST` | Hostname oder IP des Pi | `raspberrypi-5-ai-had` |
| `PI_USER` | SSH-Benutzername | `roimme` |
| `PI_SSH_KEY` | Lokaler Pfad zum SSH-Private-Key | `~/.ssh/id_rsa_ai-had` |
| `VAULT_PASS_FILE` | Pfad zur Vault-Passwort-Datei | `~/.pi-daemon-vault-pass` |

### Ansible Vault

Das TOTP-Secret für die 2-Faktor-Authentifizierung wird verschlüsselt gespeichert:

```bash
# Neu verschlüsseln (beim ersten Mal)
ansible-vault encrypt ansible/group_vars/all/vault.yml

# Inhalte anzeigen
ansible-vault view ansible/group_vars/all/vault.yml

# Bearbeiten
ansible-vault edit ansible/group_vars/all/vault.yml
```

### Build-Rechner einrichten (Gentoo)

Zum Cross-Kompilieren des ARM64-Images müssen Docker, QEMU und buildx installiert sein.
Das erledigt die `build-host`-Rolle automatisch:

```bash
./ansible/build_and_deploy.sh --setup-host
# → fragt sudo-Passwort ab
# → emerge docker, qemu[aarch64], docker-buildx
# → Danach: newgrp docker  (oder neu einloggen)
```

Weitere Details: [docker/README.md](../docker/README.md)

---

## SSH-Key für den Pi

```bash
# Key erzeugen
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_pi

# Key auf den Pi übertragen
ssh-copy-id -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local
```
