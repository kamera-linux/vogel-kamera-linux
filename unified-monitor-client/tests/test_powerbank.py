"""Powerbank: Protokoll-Auswertung, Akku-Schutz-Logik, Ausgabe in /api/status."""
import pytest

from pi_daemon import config, powerbank

# Echte, entschlüsselte Statusantwort (Befehl 0x0D00) einer Anker Prime 27K/250W:
# 72 %, USB-C2 gibt 5,0 V / 0,9 A ab, 18 °C
REAL_STATUS = bytes.fromhex(
    '00a10131a20a04020c13006402004855a3020101a40c04430000000000003200001e'
    'a50c04430232000900013200001ea60c044100320000000000000000a70804500001'
    '00000064a80401000000a9020100aa020102ab0704ff0000000600ac0704ff000000'
    '0600ad0201b7ae05022d000000af06040000000000b0020400b10504026c6400b203'
    '040000b303041240b40704cb0f006e0a00b503040000b6090400000000ffffffff')


def test_parse_status_real_payload():
    st = powerbank.parse_status(REAL_STATUS)
    assert st['battery_percent'] == 72
    assert st['temperature_c'] == 18
    assert st['total_output_w'] == 4.5
    assert st['total_input_w'] == 0.0
    assert st['usb_c1']['mode'] == 'off'
    assert st['usb_c2'] == {'mode': 'output', 'voltage_v': 5.0, 'current_a': 0.9, 'power_w': 4.5}


def test_frame_length_and_checksum():
    f = powerbank._frame(b'\x03\x00\x01\x00\x01')
    assert f[:2] == b'\xff\x09'
    assert int.from_bytes(f[2:4], 'little') == len(f)
    x = 0
    for b in f:
        x ^= b
    assert x == 0   # XOR über alles inkl. Prüfsumme ergibt 0


def test_aes_roundtrip():
    iv = b'AFYHYQ2G28200319'
    data = powerbank._tlv([(0xA1, b'\x21')])
    enc = powerbank._aes(powerbank._INITIAL_KEY, iv, data, True)
    assert len(enc) == 16
    assert powerbank._aes(powerbank._INITIAL_KEY, iv, enc, False) == data


@pytest.fixture
def guard(monkeypatch):
    monkeypatch.setattr(config, 'POWERBANK_WARN_PERCENT', 10)
    monkeypatch.setattr(config, 'POWERBANK_SHUTDOWN_PERCENT', 5)
    g = powerbank._Guard()
    monkeypatch.setattr(powerbank, '_guard', g)
    return g


def test_warn_once_and_reset(guard):
    assert powerbank._evaluate(50, 0) == ''
    assert powerbank._evaluate(10, 0) == 'warn'
    assert powerbank._evaluate(9, 0) == ''          # nur einmal warnen
    assert powerbank._evaluate(11, 0) == ''         # Hysterese: noch kein Reset
    assert powerbank._evaluate(12, 0) == ''         # Reset
    assert powerbank._evaluate(10, 0) == 'warn'


def test_shutdown_needs_two_low_readings(guard):
    guard.warned = True
    assert powerbank._evaluate(5, 0) == ''
    assert powerbank._evaluate(5, 0) == 'shutdown'
    assert powerbank._evaluate(4, 0) == ''          # nur einmal auslösen


def test_no_shutdown_while_charging(guard):
    guard.warned = True
    for _ in range(5):
        assert powerbank._evaluate(3, 30.0) == ''


def test_single_low_reading_resets(guard):
    guard.warned = True
    assert powerbank._evaluate(5, 0) == ''
    assert powerbank._evaluate(6, 0) == ''
    assert powerbank._evaluate(5, 0) == ''


def test_status_endpoint_includes_powerbank(client, auth_header, monkeypatch):
    monkeypatch.setattr(config, 'POWERBANK_MAC', '00:11:22:33:44:55')
    monkeypatch.setattr(powerbank, '_cache', {'battery_percent': 72, 'ok': True})
    data = client.get('/api/status', headers=auth_header).get_json()
    assert data['powerbank'] == {'battery_percent': 72, 'ok': True}


def test_status_endpoint_powerbank_disabled(client, auth_header, monkeypatch):
    monkeypatch.setattr(config, 'POWERBANK_MAC', '')
    data = client.get('/api/status', headers=auth_header).get_json()
    assert data['powerbank'] == {}


# ── Hängende Bluetooth-Verbindung ────────────────────────────────────────────

class _Variant:
    def __init__(self, value):
        self.value = value


def _fake_dbus(monkeypatch, objects, calls):
    """Ersetzt dbus_fast durch eine Attrappe, die BlueZ mit den gegebenen Objekten spielt."""
    import sys
    import types

    class MessageType:
        ERROR = 'error'
        METHOD_RETURN = 'return'

    class Message:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class _Reply:
        def __init__(self, body=None, message_type=MessageType.METHOD_RETURN):
            self.body, self.message_type = body, message_type

    class _Bus:
        async def connect(self):
            return self

        async def call(self, msg):
            calls.append((msg.path, msg.member))
            return _Reply([objects]) if msg.member == 'GetManagedObjects' else _Reply([])

        def disconnect(self):
            calls.append(('bus', 'geschlossen'))

    mod = types.ModuleType('dbus_fast')
    mod.BusType = types.SimpleNamespace(SYSTEM='system')
    mod.Message, mod.MessageType = Message, MessageType
    aio = types.ModuleType('dbus_fast.aio')
    aio.MessageBus = lambda bus_type=None: _Bus()
    monkeypatch.setitem(sys.modules, 'dbus_fast', mod)
    monkeypatch.setitem(sys.modules, 'dbus_fast.aio', aio)


def _run(coro):
    import asyncio
    return asyncio.run(coro)


def test_haengende_verbindung_wird_getrennt(monkeypatch):
    calls = []
    _fake_dbus(monkeypatch, {
        '/org/bluez/hci0': {'org.bluez.Adapter1': {}},
        '/org/bluez/hci0/dev_AA': {'org.bluez.Device1': {'Address': _Variant('AA:BB:CC:00:11:22'), 'Connected': _Variant(True)}},
        '/org/bluez/hci0/dev_PB': {'org.bluez.Device1': {'Address': _Variant('00:7F:1D:00:00:01'), 'Connected': _Variant(True)}},
    }, calls)
    assert _run(powerbank._drop_stale_connection('00:7f:1d:00:00:01')) is True
    # nur die Powerbank wird getrennt, kein anderes Gerät; der Bus wird wieder geschlossen
    assert ('/org/bluez/hci0/dev_PB', 'Disconnect') in calls
    assert ('/org/bluez/hci0/dev_AA', 'Disconnect') not in calls
    assert calls[-1] == ('bus', 'geschlossen')


def test_nicht_verbundene_powerbank_bleibt_unberuehrt(monkeypatch):
    calls = []
    _fake_dbus(monkeypatch, {
        '/org/bluez/hci0/dev_PB': {'org.bluez.Device1': {'Address': _Variant('00:7F:1D:00:00:01'), 'Connected': _Variant(False)}},
    }, calls)
    assert _run(powerbank._drop_stale_connection('00:7F:1D:00:00:01')) is False
    assert not [c for c in calls if c[1] == 'Disconnect']
