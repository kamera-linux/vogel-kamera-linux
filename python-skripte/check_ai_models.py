#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Skript zur Überprüfung verfügbarer AI-Modelle für Vogelarten-Erkennung
"""

import paramiko
import sys
import os
from config import config

def check_remote_ai_models():
    """Prüft verfügbare AI-Modelle auf dem Raspberry Pi"""
    
    # SSH-Verbindungsdetails
    remote_host = config.get_remote_host_config()
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], username=remote_host['username'], key_filename=remote_host['key_filename'])
        
        print("🔍 Suche nach verfügbaren AI-Modellen auf dem Raspberry Pi...")
        print("=" * 60)
        
        # Standard Hailo-Modelle prüfen
        print("\n📂 Standard Hailo-Modelle (/usr/share/rpi-camera-assets/):")
        stdin, stdout, stderr = ssh.exec_command("ls -la /usr/share/rpi-camera-assets/ | grep -E '\\.json$|\\.hef$'")
        output = stdout.read().decode()
        if output:
            print(output)
        else:
            print("  Keine JSON/HEF-Dateien gefunden.")
        
        # Nach Vogel-spezifischen Modellen suchen
        print("\n🐦 Suche nach Vogel-spezifischen Modellen:")
        search_commands = [
            "find /usr/share -name '*bird*' -o -name '*aves*' -o -name '*ornith*' 2>/dev/null",
            "find /opt -name '*bird*' -o -name '*aves*' -o -name '*ornith*' 2>/dev/null",
            "find /home -name '*bird*' -o -name '*aves*' -o -name '*ornith*' 2>/dev/null | head -10"
        ]
        
        for cmd in search_commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode().strip()
            if output:
                print(f"  Gefunden: {output}")
        
        # Verfügbare Hardware prüfen
        print("\n🔧 Hardware-Information:")
        stdin, stdout, stderr = ssh.exec_command("cat /proc/device-tree/model")
        model = stdout.read().decode().strip()
        print(f"  Raspberry Pi Modell: {model}")
        
        # Hailo-Treiber prüfen
        stdin, stdout, stderr = ssh.exec_command("lsmod | grep hailo")
        hailo_driver = stdout.read().decode().strip()
        if hailo_driver:
            print(f"  Hailo-Treiber: ✅ Geladen")
            print(f"    {hailo_driver}")
        else:
            print(f"  Hailo-Treiber: ❌ Nicht gefunden")
        
        # libcamera-vid mit Hailo-Support prüfen
        print("\n📹 libcamera-vid Hailo-Support:")
        stdin, stdout, stderr = ssh.exec_command("libcamera-vid --help | grep -i post-process")
        help_output = stdout.read().decode().strip()
        if help_output:
            print("  ✅ --post-process-file Parameter verfügbar")
        else:
            print("  ❌ Kein Post-Processing Support erkannt")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Fehler bei der Verbindung: {e}")
        return False
    
    return True

def suggest_models():
    """Gibt Empfehlungen für Vogelarten-Modelle"""
    print("\n" + "=" * 60)
    print("💡 EMPFEHLUNGEN FÜR VOGELARTEN-ERKENNUNG:")
    print("=" * 60)
    
    print("\n1️⃣ SOFORT VERFÜGBAR:")
    print("   • Standard YOLOv8: Erkennt 'bird' (allgemein)")
    print("   • Aufruf: --ai-modul on --ai-model yolov8")
    
    print("\n2️⃣ ERWEITERTE OPTIONEN:")
    print("   • BirdNET für Raspberry Pi installieren")
    print("   • iNaturalist Vision Modell adaptieren")
    print("   • Eigenes YOLOv8 für lokale Vogelarten trainieren")
    
    print("\n3️⃣ EMPFOHLENE VOGELARTEN FÜR TRAINING:")
    print("   Häufige deutsche Gartenvögel:")
    print("   • Amsel, Blaumeise, Kohlmeise, Rotkehlchen")
    print("   • Buchfink, Grünfink, Haussperling")
    print("   • Star, Elster, Rabenkrähe")
    
    print("\n4️⃣ NÄCHSTE SCHRITTE:")
    print("   1. Testen Sie erst das Standard-Modell")
    print("   2. Sammeln Sie Trainingsdaten aus Ihrem Vogelhaus")
    print("   3. Trainieren Sie ein spezifisches Modell")
    print("   4. Siehe: AI-MODELLE-VOGELARTEN.md")

def main():
    """Hauptfunktion"""
    print("🐦 AI-Modell Checker für Vogelarten-Erkennung")
    print("=" * 50)
    
    # Konfiguration validieren
    config_errors = config.validate_config()
    if config_errors:
        print("⚠️ Konfigurationsprobleme gefunden:")
        for error in config_errors:
            print(f"  - {error}")
        print("\nBitte konfigurieren Sie das System entsprechend der README.md")
        return 1
    
    # Remote-Modelle prüfen
    if check_remote_ai_models():
        suggest_models()
        return 0
    else:
        print("\n❌ Konnte Remote-System nicht erreichen.")
        return 1

if __name__ == "__main__":
    sys.exit(main())