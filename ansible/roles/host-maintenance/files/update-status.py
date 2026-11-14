#!/usr/bin/python3 -I
"""Update-Status des Pi für pi-daemon /metrics (→ Prometheus → Grafana).

Schreibt /etc/pi-daemon/update-status.json (im Container: /config/update-status.json).
Läuft als root über update-status.timer alle 15 Minuten und am Ende von boot-update.sh.
Liest nur – führt kein apt update aus (das macht boot-update.sh beim Systemstart).
"""
import json
import os
import platform
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

OUT = Path('/etc/pi-daemon/update-status.json')
UU_LOG = Path('/var/log/unattended-upgrades/unattended-upgrades.log')
APT_HISTORY = Path('/var/log/apt/history.log')
BOOT_STATUS = Path('/run/boot-health-check.status')
ENV = {**os.environ, 'LC_ALL': 'C'}


def run(*cmd) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=120).stdout
    except Exception:
        return ''


def mtime(path):
    try:
        return int(Path(path).stat().st_mtime)
    except OSError:
        return None


def pending_updates():
    held = set(run('apt-mark', 'showhold').split())
    names, security = [], 0
    for line in run('apt', 'list', '--upgradable').splitlines():
        if '/' not in line or line.startswith('Listing'):
            continue
        name, rest = line.split('/', 1)
        names.append(name)
        if '-security' in rest.split(' ', 1)[0]:
            security += 1
    return {
        'pending': len(names),
        'pending_security': security,
        'held_pending': sum(1 for n in names if n in held),
    }


def last_unattended_run():
    """Letzter automatischer Lauf von unattended-upgrade aus dessen Log.

    boot-update.sh startet ihn mit LC_ALL=C.UTF-8, er schreibt also englisch.
    Von Hand gestartete Läufe (deutsche Meldungen, z. B. --dry-run) zählen so nicht mit.
    """
    try:
        lines = UU_LOG.read_text(errors='replace').splitlines()
    except OSError:
        return None
    start = None
    for i, line in enumerate(lines):
        if 'Starting unattended upgrades script' in line:
            start = i
    if start is None:
        return None
    block = lines[start:]
    try:
        ts = int(datetime.strptime(block[0][:19], '%Y-%m-%d %H:%M:%S').timestamp())
    except ValueError:
        return None
    upgraded = 0
    for line in block:
        m = re.search(r'Packages that will be upgraded: (.*)', line)
        if m:
            upgraded = len(m.group(1).split())
    ok = not any(' ERROR ' in line for line in block)
    return {'time': ts, 'ok': ok, 'upgraded': upgraded}


def last_auto_install():
    """Zeitpunkt der letzten Installation durch unattended-upgrade (apt-History)."""
    try:
        text = APT_HISTORY.read_text(errors='replace')
    except OSError:
        return None
    last = None
    for entry in text.split('\n\n'):
        # unattended-upgrade installiert über python-apt: kein "Commandline:"-Eintrag
        # (manuelle apt-Aufrufe haben immer einen, z. B. "apt install unattended-upgrades")
        cmd = re.search(r'Commandline: (.*)', entry)
        if 'Start-Date' in entry and (cmd is None or re.search(r'/unattended-upgrade(\s|$)', cmd.group(1))):
            m = re.search(r'Start-Date: (\S+\s+\S+)', entry)
            if m:
                last = m.group(1)
    if not last:
        return None
    try:
        return int(datetime.strptime(last, '%Y-%m-%d %H:%M:%S').timestamp())
    except ValueError:
        return None


def kernels():
    running = platform.release()
    flavor = running.rsplit('+', 1)[-1]
    found = [d.name for d in Path('/lib/modules').iterdir() if d.name.endswith('+' + flavor)]

    def key(v):
        return [int(x) if x.isdigit() else x for x in re.split(r'[.+-]', v)]

    newest = max(found, key=key) if found else running
    return running, newest


def boot_check():
    try:
        msg = BOOT_STATUS.read_text().strip()
    except OSError:
        return None
    return {'ok': msg.startswith('OK') or msg.startswith('übersprungen'),
            'time': mtime(BOOT_STATUS), 'message': msg}


def main():
    running, newest = kernels()
    status = {
        'generated': int(time.time()),
        **pending_updates(),
        'reboot_required': Path('/run/reboot-required').exists() or running != newest,
        'kernel_running': running,
        'kernel_newest': newest,
        'lists_updated': mtime('/var/lib/apt/periodic/update-success-stamp')
                         or mtime('/var/lib/apt/periodic/update-stamp'),
        'last_run': last_unattended_run(),
        'last_install': last_auto_install(),
        'boot_check': boot_check(),
    }
    tmp = OUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(status, ensure_ascii=False, indent=1) + '\n')
    tmp.chmod(0o644)
    tmp.replace(OUT)


if __name__ == '__main__':
    main()
