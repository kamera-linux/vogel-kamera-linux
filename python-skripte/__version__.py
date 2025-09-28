#!/usr/bin/env python3
"""
Versionsinformationen für Vogel-Kamera-Linux
"""

__version__ = '1.1.7'
__author__ = "Vogel-Kamera-Team"
__description__ = "Ferngesteuerte Kameraüberwachung für Vogelhäuser mit KI-gestützter Objekterkennung"
__license__ = "MIT"

# Kompatibilität
REQUIRED_PYTHON = "3.8"
SUPPORTED_OS = ["Linux", "Raspberry Pi OS"]

# Release Information (v1.1.6)
RELEASE_FEATURES = [
    "GitHub Discussions Integration",
    "Community & Diskussionen Bereich", 
    "Erweiterte Support-Optionen",
    "Nutzer-Interaktion Features"
]

# Modul-Informationen
MODULES = {
    "ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py": {
        "version": __version__,
        "description": "Hauptskript mit KI-Objekterkennung (YOLOv8)",
        "features": ["4K Video", "Audio", "KI-Erkennung", "Auto-Organisation"]
    },
    "ai-had-audio-remote-param-vogel-libcamera-single.py": {
        "version": __version__,
        "description": "Spezialisiertes Audio-Aufnahmeskript",
        "features": ["USB-Audio", "Remote-Steuerung", "Auto-Erkennung"]
    },
    "ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py": {
        "version": __version__,
        "description": "Zeitlupe-Aufnahmen für detaillierte Analyse",
        "features": ["120fps+", "Zeitlupe", "Flexible Auflösung"]
    },
    "generate_qr_codes.py": {
        "version": __version__,
        "description": "QR-Code Generator für YouTube-Integration",
        "features": ["YouTube QR-Codes", "Mobile Zugriff", "Automatisierung"]
    }
}

def get_version_info():
    """Gibt formatierte Versionsinformationen zurück"""
    return f"""
Vogel-Kamera-Linux v{__version__}
{__description__}

Autor: {__author__}
Lizenz: {__license__}
Python: >= {REQUIRED_PYTHON}
OS: {', '.join(SUPPORTED_OS)}
"""

def print_version():
    """Druckt Versionsinformationen"""
    print(get_version_info())

if __name__ == "__main__":
    print_version()