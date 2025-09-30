#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Remote System Status für Raspberry Pi 5
Schnelle Abfrage von CPU-Temperatur und Festplattenbelegung
"""

import subprocess
import sys
import os

def quick_system_check():
    """Schnelle System-Status Abfrage per SSH"""
    
    # SSH-Verbindungsdetails (aus Ihrem System)
    ssh_key = "~/.ssh/id_rsa_ai-had"
    remote_host = "roimme@raspberrypi-5-ai-had"
    
    print("🔍 Raspberry Pi 5 System-Check...")
    print("=" * 40)
    
    try:
        # CPU-Temperatur
        temp_cmd = f'ssh -i {ssh_key} {remote_host} "vcgencmd measure_temp"'
        temp_result = subprocess.run(temp_cmd, shell=True, capture_output=True, text=True)
        
        if temp_result.returncode == 0:
            temp = temp_result.stdout.strip().replace("temp=", "").replace("'C", "°C")
            temp_val = float(temp.replace("°C", ""))
            temp_status = "🟢" if temp_val < 50 else "🟡" if temp_val < 60 else "🔴"
            print(f"🌡️  CPU-Temperatur: {temp} {temp_status}")
        else:
            print("❌ CPU-Temperatur nicht verfügbar")
        
        # Festplattenbelegung
        disk_cmd = f'ssh -i {ssh_key} {remote_host} "df -h / | tail -1"'
        disk_result = subprocess.run(disk_cmd, shell=True, capture_output=True, text=True)
        
        if disk_result.returncode == 0:
            parts = disk_result.stdout.strip().split()
            if len(parts) >= 5:
                used_percent = int(parts[4].replace('%', ''))
                disk_status = "🟢" if used_percent < 80 else "🟡" if used_percent < 90 else "🔴"
                print(f"💾 Festplatte: {parts[2]} / {parts[1]} ({parts[4]} belegt) {disk_status}")
        else:
            print("❌ Festplattenstatus nicht verfügbar")
        
        # Memory (optional)
        mem_cmd = f'ssh -i {ssh_key} {remote_host} "free -h | grep -E \\"Speicher|Mem\\" | head -1"'
        mem_result = subprocess.run(mem_cmd, shell=True, capture_output=True, text=True)
        
        if mem_result.returncode == 0:
            parts = mem_result.stdout.strip().split()
            if len(parts) >= 7:
                print(f"💭 RAM: {parts[2]} / {parts[1]} (verfügbar: {parts[6]})")
        
        # System Load
        load_cmd = f'ssh -i {ssh_key} {remote_host} "uptime"'
        load_result = subprocess.run(load_cmd, shell=True, capture_output=True, text=True)
        
        if load_result.returncode == 0:
            uptime_line = load_result.stdout.strip()
            if "load average:" in uptime_line:
                load_part = uptime_line.split("load average:")[1].strip()
                load_1min = float(load_part.split(',')[0].strip().replace(',', '.'))
                load_status = "🟢" if load_1min < 1.0 else "🟡" if load_1min < 2.0 else "🔴"
                print(f"⚡ CPU-Last: {load_1min:.2f} (1min) {load_status}")
        
        # AI-Modelle
        ai_cmd = f'ssh -i {ssh_key} {remote_host} "ls /usr/share/rpi-camera-assets/hailo_*_inference.json 2>/dev/null | wc -l"'
        ai_result = subprocess.run(ai_cmd, shell=True, capture_output=True, text=True)
        
        if ai_result.returncode == 0:
            model_count = ai_result.stdout.strip()
            print(f"🤖 AI-Modelle: {model_count} verfügbar")
    
    except Exception as e:
        print(f"❌ Fehler: {e}")

def main():
    """Hauptfunktion"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("🖥️  Quick Remote System Status")
            print("Usage:")
            print("  python3 quick_system_check.py          # Standard-Check")
            print("  python3 quick_system_check.py --watch  # Kontinuierliche Überwachung")
            return
        
        if sys.argv[1] == '--watch':
            import time
            print("⏰ Kontinuierliche Überwachung (Ctrl+C zum Beenden)")
            try:
                while True:
                    quick_system_check()
                    print("\\n" + "🔄 Aktualisierung in 30 Sekunden...")
                    time.sleep(30)
                    print("\\033[H\\033[J")  # Clear screen
            except KeyboardInterrupt:
                print("\\n👋 Überwachung beendet.")
                return
    
    quick_system_check()

if __name__ == "__main__":
    main()