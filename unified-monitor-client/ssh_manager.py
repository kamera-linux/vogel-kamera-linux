"""
SSH-Verwaltung mit paramiko und Fehlerbehandlung
"""
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
import paramiko

from config import (
    SSH_KEY, SSH_USER, SSH_HOST, SSH_TIMEOUT,
    SSH_RETRIES, SSH_RETRY_DELAY, LOG_COLORS
)

logger = logging.getLogger(__name__)


class SSHManager:
    """Verwaltet SSH-Verbindungen mit Retry-Logik und Error-Handling"""
    
    def __init__(self):
        self.ssh_key_path = Path(SSH_KEY).expanduser()
        self.user = SSH_USER
        self.host = SSH_HOST
        self.timeout = SSH_TIMEOUT
        self.retries = SSH_RETRIES
        self.retry_delay = SSH_RETRY_DELAY
        self._client = None
        self._transport = None
    
    def _log(self, color: str, message: str):
        """Print farbige Log-Nachricht"""
        sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
        sys.stdout.flush()
    
    def _create_client(self) -> paramiko.SSHClient:
        """Erstellt und konfiguriert SSH-Client"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Prüfe SSH-Key
        if not self.ssh_key_path.exists():
            raise FileNotFoundError(f"SSH-Key nicht gefunden: {self.ssh_key_path}")
        
        return client
    
    def connect(self) -> bool:
        """
        Verbindet mit SSH-Host mit Retry-Logik
        Returns: True wenn erfolgreich, False sonst
        """
        for attempt in range(1, self.retries + 1):
            try:
                if self._client and self._client.get_transport() and self._client.get_transport().is_active():
                    return True
                
                client = self._create_client()
                client.connect(
                    self.host,
                    username=self.user,
                    key_filename=str(self.ssh_key_path),
                    timeout=self.timeout,
                    auth_timeout=self.timeout,
                    allow_agent=False,
                    look_for_keys=False,
                )
                self._client = client
                logger.info(f"SSH-Verbindung zu {self.user}@{self.host} hergestellt")
                return True
                
            except Exception as e:
                logger.warning(f"SSH-Verbindung Fehler (Versuch {attempt}/{self.retries}): {e}")
                if attempt < self.retries:
                    time.sleep(self.retry_delay)
        
        logger.error(f"SSH-Verbindung zu {self.user}@{self.host} fehlgeschlagen nach {self.retries} Versuchen")
        return False
    
    def exec_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Führt Remote-Befehl aus
        Returns: (success, stdout, stderr)
        """
        if not self.connect():
            return False, "", "SSH-Verbindung fehlgeschlagen"
        
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
            
            exit_code = stdout.channel.recv_exit_status()
            return exit_code == 0, out, err
            
        except Exception as e:
            logger.error(f"SSH-Befehl Fehler: {e}")
            self._client = None
            return False, "", str(e)
    
    def exec_command_safe(self, command: str, fallback: str = "") -> str:
        """
        Führt Remote-Befehl aus, gibt Output zurück oder fallback bei Fehler
        """
        success, out, err = self.exec_command(command)
        return out.strip() if success else fallback
    
    def file_exists(self, remote_path: str) -> bool:
        """Prüft ob Remote-Datei existiert"""
        success, _, _ = self.exec_command(f"[ -f '{remote_path}' ] && echo 'OK'")
        return success
    
    def get_file_hash(self, remote_path: str) -> Optional[str]:
        """Bekommt MD5-Hash einer Remote-Datei"""
        success, out, _ = self.exec_command(f"md5sum '{remote_path}' 2>/dev/null | awk '{{print $1}}'")
        return out.strip() if success and out.strip() else None
    
    def read_file(self, remote_path: str, max_lines: Optional[int] = None) -> str:
        """Liest Remote-Datei"""
        if max_lines:
            cmd = f"tail -{max_lines} '{remote_path}' 2>/dev/null"
        else:
            cmd = f"cat '{remote_path}' 2>/dev/null"
        
        return self.exec_command_safe(cmd, fallback="")
    
    def tail_file(self, remote_path: str, lines: int = 10) -> str:
        """Liest letzte N Zeilen einer Remote-Datei"""
        return self.read_file(remote_path, max_lines=lines)
    
    def send_file(self, local_path: Path, remote_path: str) -> bool:
        """Sendet Datei via SCP"""
        if not self.connect():
            return False
        
        try:
            sftp = self._client.open_sftp()
            sftp.put(str(local_path), remote_path)
            sftp.close()
            logger.info(f"Datei übertragen: {local_path} → {remote_path}")
            return True
        except Exception as e:
            logger.error(f"SCP-Fehler: {e}")
            return False
    
    def close(self):
        """Schließt SSH-Verbindung"""
        if self._client:
            try:
                self._client.close()
            except:
                pass
            self._client = None
    
    def __del__(self):
        self.close()


# Globale Instanz
_ssh_manager: Optional[SSHManager] = None


def get_ssh_manager() -> SSHManager:
    """Gibt globale SSH-Manager-Instanz"""
    global _ssh_manager
    if _ssh_manager is None:
        _ssh_manager = SSHManager()
    return _ssh_manager
