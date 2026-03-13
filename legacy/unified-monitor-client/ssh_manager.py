"""
SSH-Verwaltung mit subprocess (OpenSSH) - Key-basierte Authentifizierung
"""
import sys
import time
import logging
import threading
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, Callable

from config import (
    SSH_KEY, SSH_USER, SSH_HOST, SSH_TIMEOUT,
    SSH_RETRIES, SSH_RETRY_DELAY, LOG_COLORS
)

logger = logging.getLogger(__name__)


class SSHManager:
    """Verwaltet SSH-Verbindungen mit subprocess (OpenSSH) und Fehlerbehandlung"""
    
    def __init__(self):
        self.ssh_key_path = Path(SSH_KEY).expanduser()
        self.user = SSH_USER
        self.host = SSH_HOST
        self.timeout = SSH_TIMEOUT
        self.retries = SSH_RETRIES
        self.retry_delay = SSH_RETRY_DELAY
        self._connected = False
    
    def _log(self, color: str, message: str):
        """Print farbige Log-Nachricht"""
        sys.stdout.write(f"{LOG_COLORS.get(color, '')}{message}{LOG_COLORS['reset']}\n")
        sys.stdout.flush()
    
    def connect(self) -> bool:
        """
        Verbindet mit SSH-Host mit Retry-Logik (nutzt OpenSSH über subprocess)
        Returns: True wenn erfolgreich, False sonst
        """
        if self._connected:
            return True
        
        # Pre-populate SSH known_hosts mit Pi (verhindert interaktive Prompts)
        self._add_to_known_hosts()
        
        for attempt in range(1, self.retries + 1):
            try:
                # Einfacher Test: 'echo' via SSH
                success, _, _ = self.exec_command("echo 'SSH_TEST_OK'", timeout=5)
                if success:
                    self._connected = True
                    logger.info(f"SSH-Verbindung zu {self.user}@{self.host} hergestellt")
                    return True
            except Exception as e:
                logger.warning(f"SSH-Verbindung Fehler (Versuch {attempt}/{self.retries}): {e}")
                if attempt < self.retries:
                    time.sleep(self.retry_delay)
        
        logger.error(f"SSH-Verbindung zu {self.user}@{self.host} fehlgeschlagen nach {self.retries} Versuchen")
        self._connected = False
        return False
    
    def _add_to_known_hosts(self) -> bool:
        """Fügt Host-Key zu known_hosts hinzu (non-interactive)"""
        try:
            ssh_keyscan_cmd = f"ssh-keyscan -t ed25519,rsa {self.host} >> ~/.ssh/known_hosts 2>/dev/null"
            subprocess.run(ssh_keyscan_cmd, shell=True, timeout=10)
            return True
        except Exception as e:
            logger.debug(f"Known_hosts Pre-populate: {e}")
            return False
    
    def exec_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Führt Remote-Befehl aus via OpenSSH mit Key-Authentifizierung (KEIN sshpass!)
        Returns: (success, stdout, stderr)
        """
        try:
            ssh_host = f"{self.user}@{self.host}"
            ssh_cmd = [
                "ssh",
                "-i", str(self.ssh_key_path),
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=accept-new",  # Akzeptiert neue Keys automatisch
                "-o", "UserKnownHostsFile=~/.ssh/known_hosts",  # Nutze normale known_hosts
                "-o", "LogLevel=ERROR",  # WICHTIG: Unterdrücke Warnungen auf stderr
                "-o", "PreferredAuthentications=publickey",  # NUR Key-Auth
                ssh_host,
                command
            ]
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Ersetze ungültige UTF-8 bytes statt Exception
                timeout=timeout
            )
            
            return result.returncode == 0, result.stdout, result.stderr
        
        except subprocess.TimeoutExpired:
            logger.error(f"SSH-Befehl Timeout nach {timeout}s")
            return False, "", f"Timeout nach {timeout}s"
        except Exception as e:
            logger.error(f"SSH-Befehl Fehler: {e}")
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
        """Sendet Datei via SCP mit Key-Authentifizierung"""
        try:
            scp_cmd = [
                "scp",
                "-i", str(self.ssh_key_path),
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "UserKnownHostsFile=~/.ssh/known_hosts",
                "-o", "LogLevel=ERROR",  # WICHTIG: Unterdrücke Warnungen
                "-o", "PreferredAuthentications=publickey",  # NUR Key-Auth
                str(local_path),
                f"{self.user}@{self.host}:{remote_path}"
            ]
            
            result = subprocess.run(
                scp_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            if result.returncode == 0:
                logger.info(f"Datei übertragen: {local_path} → {remote_path}")
                return True
            else:
                logger.error(f"SCP-Fehler: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"SCP-Fehler: {e}")
            return False
    
    def close(self):
        """Schließt SSH-Verbindung"""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Prüft ob SSH-Verbindung aktiv ist"""
        return self._connected
    
    def health_check(self) -> bool:
        """
        Führt einfachen Health-Check durch (ping via SSH)
        Returns: True wenn Verbindung aktiv, False sonst
        """
        try:
            success, out, _ = self.exec_command("echo 'HEALTH_CHECK_OK'", timeout=5)
            return success and "HEALTH_CHECK_OK" in out
        except Exception as e:
            logger.warning(f"SSH Health-Check Fehler: {e}")
            return False
    
    def __del__(self):
        self.close()


# Globale Instanz
_ssh_manager: Optional[SSHManager] = None


class SSHHealthChecker:
    """
    Überwacht SSH-Verbindung und führt regelmäßig Health-Checks durch.
    
    Verhindert Timeout-Probleme bei längeren Sessions durch regelmäßige Pings
    und automatische Wiederverbindung bei Fehlern.
    """
    
    def __init__(self, ssh_manager: SSHManager, interval: int = 120, on_reconnect: Optional[Callable] = None):
        """
        Args:
            ssh_manager: SSHManager-Instanz zum Überwachen
            interval: Health-Check Interval in Sekunden (default: 2 Min)
            on_reconnect: Callback-Funktion bei Wiederverbindung (z.B. für Logging)
        """
        self.ssh = ssh_manager
        self.interval = interval
        self.on_reconnect = on_reconnect
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_check_ok = True
        self.check_count = 0
        self.reconnect_count = 0
    
    def start(self) -> threading.Thread:
        """Startet Health-Checker Thread"""
        if self.running:
            logger.warning("SSH Health-Checker läuft schon")
            return self.thread
        
        self.running = True
        self.thread = threading.Thread(target=self._health_check_loop, daemon=True, name="SSHHealthChecker")
        self.thread.start()
        logger.info(f"SSH Health-Checker gestartet (Interval: {self.interval}s)")
        return self.thread
    
    def stop(self):
        """Stoppt Health-Checker Thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("SSH Health-Checker gestoppt")
    
    def _health_check_loop(self):
        """Haupt-Loop für Health-Checks"""
        while self.running:
            try:
                self.check_count += 1
                
                # Führe Health-Check durch
                if self.ssh.health_check():
                    self.last_check_ok = True
                    logger.debug(f"SSH Health-Check #{self.check_count}: ✅ OK")
                else:
                    # Verbindung fehlgeschlagen - versuche Reconnect
                    if self.last_check_ok:
                        logger.warning(f"SSH Health-Check #{self.check_count}: ❌ FEHLER - starte Reconnect...")
                        self.last_check_ok = False
                    
                    # Schließe alte Verbindung und versuche neu zu verbinden
                    self.ssh.close()
                    time.sleep(1)
                    
                    if self.ssh.connect():
                        self.reconnect_count += 1
                        logger.info(f"SSH Reconnect erfolgreich (#{self.reconnect_count})")
                        self.last_check_ok = True
                        
                        # Rufe Callback auf bei Wiederverbindung
                        if self.on_reconnect:
                            try:
                                self.on_reconnect()
                            except Exception as e:
                                logger.error(f"Reconnect-Callback Fehler: {e}")
                    else:
                        logger.error(f"SSH Reconnect fehlgeschlagen - warte auf nächsten Versuch")
                
                # Warte auf nächsten Check
                time.sleep(self.interval)
            
            except Exception as e:
                logger.error(f"SSH Health-Checker Exception: {e}")
                time.sleep(self.interval)
    
    def get_stats(self) -> dict:
        """Gibt Health-Check Statistiken zurück"""
        return {
            'checks': self.check_count,
            'reconnects': self.reconnect_count,
            'status': '✅ OK' if self.last_check_ok else '❌ ERROR',
            'interval': self.interval,
        }


def get_ssh_manager() -> SSHManager:
    """Gibt globale SSH-Manager-Instanz"""
    global _ssh_manager
    if _ssh_manager is None:
        _ssh_manager = SSHManager()
    return _ssh_manager
