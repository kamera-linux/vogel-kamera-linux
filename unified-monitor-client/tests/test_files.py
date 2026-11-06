"""Download/Delete: Zugriff nur innerhalb von VIDEO_BASE_DIR."""
import pytest

from conftest import make_token


@pytest.fixture
def aufnahme(video_dir):
    d = video_dir / '2026-11-06'
    d.mkdir()
    f = d / 'vogel.mp4'
    f.write_bytes(b'video')
    return f


def test_download_ok(client, auth_header, aufnahme):
    r = client.get('/api/download?p=2026-11-06/vogel.mp4', headers=auth_header)
    assert r.status_code == 200
    assert r.data == b'video'


def test_download_token_als_query_abgelehnt(client, aufnahme):
    # Token darf nicht in der URL stehen (Logs, Browser-Verlauf)
    r = client.get(f'/api/download?p=2026-11-06/vogel.mp4&token={make_token()}')
    assert r.status_code == 401


def test_snapshot_braucht_header(client, monkeypatch, tmp_path, auth_header):
    import pi_daemon_secure as daemon
    frame = tmp_path / 'frame.jpg'
    frame.write_bytes(b'\xff\xd8jpeg')
    monkeypatch.setattr(daemon, '_STREAM_FRAME', frame)
    assert client.get(f'/api/snapshot?token={make_token()}').status_code == 401
    r = client.get('/api/snapshot', headers=auth_header)
    assert r.status_code == 200
    assert r.data == b'\xff\xd8jpeg'


def test_download_ohne_token(client, aufnahme):
    assert client.get('/api/download?p=2026-11-06/vogel.mp4').status_code == 401


@pytest.mark.parametrize('pfad', [
    '../geheim.txt',
    '2026-11-06/../../geheim.txt',
    '/etc/passwd',
    '../videos-evil/x.mp4',   # Nachbarordner mit gleichem Präfix
])
def test_download_path_traversal(client, auth_header, video_dir, pfad):
    (video_dir.parent / 'geheim.txt').write_text('geheim')
    evil = video_dir.parent / 'videos-evil'
    evil.mkdir(exist_ok=True)
    (evil / 'x.mp4').write_text('evil')
    r = client.get('/api/download', query_string={'p': pfad}, headers=auth_header)
    assert r.status_code == 403


def test_download_nicht_vorhanden(client, auth_header, video_dir):
    r = client.get('/api/download?p=gibtsnicht.mp4', headers=auth_header)
    assert r.status_code == 404


def test_delete_mit_begleitdateien(client, auth_header, aufnahme):
    aufnahme.with_suffix('.h264').write_bytes(b'raw')
    aufnahme.with_suffix('.wav').write_bytes(b'audio')
    r = client.post('/api/delete', json={'p': '2026-11-06/vogel.mp4'}, headers=auth_header)
    assert r.status_code == 200
    assert sorted(r.get_json()['deleted']) == ['vogel.h264', 'vogel.mp4', 'vogel.wav']
    assert not list(aufnahme.parent.iterdir())


def test_delete_path_traversal(client, auth_header, video_dir):
    opfer = video_dir.parent / 'opfer.txt'
    opfer.write_text('bleibt')
    r = client.post('/api/delete', json={'p': '../opfer.txt'}, headers=auth_header)
    assert r.status_code == 403
    assert opfer.exists()


def test_delete_ohne_token(client, aufnahme):
    r = client.post('/api/delete', json={'p': '2026-11-06/vogel.mp4'})
    assert r.status_code == 401
    assert aufnahme.exists()
