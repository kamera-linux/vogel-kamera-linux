"""Flask-App: Auth (Passwort + TOTP → JWT) und alle HTTP-Routen."""
import gzip
import hashlib
import hmac
import mimetypes
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import bcrypt
import jwt
import psutil
import pyotp
from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from . import config, metrics, monitoring, powerbank, settings
from .camera import (
    CameraManager, _kill_process_group, _read_last_detection, _read_seen_detection,
    invalidate_media_scan, media_summary,
)
from .config import logger
from .hailo import _get_hailo_hw_info
from .monitoring import _log_thread_status
from .runtime import _lock, state
from .settings import (
    DETECTION_ENGINES, RECORDING_PROFILES, _RESOLUTION_MAP, _load_rec_settings, _save_active_engine,
    _save_camera_settings, _save_detection_settings, _save_rec_settings,
)
from .sync import (
    _load_sync_settings, _save_sync_settings, ssh_options, validate_target, write_private_key,
)


# ---------------------------------------------------------------------------
# Flask-App
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder=None)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri='memory://',
)


# ── Security-Header ──────────────────────────────────────────────────────────
# Skripte kommen ausschließlich aus web/app.js – keine Inline-Skripte, keine
# onclick-Attribute. Eingeschleustes HTML kann damit keinen Code ausführen.
# Styles brauchen weiterhin 'unsafe-inline' (style-Attribute im Markup).
# Dazu: kein Datenabfluss an fremde Server (connect-src/img-src), kein Einbetten in Frames.
_CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; connect-src 'self'; media-src 'self' blob:; "
        "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")


@app.after_request
def _security_headers(resp):
    resp.headers.setdefault('Content-Security-Policy', _CSP)
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'DENY')
    resp.headers.setdefault('Referrer-Policy', 'no-referrer')
    resp.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
    if request.path.startswith('/api/'):
        resp.headers.setdefault('Cache-Control', 'no-store')
    return resp


def _int_arg(value, default: int) -> int:
    """int() für Request-Werte: ungültige Eingaben → Standardwert statt HTTP 500."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ── JWT-Helpers ─────────────────────────────────────────────────────────────

def _make_token(client_ip: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': 'admin',
        'iat': now,
        'exp': now + timedelta(hours=config.TOKEN_EXPIRY_H),
        'ip':  client_ip,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')


def require_auth(f):
    @wraps(f)
    def _inner(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            abort(401)
        try:
            claims = jwt.decode(auth[7:], config.JWT_SECRET, algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            abort(401)
        # Nur echte Login-Token. Download-Tickets (typ=file) sind mit demselben Secret
        # signiert, stehen aber in URLs – sie dürfen niemals als Login gelten.
        if claims.get('sub') != 'admin' or 'typ' in claims:
            abort(401)
        return f(*args, **kwargs)
    return _inner


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
@limiter.limit('5 per minute')
def api_login():
    data      = request.get_json(silent=True) or {}
    password  = (data.get('password') or '').encode('utf-8')
    totp_code = data.get('totp', '')

    pw_ok   = bool(config.PASSWORD_HASH) and bcrypt.checkpw(password, config.PASSWORD_HASH.encode('utf-8'))
    totp_ok = pyotp.TOTP(config.TOTP_SECRET).verify(totp_code, valid_window=1)

    if not pw_ok or not totp_ok:
        time.sleep(1)   # Brute-force-Abbremsung
        return jsonify({'error': 'Ungültige Anmeldedaten'}), 401

    token = _make_token(request.remote_addr)
    logger.info('Login von %s', request.remote_addr)
    return jsonify({'token': token, 'expires_in': config.TOKEN_EXPIRY_H * 3600})



# ── Health-Check (OHNE Auth für Docker) ─────────────────────────────────────────

@app.route('/api/health')
def api_health():
    """Unauthentifizierter Health-Check Endpoint für Docker Health-Check.
    
    Nutzt gecachte Systeminfo, um zu vermeiden dass psutil blockiert.
    Wenn Cache älter als TTL, wird 503 zurückgegeben (statt zu blockieren).
    """
    try:
        with monitoring._last_health_response_lock:
            now = time.monotonic()
            cache_age = now - monitoring._last_health_response.get('cached_at', 0)
            
            # Cache ist zu alt → lieber 503 als blockieren
            if cache_age > 5.0:
                logger.warning(f'Health-Check: Cache zu alt ({cache_age:.1f}s) – 503')
                _log_thread_status("Health-Check: Cache zu alt", critical=True)
                return jsonify({
                    'status': 'degraded',
                    'error': 'System-Info outdated (psutil blocked?)',
                    'version': config.APP_VERSION,
                }), 503
            
            response = monitoring._last_health_response.copy()
        
        return jsonify(response), 200
    except Exception as exc:
        logger.error(f'Health-Check Exception: {exc}')
        return jsonify({
            'status': 'error',
            'error': str(exc),
            'version': config.APP_VERSION,
        }), 500


# ── Prometheus-Metriken ───────────────────────────────────────────────────────

@app.route('/metrics')
def prometheus_metrics():
    """Messwerte im Prometheus-Textformat. Eigenes, nur lesendes Token statt Login:
    Prometheus kann kein 2FA, und das Token darf nichts steuern."""
    if not config.METRICS_TOKEN:
        abort(404)   # nicht eingerichtet → Endpunkt existiert nicht
    auth = request.headers.get('Authorization', '')
    given = auth[7:] if auth.startswith('Bearer ') else ''
    if not hmac.compare_digest(given.encode(), config.METRICS_TOKEN.encode()):
        abort(401)
    resp = Response(metrics.render(), mimetype='text/plain')
    resp.headers['Content-Type'] = 'text/plain; version=0.0.4; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-store'
    return resp


_net_io_prev: tuple = None   # (monotonic_time, bytes_recv, bytes_sent) für Netzwerk-Rate
psutil.cpu_percent(interval=None)   # Messung starten, damit der erste Status-Abruf einen Wert hat


# ── Status ────────────────────────────────────────────────────────────────────

@app.route('/api/status')
@require_auth
def api_status():
    try:
        cpu  = psutil.cpu_percent(interval=None)   # seit dem letzten Aufruf – blockiert nicht
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage(config.VIDEO_BASE_DIR if Path(config.VIDEO_BASE_DIR).exists() else '/')
        load = os.getloadavg()
        try:
            cpu_temp = round(int(Path('/sys/class/thermal/thermal_zone0/temp').read_text().strip()) / 1000.0, 1)
        except Exception:
            cpu_temp = None
        uptime_s = int(time.time() - psutil.boot_time())
        _ud, _ur = divmod(uptime_s, 86400)
        _uh, _um = divmod(_ur, 3600)
        system = {
            'cpu_percent':  cpu,
            'cpu_temp':     cpu_temp,
            'load_1min':    round(load[0], 2),
            'load_5min':    round(load[1], 2),
            'load_15min':   round(load[2], 2),
            'mem_used_mb':  round(mem.used   / 1_048_576),
            'mem_total_mb': round(mem.total  / 1_048_576),
            'disk_free_gb': round(disk.free  / 1_073_741_824, 1),
            'disk_total_gb': round(disk.total / 1_073_741_824, 1),
            'uptime_days':  _ud,
            'uptime_hours': _uh,
            'uptime_minutes': _um // 60,
        }
        try:
            system['container_ram_mb'] = round(psutil.Process().memory_info().rss / 1_048_576)
        except Exception:
            pass
        try:
            global _net_io_prev
            _nc = psutil.net_io_counters()
            _nt = time.monotonic()
            if _net_io_prev is not None:
                _pt, _pr, _ps = _net_io_prev
                _dt = _nt - _pt
                if _dt > 0.1:
                    system['net_rx_kbs'] = round((_nc.bytes_recv - _pr) / _dt / 1024, 1)
                    system['net_tx_kbs'] = round((_nc.bytes_sent - _ps) / _dt / 1024, 1)
            _net_io_prev = (_nt, _nc.bytes_recv, _nc.bytes_sent)
        except Exception:
            pass
    except Exception:
        system = {}

    media = media_summary()

    with _lock:
        rec_running  = state.recording_running
        rec_start    = state.recording_started_at
        rec_dur      = state.recording_duration_s
        aud_running  = state.audio_running
        aud_start    = state.audio_started_at
        aud_dur      = state.audio_duration_s

    # Fortschritt berechnen (0–100), None wenn keine Aufnahme läuft
    if rec_running and rec_dur > 0:
        elapsed  = time.monotonic() - rec_start
        progress = min(100, round(elapsed / rec_dur * 100))
        rec_remaining = max(0, rec_dur - int(elapsed))
    else:
        progress      = None
        rec_remaining = None

    # Fortschritt Audio-Only
    if aud_running and aud_dur > 0:
        elapsed_a     = time.monotonic() - aud_start
        aud_progress  = min(100, round(elapsed_a / aud_dur * 100))
        aud_remaining = max(0, aud_dur - int(elapsed_a))
    else:
        aud_progress  = None
        aud_remaining = None

    return jsonify({
        'detection_running':    state.detection_running,
        'detection_mode':       state.detection_mode,
        'birds_recorded':       state.birds_recorded,
        'today_recordings':     media['today'],
        'pending':              media['pending'],     # H264 ohne MP4
        'recordings_rev':       media['rev'],         # ändert sich mit der Aufnahmeliste
        'recording_running':    rec_running,
        'recording_progress':   progress,       # 0–100 oder null
        'recording_remaining':  rec_remaining,  # Sekunden verbleibend oder null
        'recording_duration':   rec_dur if rec_running else None,
        'audio_running':        aud_running,
        'audio_progress':       aud_progress,
        'audio_remaining':      aud_remaining,
        'audio_duration':       aud_dur if aud_running else None,
        'camera_hw_error':      state.camera_hw_error,
        'last_error':           state.last_error,
        'recording_file':       state.recording_file,
        'started_at':           state.started_at,
        'system':               system,
        'version':              config.APP_VERSION,
        'grafana_url':          config.GRAFANA_URL or None,   # Link „Monitoring" in der GUI
        'grafana_port':         config.GRAFANA_PORT or None,  # … oder Grafana auf diesem Pi
        'active_engine':        settings._active_engine,
        'detection_target':     settings._detection_target,
        'detection_threshold':  settings._detection_threshold,
        'last_detection':       _read_last_detection(),
        'seen_detection':       _read_seen_detection(),   # gerade gesehen, aber unter der Schwelle
        'hailo_hw':             _get_hailo_hw_info(),
        'powerbank':            powerbank.get_status(),
        'lens_position':        settings._lens_position,
        'ev':                   settings._ev,
        'awb':                  settings._awb,
        'brightness':           settings._brightness,
        'contrast':             settings._contrast,
        'saturation':           settings._saturation,
        'sharpness':            settings._sharpness,
        'gain':                 settings._gain,
    })


# ── Detection ────────────────────────────────────────────────────────────────

@app.route('/api/detection/start', methods=['POST'])
@require_auth
def api_detection_start():
    """Startet Detection ohne Detection-Modus (einfache Einzelerkennung)."""
    ok = CameraManager.start_detection()
    return jsonify({'success': ok})


@app.route('/api/detection/stop', methods=['POST'])
@require_auth
def api_detection_stop():
    ok = CameraManager.stop_detection()
    return jsonify({'success': ok})


@app.route('/api/detection/mode/start', methods=['POST'])
@require_auth
def api_detection_mode_start():
    """Aktiviert Detection-Modus: bei Vogelerkennung automatisch aufnehmen + weiter."""
    ok = CameraManager.start_detection_mode()
    if not ok:
        with _lock:
            msg = 'Aufnahme läuft gerade' if state.recording_running else 'Unbekannter Fehler'
        return jsonify({'success': False, 'error': msg}), 409
    return jsonify({'success': True, 'detection_mode': True})


@app.route('/api/detection/mode/stop', methods=['POST'])
@require_auth
def api_detection_mode_stop():
    """Beendet Detection-Modus und stoppt die Detection."""
    ok = CameraManager.stop_detection_mode()
    return jsonify({'success': ok, 'detection_mode': False, 'birds_recorded': state.birds_recorded})


# ── Aufnahme-Profile ──────────────────────────────────────────────────────────

@app.route('/api/profiles')
@require_auth
def api_profiles():
    """Gibt die verfügbaren Aufnahme-Profile zurück."""
    return jsonify(RECORDING_PROFILES)


@app.route('/api/detection-engine', methods=['GET', 'POST'])
@require_auth
def api_detection_engine():
    """Liest oder wechselt die aktive Detection-Engine.
    POST { "engine": "hailo" | "cpu_yolo" }
    Stoppt laufende Detection und startet sie mit der neuen Engine neu.
    """
    if request.method == 'GET':
        return jsonify({
            'active':  settings._active_engine,
            'engines': DETECTION_ENGINES,
        })
    data   = request.get_json(silent=True) or {}
    engine = data.get('engine', '')
    if engine not in DETECTION_ENGINES:
        return jsonify({'error': f'Unbekannte Engine: {engine}'}), 400
    if engine == settings._active_engine:
        return jsonify({'success': True, 'active': settings._active_engine, 'changed': False})
    with _lock:
        was_running = state.detection_running
        was_mode    = state.detection_mode
        if was_running:
            CameraManager.stop_detection()
        settings._active_engine   = engine
        settings.DETECTION_SCRIPT = DETECTION_ENGINES[engine]['script']
    _save_active_engine(engine)
    logger.info('Detection-Engine gewechselt auf: %s (%s)', engine, settings.DETECTION_SCRIPT)
    if was_running:
        if was_mode:
            CameraManager.start_detection_mode()
        else:
            CameraManager.start_detection()
    return jsonify({'success': True, 'active': settings._active_engine, 'changed': True})


@app.route('/api/detection-settings', methods=['GET', 'POST'])
@require_auth
def api_detection_settings():
    """Liest oder setzt Detection-Zielklasse und Confidence-Schwelle.
    GET  → { "target_class": "bird"|"person"|"dog"|"cat"|"all4", "threshold": 0.45 }
    POST { "target_class": "bird"|"person"|"dog"|"cat"|"all4", "threshold": 0.45 }
    Bei laufender Detection wird diese neu gestartet, damit die neuen Werte wirken.
    """
    if request.method == 'GET':
        return jsonify({'target_class': settings._detection_target, 'threshold': settings._detection_threshold})
    data = request.get_json(silent=True) or {}
    target = data.get('target_class', settings._detection_target)
    if target not in settings.DETECTION_TARGETS:
        return jsonify({'error': f'Ungültige Zielklasse: {target}. Erlaubt: bird, person, dog, cat, all4'}), 400
    try:
        threshold = float(data.get('threshold', settings._detection_threshold))
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold muss eine Zahl zwischen 0.1 und 0.95 sein'}), 400
    threshold = max(0.1, min(0.95, threshold))
    with _lock:
        was_running = state.detection_running
        was_mode    = state.detection_mode
        if was_running:
            CameraManager.stop_detection()
        settings._detection_target    = target
        settings._detection_threshold = threshold
    _save_detection_settings(target, threshold)
    logger.info('Detection-Settings geändert: target=%s threshold=%.2f', target, threshold)
    if was_running:
        if was_mode:
            CameraManager.start_detection_mode()
        else:
            CameraManager.start_detection()
    return jsonify({'success': True, 'target_class': settings._detection_target, 'threshold': settings._detection_threshold})


@app.route('/api/camera-settings', methods=['GET', 'POST'])
@require_auth
def api_camera_settings():
    """Liest oder setzt Kamera-Einstellungen (lens_position, ev, awb, brightness, contrast, saturation, sharpness, gain).
    GET  → { "lens_position": 3.0, "ev": 0.0, "awb": "auto", "brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "sharpness": 1.0, "gain": 1.0 }
    POST { "brightness": 0.5 } oder beliebige Kombination der Parameter
    """
    if request.method == 'GET':
        return jsonify({'lens_position': settings._lens_position, 'ev': settings._ev, 'awb': settings._awb, 'brightness': settings._brightness, 'contrast': settings._contrast, 'saturation': settings._saturation, 'sharpness': settings._sharpness, 'gain': settings._gain})
    
    data = request.get_json(silent=True) or {}
    lp, ev, awb = settings._lens_position, settings._ev, settings._awb
    brightness, contrast, saturation, sharpness, gain = settings._brightness, settings._contrast, settings._saturation, settings._sharpness, settings._gain
    
    # lens_position validieren und updaten
    if 'lens_position' in data:
        try:
            lp = float(data['lens_position'])
            lp = max(0.0, min(10.0, lp))
        except (TypeError, ValueError):
            return jsonify({'error': 'lens_position muss eine Zahl zwischen 0.0 und 10.0 sein'}), 400
    
    # ev validieren und updaten
    if 'ev' in data:
        try:
            ev = float(data['ev'])
            ev = max(-2.0, min(2.0, ev))
        except (TypeError, ValueError):
            return jsonify({'error': 'ev muss eine Zahl zwischen -2.0 und 2.0 sein'}), 400
    
    # awb validieren und updaten
    if 'awb' in data:
        awb = str(data['awb']).lower()
        if awb not in ['auto', 'daylight', 'cloudy', 'tungsten', 'fluorescent', 'indoor']:
            return jsonify({'error': 'awb muss einer der folgenden Werte sein: auto, daylight, cloudy, tungsten, fluorescent, indoor'}), 400
    
    # brightness validieren und updaten
    if 'brightness' in data:
        try:
            brightness = float(data['brightness'])
            brightness = max(-1.0, min(1.0, brightness))
        except (TypeError, ValueError):
            return jsonify({'error': 'brightness muss eine Zahl zwischen -1.0 und 1.0 sein'}), 400
    
    # contrast validieren und updaten
    if 'contrast' in data:
        try:
            contrast = float(data['contrast'])
            contrast = max(0.5, min(2.0, contrast))
        except (TypeError, ValueError):
            return jsonify({'error': 'contrast muss eine Zahl zwischen 0.5 und 2.0 sein'}), 400
    
    # saturation validieren und updaten
    if 'saturation' in data:
        try:
            saturation = float(data['saturation'])
            saturation = max(0.0, min(2.0, saturation))
        except (TypeError, ValueError):
            return jsonify({'error': 'saturation muss eine Zahl zwischen 0.0 und 2.0 sein'}), 400
    
    # sharpness validieren und updaten
    if 'sharpness' in data:
        try:
            sharpness = float(data['sharpness'])
            sharpness = max(0.0, min(2.0, sharpness))
        except (TypeError, ValueError):
            return jsonify({'error': 'sharpness muss eine Zahl zwischen 0.0 und 2.0 sein'}), 400
    
    # gain validieren und updaten
    if 'gain' in data:
        try:
            gain = float(data['gain'])
            gain = max(1.0, min(8.0, gain))
        except (TypeError, ValueError):
            return jsonify({'error': 'gain muss eine Zahl zwischen 1.0 und 8.0 sein'}), 400
    
    with _lock:
        settings._lens_position = lp
        settings._ev = ev
        settings._awb = awb
        settings._brightness = brightness
        settings._contrast = contrast
        settings._saturation = saturation
        settings._sharpness = sharpness
        settings._gain = gain
    
    _save_camera_settings({'lens_position': lp, 'ev': ev, 'awb': awb, 'brightness': brightness, 'contrast': contrast, 'saturation': saturation, 'sharpness': sharpness, 'gain': gain})
    logger.info('Kamera-Einstellungen geändert: lens_position=%.1f, ev=%.1f, awb=%s, brightness=%.1f, contrast=%.1f, saturation=%.1f, sharpness=%.1f, gain=%.1f', lp, ev, awb, brightness, contrast, saturation, sharpness, gain)
    return jsonify({'success': True, 'lens_position': settings._lens_position, 'ev': settings._ev, 'awb': settings._awb, 'brightness': settings._brightness, 'contrast': settings._contrast, 'saturation': settings._saturation, 'sharpness': settings._sharpness, 'gain': settings._gain})


@app.route('/api/rec-settings', methods=['GET', 'POST'])
@require_auth
def api_rec_settings():
    """Liest oder speichert persistente Aufnahme-Einstellungen (Profil + Dauer)."""
    if request.method == 'GET':
        return jsonify(_load_rec_settings())
    data = request.get_json(silent=True) or {}
    profile  = data.get('profile', 'normal_hd')
    duration = min(max(_int_arg(data.get('duration'), 15), 3), 600)   # max 10 min = 600 s
    if profile not in RECORDING_PROFILES:
        return jsonify({'error': f'Unbekanntes Profil: {profile}'}), 400
    _save_rec_settings({'profile': profile, 'duration': duration})
    return jsonify({'success': True, 'profile': profile, 'duration': duration})


# ── Recording ────────────────────────────────────────────────────────────────

@app.route('/api/record', methods=['POST'])
@require_auth
def api_record():
    with _lock:
        if state.detection_mode:
            return jsonify({'error': 'Im Detection-Modus gesperrt – manuelle Aufnahme nicht möglich'}), 409
        if state.recording_running:
            return jsonify({'error': 'Recording läuft bereits'}), 409

    data         = request.get_json(silent=True) or {}
    profile_name = data.get('profile')      # optionaler Profilname
    duration     = min(max(_int_arg(data.get('duration'), 15), 3), 600)   # max 10 min = 600 s

    if profile_name and profile_name in RECORDING_PROFILES:
        profile    = RECORDING_PROFILES[profile_name]
        resolution = profile['resolution']
        fps        = profile['fps']
        bitrate    = profile['bitrate']
        slowmotion = profile['slowmotion']
    else:
        # Fallback: direkte Parameter (Legacy-Kompatibilität)
        resolution = str(data.get('resolution', '1080p'))
        if resolution not in _RESOLUTION_MAP:
            return jsonify({'error': f'Unbekannte Auflösung: {resolution}'}), 400
        fps        = min(max(_int_arg(data.get('fps'), 30), 1), 120)
        bitrate    = min(max(_int_arg(data.get('bitrate'), 8000), 1000), 25000)
        slowmotion = bool(data.get('slowmotion', False))

    threading.Thread(
        target=CameraManager.record,
        kwargs={
            'duration':    duration,
            'resolution':  resolution,
            'fps':         fps,
            'bitrate':     bitrate,
            'slowmotion':  slowmotion,
            'triggered_by': 'manual',
        },
        daemon=True,
    ).start()

    label = RECORDING_PROFILES[profile_name]['label'] if profile_name in (RECORDING_PROFILES if profile_name else {}) else resolution
    return jsonify({'success': True, 'message': f'Recording gestartet ({duration}s – {label})'})


@app.route('/api/record/audio', methods=['POST'])
@require_auth
def api_record_audio():
    """Startet eine reine Audio-Aufnahme (kein Video). Dauer max. 3600s."""
    with _lock:
        if state.recording_running:
            return jsonify({'error': 'Video-Aufnahme läuft bereits'}), 409
        if state.audio_running:
            return jsonify({'error': 'Audio-Aufnahme läuft bereits'}), 409

    data     = request.get_json(silent=True) or {}
    duration = min(max(_int_arg(data.get('duration'), 60), 3), 3600)

    threading.Thread(
        target=CameraManager.record_audio,
        kwargs={'duration': duration},
        daemon=True,
    ).start()
    return jsonify({'success': True, 'message': f'Audio-Aufnahme gestartet ({duration}s)'})


@app.route('/api/record/kill', methods=['POST'])
@require_auth
def api_record_kill():
    """Beendet einen hängenden Aufnahme- oder Audio-Prozess sofort (SIGTERM → SIGKILL)."""
    with _lock:
        proc = state.recording_process
        if not proc:
            return jsonify({'error': 'Kein Aufnahmeprozess aktiv'}), 409

    logger.warning('Kill-Aufnahme angefordert (PID %d)', proc.pid)
    _kill_process_group(proc, timeout=3)
    return jsonify({'success': True, 'message': 'Aufnahmeprozess beendet'})


@app.route('/api/convert', methods=['POST'])
@require_auth
def api_convert():
    def _run():
        count, errors = CameraManager.convert_all_pending()
        if count == 0 and not errors:
            # nichts ausstehend → neueste h264 (auch bereits konvertierte) nochmal probieren
            h264 = CameraManager._find_latest_h264()
            if h264:
                ok, results = CameraManager._convert_one(h264)
                if ok:
                    for mp4 in results:
                        CameraManager.transfer_all(mp4)
                else:
                    with _lock:
                        state.last_error = results[0] if results else 'Konvertierungsfehler'
            else:
                with _lock:
                    state.last_error = 'Keine h264-Dateien gefunden'
        elif errors:
            with _lock:
                state.last_error = '; '.join(errors[:3])

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Konvertierung gestartet – alle ausstehenden H264-Dateien werden verarbeitet'})


@app.route('/api/recordings')
@require_auth
def api_recordings():
    return jsonify(CameraManager.list_recordings())


# ── Download ──────────────────────────────────────────────────────────────────

def _resolve_media_path(rel: str):
    """Gibt (Path, None) für eine Datei unterhalb von VIDEO_BASE_DIR zurück,
    sonst (None, Fehlerantwort). Verhindert Path-Traversal."""
    if not rel:
        return None, (jsonify({'error': 'Parameter p fehlt'}), 400)
    base = Path(config.VIDEO_BASE_DIR).resolve()
    target = (base / rel).resolve()
    if target == base or not target.is_relative_to(base):
        return None, (jsonify({'error': 'Zugriff verweigert'}), 403)
    if not target.exists() or not target.is_file():
        return None, (jsonify({'error': 'Datei nicht gefunden'}), 404)
    return target, None


@app.route('/api/download')
@require_auth
def api_download():
    # Token nur per Authorization-Header (kein ?token= – landet sonst in Logs/Verlauf)
    target, err = _resolve_media_path(request.args.get('p', ''))
    if err:
        return err
    return send_file(str(target), as_attachment=True, download_name=target.name)


# ── Download-Ticket ───────────────────────────────────────────────────────────
# Der Browser kann bei <video src=…> und bei normalen Datei-Downloads keinen
# Authorization-Header mitschicken. Statt das Login-Token in die URL zu legen,
# stellt die API ein Ticket aus: signiert, nur für genau eine Datei, kurz gültig.
# Damit streamt der Browser selbst (Range-Requests, Fortschritt, kein Blob im RAM).

_TICKET_TTL_S = 600


@app.route('/api/download-ticket', methods=['POST'])
@require_auth
def api_download_ticket():
    data = request.get_json(silent=True) or {}
    rel = str(data.get('p') or '').strip()
    target, err = _resolve_media_path(rel)
    if err:
        return err
    now = datetime.now(timezone.utc)
    ticket = jwt.encode(
        {'typ': 'file', 'p': rel, 'iat': now, 'exp': now + timedelta(seconds=_TICKET_TTL_S)},
        config.JWT_SECRET, algorithm='HS256')
    return jsonify({'url': f'/api/file?t={ticket}', 'expires_in': _TICKET_TTL_S,
                    'size': target.stat().st_size})


@app.route('/api/file')
def api_file():
    """Liefert die Datei aus einem Download-Ticket. ?dl=1 → als Anhang speichern."""
    try:
        claims = jwt.decode(request.args.get('t', ''), config.JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        abort(401)
    if claims.get('typ') != 'file':   # Login-Token ist hier ausdrücklich kein gültiges Ticket
        abort(401)
    target, err = _resolve_media_path(str(claims.get('p') or ''))
    if err:
        return err
    return send_file(str(target), conditional=True, download_name=target.name,
                     as_attachment=request.args.get('dl') == '1')


# ── Löschen ───────────────────────────────────────────────────────────────────

@app.route('/api/delete', methods=['POST'])
@require_auth
def api_delete():
    data = request.get_json(force=True, silent=True) or {}
    rel = str(data.get('p') or '').strip()
    if not rel:
        return jsonify({'error': 'Parameter p fehlt'}), 400
    base = Path(config.VIDEO_BASE_DIR).resolve()
    target = (base / rel).resolve()
    if target == base or not target.is_relative_to(base):
        return jsonify({'error': 'Zugriff verweigert'}), 403
    if not target.exists() or not target.is_file():
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    deleted = [str(target.name)]
    target.unlink()
    # Zugehörige Dateien mitbereinigen (H264-Quelle + WAV bei Video-Aufnahmen)
    for ext in ('.h264', '.wav'):
        companion = target.with_suffix(ext)
        if companion.exists():
            companion.unlink()
            deleted.append(companion.name)
    invalidate_media_scan()
    logger.info('Gelöscht: %s', deleted)
    return jsonify({'success': True, 'deleted': deleted})


# ── Manueller Transfer ───────────────────────────────────────────────────────

@app.route('/api/transfer', methods=['POST'])
@require_auth
def api_transfer():
    """Überträgt alle vorhandenen MP4s an alle aktiven Sync-Ziele (ohne Konvertierung)."""
    def _run():
        base = Path(config.VIDEO_BASE_DIR)
        mp4s = sorted(base.rglob('*.mp4'), key=lambda f: f.stat().st_mtime, reverse=True) if base.exists() else []
        if not mp4s:
            with _lock:
                state.last_error = 'Keine MP4-Dateien zum Übertragen gefunden'
            return
        total_ok = 0
        for mp4 in mp4s[:50]:  # max 50 neueste
            results = CameraManager.transfer_all(str(mp4))
            if any(ok for _, ok, _ in results):
                total_ok += 1
        logger.info('Manueller Transfer: %d MP4(s) übertragen', total_ok)
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Übertragung gestartet – alle MP4s werden an aktive Ziele gesendet'})




@app.route('/api/settings', methods=['GET'])
@require_auth
def api_settings_get():
    s = _load_sync_settings()
    targets = s.get('targets', [])
    # key_set pro Target prüfen
    for t in targets:
        t['key_set'] = Path(f"/config/sync_key_{t['id']}").exists()
    return jsonify({'targets': targets})


@app.route('/api/settings/targets', methods=['POST'])
@require_auth
def api_settings_targets_post():
    """Speichert die komplette targets-Liste."""
    data = request.get_json(silent=True) or {}
    targets = data.get('targets', [])
    # Validierung + ID-Vergabe
    if not isinstance(targets, list) or len(targets) > 20:
        return jsonify({'success': False, 'error': 'targets muss eine Liste (max. 20) sein'}), 400
    clean = []
    for i, t in enumerate(targets):
        if not isinstance(t, dict):
            return jsonify({'success': False, 'error': f'Ziel {i + 1}: ungültiges Format'}), 400
        entry = {
            'id':      i,
            'name':    str(t.get('name', f'Ziel {i+1}')).strip()[:60],
            'host':    str(t.get('host', '')).strip(),
            'user':    str(t.get('user', '')).strip(),
            'path':    str(t.get('path', '')).strip(),
            'enabled': bool(t.get('enabled', True)),
        }
        # Leere Ziele dürfen gespeichert werden (Formular halb ausgefüllt),
        # sobald etwas eingetragen ist, muss alles gültig sein
        if entry['host'] or entry['user'] or entry['path']:
            err = validate_target(entry['host'], entry['user'], entry['path'])
            if err:
                return jsonify({'success': False, 'error': f'Ziel „{entry["name"]}“: {err}'}), 400
        clean.append(entry)

    for i, t in enumerate(targets):
        # SSH-Key optional mitliefern
        if t.get('ssh_key'):
            key_content = str(t['ssh_key']).strip()
            if len(key_content) > 16384 or 'PRIVATE KEY-----' not in key_content:
                return jsonify({'success': False, 'error': f'Ziel {i + 1}: kein gültiger privater SSH-Key'}), 400
            key_file = Path(f'/config/sync_key_{i}')
            try:
                write_private_key(key_file, key_content)
                logger.info('SSH-Key gespeichert: %s', key_file)
            except Exception as exc:
                return jsonify({'success': False, 'error': f'SSH-Key für Ziel {i} fehlgeschlagen: {exc}'}), 500
    s = _load_sync_settings()
    s['targets'] = clean
    _save_sync_settings(s)
    # key_set befüllen für Response
    for t in clean:
        t['key_set'] = Path(f"/config/sync_key_{t['id']}").exists()
    return jsonify({'success': True, 'targets': clean})


@app.route('/api/settings/test', methods=['POST'])
@require_auth
def api_settings_test():
    """Testet Verbindung zu einem Sync-Ziel (per target_id, oder erstem aktiven)."""
    data = request.get_json(silent=True) or {}
    target_id = data.get('target_id')
    s = _load_sync_settings()
    targets = s.get('targets', [])
    if target_id is not None:
        tid = _int_arg(target_id, -1)
        t = next((x for x in targets if x.get('id') == tid), None)
    else:
        t = next((x for x in targets if x.get('host') and x.get('user')), None)
    if not t:
        return jsonify({'success': False, 'error': 'Kein Sync-Ziel konfiguriert'})
    host = t.get('host', '')
    user = t.get('user', '')
    err = validate_target(host, user, t.get('path') or '/')
    if err:
        return jsonify({'success': False, 'error': err})
    key_file = f"/config/sync_key_{t['id']}"
    key_exists = Path(key_file).exists()
    cmd = ['ssh', *ssh_options(key_file), '--', f'{user}@{host}', 'echo VERBINDUNG_OK']
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=12, text=True)
        if result.returncode == 0 and 'VERBINDUNG_OK' in result.stdout:
            return jsonify({'success': True, 'message': f'✅ Verbindung zu {user}@{host} erfolgreich'})
        err = (result.stderr or result.stdout).strip()[:400]
        if not key_exists:
            err = f'Kein SSH-Key gespeichert für dieses Ziel. Bitte Key eingeben und "Alle speichern" klicken. | {err}'
        elif 'Permission denied' in err:
            err = f'Permission denied – Public Key von {user}@{host} nicht autorisiert? Bitte ~/.ssh/authorized_keys prüfen. | {err}'
        return jsonify({'success': False, 'error': err or f'SSH Return-Code {result.returncode}'})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout (8s) – Host nicht erreichbar?'})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)})


@app.route('/api/pending')
@require_auth
def api_pending():
    """Gibt Anzahl H264-Dateien zurück, die noch nicht konvertiert wurden."""
    return jsonify({'pending': media_summary()['pending']})


# ── Live-Stream (MJPEG) ──────────────────────────────────────────────────────

_STREAM_FRAME = Path('/tmp/det_latest_frame.jpg')


@app.route('/api/snapshot')
@require_auth
def api_snapshot():
    """Einzelnes JPEG-Frame der Detection-Kamera (für JS-Polling, Token per Bearer-Header)."""
    if not _STREAM_FRAME.exists():
        abort(503)   # Noch kein Frame verfügbar
    resp = send_file(str(_STREAM_FRAME), mimetype='image/jpeg')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


# ── Web-GUI ───────────────────────────────────────────────────────────────────

WEB_DIR = Path(__file__).resolve().parent.parent / 'web'


_TEXT_SUFFIXES = ('.html', '.js', '.css', '.svg', '.json')
_text_cache: dict = {}   # Pfad → (mtime_ns, size, etag, roh, gzip)


def _serve_text(path: Path) -> Response:
    """Liefert HTML/JS/CSS gzip-komprimiert und mit ETag aus.
    'no-cache' heißt: Der Browser fragt jedes Mal nach, bekommt aber nur ein 304,
    solange sich die Datei nicht geändert hat – nach einem Hotpatch sofort die neue."""
    st = path.stat()
    cached = _text_cache.get(str(path))
    if not cached or cached[:2] != (st.st_mtime_ns, st.st_size):
        raw = path.read_bytes()
        etag = hashlib.sha1(raw).hexdigest()[:16]
        cached = (st.st_mtime_ns, st.st_size, etag, raw, gzip.compress(raw, 6))
        _text_cache[str(path)] = cached
    _, _, etag, raw, packed = cached

    use_gzip = 'gzip' in request.headers.get('Accept-Encoding', '')
    # Eigener ETag je Kodierung, sonst liefern Caches die falsche Variante aus
    full_etag = f'"{etag}-gz"' if use_gzip else f'"{etag}"'
    if request.headers.get('If-None-Match') == full_etag:
        resp = Response(status=304)
    else:
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        resp = Response(packed if use_gzip else raw, mimetype=mime)
        if use_gzip:
            resp.headers['Content-Encoding'] = 'gzip'
    resp.headers['ETag'] = full_etag
    resp.headers['Vary'] = 'Accept-Encoding'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


@app.route('/')
@app.route('/index.html')
def serve_index():
    f = WEB_DIR / 'index.html'
    if f.exists():
        return _serve_text(f)
    return '<!doctype html><h1>Web-GUI nicht gefunden</h1><p>web/index.html fehlt.</p>', 404


@app.route('/web/<path:filename>')
def serve_static(filename):
    """Statische Dateien aus dem web/-Verzeichnis (app.js, app.css, Logo)."""
    target = (WEB_DIR / filename).resolve()
    if target.suffix in _TEXT_SUFFIXES and target.is_file() and target.is_relative_to(WEB_DIR):
        return _serve_text(target)
    # Bilder ändern sich praktisch nie → einen Tag im Browser-Cache halten
    return send_from_directory(str(WEB_DIR), filename, max_age=86400)


@app.route('/cert.pem')
def serve_cert():
    """Self-signed Zertifikat zum Download (kein Auth noetig).
    Browser-Import: Einstellungen Zertifikate Behoerden Importieren."""
    cert = Path(config.CERT_FILE)
    if not cert.exists():
        return jsonify({'error': 'Zertifikat nicht gefunden'}), 404
    return send_file(str(cert), mimetype='application/x-pem-file',
                     as_attachment=True, download_name='vogel-kamera.pem')



# ── Error-Handler ─────────────────────────────────────────────────────────────

@app.errorhandler(401)
def err_401(_):
    return jsonify({'error': 'Nicht autorisiert'}), 401


@app.errorhandler(404)
def err_404(_):
    return jsonify({'error': 'Nicht gefunden'}), 404


@app.errorhandler(429)
def err_429(_):
    return jsonify({'error': 'Zu viele Anfragen'}), 429
