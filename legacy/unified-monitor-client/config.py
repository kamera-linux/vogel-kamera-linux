"""
Konfiguration für Unified Monitor Client
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Lade .env Datei falls vorhanden
ENV_FILE = Path(__file__).parent / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# SSH-Konfiguration (aus .env oder Defaults)
SSH_KEY = os.getenv('SSH_KEY', os.path.expanduser('~/.ssh/id_rsa_ai-had'))
SSH_USER = os.getenv('SSH_USER', 'roimme')
SSH_HOST = os.getenv('SSH_HOST', 'raspberrypi-5-ai-had')
SSH_PORT = int(os.getenv('SSH_PORT', '22'))
SSH_TIMEOUT = 5
SSH_RETRIES = 3
SSH_RETRY_DELAY = 2

# Remote-Paths
PI_HOME = f'/home/{SSH_USER}'
REMOTE_REPO_DIR = f'{PI_HOME}/vogel-kamera-linux'
REMOTE_SCRIPT_DIR = f'{REMOTE_REPO_DIR}/raspberry-pi-scripts'
REMOTE_VIDEO_BASE = f'{PI_HOME}/Videos/Vogelhaus'
REMOTE_LOG_FILE = '/tmp/unified-camera-monitor.log'

# Lokale Paths
LOCAL_REPO_DIR = Path(__file__).parent.parent
SCRIPT_DIR = LOCAL_REPO_DIR / 'raspberry-pi-scripts'
CLIENT_VIDEO_BASE = Path.home() / 'Videos' / 'Vogelhaus'

# Logging
LOG_COLORS = {
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[1;34m',
    'cyan': '\033[0;36m',
    'magenta': '\033[0;35m',
    'reset': '\033[0m',
}

# Monitor-Parameter
DEFAULT_THRESHOLD = 0.5
DEFAULT_COOLDOWN = 15
DEFAULT_TRIGGER_DURATION = 1.0
DEFAULT_AUDIO_THRESHOLD = 0.3
STATUS_INTERVAL = 300  # 5 Minuten

# Video-Watcher
VIDEO_WATCH_INTERVAL = 15  # Sekunden
VIDEO_SYNC_TIMEOUT = 300  # 5 Minuten pro Video
RECENT_DAYS = 7  # Nur Videos der letzten 7 Tage beachten

# Recording-Modi
RECORDING_MODES = {
    'normal': {
        'desc': 'Standard-Modus (1920x1080 @ 30fps + Audio)',
        'audio': True,
    },
    'slowmo': {
        'desc': 'Zeitlupen-Modus HQ (2304x1296 @ 56fps)',
        'audio': False,
    },
    'slowmo-fast': {
        'desc': 'Zeitlupen-Modus Ultra-Highspeed (1536x864 @ 120fps)',
        'audio': False,
    },
    '4k': {
        'desc': 'Cinema 4K-Modus (4096x2160 @ 25fps + Audio)',
        'audio': True,
    },
    'ai-had': {
        'desc': 'AI-HAD Modus mit Audio-Erkennung (1920x1080 @ 30fps)',
        'audio': True,
    },
}
