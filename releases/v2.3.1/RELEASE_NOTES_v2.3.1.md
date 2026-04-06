# 🐛 Release v2.3.1 — Hailo-Deadlock-Fix · Container-Status-Kachel

**Datum:** 6. April 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAT+ · Debian Trixie (13) · Docker Container

---

## 📋 Executive Summary

**v2.3.1** behebt einen kritischen Deadlock-Bug, der den Web-Server einfrieren ließ, sobald `/dev/hailo0` durch einen laufenden Detection-Prozess blockiert war. Zusätzlich wurde eine neue Dashboard-Kachel „Container Status" eingeführt, die den Health-Status des Docker-Containers in Echtzeit anzeigt.

---

## 🐛 Bugfix: Hailo-Temp Deadlock (kritisch)

### Symptom
Der Web-Server (`pi-daemon`) fror vollständig ein:
- Keine API-Antworten mehr, alle HTTP-Requests hingen
- Docker-Container wurde als `unhealthy` markiert
- 20+ hängende `python3`-Prozesse akkumulierten sich
- Trat auf, solange `rpicam-hello` den Detection-Modus lief

### Ursache
Das `_HAILO_TEMP_SCRIPT` rief `Device()` aus der `hailo_platform`-Bibliothek auf. Wenn `rpicam-hello` bereits `/dev/hailo0` hielt, ging `Device()` in **D-State** (Uninterruptible Sleep):

```
PID    STATE  COMMAND
41951  S      rpicam-hello (hat /dev/hailo0 offen)
12345  D      python3 -c _HAILO_TEMP_SCRIPT  ← wartet auf Device()
```

`subprocess.run(..., timeout=10)` schickte SIGKILL — aber D-State-Prozesse ignorieren SIGKILL. Danach blockierte `communicate()` ewig im HTTP-Request-Thread. Alle weiteren Requests wurden serialisiert und froren ebenfalls ein.

### Fix
Das Hailo-Temp-Fetching wurde vollständig aus dem HTTP-Request-Thread entfernt und in einen **Background-Daemon-Thread** ausgelagert:

```python
# Neuer Daemon-Thread (startet einmalig beim Container-Start)
def _hailo_temp_updater() -> None:
    """Aktualisiert Hailo-Temp/Clock/Throttle im Hintergrund alle 30 s."""
    while True:
        time.sleep(_HAILO_TEMP_INTERVAL)
        proc = subprocess.Popen(
            ['python3', '-c', _HAILO_TEMP_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            start_new_session=True,          # eigene Prozessgruppe
        )
        try:
            stdout, _ = proc.communicate(timeout=12)
            # Ergebnis in _hailo_temp_bg dict schreiben (via Lock)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, 9)           # kein zweites communicate()!
```

**Schlüsselmerkmale:**
- `start_new_session=True`: subprocess läuft in eigener Prozessgruppe → `killpg` killt die gesamte Gruppe
- **Kein zweites `communicate()`** nach `TimeoutExpired` → verhindert erneutes Blockieren
- HTTP-Handler liest nur noch aus dem `_hailo_temp_bg`-Dict (nie blockierend)
- Beim ersten API-Aufruf nach Container-Start zeigt Dashboard `–` bis der erste 30s-Zyklus abgeschlossen ist

---

## ✨ Feature: Container-Status-Kachel

Eine neue Kachel **„Container Status"** wurde im System-Bereich des Dashboards ergänzt:

| Zustand | Anzeige | Bedeutung |
|---------|---------|-----------|
| API antwortet | `✓ Healthy` (grün) | Container läuft normal |
| API nicht erreichbar | `✗ Unhealthy` (rot) | Verbindung unterbrochen / Container down |

**Technische Umsetzung:**
- HTML-Kachel mit `id="s-health"` nach der „Freier Speicher"-Kachel
- `fetchStatus()` ruft `/api/status` auf und setzt den Kachel-Inhalt
- `apiFetch()` wurde um `try/catch` erweitert: bei Netzwerkfehler wird `null` zurückgegeben (kein unbehandelter Promise-Rejection-Fehler mehr)
- Kachel zeigt `–` bis zum ersten erfolgreichen API-Aufruf

---

## 🔧 Geänderte Dateien

- `unified-monitor-client/pi_daemon_secure.py`
  - `_hailo_temp_bg`, `_hailo_temp_bg_lock`, `_HAILO_TEMP_INTERVAL` (neu)
  - `_hailo_temp_updater()` — Background-Thread-Funktion (neu)
  - `_get_hailo_hw_info()` — liest nur noch aus `_hailo_temp_bg` (kein Subprocess mehr)
  - Daemon-Thread-Start nach Watchdog-Thread
  - `APP_VERSION` → `'2.3.1'`
- `unified-monitor-client/web/index.html`
  - Neue Kachel „Container Status" (`id="s-health"`)
  - `fetchStatus()` — Health-Kachel-Logik
  - `apiFetch()` — `try/catch` für Netzwerkfehler
- `VERSION`, `raspberry-pi-scripts/VERSION`, `unified-monitor-client/VERSION` → `2.3.1`
- `scripts/__version__.py`, `scripts/version.py` → `2.3.1`

---

## 🚀 Upgrade

```bash
# Hotpatch (kein Container-Rebuild nötig)
cd ansible && python3 build_and_deploy.py --hotpatch
```

Oder vollständiger Re-Deploy:

```bash
cd ansible && python3 build_and_deploy.py
```

---

## ⬆️ Migration von v2.3.0

Keine Konfigurationsänderungen erforderlich. Das Hotpatch-Verfahren reicht aus.

---

**Vorherige Version:** [v2.3.0](../v2.3.0/RELEASE_NOTES_v2.3.0.md)
