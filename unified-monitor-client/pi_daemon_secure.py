#!/usr/bin/env python3
"""
Pi Daemon Secure – HTTPS Flask + JWT + TOTP
Bird Camera Prozesssteuerung, gesichert mit 2FA

Läuft als Docker-Container auf dem Raspberry Pi.
Konfiguration ausschließlich über Umgebungsvariablen / .env-Datei.

Der Code liegt im Paket pi_daemon/ (Übersicht: pi_daemon/__init__.py).
Diese Datei bleibt als Startpunkt erhalten (Docker-Entrypoint, Hotpatch).
"""
import sys
from pathlib import Path

# Paket pi_daemon/ liegt neben dieser Datei – auch bei python -I / PYTHONSAFEPATH finden
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pi_daemon.main import main  # noqa: E402

if __name__ == '__main__':
    main()
