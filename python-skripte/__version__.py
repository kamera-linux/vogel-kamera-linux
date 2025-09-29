#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versionsinformationen für Vogel-Kamera-Linux (python-skripte Proxy)

Diese Datei importiert die zentrale Versionsverwaltung aus scripts/version.py
"""
import sys
import os

# Füge scripts/ Verzeichnis zum Python-Pfad hinzu
scripts_path = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_path)

# Importiere aus der zentralen version.py
try:
    from version import __version__, get_version_info
except ImportError:
    # Fallback wenn scripts/version.py nicht gefunden wird
    __version__ = "1.1.7"
    
    def get_version_info():
        return {
            'version': __version__,
            'release_name': '3D-Konstruktion und Wiki-Sidebar',
            'release_date': '2025-09-29'
        }

# Für Rückwärtskompatibilität
__author__ = "Vogel-Kamera-Team"
__description__ = "Ferngesteuerte Kameraüberwachung für Vogelhäuser mit KI-gestützter Objekterkennung"
__license__ = "MIT"
