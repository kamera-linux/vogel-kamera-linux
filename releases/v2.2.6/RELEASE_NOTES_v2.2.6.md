# 🐛 Release v2.2.6 - Bugfix: Detection-Prozess & Aufnahmen-Tageszähler

**Datum:** 31. März 2026  
**Status:** ✅ STABLE RELEASE  
**Kompatibilität:** Raspberry Pi 5 + Hailo-8 AI HAD+ · Debian Trixie (13) · Build-Host: Gentoo Linux (x86_64)

---

## 📋 Executive Summary

**v2.2.6** behebt einen kritischen Bug in der Detection-Steuerung und erweitert das Web-Dashboard um einen persistenten Aufnahmen-Tageszähler mit Datumesanzeige:

### 🐛 Bugfix: Doppelter Detection-Prozess
- **Problem:** Nach Stopp der Detection → manuelle Aufnahme → erneuter Aktivierung der Detection wurden zwei `rpicam-hello`-Prozesse gleichzeitig gestartet, die um die Kamera konkurrierten → beide crashten mit `rc=1`
- **Ursache:** `start_detection_mode()` startete neuen Prozess ohne den vorher durch die manuelle Aufnahme gestarteten Detection-Prozess zu beenden
- **Fix:** Explizites Killen eines laufenden Detection-Prozesses + 1s Wartezeit für libcamera-Freigabe vor dem Neustart

### ✨ Feature: Aufnahmen-Tageszähler im Dashboard
- **Neu:** Karte "Aufnahmen heute" zeigt die Anzahl der `.mp4`-Aufnahmen des aktuellen Tages
- **Persistent:** Zähler basiert auf Datei-mtime im Aufnahme-Verzeichnis – geht nach Container-Neustart nicht verloren
- **Datum:** Datum wird neben der Anzahl angezeigt (z. B. `15  Di 31.03.2026`)
- Ersetzt den instabilen session-basierten "Objekte aufgenommen"-Zähler

### 🚀 Ansible Hotpatch-Infrastruktur
- Neues Playbook `ansible/playbooks/hotpatch.yml` für schnellen Datei-Deployment ohne Image-Rebuild
- `build_and_deploy.py --hotpatch` – überspringt Docker-Build und überträgt direkt geänderte Dateien in den laufenden Container

---

## ✨ Geänderte Dateien

| Datei | Änderung |
|---|---|
| `unified-monitor-client/pi_daemon_secure.py` | Bugfix `start_detection_mode()` + `_count_today_recordings()` + API-Feld `today_recordings` |
| `unified-monitor-client/web/index.html` | "Aufnahmen heute"-Karte mit Datum-Anzeige (flexbox) |
| `ansible/playbooks/hotpatch.yml` | **NEU** – Schnell-Deployment ohne Image-Rebuild |
| `ansible/build_and_deploy.py` | `--hotpatch`-Argument hinzugefügt |
| `ansible/README.md` | Hotpatch-Dokumentation ergänzt |

---

## 🐛 Bugfix-Details: Detection-Prozess-Race-Condition

### Problematische Sequenz (vor v2.2.6)

```
1. Detection läuft  → PID=500, mode=True,  running=True
2. Detection stoppen → PID=500 gekillt, mode=False, running=False
3. Manuelle Aufnahme → startet Detection via start_detection()
                     → PID=707, mode=False, running=True    ← Problem!
4. Detection-Mode-Button →  start_detection_mode() prüft:
                             mode=False  → kein early-return
                             running=True → KEIN Kill!
                             startet PID=930 OHNE PID=707 zu beenden
5. PID=707 & PID=930 konkurrieren um Kamera → beide rc=1
```

### Fix in `start_detection_mode()`

```python
# Vorhandenen Detection-Prozess explizit beenden (kann noch laufen, z.B.
# nach manueller Aufnahme, die ihn via start_detection() neu gestartet hat).
if state.detection_running and state.detection_process:
    _kill_process_group(state.detection_process)
    state.detection_running = False
    state.detection_process = None
    time.sleep(1)   # libcamera-Freigabe abwarten
proc = CameraManager._launch_detection_process()
```

---

## ✨ Feature-Details: Aufnahmen-Tageszähler

### Neue Backend-Funktion `_count_today_recordings()`

```python
def _count_today_recordings() -> int:
    """Zählt Video-Aufnahmen im VIDEO_BASE_DIR die heute erstellt wurden."""
    today = datetime.now().strftime('%Y-%m-%d')
    base = Path(VIDEO_BASE_DIR)
    if not base.exists():
        return 0
    count = 0
    for f in base.rglob('*.mp4'):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d') == today:
                count += 1
        except OSError:
            pass
    return count
```

- `/api/status` liefert nun `today_recordings: <int>`

### Web-Dashboard HTML

```html
<div class="card">
  <div class="label">Aufnahmen heute</div>
  <div style="display:flex;align-items:baseline;gap:0.5rem">
    <div class="value" id="s-birds">–</div>
    <div style="font-size:0.75rem;color:var(--muted)" id="s-birds-date"></div>
  </div>
</div>
```

---

## 🚀 Ansible Hotpatch

### Neues Playbook `hotpatch.yml`

Kopiert geänderte Dateien direkt in den laufenden Docker-Container ohne Image-Rebuild:

```bash
cd ansible
source ~/ansible-venv/bin/activate
python3 build_and_deploy.py --hotpatch
```

---

## 🔄 Upgrade von v2.2.5

### Option A: Hotpatch (empfohlen für laufende Systeme)
```bash
cd ansible
source ~/ansible-venv/bin/activate
python3 build_and_deploy.py --hotpatch
```

### Option B: Vollständiges Image-Update
```bash
cd ansible
source ~/ansible-venv/bin/activate
python3 build_and_deploy.py --update
```

---

## 📦 Changelog

Vollständiger Changelog: [`CHANGELOG.md`](../../CHANGELOG.md)

---

*Erstellt am 31. März 2026*
