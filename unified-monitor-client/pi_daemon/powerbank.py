"""Anker Prime Power Bank (27K, 250W) per Bluetooth LE auslesen + Akku-Schutz.

Protokoll nach atc1441: https://github.com/atc1441/Anker_Prime_BLE_hacking
(feste Startschlüssel, AES-128-CBC mit Seriennummer als IV, danach Session-Key).
Ein Anker-Konto ist nicht nötig.

Der Container erreicht BlueZ und systemd-logind über den eingebundenen
Host-Socket /run/dbus/system_bus_socket.

Ablauf alle POWERBANK_INTERVAL Sekunden: verbinden → Status lesen → trennen.
Kurze Verbindungen, damit die Anker-App zwischendurch weiter zugreifen kann.

Akku-Schutz:
  ≤ POWERBANK_WARN_PERCENT      → einmalige Gotify-Warnung (Reset ab +2 %)
  ≤ POWERBANK_SHUTDOWN_PERCENT  → Pi herunterfahren, wenn zwei Messungen in
                                   Folge so niedrig sind und nicht geladen wird
"""
import asyncio
import struct
import threading
import time
from datetime import datetime, timezone

from . import config
from .config import logger

# ---------------------------------------------------------------------------
# BLE-Protokoll
# ---------------------------------------------------------------------------
WRITE_UUID = '22150002-4002-81c5-b46e-cf057c562025'
NOTIFY_UUID = '22150003-4002-81c5-b46e-cf057c562025'
_A2_STATIC = bytes.fromhex(
    '32633337376466613039636462373932343838396534323932613337663631633863356564353264')
_INITIAL_KEY = _A2_STATIC[:16]

_CONNECT_TIMEOUT = 20.0     # Sekunden für Verbindungsaufbau
_RESPONSE_TIMEOUT = 5.0     # Sekunden pro Antwort
_READ_TIMEOUT = 60.0        # Gesamtlimit für einen Lesevorgang

_PORT_NAMES = {0xA4: 'usb_c1', 0xA5: 'usb_c2', 0xA6: 'usb_a'}
_PORT_MODES = {0: 'off', 1: 'input', 2: 'output'}


def _tlv(items) -> bytes:
    return b''.join(bytes([t, len(v)]) + v for t, v in items)


def _parse_tlv(data: bytes, offset: int = 0):
    i = offset
    while i < len(data) - 1:
        t, ln = data[i], data[i + 1]
        if i + 2 + ln > len(data):
            return
        yield t, data[i + 2:i + 2 + ln]
        i += 2 + ln


def _frame(payload: bytes) -> bytes:
    """Rahmen: FF 09 <Länge LE16> <Payload> <XOR-Prüfsumme>."""
    msg = bytes([0xFF, 0x09]) + struct.pack('<H', len(payload) + 5) + payload
    cs = 0
    for b in msg:
        cs ^= b
    return msg + bytes([cs])


def _aes(key: bytes, iv: bytes, data: bytes, encrypt: bool) -> bytes:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    if encrypt:
        p = padding.PKCS7(128).padder()
        data = p.update(data) + p.finalize()
        e = cipher.encryptor()
        return e.update(data) + e.finalize()
    d = cipher.decryptor()
    out = d.update(data) + d.finalize()
    u = padding.PKCS7(128).unpadder()
    return u.update(out) + u.finalize()


def _parse_port(v: bytes):
    if len(v) < 12:
        return None
    volt = struct.unpack_from('<H', v, 3)[0] / 10
    amp = struct.unpack_from('<H', v, 5)[0] / 10
    return {
        'mode': _PORT_MODES.get(v[2], f'0x{v[2]:02x}'),
        'voltage_v': volt,
        'current_a': amp,
        'power_w': round(volt * amp, 2),
    }


def parse_status(d: bytes) -> dict:
    """Entschlüsselte Antwort auf Befehl 0x0500 (bzw. 0x0D00) auswerten."""
    st: dict = {}
    off = 1 if d and d[0] == 0 else 0
    for t, v in _parse_tlv(d, off):
        if t == 0xA2 and len(v) >= 10:
            st['battery_percent'] = v[8]
        elif t in _PORT_NAMES:
            st[_PORT_NAMES[t]] = _parse_port(v)
        elif t == 0xAE and len(v) >= 5:
            st['total_output_w'] = struct.unpack_from('<H', v, 1)[0] / 10
            st['total_input_w'] = struct.unpack_from('<H', v, 3)[0] / 10
        elif t == 0xB3 and len(v) >= 3:
            st['temperature_c'] = v[1]
    return st


class _Session:
    def __init__(self, client):
        self.client = client
        self.queue: asyncio.Queue = asyncio.Queue()
        self.iv = None
        self.key = None

    def on_notify(self, _handle, data) -> None:
        self.queue.put_nowait(bytes(data))

    async def send(self, group: int, cmd: int, items, key=None) -> None:
        hi, lo = (cmd >> 8) & 0xFF, cmd & 0xFF
        body = _tlv(items)
        if key:
            hi |= 0x40
            body = _aes(key, self.iv, body, True)
        await self.client.write_gatt_char(
            WRITE_UUID, _frame(bytes([0x03, 0x00, group, hi, lo]) + body), response=False)

    async def recv(self):
        """Nächste Antwort als (Befehl, Inhalt); verschlüsselte Inhalte entschlüsselt."""
        raw = await asyncio.wait_for(self.queue.get(), _RESPONSE_TIMEOUT)
        p = raw[4:-1]
        if len(p) < 5:
            return None, p
        cmd = ((p[3] & 0xBF) << 8) | p[4]
        if not p[3] & 0x40:
            return cmd, p
        for k in (self.key, _INITIAL_KEY):
            if k:
                try:
                    return cmd, _aes(k, self.iv, p[5:], False)
                except ValueError:
                    pass
        raise RuntimeError('Antwort ließ sich nicht entschlüsseln')


async def _read_once(mac: str) -> dict:
    from bleak import BleakClient

    async with BleakClient(mac, timeout=_CONNECT_TIMEOUT) as client:
        s = _Session(client)
        await client.start_notify(NOTIFY_UUID, s.on_notify)
        await asyncio.sleep(0.3)

        # 1. Unverschlüsselter Handshake – liefert u.a. die Seriennummer
        ts = struct.pack('<I', int(time.time()))
        base = [(0xA1, ts), (0xA2, _A2_STATIC)]
        await s.send(0x01, 0x0001, base)
        await s.recv()
        await s.send(0x01, 0x0003, base + [(0xA3, b'\x20'), (0xA4, b'\x00\xf0')])
        await s.recv()
        await s.send(0x01, 0x0029, base)
        _, info = await s.recv()
        serial = next((v for t, v in _parse_tlv(info, 6) if t == 0xA4), None)
        if not serial or len(serial) != 16:
            raise RuntimeError('Seriennummer nicht erhalten')
        await s.send(0x01, 0x0005, base + [(0xA3, b'\x20'), (0xA4, b'\x00\xf0'), (0xA5, b'\x02')])
        await s.recv()

        # 2. Mit Startschlüssel einen Session-Key anfordern
        s.iv = serial
        await s.send(0x01, 0x0022, base + [(0xA3, bytes(4)), (0xA5, bytes(40))], key=_INITIAL_KEY)
        deadline = time.monotonic() + 10
        while not s.key and time.monotonic() < deadline:
            _, d = await s.recv()
            off = 1 if d and d[0] == 0 else 0
            s.key = next((v for t, v in _parse_tlv(d, off) if t == 0xA1 and len(v) == 16), None)
        if not s.key:
            raise RuntimeError('Kein Session-Key erhalten')

        # 3. Status abfragen
        await s.send(0x11, 0x0500, [(0xA1, b'\x21')], key=s.key)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            cmd, d = await s.recv()
            if cmd in (0x0500, 0x0D00):
                st = parse_status(d)
                if 'battery_percent' in st:
                    return st
        raise RuntimeError('Keine Statusantwort erhalten')


async def _drop_stale_connection(mac: str) -> bool:
    """Trennt eine Verbindung zur Powerbank, die BlueZ noch offen hält.

    Wird der Container mitten in einer Abfrage beendet (Update, Neustart), bleibt die
    Verbindung auf dem Host bestehen. Eine verbundene Powerbank sendet keine Werbepakete
    mehr, die nächste Abfrage findet sie dann nicht („was not found"). Trennen behebt das.
    Gibt True zurück, wenn eine Verbindung getrennt wurde.
    """
    from dbus_fast import BusType, Message, MessageType
    from dbus_fast.aio import MessageBus

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    try:
        reply = await bus.call(Message(
            destination='org.bluez', path='/',
            interface='org.freedesktop.DBus.ObjectManager', member='GetManagedObjects'))
        if reply.message_type == MessageType.ERROR:
            return False
        dropped = False
        for path, interfaces in reply.body[0].items():
            dev = interfaces.get('org.bluez.Device1')
            if not dev:
                continue
            address = dev.get('Address')
            connected = dev.get('Connected')
            if (getattr(address, 'value', address) or '').upper() != mac.upper():
                continue
            if not getattr(connected, 'value', connected):
                continue
            res = await bus.call(Message(
                destination='org.bluez', path=path,
                interface='org.bluez.Device1', member='Disconnect'))
            dropped = dropped or res.message_type != MessageType.ERROR
        return dropped
    finally:
        bus.disconnect()


# ---------------------------------------------------------------------------
# Cache für /api/status
# ---------------------------------------------------------------------------
_cache: dict = {}
_cache_lock = threading.Lock()


def get_status() -> dict:
    """Letzter bekannter Powerbank-Status (leer, wenn deaktiviert)."""
    if not config.POWERBANK_MAC:
        return {}
    with _cache_lock:
        return dict(_cache)


# ---------------------------------------------------------------------------
# Akku-Schutz
# ---------------------------------------------------------------------------
class _Guard:
    warned = False
    low_count = 0
    shutdown_started = False


_guard = _Guard()


def _evaluate(percent: int, input_w: float) -> str:
    """Entscheidet über Warnung/Herunterfahren. Rückgabe: 'warn', 'shutdown' oder ''."""
    if _guard.shutdown_started:
        return ''
    charging = input_w >= 1.0

    if percent <= config.POWERBANK_SHUTDOWN_PERCENT and not charging:
        _guard.low_count += 1
    else:
        _guard.low_count = 0
    if _guard.low_count >= 2:
        _guard.shutdown_started = True
        return 'shutdown'

    if percent >= config.POWERBANK_WARN_PERCENT + 2:
        _guard.warned = False
    elif percent <= config.POWERBANK_WARN_PERCENT and not _guard.warned:
        _guard.warned = True
        return 'warn'
    return ''


async def _logind_poweroff() -> None:
    from dbus_fast import BusType, Message, MessageType
    from dbus_fast.aio import MessageBus

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    try:
        reply = await bus.call(Message(
            destination='org.freedesktop.login1',
            path='/org/freedesktop/login1',
            interface='org.freedesktop.login1.Manager',
            member='PowerOff',
            signature='b',
            body=[False],
        ))
        if reply.message_type == MessageType.ERROR:
            raise RuntimeError(f'logind PowerOff: {reply.error_name} {reply.body}')
    finally:
        bus.disconnect()


def _shutdown(percent: int) -> None:
    from .camera import CameraManager, _kill_process_group
    from .monitoring import _send_gotify_alert
    from .runtime import _lock, state

    msg = f'Powerbank bei {percent} % – Raspberry Pi wird heruntergefahren'
    logger.critical(msg)
    _send_gotify_alert('Akku leer', msg)

    # Laufende Prozesse sauber beenden, damit Videodateien vollständig sind
    try:
        CameraManager.stop_detection_mode()
    except Exception as exc:
        logger.warning('Detection stoppen vor Shutdown fehlgeschlagen: %s', exc)
    with _lock:
        proc = state.recording_process
    if proc:
        _kill_process_group(proc, timeout=5)

    try:
        asyncio.run(_logind_poweroff())
    except Exception as exc:
        logger.error('Herunterfahren fehlgeschlagen: %s', exc)
        _send_gotify_alert('Akku leer', f'Herunterfahren fehlgeschlagen: {exc}')
        _guard.shutdown_started = False


def _handle_reading(st: dict) -> None:
    from .monitoring import _send_gotify_alert

    percent = st['battery_percent']
    action = _evaluate(percent, st.get('total_input_w') or 0.0)
    if action == 'warn':
        msg = f'Powerbank nur noch bei {percent} % – bitte laden'
        logger.warning(msg)
        _send_gotify_alert('Akku niedrig', msg)
    elif action == 'shutdown':
        _shutdown(percent)


def _powerbank_updater() -> None:
    """Daemon-Thread: liest die Powerbank periodisch aus."""
    if not config.POWERBANK_MAC:
        logger.info('Powerbank-Überwachung deaktiviert (PI_DAEMON_POWERBANK_MAC leer)')
        return
    logger.info('Powerbank-Überwachung aktiv: %s alle %ds (Warnung ≤%d%%, Shutdown ≤%d%%)',
                config.POWERBANK_MAC, config.POWERBANK_INTERVAL,
                config.POWERBANK_WARN_PERCENT, config.POWERBANK_SHUTDOWN_PERCENT)
    failures = 0
    while True:
        try:
            st = asyncio.run(asyncio.wait_for(_read_once(config.POWERBANK_MAC), _READ_TIMEOUT))
            st['ok'] = True
            st['updated_at'] = datetime.now(timezone.utc).isoformat()
            with _cache_lock:
                _cache.clear()
                _cache.update(st)
            failures = 0
            _handle_reading(st)
        except Exception as exc:
            failures += 1
            err = str(exc) or type(exc).__name__
            # Alte Messwerte behalten, nur Fehler markieren
            with _cache_lock:
                _cache['ok'] = False
                _cache['error'] = err
            log = logger.warning if failures in (1, 10) or failures % 60 == 0 else logger.debug
            log('Powerbank nicht lesbar (%dx): %s', failures, err)
            # Hängt noch eine alte Verbindung auf dem Host? Dann trennen – die nächste
            # Abfrage findet die Powerbank wieder.
            try:
                if asyncio.run(asyncio.wait_for(_drop_stale_connection(config.POWERBANK_MAC), 10)):
                    logger.warning('Powerbank: hängende Bluetooth-Verbindung getrennt')
            except Exception as exc:
                logger.debug('Powerbank: Verbindung trennen nicht möglich: %s', exc)
        time.sleep(config.POWERBANK_INTERVAL)
