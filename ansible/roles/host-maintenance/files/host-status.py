#!/usr/bin/python3 -I
"""Host-Werte für pi-daemon /metrics (→ Prometheus → Grafana), die der Container nicht lesen kann.

Schreibt /run/vogelkamera/host-status.json (im Container: /host-status/host-status.json).
Läuft als root über host-status.timer jede Minute. /run liegt im RAM – die SD-Karte
wird dadurch nicht belastet.

  - Versorgungsspannung am USB-C-Eingang (PMIC, vcgencmd pmic_read_adc EXT5V_V)
  - Unterspannungs-/Drossel-Flags (vcgencmd get_throttled)
  - Unterspannungs-Meldungen des Kernels seit dem Boot
  - WLAN-Signal (/proc/net/wireless – der Container hat ein eigenes Netz)
  - Eingriffe des WLAN-Watchdogs (Zähler, die wlan-watchdog.sh hochzählt)
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path

OUT_DIR = Path('/run/vogelkamera')
OUT = OUT_DIR / 'host-status.json'
WATCHDOG_DIR = OUT_DIR / 'wlan-watchdog'
INTERFACE = 'wlan0'
ENV = {**os.environ, 'LC_ALL': 'C'}


def run(*cmd) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=30).stdout
    except Exception:
        return ''


def supply_volts():
    m = re.search(r'=([0-9.]+)V', run('vcgencmd', 'pmic_read_adc', 'EXT5V_V'))
    return round(float(m.group(1)), 3) if m else None


def throttled():
    m = re.search(r'throttled=(0x[0-9a-fA-F]+)', run('vcgencmd', 'get_throttled'))
    return int(m.group(1), 16) if m else None


def undervoltage_events():
    out = run('journalctl', '-k', '-b', '-q', '--no-pager', '-o', 'cat')
    return sum(1 for line in out.splitlines() if 'Undervoltage detected' in line)


def wifi():
    # wlan0: 0000   50.  -60.  -256   0 ...   (Qualität, Pegel in dBm, Rauschen)
    try:
        for line in Path('/proc/net/wireless').read_text().splitlines():
            parts = line.split()
            if parts and parts[0] == f'{INTERFACE}:':
                return {'quality': int(float(parts[2].rstrip('.'))),
                        'signal_dbm': int(float(parts[3].rstrip('.')))}
    except (OSError, ValueError, IndexError):
        pass
    return None


def watchdog_counts():
    counts = {}
    if WATCHDOG_DIR.is_dir():
        for f in WATCHDOG_DIR.iterdir():
            try:
                counts[f.name] = int(f.read_text().strip() or 0)
            except (OSError, ValueError):
                pass
    return counts


def main():
    status = {
        'generated':           int(time.time()),
        'supply_volts':        supply_volts(),
        'throttled':           throttled(),
        'undervoltage_events': undervoltage_events(),
        'wifi':                wifi(),
        'wlan_watchdog':       watchdog_counts(),
    }
    OUT_DIR.mkdir(mode=0o755, exist_ok=True)
    tmp = OUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(status) + '\n')
    tmp.chmod(0o644)
    tmp.replace(OUT)


if __name__ == '__main__':
    main()
