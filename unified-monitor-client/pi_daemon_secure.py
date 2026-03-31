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
from flask import Flask, request, jsonify, send_file, send_from_directory, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------------------------------------------------------------
# App-Version
# ---------------------------------------------------------------------------
APP_VERSION = '2.2.6'

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
SYNC_DEST         = os.environ.get('PI_DAEMON_SYNC_DEST', '')
SYNC_SSH_KEY      = os.environ.get('PI_DAEMON_SYNC_SSH_KEY', '/certs/id_rsa_sync')
SETTINGS_FILE     = '/config/sync-config.json'
SYNC_KEY_FILE     = '/config/sync_rsa'
# Verfügbare Detection-Engines (key → Dateipfad im Container)
_SCRIPT_BASE = '/home/roimme/vogel-kamera-linux/raspberry-pi-scripts'
DETECTION_ENGINES: dict = {
    'hailo':    {'label': '🔬 Hailo NPU (AI HAD+, 25fps, <5% CPU)',  'script': f'{_SCRIPT_BASE}/unified-camera-monitor-hailo.py'},
    'cpu_yolo': {'label': '🖥 CPU-YOLO (kein HAT nötig, ~80% CPU)', 'script': f'{_SCRIPT_BASE}/unified-camera-monitor-detect-only.py'},
}
DETECTION_ENGINE_FILE = '/config/detection-engine.json'

def _load_active_engine() -> str:
    """Gibt den aktiven Engine-Key zurück. Fallback: env-Variable, dann 'hailo'."""
    try:
        data = json.loads(Path(DETECTION_ENGINE_FILE).read_text())
        if data.get('engine') in DETECTION_ENGINES:
            return data['engine']
    except Exception:
        pass
    # Fallback: aus Env-Variable den Dateinamen ableiten
    env_script = os.environ.get('PI_DAEMON_DETECTION_SCRIPT', '')
    for key, info in DETECTION_ENGINES.items():
        if info['script'] == env_script:
            return key
    return 'hailo'

def _save_active_engine(engine: str) -> None:
    try:
        Path(DETECTION_ENGINE_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(DETECTION_ENGINE_FILE).write_text(json.dumps({'engine': engine}, indent=2))
    except Exception as exc:
        logger.error('Detection-Engine-Einstellung konnte nicht gespeichert werden: %s', exc)

# Aktive Engine – wird beim Start geladen und kann zur Laufzeit gewechselt werden
_active_engine: str = _load_active_engine()
DETECTION_SCRIPT: str = DETECTION_ENGINES[_active_engine]['script']

# Detection-Settings: Erkennungsziel und Confidence-Schwelle
DETECTION_SETTINGS_FILE = '/config/detection-settings.json'

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


def _read_last_detection() -> dict:
    """Letzte Erkennung aus /tmp/last-detection.json lesen (geschrieben vom Hailo-Script)."""
    try:
        p = Path('/tmp/last-detection.json')
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return None


def _load_detection_settings() -> dict:
    """Lädt target_class und threshold. Fallback: Vogel + 0.45."""
    try:
        data = json.loads(Path(DETECTION_SETTINGS_FILE).read_text())
        target = data.get('target_class', 'bird')
        if target not in ('bird', 'person'):
            target = 'bird'
        threshold = float(data.get('threshold', 0.45))
        threshold = max(0.1, min(0.95, threshold))
        return {'target_class': target, 'threshold': threshold}
    except Exception:
        return {'target_class': 'bird', 'threshold': 0.45}

def _save_detection_settings(target_class: str, threshold: float) -> None:
    try:
        Path(DETECTION_SETTINGS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(DETECTION_SETTINGS_FILE).write_text(
            json.dumps({'target_class': target_class, 'threshold': threshold}, indent=2)
        )
    except Exception as exc:
        logger.error('Detection-Settings konnten nicht gespeichert werden: %s', exc)

CAMERA_SETTINGS_FILE = '/config/camera-settings.json'

def _load_camera_settings() -> dict:
    """Lädt Kamera-Einstellungen. Fallback: lens_position=3.0, ev=0.0, awb='auto', brightness=0.0, contrast=1.0, saturation=1.0, sharpness=1.0, gain=1.0."""
    try:
        data = json.loads(Path(CAMERA_SETTINGS_FILE).read_text())
        lp = float(data.get('lens_position', 3.0))
        lp = max(0.0, min(10.0, lp))
        ev = float(data.get('ev', 0.0))
        ev = max(-2.0, min(2.0, ev))
        awb = str(data.get('awb', 'auto')).lower()
        if awb not in ['auto', 'daylight', 'cloudy', 'tungsten', 'fluorescent', 'indoor']:
            awb = 'auto'
        brightness = float(data.get('brightness', 0.0))
        brightness = max(-1.0, min(1.0, brightness))
        contrast = float(data.get('contrast', 1.0))
        contrast = max(0.5, min(2.0, contrast))
        saturation = float(data.get('saturation', 1.0))
        saturation = max(0.0, min(2.0, saturation))
        sharpness = float(data.get('sharpness', 1.0))
        sharpness = max(0.0, min(2.0, sharpness))
        gain = float(data.get('gain', 1.0))
        gain = max(1.0, min(8.0, gain))
        return {
            'lens_position': lp,
            'ev': ev,
            'awb': awb,
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation,
            'sharpness': sharpness,
            'gain': gain
        }
    except Exception:
        return {
            'lens_position': 3.0,
            'ev': 0.0,
            'awb': 'auto',
            'brightness': 0.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'sharpness': 1.0,
            'gain': 1.0
        }

def _save_camera_settings(data: dict) -> None:
    try:
        Path(CAMERA_SETTINGS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(CAMERA_SETTINGS_FILE).write_text(json.dumps(data, indent=2))
    except Exception as exc:
        logger.error('Kamera-Einstellungen konnten nicht gespeichert werden: %s', exc)

_det_settings    = _load_detection_settings()
_detection_target: str   = _det_settings['target_class']
_detection_threshold: float = _det_settings['threshold']

_cam_settings  = _load_camera_settings()
_lens_position: float = _cam_settings['lens_position']
_ev: float = _cam_settings['ev']
_awb: str = _cam_settings['awb']
_brightness: float = _cam_settings['brightness']
_contrast: float = _cam_settings['contrast']
_saturation: float = _cam_settings['saturation']
_sharpness: float = _cam_settings['sharpness']
_gain: float = _cam_settings['gain']

# ---------------------------------------------------------------------------
# Aufnahme-Profile  (gelten für BEIDE Modi: manuell UND Detection-getriggert)
# Jedes Profil: duration(s), resolution, fps, bitrate(kbps), slowmotion
# ---------------------------------------------------------------------------
RECORDING_PROFILES = {
    # ── Standard-Profile ────────────────────────────────────────────────────
    'normal_hd': {
        'label':      'Normal HD (1080p 30fps)',
        'resolution': '1080p',   # 1920×1080
        'fps':        30,
        'bitrate':    8000,      # kbps
        'slowmotion': False,
    },
    'normal_2k': {
        'label':      'Normal 2K (2560×1440 30fps)',
        'resolution': '2k',
        'fps':        30,
        'bitrate':    12000,
        'slowmotion': False,
    },
    'normal_4k': {
        'label':      'Normal 4K (4096×2160 25fps – max)',
        'resolution': '4k',
        'fps':        25,
        'bitrate':    25000,
        'slowmotion': False,
    },
    # ── Zeitlupe-Profile (High-FPS Aufnahme, Wiedergabe bei 30fps = Zeitlupe) ─
    'slowmo_720p': {
        'label':      'Zeitlupe 720p (120fps → 4× langsamer)',
        'resolution': 'slowmo_720p',  # 1280×720 @ 120fps
        'fps':        120,
        'bitrate':    12000,
        'slowmotion': True,
    },
    'slowmo_1080p': {
        'label':      'Zeitlupe 1080p (60fps → 2× langsamer)',
        'resolution': 'slowmo_1080p',  # 1920×1080 @ 60fps
        'fps':        60,
        'bitrate':    16000,
        'slowmotion': True,
    },
}

# Auflösungs-Map erweitert um Zeitlupe-Auflösungen
_RESOLUTION_MAP = {
    '480p':        ( 854,   480),
    '720p':        (1280,   720),
    '1080p':       (1920,  1080),
    '2k':          (2560,  1440),
    '4k':          (4096,  2160),
    'slowmo_720p': (1280,   720),   # 1280×720 @ 120fps
    'slowmo_1080p':(1920,  1080),   # 1920×1080 @ 60fps
}

# Persistente Aufnahme-Einstellungen (werden via API gesetzt)
REC_SETTINGS_FILE = '/config/rec-settings.json'

def _load_rec_settings() -> dict:
    """Lädt persistente Aufnahme-Einstellungen. Fallback auf profile 'normal_hd'."""
    try:
        data = json.loads(Path(REC_SETTINGS_FILE).read_text())
        if data.get('profile') in RECORDING_PROFILES:
            return data
    except Exception:
        pass
    return {'profile': 'normal_hd', 'duration': 15}

def _save_rec_settings(data: dict) -> None:
    try:
        Path(REC_SETTINGS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(REC_SETTINGS_FILE).write_text(json.dumps(data, indent=2))
    except Exception as exc:
        logger.error('Aufnahme-Einstellungen konnten nicht gespeichert werden: %s', exc)

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
    detection_running:     bool  = False
    detection_mode:        bool  = False   # True = Detection-Modus aktiv (blockiert manuelle Aufnahme)
    recording_running:     bool  = False
    recording_started_at:  float = 0.0     # time.monotonic() beim Start der Aufnahme
    recording_duration_s:  int   = 0       # geplante Aufnahmedauer in Sekunden
    audio_running:         bool  = False   # True = reine Audio-Aufnahme läuft
    audio_started_at:      float = 0.0
    audio_duration_s:      int   = 0
    detection_process:     subprocess.Popen = None
    recording_process:     subprocess.Popen = None
    last_error:            str  = None
    recording_file:        dict = None
    birds_recorded:        int  = 0        # Zähler Vogel-getriggerte Aufnahmen in dieser Session
    started_at:            str  = datetime.now(timezone.utc).isoformat()
    camera_hw_error:       bool  = False   # True = IMX708-Sensor hardware-stuck, Neustart nötig


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


def _camera_reset() -> bool:
    """Setzt den IMX708-Kamera-Sensor per sysfs unbind/bind zurück.
    Gibt True zurück wenn der Reset erfolgreich war (Sensor antwortet wieder).
    """
    SYSFS        = '/sys/bus/i2c/drivers/imx708'
    DEVICE       = '11-001a'
    DRIVER_LINK  = f'/sys/bus/i2c/devices/{DEVICE}/driver'  # Symlink existiert wenn Treiber gebunden
    try:
        unbind = Path(SYSFS) / 'unbind'
        bind   = Path(SYSFS) / 'bind'
        if not unbind.exists():
            logger.warning('Kamera-Reset: sysfs-Pfad nicht gefunden (%s) – Hardware nicht RPi-Kamera?', SYSFS)
            return False

        # Nur unbinden wenn Sensor aktuell gebunden ist (sonst ENODEV → direkt bind)
        if Path(DRIVER_LINK).exists():
            logger.info('Kamera-Reset: imx708 unbind …')
            unbind.write_text(DEVICE)
            time.sleep(15)  # Sensor braucht Zeit zum Zurücksetzen (Voltage stabilisierung)
        else:
            logger.info('Kamera-Reset: imx708 bereits ungebunden – warte auf Sensor-Recovery …')
            time.sleep(10)

        logger.info('Kamera-Reset: imx708 bind …')
        bind.write_text(DEVICE)
        time.sleep(5)   # Warte auf asynchronen Probe-Vorgang
        # Prüfe ob Bind erfolgreich: driver-Symlink existiert wenn der Sensor antwortet
        if Path(DRIVER_LINK).exists():
            logger.info('Kamera-Reset erfolgreich – imx708 wieder gebunden')
            with _lock:
                state.camera_hw_error = False
            return True
        else:
            logger.warning('Kamera-Reset: Sensor antwortet nicht – Hardware-Neustart (Pi-Reboot) erforderlich')
            with _lock:
                state.camera_hw_error = True
                state.last_error = 'Kamera-Hardware-Fehler: IMX708-Sensor antwortet nicht. Pi-Neustart erforderlich.'
            return False
    except PermissionError:
        logger.warning('Kamera-Reset: keine Schreibrechte für sysfs – Daemon läuft nicht als root')
        return False
    except Exception as exc:
        logger.warning('Kamera-Reset fehlgeschlagen: %s', exc)
        return False


class CameraManager:

    # Umgebungsvariablen für den Detection-Subprozess:
    # Hailo-Script braucht keine Host-Python-Libs (kein picamera2/ultralytics) –
    # Container-Python 3.13 ist ausreichend, da nur subprocess + re genutzt werden.
    _DETECTION_ENV: dict = {
        **os.environ,
        'HOME': '/tmp',
    }

    # ── Detection-Prozess-Management ─────────────────────────────────────────

    @staticmethod
    def _launch_detection_process() -> 'subprocess.Popen | None':
        """Startet den Hailo-Detection-Subprozess. Gibt Popen zurück oder None bei Fehler."""
        try:
            proc = subprocess.Popen(
                # Container-Python reicht: Hailo-Script importiert nur stdlib
                [
                    'python3', DETECTION_SCRIPT,
                    '--target-class', _detection_target,
                    '--threshold',    str(_detection_threshold),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp,
                env=CameraManager._DETECTION_ENV,
            )
            logger.info('Detection-Prozess gestartet PID=%d', proc.pid)
            return proc
        except Exception as exc:
            logger.error('Detection-Start fehlgeschlagen: %s', exc)
            state.last_error = str(exc)
            return None

    @staticmethod
    def start_detection() -> bool:
        """Startet Detection ohne Detection-Modus (Watchdog-Nutzung, kein Auto-Record)."""
        with _lock:
            if state.detection_running:
                return True
            proc = CameraManager._launch_detection_process()
            if proc:
                state.detection_process = proc
                state.detection_running = True
                return True
            return False

    @staticmethod
    def start_detection_mode() -> bool:
        """Aktiviert den Detection-Modus: blockiert manuelle Aufnahme,
        startet Detection-Loop mit Auto-Record bei Vogelerkennung."""
        with _lock:
            if state.detection_mode and state.detection_running:
                return True   # schon aktiv und Prozess läuft
            if state.recording_running:
                return False  # manuelle Aufnahme läuft noch
            # Vorhandenen Detection-Prozess explizit beenden (kann noch laufen, z.B.
            # nach manueller Aufnahme, die ihn via start_detection() neu gestartet hat).
            # Ohne diesen Kill würde ein zweiter Prozess die Kamera blockieren → rc=1.
            if state.detection_running and state.detection_process:
                _kill_process_group(state.detection_process)
                state.detection_running = False
                state.detection_process = None
                time.sleep(1)   # libcamera-Freigabe abwarten
            proc = CameraManager._launch_detection_process()
            if not proc:
                return False
            state.detection_process = proc
            state.detection_running = True
            if not state.detection_mode:
                state.detection_mode   = True
                state.birds_recorded   = 0
                logger.info('Detection-Modus aktiviert')
            else:
                logger.info('Detection-Modus: Prozess neu gestartet')
            return True

    @staticmethod
    def stop_detection_mode() -> bool:
        """Beendet den Detection-Modus sauber."""
        with _lock:
            if not state.detection_mode:
                return True
            state.detection_mode = False
            if state.detection_running and state.detection_process:
                _kill_process_group(state.detection_process)
                state.detection_running  = False
                state.detection_process  = None
            logger.info('Detection-Modus beendet (Vögel aufgenommen: %d)', state.birds_recorded)
            return True

    @staticmethod
    def stop_detection() -> bool:
        """Stoppt den Detection-Prozess (und deaktiviert ggf. Detection-Modus)."""
        with _lock:
            state.detection_mode = False
            if not state.detection_running:
                return True
            try:
                _kill_process_group(state.detection_process)
                state.detection_running = False
                state.detection_process = None
                logger.info('Detection gestoppt')
                return True
            except Exception as exc:
                logger.error('Detection-Stop fehlgeschlagen: %s', exc)
                state.detection_running = False
                state.detection_process = None
                state.last_error = str(exc)
                return False

    @staticmethod
    def _stop_detection_for_recording() -> None:
        """Stoppt Detection-Prozess und wartet auf libcamera-Freigabe.
        Muss MIT gehaltener _lock aufgerufen werden."""
        if state.detection_running and state.detection_process:
            _kill_process_group(state.detection_process)
            state.detection_running = False
            state.detection_process = None
            logger.info('Detection-Prozess für Aufnahme gestoppt')
        time.sleep(1)   # libcamera braucht Zeit zum Freigeben

    # ── Aufnahme ─────────────────────────────────────────────────────────────

    @staticmethod
    def record(duration: int = 15, resolution: str = '1080p', fps: int = 30,
               bitrate: int = 8000, slowmotion: bool = False,
               triggered_by: str = 'manual'):
        """Startet Recording. Blockiert bis Abschluss (in Background-Thread aufrufen).
        triggered_by: 'manual' oder 'detection'"""

        # ── Zustand prüfen und belegen ──────────────────────────────────────
        with _lock:
            if state.recording_running:
                return False, 'Recording läuft bereits'
            # Manuelle Aufnahme nur erlaubt wenn kein Detection-Modus
            if triggered_by == 'manual' and state.detection_mode:
                return False, 'Im Detection-Modus gesperrt'
            CameraManager._stop_detection_for_recording()
            state.recording_running    = True
            state.recording_started_at = time.monotonic()
            state.recording_duration_s = duration

        # ── Aufnahme (Lock freigegeben) ─────────────────────────────────────
        try:
            w, h = _RESOLUTION_MAP.get(resolution, (1920, 1080))

            recording_dir = Path(VIDEO_BASE_DIR)
            recording_dir.mkdir(parents=True, exist_ok=True)

            # Format: Jahr_KW_Tag_Uhrzeit_Aufloesung_fps  (z.B. 2026_11_14_190045_1920x1080_30fps)
            ts         = datetime.now().strftime('%Y_%V_%d_%H%M%S')
            # Zeitlupe → rohes h264 (mehrere Playback-Versionen per ffmpeg)
            # Normal  → libav-MP4 direkt (Audio+Video im gleichen Prozess, perfekt synchron)
            if slowmotion:
                video_file = recording_dir / f'{ts}_{w}x{h}_{fps}fps.h264'
            else:
                video_file = recording_dir / f'{ts}_{w}x{h}_{fps}fps.mp4'

            # Mic-Eingangspegel sicherstellen (USB-Audio-Karte setzt ihn manchmal auf 0%)
            try:
                subprocess.run(
                    ['amixer', '-c', '0', 'sset', 'Mic', '50%'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            except Exception:
                pass

            if slowmotion:
                # Zeitlupe: rohes h264, kein Audio, mehrere Playback-Versionen per ffmpeg
                video_cmd = [
                    'rpicam-vid',
                    '--width', str(w), '--height', str(h),
                    '--framerate', str(fps),
                    '--bitrate', str(bitrate * 1000),
                    '-o', str(video_file),
                    '--inline',
                    '--rotation', '0',
                    '--autofocus-mode', 'manual',
                    '--lens-position', str(_lens_position),
                    '--ev', str(_ev),
                    '--awb', _awb,
                    '--brightness', str(_brightness),
                    '--contrast', str(_contrast),
                    '--saturation', str(_saturation),
                    '--sharpness', str(_sharpness),
                    '--gain', str(_gain),
                    '--timeout', str(duration * 1000),
                ]
                video_proc = subprocess.Popen(video_cmd,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                audio_proc = None
            else:
                # ── Normal: rpicam-vid --codec libav mit eingebautem Audio ──
                # Ein einziger Prozess muxed Video+Audio in die gleiche Timeline.
                # Kein Sync-Offset, kein ffmpeg-Merge, kein TXT-Sidecar nötig.
                video_cmd = [
                    'rpicam-vid', '-n',
                    '--width', str(w), '--height', str(h),
                    '--framerate', str(fps),
                    '--rotation', '0',
                    '--autofocus-mode', 'manual',
                    '--lens-position', str(_lens_position),
                    '--ev', str(_ev),
                    '--awb', _awb,
                    '--brightness', str(_brightness),
                    '--contrast', str(_contrast),
                    '--saturation', str(_saturation),
                    '--sharpness', str(_sharpness),
                    '--gain', str(_gain),
                    '--codec', 'libav',
                    '--libav-format', 'mp4',
                    '--libav-audio',
                    '--audio-codec', 'aac',
                    '--audio-samplerate', '48000',
                    '--audio-source', 'alsa',
                    '--audio-device', 'plughw:0,0',
                    '--timeout', str(duration * 1000),
                    '-o', str(video_file),
                ]
                video_proc = subprocess.Popen(video_cmd,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                audio_proc = None

            logger.info('Recording [%s] %ds %s %dfps → %s | Load: %.2f %.2f %.2f',
                        triggered_by, duration, resolution, fps, video_file.name,
                        *os.getloadavg())

            with _lock:
                state.recording_process = video_proc

            # ── Warten bis rpicam-vid sich nach --timeout selbst beendet ──
            # Kill nur als Fallback wenn Prozess hängt (timeout + 10s Puffer).
            fallback_timeout = duration + 10
            deadline = time.monotonic() + fallback_timeout
            while time.monotonic() < deadline:
                if video_proc.poll() is not None:
                    break
                time.sleep(0.5)

            # ── Fallback-Kill falls Prozess hängt ───────────────────────────
            if video_proc.poll() is None:
                try:
                    _kill_process_group(video_proc, timeout=5)
                    logger.warning('rpicam-vid musste per Kill beendet werden')
                except Exception as e:
                    logger.warning('rpicam-vid Kill fehlgeschlagen: %s', e)

            with _lock:
                state.recording_process = None

            # stderr von rpicam-vid auslesen (nicht-blockierend nach Kill)
            try:
                stderr_out = video_proc.stderr.read().decode('utf-8', errors='replace').strip()
            except Exception:
                stderr_out = ''
            if stderr_out:
                for line in stderr_out.splitlines():
                    if 'ERROR' in line or 'error' in line.lower():
                        logger.error('rpicam-vid: %s', line)
                    else:
                        logger.debug('rpicam-vid: %s', line)

            # Kurze Pause: Dateisystem-Flush sicherstellen (wie in alten Skripten +1s)
            time.sleep(2)

            if video_file.exists():
                rec_info = {
                    'video':     str(video_file),
                    'audio':     None,  # Bei libav-MP4 bereits eingebettet
                    'timestamp': ts,
                }
                with _lock:
                    state.recording_file = rec_info
                logger.info('Recording abgeschlossen: %s | Load: %.2f %.2f %.2f',
                            video_file.name, *os.getloadavg())

                if slowmotion:
                    # Zeitlupe h264 → mehrere MP4-Playback-Versionen per ffmpeg
                    ok, results = CameraManager._convert_one(video_file, recording_fps=fps, slowmotion=True)
                    if ok:
                        logger.info('Slowmo-Konvertierung: %d Datei(en)', len(results))
                        for mp4 in results:
                            CameraManager.transfer_all(mp4)
                    else:
                        logger.warning('Konvertierung fehlgeschlagen: %s', results[0] if results else '?')
                        with _lock:
                            state.last_error = f'Konvertierung: {results[0] if results else "Fehler"}'
                else:
                    # Normal: libav-MP4 ist fertig, direkt transferieren
                    CameraManager.transfer_all(str(video_file))

                return True, rec_info

            logger.error('Video-Datei nicht erstellt: %s', video_file)
            err_msg = f'Video-Datei nicht erstellt ({video_file.name})'
            if stderr_out:
                first_error = next((l for l in stderr_out.splitlines() if 'ERROR' in l), stderr_out.splitlines()[-1] if stderr_out else '')
                err_msg = first_error.strip() or err_msg
            with _lock:
                state.last_error = err_msg
            return False, err_msg

        except Exception as exc:
            logger.error('Recording fehlgeschlagen: %s', exc)
            with _lock:
                state.last_error = str(exc)
            return False, str(exc)

        finally:
            with _lock:
                state.recording_running    = False
                state.recording_process    = None
                state.recording_started_at = 0.0
                state.recording_duration_s = 0
                if triggered_by == 'detection':
                    state.birds_recorded += 1
                _det_mode = state.detection_mode
            # Detection neu starten – detection_mode wiederherstellen falls aktiv
            if _det_mode:
                CameraManager.start_detection_mode()
            else:
                CameraManager.start_detection()

    @staticmethod
    def record_audio(duration: int = 60):
        """Startet eine reine Audio-Aufnahme (kein Video) mit arecord.
        Orientiert an Legacy-Skript ai-had-audio-remote-param-vogel-libcamera-single.py.
        Gibt (ok, wav_path_or_error) zurück."""
        with _lock:
            if state.recording_running:
                return False, 'Video-Recording läuft bereits'
            if state.audio_running:
                return False, 'Audio-Aufnahme läuft bereits'
            state.audio_running    = True
            state.audio_started_at = time.monotonic()
            state.audio_duration_s = duration

        try:
            recording_dir = Path(VIDEO_BASE_DIR)
            recording_dir.mkdir(parents=True, exist_ok=True)

            # Dateiname: Jahr_KW_Tag_Uhrzeit_audio_Xmin.wav
            ts  = datetime.now().strftime('%Y_%V_%d_%H%M%S')
            dur_min = max(1, round(duration / 60))
            wav = recording_dir / f'{ts}_audio_{dur_min}min.wav'

            # arecord: 44.1 kHz, Mono, 16-bit signed LE, WAV-Format
            # Kein -D: nutzt ALSA-Default (erstes verfügbares Mikrofon)
            # Kein -d Flag: Dauer via Python-Sleep + Kill (analog Video)
            audio_cmd = [
                'arecord', '-f', 'S16_LE', '-r', '44100', '-c', '1', '-t', 'wav',
                str(wav),
            ]

            # Mic-Eingangspegel sicherstellen
            try:
                subprocess.run(
                    ['amixer', '-c', '0', 'sset', 'Mic', '50%'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            except Exception:
                pass

            logger.info('Audio-Only-Recording gestartet: %ds → %s', duration, wav.name)
            audio_proc = subprocess.Popen(
                audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            with _lock:
                state.recording_process = audio_proc

            # Dauer abwarten (1s-Schritte für sofortigen Kill-Response)
            deadline = time.monotonic() + duration
            while time.monotonic() < deadline:
                if audio_proc.poll() is not None:
                    logger.warning('arecord vorzeitig beendet (rc=%d)', audio_proc.returncode)
                    break
                time.sleep(1)

            # Prozess explizit stoppen
            if audio_proc.poll() is None:
                try:
                    _kill_process_group(audio_proc, timeout=5)
                except Exception as e:
                    logger.warning('arecord Kill fehlgeschlagen: %s', e)

            with _lock:
                state.recording_process = None

            # stderr auswerten
            try:
                stderr_out = audio_proc.stderr.read().decode('utf-8', errors='replace').strip()
            except Exception:
                stderr_out = ''
            if stderr_out:
                for line in stderr_out.splitlines():
                    if 'error' in line.lower():
                        logger.error('arecord: %s', line)
                    else:
                        logger.debug('arecord: %s', line)

            time.sleep(1)  # Dateisystem-Flush

            if wav.exists() and wav.stat().st_size > 4096:
                logger.info('Audio-Aufnahme abgeschlossen: %s (%.1f MB)',
                            wav.name, wav.stat().st_size / 1048576)
                CameraManager.transfer_all(str(wav))
                return True, str(wav)

            err = f'WAV-Datei nicht erstellt oder leer ({wav.name})'
            if stderr_out:
                err = next((l for l in stderr_out.splitlines() if 'error' in l.lower()),
                           stderr_out.splitlines()[-1] if stderr_out else err)
            logger.error(err)
            with _lock:
                state.last_error = err
            return False, err

        except Exception as exc:
            logger.error('Audio-Aufnahme fehlgeschlagen: %s', exc)
            with _lock:
                state.last_error = str(exc)
            return False, str(exc)

        finally:
            with _lock:
                state.audio_running    = False
                state.audio_started_at = 0.0
                state.audio_duration_s = 0
                state.recording_process = None

    @staticmethod
    def _find_latest_h264() -> 'Path | None':
        """Findet die neueste h264-Datei in VIDEO_BASE_DIR (Fallback nach Neustart)."""
        base = Path(VIDEO_BASE_DIR)
        if not base.exists():
            return None
        files = sorted(base.rglob('*.h264'), key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0] if files else None

    @staticmethod
    def _run_ffmpeg_convert(h264: 'Path', mp4: 'Path', input_fps: int,
                            wav: 'Path | None' = None,
                            audio_delay_s: float = 0.0) -> 'tuple[bool, str]':
        """Hilfsfunktion: Konvertiert h264 → mp4 mit angegebener Input-fps.
        audio_delay_s: Kamera-Init-Offset in Sekunden (aus TXT-Sidecar).
                       Positiver Wert → Audio um diesen Betrag nach hinten schieben
                       (arecord lief vor dem ersten Video-Frame).
        Gibt (ok, mp4_path_or_error) zurück."""
        audio_valid = wav is not None and wav.exists() and wav.stat().st_size > 4096
        # -f h264 erzwingt den Raw-H264-Demuxer; -r überschreibt VUI-Framerate
        # (rpicam-vid/libcamera auf Pi5 kodiert VUI manchmal mit doppelter fps)
        cmd = ['ffmpeg', '-y', '-fflags', '+genpts',
               '-f', 'h264', '-r', str(input_fps), '-i', str(h264)]
        if audio_valid:
            # -itsoffset VOR -i audio: verschiebt Audio-Stream um audio_delay_s
            # nach hinten → kompensiert Kamera-Init-Zeit
            # Nur setzen wenn messbarer Offset vorhanden (>10ms)
            if audio_delay_s > 0.01:
                cmd += ['-itsoffset', f'{audio_delay_s:.3f}']
            cmd += ['-i', str(wav),
                    '-c:v', 'copy', '-c:a', 'aac',
                    # dynaudnorm statt loudnorm: kein interner Lookahead-Delay
                    # f=150: Rahmengröße 150 Frames, g=15: Gauss-Glättung
                    '-af', 'volume=2.0,dynaudnorm=f=150:g=15',
                    '-movflags', '+faststart']
        else:
            cmd += ['-c:v', 'copy', '-movflags', '+faststart']
        cmd.append(str(mp4))
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        if result.returncode == 0 and mp4.exists():
            return True, str(mp4)
        err = result.stderr.decode(errors='replace')[:500]
        return False, err

    @staticmethod
    def _convert_one(h264: 'Path', recording_fps: int = 30, slowmotion: bool = False) -> tuple:
        """Konvertiert eine einzelne h264 → mp4. Gibt (ok, [mp4_paths] | [error_str]) zurück.
        Nutzt -c:v copy + -fflags +genpts (schnell, kein Re-Encoding, kein Qualitätsverlust).
        recording_fps: tatsächliche Aufnahme-Framerate (für Zeitstempel-Berechnung)
        slowmotion:    True → mehrere MP4-Versionen mit verschiedenen Playback-fps erstellen
                              Namensschema: {stem}_pb{playback}fps.mp4 und {stem}.mp4 (Original)
        """
        try:
            wav = h264.with_suffix('.wav')

            # TXT-Sidecar lesen (fps + audio_delay_s)
            _txt = h264.with_suffix('.txt')
            _sidecar_fps: int | None = None
            _audio_delay_s: float = 0.0
            if _txt.exists():
                try:
                    _sidecar = dict(
                        line.split('=', 1)
                        for line in _txt.read_text().splitlines()
                        if '=' in line
                    )
                    _sidecar_fps   = int(_sidecar.get('fps', recording_fps))
                    _audio_delay_s = float(_sidecar.get('audio_delay_s', 0.0))
                    _sm            = _sidecar.get('slowmotion', str(slowmotion)).strip().lower()
                    slowmotion     = _sm in ('true', '1')
                except Exception:
                    pass
            # Sidecar-fps hat Vorrang vor übergebenem recording_fps
            if _sidecar_fps is not None:
                recording_fps = _sidecar_fps
            else:
                # Fallback: fps aus Dateiname parsen (z.B. ...25fps.h264)
                import re as _re
                _m = _re.search(r'_(\d+)fps\.h264$', h264.name)
                if _m:
                    recording_fps = int(_m.group(1))

            if slowmotion:
                # ── Zeitlupe: mehrere Playback-Versionen (kein Audio) ───────
                # Playback-fps-Stufen: 10, 20, 30 + Original-Geschwindigkeit
                # Beispiel 120fps aufgenommen → _pb10fps = 12x langsamer, _pb30fps = 4x
                playback_fps_list = [10, 20, 30, recording_fps]
                logger.info('Slowmo-Konvertierung: %s → %d Playback-Versionen %s',
                            h264.name, len(playback_fps_list), playback_fps_list)
                created = []
                errors  = []
                for pb_fps in playback_fps_list:
                    if pb_fps == recording_fps:
                        # Original-Geschwindigkeit → Standard-Name (kein _pb-Suffix)
                        mp4 = h264.with_suffix('.mp4')
                    else:
                        mp4 = h264.with_name(f'{h264.stem}_pb{pb_fps}fps.mp4')
                    ok, res = CameraManager._run_ffmpeg_convert(h264, mp4, pb_fps, wav=None, audio_delay_s=0.0)
                    if ok:
                        logger.info('  ✓ %s (%.1f MB)', mp4.name, mp4.stat().st_size / 1048576)
                        created.append(res)
                    else:
                        logger.error('  ✗ Fehler bei pb%dfps: %s', pb_fps, res[:200])
                        errors.append(res)
                if created:
                    return True, created
                return False, [errors[0] if errors else 'Alle Konvertierungen fehlgeschlagen']
            else:
                # ── Normal: einzelne MP4, fps bereits im h264-Dateinamen ───
                mp4 = h264.with_suffix('.mp4')
                logger.info('Konvertierung: %s%s → %s',
                            h264.name, ' (+Audio)' if wav.exists() else '', mp4.name)
                ok, res = CameraManager._run_ffmpeg_convert(
                    h264, mp4, recording_fps, wav=wav, audio_delay_s=_audio_delay_s)
                if ok:
                    logger.info('Konvertierung abgeschlossen: %s (%.1f MB)',
                                mp4.name, Path(mp4).stat().st_size / 1048576)
                    return True, [res]
                logger.error('ffmpeg Fehler: %s', res)
                return False, [res]
        except Exception as exc:
            logger.error('Konvertierung fehlgeschlagen: %s', exc)
            return False, [str(exc)]

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
            ok, results = CameraManager._convert_one(h264)
            if ok:
                converted += 1
                for mp4 in results:
                    CameraManager.transfer_all(mp4)
            else:
                errors.append(f'{h264.name}: {results[0] if results else "Fehler"}')
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
        ok, results = CameraManager._convert_one(h264)
        if ok:
            with _lock:
                if state.recording_file:
                    state.recording_file['mp4'] = results[0]
        return ok, results[0] if results else ''

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
            ssh_cmd = ('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
                       ' -o LogLevel=ERROR -o ConnectTimeout=10'
                       + (f' -i {key_file}' if Path(key_file).exists() else ''))
            cmd = ['rsync', '-az', '-e', ssh_cmd, mp4_path, dest]
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
        all_files = []
        for pattern, ftype in [('*.mp4', 'video'), ('*.wav', 'audio')]:
            for f in base.rglob(pattern):
                # WAV: nur manuell aufgenommene Audio-Dateien zeigen (_audio im Namen)
                # Begleit-WAVs von Video-Aufnahmen (z.B. 1920x1080_30fps.wav) werden ausgeblendet
                # Passt auf: _audio.wav (alt) und _audio_1min.wav (neu)
                if ftype == 'audio' and '_audio' not in f.name:
                    continue
                try:
                    rel = str(f.relative_to(base))
                except ValueError:
                    rel = f.name
                mtime = f.stat().st_mtime
                all_files.append({
                    'name':     f.name,
                    'rel_path': rel,
                    'size_mb':  round(f.stat().st_size / 1_048_576, 1),
                    'created':  datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'date':     datetime.fromtimestamp(mtime).strftime('%Y-%m-%d'),
                    'type':     ftype,
                    '_mtime':   mtime,
                })
        all_files.sort(key=lambda x: x['_mtime'], reverse=True)
        for entry in all_files:
            del entry['_mtime']
        return all_files[:100]


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
        load = os.getloadavg()
        try:
            cpu_temp = round(int(Path('/sys/class/thermal/thermal_zone0/temp').read_text().strip()) / 1000.0, 1)
        except Exception:
            cpu_temp = None
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
        }
    except Exception:
        system = {}

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
        'today_recordings':     _count_today_recordings(),
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
        'version':              APP_VERSION,
        'active_engine':        _active_engine,
        'detection_target':     _detection_target,
        'detection_threshold':  _detection_threshold,
        'last_detection':       _read_last_detection(),
        'lens_position':        _lens_position,
        'ev':                   _ev,
        'awb':                  _awb,
        'brightness':           _brightness,
        'contrast':             _contrast,
        'saturation':           _saturation,
        'sharpness':            _sharpness,
        'gain':                 _gain,
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
    global DETECTION_SCRIPT, _active_engine
    if request.method == 'GET':
        return jsonify({
            'active':  _active_engine,
            'engines': DETECTION_ENGINES,
        })
    data   = request.get_json(silent=True) or {}
    engine = data.get('engine', '')
    if engine not in DETECTION_ENGINES:
        return jsonify({'error': f'Unbekannte Engine: {engine}'}), 400
    if engine == _active_engine:
        return jsonify({'success': True, 'active': _active_engine, 'changed': False})
    with _lock:
        was_running = state.detection_running
        was_mode    = state.detection_mode
        if was_running:
            CameraManager.stop_detection()
        _active_engine   = engine
        DETECTION_SCRIPT = DETECTION_ENGINES[engine]['script']
    _save_active_engine(engine)
    logger.info('Detection-Engine gewechselt auf: %s (%s)', engine, DETECTION_SCRIPT)
    if was_running:
        if was_mode:
            CameraManager.start_detection_mode()
        else:
            CameraManager.start_detection()
    return jsonify({'success': True, 'active': _active_engine, 'changed': True})


@app.route('/api/detection-settings', methods=['GET', 'POST'])
@require_auth
def api_detection_settings():
    """Liest oder setzt Detection-Zielklasse und Confidence-Schwelle.
    GET  → { "target_class": "bird"|"person"|"dog"|"cat"|"all4", "threshold": 0.45 }
    POST { "target_class": "bird"|"person"|"dog"|"cat"|"all4", "threshold": 0.45 }
    Bei laufender Detection wird diese neu gestartet, damit die neuen Werte wirken.
    """
    global _detection_target, _detection_threshold
    if request.method == 'GET':
        return jsonify({'target_class': _detection_target, 'threshold': _detection_threshold})
    data = request.get_json(silent=True) or {}
    target = data.get('target_class', _detection_target)
    if target not in ('bird', 'person', 'dog', 'cat', 'all4'):
        return jsonify({'error': f'Ungültige Zielklasse: {target}. Erlaubt: bird, person, dog, cat, all4'}), 400
    try:
        threshold = float(data.get('threshold', _detection_threshold))
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold muss eine Zahl zwischen 0.1 und 0.95 sein'}), 400
    threshold = max(0.1, min(0.95, threshold))
    with _lock:
        was_running = state.detection_running
        was_mode    = state.detection_mode
        if was_running:
            CameraManager.stop_detection()
        _detection_target    = target
        _detection_threshold = threshold
    _save_detection_settings(target, threshold)
    logger.info('Detection-Settings geändert: target=%s threshold=%.2f', target, threshold)
    if was_running:
        if was_mode:
            CameraManager.start_detection_mode()
        else:
            CameraManager.start_detection()
    return jsonify({'success': True, 'target_class': _detection_target, 'threshold': _detection_threshold})


@app.route('/api/camera-settings', methods=['GET', 'POST'])
@require_auth
def api_camera_settings():
    """Liest oder setzt Kamera-Einstellungen (lens_position, ev, awb, brightness, contrast, saturation, sharpness, gain).
    GET  → { "lens_position": 3.0, "ev": 0.0, "awb": "auto", "brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "sharpness": 1.0, "gain": 1.0 }
    POST { "brightness": 0.5 } oder beliebige Kombination der Parameter
    """
    global _lens_position, _ev, _awb, _brightness, _contrast, _saturation, _sharpness, _gain
    if request.method == 'GET':
        return jsonify({'lens_position': _lens_position, 'ev': _ev, 'awb': _awb, 'brightness': _brightness, 'contrast': _contrast, 'saturation': _saturation, 'sharpness': _sharpness, 'gain': _gain})
    
    data = request.get_json(silent=True) or {}
    lp, ev, awb = _lens_position, _ev, _awb
    brightness, contrast, saturation, sharpness, gain = _brightness, _contrast, _saturation, _sharpness, _gain
    
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
        _lens_position = lp
        _ev = ev
        _awb = awb
        _brightness = brightness
        _contrast = contrast
        _saturation = saturation
        _sharpness = sharpness
        _gain = gain
    
    _save_camera_settings({'lens_position': lp, 'ev': ev, 'awb': awb, 'brightness': brightness, 'contrast': contrast, 'saturation': saturation, 'sharpness': sharpness, 'gain': gain})
    logger.info('Kamera-Einstellungen geändert: lens_position=%.1f, ev=%.1f, awb=%s, brightness=%.1f, contrast=%.1f, saturation=%.1f, sharpness=%.1f, gain=%.1f', lp, ev, awb, brightness, contrast, saturation, sharpness, gain)
    return jsonify({'success': True, 'lens_position': _lens_position, 'ev': _ev, 'awb': _awb, 'brightness': _brightness, 'contrast': _contrast, 'saturation': _saturation, 'sharpness': _sharpness, 'gain': _gain})


@app.route('/api/rec-settings', methods=['GET', 'POST'])
@require_auth
def api_rec_settings():
    """Liest oder speichert persistente Aufnahme-Einstellungen (Profil + Dauer)."""
    if request.method == 'GET':
        return jsonify(_load_rec_settings())
    data = request.get_json(silent=True) or {}
    profile  = data.get('profile', 'normal_hd')
    duration = min(max(int(data.get('duration', 15)), 3), 600)   # max 10 min = 600 s
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
    duration     = min(max(int(data.get('duration', 15)), 3), 600)   # max 10 min = 600 s

    if profile_name and profile_name in RECORDING_PROFILES:
        profile    = RECORDING_PROFILES[profile_name]
        resolution = profile['resolution']
        fps        = profile['fps']
        bitrate    = profile['bitrate']
        slowmotion = profile['slowmotion']
    else:
        # Fallback: direkte Parameter (Legacy-Kompatibilität)
        resolution = data.get('resolution', '1080p')
        fps        = min(max(int(data.get('fps',     30)),    1), 120)
        bitrate    = min(max(int(data.get('bitrate', 8000)), 1000), 25000)
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
    duration = min(max(int(data.get('duration', 60)), 3), 3600)

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
def api_download():
    # Token entweder als Bearer-Header ODER als ?token= Query-Parameter (für <a href> Downloads)
    auth = request.headers.get('Authorization', '')
    token_val = auth[7:] if auth.startswith('Bearer ') else request.args.get('token', '')
    if not token_val:
        abort(401)
    try:
        jwt.decode(token_val, JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        abort(401)
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
    # Zugehörige Dateien mitbereinigen (H264-Quelle + WAV bei Video-Aufnahmen)
    for ext in ('.h264', '.wav'):
        companion = target.with_suffix(ext)
        if companion.exists():
            companion.unlink()
            deleted.append(companion.name)
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
    key_exists = Path(key_file).exists()
    key_opts = ['-i', key_file] if key_exists else []
    cmd = ['ssh',
           '-o', 'StrictHostKeyChecking=no',
           '-o', 'UserKnownHostsFile=/dev/null',
           '-o', 'ConnectTimeout=8',
           '-o', 'BatchMode=yes',
           ] + key_opts + [f'{user}@{host}', 'echo VERBINDUNG_OK']
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
    base = Path(VIDEO_BASE_DIR)
    h264_files = list(base.rglob('*.h264')) if base.exists() else []
    pending = [f for f in h264_files if not f.with_suffix('.mp4').exists()]
    return jsonify({'pending': len(pending)})


# ── Live-Stream (MJPEG) ──────────────────────────────────────────────────────

_STREAM_FRAME = Path('/tmp/det_latest_frame.jpg')


@app.route('/api/snapshot')
def api_snapshot():
    """Einzelnes JPEG-Frame der Detection-Kamera (für JS-Polling).
    Token via ?token= Query-Parameter oder Bearer-Header."""
    auth = request.headers.get('Authorization', '')
    token_val = auth[7:] if auth.startswith('Bearer ') else request.args.get('token', '')
    if not token_val:
        abort(401)
    try:
        jwt.decode(token_val, JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        abort(401)
    if not _STREAM_FRAME.exists():
        abort(503)   # Noch kein Frame verfügbar
    resp = send_file(str(_STREAM_FRAME), mimetype='image/jpeg')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


# ── Web-GUI ───────────────────────────────────────────────────────────────────

WEB_DIR = Path(__file__).parent / 'web'


@app.route('/')
@app.route('/index.html')
def serve_index():
    f = WEB_DIR / 'index.html'
    if f.exists():
        return send_file(str(f))
    return '<!doctype html><h1>Web-GUI nicht gefunden</h1><p>web/index.html fehlt.</p>', 404


@app.route('/web/<path:filename>')
def serve_static(filename):
    """Statische Dateien aus dem web/-Verzeichnis (z. B. logo.png)."""
    return send_from_directory(str(WEB_DIR), filename)


@app.route('/cert.pem')
def serve_cert():
    """Self-signed Zertifikat zum Download (kein Auth noetig).
    Browser-Import: Einstellungen Zertifikate Behoerden Importieren."""
    cert = Path(CERT_FILE)
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


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    _check_config()

    CameraManager.start_detection_mode()

    def _detection_watchdog():
        """Überwacht Detection-Prozess. Bei Detection-Modus + Vogel (rc=0): Aufnahme starten."""
        time.sleep(10)
        consecutive_failures = 0   # Zählt aufeinander folgende rc=1 Exits (V4L2-Fehler)
        while True:
            time.sleep(5)
            with _lock:
                if not state.detection_running or state.detection_process is None:
                    continue
                proc = state.detection_process
                rc = proc.poll()
                if rc is None:
                    continue  # Prozess läuft noch
                logger.warning('Detection-Prozess beendet (rc=%d)', rc)
                state.detection_running = False
                state.detection_process = None
                should_record = state.detection_mode and rc == 0
                should_restart = not state.recording_running and (not should_record)

            if rc == 0:
                consecutive_failures = 0   # Sauber beendet (Vogel erkannt)
            else:
                consecutive_failures += 1

            if should_record:
                consecutive_failures = 0
                # Vogel erkannt im Detection-Modus → Aufnahme aus gespeicherten Einstellungen starten
                settings = _load_rec_settings()
                profile_name = settings.get('profile', 'normal_hd')
                duration     = settings.get('duration', 15)
                profile      = RECORDING_PROFILES.get(profile_name, RECORDING_PROFILES['normal_hd'])
                logger.info('Detection-Modus: Vogel erkannt – starte Aufnahme (Profil: %s)', profile_name)
                threading.Thread(
                    target=CameraManager.record,
                    kwargs={
                        'duration':    duration,
                        'resolution':  profile['resolution'],
                        'fps':         profile['fps'],
                        'bitrate':     profile['bitrate'],
                        'slowmotion':  profile['slowmotion'],
                        'triggered_by': 'detection',
                    },
                    daemon=True,
                    name='det-rec',
                ).start()
            elif should_restart:
                if consecutive_failures >= 3:
                    consecutive_failures = 0
                    # imx708-Reset nur wenn KEIN Hailo-Script (rpicam-hello braucht keinen
                    # sysfs-Reset – Fehler dort = npicam-init-Problem, kein Sensor-Stuck).
                    if _active_engine == 'hailo':
                        logger.warning(
                            'Hailo rpicam-hello Startfehler × 3 – warte 15s vor erneutem Versuch')
                        time.sleep(15)
                    else:
                        logger.warning('Kamera-Reset nach 3 aufeinander folgenden Fehlern …')
                        reset_ok = _camera_reset()
                        if not reset_ok:
                            logger.warning('Kamera-Hardware-Fehler: Retry in 5 Minuten …')
                            time.sleep(300)
                        else:
                            time.sleep(3)
                else:
                    time.sleep(2)
                CameraManager.start_detection()

    watchdog = threading.Thread(target=_detection_watchdog, daemon=True, name='detection-watchdog')
    watchdog.start()

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
