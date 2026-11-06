"""Gemeinsamer Laufzeit-Zustand (Lock + DaemonState)."""
import subprocess
import threading
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Globaler Zustand
# ---------------------------------------------------------------------------
_lock = threading.RLock()   # Reentrant – gleicher Thread darf mehrfach acquiren


class DaemonState:
    detection_running:     bool  = False
    detection_mode:        bool  = False   # True = Detection-Modus aktiv (blockiert manuelle Aufnahme)
    recording_running:     bool  = False
    recording_started_at:  float = 0.0     # time.monotonic() beim Start der Aufnahme
    recording_duration_s:  int   = 0       # geplante Aufnahmedauer in Sekunden
    audio_running:         bool  = False   # True = reine Audio-Aufnahme läuft
    audio_started_at:      float = 0.0
    audio_duration_s:      int   = 0
    detection_process:     subprocess.Popen = None
    recording_process:     subprocess.Popen = None
    last_error:            str  = None
    recording_file:        dict = None
    birds_recorded:        int  = 0        # Zähler Vogel-getriggerte Aufnahmen in dieser Session
    started_at:            str  = datetime.now(timezone.utc).isoformat()
    camera_hw_error:       bool  = False   # True = IMX708-Sensor hardware-stuck, Neustart nötig


state = DaemonState()
