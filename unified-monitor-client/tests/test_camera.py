"""Aufnahme-Ablauf in pi_daemon.camera – ohne Kamera, ffmpeg oder rsync.

Abgesichert wird:
  - Nach der Aufnahme startet die Detection sofort wieder; Konvertierung und Transfer
    laufen erst im Nachbearbeitungs-Thread (vorher blockierten sie die Kamera).
  - Die Profil-Bitrate kommt auch bei normalen (libav-)Aufnahmen bei rpicam-vid an.
  - Auto-Convert fasst keine Datei an, die gerade aufgenommen wird.
  - Speicher-Aufräumung und atomares Schreiben der Einstellungen.
"""
import json
import queue
from collections import namedtuple
from pathlib import Path

import pytest

from pi_daemon import camera, config, storage
from pi_daemon.camera import CameraManager
from pi_daemon.runtime import state


@pytest.fixture
def cam(monkeypatch, video_dir):
    """CameraManager ohne echte Prozesse; protokolliert die Reihenfolge der Schritte."""
    events = []
    popen_cmds = []

    class FakeProc:
        pid = 4242
        returncode = 0

        def __init__(self, cmd):
            # rpicam-vid/ffmpeg „schreiben" ihre Ausgabedatei
            out = cmd[cmd.index('-o') + 1] if '-o' in cmd else cmd[-1]
            Path(out).write_bytes(b'x' * 8192)

            class _Err:
                @staticmethod
                def read():
                    return b''
            self.stderr = _Err()

        def poll(self):
            return 0

    def fake_popen(cmd, **_kw):
        popen_cmds.append(cmd)
        return FakeProc(cmd)

    monkeypatch.setattr(camera.subprocess, 'Popen', fake_popen)
    monkeypatch.setattr(camera.subprocess, 'run', lambda *a, **k: None)   # amixer
    monkeypatch.setattr(camera.time, 'sleep', lambda _s: None)
    monkeypatch.setattr(camera, '_post_queue', queue.Queue())
    monkeypatch.setattr(camera, '_busy_files', set())
    monkeypatch.setattr(CameraManager, '_stop_detection_for_recording',
                        staticmethod(lambda: events.append('detection_stop')))
    monkeypatch.setattr(CameraManager, 'start_detection',
                        staticmethod(lambda: events.append('detection_start') or True))
    monkeypatch.setattr(CameraManager, 'start_detection_mode',
                        staticmethod(lambda: events.append('detection_start') or True))
    monkeypatch.setattr(CameraManager, 'transfer_all',
                        staticmethod(lambda p: events.append(('transfer', Path(p).name)) or []))
    for name in ('recording_running', 'audio_running', 'detection_mode', 'birds_recorded',
                 'last_error', 'recording_file', 'recording_process'):
        monkeypatch.setattr(state, name, getattr(state, name))
    return namedtuple('Cam', 'events popen_cmds video_dir')(events, popen_cmds, video_dir)


def _drain_queue():
    """Arbeitet die Nachbearbeitungs-Queue ab – wie der Hintergrund-Thread."""
    while not camera._post_queue.empty():
        CameraManager.post_process(*camera._post_queue.get())


# ── Aufnahme blockiert die Detection nicht mehr ──────────────────────────────

def test_record_startet_detection_vor_dem_transfer(cam):
    ok, info = CameraManager.record(duration=3)
    assert ok
    video = Path(info['video'])

    # Detection läuft wieder, übertragen wurde noch nichts
    assert cam.events == ['detection_stop', 'detection_start']
    assert camera._post_queue.qsize() == 1
    assert camera._is_busy(video)
    assert state.recording_running is False

    _drain_queue()
    assert cam.events[-1] == ('transfer', video.name)
    assert not camera._is_busy(video)


def test_record_zeitlupe_konvertiert_erst_in_der_nachbearbeitung(cam, monkeypatch):
    converted = []

    def fake_convert(h264, mp4, input_fps, wav=None, audio_delay_s=0.0):
        converted.append(mp4.name)
        mp4.write_bytes(b'x')
        return True, str(mp4)

    monkeypatch.setattr(CameraManager, '_run_ffmpeg_convert', staticmethod(fake_convert))

    ok, info = CameraManager.record(duration=3, resolution='slowmo_fast', fps=120, slowmotion=True)
    assert ok and info['video'].endswith('.h264')
    assert converted == []                      # record() selbst konvertiert nicht
    assert cam.events == ['detection_stop', 'detection_start']

    _drain_queue()
    assert len(converted) == 4                  # 10, 20, 30 fps + Originalgeschwindigkeit
    assert [e for e in cam.events if e[0] == 'transfer'] and len(cam.events) == 2 + 4


def test_record_ohne_datei_gibt_busy_wieder_frei(cam, monkeypatch):
    class DeadProc:
        pid = 1
        stderr = type('E', (), {'read': staticmethod(lambda: b'ERROR: no cameras available')})()

        def poll(self):
            return 1

    monkeypatch.setattr(camera.subprocess, 'Popen', lambda cmd, **k: DeadProc())
    ok, err = CameraManager.record(duration=3)
    assert not ok and 'no cameras' in err
    assert camera._busy_files == set()
    assert camera._post_queue.empty()
    assert cam.events[-1] == 'detection_start'


# ── Bitrate ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('slowmotion', [False, True])
def test_bitrate_erreicht_rpicam_vid(cam, slowmotion):
    CameraManager.record(duration=3, bitrate=12000, slowmotion=slowmotion)
    cmd = cam.popen_cmds[0]
    assert cmd[0] == 'rpicam-vid'
    assert cmd[cmd.index('--bitrate') + 1] == '12000000'


# ── Auto-Convert und laufende Aufnahme ───────────────────────────────────────

def test_convert_all_pending_ueberspringt_belegte_dateien(cam, monkeypatch):
    laufend = cam.video_dir / 'laufend_120fps.h264'
    fertig = cam.video_dir / 'fertig_30fps.h264'
    laufend.write_bytes(b'x')
    fertig.write_bytes(b'x')
    camera._mark_busy(laufend)

    seen = []

    def fake_convert_one(h264, recording_fps=30, slowmotion=False):
        seen.append(h264.name)
        return True, [str(h264.with_suffix('.mp4'))]

    monkeypatch.setattr(CameraManager, '_convert_one', staticmethod(fake_convert_one))
    count, errors = CameraManager.convert_all_pending()
    assert (count, errors) == (1, [])
    assert seen == ['fertig_30fps.h264']
    assert CameraManager._find_latest_h264() == fertig


def test_audio_transfer_laeuft_ueber_die_queue(cam):
    ok, wav = CameraManager.record_audio(duration=3)
    assert ok
    assert not [e for e in cam.events if e[0] == 'transfer']
    assert state.audio_running is False
    _drain_queue()
    assert cam.events[-1] == ('transfer', Path(wav).name)


# ── Speicher-Aufräumung ──────────────────────────────────────────────────────

def _fake_disk(monkeypatch, video_dir, total_gb=10.0, per_file_gb=1.0):
    """Freier Platz = total − Anzahl Mediendateien × per_file_gb."""
    Usage = namedtuple('Usage', 'total used free')

    def disk_usage(_path):
        n = sum(1 for f in video_dir.rglob('*') if f.is_file())
        free = (total_gb - n * per_file_gb) * 1_073_741_824
        return Usage(total_gb * 1_073_741_824, 0, free)

    monkeypatch.setattr(camera.shutil, 'disk_usage', disk_usage)


def test_aufraeumung_ist_standardmaessig_aus(cam, monkeypatch):
    _fake_disk(monkeypatch, cam.video_dir, total_gb=1.0)
    (cam.video_dir / 'a.mp4').write_bytes(b'x')
    assert config.MIN_FREE_GB == 0
    assert camera.free_disk_space() == 0
    assert (cam.video_dir / 'a.mp4').exists()


def test_aufraeumung_loescht_aelteste_zuerst_und_schont_belegte(cam, monkeypatch):
    import os
    names = ['alt.mp4', 'mittel.mp4', 'neu.mp4', 'belegt.h264']
    for i, name in enumerate(names):
        f = cam.video_dir / name
        f.write_bytes(b'x')
        os.utime(f, (1000 + i, 1000 + i))
    os.utime(cam.video_dir / 'belegt.h264', (1, 1))     # die älteste, aber in Arbeit
    (cam.video_dir / 'notiz.txt').write_text('bleibt')
    camera._mark_busy(cam.video_dir / 'belegt.h264')

    # 5 Dateien → 5 GB frei; verlangt werden 7 GB → zwei Aufnahmen müssen weg
    _fake_disk(monkeypatch, cam.video_dir)
    monkeypatch.setattr(config, 'MIN_FREE_GB', 7.0)
    assert camera.free_disk_space() == 2
    assert sorted(f.name for f in cam.video_dir.iterdir()) == ['belegt.h264', 'neu.mp4', 'notiz.txt']


# ── Atomares Schreiben ───────────────────────────────────────────────────────

def test_write_json_atomic_schreibt_und_raeumt_auf(tmp_path):
    target = tmp_path / 'sub' / 'settings.json'
    storage.write_json_atomic(target, {'a': 1})
    storage.write_json_atomic(target, {'a': 2})
    assert json.loads(target.read_text()) == {'a': 2}
    assert [f.name for f in target.parent.iterdir()] == ['settings.json']


def test_write_json_atomic_gleichzeitige_aufrufe(tmp_path):
    """Die Web-GUI kann zwei Speichervorgänge fast gleichzeitig auslösen."""
    import threading
    target = tmp_path / 'settings.json'
    errors = []

    def schreiben(i):
        try:
            for _ in range(50):
                storage.write_json_atomic(target, {'wert': i, 'fuell': 'x' * 2000})
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=schreiben, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert json.loads(target.read_text())['wert'] in range(8)
    assert [f.name for f in tmp_path.iterdir()] == ['settings.json']


def test_write_json_atomic_laesst_alte_datei_bei_fehler_stehen(tmp_path, monkeypatch):
    target = tmp_path / 'settings.json'
    storage.write_json_atomic(target, {'ok': True})

    def kaputt(_src, _dst):
        raise OSError('Platte voll')

    monkeypatch.setattr(storage.os, 'replace', kaputt)
    with pytest.raises(OSError):
        storage.write_json_atomic(target, {'ok': False})
    assert json.loads(target.read_text()) == {'ok': True}
    assert [f.name for f in tmp_path.iterdir()] == ['settings.json']
