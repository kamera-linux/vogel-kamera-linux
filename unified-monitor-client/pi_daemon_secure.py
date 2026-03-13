#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pi Daemon Secure – HTTPS Flask + JWT + TOTP
Bird Camera Prozesssteuerung, gesichert mit 2FA

Läuft als Docker-Container auf dem Raspberry Pi.
Konfiguration ausschließlich über Umgebungsvariablen / .env-Datei.
"""

import os
import sys
import json
import subprocess
import threading
import time
import logging
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
import pyotp
import psutil
from flask import Flask, request, jsonify, send_file, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------------------------------------------------------------
# Konfiguration (ausschließlich Umgebungsvariablen)
# ---------------------------------------------------------------------------
PORT              = int(os.environ.get('PI_DAEMON_PORT', 8443))
CERT_FILE         = os.environ.get('PI_DAEMON_CERT_FILE', '/certs/cert.pem')
KEY_FILE          = os.environ.get('PI_DAEMON_KEY_FILE',  '/certs/key.pem')
JWT_SECRET        = os.environ.get('PI_DAEMON_JWT_SECRET', '')
TOTP_SECRET       = os.environ.get('PI_DAEMON_TOTP_SECRET', '')
PASSWORD_HASH     = os.environ.get('PI_DAEMON_PASSWORD_HASH', '')
TOKEN_EXPIRY_H    = int(os.environ.get('PI_DAEMON_TOKEN_EXPIRY_HOURS', 8))
VIDEO_BASE_DIR    = os.environ.get('PI_DAEMON_VIDEO_DIR', '/videos/Vogelhaus/AI-HAD')
# Sync-Ziel nach Konvertierung (optional): z.B. 'user@raspi-collector:/videos/'
# Wird beim Start aus /config/sync-config.json überschrieben wenn vorhanden
SYNC_DEST         = os.environ.get('PI_DAEMON_SYNC_DEST', '')
SYNC_SSH_KEY      = os.environ.get('PI_DAEMON_SYNC_SSH_KEY', '/certs/id_rsa_sync')
# Persistente Einstellungen (ausserhalb des Containers in /etc/pi-daemon/)
SETTINGS_FILE     = '/config/sync-config.json'
SYNC_KEY_FILE     = '/config/sync_rsa'
DETECTION_SCRIPT  = os.environ.get(
    'PI_DAEMON_DETECTION_SCRIPT',
    '/home/roimme/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-detect-only.py',
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    handlers=[
        logging.FileHandler('/tmp/pi_daemon_secure.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Startup-Validierung
# ---------------------------------------------------------------------------
def _check_config() -> None:
    missing = [v for v in ('PI_DAEMON_JWT_SECRET', 'PI_DAEMON_TOTP_SECRET', 'PI_DAEMON_PASSWORD_HASH')
               if not os.environ.get(v)]
    if missing:
        logger.critical('Fehlende Pflicht-Umgebungsvariablen: %s', ', '.join(missing))
        sys.exit(1)


# ---------------------------------------------------------------------------
# Globaler Zustand
# ---------------------------------------------------------------------------
_lock = threading.RLock()   # Reentrant – gleicher Thread darf mehrfach acquiren


class DaemonState:
    detection_running:  bool = False
    recording_running:  bool = False
    detection_process:  subprocess.Popen = None
    recording_process:  subprocess.Popen = None
    last_error:         str  = None
    recording_file:     dict = None
    started_at:         str  = datetime.now(timezone.utc).isoformat()


state = DaemonState()


# ---------------------------------------------------------------------------
# Kamera-Management
# ---------------------------------------------------------------------------
def _kill_process_group(proc: subprocess.Popen, timeout: int = 5) -> None:
    """Beendet eine Prozessgruppe per SIGTERM, danach SIGKILL."""
    try:
        os.killpg(os.getpgid(proc.pid), 15)
        proc.wait(timeout=timeout)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except Exception:
            pass


class CameraManager:

    @staticmethod
    def start_detection() -> bool:
        with _lock:
            if state.detection_running:
                return True
            try:
                proc = subprocess.Popen(
                    ['python3', DETECTION_SCRIPT, '--use-hailo'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp,
                )
                state.detection_process = proc
                state.detection_running = True
                logger.info('Detection gestartet PID=%d', proc.pid)
                return True
            except Exception as exc:
                logger.error('Detection-Start fehlgeschlagen: %s', exc)
                state.last_error = str(exc)
                return False

    @staticmethod
    def stop_detection() -> bool:
        with _lock:
            if not state.detection_running:
                return True
            try:
                _kill_process_group(state.detection_process)
                state.detection_running = False
                logger.info('Detection gestoppt')
                return True
            except Exception as exc:
                logger.error('Detection-Stop fehlgeschlagen: %s', exc)
                state.detection_running = False
                state.last_error = str(exc)
                return False

    @staticmethod
    def _stop_detection_for_recording() -> None:
        """Stoppt Detection und wartet auf libcamera-Freigabe.
        Muss MIT gehaltener _lock aufgerufen werden."""
        if state.detection_running and state.detection_process:
            _kill_process_group(state.detection_process)
            state.detection_running = False
            logger.info('Detection für Recording gestoppt')
        time.sleep(1)   # libcamera braucht Zeit zum Freigeben

    @staticmethod
    def record(duration: int = 10, resolution: str = '2k', fps: int = 30, bitrate: int = 6000):
        """Startet Recording. Blockiert bis Abschluss (in Background-Thread aufrufen)."""

        # ── Zustand prüfen und belegen ──────────────────────────────────────
        with _lock:
            if state.recording_running:
                return False, 'Recording läuft bereits'
            CameraManager._stop_detection_for_recording()
            state.recording_running = True

        # ── Aufnahme (Lock freigegeben) ─────────────────────────────────────
        try:
            res_map = {
                '480p':  (854,  480),
                '720p':  (1280, 720),
                '1080p': (1920, 1080),
                '2k':    (2560, 1440),
                '4k':    (4096, 2160),
            }
            w, h = res_map.get(resolution, (2560, 1440))

            recording_dir = Path(VIDEO_BASE_DIR)
            recording_dir.mkdir(parents=True, exist_ok=True)

            ts          = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_file  = recording_dir / f'recording_{ts}.h264'
            audio_file  = recording_dir / f'recording_{ts}.wav'

            video_cmd = [
                'rpicam-vid',
                '-t', str(duration * 1000),
                '-w', str(w), '-h', str(h),
                '--framerate', str(fps),
                '--bitrate', str(bitrate * 1000),
                '-o', str(video_file),
                '--inline',
            ]
            audio_cmd = [
                'arecord', '-f', 'S16_LE', '-r', '44100',
                '-c', '1', '-t', 'wav',
                '-d', str(duration), str(audio_file),
            ]

            logger.info('Recording %ds %s → %s', duration, resolution, video_file.name)

            video_proc = subprocess.Popen(video_cmd,
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio_proc = subprocess.Popen(audio_cmd,
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with _lock:
                state.recording_process = video_proc

            video_proc.wait()
            audio_proc.wait()

            # Kurze Pause: Dateisystem-Flush sicherstellen (wie in alten Skripten +1s)
            time.sleep(2)

            if video_file.exists():
                rec_info = {
                    'video':     str(video_file),
                    'audio':     str(audio_file) if audio_file.exists() else None,
                    'timestamp': ts,
                }
                with _lock:
                    state.recording_file = rec_info
                logger.info('Recording abgeschlossen: %s', video_file.name)

                # Auto-Konvertierung direkt auf die gerade aufgenommene h264
                ok, result = CameraManager._convert_one(video_file)
                if ok:
                    logger.info('Auto-Konvertierung nach Recording: %s', Path(result).name)
                    CameraManager.transfer_all(result)
                else:
                    logger.warning('Auto-Konvertierung fehlgeschlagen: %s', result)
                    with _lock:
                        state.last_error = f'Konvertierung: {result}'

                return True, rec_info

            logger.error('Video-Datei nicht erstellt: %s', video_file)
            return False, 'Video-Datei nicht erstellt'

        except Exception as exc:
            logger.error('Recording fehlgeschlagen: %s', exc)
            with _lock:
                state.last_error = str(exc)
            return False, str(exc)

        finally:
            with _lock:
                state.recording_running = False
                state.recording_process = None
            CameraManager.start_detection()

    @staticmethod
    def _find_latest_h264() -> 'Path | None':
        """Findet die neueste h264-Datei in VIDEO_BASE_DIR (Fallback nach Neustart)."""
        base = Path(VIDEO_BASE_DIR)
        if not base.exists():
            return None
        files = sorted(base.rglob('*.h264'), key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0] if files else None

    @staticmethod
    def _convert_one(h264: 'Path') -> tuple:
        """Konvertiert eine einzelne h264 → mp4. Gibt (ok, mp4_path_or_error) zurück.
        Nutzt -c:v copy + -fflags +genpts (schnell, kein Re-Encoding, kein Qualitätsverlust)."""
        try:
            mp4 = h264.with_suffix('.mp4')
            wav = h264.with_suffix('.wav')
            audio_valid = wav.exists() and wav.stat().st_size > 4096  # mind. 4KB

            cmd = ['ffmpeg', '-y', '-fflags', '+genpts', '-r', '30', '-i', str(h264)]
            if audio_valid:
                cmd += ['-i', str(wav), '-c:v', 'copy', '-c:a', 'aac', '-shortest']
            else:
                cmd += ['-c:v', 'copy']
            cmd.append(str(mp4))

            logger.info('Konvertierung: %s%s → %s',
                        h264.name, ' (+Audio)' if audio_valid else '', mp4.name)
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            if result.returncode == 0 and mp4.exists():
                logger.info('Konvertierung abgeschlossen: %s (%.1f MB)',
                            mp4.name, mp4.stat().st_size / 1048576)
                return True, str(mp4)
            err = result.stderr.decode(errors='replace')[:500]
            logger.error('ffmpeg Fehler: %s', err)
            return False, err
        except Exception as exc:
            logger.error('Konvertierung fehlgeschlagen: %s', exc)
            return False, str(exc)

    @staticmethod
    def convert_all_pending() -> tuple:
        """Konvertiert alle h264-Dateien die noch kein mp4 haben.
        Gibt (converted_count, error_list) zurück."""
        base = Path(VIDEO_BASE_DIR)
        h264_files = sorted(base.rglob('*.h264'), key=lambda f: f.stat().st_mtime) if base.exists() else []
        pending = [f for f in h264_files if not f.with_suffix('.mp4').exists()]
        if not pending:
            return 0, []
        converted = 0
        errors = []
        for h264 in pending:
            ok, result = CameraManager._convert_one(h264)
            if ok:
                converted += 1
                CameraManager.transfer_all(result)
            else:
                errors.append(f'{h264.name}: {result}')
        return converted, errors

    # Legacy-kompatibler Wrapper
    @staticmethod
    def convert() -> tuple:
        with _lock:
            rec = state.recording_file
        if rec:
            h264 = Path(rec.get('video', ''))
        else:
            h264 = CameraManager._find_latest_h264()
        if not h264 or not h264.exists():
            # Fallback: alle ausstehenden konvertieren
            count, errs = CameraManager.convert_all_pending()
            if count:
                return True, f'{count} Dateien konvertiert'
            return False, errs[0] if errs else 'Keine h264-Dateien vorhanden'
        ok, result = CameraManager._convert_one(h264)
        if ok:
            with _lock:
                if state.recording_file:
                    state.recording_file['mp4'] = result
        return ok, result

    @staticmethod
    def transfer_all(mp4_path: str) -> list:
        """Überträgt MP4 per rsync an alle konfigurierten Sync-Ziele.
        Gibt Liste von (target_name, ok, msg) zurück."""
        targets = _get_active_targets()
        if not targets:
            return []
        results = []
        for t in targets:
            dest = f"{t['user']}@{t['host']}:{t['path']}"
            key_file = f"/config/sync_key_{t['id']}"
            ssh_opts = 'StrictHostKeyChecking=no,LogLevel=ERROR,ConnectTimeout=10'
            if Path(key_file).exists():
                ssh_opts += f',IdentityFile={key_file}'
            cmd = ['rsync', '-az', '-e', f'ssh -o {ssh_opts}', mp4_path, dest]
            logger.info('Transfer [%s]: %s → %s', t['name'], Path(mp4_path).name, dest)
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=600)
                ok = r.returncode == 0
                msg = dest if ok else r.stderr.decode(errors='replace')[:200]
                if ok:
                    logger.info('Transfer abgeschlossen [%s]: %s', t['name'], Path(mp4_path).name)
                else:
                    logger.error('Transfer fehlgeschlagen [%s]: %s', t['name'], msg)
                results.append((t['name'], ok, msg))
            except subprocess.TimeoutExpired:
                results.append((t['name'], False, 'Timeout'))
            except Exception as exc:
                results.append((t['name'], False, str(exc)))
        return results

    @staticmethod
    def list_recordings() -> list:
        base = Path(VIDEO_BASE_DIR)
        if not base.exists():
            return []
        # rglob: auch Unterverzeichnisse durchsuchen
        files = sorted(base.rglob('*.mp4'), key=lambda f: f.stat().st_mtime, reverse=True)
        result = []
        for f in files[:100]:
            try:
                rel = str(f.relative_to(base))
            except ValueError:
                rel = f.name
            mtime = f.stat().st_mtime
            result.append({
                'name':     f.name,
                'rel_path': rel,
                'size_mb':  round(f.stat().st_size / 1_048_576, 1),
                'created':  datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'date':     datetime.fromtimestamp(mtime).strftime('%Y-%m-%d'),
            })
        return result


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


# ── JWT-Helpers ─────────────────────────────────────────────────────────────

def _make_token(client_ip: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': 'admin',
        'iat': now,
        'exp': now + timedelta(hours=TOKEN_EXPIRY_H),
        'ip':  client_ip,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def require_auth(f):
    @wraps(f)
    def _inner(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            abort(401)
        try:
            jwt.decode(auth[7:], JWT_SECRET, algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
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

    pw_ok   = bool(PASSWORD_HASH) and bcrypt.checkpw(password, PASSWORD_HASH.encode('utf-8'))
    totp_ok = pyotp.TOTP(TOTP_SECRET).verify(totp_code, valid_window=1)

    if not pw_ok or not totp_ok:
        time.sleep(1)   # Brute-force-Abbremsung
        return jsonify({'error': 'Ungültige Anmeldedaten'}), 401

    token = _make_token(request.remote_addr)
    logger.info('Login von %s', request.remote_addr)
    return jsonify({'token': token, 'expires_in': TOKEN_EXPIRY_H * 3600})


# ── Status ────────────────────────────────────────────────────────────────────

@app.route('/api/status')
@require_auth
def api_status():
    try:
        cpu  = psutil.cpu_percent(interval=0.3)
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage(VIDEO_BASE_DIR if Path(VIDEO_BASE_DIR).exists() else '/')
        system = {
            'cpu_percent':  cpu,
            'mem_used_mb':  round(mem.used   / 1_048_576),
            'mem_total_mb': round(mem.total  / 1_048_576),
            'disk_free_gb': round(disk.free  / 1_073_741_824, 1),
            'disk_total_gb': round(disk.total / 1_073_741_824, 1),
        }
    except Exception:
        system = {}

    return jsonify({
        'detection_running': state.detection_running,
        'recording_running': state.recording_running,
        'last_error':        state.last_error,
        'recording_file':    state.recording_file,
        'started_at':        state.started_at,
        'system':            system,
    })


# ── Detection ────────────────────────────────────────────────────────────────

@app.route('/api/detection/start', methods=['POST'])
@require_auth
def api_detection_start():
    ok = CameraManager.start_detection()
    return jsonify({'success': ok})


@app.route('/api/detection/stop', methods=['POST'])
@require_auth
def api_detection_stop():
    ok = CameraManager.stop_detection()
    return jsonify({'success': ok})


# ── Recording ────────────────────────────────────────────────────────────────

@app.route('/api/record', methods=['POST'])
@require_auth
def api_record():
    with _lock:
        if state.recording_running:
            return jsonify({'error': 'Recording läuft bereits'}), 409

    data       = request.get_json(silent=True) or {}
    duration   = min(max(int(data.get('duration',   10)),    3), 300)
    resolution = data.get('resolution', '2k')
    fps        = min(max(int(data.get('fps',        30)),    1), 60)
    bitrate    = min(max(int(data.get('bitrate', 6000)), 1000), 25000)

    threading.Thread(
        target=CameraManager.record,
        args=(duration, resolution, fps, bitrate),
        daemon=True,
    ).start()

    return jsonify({'success': True, 'message': f'Recording gestartet ({duration}s)'})


@app.route('/api/convert', methods=['POST'])
@require_auth
def api_convert():
    def _run():
        count, errors = CameraManager.convert_all_pending()
        if count == 0 and not errors:
            # nichts ausstehend → neueste h264 (auch bereits konvertierte) nochmal probieren
            h264 = CameraManager._find_latest_h264()
            if h264:
                ok, result = CameraManager._convert_one(h264)
                if ok:
                    CameraManager.transfer_all(result)
                else:
                    with _lock:
                        state.last_error = result
            else:
                with _lock:
                    state.last_error = 'Keine h264-Dateien gefunden'
        elif errors:
            with _lock:
                state.last_error = '; '.join(errors[:3])

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Konvertierung gestartet – alle ausstehenden H264-Dateien werden verarbeitet'})


# ── Auto-Convert Watcher ──────────────────────────────────────────────────────

def _auto_convert_watcher():
    """Hintergrund-Thread: prüft alle 3 Minuten auf unconvertierte H264-Dateien."""
    time.sleep(30)  # kurzer Start-Delay
    while True:
        try:
            count, errors = CameraManager.convert_all_pending()
            if count:
                logger.info('Auto-Convert: %d Datei(en) konvertiert', count)
            if errors:
                logger.warning('Auto-Convert Fehler: %s', '; '.join(errors[:3]))
        except Exception as exc:
            logger.error('Auto-Convert Watcher Fehler: %s', exc)
        time.sleep(180)


threading.Thread(target=_auto_convert_watcher, daemon=True, name='auto-convert').start()


@app.route('/api/recordings')
@require_auth
def api_recordings():
    return jsonify(CameraManager.list_recordings())


# ── Download ──────────────────────────────────────────────────────────────────

@app.route('/api/download')
@require_auth
def api_download():
    rel = request.args.get('p', '')
    if not rel:
        return jsonify({'error': 'Parameter p fehlt'}), 400
    # Sicherheit: kein Path-Traversal ausserhalb VIDEO_BASE_DIR
    base = Path(VIDEO_BASE_DIR).resolve()
    target = (base / rel).resolve()
    if not str(target).startswith(str(base) + '/'):
        return jsonify({'error': 'Zugriff verweigert'}), 403
    if not target.exists() or not target.is_file():
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    return send_file(str(target), as_attachment=True, download_name=target.name)


# ── Löschen ───────────────────────────────────────────────────────────────────

@app.route('/api/delete', methods=['POST'])
@require_auth
def api_delete():
    data = request.get_json(force=True, silent=True) or {}
    rel = data.get('p', '').strip()
    if not rel:
        return jsonify({'error': 'Parameter p fehlt'}), 400
    base = Path(VIDEO_BASE_DIR).resolve()
    target = (base / rel).resolve()
    if not str(target).startswith(str(base) + '/'):
        return jsonify({'error': 'Zugriff verweigert'}), 403
    if not target.exists() or not target.is_file():
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    deleted = [str(target.name)]
    target.unlink()
    # Optionale Bereinigung: zugehörige H264-Quelldatei
    h264 = target.with_suffix('.h264')
    if h264.exists():
        h264.unlink()
        deleted.append(h264.name)
    logger.info('Gelöscht: %s', deleted)
    return jsonify({'success': True, 'deleted': deleted})


# ── Manueller Transfer ───────────────────────────────────────────────────────

@app.route('/api/transfer', methods=['POST'])
@require_auth
def api_transfer():
    """Überträgt alle vorhandenen MP4s an alle aktiven Sync-Ziele (ohne Konvertierung)."""
    def _run():
        base = Path(VIDEO_BASE_DIR)
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


# ── Einstellungen (Multi-Target Sync) ────────────────────────────────────────

def _load_sync_settings() -> dict:
    try:
        return json.loads(Path(SETTINGS_FILE).read_text())
    except Exception:
        return {'targets': []}


def _save_sync_settings(data: dict) -> None:
    try:
        Path(SETTINGS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(SETTINGS_FILE).write_text(json.dumps(data, indent=2))
    except Exception as exc:
        logger.error('Einstellungen konnten nicht gespeichert werden: %s', exc)


def _get_active_targets() -> list:
    """Gibt alle aktiven (enabled=True, host+user+path gesetzt) Sync-Ziele zurück."""
    s = _load_sync_settings()
    result = []
    for t in s.get('targets', []):
        if t.get('enabled', True) and t.get('host') and t.get('user') and t.get('path'):
            result.append(t)
    return result


# Einstellungen beim Start laden (Legacy SYNC_DEST aus Umgebungsvariable)
def _migrate_legacy_settings() -> None:
    """Migriert alte Einzel-Host-Konfiguration in targets-Array."""
    s = _load_sync_settings()
    if 'targets' not in s:
        s['targets'] = []
    # Legacy: sync_host/sync_user/sync_path im Root → in targets migrieren
    if s.get('sync_host') and not s['targets']:
        s['targets'].append({
            'id': 0, 'name': 'Standard-Ziel',
            'host': s.pop('sync_host', ''),
            'user': s.pop('sync_user', ''),
            'path': s.pop('sync_path', ''),
            'enabled': True,
        })
        _save_sync_settings(s)
    # Legacy: alter sync_rsa Key → sync_key_0
    old_key = Path('/config/sync_rsa')
    new_key = Path('/config/sync_key_0')
    if old_key.exists() and not new_key.exists():
        try:
            import shutil
            shutil.copy2(str(old_key), str(new_key))
            os.chmod(str(new_key), 0o600)
        except Exception:
            pass


_migrate_legacy_settings()


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
    clean = []
    for i, t in enumerate(targets):
        entry = {
            'id':      i,
            'name':    str(t.get('name', f'Ziel {i+1}')).strip()[:60],
            'host':    str(t.get('host', '')).strip(),
            'user':    str(t.get('user', '')).strip(),
            'path':    str(t.get('path', '')).strip(),
            'enabled': bool(t.get('enabled', True)),
        }
        # SSH-Key optional mitliefern
        if t.get('ssh_key'):
            key_content = t['ssh_key'].strip()
            key_file = Path(f'/config/sync_key_{i}')
            try:
                key_file.parent.mkdir(parents=True, exist_ok=True)
                key_file.write_text(key_content + '\n')
                os.chmod(str(key_file), 0o600)
                logger.info('SSH-Key gespeichert: %s', key_file)
            except Exception as exc:
                return jsonify({'success': False, 'error': f'SSH-Key für Ziel {i} fehlgeschlagen: {exc}'}), 500
        clean.append(entry)
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
        t = next((x for x in targets if x['id'] == int(target_id)), None)
    else:
        t = next((x for x in targets if x.get('host') and x.get('user')), None)
    if not t:
        return jsonify({'success': False, 'error': 'Kein Sync-Ziel konfiguriert'})
    host = t['host']
    user = t['user']
    key_file = f"/config/sync_key_{t['id']}"
    key_opts = ['-i', key_file] if Path(key_file).exists() else []
    cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=8',
           '-o', 'BatchMode=yes'] + key_opts + [f'{user}@{host}', 'echo VERBINDUNG_OK']
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=12, text=True)
        if result.returncode == 0 and 'VERBINDUNG_OK' in result.stdout:
            return jsonify({'success': True, 'message': f'✅ Verbindung zu {user}@{host} erfolgreich'})
        err = (result.stderr or result.stdout)[:300]
        return jsonify({'success': False, 'error': err or f'SSH Return-Code {result.returncode}'})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout (8s) – Host nicht erreichbar?'})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)})


@app.route('/api/pending')
@require_auth
def api_pending():
    """Gibt Anzahl H264-Dateien zurück, die noch nicht konvertiert wurden."""
    base = Path(VIDEO_BASE_DIR)
    h264_files = list(base.rglob('*.h264')) if base.exists() else []
    pending = [f for f in h264_files if not f.with_suffix('.mp4').exists()]
    return jsonify({'pending': len(pending)})


# ── Web-GUI ───────────────────────────────────────────────────────────────────

WEB_DIR = Path(__file__).parent / 'web'


@app.route('/')
@app.route('/index.html')
def serve_index():
    f = WEB_DIR / 'index.html'
    if f.exists():
        return send_file(str(f))
    return '<!doctype html><h1>Web-GUI nicht gefunden</h1><p>web/index.html fehlt.</p>', 404


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


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    _check_config()

    CameraManager.start_detection()

    ssl_ctx = (CERT_FILE, KEY_FILE) if Path(CERT_FILE).exists() and Path(KEY_FILE).exists() else None
    if ssl_ctx is None:
        logger.warning('SSL-Zertifikat nicht gefunden – startet UNVERSCHLÜSSELT (nur Entwicklung!)')

    logger.info('Pi Daemon Secure auf Port %d (HTTPS=%s)', PORT, 'ja' if ssl_ctx else 'NEIN')

    app.run(
        host='0.0.0.0',
        port=PORT,
        ssl_context=ssl_ctx,
        threaded=True,
        use_reloader=False,
    )
