"""Sync-Ziele (Multi-Target rsync): Einstellungen laden/speichern, Legacy-Migration."""
import json
import os
from pathlib import Path

from . import config
from .config import logger


def _load_sync_settings() -> dict:
    try:
        return json.loads(Path(config.SETTINGS_FILE).read_text())
    except Exception:
        return {'targets': []}


def _save_sync_settings(data: dict) -> None:
    try:
        Path(config.SETTINGS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(config.SETTINGS_FILE).write_text(json.dumps(data, indent=2))
    except Exception as exc:
        logger.error('Einstellungen konnten nicht gespeichert werden: %s', exc)


def _get_active_targets() -> list:
    """Gibt alle aktiven (enabled=True, host+user+path gesetzt) Sync-Ziele zurück."""
    s = _load_sync_settings()
    result = []
    for t in s.get('targets', []):
        if t.get('enabled', True) and t.get('host') and t.get('user') and t.get('path'):
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
