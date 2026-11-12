"""Prometheus-Metriken (/metrics) im Textformat – ohne zusätzliche Abhängigkeit.

Gedacht für einen Prometheus im Heimnetz, der den Pi von außen abfragt. Auf dem Pi
selbst läuft dafür nichts weiter: Eine Abfrage liest nur Werte, die der Daemon ohnehin
hat (Zustand, gecachter Verzeichnis-Scan, Hailo- und Powerbank-Cache), und startet
keine Prozesse.

Aktiv nur, wenn PI_DAEMON_METRICS_TOKEN gesetzt ist. Details: MONITORING.md.
"""
import os
import time
from pathlib import Path

import psutil

from . import camera, config, hailo, powerbank, settings
from .runtime import _lock, state

_PREFIX = 'vogelkamera_'
_cpu_prev = None   # (busy, total) der letzten Abfrage – für die CPU-Auslastung dazwischen


def _cpu_usage_ratio():
    """CPU-Auslastung (0–1) seit der letzten /metrics-Abfrage.
    Eigene Messung, damit sich Web-GUI und Prometheus nicht gegenseitig verfälschen."""
    global _cpu_prev
    t = psutil.cpu_times()
    total = sum(t)
    busy = total - t.idle - getattr(t, 'iowait', 0.0)
    prev, _cpu_prev = _cpu_prev, (busy, total)
    if prev is None or total <= prev[1]:
        return None
    return max(0.0, min(1.0, (busy - prev[0]) / (total - prev[1])))


def _escape(value) -> str:
    return str(value).replace('\\', r'\\').replace('"', r'\"').replace('\n', r'\n')


class _Writer:
    def __init__(self):
        self.lines = []
        self._seen = set()

    def add(self, name, value, help_text, kind='gauge', labels=None):
        """Fügt einen Messwert hinzu. None (Wert unbekannt) wird ausgelassen."""
        if value is None:
            return
        name = _PREFIX + name
        if name not in self._seen:
            self._seen.add(name)
            self.lines.append(f'# HELP {name} {help_text}')
            self.lines.append(f'# TYPE {name} {kind}')
        label_str = ''
        if labels:
            label_str = '{' + ','.join(f'{k}="{_escape(v)}"' for k, v in labels.items()) + '}'
        if isinstance(value, bool):
            value = int(value)
        self.lines.append(f'{name}{label_str} {float(value):g}' if isinstance(value, float)
                          else f'{name}{label_str} {value}')

    def render(self) -> str:
        return '\n'.join(self.lines) + '\n'


def render() -> str:
    w = _Writer()
    w.add('info', 1, 'Version des pi-daemon', labels={'version': config.APP_VERSION})

    # ── Kamera und Erkennung ─────────────────────────────────────────────
    with _lock:
        snap = {
            'detection_running': state.detection_running,
            'detection_mode':    state.detection_mode,
            'recording_running': state.recording_running,
            'audio_running':     state.audio_running,
            'camera_hw_error':   state.camera_hw_error,
            'birds_recorded':    state.birds_recorded,
            'has_error':         bool(state.last_error),
        }
    w.add('detection_running', snap['detection_running'], 'Detection-Prozess laeuft (1/0)')
    w.add('detection_mode', snap['detection_mode'], 'Detection-Modus (Automatik) aktiv (1/0)')
    w.add('recording_running', snap['recording_running'], 'Video-Aufnahme laeuft (1/0)')
    w.add('audio_recording_running', snap['audio_running'], 'Audio-Aufnahme laeuft (1/0)')
    w.add('camera_hardware_error', snap['camera_hw_error'], 'Kamera-Sensor antwortet nicht (1/0)')
    w.add('last_error', snap['has_error'], 'Es steht eine Fehlermeldung im Status (1/0)')
    w.add('triggered_recordings_total', snap['birds_recorded'],
          'Durch Erkennung ausgeloeste Aufnahmen seit Start des Detection-Modus', kind='counter')
    w.add('detection_threshold', float(settings._detection_threshold), 'Eingestellte Confidence-Schwelle (0-1)')

    media = camera.media_summary()
    w.add('recordings_today', media['today'], 'Video-Aufnahmen mit heutigem Datum')
    w.add('pending_conversions', media['pending'], 'H264-Dateien ohne MP4')
    w.add('postprocess_queue_length', camera._post_queue.qsize(),
          'Aufnahmen, die auf Konvertierung/Transfer warten')

    # ── System ───────────────────────────────────────────────────────────
    try:
        w.add('cpu_usage_ratio', _cpu_usage_ratio(), 'CPU-Auslastung seit der letzten Abfrage (0-1)')
        load = os.getloadavg()
        for window, value in zip(('1m', '5m', '15m'), load):
            w.add('load_average', round(value, 2), 'Systemlast', labels={'window': window})
        mem = psutil.virtual_memory()
        w.add('memory_used_bytes', mem.used, 'Belegter Arbeitsspeicher')
        w.add('memory_total_bytes', mem.total, 'Arbeitsspeicher gesamt')
        base = config.VIDEO_BASE_DIR if Path(config.VIDEO_BASE_DIR).exists() else '/'
        disk = psutil.disk_usage(base)
        w.add('disk_free_bytes', disk.free, 'Freier Platz im Video-Verzeichnis')
        w.add('disk_total_bytes', disk.total, 'Groesse des Dateisystems mit dem Video-Verzeichnis')
        w.add('daemon_memory_bytes', psutil.Process().memory_info().rss, 'Arbeitsspeicher des pi-daemon (RSS)')
        net = psutil.net_io_counters()
        w.add('network_receive_bytes_total', net.bytes_recv, 'Empfangene Bytes seit Boot', kind='counter')
        w.add('network_transmit_bytes_total', net.bytes_sent, 'Gesendete Bytes seit Boot', kind='counter')
        w.add('boot_time_seconds', int(psutil.boot_time()), 'Zeitpunkt des letzten Boots (Unix-Zeit)')
    except Exception:
        pass   # einzelne Systemwerte duerfen fehlen, der Rest wird trotzdem geliefert
    try:
        raw = Path('/sys/class/thermal/thermal_zone0/temp').read_text().strip()
        w.add('cpu_temperature_celsius', round(int(raw) / 1000.0, 1), 'CPU-Temperatur')
    except Exception:
        pass

    # ── Hailo-NPU (nur gecachte Werte – nie ein Subprozess im Request) ────
    with hailo._hailo_temp_bg_lock:
        npu = dict(hailo._hailo_temp_bg)
    w.add('npu_temperature_celsius', npu.get('npu_temp_c'), 'Temperatur des Hailo-Chips')
    if npu.get('nn_clock_mhz') is not None:
        w.add('npu_clock_hertz', npu['nn_clock_mhz'] * 1_000_000, 'Takt des Hailo-NN-Kerns')
    # Achtung: throttle_active heißt nur, dass die Schutzfunktion eingeschaltet ist. Ob gerade
    # gedrosselt wird, sagt allein throttle_level (-1 = nein).
    w.add('npu_throttle_enabled', npu.get('throttle_active'), 'Temperatur-Schutz des Hailo-Chips eingeschaltet (1/0)')
    w.add('npu_throttle_level', npu.get('throttle_level'), 'Hailo-Drosselstufe: -1 = keine Drosselung, ab 0 wird gedrosselt')

    # ── Powerbank ────────────────────────────────────────────────────────
    pb = powerbank.get_status()
    if pb:
        w.add('powerbank_reachable', pb.get('ok') is not False and 'battery_percent' in pb,
              'Letzte Bluetooth-Abfrage der Powerbank erfolgreich (1/0)')
        w.add('powerbank_battery_percent', pb.get('battery_percent'), 'Akkustand der Powerbank')
        w.add('powerbank_input_watts', pb.get('total_input_w'), 'Ladeleistung der Powerbank')
        w.add('powerbank_output_watts', pb.get('total_output_w'), 'Abgegebene Leistung der Powerbank')
        w.add('powerbank_temperature_celsius', pb.get('temperature_c'), 'Temperatur der Powerbank')
        for port in ('usb_c1', 'usb_c2', 'usb_a'):
            info = pb.get(port)
            if isinstance(info, dict) and info.get('power_w') is not None:
                w.add('powerbank_port_watts', float(info['power_w']), 'Leistung je Anschluss',
                      labels={'port': port, 'mode': info.get('mode', '')})

    w.add('scrape_timestamp_seconds', int(time.time()), 'Zeitpunkt dieser Abfrage (Unix-Zeit)')
    return w.render()
