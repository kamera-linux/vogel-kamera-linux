"""Login (Passwort + TOTP), JWT-Prüfung und Rate-Limit."""
from datetime import timedelta

import jwt

from conftest import JWT_SECRET, PASSWORD, make_token


def test_login_ok(client, totp_now):
    r = client.post('/api/login', json={'password': PASSWORD, 'totp': totp_now})
    assert r.status_code == 200
    token = r.get_json()['token']
    assert jwt.decode(token, JWT_SECRET, algorithms=['HS256'])['sub'] == 'admin'


def test_login_falsches_passwort(client, totp_now):
    r = client.post('/api/login', json={'password': 'falsch', 'totp': totp_now})
    assert r.status_code == 401
    assert 'token' not in r.get_json()


def test_login_falscher_totp(client):
    r = client.post('/api/login', json={'password': PASSWORD, 'totp': '000000'})
    assert r.status_code == 401


def test_login_ohne_body(client):
    r = client.post('/api/login')
    assert r.status_code == 401


def test_login_rate_limit(client):
    codes = [client.post('/api/login', json={'password': 'x', 'totp': '0'}).status_code
             for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_geschuetzt_ohne_token(client):
    assert client.get('/api/recordings').status_code == 401


def test_geschuetzt_falsche_signatur(client):
    h = {'Authorization': f'Bearer {make_token(secret="anderes-secret-anderes-secret-xx")}'}
    assert client.get('/api/recordings', headers=h).status_code == 401


def test_geschuetzt_abgelaufen(client):
    h = {'Authorization': f'Bearer {make_token(expires_in=timedelta(seconds=-10))}'}
    assert client.get('/api/recordings', headers=h).status_code == 401


def test_geschuetzt_alg_none_abgelehnt(client):
    token = jwt.encode({'sub': 'admin'}, key=None, algorithm='none')
    h = {'Authorization': f'Bearer {token}'}
    assert client.get('/api/recordings', headers=h).status_code == 401


def test_health_ohne_auth(client):
    r = client.get('/api/health')
    assert r.status_code in (200, 503)
    assert 'version' in r.get_json()
