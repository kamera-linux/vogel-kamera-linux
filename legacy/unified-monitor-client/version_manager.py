"""
Version-Management und Remote-Skript-Synchronisation
"""
import sys
import logging
import hashlib
from pathlib import Path
from typing import Tuple

from config import (
    LOCAL_REPO_DIR, REMOTE_SCRIPT_DIR, SCRIPT_DIR,
    REMOTE_REPO_DIR, LOG_COLORS
)
from ssh_manager import get_ssh_manager

logger = logging.getLogger(__name__)


class VersionManager:
    """Verwaltet Versionen und Remote-Skript-Synchronisation"""
    
    def __init__(self):
        self.ssh = get_ssh_manager()
        self.local_version = self._read_local_version()
        self.remote_version = None
    
    def _log(self, color: str, message: str):
        """Print farbige Log-Nachricht"""
        import sys
        sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
        sys.stdout.flush()
    
    def _read_local_version(self) -> str:
        """Liest lokale Version aus VERSION-Datei"""
        version_file = Path(__file__).parent / 'VERSION'
        if version_file.exists():
            version = version_file.read_text().strip()
            # Entferne führendes 'v' if vorhanden
            return version.lstrip('v')
        return "UNKNOWN"
    
    def get_remote_version(self) -> str:
        """Liest Remote-Version - versucht mehrere Orte"""
        if not self.remote_version:
            # Versuche mehrere Orts-Optionen
            version_files = [
                f'{REMOTE_REPO_DIR}/auto-start-kamera/VERSION',  # Primary
                f'{REMOTE_REPO_DIR}/unified-monitor-client/VERSION',  # Alternative
                f'{REMOTE_REPO_DIR}/VERSION',  # Root Version
            ]
            
            version = "UNKNOWN"
            for version_file in version_files:
                version = self.ssh.exec_command_safe(
                    f"cat '{version_file}' 2>/dev/null | tr -d '[:space:]'",
                    fallback=None
                )
                if version and version != "UNKNOWN":
                    break
            
            self.remote_version = version if version else "UNKNOWN"
        
        return self.remote_version
    
    def compare_versions(self) -> bool:
        """
        Vergleicht Versionen
        Returns: True wenn OK (gleich), False wenn Update nötig
        """
        local = self.local_version
        remote = self.get_remote_version()
        
        self._log('cyan', f"   📌 Lokale Version:  v{local}")
        self._log('cyan', f"   📍 Remote Version:  v{remote}")
        
        if local == remote:
            return True
        
        if remote == "UNKNOWN":
            return False
        
        if self._version_greater_than(local, remote):
            return False
        
        return True
    
    @staticmethod
    def _version_greater_than(v1: str, v2: str) -> bool:
        """Vergleicht zwei Versionen (v1 > v2?)"""
        try:
            parts1 = [int(x) for x in v1.lstrip('v').split('.')]
            parts2 = [int(x) for x in v2.lstrip('v').split('.')]
            
            for p1, p2 in zip(parts1, parts2):
                if p1 > p2:
                    return True
                elif p1 < p2:
                    return False
            
            return len(parts1) > len(parts2)
        except:
            return v1 > v2
    
    def sync_remote_scripts(self) -> bool:
        """
        Synchronisiert Remote-Skripte basierend auf MD5-Hash
        Returns: True wenn erfolgreich oder aktuell
        """
        self._log('cyan', "🔄 Prüfe Remote-Skripte auf Aktualität...")
        
        # Synchronisiere alle wichtigen Remote-Skripte
        # Format: (lokaler_pfad, remote_pfad)
        # - unified-camera-monitor.py: Fallback für manuelle Aufnahme
        # - unified-camera-monitor-auto.py: Vogelerkennung + Auto-Recording
        # - unified-camera-monitor-manual.py: Manuelle Aufnahme (rpicam-vid)
        # - unified-camera-monitor-detect-only.py: YOLO Detection ohne Video
        # - hailo_onnx_hybrid.py: HAILO + ONNX Hybrid Bird Detector (NEU! 28 fps)
        # - monitors.py: Status-Reporting, Log-Tailing, Video-Watching (Hilfsfunktionen)
        # - get_pi_status.sh: System-Status Abruf (CPU, RAM, Disk, Temp, Procs) - WICHTIG!
        scripts_to_sync = [
            (LOCAL_REPO_DIR / 'raspberry-pi-scripts' / 'unified-camera-monitor.py', f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor.py'),
            (LOCAL_REPO_DIR / 'raspberry-pi-scripts' / 'unified-camera-monitor-auto.py', f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor-auto.py'),
            (LOCAL_REPO_DIR / 'raspberry-pi-scripts' / 'unified-camera-monitor-manual.py', f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor-manual.py'),
            (LOCAL_REPO_DIR / 'raspberry-pi-scripts' / 'unified-camera-monitor-detect-only.py', f'{REMOTE_SCRIPT_DIR}/unified-camera-monitor-detect-only.py'),
            (LOCAL_REPO_DIR / 'raspberry-pi-scripts' / 'hailo_onnx_hybrid.py', f'{REMOTE_SCRIPT_DIR}/hailo_onnx_hybrid.py'),
            (Path(__file__).parent / 'monitors.py', f'{REMOTE_SCRIPT_DIR}/monitors.py'),
            (Path(__file__).parent / 'get_pi_status.sh', f'{REMOTE_SCRIPT_DIR}/get_pi_status.sh'),
        ]
        
        scripts_updated = 0
        
        for local_path, remote_path in scripts_to_sync:
            # Lokaler und Remote-Pfad sind jetzt direkt definiert
            script_name = local_path.name
            
            if not local_path.exists():
                self._log('yellow', f"⚠️  Lokale Datei nicht gefunden: {script_name}")
                continue
            
            # Berechne Hashes
            local_hash = self._calculate_md5(local_path)
            remote_hash = self.ssh.get_file_hash(remote_path)
            
            # Vergleiche und synchronisiere
            if remote_hash is None:
                self._log('yellow', f"⚠️  Remote-Datei nicht gefunden (oder nicht erreichbar): {script_name}")
                self._log('yellow', f"   Übertrage trotzdem...")
            elif local_hash == remote_hash:
                self._log('green', f"✅ Aktuell: {script_name}")
                continue
            
            self._log('yellow', f"🔄 Aktualisiere: {script_name}")
            
            # Übertrage Datei
            if self.ssh.send_file(local_path, remote_path):
                self._log('green', f"   ✅ Erfolgreich übertragen")
                scripts_updated += 1
            else:
                self._log('red', f"   ❌ Fehler beim Upload: {script_name}")
                return False
        
        # Synchronisiere auch VERSION-Dateien (NEU in v2.1.2!)
        # Dies stellt sicher, dass Remote-Version aktuell ist
        version_files_to_sync = [
            ('Root VERSION', LOCAL_REPO_DIR / 'VERSION', f'{REMOTE_REPO_DIR}/VERSION'),
            ('Auto-start VERSION', LOCAL_REPO_DIR / 'auto-start-kamera' / 'VERSION', f'{REMOTE_REPO_DIR}/auto-start-kamera/VERSION'),
            ('Unified-Monitor VERSION', Path(__file__).parent / 'VERSION', f'{REMOTE_REPO_DIR}/unified-monitor-client/VERSION'),
            ('Raspberry Pi Scripts VERSION', LOCAL_REPO_DIR / 'raspberry-pi-scripts' / 'VERSION', f'{REMOTE_REPO_DIR}/raspberry-pi-scripts/VERSION'),
        ]
        
        for desc, local_path, remote_path in version_files_to_sync:
            if not local_path.exists():
                continue
            
            local_hash = self._calculate_md5(local_path)
            remote_hash = self.ssh.get_file_hash(remote_path)
            
            if remote_hash is None or local_hash != remote_hash:
                if self.ssh.send_file(local_path, remote_path):
                    scripts_updated += 1
        
        # Invalidiere Version-Cache - wird beim nächsten compare_versions() neu gelesen
        self.remote_version = None
        
        if scripts_updated == 0:
            self._log('green', f"✅ Alle Remote-Skripte sind aktuell")
        else:
            self._log('green', f"✅ {scripts_updated} Datei(en) aktualisiert")
        
        return True
    
    @staticmethod
    def _calculate_md5(file_path: Path) -> str:
        """Berechnet MD5-Hash einer lokalen Datei"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
