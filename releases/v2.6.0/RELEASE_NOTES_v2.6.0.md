# 🔌 Release v2.6.0 - Strom- & WLAN-Monitoring

**Release Date:** 16. November 2026  
**Version:** 2.6.0  
**Vorgänger:** [v2.5.1](../v2.5.1/RELEASE_NOTES_v2.5.1.md)

---

## Warum

In den Tagen nach v2.5.1 brach das WLAN immer wieder ab. Der neue Watchdog fing das ab, die
Ursache blieb aber unsichtbar: **Unterspannung**. Der Pi meldete bis zu 98-mal pro Boot
`Undervoltage detected!` – das Kabel zur Powerbank war zu schwach. Nach dem Kabeltausch am
16.11. verschwanden die Meldungen im Normalbetrieb. Damit so etwas künftig sofort auffällt, zeigt
das Dashboard jetzt Stromversorgung und WLAN.

---

## 🔌 Stromversorgung

| Panel | Inhalt |
|---|---|
| Versorgungsspannung Pi | Spannung am USB-C-Eingang (PMIC), Warnlinien bei 4,63 V und 4,8 V |
| Unterspannung jetzt / seit Boot | aus `vcgencmd get_throttled` |
| Unterspannungs-Meldungen 24 h | Kernel-Meldungen `Undervoltage detected!` |
| Neustarts (7 Tage) | Updates, Watchdog, Stromausfall |
| Leistung je Anschluss | welcher Port der Powerbank wie viel liefert |

**Restlaufzeit:** jetzt in Stunden statt „1.07 days“. Die Powerbank meldet nach dem Anstecken eine
Weile 100 %, obwohl sie schon entlädt. Diese Phase fließt nicht mehr in die Hochrechnung ein –
vorher kamen z. B. 24 h statt realistischer 16 h heraus. Farben: rot unter 6 h, orange ab 6 h,
grün ab 12 h.

---

## 📶 WLAN

| Panel | Inhalt |
|---|---|
| WLAN-Signal | Empfangspegel in dBm, Warnlinien bei −70 und −80 dBm |
| WLAN-Watchdog-Eingriffe | pro Stunde: Router weg, Reconnect, Treiber neu geladen |
| WLAN-Ausfälle 24 h | wie oft der Router nicht erreichbar war |

---

## 🐦 Erkennungen

Jede Auslösung im Detection-Modus landet in `/etc/pi-daemon/detection-log.jsonl` (Zeit, Klasse,
Confidence; die letzten 30 Tage).

| Panel | Inhalt |
|---|---|
| Aktivität nach Uhrzeit (7 Tage) | wann die Vögel kommen |
| Confidence der Auslösungen (7 Tage) | viele Werte knapp über der Schwelle → Fehlauslösungen? |
| Auslösungen 24 h / 7 Tage, Schwelle, Letzte Confidence | Kennzahlen |

Arten unterscheidet die Erkennung nicht: Das Modell (YOLOv8/COCO) kennt nur „bird“.

Außerdem neu: **Lüfter**, **NPU-Takt** und **Letzter Fehler**.

---

## 🛠 Technik

- Spannung, Unterspannung, WLAN und Watchdog kann der Container nicht selbst lesen (eigenes Netz,
  kein `vcgencmd`). Das neue Host-Skript `/usr/local/bin/host-status.py` schreibt sie jede Minute
  (`host-status.timer`) nach `/run/vogelkamera/host-status.json` – im RAM, ohne Schreiblast auf
  der SD-Karte. Im Container ist der Ordner schreibgeschützt unter `/host-status` eingebunden.
- `wlan-watchdog.sh` zählt seine Eingriffe unter `/run/vogelkamera/wlan-watchdog/`
- Neue Messwerte: `vogelkamera_power_supply_volts`, `_undervoltage_*`, `_throttled_*`,
  `_wifi_*`, `_wlan_watchdog_actions_total`, `_fan_rpm`, `_detections_*`, `_detection_last_*`
  (Übersicht in [MONITORING.md](../../MONITORING.md))

9 neue Tests (134 gesamt).

---

## 🚀 Update

```bash
./ansible/build_and_deploy.sh --update
```

Das Update ändert die Host-Rolle und das Compose-File; der Container startet neu. Die Panels zu
Erkennungen und Watchdog füllen sich ab dem Update.
