# 🐳 Release v2.2.0 - Docker & Ansible Build-Infrastruktur

**Datum:** 13. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.0** erweitert die Deployment-Infrastruktur um vollständige **Ansible-Unterstützung für den lokalen Build-Rechner**. Ein einziger Befehl (`--setup-host`) installiert alle Voraussetzungen für das ARM64-Cross-Compilation auf Gentoo Linux: Docker CE, QEMU (aarch64 User-Space), docker-buildx und die persistente `binfmt_misc`-Kernel-Registrierung.

### 🎯 Kernziele erreicht:
- ✅ **Einmalige Einrichtung:** `./ansible/build_and_deploy.sh --setup-host`
- ✅ **Vollständig automatisiert:** Docker, QEMU, buildx per Ansible/Portage
- ✅ **Persistent:** QEMU-binfmt überlebt Neustarts via `/etc/local.d/`
- ✅ **Idempotent:** Wiederholte Ausführung sicher, bereits installiertes wird übersprungen
- ✅ **Dokumentiert:** Neue `ansible/README.md` + erweitertes `docker/README.md`

---

## 🐳 Neue Features

### 1. Ansible-Rolle `build-host` (Gentoo)

Die neue Rolle `ansible/roles/build-host/tasks/main.yml` richtet einen Gentoo-Rechner als ARM64-Build-Host ein:

```
Schritt 1: /etc/portage/package.accept_keywords
           → docker, docker-cli, docker-buildx, qemu (~amd64)

Schritt 2: /etc/portage/package.use/qemu
           → static-user + QEMU_USER_TARGETS: aarch64

Schritt 3: emerge docker, docker-cli, docker-buildx, qemu

Schritt 4: docker-Dienst starten (OpenRC oder systemd)

Schritt 5: Benutzer zur docker-Gruppe hinzufügen

Schritt 6: binfmt_misc laden + /etc/modules-load.d/ Eintrag

Schritt 7: /etc/local.d/qemu-binfmt.start (persistent, OpenRC)

Schritt 8: docker run --privileged tonistiigi/binfmt --install arm64

Schritt 9: docker buildx create --name pi-builder
           docker buildx inspect --bootstrap
           docker buildx use pi-builder
```

**Idempotenz:** Alle Tasks nutzen Ansible-Module mit integrierter Idempotenz (`lineinfile`, `copy`, `portage state=present`, `service`, `user`, `modprobe`). Der `buildx create`-Task ignoriert "already exists"-Fehler explizit.

### 2. `--setup-host` Befehl

```bash
./ansible/build_and_deploy.sh --setup-host
```

- Läuft **vollständig lokal** (kein SSH zum Pi nötig)
- Fragt `sudo`-Passwort interaktiv ab
- Danach einmalig `newgrp docker` oder neu einloggen

### 3. Neues Playbook `setup-build-host.yml`

```yaml
- hosts: localhost
  connection: local
  vars:
    build_host_user: "{{ lookup('env', 'USER') }}"
  roles:
    - build-host
```

---

## 🔧 Geänderte Dateien

### `ansible/build_and_deploy.sh`

Neuer Modus `--setup-host` ergänzt:
- In Usage-Kommentar dokumentiert
- `MODE="setup-host"` Erkennung
- Eigener Ausführungsblock vor dem SSH-Check (kein Pi-Zugriff nötig)
- `--help` aktualisiert mit allen vier Befehlen

### `ansible/group_vars/all/vars.yml`

```yaml
# Build-Host (lokaler Rechner)
build_host_user: "{{ lookup('env', 'USER') }}"
```

### `docker/README.md`

Ansible-Tipp-Box vor dem manuellen Schritt-für-Schritt-Guide:

```markdown
> **Tipp – automatisch per Ansible:**
> ./ansible/build_and_deploy.sh --setup-host
```

---

## 📁 Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `ansible/README.md` | Vollständige Ansible-Dokumentation: Schnellstart, Befehle, Struktur, Einrichtung |
| `ansible/playbooks/setup-build-host.yml` | Playbook für lokalen Gentoo Build-Host |
| `ansible/roles/build-host/tasks/main.yml` | Ansible-Rolle: Docker, QEMU, buildx auf Gentoo |
| `docker/README.md` | Gentoo-Schritt-für-Schritt-Anleitung für ARM64 Cross-Compilation |

---

## 🔄 Upgrade von v2.1.2

Kein Breaking Change. Bestehende Deployments laufen unverändert weiter.

**Neu nutzen:**
```bash
# Build-Host einrichten (nur nötig wenn Cross-Compilation nicht funktioniert)
./ansible/build_and_deploy.sh --setup-host

# Danach wie gewohnt
./ansible/build_and_deploy.sh --install   # oder --update
```

---

## 📊 Versionsübersicht

| Komponente | Version |
|-----------|---------|
| Gesamt | 2.2.0 |
| `unified-monitor-client` | 2.2.0 |
| `raspberry-pi-scripts` | 2.2.0 |
| `scripts/__version__.py` | 2.2.0 |
