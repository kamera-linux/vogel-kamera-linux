# 🚀 Release v2.3.0 — NPU Throttle-Level · Dashboard Stats · Favicon

**Datum:** 5. April 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAT+ · Debian Trixie (13) · Docker Container

---

## 📋 Executive Summary

**v2.3.0** erweitert das Web-Dashboard um mehrere neue Monitoring-Kacheln, verbessert die NPU-Anzeige erheblich und poliert das UI mit einem Browser-Favicon.

---

## 🔬 NPU Throttle-Level Anzeige

Bisher zeigte das Dashboard nur die abstrakte „Throttle-Zone" (0–2). Ab v2.3.0 erscheint stattdessen der **Throttle-Level** mit Taktfrequenz:

| Anzeige | Bedeutung | Takt |
|---------|-----------|------|
| `– Normal` (grün) | Normalbetrieb, kein Throttling | 400 MHz |
| `L0` (orange) | Aktiviert bei ≥ 104 °C | 350 MHz |
| `L1` (rot) | Aktiviert bei ≥ 108 °C | 300 MHz |
| `L2` (rot) | Aktiviert bei ≥ 112 °C | 250 MHz |
| `L3` (rot) | Aktiviert bei ≥ 116 °C | 200 MHz |

**Technisch:** Das `_HAILO_TEMP_SCRIPT` liest `_get_health_information().current_temperature_throttling_level` aus der Hailo-Python-API (`/usr/lib/python3/dist-packages/hailo_platform`).

> **Hinweis:** Eine NPU-Auslastung in Prozent ist auf dem Hailo-8 AI HAT+ hardwarebedingt nicht verfügbar (`Current Monitoring: Disabled`).

---

## 📊 Neue Dashboard-Kacheln

Das Dashboard ist jetzt in **4 semantische Gruppen** gegliedert:

### 🎯 Kamera & Erkennung
_(unverändert)_

### 🔬 NPU
- **Temperatur** — Hailo-8 Chip-Temperatur (Ø TS0/TS1)
- **Takt** — aktueller NN-Core-Takt in MHz
- **Throttle-Level** — `– Normal` / `L0`–`L3` mit aktueller Frequenz *(neu: Level + MHz)*

### 🖥️ System
- **CPU** — Auslastung in %
- **Temp CPU** — BCM2712 Kerntemperatur
- **Load Avg** — 1-Minuten-Systemlast
- **Uptime** *(neu)* — Betriebszeit seit letztem Neustart (z. B. `2 Tage 14:32`)
- **RAM genutzt** — physischer Speicher
- **Container RAM** *(neu)* — RSS-Speicher des `pi-daemon`-Prozesses
- **Freier Speicher** — freier Speicher auf der SD-Karte

### 🌐 Netzwerk *(neu)*
- **Empfangen** — kumulativer eingehender Netzwerkdurchsatz seit Boot
- **Gesendet** — kumulativer ausgehender Netzwerkdurchsatz seit Boot

---

## 🌐 Browser Favicon / Tray-Icon

Das vorhandene `logo.png` wird jetzt als Browser-Tab-Icon eingebunden:

```html
<link rel="icon" type="image/png" href="/web/logo.png">
<link rel="apple-touch-icon" href="/web/logo.png">
```

- Standard-Browser zeigen das Vogel-Kamera-Logo im Tab an
- iOS/Safari: beim Hinzufügen der Seite zum Homescreen wird `logo.png` als App-Icon verwendet
- Kein separates `.ico`-File nötig

---

## ❓ Online-Hilfe überarbeitet

Das Hilfe-Modal (`?`-Button) wurde vollständig neu strukturiert und spiegelt jetzt die 4 Dashboard-Gruppen wider:

- **🎯 Kamera & Erkennung** — Detection, Modus, Hailo-8 NPU, Erkennungsziel, Objekt erkannt, Aufnahmen heute, Recording
- **🔬 NPU** — Temperatur (Farbschwellen), Takt (400 MHz normal), Throttle-Level (L0–L3 mit Temperaturen und MHz)
- **🖥️ System** — CPU, Temp CPU, Load Avg, **Uptime**, RAM, **Container RAM**, Freier Speicher
- **🌐 Netzwerk** — Empfangen, Gesendet

Veralteter Eintrag „Leistungsaufnahme" entfernt.

---

## 🔧 Technische Details

### Backend (`pi_daemon_secure.py`)

**`_HAILO_TEMP_SCRIPT`** — jetzt 5 CSV-Felder:
```
temp_avg, nn_clock_mhz, throttle_active(0/1), throttle_zone(0-2), throttle_level(-1 to 3)
```

**Neu gecachte Felder:** `throttle_level`, `uptime_seconds`, `container_ram_mb`, `net_recv_mb`, `net_sent_mb`

### Frontend (`web/index.html`)

- `s-throttle` zeigt `– Normal` (grün) oder `L{n} {MHz} MHz` (orange/rot)
- Neue IDs: `s-uptime`, `s-container-ram`, `s-net-recv`, `s-net-sent`
- 4 Gruppen-Struktur mit Trennlinien

---

## 📁 Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `unified-monitor-client/pi_daemon_secure.py` | `_HAILO_TEMP_SCRIPT` (5 Felder), neue Cache-Keys, neue API-Felder |
| `unified-monitor-client/web/index.html` | Throttle-Level-JS, 4 Gruppen, neue Kacheln, Favicon, Hilfe-Modal |
| `unified-monitor-client/VERSION` | 2.3.0 |
| `raspberry-pi-scripts/VERSION` | 2.3.0 |
| `VERSION` | 2.3.0 |
| `scripts/__version__.py` | 2.3.0 |
| `scripts/version.py` | 2.3.0 |
| `CHANGELOG.md` | v2.3.0 Eintrag |

---

## ⬆️ Upgrade

```bash
# Hotpatch (Dateien direkt in laufenden Container)
cd ansible && python3 build_and_deploy.py --hotpatch

# Oder vollständiges Update mit neuem Image
cd ansible && python3 build_and_deploy.py --update
```

---

*Vogel-Kamera-Linux v2.3.0 · Raspberry Pi 5 + Hailo-8 AI HAT+ · Debian Trixie · Docker*
