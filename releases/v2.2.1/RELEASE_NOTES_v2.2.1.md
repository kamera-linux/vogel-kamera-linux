# 🖥️ Release v2.2.1 - Web-GUI Verbesserungen & HTTPS-Komfort

**Datum:** 15. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.1** verbessert die Web-GUI deutlich: Das Projekt-Logo erscheint jetzt auf dem Login-Bildschirm und in der Topbar, die Versionsnummer wird live angezeigt, und der Umgang mit dem selbstsignierten HTTPS-Zertifikat wird einfacher. Außerdem wurden der Dockerfile-Build-Warnungs-Fix, ein E2E-Test-Bug und die Hilfetexte vervollständigt.

### 🎯 Kernziele erreicht:
- ✅ **Version-Badge** in der Web-GUI-Topbar (live aus der API)
- ✅ **Projekt-Logo** auf Login-Seite (220 px) und Topbar (32 px)
- ✅ **HTTPS-Komfort:** Zertifikat-Download-Link + Chrome-Importanleitung direkt auf der Login-Seite
- ✅ **Dockerfile:** Build-Warnung `RedundantTargetPlatform` behoben
- ✅ **E2E-Test:** Falscher Profilname `FHD` → `normal_hd` korrigiert
- ✅ **Hilfe-Modal** um zwei fehlende Sektionen ergänzt

---

## ✨ Neue Features

### 1. Versions-Badge in der Topbar

Die Web-GUI zeigt jetzt die aktive Server-Version direkt in der Topbar an. Der Wert wird beim ersten `/api/status`-Poll dynamisch aus der API geladen.

```
🐦 Vogel-Kamera  v2.2.1
```

**Technisch:**
- `APP_VERSION = '2.2.1'` Konstante in `pi_daemon_secure.py`
- `/api/status` Response enthält `"version": "2.2.1"`
- JS füllt `<small id="gui-version" class="version-badge">` beim ersten Polling
- CSS `.version-badge` — abgerundete Pille, gedämpfte Farbe

### 2. Projekt-Logo in der Web-GUI

Das Projektlogo (`Entwurf-T-Shirt-transparenz.png`, transparent, 880×1192 px) ist jetzt in der Web-GUI eingebunden:

| Position | Größe | Beschreibung |
|----------|-------|-------------|
| Login-Bildschirm | 220 px Höhe | Zentriert über dem Login-Formular |
| Topbar (linke Ecke) | 32 px Höhe | Neben dem Seitentitel, ersetzt 🐦-Emoji |

**Route:** `GET /web/<filename>` — Flask `send_from_directory` für statische Dateien aus `web/`

### 3. HTTPS-Zertifikat: Download & Chrome-Importanleitung

Auf der Login-Seite erscheint jetzt ein Hinweis mit direktem Download-Link und schrittweiser Chrome-Anleitung, um die Browser-Warnung „Nicht sicher" dauerhaft zu entfernen:

```html
Selbstsigniertes Zertifikat –
[Zertifikat herunterladen]          ← direkt als vogel-kamera.pem
Chrome: chrome://settings/certificates
→ Zertifizierungsstellen → Importieren → „Für Websites vertrauen" ✓
```

**Neue Route:** `GET /cert.pem` (keine Auth erforderlich) — liefert das Serverzertifikat als Download

**SSL SAN erweitert:**
- `DNS:{{ pi_host }}`, `DNS:localhost`
- `IP:{{ ansible_default_ipv4.address }}`, `IP:127.0.0.1`
- CN jetzt dynamisch via `{{ pi_host }}` statt hartcodiert

> ⚠️ Die erweiterten SANs gelten nur für **neu generierte** Zertifikate.  
> Altes Zertifikat auf dem Pi löschen und `--install` neu ausführen, um sie zu aktivieren.

### 4. Hilfe-Modal vervollständigt

Zwei fehlende Sektionen wurden im Online-Hilfe-Modal ergänzt:

**🎤 Audio-Only Aufnahme**
- Max. 60 Minuten
- Grüner Fortschrittsbalken
- Gegenseitiger Ausschluss mit Video-Aufnahme

**📷 Live-Vorschau**
- Benötigt aktiven Detection-Modus
- 250 ms Aktualisierungsrate
- Start/Stop umschaltbar

---

## 🔧 Bugfixes

### E2E-Test: Falsches Aufnahme-Profil `FHD`

**Problem:** `build_and_deploy.sh --e2e` sendete `profile=FHD` an `/api/record`. Das Profil `FHD` existiert nicht — der Daemon antwortete mit HTTP 400.

**Fix:** Profilname in Schritt [5] von `"FHD"` → `"normal_hd"` geändert (entspricht dem tatsächlichem Key im Daemon).

### Dockerfile: Build-Warnung `RedundantTargetPlatform`

**Problem:** `FROM --platform=linux/arm64 python:3.13-slim-bookworm` löste die Warnung `RedundantTargetPlatform` aus, da `docker buildx --platform linux/arm64` das Ziel bereits via Buildkit setzt.

**Fix:** `--platform`-Flag aus der `FROM`-Zeile entfernt → `FROM python:3.13-slim-bookworm`

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `unified-monitor-client/pi_daemon_secure.py` | `APP_VERSION`, `/api/status` version-Feld, `/web/<filename>` Route, `/cert.pem` Route |
| `unified-monitor-client/web/index.html` | Logo (Login + Topbar), Version-Badge, Cert-Hinweis, Hilfe-Modal |
| `unified-monitor-client/web/logo.png` | Neu: Projekt-Logo (880×1192 px, transparent, ~1 MB) |
| `ansible/build_and_deploy.sh` | E2E-Profil `FHD` → `normal_hd` |
| `ansible/roles/ssl/tasks/main.yml` | Erweiterter SAN, dynamischer CN |
| `docker/Dockerfile` | `--platform` aus `FROM` entfernt |
| `VERSION` | 2.2.0 → 2.2.1 |

---

## 🔄 Upgrade von v2.2.0

Kein Breaking Change. Einfaches Update genügt:

```bash
cd ansible && bash build_and_deploy.sh --update --e2e
```

**Optional — Chrome HTTPS-Warnung beheben:**

1. Nach dem Deploy Login-Seite aufrufen: `https://raspberrypi-5-ai-had:8443`
2. Auf **„Zertifikat herunterladen"** klicken → `vogel-kamera.pem`
3. Chrome öffnen: `chrome://settings/certificates`
4. Tab **„Zertifizierungsstellen"** → **„Importieren"**
5. `vogel-kamera.pem` auswählen → **„Diesem Zertifikat für die Identifizierung von Websites vertrauen"** ✓ → OK

**Optional — Zertifikat mit erweitertem SAN neu generieren** (IP-Adresse im SAN):

```bash
# Altes Zertifikat auf dem Pi löschen
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had \
  "sudo rm /etc/pi-daemon/certs/cert.pem /etc/pi-daemon/certs/key.pem"

# Neu deployen (generiert neues Zertifikat mit IP + DNS im SAN)
cd ansible && bash build_and_deploy.sh --install
```

---

## 📊 Versionsübersicht

| Komponente | Version |
|-----------|---------|
| Gesamt | 2.2.1 |
| `unified-monitor-client` | 2.2.1 |
| `raspberry-pi-scripts` | 2.2.1 |
| `scripts/__version__.py` | 2.2.1 |
