"""Health-Cache, Gotify-Alerts, Thread-Diagnose."""
import os
import sys
import threading
import time
import traceback
import faulthandler
from datetime import datetime
from pathlib import Path

import psutil

from . import config
from .config import logger


# ---------------------------------------------------------------------------
# Thread-Monitoring und Deadlock-Erkennung
# ---------------------------------------------------------------------------
_thread_state: dict = {}                    # {thread_name: {state: str, started_at: float, lock_acquired: bool}}
_thread_state_lock = threading.Lock()
_last_thread_dump_time: float = 0.0
_THREAD_DUMP_INTERVAL: float = 30.0         # Sekunden zwischen Thread-Dumps (nur im Fehlerfall)

def _send_gotify_alert(status: str, reason: str) -> None:
    """Sendet Alert an Gotify Server wenn Container unhealthy wird.
    
    Gotify ist eine selbst-gehostete, open-source Alert-Plattform.
    Konfiguration über Umgebungsvariablen:
      GOTIFY_URL: URL zum Gotify Server (z.B. http://192.168.178.36:8080)
      GOTIFY_TOKEN: API Token (generiert im Gotify Dashboard)
    """
    if not config.GOTIFY_URL or not config.GOTIFY_TOKEN:
        return
    
    try:
        import requests
        url = f'{config.GOTIFY_URL.rstrip("/")}/message'
        headers = {'Authorization': f'Bearer {config.GOTIFY_TOKEN}'}
        data = {
            'title': f'🚨 pi-daemon {status}',
            'message': reason,
            'priority': 10 if status == 'unhealthy' else 5
        }
        resp = requests.post(url, json=data, headers=headers, timeout=5)
        if resp.status_code in (200, 201):
            logger.info(f'Gotify-Alert gesendet: {status}')
        else:
            logger.warning(f'Gotify-Alert fehlgeschlagen (HTTP {resp.status_code}): {resp.text[:200]}')
    except Exception as exc:
        logger.warning(f'Gotify-Alert Exception: {exc}')


def _log_thread_status(label: str = "Thread-Status", critical: bool = False) -> None:
    """Logged den Status aller Threads (für Deadlock-Diagnostik)."""
    global _last_thread_dump_time
    now = time.monotonic()
    if not critical and (now - _last_thread_dump_time < _THREAD_DUMP_INTERVAL):
        return
    _last_thread_dump_time = now
    
    msg_lines = [f"\n{'='*70}"]
    msg_lines.append(f"{label} ({datetime.now().isoformat()})")
    msg_lines.append(f"PID: {os.getpid()}, Active Threads: {threading.active_count()}")
    msg_lines.append("-" * 70)
    
    for tid, frame in sys._current_frames().items():
        thread = next((t for t in threading.enumerate() if t.ident == tid), None)
        thread_name = thread.name if thread else f"unknown-{tid}"
        
        # Stack Trace ausgeben
        stack_str = ''.join(traceback.format_list(traceback.extract_stack(frame)))
        msg_lines.append(f"\n[{thread_name}] TID={tid}")
        for line in stack_str.split('\n')[-5:]:  # Letzten 5 Stack-Frames
            if line.strip():
                msg_lines.append(f"  {line}")
    
    msg_lines.append(f"\n{'='*70}")
    full_msg = '\n'.join(msg_lines)
    
    if critical:
        logger.error(full_msg)
    else:
        logger.debug(full_msg)


# ── Health-Cache (für /api/health, OHNE Auth für Docker) ─────────────────────

_last_health_response: dict = {
    'version': config.APP_VERSION,
    'status': 'ok',
    'system': {},
    'cached_at': 0.0,
}
_last_health_response_lock = threading.Lock()
_HEALTH_CACHE_TTL: float = 2.0  # Sekunden – Cache Health-Response, um Blocking zu vermeiden

# Alert-Tracking für WhatsApp
_consecutive_health_failures: int = 0
_last_alert_time: float = 0.0
_ALERT_THRESHOLD: int = 5  # Consecutive Failures bevor Alert
_ALERT_COOLDOWN: float = 300.0  # Sekunden zwischen Alerts (5 Minuten)

def _update_health_cache() -> None:
    """Aktualisiert den Health-Cache im Hintergrund (wird von daemon aufgerufen)."""
    global _last_health_response, _consecutive_health_failures, _last_alert_time
    try:
        start = time.monotonic()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(config.VIDEO_BASE_DIR if Path(config.VIDEO_BASE_DIR).exists() else '/')
        elapsed = time.monotonic() - start
        
        system = {
            'mem_used_mb': round(mem.used / 1_048_576),
            'mem_total_mb': round(mem.total / 1_048_576),
            'disk_free_gb': round(disk.free / 1_073_741_824, 1),
        }
        
        if elapsed > 0.5:
            logger.warning(f'Health-Cache-Update dauerte {elapsed:.2f}s (psutil blockiert?)')
            _log_thread_status("psutil blockiert Health-Check", critical=True)
        
        with _last_health_response_lock:
            _last_health_response = {
                'version': config.APP_VERSION,
                'status': 'ok',
                'system': system,
                'cached_at': time.monotonic(),
                'threads_active': threading.active_count(),
            }
            _consecutive_health_failures = 0  # Reset bei Erfolg
    except Exception as exc:
        logger.error(f'Health-Cache-Update fehlgeschlagen: {exc}')
        _consecutive_health_failures += 1
        
        # Sende Gotify-Alert wenn zu viele Fehler hintereinander
        now = time.monotonic()
        if _consecutive_health_failures >= _ALERT_THRESHOLD and (now - _last_alert_time) > _ALERT_COOLDOWN:
            _send_gotify_alert('unhealthy', f'Health-Cache konnte {_consecutive_health_failures}x nicht aktualisiert werden: {exc}')
            _last_alert_time = now
        
        with _last_health_response_lock:
            _last_health_response['status'] = 'warn'
            _last_health_response['error'] = str(exc)


def _thread_monitor_daemon():
    """Monitort Thread-Status und aktualisiert Health-Cache regelmäßig."""
    faulthandler.enable()  # Stacktrace auf SIGUSR1
    while True:
        try:
            time.sleep(2)  # Alle 2 Sekunden
            _update_health_cache()

            # Prüfe ob Threads blockiert sind (vereinfachte Heuristik)
            active = threading.active_count()
            if active > 50:  # Zu viele Threads?
                logger.warning(f'Viele aktive Threads: {active} (möglicher Thread-Leak?)')
                _log_thread_status("Zu viele Threads", critical=False)
        except Exception as exc:
            logger.debug(f'Thread-Monitor-Fehler: {exc}')
