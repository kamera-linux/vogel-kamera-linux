# 🐳 Docker — ARM64-Image auf Gentoo Linux bauen

Schritt-für-Schritt-Anleitung für das Cross-Compilation des Vogel-Kamera Docker-Images (`linux/arm64`) auf einem **Gentoo x86_64**-System.

---

## Voraussetzungen

> **Tipp – automatisch per Ansible:**
> ```bash
> ./ansible/build_and_deploy.sh --setup-host
> ```
> Installiert Docker, QEMU (aarch64) und buildx automatisch.
> Danach einmal neu einloggen oder `newgrp docker` ausführen.

### Schritt 1 — Docker installieren

Auf Gentoo wird Docker über `app-containers/docker` installiert:

```bash
# USE-Flags setzen (empfohlen)
echo 'app-containers/docker ~amd64' >> /etc/portage/package.accept_keywords
echo 'app-containers/docker-cli ~amd64' >> /etc/portage/package.accept_keywords

# Docker installieren
emerge --ask app-containers/docker app-containers/docker-cli
```

Docker-Daemon beim Systemstart aktivieren und starten:

```bash
# OpenRC
rc-update add docker default
rc-service docker start

# systemd
systemctl enable --now docker
```

Eigenen User zur `docker`-Gruppe hinzufügen (kein `sudo` nötig):

```bash
gpasswd -a $USER docker
newgrp docker          # Gruppe sofort aktivieren (oder neu einloggen)
```

Prüfen:

```bash
docker version
docker run --rm hello-world
```

---

### Schritt 2 — QEMU-User-Static installieren

QEMU wird benötigt, um ARM64-Binaries auf x86_64 auszuführen:

```bash
echo 'app-emulation/qemu ~amd64' >> /etc/portage/package.accept_keywords

# Minimales USE-Flag: nur User-Space-Emulation, kein KVM-Overhead
echo 'app-emulation/qemu static-user QEMU_SOFTMMU_TARGETS: QEMU_USER_TARGETS: aarch64' \
  >> /etc/portage/package.use/qemu

emerge --ask app-emulation/qemu
```

QEMU-Binary-Formate im Kernel registrieren:

```bash
# Prüfen ob binfmt_misc geladen ist
lsmod | grep binfmt_misc
# Falls nicht: modprobe binfmt_misc

# QEMU-Interpreter für ARM64 mit Docker registrieren (einmalig)
docker run --privileged --rm tonistiigi/binfmt --install arm64

# Prüfen ob aarch64 registriert ist
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
```

> Die Registrierung über `tonistiigi/binfmt` ist nach einem Neustart weg.  
> Für dauerhafte Registrierung: `sys-apps/binfmt-support` oder einen OpenRC-/systemd-Dienst einrichten  
> (siehe Anhang unten).

---

### Schritt 3 — Docker Buildx einrichten

`docker buildx` ist in neueren Docker-Versionen enthalten. Prüfen:

```bash
docker buildx version
```

Einen neuen Builder mit Multi-Plattform-Unterstützung anlegen:

```bash
docker buildx create --name multiarch --driver docker-container --use
docker buildx inspect --bootstrap
```

Ausgabe sollte `linux/amd64, linux/arm64` unter "Platforms" zeigen.

---

## Image bauen

### Schritt 4 — Repository klonen

```bash
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
```

### Schritt 5 — ARM64-Image bauen

**Wichtig:** Der Build-Kontext muss das **Repo-Root** sein (nicht `docker/`), da der Dockerfile Dateien aus `unified-monitor-client/` und `raspberry-pi-scripts/` kopiert.

```bash
docker buildx build \
  --platform linux/arm64 \
  --file docker/Dockerfile \
  --tag vogel-pi:latest \
  --load \
  .
```

| Flag | Bedeutung |
|------|-----------|
| `--platform linux/arm64` | Ziel-Architektur (Raspberry Pi 5) |
| `--file docker/Dockerfile` | Dockerfile-Pfad (Kontext ist `.`) |
| `--tag vogel-pi:latest` | Image-Name und Tag |
| `--load` | Image ins lokale `docker images` laden |

Der Build dauert auf x86_64 via QEMU-Emulation typisch **5–15 Minuten** (abhängig von CPU und `rpicam-apps`-Paket).

---

### Schritt 6 — Image prüfen

```bash
# Architektur verifizieren
docker inspect vogel-pi:latest | grep Architecture
# Erwartet: "Architecture": "arm64"

# Image-Größe
docker images vogel-pi
```

---

## Image auf den Raspberry Pi übertragen

### Option A — Direkt per SSH (kein Registry nötig)

```bash
# As tar.gz exportieren
docker save vogel-pi:latest | gzip > vogel-pi-arm64.tar.gz

# Zum Pi übertragen
scp -i ~/.ssh/id_rsa_pi vogel-pi-arm64.tar.gz pi@raspberry-pi.local:~

# Auf dem Pi laden
ssh -i ~/.ssh/id_rsa_pi pi@raspberry-pi.local "docker load < ~/vogel-pi-arm64.tar.gz"
```

### Option B — Ansible (empfohlen für dieses Projekt)

```bash
cp ansible/.env.example ansible/.env
nano ansible/.env    # PI_HOST, PI_USER, PI_SSH_KEY eintragen

./ansible/build_and_deploy.sh --install
```

Das Skript erledigt Build + Export + Transfer + Container-Start automatisch.

---

## Container lokal testen (optional)

Da `rpicam-apps` Kamera-Hardware erwartet, kann der Container lokal nur eingeschränkt getestet werden. Für reine API-Tests:

```bash
docker run --rm -it \
  -p 8443:8443 \
  --platform linux/arm64 \
  vogel-pi:latest \
  python3 -c "import flask, pyotp; print('Imports OK')"
```

---

## Anhang: QEMU-Registrierung dauerhaft einrichten (OpenRC)

Damit `binfmt_misc` nach einem Neustart erhalten bleibt:

```bash
# /etc/local.d/qemu-binfmt.start
#!/bin/sh
docker run --privileged --rm tonistiigi/binfmt --install arm64
```

```bash
chmod +x /etc/local.d/qemu-binfmt.start
rc-update add local default
```

---

## Anhang: Kern-Konfiguration für binfmt_misc

Falls `binfmt_misc` nicht als Modul vorhanden ist:

```bash
# Prüfen
zcat /proc/config.gz | grep BINFMT_MISC
# Erwartet: CONFIG_BINFMT_MISC=y oder CONFIG_BINFMT_MISC=m
```

Falls nicht gesetzt → Kernel neu kompilieren mit:

```
Kernel hacking  --->
  [*] Magic SysRq key
General setup  --->
  [*] Enable binfmt_misc
```

---

## Fehlerbehebung

**`exec format error` beim Build:**
QEMU ist nicht korrekt registriert.
```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
```

**`docker buildx` nicht gefunden:**
```bash
emerge --ask app-containers/docker-buildx
# oder: Plugin manuell nach ~/.docker/cli-plugins/ herunterladen
```

**Build bricht bei `rpicam-apps` ab:**
Das Paket zieht viele Abhängigkeiten nach. Erhöhe den Buildtime-Timeout:
```bash
# In /etc/docker/daemon.json
{ "default-network-opts": {}, "log-level": "warn" }
```
Oder baue mit `--progress=plain` für detaillierte Ausgabe:
```bash
docker buildx build --platform linux/arm64 --progress=plain -f docker/Dockerfile --tag vogel-pi:latest --load .
```

**Kein Speicherplatz:**
QEMU-Builds benötigen erheblich mehr temporären Disk-Speicher (~3–5 GB).
```bash
# Build-Cache aufräumen
docker buildx prune -f
docker system prune -f
```
