"""Protokoll der Auslösungen im Detection-Modus – für die Auswertung in Grafana.

Jede Auslösung (Vogel erkannt → Aufnahme) wird als eine JSON-Zeile in
config.DETECTION_LOG_FILE angehängt: Zeitpunkt, Klasse, Confidence. Die Datei liegt
unter /config und übersteht damit Container-Neustarts; Einträge älter als
config.DETECTION_LOG_DAYS werden beim Schreiben entfernt.

/metrics liest daraus Kennzahlen (Aktivität nach Uhrzeit, Confidence-Verteilung). Die
Auswertung wird gecacht, bis sich die Datei ändert.
"""
import json
import threading
import time
from datetime import datetime
from pathlib import Path

from . import config
from .config import logger

_lock = threading.Lock()
_cache: dict = {'key': None, 'entries': []}

# Confidence-Klassen für die Verteilung: 0.50, 0.55, … 0.95 (jeweils bis unter die nächste)
_BIN_WIDTH = 0.05


def _read_entries() -> list:
    try:
        lines = Path(config.DETECTION_LOG_FILE).read_text().splitlines()
    except OSError:
        return []
    entries = []
    for line in lines:
        try:
            e = json.loads(line)
            entries.append({'ts': float(e['ts']), 'class': str(e.get('class', 'bird')),
                            'conf': None if e.get('conf') is None else float(e['conf'])})
        except (ValueError, KeyError, TypeError):
            continue
    return entries


def append(cls: str, conf, ts: float = None) -> None:
    """Hängt eine Auslösung an und entfernt dabei veraltete Einträge."""
    ts = time.time() if ts is None else ts
    cutoff = ts - config.DETECTION_LOG_DAYS * 86400
    with _lock:
        try:
            entries = [e for e in _read_entries() if e['ts'] >= cutoff]
            entries.append({'ts': round(ts, 1), 'class': cls,
                            'conf': None if conf is None else round(float(conf), 3)})
            path = Path(config.DETECTION_LOG_FILE)
            tmp = path.with_suffix('.tmp')
            tmp.write_text(''.join(json.dumps(e) + '\n' for e in entries))
            tmp.replace(path)
        except Exception as exc:   # Protokoll ist Komfort – darf die Aufnahme nie stören
            logger.warning('Erkennungs-Protokoll nicht geschrieben: %s', exc)


def record_trigger(last_detection: dict) -> None:
    """Übernimmt die Auslösung, die das Detection-Skript gerade geschrieben hat.
    Ist last-detection.json veraltet oder fehlt, wird nur der Zeitpunkt protokolliert."""
    cls, conf = 'bird', None
    if isinstance(last_detection, dict):
        try:
            when = datetime.strptime(f"{last_detection['date']} {last_detection['time']}",
                                     '%Y-%m-%d %H:%M:%S').timestamp()
            if abs(time.time() - when) <= 120:
                cls = str(last_detection.get('class') or 'bird')
                conf = last_detection.get('conf')
        except (KeyError, ValueError, TypeError):
            pass
    append(cls, conf)


def _entries() -> list:
    """Einträge aus der Datei, gecacht bis sich Größe oder Änderungszeit ändern."""
    try:
        st = Path(config.DETECTION_LOG_FILE).stat()
        key = (st.st_size, st.st_mtime_ns)
    except OSError:
        return []
    with _lock:
        if _cache['key'] != key:
            _cache.update(key=key, entries=_read_entries())
        return _cache['entries']


def stats(now: float = None) -> dict:
    """Kennzahlen für /metrics.

    by_hour:   Auslösungen der letzten 7 Tage je Stunde des Tages (Ortszeit), alle 24 Stunden
    conf_bins: Confidence-Verteilung der letzten 7 Tage ({'0.85': n, …})
    """
    now = time.time() if now is None else now
    entries = _entries()
    week = [e for e in entries if now - 7 * 86400 <= e['ts'] <= now]
    by_hour = {f'{h:02d}': 0 for h in range(24)}
    conf_bins: dict = {}
    for e in week:
        by_hour[datetime.fromtimestamp(e['ts']).strftime('%H')] += 1
        if e['conf'] is not None:
            b = int(min(max(e['conf'], 0.0), 0.999) / _BIN_WIDTH) * _BIN_WIDTH
            key = f'{b:.2f}'
            conf_bins[key] = conf_bins.get(key, 0) + 1
    last = max(entries, key=lambda e: e['ts']) if entries else None
    return {
        'count_24h': sum(1 for e in week if e['ts'] >= now - 86400),
        'count_7d':  len(week),
        'by_hour':   by_hour,
        'conf_bins': conf_bins,
        'last_ts':   last['ts'] if last else None,
        'last_conf': last['conf'] if last else None,
    }
