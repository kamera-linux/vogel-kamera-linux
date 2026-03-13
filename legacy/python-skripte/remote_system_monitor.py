#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote System Monitor für Raspberry Pi 5
Überwacht Festplattenbelegung, CPU-Temperatur und Systemressourcen
"""

import paramiko
import json
import re
from datetime import datetime
from config import config

def get_remote_system_info():
    """Sammle umfassende Systeminformationen vom Remote-Host"""
    
    # SSH-Verbindung (aus bestehender Konfiguration)
    remote_host = config.get_remote_host_config()
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host['hostname'], 
                   username=remote_host['username'], 
                   key_filename=remote_host['key_filename'])
        
        system_info = {}
        
        # 📊 Festplattenbelegung
        stdin, stdout, stderr = ssh.exec_command("df -h --output=source,size,used,avail,pcent,target")
        df_output = stdout.read().decode().strip()
        system_info['disk'] = parse_disk_usage(df_output)
        
        # 🌡️ CPU-Temperatur
        stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
        temp_output = stdout.read().decode().strip()
        system_info['cpu_temp'] = parse_cpu_temp(temp_output)
        
        # 💭 Memory-Info
        stdin, stdout, stderr = ssh.exec_command("free -h")
        memory_output = stdout.read().decode().strip()
        system_info['memory'] = parse_memory_usage(memory_output)
        
        # ⚡ CPU-Last und Uptime
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        system_info['load'] = parse_system_load(uptime_output)
        
        # 🎥 AI-Modell-Verfügbarkeit
        stdin, stdout, stderr = ssh.exec_command("ls -la /usr/share/rpi-camera-assets/hailo_*_inference.json")
        ai_models_output = stdout.read().decode().strip()
        system_info['ai_models'] = parse_ai_models(ai_models_output)
        
        # 📅 Letzte Boot-Zeit
        stdin, stdout, stderr = ssh.exec_command("who -b")
        boot_output = stdout.read().decode().strip()
        system_info['boot_time'] = parse_boot_time(boot_output)
        
        ssh.close()
        system_info['timestamp'] = datetime.now().isoformat()
        system_info['status'] = 'success'
        
        return system_info
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def parse_disk_usage(df_output):
    """Parse df -h Output"""
    lines = df_output.split('\n')[1:]  # Skip header
    disks = []
    
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 6:
                disks.append({
                    'filesystem': parts[0],
                    'size': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'use_percent': parts[4],
                    'mount_point': parts[5]
                })
    
    return disks

def parse_cpu_temp(temp_output):
    """Parse CPU-Temperatur Output"""
    # Format: temp=40.0'C
    match = re.search(r'temp=(\d+\.?\d*)', temp_output)
    if match:
        temp_celsius = float(match.group(1))
        return {
            'celsius': temp_celsius,
            'fahrenheit': round(temp_celsius * 9/5 + 32, 1),
            'status': get_temp_status(temp_celsius),
            'raw': temp_output
        }
    return {'error': 'Could not parse temperature', 'raw': temp_output}

def get_temp_status(temp_celsius):
    """Bewerte CPU-Temperatur"""
    if temp_celsius < 50:
        return 'optimal'
    elif temp_celsius < 60:
        return 'good'
    elif temp_celsius < 70:
        return 'warm'
    elif temp_celsius < 80:
        return 'hot'
    else:
        return 'critical'

def parse_memory_usage(memory_output):
    """Parse Memory Usage"""
    lines = memory_output.split('\n')
    for line in lines:
        if 'Speicher:' in line or 'Mem:' in line:
            parts = line.split()
            if len(parts) >= 7:
                return {
                    'total': parts[1],
                    'used': parts[2],
                    'free': parts[3],
                    'shared': parts[4],
                    'cache': parts[5],
                    'available': parts[6]
                }
    return {'error': 'Could not parse memory usage'}

def parse_system_load(uptime_output):
    """Parse System Load"""
    # Format: 11:11:33 up 3:18, 2 users, load average: 0,00, 0,00, 0,03
    match = re.search(r'load average: ([\d,\.]+), ([\d,\.]+), ([\d,\.]+)', uptime_output)
    uptime_match = re.search(r'up\s+(.+?),\s+\d+\s+user', uptime_output)
    
    load_data = {}
    if match:
        load_data['load_1min'] = float(match.group(1).replace(',', '.'))
        load_data['load_5min'] = float(match.group(2).replace(',', '.'))
        load_data['load_15min'] = float(match.group(3).replace(',', '.'))
    
    if uptime_match:
        load_data['uptime'] = uptime_match.group(1).strip()
    
    load_data['raw'] = uptime_output
    return load_data

def parse_ai_models(ai_models_output):
    """Parse verfügbare AI-Modelle"""
    models = []
    lines = ai_models_output.split('\n')
    
    for line in lines:
        if 'hailo_' in line and '_inference.json' in line:
            parts = line.split()
            if len(parts) >= 9:
                filename = parts[-1]
                model_name = filename.replace('hailo_', '').replace('_inference.json', '')
                file_size = parts[4]
                models.append({
                    'name': model_name,
                    'filename': filename,
                    'size': file_size,
                    'path': f"/usr/share/rpi-camera-assets/{filename}"
                })
    
    return models

def parse_boot_time(boot_output):
    """Parse Boot-Zeit"""
    # Format: system boot  2025-09-30 07:53
    match = re.search(r'system boot\s+(.+)', boot_output)
    if match:
        return match.group(1).strip()
    return boot_output.strip()

def print_system_summary(system_info):
    """Formatierte Ausgabe der Systeminformationen"""
    if system_info['status'] != 'success':
        print(f"❌ Fehler beim Abrufen der Systeminformationen: {system_info.get('error', 'Unbekannter Fehler')}")
        return
    
    print("🖥️  RASPBERRY PI 5 SYSTEM STATUS")
    print("=" * 50)
    
    # CPU-Temperatur
    if 'cpu_temp' in system_info and 'celsius' in system_info['cpu_temp']:
        temp = system_info['cpu_temp']
        status_emoji = {
            'optimal': '🟢',
            'good': '🟡', 
            'warm': '🟠',
            'hot': '🔴',
            'critical': '🚨'
        }.get(temp['status'], '❓')
        
        print(f"🌡️  CPU-Temperatur: {temp['celsius']}°C ({temp['fahrenheit']}°F) {status_emoji}")
    
    # Festplattenbelegung (nur Hauptpartition)
    if 'disk' in system_info:
        for disk in system_info['disk']:
            if disk['mount_point'] == '/':
                used_percent = disk['use_percent'].replace('%', '')
                emoji = '🟢' if int(used_percent) < 80 else '🟡' if int(used_percent) < 90 else '🔴'
                print(f"💾 Festplatte: {disk['used']} / {disk['size']} ({disk['use_percent']}) {emoji}")
                break
    
    # Memory
    if 'memory' in system_info and 'used' in system_info['memory']:
        mem = system_info['memory']
        print(f"💭 RAM: {mem['used']} / {mem['total']} (verfügbar: {mem['available']})")
    
    # System Load
    if 'load' in system_info and 'load_1min' in system_info['load']:
        load = system_info['load']
        load_emoji = '🟢' if load['load_1min'] < 1.0 else '🟡' if load['load_1min'] < 2.0 else '🔴'
        print(f"⚡ CPU-Last: {load['load_1min']:.2f} (1min) {load_emoji}")
        if 'uptime' in load:
            print(f"⏱️  Uptime: {load['uptime']}")
    
    # AI-Modelle
    if 'ai_models' in system_info and system_info['ai_models']:
        print(f"🤖 AI-Modelle: {len(system_info['ai_models'])} verfügbar")
        for model in system_info['ai_models']:
            print(f"   • {model['name']} ({model['size']})")
    
    # Boot-Zeit
    if 'boot_time' in system_info:
        print(f"🚀 Boot-Zeit: {system_info['boot_time']}")
    
    print(f"📅 Abfrage: {system_info['timestamp']}")

def main():
    """Hauptfunktion für direkten Aufruf"""
    print("🔍 Sammle Remote-System-Informationen...")
    system_info = get_remote_system_info()
    print_system_summary(system_info)
    
    # Optional: JSON-Export
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print("\n" + "="*50)
        print("📄 JSON-Export:")
        print(json.dumps(system_info, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()