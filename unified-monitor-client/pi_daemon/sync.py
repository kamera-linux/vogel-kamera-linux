"""Sync-Ziele (Multi-Target rsync): Einstellungen laden/speichern, Legacy-Migration."""
import json
import os
import re
from pathlib import Path

from . import config
from .config import logger
from .storage import write_json_atomic

# ---------------------------------------------------------------------------
# Eingabeprüfung: host/user/path landen in ssh- und rsync-Argumenten.
# Ohne Prüfung könnte z. B. user="-oProxyCommand=…" einen Befehl ausführen.
# ---------------------------------------------------------------------------
_HOST_RE = re.compile(r'^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.?)+$|^[0-9A-Fa-f:]+$')
_USER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.-]{0,31}$')
_PATH_RE = re.compile(r'^[A-Za-z0-9_./~+@,=-]{1,255}$')

KNOWN_HOSTS_FILE = '/config/known_hosts'


def validate_target(host: str, user: str, path: str) -> str:
    """Prüft ein Sync-Ziel. Rückgabe: Fehlermeldung oder '' wenn gültig."""
    if not host or len(host) > 253 or not _HOST_RE.match(host):
        return f'Ungültiger Host: {host!r} (erlaubt: Hostname, IPv4 oder IPv6)'
    if not user or not _USER_RE.match(user):
        return f'Ungültiger Benutzer: {user!r} (erlaubt: Buchstaben, Ziffern, _ . -; nicht mit - beginnen)'
    if not path or path.startswith('-') or not _PATH_RE.match(path):
        return (f'Ungültiger Pfad: {path!r} (erlaubt: Buchstaben, Ziffern, / . _ ~ + @ , = -; '
                'keine Leerzeichen, nicht mit - beginnen)')
    return ''


def ssh_options(key_file: str) -> list:
    """Gemeinsame ssh-Optionen: Host-Key beim ersten Kontakt merken, danach prüfen."""
    opts = [
        '-o', 'StrictHostKeyChecking=accept-new',
        '-o', f'UserKnownHostsFile={KNOWN_HOSTS_FILE}',
        '-o', 'ConnectTimeout=10',
        '-o', 'BatchMode=yes',
    ]
    if Path(key_file).exists():
        opts += ['-i', key_file]
    return opts


def write_private_key(key_file: Path, content: str) -> None:
    """Schreibt einen SSH-Key direkt mit Rechten 0600 (kein kurzzeitig lesbarer Zustand)."""
    key_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as fh:
        os.fchmod(fh.fileno(), 0o600)
        fh.write(content + '\n')


def _load_sync_settings() -> dict:
    try:
        return json.loads(Path(config.SETTINGS_FILE).read_text())
    except Exception:
        return {'targets': []}


def _save_sync_settings(data: dict) -> None:
    try:
        write_json_atomic(config.SETTINGS_FILE, data)
    except Exception as exc:
        logger.error('Einstellungen konnten nicht gespeichert werden: %s', exc)


def _get_active_targets() -> list:
    """Gibt alle aktiven (enabled=True, host+user+path gesetzt) Sync-Ziele zurück."""
    s = _load_sync_settings()
    result = []
    for t in s.get('targets', []):
        if t.get('enabled', True) and t.get('host') and t.get('user') and t.get('path'):
            err = validate_target(t['host'], t['user'], t['path'])
            if err:
                logger.error('Sync-Ziel %r übersprungen: %s', t.get('name'), err)
                continue
            result.append(t)
    return result


# Einstellungen beim Start laden (Legacy SYNC_DEST aus Umgebungsvariable)
def _migrate_legacy_settings() -> None:
    """Migriert alte Einzel-Host-Konfiguration in targets-Array."""
    s = _load_sync_settings()
    if 'targets' not in s:
        s['targets'] = []
    # Legacy: sync_host/sync_user/sync_path im Root → in targets migrieren
    if s.get('sync_host') and not s['targets']:
        s['targets'].append({
            'id': 0, 'name': 'Standard-Ziel',
            'host': s.pop('sync_host', ''),
            'user': s.pop('sync_user', ''),
            'path': s.pop('sync_path', ''),
            'enabled': True,
        })
        _save_sync_settings(s)
    # Legacy: alter sync_rsa Key → sync_key_0
    old_key = Path('/config/sync_rsa')
    new_key = Path('/config/sync_key_0')
    if old_key.exists() and not new_key.exists():
        try:
            import shutil
            shutil.copy2(str(old_key), str(new_key))
            os.chmod(str(new_key), 0o600)
        except Exception:
            pass
