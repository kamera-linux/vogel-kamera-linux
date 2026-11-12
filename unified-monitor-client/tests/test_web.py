"""Web-GUI: Auslieferung (gzip, ETag, strikte CSP), Download-Tickets, Status-Kennzahlen."""
import gzip
import os
import re
from datetime import timedelta
from pathlib import Path

import pytest

from pi_daemon import api, camera
from tests.conftest import make_token

WEB = Path(api.WEB_DIR)


# ── Auslieferung ─────────────────────────────────────────────────────────────

def test_csp_erlaubt_keine_inline_skripte(client):
    csp = client.get('/').headers['Content-Security-Policy']
    script_src = re.search(r"script-src ([^;]*)", csp).group(1)
    assert script_src.strip() == "'self'"


def test_html_enthaelt_keine_inline_skripte_oder_handler():
    """Sonst würde die strikte CSP die GUI lahmlegen."""
    html = (WEB / 'index.html').read_text()
    assert not re.search(r'\son[a-z]+\s*=', html), 'Inline-Event-Handler gefunden'
    assert not re.search(r'<script(?![^>]*\bsrc=)', html), 'Inline-<script> gefunden'
    assert 'javascript:' not in html


def test_alle_data_actions_haben_eine_funktion():
    html = (WEB / 'index.html').read_text()
    js = (WEB / 'app.js').read_text()
    used = set(re.findall(r'data-action="([a-z-]+)"', html + js))
    defined = set(re.findall(r"^\s*'([a-z-]+)':", js.split('const ACTIONS = {')[1].split('};')[0], re.M))
    assert used and used <= defined, f'ohne Funktion: {used - defined}'


def test_alle_ids_aus_app_js_existieren_im_html():
    html = (WEB / 'index.html').read_text()
    js = (WEB / 'app.js').read_text()
    ids = set(re.findall(r'id="([^"${}]+)"', html))
    wanted = set(re.findall(r"\$\('([a-z0-9-]+)'\)", js)) | set(re.findall(r"set(?:Text|Html)\('([a-z0-9-]+)'", js))
    # von app.js selbst erzeugt (Kamera-Regler)
    wanted = {w for w in wanted if not w.startswith('cam-') or w in ('cam-settings', 'cam-details')}
    assert wanted - ids == set()


@pytest.mark.parametrize('pfad,mime', [
    ('/', 'text/html'), ('/web/app.js', 'javascript'), ('/web/app.css', 'text/css')])
def test_textdateien_gzip_und_etag(client, pfad, mime):
    r = client.get(pfad, headers={'Accept-Encoding': 'gzip'})
    assert r.status_code == 200 and mime in r.headers['Content-Type']
    assert r.headers['Content-Encoding'] == 'gzip'
    assert len(gzip.decompress(r.data)) > len(r.data)
    assert r.headers['Cache-Control'] == 'no-cache'

    r304 = client.get(pfad, headers={'Accept-Encoding': 'gzip', 'If-None-Match': r.headers['ETag']})
    assert r304.status_code == 304 and r304.data == b''

    plain = client.get(pfad)
    assert 'Content-Encoding' not in plain.headers
    assert plain.data == gzip.decompress(r.data)
    assert plain.headers['ETag'] != r.headers['ETag']


def test_bilder_werden_ausgeliefert_und_gecacht(client):
    for name in ('logo.webp', 'icon.png'):
        r = client.get(f'/web/{name}')
        assert r.status_code == 200
        assert 'max-age=86400' in r.headers['Cache-Control']
        assert len(r.data) < 100_000, f'{name} ist wieder groß geworden'


def test_static_kein_ausbruch_aus_web_verzeichnis(client):
    assert client.get('/web/../pi_daemon/config.py').status_code == 404
    assert client.get('/web/%2e%2e/pi_daemon/config.py').status_code == 404


# ── Download-Ticket ──────────────────────────────────────────────────────────

@pytest.fixture
def video(video_dir):
    f = video_dir / '2026-11-06' / 'vogel.mp4'
    f.parent.mkdir()
    f.write_bytes(bytes(range(256)) * 40)
    return f


def _ticket(client, auth_header, p='2026-11-06/vogel.mp4'):
    return client.post('/api/download-ticket', headers=auth_header, json={'p': p})


def test_ticket_braucht_login(client, video):
    assert client.post('/api/download-ticket', json={'p': '2026-11-06/vogel.mp4'}).status_code == 401


def test_ticket_liefert_datei_ohne_auth_header(client, auth_header, video):
    r = _ticket(client, auth_header)
    assert r.status_code == 200 and r.json['size'] == video.stat().st_size
    f = client.get(r.json['url'])
    assert f.status_code == 200 and f.data == video.read_bytes()
    assert 'attachment' not in f.headers.get('Content-Disposition', '')
    dl = client.get(r.json['url'] + '&dl=1')
    assert 'attachment' in dl.headers['Content-Disposition']


def test_ticket_unterstuetzt_range_fuer_den_player(client, auth_header, video):
    url = _ticket(client, auth_header).json['url']
    r = client.get(url, headers={'Range': 'bytes=100-199'})
    assert r.status_code == 206
    assert r.data == video.read_bytes()[100:200]


def test_ticket_gilt_nur_fuer_eine_datei_und_laeuft_ab(client, auth_header, video, monkeypatch):
    (video.parent / 'andere.mp4').write_bytes(b'geheim')
    url = _ticket(client, auth_header).json['url']
    # Pfad lässt sich nicht nachträglich ändern – er steckt signiert im Ticket
    assert client.get(url + '&p=2026-11-06/andere.mp4').data == video.read_bytes()

    monkeypatch.setattr(api, '_TICKET_TTL_S', -1)
    abgelaufen = _ticket(client, auth_header).json['url']
    assert client.get(abgelaufen).status_code == 401


def test_login_token_ist_kein_ticket_und_umgekehrt(client, auth_header, video):
    assert client.get(f'/api/file?t={make_token()}').status_code == 401
    assert client.get('/api/file?t=unsinn').status_code == 401
    assert client.get('/api/file').status_code == 401
    ticket = _ticket(client, auth_header).json['url'].split('t=')[1]
    # Ein Ticket steht in einer URL – es darf nicht als Login taugen
    r = client.get('/api/recordings', headers={'Authorization': f'Bearer {ticket}'})
    assert r.status_code == 401


@pytest.mark.parametrize('pfad', ['../../etc/passwd', '/etc/passwd', '', '.'])
def test_ticket_kein_path_traversal(client, auth_header, video, pfad):
    assert _ticket(client, auth_header, pfad).status_code in (400, 403, 404)


def test_ticket_fuer_geloeschte_datei(client, auth_header, video):
    url = _ticket(client, auth_header).json['url']
    video.unlink()
    assert client.get(url).status_code == 404


# ── Status-Kennzahlen ────────────────────────────────────────────────────────

def test_status_meldet_pending_und_listen_stand(client, auth_header, video_dir):
    def status():
        return client.get('/api/status', headers=auth_header).json

    leer = status()
    assert leer['pending'] == 0 and leer['today_recordings'] == 0

    (video_dir / 'a_120fps.h264').write_bytes(b'x')          # noch nicht konvertiert
    (video_dir / 'b.mp4').write_bytes(b'x')
    (video_dir / 'b.wav').write_bytes(b'x')                   # Begleit-WAV: nicht gelistet
    (video_dir / 'c_audio_1min.wav').write_bytes(b'x')
    voll = status()
    assert voll['pending'] == 1 and voll['today_recordings'] == 1
    assert voll['recordings_rev'] != leer['recordings_rev']
    assert client.get('/api/pending', headers=auth_header).json == {'pending': 1}

    names = [r['name'] for r in client.get('/api/recordings', headers=auth_header).json]
    assert sorted(names) == ['b.mp4', 'c_audio_1min.wav']

    # Unveränderte Liste → gleicher Stand; die GUI lädt dann nicht neu
    assert status()['recordings_rev'] == voll['recordings_rev']
    (video_dir / 'b.mp4').write_bytes(b'xx')
    assert status()['recordings_rev'] != voll['recordings_rev']


def test_scan_cache_und_invalidierung_beim_loeschen(client, auth_header, video_dir, monkeypatch):
    monkeypatch.setattr(camera, '_SCAN_TTL', 60)
    camera.invalidate_media_scan()
    (video_dir / 'a.mp4').write_bytes(b'x')
    assert len(client.get('/api/recordings', headers=auth_header).json) == 1
    (video_dir / 'b.mp4').write_bytes(b'x')
    os.utime(video_dir / 'b.mp4')
    assert len(client.get('/api/recordings', headers=auth_header).json) == 1   # noch aus dem Cache
    r = client.post('/api/delete', headers=auth_header, json={'p': 'a.mp4'})
    assert r.status_code == 200
    names = [x['name'] for x in client.get('/api/recordings', headers=auth_header).json]
    assert names == ['b.mp4']                                                   # sofort aktuell
    camera.invalidate_media_scan()


def test_abgelaufenes_login_wird_abgelehnt(client):
    h = {'Authorization': f'Bearer {make_token(expires_in=timedelta(seconds=-5))}'}
    assert client.post('/api/download-ticket', headers=h, json={'p': 'x.mp4'}).status_code == 401
