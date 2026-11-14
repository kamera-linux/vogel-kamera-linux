# 📡 Release v2.5.1 - WLAN-Watchdog & Auto-Updates

**Release Date:** 14. November 2026  
**Version:** 2.5.1  
**Vorgänger:** [v2.5.0](../v2.5.0/RELEASE_NOTES_v2.5.0.md)

---

## 🔧 Bug Fixes

**WLAN kam nach einem Abbruch nicht wieder:** Am 14.11. trennte der WLAN-Chip des Pi die
Verbindung von sich aus. Alle Wiederverbindungen scheiterten mit `ASSOC-REJECT status_code=16`,
danach gab NetworkManager mit `no-secrets` auf und sperrte das automatische Verbinden
**dauerhaft**. Die Kamera war über eine Stunde offline, bis sie aus- und wieder eingeschaltet
wurde. Der vorhandene WLAN-Watchdog hätte das abfangen sollen, lief aber nie: Der Timer war aus,
und dem Skript fehlte die Shebang-Zeile.

Der neue Watchdog prüft jede Minute, ob der Router erreichbar ist, und geht stufenweise vor:

1. Verbindung mit `nmcli connection up` neu aufbauen (hebt auch die `no-secrets`-Sperre auf)
2. ab dem 2. Fehlschlag in Folge: WLAN-Treiber `brcmfmac` neu laden
3. nach 30 Minuten ohne Netz: Neustart

Jeder Schritt steht im Systemlog: `journalctl -t wlan-watchdog`.

**Powerbank dauerhaft „nicht erreichbar“** nach einem Container-Neustart mitten in einer
Bluetooth-Abfrage: Der Daemon trennt eine hängende Verbindung jetzt selbst (#50).

**Web-GUI:** Die Knöpfe der Aufnahmeliste bleiben bei langen Dateinamen in einer Zeile (#49).

---

## 🛠 Automatische Updates beim Systemstart

Die Kamera läuft nur tagsüber, deshalb gibt es keinen nächtlichen Update-Zeitplan. Stattdessen
beim Einschalten, **bevor Docker startet**:

| Schritt | Was passiert |
|---|---|
| `boot-update` | Paketlisten holen, Updates installieren (unattended-upgrades) – höchstens alle 6 h, ohne Netz nach 2 min übersprungen. Verlangt ein Update einen Neustart, startet der Pi sofort neu |
| `boot-health-check` | Paketsystem in Ordnung, neuester Kernel aktiv, Hailo (`/dev/hailo0`), Kamera erkannt |
| Docker | startet nur, wenn die Boot-Prüfung bestanden ist |

- Automatisch aktualisiert wird alles aus Debian, Raspberry Pi und Docker – **außer gesperrten
  Paketen**: Docker bleibt auf 29.6.0 (nach Problemen mit einem früheren Docker-Update, siehe
  `ansible/roles/docker/tasks/main.yml`), Hailo muss zur Treiberversion im Kernel passen
- Updates, die Pakete entfernen müssten (z. B. libcamera 0.7 → 0.8), installiert
  unattended-upgrades grundsätzlich nicht von selbst
- Notausgänge auf dem Pi: `sudo touch /etc/vogelkamera/skip-boot-update` bzw.
  `/etc/vogelkamera/skip-boot-check`
- Logs: `journalctl -t boot-update`, `journalctl -t boot-health-check`

> ⚠️ Der pi-daemon-Container nutzt viele Bibliotheken direkt vom Host (libcamera, Python 3.13 …).
> Ob er nach einem Update läuft, zeigt im Dashboard die Kachel „Kamera“.

Alles zusammen richtet die neue Ansible-Rolle **`host-maintenance`** ein (bei `--install` und
`--update`). Ohne Kamera/Hailo (Test-Pi) `host_boot_check_gate: false` setzen, sonst startet
Docker dort nie.

---

## 📈 Grafana: Zeile „System-Updates“

| Kachel | Inhalt |
|---|---|
| Updates verfügbar / Sicherheits-Updates / Gesperrt (hold) | anstehende Updates |
| Neustart nötig | Ja/Nein |
| Boot-Prüfung | OK/Fehler |
| Kernel | laufende Version |
| Letzter Update-Lauf, Update-Lauf zuletzt, Zuletzt installiert | Ergebnis und Zeitpunkt |
| Paketlisten aktualisiert, Status-Alter | werden orange, wenn die Automatik hängt |

Neue Messwerte: `vogelkamera_os_*` und `vogelkamera_boot_check_*`. Der Host schreibt sie alle
15 Minuten nach `/etc/pi-daemon/update-status.json`, der Daemon liest die Datei (im Container
`/config/update-status.json`). Fehlt sie, fallen nur diese Werte weg.

3 neue Tests (126 gesamt).

---

## 🚀 Update

```bash
./ansible/build_and_deploy.sh --update
```

Danach Grafana neu laden – die neue Zeile steht ganz unten. „Letzter Update-Lauf“ füllt sich
nach dem nächsten Systemstart.
