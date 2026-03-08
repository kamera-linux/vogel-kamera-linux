#!/usr/bin/env python3
"""
Remote System Diagnose-Script
Verbindet sich per SSH mit dem Raspberry Pi und führt umfassende Tests durch
"""

import os
import sys
import paramiko
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Konfiguration laden
ENV_FILE = Path(__file__).parent / '.env'
if not ENV_FILE.exists():
    print("❌ .env-Datei nicht gefunden!")
    sys.exit(1)

load_dotenv(ENV_FILE)

SSH_KEY = os.path.expanduser(os.getenv('SSH_KEY', os.path.expanduser('~/.ssh/id_rsa_pi')))
SSH_USER = os.getenv('SSH_USER', 'pi')
SSH_HOST = os.getenv('SSH_HOST', 'raspberry-pi.local')

# Farben
COLORS = {
    'green': '\033[0;32m',
    'red': '\033[0;31m',
    'yellow': '\033[1;33m',
    'blue': '\033[1;34m',
    'cyan': '\033[0;36m',
    'magenta': '\033[0;35m',
    'reset': '\033[0m',
}

def log(color, message):
    """Farbige Log-Ausgabe"""
    print(f"{COLORS.get(color, '')}{message}{COLORS['reset']}")

def connect_ssh():
    """Stellt SSH-Verbindung her"""
    log('cyan', f"\n🔗 Verbinde zu {SSH_USER}@{SSH_HOST}...")
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY, timeout=10)
        log('green', "✅ SSH-Verbindung OK\n")
        return client
    except Exception as e:
        log('red', f"❌ SSH-Fehler: {e}")
        sys.exit(1)

def execute_command(client, cmd, description=""):
    """Führt Kommando remote aus"""
    try:
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        
        if error and "warning" not in error.lower():
            return None, error
        return output, None
    except Exception as e:
        return None, str(e)

def diagnose_system(client):
    """Umfassende System-Diagnose"""
    log('blue', "="*70)
    log('blue', "📊 SYSTEM-DIAGNOSE")
    log('blue', "="*70)
    
    # 1. System Info
    log('cyan', "\n📋 SYSTEM-INFORMATIONEN")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "uname -a")
    if output:
        print(f"   Kernel: {output}")
    
    output, _ = execute_command(client, "cat /etc/os-release | grep PRETTY_NAME")
    if output:
        print(f"   OS: {output.split('=')[1].strip('\"')}")
    
    output, _ = execute_command(client, "cat /proc/cpuinfo | grep 'model name' | head -1")
    if output:
        cpu = output.split(':')[1].strip()
        print(f"   CPU: {cpu}")
    
    output, _ = execute_command(client, "nproc")
    if output:
        print(f"   Cores: {output}")
    
    # 2. CPU & Load
    log('cyan', "\n⚡ CPU & LOAD")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "uptime | awk '{print $(NF-2), $(NF-1), $NF}'")
    if output:
        load = output.replace(',', '')
        log('yellow', f"   Load Average (1m, 5m, 15m): {load}")
    
    output, _ = execute_command(client, "cat /proc/cpuinfo | grep 'BogoMIPS' | head -1")
    if output:
        print(f"   BogoMIPS: {output.split(':')[1].strip()}")
    
    # 3. Temperatur
    log('cyan', "\n🌡️  TEMPERATUR")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000}'")
    if output:
        try:
            temp = float(output.split('=')[1].split('\'')[0]) if '=' in output else float(output)
            if temp > 75:
                log('red', f"   ⛔ KRITISCH: {temp}°C (Drosselung aktiv!)")
            elif temp > 65:
                log('yellow', f"   ⚠️  WARM: {temp}°C")
            else:
                log('green', f"   ✅ OK: {temp}°C")
        except:
            print(f"   {output}")
    
    # 4. Drosselung
    log('cyan', "\n🔧 CPU DROSSELUNG")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "vcgencmd get_throttled 2>/dev/null")
    if output:
        throttled = output.split('=')[1] if '=' in output else output
        if throttled == '0x0':
            log('green', "   ✅ Keine Drosselung")
        else:
            log('red', f"   ⚠️  Drosselung aktiv: {throttled}")
    
    # 5. RAM
    log('cyan', "\n💾 SPEICHER")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "free -h | grep Mem")
    if output:
        parts = output.split()
        total = parts[1]
        used = parts[2]
        available = parts[6]
        print(f"   Total: {total} | Used: {used} | Available: {available}")
    
    output, _ = execute_command(client, "free | grep Mem | awk '{printf \"%.1f%%\", ($3/$2)*100}'")
    if output:
        usage = output
        if float(usage.rstrip('%')) > 75:
            log('red', f"   ⛔ RAM-Auslastung: {usage}")
        elif float(usage.rstrip('%')) > 50:
            log('yellow', f"   ⚠️  RAM-Auslastung: {usage}")
        else:
            log('green', f"   ✅ RAM-Auslastung: {usage}")
    
    # 6. Festplatte
    log('cyan', "\n💿 FESTPLATTE")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "df -h / | tail -1")
    if output:
        parts = output.split()
        print(f"   Total: {parts[1]} | Used: {parts[2]} | Available: {parts[3]}")
        usage_pct = parts[4]
        if int(usage_pct.rstrip('%')) > 90:
            log('red', f"   ⛔ Auslastung: {usage_pct}")
        elif int(usage_pct.rstrip('%')) > 75:
            log('yellow', f"   ⚠️  Auslastung: {usage_pct}")
        else:
            log('green', f"   ✅ Auslastung: {usage_pct}")
    
    # 7. Laufende Prozesse
    log('cyan', "\n🔍 TOP PROZESSE (CPU)")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "ps aux --sort=-%cpu | head -6 | awk '{printf \"   %-20s %6s%% %6s MB\\n\", $11, $3, $6/1024}'")
    if output:
        for line in output.split('\n'):
            if line.strip():
                print(line)
    
    # 8. Camera & Preview-Stream
    log('cyan', "\n📹 KAMERA & STREAMS")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "pgrep -f 'unified-camera-monitor|libcamera|rpicam' | wc -l")
    if output:
        count = int(output)
        if count > 0:
            log('yellow', f"   ⚠️  {count} Kamera/Stream-Prozesse laufen")
            
            # Details
            output, _ = execute_command(client, "ps aux | grep -E 'unified-camera-monitor|libcamera|rpicam' | grep -v grep")
            if output:
                for line in output.split('\n')[:3]:
                    if line.strip():
                        print(f"   • {line[:80]}")
        else:
            log('green', "   ✅ Keine Kamera-Prozesse")
    
    # 9. YOLO/Python
    log('cyan', "\n🤖 YOLO / PYTHON")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "pgrep -f 'yolo|ultralytics' | wc -l")
    if output:
        count = int(output)
        if count > 0:
            log('yellow', f"   ⚠️  {count} YOLO-Prozess(e) laufen")
        else:
            log('green', "   ✅ Keine YOLO-Prozesse")
    
    # 10. Python venv
    output, _ = execute_command(client, "ls -la ~/.local/lib/python*/site-packages 2>/dev/null | wc -l")
    if output and int(output) > 10:
        log('green', f"   ✅ Python-Pakete: ~{int(output)} Module")
    
    # 11. SSH Sessions
    log('cyan', "\n🔌 SSH SESSIONS")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "who | wc -l")
    if output:
        sessions = int(output)
        log('yellow', f"   Aktive Sessions: {sessions}")
    
    # 12. Systemd Services
    log('cyan', "\n⚙️  SYSTEMD SERVICES")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "systemctl list-units --type=service --state=running | wc -l")
    if output:
        print(f"   Laufende Services: {output}")
    
    # Check für fehlgeschlagene Services
    failed_output, _ = execute_command(client, "systemctl list-units --type=service --state=failed --no-pager --all | grep -c 'failed'")
    failed_count = int(failed_output) if failed_output else 0
    
    if failed_count > 0:
        log('red', f"   ⚠️  Fehlgeschlagene Services: {failed_count}")
        # Details zu fehlgeschlagenen Services
        details, _ = execute_command(client, "systemctl list-units --type=service --state=failed --no-pager --all")
        if details:
            lines = [l for l in details.split('\n') if '.service' in l and 'failed' in l]
            for service_line in lines[:10]:
                if service_line.strip():
                    log('red', f"      • {service_line[:75]}")
    else:
        log('green', "   ✅ Alle Services laufen normal")
    
    # 13. Netzwerk
    log('cyan', "\n🌐 NETZWERK")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "hostname -I")
    if output:
        print(f"   IP-Adressen: {output}")
    
    output, _ = execute_command(client, "cat /sys/class/net/eth0/statistics/rx_bytes 2>/dev/null || echo '0'")
    rx_bytes = int(output) if output and output != '0' else 0
    output, _ = execute_command(client, "cat /sys/class/net/eth0/statistics/tx_bytes 2>/dev/null || echo '0'")
    tx_bytes = int(output) if output and output != '0' else 0
    
    if rx_bytes > 0 or tx_bytes > 0:
        print(f"   RX: {rx_bytes/1024/1024:.1f} MB | TX: {tx_bytes/1024/1024:.1f} MB")
    
    # 14. Zusammenfassung
    log('cyan', "\n📈 ZUSAMMENFASSUNG")
    log('cyan', "-" * 70)
    
    output, _ = execute_command(client, "uptime | awk '{print $(NF-2)}' | tr -d ','")
    if output:
        try:
            load = float(output)
            nproc, _ = execute_command(client, "nproc")
            cores = int(nproc) if nproc else 4
            load_per_core = load / cores
            
            if load > 3:
                log('red', f"   ⛔ HOHE LAST: {load} ({load_per_core:.1f} pro Core)")
            elif load > 1.5:
                log('yellow', f"   ⚠️  ERHÖHTE LAST: {load} ({load_per_core:.1f} pro Core)")
            else:
                log('green', f"   ✅ NORMAL: {load} ({load_per_core:.1f} pro Core)")
        except:
            pass

def main():
    """Hauptprogramm"""
    log('blue', "\n" + "="*70)
    log('blue', "🐦 UNIFIED MONITOR - REMOTE SYSTEM DIAGNOSE")
    log('blue', "="*70)
    log('yellow', f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    client = connect_ssh()
    
    try:
        diagnose_system(client)
        
        log('cyan', "\n" + "="*70)
        log('green', "✨ Diagnose abgeschlossen!")
        log('cyan', "="*70 + "\n")
        
    except KeyboardInterrupt:
        log('yellow', "\n\n⏹️  Abgebrochen")
        sys.exit(1)
    except Exception as e:
        log('red', f"\n\n❌ Fehler: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == '__main__':
    main()
