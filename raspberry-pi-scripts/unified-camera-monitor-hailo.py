#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hailo NPU Bird Detector – Vogel-Kamera-Linux
==============================================

Nutzt rpicam-hello + Hailo YOLOv8 HEF für 25+ fps Vogel-Erkennung
auf dem Raspberry Pi AI HAD+.  Kein YOLO-CPU, kein LD_LIBRARY_PATH-Hack,
kein picamera2-Import – läuft direkt mit Container-Python.

Architektur:
    rpicam-hello --post-process-file hailo_yolov8_inference.json -v 2
        ↓ stderr-Pipe
    Python Parser  →  COCO class "bird" + Confidence-Filter
        ↓ Vogel erkannt
    sys.exit(0)  ← pi_daemon_secure.py Watchdog startet Aufnahme

Exit-Code-Protokoll mit pi_daemon_secure.py:
    0  → Vogel erkannt  (daemon triggert Aufnahme bei detection_mode=True)
    1  → Startfehler    (daemon wartet und versucht neu)
    2  → Gestoppt       (daemon hat SIGTERM gesendet – kein Aufnahme-Trigger)

Performance (AI HAD+ mit Hailo-8):
    FPS:      25–28
    CPU-Last: < 5 %   (NPU erledigt Inferenz)
    RAM:      ~50 MB  (kein YOLO-Modell geladen)
"""

import argparse
import logging
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging  (FileHandler = selbe Log-Datei wie CPU-YOLO-Script → nahtloser Tausch)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/unified-camera-monitor.log'),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
HAILO_JSON   = '/usr/share/rpi-camera-assets/hailo_yolov8_inference.json'
RPICAM_HELLO = '/usr/local/bin/rpicam-hello'   # Container-Wrapper (→ Host-Binary)

# COCO-Klassennamen für Vogel – rpicam-hello gibt sie lowercase aus
BIRD_CLASSES = {'bird'}

# Format der Erkennungszeilen von rpicam-hello -v 2:
#   "bird : 0.923 (123, 456, 789, 234)"
# Die regex sucht überall in der Zeile (finditer) um Logging-Präfixe zu ignorieren.
_DETECTION_RE = re.compile(
    r'(\w+)\s*:\s*([\d.]+)\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)'
)

# ---------------------------------------------------------------------------
# Signal-Handler (SIGTERM kommt vom Daemon wenn er die Aufnahme startet)
# ---------------------------------------------------------------------------
_stopped_by_signal = False


def _on_signal(signum, _frame):
    global _stopped_by_signal
    logger.info('Signal %d empfangen – fahre herunter …', signum)
    _stopped_by_signal = True


signal.signal(signal.SIGTERM, _on_signal)
signal.signal(signal.SIGINT,  _on_signal)


# ---------------------------------------------------------------------------
# Haupt-Logik
# ---------------------------------------------------------------------------

def _build_cmd(fps: int, resolution: str) -> list:
    w, h = resolution.split('x', 1)
    return [
        RPICAM_HELLO,
        '--post-process-file', HAILO_JSON,
        '--framerate', str(fps),
        '--width',     w,
        '--height',    h,
        '-t', '0',     # unbegrenzt laufen
        '-n',          # kein Display/Preview-Fenster
        '-v', '2',     # verbose: enthält Detection-Ausgaben
    ]


def _terminate(proc: subprocess.Popen) -> None:
    """Beendet rpicam-hello sauber."""
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description='Hailo NPU Bird Detector')
    parser.add_argument('--threshold',  type=float, default=0.45,
                        help='Confidence-Schwelle (Standard 0.45)')
    parser.add_argument('--cooldown',   type=int,   default=15,
                        help='Mindestabstand zwischen Triggern in Sekunden (Standard 15)')
    parser.add_argument('--fps',        type=int,   default=25,
                        help='Ziel-FPS (Standard 25)')
    parser.add_argument('--resolution', type=str,   default='1920x1080',
                        help='Kamera-Auflösung WxH (Standard 1920x1080)')
    args = parser.parse_args()

    # ── Voraussetzungen prüfen ────────────────────────────────────────────
    if not Path(HAILO_JSON).exists():
        logger.error('Hailo-JSON nicht gefunden: %s', HAILO_JSON)
        logger.error('Hailo-Modell-Dateien nicht gemountet?  '
                     'Prüfe Volume-Mount /usr/share/rpi-camera-assets in docker-compose.yml')
        sys.exit(1)

    if not Path(RPICAM_HELLO).exists():
        logger.error('rpicam-hello Wrapper nicht gefunden: %s', RPICAM_HELLO)
        logger.error('Dockerfile-Wrapper oder /opt/rpicam-hello Volume-Mount fehlt?')
        sys.exit(1)

    cmd = _build_cmd(args.fps, args.resolution)
    logger.info('Hailo NPU Detector gestartet (threshold=%.2f, fps=%d, res=%s)',
                args.threshold, args.fps, args.resolution)
    logger.info('Starte: %s', ' '.join(cmd))

    # ── rpicam-hello starten (mit Startup-Retry) ──────────────────────────
    # rpicam-hello kann bei Container-Start oder nach einer Aufnahme kurz
    # fehlschlagen (libcamera-Init noch nicht bereit).  3 Versuche mit je 5s.
    proc = None
    for attempt in range(1, 4):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,          # zeilenweise, minimale Latenz
            )
            # Kurz warten und prüfen ob rpicam-hello sofort crasht
            time.sleep(2)
            if proc.poll() is not None:
                logger.warning('rpicam-hello sofort beendet (rc=%d), Versuch %d/3',
                               proc.returncode, attempt)
                proc = None
                if attempt < 3:
                    time.sleep(5)
                continue
            logger.info('rpicam-hello läuft (PID=%d, Versuch %d/3)', proc.pid, attempt)
            break
        except Exception as exc:
            logger.error('rpicam-hello Start fehlgeschlagen (Versuch %d/3): %s', attempt, exc)
            proc = None
            if attempt < 3:
                time.sleep(5)

    if proc is None:
        logger.error('rpicam-hello konnte nach 3 Versuchen nicht gestartet werden')
        sys.exit(1)

    # ── Detection-Loop: stderr zeilenweise einlesen ───────────────────────
    bird_found = False
    try:
        for line in proc.stderr:
            if _stopped_by_signal:
                break

            line = line.rstrip()
            if not line:
                continue

            for m in _DETECTION_RE.finditer(line):
                class_name = m.group(1).lower().strip()
                confidence = float(m.group(2))

                if class_name in BIRD_CLASSES and confidence >= args.threshold:
                    logger.info(
                        '🐦 Vogel erkannt! class=%s conf=%.3f (Hailo NPU) – beende für Aufnahme',
                        class_name, confidence,
                    )
                    bird_found = True
                    break

            if bird_found:
                break

    except (IOError, OSError):
        # SIGTERM unterbrach den Blocking-Read → normal
        pass

    # ── Aufräumen ─────────────────────────────────────────────────────────
    _terminate(proc)

    if _stopped_by_signal:
        logger.info('Hailo Detector gestoppt durch Signal (kein Vogel-Trigger)')
        sys.exit(2)

    if bird_found:
        # rc=0 → pi_daemon_secure.py Watchdog triggert Aufnahme (wenn detection_mode=True)
        sys.exit(0)

    # Unerwartetes Ende von rpicam-hello (rc != None)
    rc = proc.returncode if proc.returncode is not None else -1
    logger.error('rpicam-hello unerwartet beendet (rc=%d)', rc)
    sys.exit(1)


if __name__ == '__main__':
    main()
