# 📈 Release v2.5.0 - Web-GUI, Player & Monitoring

**Release Date:** 12. November 2026  
**Version:** 2.5.0  
**Vorgänger:** [v2.4.2](../v2.4.2/RELEASE_NOTES_v2.4.2.md)

---

## ⚡ Erkennung läuft nach einer Aufnahme sofort weiter

Bisher blieb die Kamera nach jeder Aufnahme blind, bis Zeitlupen-Konvertierung und rsync-Transfer
fertig waren – bei einem nicht erreichbaren Sync-Ziel mindestens 10 Sekunden pro Ziel, bei großen
Dateien deutlich länger. Konvertierung und Transfer laufen jetzt in einem eigenen
Nachbearbeitungs-Thread; die Erkennung startet, sobald `rpicam-vid` fertig ist.

## 🖥 Web-GUI

- **▶ Abspielen:** Videos und Audio-Aufnahmen direkt im Browser ansehen
- **Neue Anordnung:** Zustand und Steuerung oben, „System & Hardware“ einklappbar;
  Aufnahmeliste auf dem Handy als Karten
- **Dauer-Regler:** 10 s bis 10 min (vorher mindestens 1 Minute, Anzeige teils falsch)
- **Ein Knopf** für Detection-Modus starten/stoppen; Ruhezustände grau statt rot
- **Hinweis bei Verbindungsverlust**, veraltete Werte werden abgedunkelt
- **„Objekt erkannt“** bleibt nach Neustarts stehen und zeigt zusätzlich, was die Kamera gerade
  sieht, wenn es unter der Schwelle liegt – so ist klar, ob die Confidence zu hoch eingestellt ist
- **Weniger Last** auf Pi und Netz: Aufnahmeliste nur bei Änderung, Pause im Hintergrund-Tab,
  Logo 1,2 MB → 20 KB, gzip
- **Strikte CSP** (`script-src 'self'`): GUI aufgeteilt in `index.html`, `app.js`, `app.css`

## 📈 Monitoring (optional)

- **`/metrics`** liefert Akku, Temperaturen, Erkennungen, Speicher und Systemlast im
  Prometheus-Format – mit eigenem, nur lesendem Token (`PI_METRICS_TOKEN`)
- **Prometheus + Grafana direkt auf dem Pi** mit fertigem Dashboard „Vogel-Kamera“ – zwei Zeilen
  in `ansible/.env` (`PI_MONITORING=true`, `PI_GRAFANA_ADMIN_PASSWORD=…`), den Rest erledigt die
  neue Ansible-Rolle `monitoring`
- Alternativ auf einem anderen Rechner im Heimnetz: [`monitoring/`](../../monitoring/)
- **Knopf „📈 Monitoring“** in der Web-GUI, sobald das Monitoring eingerichtet ist

Einrichtung: [monitoring/README.md](../../monitoring/README.md)

## 🔧 Bug Fixes

- Profil-Bitrate (8/12/25 Mbit/s) galt nur für Zeitlupe, nicht für normale Aufnahmen.
  **Achtung:** Dateigrößen normaler Aufnahmen ändern sich dadurch
- Auto-Convert konnte eine noch laufende Zeitlupen-Aufnahme konvertieren und das halbe Video übertragen
- Logdateien im tmpfs wuchsen unbegrenzt – jetzt mit Rotation
- Im Detection-Log fehlte die Zeile „Erkannt!“ mit Klasse und Confidence der Auslösung
- Einstellungsdateien werden atomar geschrieben (kein halbes JSON nach Akku-Abschaltung)

## ⚙️ Neue Einstellungen (alle optional, in `ansible/.env` bzw. `group_vars`)

| Einstellung | Wirkung | Standard |
|---|---|---|
| `PI_MONITORING` + `PI_GRAFANA_ADMIN_PASSWORD` | Prometheus + Grafana auf dem Pi | aus |
| `PI_METRICS_TOKEN` | schaltet `/metrics` ein (nur für Monitoring auf anderem Rechner nötig) | leer = aus |
| `PI_GRAFANA_URL` | Knopf „Monitoring“ für ein Grafana auf anderem Rechner | leer |
| `pi_min_free_gb` | älteste Aufnahmen löschen, wenn weniger GB frei sind | `0` = aus |

## 🔄 Update

```bash
./ansible/build_and_deploy.sh --update
```

Ein voller Build ist nötig (geänderte Detection-Skripte im Image). Der Hotpatch kopiert ab dieser
Version das ganze `web/`-Verzeichnis.

## 🧪 Tests

60 neue Tests (120 gesamt): Aufnahme-Ablauf, Web-GUI und Download-Tickets, Prometheus-Endpunkt.
