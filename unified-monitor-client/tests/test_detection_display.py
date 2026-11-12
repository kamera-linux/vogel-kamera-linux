"""Anzeige der Erkennung in der Web-GUI: letzte Auslösung (dauerhaft) und
„gerade gesehen, aber unter der Schwelle" (flüchtig)."""
import importlib.util
import json
import time
from pathlib import Path

import pytest

from pi_daemon import camera, config
from pi_daemon.runtime import state

SCRIPT = Path(__file__).resolve().parents[2] / 'raspberry-pi-scripts' / 'unified-camera-monitor-hailo.py'


@pytest.fixture(scope='module')
def hailo():
    """Das Detection-Skript als Modul (Dateiname mit Bindestrichen → importlib)."""
    spec = importlib.util.spec_from_file_location('hailo_script', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'LAST_DETECTION_FILE', str(tmp_path / 'last-detection.json'))
    monkeypatch.setattr(config, 'SEEN_DETECTION_FILE', str(tmp_path / 'detection-seen.json'))
    monkeypatch.setattr(state, 'detection_running', True)
    return tmp_path


# ── Detection-Skript ─────────────────────────────────────────────────────────

def test_seen_tracker_schreibt_hoechstens_einmal_pro_intervall(hailo, tmp_path):
    f = tmp_path / 'seen.json'
    t = hailo.SeenTracker(str(f), threshold=0.85, interval=1.0)
    assert t.observe('person', 0.52, now=100.0) is True          # erster Wert sofort
    assert json.loads(f.read_text())['conf'] == 0.52
    assert t.observe('person', 0.71, now=100.3) is False         # innerhalb des Intervalls
    assert t.observe('person', 0.60, now=100.6) is False
    assert json.loads(f.read_text())['conf'] == 0.52             # Datei noch unverändert
    assert t.observe('person', 0.55, now=101.1) is True
    data = json.loads(f.read_text())
    assert data['conf'] == 0.71                                   # der beste Wert des Intervalls
    assert data['class'] == 'person' and data['threshold'] == 0.85
    assert abs(data['ts'] - time.time()) < 5
    assert [p.name for p in tmp_path.iterdir()] == ['seen.json']  # keine Temp-Datei übrig


def test_seen_tracker_clear_und_unbeschreibbarer_pfad(hailo, tmp_path):
    f = tmp_path / 'seen.json'
    t = hailo.SeenTracker(str(f), 0.5)
    t.observe('bird', 0.45, now=10.0)
    t.clear()
    assert not f.exists()
    t.clear()                                                     # zweimal ist kein Fehler
    kaputt = hailo.SeenTracker(str(tmp_path / 'gibtsnicht' / 'seen.json'), 0.5)
    assert kaputt.observe('bird', 0.45, now=10.0) is True         # Fehler beim Schreiben stört die Erkennung nicht


def test_skript_legt_letzte_erkennung_dauerhaft_ab(hailo):
    """/tmp ist im Container ein tmpfs – dort ginge die Anzeige bei jedem Neustart verloren."""
    assert hailo.LAST_DETECTION_FILE.endswith('last-detection.json')
    assert hailo.SEEN_DETECTION_FILE.startswith('/tmp/')
    quelle = SCRIPT.read_text()
    assert "'/config/last-detection.json' if os.path.isdir('/config')" in quelle
    assert "'date':" in quelle


# ── Daemon ───────────────────────────────────────────────────────────────────

def test_daemon_uebergibt_die_dateipfade_an_das_skript(files, monkeypatch):
    calls = []

    class FakeProc:
        pid = 1

    monkeypatch.setattr(camera.subprocess, 'Popen', lambda args, **k: calls.append(args) or FakeProc())
    camera.CameraManager._launch_detection_process()
    args = calls[0]
    assert args[args.index('--last-detection-file') + 1] == config.LAST_DETECTION_FILE
    assert args[args.index('--seen-file') + 1] == config.SEEN_DETECTION_FILE


def test_status_zeigt_letzte_ausloesung_mit_datum(client, auth_header, files):
    assert client.get('/api/status', headers=auth_header).json['last_detection'] is None
    Path(config.LAST_DETECTION_FILE).write_text(json.dumps(
        {'class': 'person', 'conf': 0.91, 'time': '20:45:14', 'date': '2026-11-12'}))
    d = client.get('/api/status', headers=auth_header).json['last_detection']
    assert d == {'class': 'person', 'conf': 0.91, 'time': '20:45:14', 'date': '2026-11-12'}


def test_gesehen_nur_wenn_frisch_und_detection_laeuft(client, auth_header, files, monkeypatch):
    seen = Path(config.SEEN_DETECTION_FILE)

    def status():
        return client.get('/api/status', headers=auth_header).json['seen_detection']

    assert status() is None                                       # keine Datei
    seen.write_text(json.dumps({'class': 'person', 'conf': 0.62, 'threshold': 0.85, 'ts': time.time()}))
    s = status()
    assert s['class'] == 'person' and s['conf'] == 0.62 and s['threshold'] == 0.85 and s['age_s'] < 5

    seen.write_text(json.dumps({'class': 'person', 'conf': 0.62, 'threshold': 0.85, 'ts': time.time() - 60}))
    assert status() is None                                       # veraltet

    seen.write_text(json.dumps({'class': 'person', 'conf': 0.62, 'threshold': 0.85, 'ts': time.time()}))
    monkeypatch.setattr(state, 'detection_running', False)
    assert status() is None                                       # Detection steht

    monkeypatch.setattr(state, 'detection_running', True)
    seen.write_text('{kaputt')
    assert status() is None                                       # halbe/kaputte Datei
