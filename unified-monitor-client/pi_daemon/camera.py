"""Kamera-Steuerung: Detection-Prozess, Aufnahme (Video/Audio), Konvertierung, Transfer."""
import hashlib
import json
import os
import queue
import shlex
import shutil
import stat
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from . import config, settings
from .config import logger
from .runtime import _lock, state
from .settings import RECORDING_PROFILES, _RESOLUTION_MAP, _load_rec_settings
from .sync import _get_active_targets, ssh_options


# ---------------------------------------------------------------------------
# Nachbearbeitung (Konvertierung + Transfer) läuft getrennt von der Aufnahme
# ---------------------------------------------------------------------------
# Dateien, die gerade aufgenommen werden oder auf Nachbearbeitung warten.
# Auto-Convert und Speicher-Aufräumung fassen sie nicht an. Geschützt durch _lock.
_busy_files: set = set()
_convert_lock = threading.Lock()   # immer nur ein ffmpeg gleichzeitig
_sweep_lock = threading.Lock()     # immer nur ein „alle ausstehenden"-Durchlauf
_post_queue: queue.Queue = queue.Queue()   # (Pfad, fps, slowmotion)


def _mark_busy(path: Path) -> None:
    with _lock:
        _busy_files.add(Path(path))


def _release_busy(path: Path) -> None:
    with _lock:
        _busy_files.discard(Path(path))


def _is_busy(path: Path) -> bool:
    with _lock:
        return Path(path) in _busy_files


# ---------------------------------------------------------------------------
# Verzeichnis-Scan (kurz gecacht)
# ---------------------------------------------------------------------------
# Die Web-GUI fragt den Status alle paar Sekunden ab. Statt bei jeder Anfrage
# mehrfach das Video-Verzeichnis zu durchlaufen, teilen sich Status, Aufnahmeliste
# und Pending-Zähler einen Scan, der _SCAN_TTL Sekunden gültig bleibt.
_MEDIA_SUFFIXES = ('.mp4', '.h264', '.wav')
_SCAN_TTL: float = 3.0
_scan_lock = threading.Lock()
_scan_cache: dict = {'at': float('-inf'), 'base': '', 'files': []}


def _scan_media() -> list:
    """Alle Mediendateien unter VIDEO_BASE_DIR als Liste von (Path, os.stat_result)."""
    base = Path(config.VIDEO_BASE_DIR)
    now = time.monotonic()
    with _scan_lock:
        if _scan_cache['base'] == str(base) and now - _scan_cache['at'] < _SCAN_TTL:
            return _scan_cache['files']
        files = []
        if base.exists():
            for f in base.rglob('*'):
                if f.suffix not in _MEDIA_SUFFIXES:
                    continue
                try:
                    st = f.stat()
                except OSError:
                    continue
                if stat.S_ISREG(st.st_mode):
                    files.append((f, st))
        _scan_cache.update(at=now, base=str(base), files=files)
        return files


def invalidate_media_scan() -> None:
    """Nach Löschen/Anlegen von Dateien aufrufen, damit die GUI sofort den neuen Stand sieht."""
    with _scan_lock:
        _scan_cache['at'] = float('-inf')


def _is_listed(f: Path) -> bool:
    """MP4s und manuell aufgenommene Audio-Dateien (_audio im Namen) erscheinen in der Liste.
    Begleit-WAVs von Video-Aufnahmen und rohe H264-Dateien nicht."""
    return f.suffix == '.mp4' or (f.suffix == '.wav' and '_audio' in f.name)


def media_summary() -> dict:
    """Kennzahlen für /api/status: Aufnahmen heute, ausstehende Konvertierungen und eine
    Prüfsumme der Aufnahmeliste (die GUI lädt die Liste nur neu, wenn sie sich ändert)."""
    files = _scan_media()
    today = datetime.now().strftime('%Y-%m-%d')
    paths = {f for f, _ in files}
    today_count = 0
    pending = 0
    h = hashlib.sha1()
    for f, st in sorted(files, key=lambda x: str(x[0])):
        if f.suffix == '.mp4' and datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d') == today:
            today_count += 1
        if f.suffix == '.h264' and f.with_suffix('.mp4') not in paths:
            pending += 1
        if _is_listed(f):
            h.update(f'{f}|{st.st_size}|{int(st.st_mtime)}\n'.encode())
    return {'today': today_count, 'pending': pending, 'rev': h.hexdigest()[:12]}


def _count_today_recordings() -> int:
    """Zählt Video-Aufnahmen im VIDEO_BASE_DIR die heute erstellt wurden."""
    return media_summary()['today']


def _read_last_detection() -> dict:
    """Letzte Erkennung aus /tmp/last-detection.json lesen (geschrieben vom Hailo-Script)."""
    try:
        p = Path('/tmp/last-detection.json')
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Kamera-Management
# ---------------------------------------------------------------------------
def _kill_process_group(proc: subprocess.Popen, timeout: int = 5) -> None:
    """Beendet eine Prozessgruppe per SIGTERM, danach SIGKILL."""
    try:
        os.killpg(os.getpgid(proc.pid), 15)
        proc.wait(timeout=timeout)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except Exception:
            pass


def _camera_reset() -> bool:
    """Setzt den IMX708-Kamera-Sensor per sysfs unbind/bind zurück.
    Gibt True zurück wenn der Reset erfolgreich war (Sensor antwortet wieder).
    """
    SYSFS        = '/sys/bus/i2c/drivers/imx708'
    DEVICE       = '11-001a'
    DRIVER_LINK  = f'/sys/bus/i2c/devices/{DEVICE}/driver'  # Symlink existiert wenn Treiber gebunden
    try:
        unbind = Path(SYSFS) / 'unbind'
        bind   = Path(SYSFS) / 'bind'
        if not unbind.exists():
            logger.warning('Kamera-Reset: sysfs-Pfad nicht gefunden (%s) – Hardware nicht RPi-Kamera?', SYSFS)
            return False

        # Nur unbinden wenn Sensor aktuell gebunden ist (sonst ENODEV → direkt bind)
        if Path(DRIVER_LINK).exists():
            logger.info('Kamera-Reset: imx708 unbind …')
            unbind.write_text(DEVICE)
            time.sleep(15)  # Sensor braucht Zeit zum Zurücksetzen (Voltage stabilisierung)
        else:
            logger.info('Kamera-Reset: imx708 bereits ungebunden – warte auf Sensor-Recovery …')
            time.sleep(10)

        logger.info('Kamera-Reset: imx708 bind …')
        bind.write_text(DEVICE)
        time.sleep(5)   # Warte auf asynchronen Probe-Vorgang
        # Prüfe ob Bind erfolgreich: driver-Symlink existiert wenn der Sensor antwortet
        if Path(DRIVER_LINK).exists():
            logger.info('Kamera-Reset erfolgreich – imx708 wieder gebunden')
            with _lock:
                state.camera_hw_error = False
            return True
        else:
            logger.warning('Kamera-Reset: Sensor antwortet nicht – Hardware-Neustart (Pi-Reboot) erforderlich')
            with _lock:
                state.camera_hw_error = True
                state.last_error = 'Kamera-Hardware-Fehler: IMX708-Sensor antwortet nicht. Pi-Neustart erforderlich.'
            return False
    except PermissionError:
        logger.warning('Kamera-Reset: keine Schreibrechte für sysfs – Daemon läuft nicht als root')
        return False
    except Exception as exc:
        logger.warning('Kamera-Reset fehlgeschlagen: %s', exc)
        return False


class CameraManager:

    # Umgebungsvariablen für den Detection-Subprozess:
    # Hailo-Script braucht keine Host-Python-Libs (kein picamera2/ultralytics) –
    # Container-Python 3.13 ist ausreichend, da nur subprocess + re genutzt werden.
    _DETECTION_ENV: dict = {
        **os.environ,
        'HOME': '/tmp',
    }

    # ── Detection-Prozess-Management ─────────────────────────────────────────

    @staticmethod
    def _launch_detection_process() -> 'subprocess.Popen | None':
        """Startet den Hailo-Detection-Subprozess. Gibt Popen zurück oder None bei Fehler."""
        try:
            proc = subprocess.Popen(
                # Container-Python reicht: Hailo-Script importiert nur stdlib
                [
                    'python3', settings.DETECTION_SCRIPT,
                    '--target-class', settings._detection_target,
                    '--threshold',    str(settings._detection_threshold),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp,
                env=CameraManager._DETECTION_ENV,
            )
            logger.info('Detection-Prozess gestartet PID=%d', proc.pid)
            return proc
        except Exception as exc:
            logger.error('Detection-Start fehlgeschlagen: %s', exc)
            state.last_error = str(exc)
            return None

    @staticmethod
    def start_detection() -> bool:
        """Startet Detection ohne Detection-Modus (Watchdog-Nutzung, kein Auto-Record)."""
        with _lock:
            if state.detection_running:
                return True
            proc = CameraManager._launch_detection_process()
            if proc:
                state.detection_process = proc
                state.detection_running = True
                return True
            return False

    @staticmethod
    def start_detection_mode() -> bool:
        """Aktiviert den Detection-Modus: blockiert manuelle Aufnahme,
        startet Detection-Loop mit Auto-Record bei Vogelerkennung."""
        with _lock:
            if state.detection_mode and state.detection_running:
                return True   # schon aktiv und Prozess läuft
            if state.recording_running:
                return False  # manuelle Aufnahme läuft noch
            # Vorhandenen Detection-Prozess explizit beenden (kann noch laufen, z.B.
            # nach manueller Aufnahme, die ihn via start_detection() neu gestartet hat).
            # Ohne diesen Kill würde ein zweiter Prozess die Kamera blockieren → rc=1.
            if state.detection_running and state.detection_process:
                _kill_process_group(state.detection_process)
                state.detection_running = False
                state.detection_process = None
                time.sleep(1)   # libcamera-Freigabe abwarten
            proc = CameraManager._launch_detection_process()
            if not proc:
                return False
            state.detection_process = proc
            state.detection_running = True
            if not state.detection_mode:
                state.detection_mode   = True
                state.birds_recorded   = 0
                logger.info('Detection-Modus aktiviert')
            else:
                logger.info('Detection-Modus: Prozess neu gestartet')
            return True

    @staticmethod
    def stop_detection_mode() -> bool:
        """Beendet den Detection-Modus sauber."""
        with _lock:
            if not state.detection_mode:
                return True
            state.detection_mode = False
            if state.detection_running and state.detection_process:
                _kill_process_group(state.detection_process)
                state.detection_running  = False
                state.detection_process  = None
            logger.info('Detection-Modus beendet (Vögel aufgenommen: %d)', state.birds_recorded)
            return True

    @staticmethod
    def stop_detection() -> bool:
        """Stoppt den Detection-Prozess (und deaktiviert ggf. Detection-Modus)."""
        with _lock:
            state.detection_mode = False
            if not state.detection_running:
                return True
            try:
                _kill_process_group(state.detection_process)
                state.detection_running = False
                state.detection_process = None
                logger.info('Detection gestoppt')
                return True
            except Exception as exc:
                logger.error('Detection-Stop fehlgeschlagen: %s', exc)
                state.detection_running = False
                state.detection_process = None
                state.last_error = str(exc)
                return False

    @staticmethod
    def _stop_detection_for_recording() -> None:
        """Stoppt Detection-Prozess und wartet auf libcamera-Freigabe.
        Muss MIT gehaltener _lock aufgerufen werden."""
        if state.detection_running and state.detection_process:
            _kill_process_group(state.detection_process)
            state.detection_running = False
            state.detection_process = None
            logger.info('Detection-Prozess für Aufnahme gestoppt')
        time.sleep(1)   # libcamera braucht Zeit zum Freigeben

    # ── Aufnahme ─────────────────────────────────────────────────────────────

    @staticmethod
    def record(duration: int = 15, resolution: str = '1080p', fps: int = 30,
               bitrate: int = 8000, slowmotion: bool = False,
               triggered_by: str = 'manual'):
        """Startet Recording. Blockiert bis Abschluss (in Background-Thread aufrufen).
        triggered_by: 'manual' oder 'detection'"""

        # ── Zustand prüfen und belegen ──────────────────────────────────────
        with _lock:
            if state.recording_running:
                return False, 'Recording läuft bereits'
            # Manuelle Aufnahme nur erlaubt wenn kein Detection-Modus
            if triggered_by == 'manual' and state.detection_mode:
                return False, 'Im Detection-Modus gesperrt'
            CameraManager._stop_detection_for_recording()
            state.recording_running    = True
            state.recording_started_at = time.monotonic()
            state.recording_duration_s = duration

        # ── Aufnahme (Lock freigegeben) ─────────────────────────────────────
        video_file = None
        queued = False
        try:
            w, h = _RESOLUTION_MAP.get(resolution, (1920, 1080))

            recording_dir = Path(config.VIDEO_BASE_DIR)
            recording_dir.mkdir(parents=True, exist_ok=True)

            # Format: Jahr_KW_Tag_Uhrzeit_Aufloesung_fps  (z.B. 2026_11_14_190045_1920x1080_30fps)
            ts         = datetime.now().strftime('%Y_%V_%d_%H%M%S')
            # Zeitlupe → rohes h264 (mehrere Playback-Versionen per ffmpeg)
            # Normal  → libav-MP4 direkt (Audio+Video im gleichen Prozess, perfekt synchron)
            if slowmotion:
                video_file = recording_dir / f'{ts}_{w}x{h}_{fps}fps.h264'
            else:
                video_file = recording_dir / f'{ts}_{w}x{h}_{fps}fps.mp4'
            _mark_busy(video_file)

            # Mic-Eingangspegel sicherstellen (USB-Audio-Karte setzt ihn manchmal auf 0%)
            try:
                subprocess.run(
                    ['amixer', '-c', '0', 'sset', 'Mic', '50%'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            except Exception:
                pass

            if slowmotion:
                # Zeitlupe: rohes h264, kein Audio, mehrere Playback-Versionen per ffmpeg
                video_cmd = [
                    'rpicam-vid',
                    '--width', str(w), '--height', str(h),
                    '--framerate', str(fps),
                    '--bitrate', str(bitrate * 1000),
                    '-o', str(video_file),
                    '--inline',
                    '--rotation', '0',
                    '--autofocus-mode', 'manual',
                    '--lens-position', str(settings._lens_position),
                    '--ev', str(settings._ev),
                    '--awb', settings._awb,
                    '--brightness', str(settings._brightness),
                    '--contrast', str(settings._contrast),
                    '--saturation', str(settings._saturation),
                    '--sharpness', str(settings._sharpness),
                    '--gain', str(settings._gain),
                    '--timeout', str(duration * 1000),
                ]
                video_proc = subprocess.Popen(video_cmd,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            else:
                # ── Normal: rpicam-vid --codec libav mit eingebautem Audio ──
                # Ein einziger Prozess muxed Video+Audio in die gleiche Timeline.
                # Kein Sync-Offset, kein ffmpeg-Merge, kein TXT-Sidecar nötig.
                video_cmd = [
                    'rpicam-vid', '-n',
                    '--width', str(w), '--height', str(h),
                    '--framerate', str(fps),
                    '--bitrate', str(bitrate * 1000),
                    '--rotation', '0',
                    '--autofocus-mode', 'manual',
                    '--lens-position', str(settings._lens_position),
                    '--ev', str(settings._ev),
                    '--awb', settings._awb,
                    '--brightness', str(settings._brightness),
                    '--contrast', str(settings._contrast),
                    '--saturation', str(settings._saturation),
                    '--sharpness', str(settings._sharpness),
                    '--gain', str(settings._gain),
                    '--codec', 'libav',
                    '--libav-format', 'mp4',
                    '--libav-audio',
                    '--audio-codec', 'aac',
                    '--audio-samplerate', '48000',
                    '--audio-source', 'alsa',
                    '--audio-device', 'plughw:0,0',
                    '--timeout', str(duration * 1000),
                    '-o', str(video_file),
                ]
                video_proc = subprocess.Popen(video_cmd,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            logger.info('Recording [%s] %ds %s %dfps → %s | Load: %.2f %.2f %.2f',
                        triggered_by, duration, resolution, fps, video_file.name,
                        *os.getloadavg())

            with _lock:
                state.recording_process = video_proc

            # ── Warten bis rpicam-vid sich nach --timeout selbst beendet ──
            # Kill nur als Fallback wenn Prozess hängt (timeout + 10s Puffer).
            fallback_timeout = duration + 10
            deadline = time.monotonic() + fallback_timeout
            while time.monotonic() < deadline:
                if video_proc.poll() is not None:
                    break
                time.sleep(0.5)

            # ── Fallback-Kill falls Prozess hängt ───────────────────────────
            if video_proc.poll() is None:
                try:
                    _kill_process_group(video_proc, timeout=5)
                    logger.warning('rpicam-vid musste per Kill beendet werden')
                except Exception as e:
                    logger.warning('rpicam-vid Kill fehlgeschlagen: %s', e)

            with _lock:
                state.recording_process = None

            # stderr von rpicam-vid auslesen (nicht-blockierend nach Kill)
            try:
                stderr_out = video_proc.stderr.read().decode('utf-8', errors='replace').strip()
            except Exception:
                stderr_out = ''
            if stderr_out:
                for line in stderr_out.splitlines():
                    if 'ERROR' in line or 'error' in line.lower():
                        logger.error('rpicam-vid: %s', line)
                    else:
                        logger.debug('rpicam-vid: %s', line)

            # Kurze Pause: Dateisystem-Flush sicherstellen (wie in alten Skripten +1s)
            time.sleep(2)

            if video_file.exists():
                rec_info = {
                    'video':     str(video_file),
                    'audio':     None,  # Bei libav-MP4 bereits eingebettet
                    'timestamp': ts,
                }
                with _lock:
                    state.recording_file = rec_info
                logger.info('Recording abgeschlossen: %s | Load: %.2f %.2f %.2f',
                            video_file.name, *os.getloadavg())

                # Konvertierung (Zeitlupe) und Transfer laufen im Nachbearbeitungs-Thread.
                # Die Kamera ist ab hier frei – das finally unten startet die Detection
                # sofort wieder, statt auf ffmpeg/rsync zu warten.
                _post_queue.put((video_file, fps, slowmotion))
                queued = True

                return True, rec_info

            logger.error('Video-Datei nicht erstellt: %s', video_file)
            err_msg = f'Video-Datei nicht erstellt ({video_file.name})'
            if stderr_out:
                first_error = next((l for l in stderr_out.splitlines() if 'ERROR' in l), stderr_out.splitlines()[-1] if stderr_out else '')
                err_msg = first_error.strip() or err_msg
            with _lock:
                state.last_error = err_msg
            return False, err_msg

        except Exception as exc:
            logger.error('Recording fehlgeschlagen: %s', exc)
            with _lock:
                state.last_error = str(exc)
            return False, str(exc)

        finally:
            if video_file is not None and not queued:
                _release_busy(video_file)
            with _lock:
                state.recording_running    = False
                state.recording_process    = None
                state.recording_started_at = 0.0
                state.recording_duration_s = 0
                if triggered_by == 'detection':
                    state.birds_recorded += 1
                _det_mode = state.detection_mode
            # Detection neu starten – detection_mode wiederherstellen falls aktiv
            if _det_mode:
                CameraManager.start_detection_mode()
            else:
                CameraManager.start_detection()

    @staticmethod
    def record_audio(duration: int = 60):
        """Startet eine reine Audio-Aufnahme (kein Video) mit ffmpeg (oder arecord als Fallback).
        Nutzt 48kHz und ggf. Audio-Verarbeitung.
        Gibt (ok, wav_path_or_error) zurück."""
        with _lock:
            if state.recording_running:
                return False, 'Video-Recording läuft bereits'
            if state.audio_running:
                return False, 'Audio-Aufnahme läuft bereits'
            state.audio_running    = True
            state.audio_started_at = time.monotonic()
            state.audio_duration_s = duration

        wav = None
        queued = False
        try:
            recording_dir = Path(config.VIDEO_BASE_DIR)
            recording_dir.mkdir(parents=True, exist_ok=True)

            # Dateiname: Jahr_KW_Tag_Uhrzeit_audio_Xmin.wav
            ts  = datetime.now().strftime('%Y_%V_%d_%H%M%S')
            dur_min = max(1, round(duration / 60))
            wav = recording_dir / f'{ts}_audio_{dur_min}min.wav'
            _mark_busy(wav)

            # Mic-Eingangspegel sicherstellen
            try:
                subprocess.run(
                    ['amixer', '-c', '0', 'sset', 'Mic', '50%'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            except Exception:
                pass

            # ── Versuche ffmpeg zuerst (mit 48kHz und einfachen Filtern) ──
            use_ffmpeg = True
            ffmpeg_available = shutil.which('ffmpeg') is not None
            
            if not ffmpeg_available:
                logger.warning('ffmpeg nicht verfügbar – verwende arecord stattdessen')
                use_ffmpeg = False

            if use_ffmpeg:
                logger.info('Audio-Recording mit ffmpeg gestartet: %ds → %s (48kHz)', duration, wav.name)
                audio_cmd = [
                    'ffmpeg',
                    '-hide_banner',
                    '-loglevel', 'warning',
                    '-f', 'alsa',
                    '-i', 'default',
                    '-t', str(duration),
                    '-af', 'highpass=f=80,volume=1.5',  # Einfache, robuste Filter
                    '-acodec', 'pcm_s16le',
                    '-ar', '48000',  # 48kHz
                    '-ac', '1',
                    '-y',
                    str(wav),
                ]
                logger.debug('ffmpeg cmd: %s', ' '.join(audio_cmd))
                
                audio_proc = subprocess.Popen(
                    audio_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
            else:
                # Fallback: arecord mit 48kHz
                logger.info('Audio-Recording mit arecord gestartet: %ds → %s (48kHz)', duration, wav.name)
                audio_cmd = [
                    'arecord',
                    '-f', 'S16_LE',
                    '-r', '48000',  # 48kHz (nicht default 44100)
                    '-c', '1',
                    '-t', 'wav',
                    '-d', str(duration),
                    str(wav),
                ]
                logger.debug('arecord cmd: %s', ' '.join(audio_cmd))
                
                audio_proc = subprocess.Popen(
                    audio_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

            with _lock:
                state.recording_process = audio_proc

            # Dauer abwarten (mit Fehler-Überwachung)
            stderr_lines = []
            deadline = time.monotonic() + duration
            while time.monotonic() < deadline:
                rc = audio_proc.poll()
                if rc is not None:
                    # Prozess beendet (Fehler oder OK)
                    logger.warning('%s beendet mit rc=%d', 'ffmpeg' if use_ffmpeg else 'arecord', rc)
                    try:
                        remaining = audio_proc.stderr.read()
                        if remaining:
                            stderr_lines.append(remaining)
                    except Exception:
                        pass
                    break
                time.sleep(1)

            # Prozess explicit stoppen (falls noch läuft)
            if audio_proc.poll() is None:
                try:
                    _kill_process_group(audio_proc, timeout=5)
                    logger.info('Audio-Prozess beendet')
                except Exception as e:
                    logger.warning('Audio-Prozess Kill fehlgeschlagen: %s', e)

            with _lock:
                state.recording_process = None

            # stderr vollständig auslesen
            try:
                stderr_remaining = audio_proc.stderr.read()
                if stderr_remaining:
                    stderr_lines.append(stderr_remaining)
            except Exception:
                pass
            
            stderr_out = ''.join(stderr_lines).strip()
            if stderr_out:
                for line in stderr_out.splitlines()[:5]:  # Nur erste 5 Zeilen loggen
                    if 'error' in line.lower():
                        logger.error('Audio-Prozess: %s', line)
                    else:
                        logger.debug('Audio-Prozess: %s', line)

            time.sleep(1)  # Dateisystem-Flush

            # Überprüfe ob Datei erstellt wurde
            if wav.exists() and wav.stat().st_size > 4096:
                file_size_mb = wav.stat().st_size / 1048576
                logger.info('Audio-Aufnahme erfolgreich: %s (%.2f MB)', wav.name, file_size_mb)
                _post_queue.put((wav, 0, False))
                queued = True
                return True, str(wav)

            # Datei nicht erstellt oder zu klein
            err = f'Audio-Datei nicht erstellt oder zu klein: {wav.name}'
            if stderr_out:
                # Fehler aus stderr
                error_lines = [l for l in stderr_out.splitlines() if 'error' in l.lower()]
                if error_lines:
                    err = error_lines[0]
                elif stderr_out.splitlines():
                    err = stderr_out.splitlines()[-1]
            
            logger.error(err)
            with _lock:
                state.last_error = err
            return False, err

        except Exception as exc:
            err = f'Audio-Aufnahme Fehler: {exc}'
            logger.error(err)
            with _lock:
                state.last_error = err
            return False, err

        finally:
            if wav is not None and not queued:
                _release_busy(wav)
            with _lock:
                state.audio_running    = False
                state.audio_started_at = 0.0
                state.audio_duration_s = 0
                state.recording_process = None

    @staticmethod
    def post_process(path: 'Path', fps: int = 30, slowmotion: bool = False) -> None:
        """Nachbearbeitung einer fertigen Aufnahme: Zeitlupe konvertieren, dann übertragen.
        Wird vom Nachbearbeitungs-Thread aufgerufen, nie aus record() heraus."""
        try:
            if slowmotion:
                # Zeitlupe h264 → mehrere MP4-Playback-Versionen per ffmpeg
                ok, results = CameraManager._convert_one(path, recording_fps=fps, slowmotion=True)
                if ok:
                    logger.info('Slowmo-Konvertierung: %d Datei(en)', len(results))
                    for mp4 in results:
                        CameraManager.transfer_all(mp4)
                else:
                    logger.warning('Konvertierung fehlgeschlagen: %s', results[0] if results else '?')
                    with _lock:
                        state.last_error = f'Konvertierung: {results[0] if results else "Fehler"}'
            else:
                # Normal (libav-MP4) und Audio (WAV): fertig, direkt übertragen
                CameraManager.transfer_all(str(path))
        finally:
            _release_busy(path)
            invalidate_media_scan()

    @staticmethod
    def _find_latest_h264() -> 'Path | None':
        """Findet die neueste h264-Datei in VIDEO_BASE_DIR (Fallback nach Neustart)."""
        base = Path(config.VIDEO_BASE_DIR)
        if not base.exists():
            return None
        files = sorted((f for f in base.rglob('*.h264') if not _is_busy(f)),
                       key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0] if files else None

    @staticmethod
    def _run_ffmpeg_convert(h264: 'Path', mp4: 'Path', input_fps: int,
                            wav: 'Path | None' = None,
                            audio_delay_s: float = 0.0) -> 'tuple[bool, str]':
        """Hilfsfunktion: Konvertiert h264 → mp4 mit angegebener Input-fps.
        audio_delay_s: Kamera-Init-Offset in Sekunden (aus TXT-Sidecar).
                       Positiver Wert → Audio um diesen Betrag nach hinten schieben
                       (arecord lief vor dem ersten Video-Frame).
        Gibt (ok, mp4_path_or_error) zurück."""
        audio_valid = wav is not None and wav.exists() and wav.stat().st_size > 4096
        # -f h264 erzwingt den Raw-H264-Demuxer; -r überschreibt VUI-Framerate
        # (rpicam-vid/libcamera auf Pi5 kodiert VUI manchmal mit doppelter fps)
        cmd = ['ffmpeg', '-y', '-fflags', '+genpts',
               '-f', 'h264', '-r', str(input_fps), '-i', str(h264)]
        if audio_valid:
            # -itsoffset VOR -i audio: verschiebt Audio-Stream um audio_delay_s
            # nach hinten → kompensiert Kamera-Init-Zeit
            # Nur setzen wenn messbarer Offset vorhanden (>10ms)
            if audio_delay_s > 0.01:
                cmd += ['-itsoffset', f'{audio_delay_s:.3f}']
            cmd += ['-i', str(wav),
                    '-c:v', 'copy', '-c:a', 'aac',
                    # dynaudnorm statt loudnorm: kein interner Lookahead-Delay
                    # f=150: Rahmengröße 150 Frames, g=15: Gauss-Glättung
                    '-af', 'volume=2.0,dynaudnorm=f=150:g=15',
                    '-movflags', '+faststart']
        else:
            cmd += ['-c:v', 'copy', '-movflags', '+faststart']
        cmd.append(str(mp4))
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        if result.returncode == 0 and mp4.exists():
            return True, str(mp4)
        err = result.stderr.decode(errors='replace')[:500]
        return False, err

    @staticmethod
    def _convert_one(h264: 'Path', recording_fps: int = 30, slowmotion: bool = False) -> tuple:
        """Konvertiert eine einzelne h264 → mp4. Gibt (ok, [mp4_paths] | [error_str]) zurück.
        Nutzt -c:v copy + -fflags +genpts (schnell, kein Re-Encoding, kein Qualitätsverlust).
        recording_fps: tatsächliche Aufnahme-Framerate (für Zeitstempel-Berechnung)
        slowmotion:    True → mehrere MP4-Versionen mit verschiedenen Playback-fps erstellen
                              Namensschema: {stem}_pb{playback}fps.mp4 und {stem}.mp4 (Original)
        Es läuft immer nur eine Konvertierung gleichzeitig (_convert_lock).
        """
        with _convert_lock:
            return CameraManager._convert_one_locked(h264, recording_fps, slowmotion)

    @staticmethod
    def _convert_one_locked(h264: 'Path', recording_fps: int, slowmotion: bool) -> tuple:
        try:
            wav = h264.with_suffix('.wav')

            # TXT-Sidecar lesen (fps + audio_delay_s)
            _txt = h264.with_suffix('.txt')
            _sidecar_fps: int | None = None
            _audio_delay_s: float = 0.0
            if _txt.exists():
                try:
                    _sidecar = dict(
                        line.split('=', 1)
                        for line in _txt.read_text().splitlines()
                        if '=' in line
                    )
                    _sidecar_fps   = int(_sidecar.get('fps', recording_fps))
                    _audio_delay_s = float(_sidecar.get('audio_delay_s', 0.0))
                    _sm            = _sidecar.get('slowmotion', str(slowmotion)).strip().lower()
                    slowmotion     = _sm in ('true', '1')
                except Exception:
                    pass
            # Sidecar-fps hat Vorrang vor übergebenem recording_fps
            if _sidecar_fps is not None:
                recording_fps = _sidecar_fps
            else:
                # Fallback: fps aus Dateiname parsen (z.B. ...25fps.h264)
                import re as _re
                _m = _re.search(r'_(\d+)fps\.h264$', h264.name)
                if _m:
                    recording_fps = int(_m.group(1))

            if slowmotion:
                # ── Zeitlupe: mehrere Playback-Versionen (kein Audio) ───────
                # Playback-fps-Stufen: 10, 20, 30 + Original-Geschwindigkeit
                # Beispiel 120fps aufgenommen → _pb10fps = 12x langsamer, _pb30fps = 4x
                playback_fps_list = [10, 20, 30, recording_fps]
                logger.info('Slowmo-Konvertierung: %s → %d Playback-Versionen %s',
                            h264.name, len(playback_fps_list), playback_fps_list)
                created = []
                errors  = []
                for pb_fps in playback_fps_list:
                    if pb_fps == recording_fps:
                        # Original-Geschwindigkeit → Standard-Name (kein _pb-Suffix)
                        mp4 = h264.with_suffix('.mp4')
                    else:
                        mp4 = h264.with_name(f'{h264.stem}_pb{pb_fps}fps.mp4')
                    ok, res = CameraManager._run_ffmpeg_convert(h264, mp4, pb_fps, wav=None, audio_delay_s=0.0)
                    if ok:
                        logger.info('  ✓ %s (%.1f MB)', mp4.name, mp4.stat().st_size / 1048576)
                        created.append(res)
                    else:
                        logger.error('  ✗ Fehler bei pb%dfps: %s', pb_fps, res[:200])
                        errors.append(res)
                if created:
                    return True, created
                return False, [errors[0] if errors else 'Alle Konvertierungen fehlgeschlagen']
            else:
                # ── Normal: einzelne MP4, fps bereits im h264-Dateinamen ───
                mp4 = h264.with_suffix('.mp4')
                logger.info('Konvertierung: %s%s → %s',
                            h264.name, ' (+Audio)' if wav.exists() else '', mp4.name)
                ok, res = CameraManager._run_ffmpeg_convert(
                    h264, mp4, recording_fps, wav=wav, audio_delay_s=_audio_delay_s)
                if ok:
                    logger.info('Konvertierung abgeschlossen: %s (%.1f MB)',
                                mp4.name, Path(mp4).stat().st_size / 1048576)
                    return True, [res]
                logger.error('ffmpeg Fehler: %s', res)
                return False, [res]
        except Exception as exc:
            logger.error('Konvertierung fehlgeschlagen: %s', exc)
            return False, [str(exc)]

    @staticmethod
    def convert_all_pending() -> tuple:
        """Konvertiert alle h264-Dateien die noch kein mp4 haben.
        Dateien, die gerade aufgenommen werden oder auf Nachbearbeitung warten, bleiben
        unberührt. Gibt (converted_count, error_list) zurück."""
        with _sweep_lock:
            return CameraManager._convert_all_pending_locked()

    @staticmethod
    def _convert_all_pending_locked() -> tuple:
        base = Path(config.VIDEO_BASE_DIR)
        h264_files = sorted(base.rglob('*.h264'), key=lambda f: f.stat().st_mtime) if base.exists() else []
        pending = [f for f in h264_files
                   if not f.with_suffix('.mp4').exists() and not _is_busy(f)]
        if not pending:
            return 0, []
        converted = 0
        errors = []
        for h264 in pending:
            ok, results = CameraManager._convert_one(h264)
            if ok:
                converted += 1
                for mp4 in results:
                    CameraManager.transfer_all(mp4)
            else:
                errors.append(f'{h264.name}: {results[0] if results else "Fehler"}')
        return converted, errors

    # Legacy-kompatibler Wrapper
    @staticmethod
    def convert() -> tuple:
        with _lock:
            rec = state.recording_file
        if rec:
            h264 = Path(rec.get('video', ''))
        else:
            h264 = CameraManager._find_latest_h264()
        if not h264 or not h264.exists():
            # Fallback: alle ausstehenden konvertieren
            count, errs = CameraManager.convert_all_pending()
            if count:
                return True, f'{count} Dateien konvertiert'
            return False, errs[0] if errs else 'Keine h264-Dateien vorhanden'
        ok, results = CameraManager._convert_one(h264)
        if ok:
            with _lock:
                if state.recording_file:
                    state.recording_file['mp4'] = results[0]
        return ok, results[0] if results else ''

    @staticmethod
    def transfer_all(mp4_path: str) -> list:
        """Überträgt MP4 per rsync an alle konfigurierten Sync-Ziele.
        Gibt Liste von (target_name, ok, msg) zurück."""
        targets = _get_active_targets()
        if not targets:
            return []
        results = []
        for t in targets:
            dest = f"{t['user']}@{t['host']}:{t['path']}"
            key_file = f"/config/sync_key_{t['id']}"
            # Feste Optionen ohne Nutzereingaben → shlex.join ist hier sicher;
            # '--' trennt Optionen von Quelle/Ziel (Ziel ist bereits validiert)
            ssh_cmd = shlex.join(['ssh', '-o', 'LogLevel=ERROR', *ssh_options(key_file)])
            cmd = ['rsync', '-az', '-e', ssh_cmd, '--', mp4_path, dest]
            logger.info('Transfer [%s]: %s → %s', t['name'], Path(mp4_path).name, dest)
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=600)
                ok = r.returncode == 0
                msg = dest if ok else r.stderr.decode(errors='replace')[:200]
                if ok:
                    logger.info('Transfer abgeschlossen [%s]: %s', t['name'], Path(mp4_path).name)
                else:
                    logger.error('Transfer fehlgeschlagen [%s]: %s', t['name'], msg)
                results.append((t['name'], ok, msg))
            except subprocess.TimeoutExpired:
                results.append((t['name'], False, 'Timeout'))
            except Exception as exc:
                results.append((t['name'], False, str(exc)))
        return results

    @staticmethod
    def list_recordings() -> list:
        base = Path(config.VIDEO_BASE_DIR)
        listed = [(f, st) for f, st in _scan_media() if _is_listed(f)]
        listed.sort(key=lambda x: x[1].st_mtime, reverse=True)
        result = []
        for f, st in listed[:100]:
            try:
                rel = str(f.relative_to(base))
            except ValueError:
                rel = f.name
            created = datetime.fromtimestamp(st.st_mtime)
            result.append({
                'name':     f.name,
                'rel_path': rel,
                'size_mb':  round(st.st_size / 1_048_576, 1),
                'created':  created.strftime('%Y-%m-%d %H:%M:%S'),
                'date':     created.strftime('%Y-%m-%d'),
                'type':     'video' if f.suffix == '.mp4' else 'audio',
            })
        return result



# ── Speicher-Aufräumung ───────────────────────────────────────────────────────

def free_disk_space() -> int:
    """Löscht die ältesten Aufnahmen, bis wieder config.MIN_FREE_GB frei sind.
    MIN_FREE_GB = 0 (Standard) schaltet die Aufräumung ab. Gibt die Anzahl gelöschter
    Dateien zurück."""
    if config.MIN_FREE_GB <= 0:
        return 0
    base = Path(config.VIDEO_BASE_DIR)
    if not base.exists():
        return 0
    need = config.MIN_FREE_GB * 1_073_741_824
    if shutil.disk_usage(base).free >= need:
        return 0

    def _mtime(f: Path) -> float:
        try:
            return f.stat().st_mtime
        except OSError:
            return 0.0

    candidates = sorted(
        (f for f in base.rglob('*')
         if f.suffix in _MEDIA_SUFFIXES and f.is_file() and not _is_busy(f)),
        key=_mtime)
    deleted = 0
    for f in candidates:
        if shutil.disk_usage(base).free >= need:
            break
        try:
            f.unlink()
            deleted += 1
            invalidate_media_scan()
            logger.warning('Speicher-Aufräumung: %s gelöscht', f.name)
        except OSError as exc:
            logger.error('Speicher-Aufräumung: %s nicht löschbar: %s', f.name, exc)
    if shutil.disk_usage(base).free < need:
        logger.error('Speicher-Aufräumung: weiterhin weniger als %.1f GB frei', config.MIN_FREE_GB)
    return deleted


# ── Nachbearbeitungs-Thread ───────────────────────────────────────────────────

def _post_process_worker():
    """Hintergrund-Thread: konvertiert und überträgt fertige Aufnahmen nacheinander."""
    while True:
        path, fps, slowmotion = _post_queue.get()
        try:
            CameraManager.post_process(path, fps, slowmotion)
        except Exception as exc:
            logger.error('Nachbearbeitung fehlgeschlagen (%s): %s', Path(path).name, exc)
        finally:
            _post_queue.task_done()


# ── Auto-Convert Watcher ──────────────────────────────────────────────────────

def _auto_convert_watcher():
    """Hintergrund-Thread: prüft alle 3 Minuten auf unconvertierte H264-Dateien
    und räumt bei knappem Speicher alte Aufnahmen weg."""
    time.sleep(30)  # kurzer Start-Delay
    while True:
        try:
            free_disk_space()
        except Exception as exc:
            logger.error('Speicher-Aufräumung Fehler: %s', exc)
        try:
            count, errors = CameraManager.convert_all_pending()
            if count:
                logger.info('Auto-Convert: %d Datei(en) konvertiert', count)
            if errors:
                logger.warning('Auto-Convert Fehler: %s', '; '.join(errors[:3]))
        except Exception as exc:
            logger.error('Auto-Convert Watcher Fehler: %s', exc)
        time.sleep(180)


# ── Detection-Watchdog ────────────────────────────────────────────────────────

def detection_watchdog():
    """Überwacht Detection-Prozess. Bei Detection-Modus + Vogel (rc=0): Aufnahme starten."""
    time.sleep(10)
    consecutive_failures = 0   # Zählt aufeinander folgende rc=1 Exits (V4L2-Fehler)
    while True:
        time.sleep(5)
        with _lock:
            if not state.detection_running or state.detection_process is None:
                continue
            proc = state.detection_process
            rc = proc.poll()
            if rc is None:
                continue  # Prozess läuft noch
            logger.warning('Detection-Prozess beendet (rc=%d)', rc)
            state.detection_running = False
            state.detection_process = None
            should_record = state.detection_mode and rc == 0
            should_restart = not state.recording_running and (not should_record)

        if rc == 0:
            consecutive_failures = 0   # Sauber beendet (Vogel erkannt)
        else:
            consecutive_failures += 1

        if should_record:
            consecutive_failures = 0
            # Vogel erkannt im Detection-Modus → Aufnahme aus gespeicherten Einstellungen starten
            rec_cfg = _load_rec_settings()
            profile_name = rec_cfg.get('profile', 'normal_hd')
            duration     = rec_cfg.get('duration', 15)
            profile      = RECORDING_PROFILES.get(profile_name, RECORDING_PROFILES['normal_hd'])
            logger.info('Detection-Modus: Vogel erkannt – starte Aufnahme (Profil: %s)', profile_name)
            threading.Thread(
                target=CameraManager.record,
                kwargs={
                    'duration':    duration,
                    'resolution':  profile['resolution'],
                    'fps':         profile['fps'],
                    'bitrate':     profile['bitrate'],
                    'slowmotion':  profile['slowmotion'],
                    'triggered_by': 'detection',
                },
                daemon=True,
                name='det-rec',
            ).start()
        elif should_restart:
            if consecutive_failures >= 3:
                consecutive_failures = 0
                # imx708-Reset nur wenn KEIN Hailo-Script (rpicam-hello braucht keinen
                # sysfs-Reset – Fehler dort = npicam-init-Problem, kein Sensor-Stuck).
                if settings._active_engine == 'hailo':
                    logger.warning(
                        'Hailo rpicam-hello Startfehler × 3 – warte 15s vor erneutem Versuch')
                    time.sleep(15)
                else:
                    logger.warning('Kamera-Reset nach 3 aufeinander folgenden Fehlern …')
                    reset_ok = _camera_reset()
                    if not reset_ok:
                        logger.warning('Kamera-Hardware-Fehler: Retry in 5 Minuten …')
                        time.sleep(300)
                    else:
                        time.sleep(3)
            else:
                time.sleep(2)
            CameraManager.start_detection()
