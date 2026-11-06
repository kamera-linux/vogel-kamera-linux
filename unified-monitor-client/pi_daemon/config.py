"""Konfiguration (ausschließlich Umgebungsvariablen), Logging, Startprüfung."""
import logging
import os
import sys


# ---------------------------------------------------------------------------
# App-Version
# ---------------------------------------------------------------------------
APP_VERSION = '2.3.8'

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

# ---------------------------------------------------------------------------
# Gotify Alerts (Self-Hosted Open-Source)
# ---------------------------------------------------------------------------
GOTIFY_URL        = os.environ.get('GOTIFY_URL', '')       # http://192.168.178.36:8080 oder http://nas.local:8080
GOTIFY_TOKEN      = os.environ.get('GOTIFY_TOKEN', '')     # API Token von Gotify


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
logger = logging.getLogger('pi_daemon')


# ---------------------------------------------------------------------------
# Startup-Validierung
# ---------------------------------------------------------------------------
def check_config() -> None:
    missing = [v for v in ('PI_DAEMON_JWT_SECRET', 'PI_DAEMON_TOTP_SECRET', 'PI_DAEMON_PASSWORD_HASH')
               if not os.environ.get(v)]
    if missing:
        logger.critical('Fehlende Pflicht-Umgebungsvariablen: %s', ', '.join(missing))
        sys.exit(1)
