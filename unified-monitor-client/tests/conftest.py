"""Test-Setup für das Paket pi_daemon.

Der Daemon liest seine Konfiguration beim Import aus Umgebungsvariablen und
zur Laufzeit aus pi_daemon.config. Die Tests setzen diese Werte per
monkeypatch, damit kein Raspberry Pi, keine Kamera und keine echten
Secrets nötig sind.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
import pyotp
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pi_daemon import api, config  # noqa: E402

PASSWORD = 'test-passwort'
JWT_SECRET = 'test-jwt-secret-mit-ausreichender-laenge-32b'
TOTP_SECRET = pyotp.random_base32()


@pytest.fixture
def video_dir(tmp_path, monkeypatch):
    base = tmp_path / 'videos'
    base.mkdir()
    monkeypatch.setattr(config, 'VIDEO_BASE_DIR', str(base))
    return base


@pytest.fixture
def client(monkeypatch, video_dir):
    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setattr(config, 'PASSWORD_HASH', pw_hash)
    monkeypatch.setattr(config, 'JWT_SECRET', JWT_SECRET)
    monkeypatch.setattr(config, 'TOTP_SECRET', TOTP_SECRET)
    # Brute-Force-Bremse (sleep 1s) im Test überspringen
    monkeypatch.setattr(api.time, 'sleep', lambda _s: None)
    api.limiter.reset()
    api.app.config['TESTING'] = True
    with api.app.test_client() as c:
        yield c


def make_token(secret=JWT_SECRET, expires_in=timedelta(hours=1)):
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': 'admin', 'iat': now, 'exp': now + expires_in},
                      secret, algorithm='HS256')


@pytest.fixture
def auth_header():
    return {'Authorization': f'Bearer {make_token()}'}


@pytest.fixture
def totp_now():
    return pyotp.TOTP(TOTP_SECRET).now()
