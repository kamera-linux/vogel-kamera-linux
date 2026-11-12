"""Einstiegspunkt: Startprüfung, Hintergrund-Threads, HTTPS-Server."""
import threading
from pathlib import Path

from . import config
from .api import app
from .camera import (
    CameraManager, _auto_convert_watcher, _post_process_worker, detection_watchdog,
)
from .config import logger
from .hailo import _hailo_temp_updater
from .monitoring import _thread_monitor_daemon
from .powerbank import _powerbank_updater
from .sync import _migrate_legacy_settings


def main() -> None:
    config.check_config()

    # Einstellungen beim Start laden (Legacy SYNC_DEST aus Umgebungsvariable)
    _migrate_legacy_settings()

    CameraManager.start_detection_mode()

    # Konvertierung + Transfer fertiger Aufnahmen (hält die Kamera nicht auf)
    threading.Thread(target=_post_process_worker, daemon=True, name='post-process').start()
    threading.Thread(target=_auto_convert_watcher, daemon=True, name='auto-convert').start()
    threading.Thread(target=detection_watchdog, daemon=True, name='detection-watchdog').start()
    threading.Thread(target=_hailo_temp_updater, daemon=True, name='hailo-temp').start()
    # Thread-Monitoring Daemon: überwacht Deadlocks und aktualisiert Health-Cache
    threading.Thread(target=_thread_monitor_daemon, daemon=True, name='thread-monitor').start()
    # Powerbank per Bluetooth auslesen, Warnung/Shutdown bei niedrigem Akku
    threading.Thread(target=_powerbank_updater, daemon=True, name='powerbank').start()

    ssl_ctx = ((config.CERT_FILE, config.KEY_FILE)
               if Path(config.CERT_FILE).exists() and Path(config.KEY_FILE).exists() else None)
    if ssl_ctx is None:
        logger.warning('SSL-Zertifikat nicht gefunden – startet UNVERSCHLÜSSELT (nur Entwicklung!)')

    logger.info('Pi Daemon Secure auf Port %d (HTTPS=%s)', config.PORT, 'ja' if ssl_ctx else 'NEIN')

    app.run(
        host='0.0.0.0',
        port=config.PORT,
        ssl_context=ssl_ctx,
        threaded=True,
        use_reloader=False,
    )
