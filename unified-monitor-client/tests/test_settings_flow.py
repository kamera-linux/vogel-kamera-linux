"""Einstellungen, die per API geändert werden, müssen beim CameraManager ankommen.

Absicherung der Modul-Aufteilung: Laufzeit-Werte leben in pi_daemon.settings und
werden von api.py gesetzt, aber von camera.py gelesen. Ein versehentliches
"from .settings import <wert>" würde eine veraltete Kopie erzeugen – diese Tests
würden das erkennen.
"""
import pytest

from pi_daemon import camera, settings


@pytest.fixture(autouse=True)
def settings_tmp(tmp_path, monkeypatch):
    """Einstellungsdateien nach tmp umleiten und Laufzeitwerte nach dem Test zurücksetzen."""
    for name in ('DETECTION_ENGINE_FILE', 'DETECTION_SETTINGS_FILE',
                 'CAMERA_SETTINGS_FILE', 'REC_SETTINGS_FILE'):
        monkeypatch.setattr(settings, name, str(tmp_path / f'{name.lower()}.json'))
    for name in ('_active_engine', 'DETECTION_SCRIPT', '_detection_target', '_detection_threshold',
                 '_lens_position', '_ev', '_awb', '_brightness', '_contrast', '_saturation',
                 '_sharpness', '_gain'):
        monkeypatch.setattr(settings, name, getattr(settings, name))


@pytest.fixture
def popen_args(monkeypatch):
    """Fängt den Detection-Subprozess ab, statt ihn zu starten."""
    calls = []

    class FakeProc:
        pid = 4242

    def fake_popen(args, **_kw):
        calls.append(args)
        return FakeProc()

    monkeypatch.setattr(camera.subprocess, 'Popen', fake_popen)
    return calls


def test_detection_settings_erreichen_detection_prozess(client, auth_header, popen_args):
    r = client.post('/api/detection-settings', headers=auth_header,
                    json={'target_class': 'person', 'threshold': 0.6})
    assert r.status_code == 200
    camera.CameraManager._launch_detection_process()
    args = popen_args[-1]
    assert args[args.index('--target-class') + 1] == 'person'
    assert args[args.index('--threshold') + 1] == '0.6'


def test_engine_wechsel_erreicht_detection_prozess(client, auth_header, popen_args):
    neu = 'cpu_yolo' if settings._active_engine == 'hailo' else 'hailo'
    r = client.post('/api/detection-engine', headers=auth_header, json={'engine': neu})
    assert r.get_json()['active'] == neu
    camera.CameraManager._launch_detection_process()
    assert popen_args[-1][1] == settings.DETECTION_ENGINES[neu]['script']


def test_kamera_settings_in_status_und_modul(client, auth_header):
    r = client.post('/api/camera-settings', headers=auth_header,
                    json={'lens_position': 5.5, 'awb': 'cloudy', 'gain': 99})
    assert r.status_code == 200
    assert settings._lens_position == 5.5
    assert settings._awb == 'cloudy'
    assert settings._gain == 8.0   # auf Maximum begrenzt
    status = client.get('/api/status', headers=auth_header).get_json()
    assert status['lens_position'] == 5.5
    assert status['awb'] == 'cloudy'


def test_kamera_settings_ungueltig(client, auth_header):
    r = client.post('/api/camera-settings', headers=auth_header, json={'awb': 'disco'})
    assert r.status_code == 400


def test_rec_settings_roundtrip(client, auth_header):
    r = client.post('/api/rec-settings', headers=auth_header,
                    json={'profile': 'normal_4k', 'duration': 9999})
    assert r.get_json() == {'success': True, 'profile': 'normal_4k', 'duration': 600}
    assert client.get('/api/rec-settings', headers=auth_header).get_json()['profile'] == 'normal_4k'


def test_main_importierbar():
    from pi_daemon import main
    assert callable(main.main)
