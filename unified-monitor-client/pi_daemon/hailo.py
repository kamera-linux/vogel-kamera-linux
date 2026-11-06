"""Hailo-NPU Hardware-Info (statisch gecacht) + Temperatur-Hintergrund-Thread."""
import os
import subprocess
import threading
import time
from pathlib import Path

from .config import logger


# ---------------------------------------------------------------------------
# Hailo Hardware-Info (gecacht, getrennte TTLs für statische/dynamische Daten)
# ---------------------------------------------------------------------------
_hailo_hw_cache: dict = {}
_hailo_hw_cache_time: float = 0.0     # letzte Aktualisierung statischer Info
_HAILO_HW_CACHE_TTL: float = 60.0    # Sekunden – Board/FW/Treiber (ändert sich selten)

# Python-Snippet für hailo_platform.
# /usr/lib/python3/dist-packages ist per Bind-Mount eingebunden (hailo_platform v4.23.0).
# System-Python fragt Treiber über /dev/hailo0 → privileged Container erforderlich.
_HAILO_TEMP_SCRIPT = (
    'import sys; sys.path.insert(0, "/usr/lib/python3/dist-packages");'
    'from hailo_platform import Device;'
    'd=Device();'
    't=d.control.get_chip_temperature();'
    'ext=d.control.get_extended_device_information();'
    'h=d.control._get_health_information();'
    'print(f"{(t.ts0_temperature+t.ts1_temperature)/2:.2f},{int(ext.neural_network_core_clock_rate//1_000_000)},{int(h.temperature_throttling_active)},{int(h.current_temperature_zone)},{int(h.current_temperature_throttling_level)}");'
    'd.release()'
)

# ── Hailo-Temp-Cache (wird ausschließlich vom Background-Thread beschrieben) ─
# HTTP-Handler liest nur noch diesen Cache → kein subprocess im Request-Thread →
# kein Deadlock wenn Device() auf /dev/hailo0 blockiert (D-State nach SIGKILL).
_hailo_temp_bg: dict = {}                # npu_temp_c, nn_clock_mhz, throttle_*
_hailo_temp_bg_lock = threading.Lock()   # schützt _hailo_temp_bg
_HAILO_TEMP_INTERVAL: float = 30.0      # Sekunden zwischen Messungen


def _hailo_temp_updater() -> None:
    """Daemon-Thread: aktualisiert Hailo-Temperatur/Clock/Throttle im Hintergrund.

    Läuft unabhängig vom HTTP-Request-Handler. Wenn Device() auf /dev/hailo0
    blockiert (Subprocess in D-State), hängt nur dieser Thread – niemals der
    Web-Server. Nach SIGKILL des Subprozesses via Prozessgruppen-Kill wird
    comm() NICHT abgewartet, um Blocking auf D-State-Proz. zu vermeiden.
    """
    while True:
        time.sleep(_HAILO_TEMP_INTERVAL)
        if not Path('/dev/hailo0').exists():
            continue
        proc = None
        try:
            proc = subprocess.Popen(
                ['python3', '-c', _HAILO_TEMP_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env={**os.environ, 'LD_LIBRARY_PATH': '/usr/lib:/usr/local/lib'},
                start_new_session=True,   # eigene Prozessgruppe → killpg möglich
            )
            try:
                stdout, _ = proc.communicate(timeout=12)
                line = stdout.decode('utf-8', errors='replace').strip()
                if line and ',' in line:
                    parts = line.split(',')
                    new: dict = {}
                    if len(parts) >= 2:
                        new['npu_temp_c']   = round(float(parts[0]), 1)
                        new['nn_clock_mhz'] = int(parts[1])
                    if len(parts) >= 4:
                        new['throttle_active'] = bool(int(parts[2]))
                        new['throttle_zone']   = int(parts[3])
                    if len(parts) >= 5:
                        new['throttle_level']  = int(parts[4])
                    with _hailo_temp_bg_lock:
                        _hailo_temp_bg.update(new)
            except subprocess.TimeoutExpired:
                # Subprocess blockiert (Device() wartet auf /dev/hailo0).
                # Prozessgruppe per SIGKILL beenden – KEIN zweites communicate()
                # da der Prozess im D-State sein kann und nicht sofort stirbt.
                try:
                    os.killpg(proc.pid, 9)
                except Exception:
                    pass
                logger.warning('Hailo-Temp-Script Timeout (Gerät vermutlich belegt)')
        except Exception as exc:
            logger.debug('Hailo-Temp-Updater-Fehler: %s', exc)
            if proc is not None:
                try:
                    os.killpg(proc.pid, 9)
                except Exception:
                    pass



def _get_hailo_hw_info() -> dict:
    """Liest Hailo-Hardware-Informationen (statisch aus sysfs/hailortcli + dynamisch aus Cache).

    Statische Daten (Board, FW, Treiber): 60 s TTL, kurze subprocess-Calls (hailortcli).
    Dynamische Daten (Temperatur, NN-Clock, Throttle): aus _hailo_temp_bg, der vom
    Background-Thread _hailo_temp_updater() befüllt wird – nie blockierend im HTTP-Thread.
    """
    global _hailo_hw_cache, _hailo_hw_cache_time
    now = time.monotonic()

    # ── Statische Info (60 s TTL) ────────────────────────────────────────
    if now - _hailo_hw_cache_time >= _HAILO_HW_CACHE_TTL:
        info: dict = {}

        # Schnell-Check: Gerät vorhanden?
        if not Path('/dev/hailo0').exists():
            _hailo_hw_cache = info
            _hailo_hw_cache_time = now
            return info

        info['device_present'] = True

        def _sysfs(path: str) -> str:
            try:
                return Path(path).read_text().strip()
            except Exception:
                return ''

        # Treiberversion aus sysfs
        drv = _sysfs('/sys/module/hailo_pci/version')
        if drv:
            info['driver_version'] = drv

        # Board-Typ aus accelerator_type
        acc = _sysfs('/sys/class/hailo_chardev/hailo0/accelerator_type')
        _ACCEL_NAMES = {'0': 'Hailo-8', '1': 'Hailo-8L', '2': 'Hailo-10H'}
        if acc in _ACCEL_NAMES:
            info['board_name'] = _ACCEL_NAMES[acc]
        elif acc:
            info['board_name'] = f'Hailo (type {acc})'

        # PCIe-Slot-Adresse
        loc = _sysfs('/sys/class/hailo_chardev/hailo0/board_location')
        if loc:
            info['board_location'] = loc

        # FW-Version via hailortcli (Trixie-Base: gleiche glibc wie Host)
        try:
            result = subprocess.run(
                ['/usr/bin/hailortcli', 'fw-control', 'identify'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith('Firmware Version:'):
                    fw = line.split(':', 1)[1].strip()
                    info['fw_version'] = fw.split()[0] if fw else fw
                elif line.startswith('Board Name:') and 'board_name' not in info:
                    info['board_name'] = line.split(':', 1)[1].strip()
        except Exception:
            pass

        _hailo_hw_cache = info
        _hailo_hw_cache_time = now

    # ── Dynamische Info: aus Background-Thread-Cache (nie blockierend) ──
    if _hailo_hw_cache.get('device_present'):
        with _hailo_temp_bg_lock:
            for key in ('npu_temp_c', 'nn_clock_mhz', 'throttle_active', 'throttle_zone', 'throttle_level'):
                if key in _hailo_temp_bg:
                    _hailo_hw_cache[key] = _hailo_temp_bg[key]

    return _hailo_hw_cache
