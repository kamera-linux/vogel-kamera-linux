#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfigurationssystem für Vogel-Kamera-Linux
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Version Information
__version__ = "1.1.2"
__version_info__ = (1, 1, 2)

class Config:
    """Zentrale Konfigurationsklasse für alle Skripte"""
    
    def __init__(self):
        # Lade .env-Datei wenn vorhanden
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            
        # Standard-Werte
        self.defaults = {
            'hostname': 'your-raspberry-pi-hostname',
            'username': 'your-username', 
            'ssh_key_path': '~/.ssh/id_rsa_rpi',
            'base_video_path': '~/Videos/Vogelhaus',
            'remote_video_path': '/home/your-username/Videos/Vogelhaus',
            'remote_audio_path': '/home/your-username/Audio/Kamerawagen'
        }
        
        # Lade Konfiguration aus Umgebungsvariablen oder verwende Defaults
        self.hostname = os.getenv('RPI_HOSTNAME', self.defaults['hostname'])
        self.username = os.getenv('RPI_USERNAME', self.defaults['username'])
        self.ssh_key_path = os.path.expanduser(os.getenv('SSH_KEY_PATH', self.defaults['ssh_key_path']))
        self.base_video_path = os.path.expanduser(os.getenv('BASE_VIDEO_PATH', self.defaults['base_video_path']))
        self.remote_video_path = os.getenv('REMOTE_VIDEO_PATH', self.defaults['remote_video_path'])
        self.remote_audio_path = os.getenv('REMOTE_AUDIO_PATH', self.defaults['remote_audio_path'])
    
    def get_remote_host_config(self):
        """Gibt SSH-Konfiguration für paramiko zurück"""
        return {
            'hostname': self.hostname,
            'username': self.username,
            'key_filename': self.ssh_key_path
        }
    
    def get_video_path(self, year, week_or_timestamp, timestamp=None, subdir="AI-HAD"):
        """Generiert lokalen Videopfad"""
        if timestamp:
            return os.path.join(self.base_video_path, subdir, str(year), str(week_or_timestamp), timestamp)
        else:
            return os.path.join(self.base_video_path, subdir, str(year), week_or_timestamp)
    
    def get_remote_video_path(self, year, timestamp):
        """Generiert Remote-Videopfad"""
        return f"{self.remote_video_path}/{year}/{timestamp}"
    
    def get_remote_audio_path(self, year, timestamp):
        """Generiert Remote-Audiopfad"""
        return f"{self.remote_audio_path}/{year}/{timestamp}"
    
    def validate_config(self):
        """Validiert die Konfiguration"""
        errors = []
        
        if self.hostname == self.defaults['hostname']:
            errors.append("Hostname nicht konfiguriert (noch Default-Wert)")
        
        if self.username == self.defaults['username']:
            errors.append("Username nicht konfiguriert (noch Default-Wert)")
        
        if not os.path.exists(self.ssh_key_path):
            errors.append(f"SSH-Schlüssel nicht gefunden: {self.ssh_key_path}")
        
        return errors

# Globale Konfigurationsinstanz
config = Config()

def main():
    """Hauptfunktion für direkte Ausführung - Konfiguration testen"""
    print("🔧 Vogel-Kamera-Linux Konfigurationscheck")
    print("=" * 50)
    
    errors = config.validate_config()
    if errors:
        print("❌ Konfigurationsprobleme gefunden:")
        for error in errors:
            print(f"  - {error}")
        print("\n💡 Lösungsschritte:")
        print("1. Kopieren Sie .env.example zu .env")
        print("2. Bearbeiten Sie .env mit Ihren Daten")
        print("3. Stellen Sie sicher, dass SSH-Schlüssel existiert")
        return False
    else:
        print("✅ Konfiguration ist vollständig!")
        print(f"📡 Remote Host: {config.hostname}")
        print(f"👤 Username: {config.username}")
        print(f"🔑 SSH Key: {config.ssh_key_path}")
        print(f"📁 Videos: {config.base_video_path}")
        return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)