"""Prometheus-Endpunkt /metrics: Zugriffsschutz und gültiges Textformat."""
import re

import pytest

from pi_daemon import config, hailo, powerbank
from pi_daemon.runtime import state
from tests.conftest import make_token

TOKEN = 'metrics-test-token'
LINE = re.compile(r'^[a-z_]+(\{[a-z_]+="[^"]*"(,[a-z_]+="[^"]*")*\})? -?[0-9.e+-]+$')


@pytest.fixture
def metrics_on(monkeypatch):
    monkeypatch.setattr(config, 'METRICS_TOKEN', TOKEN)
    return {'Authorization': f'Bearer {TOKEN}'}


def _values(text):
    return dict(line.rsplit(' ', 1) for line in text.splitlines() if not line.startswith('#'))


def test_ohne_token_konfiguration_gibt_es_den_endpunkt_nicht(client, auth_header):
    assert config.METRICS_TOKEN == ''
    assert client.get('/metrics').status_code == 404
    assert client.get('/metrics', headers=auth_header).status_code == 404
    assert client.get('/metrics', headers={'Authorization': 'Bearer '}).status_code == 404


def test_falsches_oder_fehlendes_token(client, metrics_on):
    assert client.get('/metrics').status_code == 401
    assert client.get('/metrics', headers={'Authorization': 'Bearer falsch'}).status_code == 401
    assert client.get('/metrics', headers={'Authorization': TOKEN}).status_code == 401
    # Das Login-Token der Web-GUI gilt hier nicht …
    assert client.get('/metrics', headers={'Authorization': f'Bearer {make_token()}'}).status_code == 401


def test_metrics_token_kann_nichts_steuern(client, metrics_on):
    # … und das Metrics-Token gilt nicht für die API
    assert client.get('/api/status', headers=metrics_on).status_code == 401
    assert client.post('/api/detection/mode/stop', headers=metrics_on).status_code == 401


def test_format_und_inhalt(client, metrics_on, video_dir, monkeypatch):
    (video_dir / 'a.mp4').write_bytes(b'x')
    (video_dir / 'roh_120fps.h264').write_bytes(b'x')
    monkeypatch.setattr(state, 'birds_recorded', 7)
    monkeypatch.setattr(state, 'detection_running', True)
    monkeypatch.setattr(hailo, '_hailo_temp_bg', {'npu_temp_c': 51.5, 'nn_clock_mhz': 400,
                                                   'throttle_active': False, 'throttle_level': -1})
    monkeypatch.setattr(powerbank, 'get_status', lambda: {
        'ok': True, 'battery_percent': 83, 'total_input_w': 0.0, 'total_output_w': 6.4,
        'temperature_c': 21, 'usb_c1': {'mode': 'output', 'power_w': 6.4}, 'usb_a': {'mode': 'off', 'power_w': 0.0}})

    r = client.get('/metrics', headers=metrics_on)
    assert r.status_code == 200
    assert r.headers['Content-Type'].startswith('text/plain; version=0.0.4')
    text = r.get_data(as_text=True)
    assert text.endswith('\n')

    names_with_type = set()
    for line in text.splitlines():
        if line.startswith('# TYPE '):
            _, _, name, kind = line.split(' ')
            assert kind in ('gauge', 'counter') and name not in names_with_type
            names_with_type.add(name)
        elif not line.startswith('# HELP '):
            assert LINE.match(line), f'ungültige Zeile: {line!r}'
            assert line.split('{')[0].split(' ')[0] in names_with_type, f'ohne TYPE: {line!r}'

    v = _values(text)
    assert v[f'vogelkamera_info{{version="{config.APP_VERSION}"}}'] == '1'
    assert v['vogelkamera_detection_running'] == '1'
    assert v['vogelkamera_recording_running'] == '0'
    assert v['vogelkamera_triggered_recordings_total'] == '7'
    assert v['vogelkamera_recordings_today'] == '1'
    assert v['vogelkamera_pending_conversions'] == '1'
    assert v['vogelkamera_npu_temperature_celsius'] == '51.5'
    assert v['vogelkamera_npu_clock_hertz'] == '400000000'
    assert v['vogelkamera_npu_throttle_active'] == '0'
    assert v['vogelkamera_powerbank_battery_percent'] == '83'
    assert v['vogelkamera_powerbank_reachable'] == '1'
    assert v['vogelkamera_powerbank_port_watts{port="usb_c1",mode="output"}'] == '6.4'
    assert int(v['vogelkamera_disk_free_bytes']) > 0
    assert 'vogelkamera_load_average{window="1m"}' in v


def test_unbekannte_werte_werden_ausgelassen(client, metrics_on, monkeypatch):
    """Ohne Hailo und ohne Powerbank fehlen die Zeilen, statt 0 vorzutäuschen."""
    monkeypatch.setattr(hailo, '_hailo_temp_bg', {})
    monkeypatch.setattr(powerbank, 'get_status', lambda: {})
    text = client.get('/metrics', headers=metrics_on).get_data(as_text=True)
    assert 'npu_' not in text and 'powerbank_' not in text


def test_cpu_auslastung_ab_der_zweiten_abfrage(client, metrics_on):
    client.get('/metrics', headers=metrics_on)
    v = _values(client.get('/metrics', headers=metrics_on).get_data(as_text=True))
    if 'vogelkamera_cpu_usage_ratio' in v:   # fehlt nur, wenn zwischen den Abfragen kein Tick lag
        assert 0.0 <= float(v['vogelkamera_cpu_usage_ratio']) <= 1.0


# ── Link „Monitoring" in der Web-GUI ─────────────────────────────────────────

def test_grafana_link_im_status(client, auth_header, monkeypatch):
    assert client.get('/api/status', headers=auth_header).json['grafana_url'] is None
    monkeypatch.setattr(config, 'GRAFANA_URL', 'http://server.lan:3002/d/vogel-kamera')
    assert client.get('/api/status', headers=auth_header).json['grafana_url'] == 'http://server.lan:3002/d/vogel-kamera'


@pytest.mark.parametrize('wert,erwartet', [
    ('http://server.lan:3002/d/vogel-kamera', 'http://server.lan:3002/d/vogel-kamera'),
    ('  HTTPS://grafana.example/d/x  ', 'HTTPS://grafana.example/d/x'),
    ('javascript:alert(1)', ''), ('server.lan:3002', ''), ('', ''),
])
def test_grafana_url_nur_http(monkeypatch, wert, erwartet):
    import importlib
    monkeypatch.setenv('PI_DAEMON_GRAFANA_URL', wert)
    try:
        assert importlib.reload(config).GRAFANA_URL == erwartet
    finally:
        monkeypatch.delenv('PI_DAEMON_GRAFANA_URL')
        importlib.reload(config)


def test_grafana_port_im_status(client, auth_header, monkeypatch):
    assert client.get('/api/status', headers=auth_header).json['grafana_port'] is None
    monkeypatch.setattr(config, 'GRAFANA_PORT', 3000)
    assert client.get('/api/status', headers=auth_header).json['grafana_port'] == 3000


@pytest.mark.parametrize('wert,erwartet', [('3000', 3000), ('', 0), ('0', 0), ('abc', 0), ('70000', 0), ('-1', 0)])
def test_grafana_port_nur_gueltige_ports(monkeypatch, wert, erwartet):
    import importlib
    monkeypatch.setenv('PI_DAEMON_GRAFANA_PORT', wert)
    try:
        assert importlib.reload(config).GRAFANA_PORT == erwartet
    finally:
        monkeypatch.delenv('PI_DAEMON_GRAFANA_PORT')
        importlib.reload(config)
