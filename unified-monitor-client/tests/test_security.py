"""Security-Audit 2026-11: Sync-Ziele, SSH-Aufrufe, Security-Header, Eingaben."""
import stat

import pytest

from pi_daemon import camera, config, sync


@pytest.fixture
def sync_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'SETTINGS_FILE', str(tmp_path / 'sync-config.json'))
    return tmp_path


# ── validate_target ──────────────────────────────────────────────────────────

@pytest.mark.parametrize('host,user,path', [
    ('192.168.1.10', 'roimme', '/home/roimme/Videos/'),
    ('nas.local', 'backup_user', '~/videos'),
    ('fe80::1', 'u', '/data/vogel-kamera'),
])
def test_validate_target_ok(host, user, path):
    assert sync.validate_target(host, user, path) == ''


@pytest.mark.parametrize('host,user,path', [
    ('nas', '-oProxyCommand=touch /tmp/x', '/v'),       # ssh-Option über Benutzer
    ('-oProxyCommand=id', 'u', '/v'),                     # ssh-Option über Host
    ('nas', 'u', '-e sh -c id'),                          # rsync-Option über Pfad
    ('nas', 'u', '/v; rm -rf /'),                         # Shell-Zeichen im Pfad
    ('nas', 'u', '/v/$(id)'),
    ('nas', 'u@x', '/v'),
    ('na s', 'u', '/v'),
    ('', 'u', '/v'),
])
def test_validate_target_rejects(host, user, path):
    assert sync.validate_target(host, user, path) != ''


def test_settings_targets_rejects_injection(client, auth_header, sync_tmp):
    r = client.post('/api/settings/targets', headers=auth_header, json={'targets': [
        {'name': 'böse', 'host': 'nas', 'user': '-oProxyCommand=id', 'path': '/v'},
    ]})
    assert r.status_code == 400
    assert not (sync_tmp / 'sync-config.json').exists()


def test_settings_targets_accepts_valid_and_empty(client, auth_header, sync_tmp):
    r = client.post('/api/settings/targets', headers=auth_header, json={'targets': [
        {'name': 'NAS', 'host': '192.168.1.10', 'user': 'roimme', 'path': '/srv/videos/'},
        {'name': 'neu', 'host': '', 'user': '', 'path': ''},
    ]})
    assert r.status_code == 200
    assert [t['host'] for t in r.get_json()['targets']] == ['192.168.1.10', '']


def test_settings_targets_rejects_non_list(client, auth_header, sync_tmp):
    r = client.post('/api/settings/targets', headers=auth_header, json={'targets': 'x'})
    assert r.status_code == 400


def test_active_targets_skip_invalid(sync_tmp):
    sync._save_sync_settings({'targets': [
        {'id': 0, 'name': 'ok', 'host': 'nas', 'user': 'u', 'path': '/v', 'enabled': True},
        {'id': 1, 'name': 'alt', 'host': 'nas', 'user': '-oProxyCommand=id', 'path': '/v', 'enabled': True},
    ]})
    assert [t['name'] for t in sync._get_active_targets()] == ['ok']


def test_write_private_key_mode_0600(tmp_path):
    f = tmp_path / 'sync_key_0'
    sync.write_private_key(f, '-----BEGIN OPENSSH PRIVATE KEY-----\nx\n-----END OPENSSH PRIVATE KEY-----')
    assert stat.S_IMODE(f.stat().st_mode) == 0o600


# ── ssh/rsync-Aufrufe ────────────────────────────────────────────────────────

def test_ssh_options_check_host_keys():
    opts = ' '.join(sync.ssh_options('/nicht/vorhanden'))
    assert 'StrictHostKeyChecking=accept-new' in opts
    assert 'StrictHostKeyChecking=no' not in opts
    assert '/dev/null' not in opts


def test_transfer_uses_double_dash(sync_tmp, monkeypatch):
    sync._save_sync_settings({'targets': [
        {'id': 0, 'name': 'nas', 'host': 'nas', 'user': 'u', 'path': '/v', 'enabled': True}]})
    calls = []

    class R:
        returncode = 0
        stderr = b''

    monkeypatch.setattr(camera.subprocess, 'run', lambda cmd, **_kw: calls.append(cmd) or R())
    camera.CameraManager.transfer_all('/videos/a.mp4')
    cmd = calls[0]
    assert cmd[cmd.index('--') + 1:] == ['/videos/a.mp4', 'u@nas:/v']
    assert 'StrictHostKeyChecking=accept-new' in cmd[cmd.index('-e') + 1]


# ── HTTP ─────────────────────────────────────────────────────────────────────

def test_security_headers(client):
    r = client.get('/api/health')
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert r.headers['X-Frame-Options'] == 'DENY'
    assert r.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('url,body', [
    ('/api/rec-settings', {'profile': 'normal_hd', 'duration': 'abc'}),
    ('/api/record/audio', {'duration': None}),
])
def test_invalid_numbers_no_500(client, auth_header, url, body, monkeypatch, tmp_path):
    monkeypatch.setattr('pi_daemon.settings.REC_SETTINGS_FILE', str(tmp_path / 'rec.json'))
    monkeypatch.setattr(camera.CameraManager, 'record_audio', staticmethod(lambda **_kw: None))
    r = client.post(url, headers=auth_header, json=body)
    assert r.status_code < 500


def test_record_rejects_unknown_resolution(client, auth_header):
    r = client.post('/api/record', headers=auth_header, json={'resolution': '$(id)'})
    assert r.status_code == 400
