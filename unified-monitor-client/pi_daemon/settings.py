"""Persistente Einstellungen: Detection-Engine, Detection-Ziel/Schwelle, Kamera, Aufnahme-Profile.

Laufzeit-Werte (_active_engine, DETECTION_SCRIPT, _detection_*, Kamera-Werte) werden von
der API neu zugewiesen – andere Module müssen sie deshalb als settings.<name> lesen,
nie per "from .settings import <name>" (das wäre eine veraltete Kopie).
"""
import json
import os
from pathlib import Path

from .config import logger


# Verfügbare Detection-Engines (key → Dateipfad im Container)
_SCRIPT_BASE = '/home/roimme/vogel-kamera-linux/raspberry-pi-scripts'
DETECTION_ENGINES: dict = {
    'hailo':    {'label': '🔬 Hailo NPU (AI HAT+, 25fps, <5% CPU)',  'script': f'{_SCRIPT_BASE}/unified-camera-monitor-hailo.py'},
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
DETECTION_TARGETS = ('bird', 'person', 'dog', 'cat', 'all4')
DETECTION_SETTINGS_FILE = '/config/detection-settings.json'


def _load_detection_settings() -> dict:
    """Lädt target_class und threshold. Fallback: Vogel + 0.45."""
    try:
        data = json.loads(Path(DETECTION_SETTINGS_FILE).read_text())
        target = data.get('target_class', 'bird')
        if target not in DETECTION_TARGETS:
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
        'label':      'Zeitlupe HQ (2304×1296 @ 56fps → 1.9× langsamer) ✨',
        'resolution': 'slowmo_hq',  # 2304×1296 @ 56fps - Bessere Qualität
        'fps':        56,
        'bitrate':    18000,
        'slowmotion': True,
    },
    'slowmo_1080p': {
        'label':      'Zeitlupe 120fps (1536×864 @ 120fps → 4× langsamer)',
        'resolution': 'slowmo_fast',  # 1536×864 @ 120fps - Ultra-Highspeed
        'fps':        120,
        'bitrate':    14000,
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
    'slowmo_hq':   (2304,  1296),   # 2304×1296 @ 56fps - Bessere Qualität
    'slowmo_fast': (1536,   864),   # 1536×864 @ 120fps - Ultra-Highspeed
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
