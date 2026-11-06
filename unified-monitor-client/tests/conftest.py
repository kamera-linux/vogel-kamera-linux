"""Test-Setup für pi_daemon_secure.

Der Daemon liest seine Konfiguration beim Import aus Umgebungsvariablen und
zur Laufzeit aus Modul-Globals. Die Tests setzen diese Globals per
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

import pi_daemon_secure as daemon  # noqa: E402

PASSWORD = 'test-passwort'
JWT_SECRET = 'test-jwt-secret-mit-ausreichender-laenge-32b'
TOTP_SECRET = pyotp.random_base32()


@pytest.fixture
def video_dir(tmp_path, monkeypatch):
    base = tmp_path / 'videos'
    base.mkdir()
    monkeypatch.setattr(daemon, 'VIDEO_BASE_DIR', str(base))
    return base


@pytest.fixture
def client(monkeypatch, video_dir):
    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setattr(daemon, 'PASSWORD_HASH', pw_hash)
    monkeypatch.setattr(daemon, 'JWT_SECRET', JWT_SECRET)
    monkeypatch.setattr(daemon, 'TOTP_SECRET', TOTP_SECRET)
    # Brute-Force-Bremse (sleep 1s) im Test überspringen
    monkeypatch.setattr(daemon.time, 'sleep', lambda _s: None)
    daemon.limiter.reset()
    daemon.app.config['TESTING'] = True
    with daemon.app.test_client() as c:
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
