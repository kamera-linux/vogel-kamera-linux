# Vogel-Kamera-Linux v2.3.2 – Gentoo Docker-Buildx-Fix · QEMU binfmt-Handler

**Veröffentlichung:** 3. Mai 2026  
**Typ:** Patch  
**Build:** `20260503-1`

---

## 🎯 Zusammenfassung

Diese Version behebt einen kritischen Fehler beim ARM64-Image-Build auf Gentoo Linux, der durch
QEMU aarch64 Segfaults auf hardenem Kernel (ASLR-Patches) verursacht wurde. Der gRPC HTTP/2-Fehler
`error reading server preface: http2: frame too large` tritt nicht mehr auf.

**Auswirkungen:** 
- ✅ Docker Buildx funktioniert wieder auf Gentoo
- ✅ ARM64-Builds stabil und reproduzierbar
- ✅ Deployment auf Raspberry Pi 5 zuverlässig

---

## 🐛 Behobene Probleme

### 1. Docker Buildx gRPC-Fehler auf Gentoo (3 Wochen alt)

**Fehler:**
```
ERROR: failed to initialize builder pi-builder (pi-builder0): listing workers: 
failed to list workers: Unavailable: connection error: desc = "error reading server 
preface: http2: frame too large"
```

**Symptome:**
- `docker buildx create --name pi-builder --use` schlägt fehl
- Nur auf Gentoo mit Hardened-Kernel (ASLR-Patches)
- Ubuntu, Debian, etc. nicht betroffen

**Ursache:**
- QEMU aarch64 Binary segfault unter Gentoo's `randomize_va_space=2`
- gRPC HTTP/2 Frame-Größe überschritten bei `docker-container`-Driver Builder
- Betroffen: buildx v0.19.0 – v0.21.2

**Lösung (v2.3.2):**
1. **binfmt-Handler aktualisieren:** tonistiigi/binfmt mit neuesten QEMU-Patches
2. **Fallback auf stabilen Builder:** Nutze `default` docker-driver statt `docker-container`-Driver
3. **Kernel-Konfiguration:** vm.mmap_rnd_bits=28, kernel.randomize_va_space=0

---

## ✨ Neue Features & Verbesserungen

### 1. Automatische QEMU binfmt-Handler-Aktualisierung

**Neue Funktion: `ensure_qemu_binfmt_handlers()`**

Die Python-Wrapper `build_and_deploy.py` aktualisieren QEMU-Emulatoren jetzt automatisch:

```bash
# Wird automatisch vor jedem Build ausgeführt
docker run --privileged --rm tonistiigi/binfmt --uninstall qemu-*
docker run --privileged --rm tonistiigi/binfmt --install all
sudo systemctl restart docker
```

**Aufruf:**
- Automatisch bei `--build` und `--update`
- Manuell testbar: `--setup-host`

### 2. Robustere Builder-Auswahl

**Alt (v2.3.1):**
```python
docker buildx create --name pi-builder --use  # ❌ gRPC Fehler auf Gentoo
```

**Neu (v2.3.2):**
```python
docker buildx use default  # ✅ Stabil auf allen Systemen
```

Der `default` docker-driver Builder ist bereits im System vorhanden und funktioniert auf allen
Linux-Distributionen, auch mit hardenem Kernel.

### 3. Erweiterte Ansible-Dokumentation

**Neue Sektion:** `ansible/README.md` → *"QEMU binfmt-Handler · Laufzeit-Updates"*

Dokumentiert:
- Kernel-Parameter für Gentoo (mmap_rnd_bits, randomize_va_space)
- Manuelle binfmt-Handler-Aktualisierung
- ASLR-Deaktivierung (falls nötig)

---

## 📋 Änderungen im Detail

### Dateien geändert:

| Datei | Änderung | Grund |
|-------|----------|-------|
| `ansible/build_and_deploy.py` | Neue `ensure_qemu_binfmt_handlers()` + `docker buildx use default` | gRPC-Fix |
| `ansible/README.md` | Neue Sektion "QEMU binfmt-Handler · Laufzeit-Updates" | Dokumentation |
| `VERSION`, `scripts/version.py` | 2.3.1 → 2.3.2 | Versionsbump |
| `raspberry-pi-scripts/VERSION` | 2.3.1 → 2.3.2 | Konsistenz |
| `unified-monitor-client/VERSION` | 2.3.1 → 2.3.2 | Konsistenz |

### Versionsinformationen:

```python
__version__ = "2.3.2"
RELEASE_NAME = "Gentoo Docker-Buildx-Fix · QEMU binfmt-Handler"
RELEASE_DATE = "2026-05-03"
```

---

## 🔧 Installationsanleitung

### Upgrade von v2.3.1

```bash
# Aktualisiere die Quellen
git pull origin main
git checkout v2.3.2  # optional: Tag direkt checken

# Alte binfmt-Handler löschen (empfohlen)
docker run --privileged --rm tonistiigi/binfmt --uninstall qemu-*

# Neuaufbau + Deployment
cd ansible && bash build_and_deploy.sh --update
```

### Neuinstallation auf Gentoo

```bash
# Build-Host einrichten
cd ansible && bash build_and_deploy.sh --setup-host

# Erstdeployment (baut Image, überträgt, richtet Pi ein)
cd ansible && bash build_and_deploy.sh --install

# E2E-Test
cd ansible && bash build_and_deploy.sh --e2e
```

---

## 🧪 Test-Ergebnisse

### Getestet auf:

| System | Kernel | Python | Docker | Buildx | Status |
|--------|--------|--------|--------|--------|--------|
| Gentoo x86_64 | v6.8+ (Hardened) | 3.13 | 28.2.2 | 0.19.0 | ✅ OK |
| RPi 5 (arm64) | v6.8+ | 3.13 | 28.2.2 | N/A | ✅ OK |

**Build-Zeit:** ~760 Sekunden (12,7 Minuten) für vollständigen ARM64-Build

**Keine gRPC-Fehler** bei mehrfachen Builds getestet.

---

## 📚 Referenzen

- GitHub Issues (Community):
  - [docker/buildx#3170](https://github.com/docker/buildx/issues/3170) – gRPC frame too large
  - [tonistiiji/binfmt#215](https://github.com/tonistiiji/binfmt/issues/215) – QEMU ASLR Segfault
  
- Dokumentation:
  - [ansible/README.md](../ansible/README.md#qemu-binfmt-handler--laufzeit-updates)
  - [docs/ARCHITEKTUR.md](../docs/ARCHITEKTUR.md)

---

## 🚀 Nächste Schritte

- [ ] CI/CD-Pipeline: Automatischer ARM64-Build bei jedem Commit
- [ ] Docker Hub: Pre-built ARM64-Image veröffentlichen
- [ ] Multi-Arch Build: ARM32 (v7) Support hinzufügen

---

## 📝 Mitwirkende

- Diagnostik & Fix: Gentoo-spezifische QEMU/Kernel-Probleme
- Testing: Mehrfache Build-Durchläufe auf Gentoo + Raspberry Pi 5

---

**Versionsvergleich:**

```diff
v2.3.1 → v2.3.2
- Docker buildx error: http2 frame too large
+ Automatische binfmt-Handler-Aktualisierung
+ Robuster Builder-Fallback (default statt pi-builder)
+ Erweiterte Gentoo-Dokumentation
```
