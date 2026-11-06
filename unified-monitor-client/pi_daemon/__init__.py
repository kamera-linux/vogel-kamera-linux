"""Pi Daemon Secure – HTTPS Flask + JWT + TOTP, Bird Camera Prozesssteuerung.

Module:
  config      Umgebungsvariablen, Logging, Startprüfung
  runtime     gemeinsamer Laufzeit-Zustand (_lock, state)
  settings    persistente Einstellungen (Engine, Detection, Kamera, Aufnahme-Profile)
  hailo       Hailo-NPU Hardware-Info + Temperatur-Thread
  monitoring  Health-Cache, Gotify-Alerts, Thread-Diagnose
  sync        Sync-Ziele für rsync-Transfer
  camera      Detection-Prozess, Aufnahme, Konvertierung, Transfer, Watchdog
  api         Flask-App mit allen HTTP-Routen
  main        Start (Threads + HTTPS-Server)

Gestartet wird über unified-monitor-client/pi_daemon_secure.py.
"""
