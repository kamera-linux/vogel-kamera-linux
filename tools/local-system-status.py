#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lokaler System-Status Monitor
==============================

Liest lokale Systemparameter aus (CPU-Temperatur, RAM, Festplatte, Last)
analog zu den Remote-Status-Abfragen, aber ohne SSH - direkt auf dem Host.

Verwendung:
    python3 local-system-status.py              # Standard-Ausgabe
    python3 local-system-status.py --json       # JSON-Format
    python3 local-system-status.py --check      # Exit-Code basierend auf Status
    python3 local-system-status.py --thresholds # Zeige Schwellenwerte

Features:
- 🌡️  CPU-Temperatur (vcgencmd oder /sys/class/thermal)
- 💾 Festplattenbelegung (df)
- 💭 RAM-Auslastung (free)
- ⚡ System-Last (uptime)
- 🎨 Farbcodierte Ausgabe mit Status-Emojis
- 📊 JSON-Export für Automatisierung
- ⚠️  Warnungen bei kritischen Werten
- 🔄 Exit-Codes für Skript-Integration

Version: 1.2.0
Autor: Vogel-Kamera-Team
Lizenz: MIT
"""

import subprocess
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Schwellenwerte für Status-Bewertung
THRESHOLDS = {
    'cpu_temp': {
        'good': 50.0,      # < 50°C = Gut
        'warning': 60.0,   # 50-60°C = Warnung
        'critical': 70.0   # > 70°C = Kritisch
    },
    'disk_usage': {
        'good': 70,        # < 70% = Gut
        'warning': 80,     # 70-80% = Warnung
        'critical': 90     # > 90% = Kritisch
    },
    'cpu_load': {
        'good': 1.0,       # < 1.0 = Gut
        'warning': 2.0,    # 1.0-2.0 = Warnung
        'critical': 3.0    # > 3.0 = Kritisch
    },
    'memory_percent': {
        'good': 70,        # < 70% = Gut
        'warning': 85,     # 70-85% = Warnung
        'critical': 95     # > 95% = Kritisch
    }
}

# ANSI Farb-Codes
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def run_command(cmd: list) -> Optional[str]:
    """
    Führt System-Kommando aus und gibt Output zurück
    
    Args:
        cmd: Liste mit Kommando und Argumenten
        
    Returns:
        str: Kommando-Output oder None bei Fehler
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None

def get_cpu_temperature() -> Optional[float]:
    """
    Ermittelt CPU-Temperatur
    
    Versucht verschiedene Methoden:
    1. vcgencmd (Raspberry Pi)
    2. /sys/class/thermal/thermal_zone*/temp (Linux generic)
    
    Returns:
        float: Temperatur in °C oder None
    """
    # Methode 1: vcgencmd (Raspberry Pi)
    output = run_command(["vcgencmd", "measure_temp"])
    if output:
        try:
            temp_str = output.replace("temp=", "").replace("'C", "").replace("°C", "")
            return float(temp_str)
        except ValueError:
            pass
    
    # Methode 2: /sys/class/thermal (Linux generic)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_millidegrees = int(f.read().strip())
            return temp_millidegrees / 1000.0
    except (FileNotFoundError, ValueError, PermissionError):
        pass
    
    return None

def get_disk_usage(path: str = "/") -> Optional[Dict[str, Any]]:
    """
    Ermittelt Festplatten-Belegung
    
    Args:
        path: Mount-Punkt (default: /)
        
    Returns:
        dict: Festplatten-Infos oder None
    """
    output = run_command(["df", "-h", path])
    if output:
        lines = output.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 6:
                try:
                    use_percent = int(parts[4].replace('%', ''))
                    return {
                        "filesystem": parts[0],
                        "size": parts[1],
                        "used": parts[2],
                        "available": parts[3],
                        "use_percent": use_percent,
                        "mount_point": parts[5]
                    }
                except (ValueError, IndexError):
                    pass
    
    return None

def get_memory_usage() -> Optional[Dict[str, Any]]:
    """
    Ermittelt RAM-Auslastung
    
    Returns:
        dict: Memory-Infos mit Prozent-Berechnung oder None
    """
    output = run_command(["free", "-h"])
    if output:
        lines = output.splitlines()
        for line in lines:
            # Unterstützt beide: "Mem:" (Englisch) und "Speicher:" (Deutsch)
            if "Mem:" in line or "Speicher:" in line:
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        # Hole numerische Werte für Prozent-Berechnung
                        output_bytes = run_command(["free", "-b"])
                        if output_bytes:
                            for bline in output_bytes.splitlines():
                                if "Mem:" in bline or "Speicher:" in bline:
                                    bparts = bline.split()
                                    total_bytes = int(bparts[1])
                                    used_bytes = int(bparts[2])
                                    percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
                                    
                                    return {
                                        "total": parts[1],
                                        "used": parts[2],
                                        "free": parts[3],
                                        "shared": parts[4],
                                        "cache": parts[5],
                                        "available": parts[6],
                                        "use_percent": round(percent, 1)
                                    }
                    except (ValueError, IndexError, ZeroDivisionError):
                        pass
    
    return None

def get_system_load() -> Optional[Dict[str, float]]:
    """
    Ermittelt System-Last (Load Average)
    
    Returns:
        dict: Load-Werte (1min, 5min, 15min) oder None
    """
    output = run_command(["uptime"])
    if output:
        if "load average:" in output:
            try:
                load_part = output.split("load average:")[1].strip()
                loads = [l.strip().replace(',', '.') for l in load_part.split(",")]
                return {
                    "load_1min": float(loads[0]),
                    "load_5min": float(loads[1]),
                    "load_15min": float(loads[2])
                }
            except (ValueError, IndexError):
                pass
    
    return None

def get_uptime() -> Optional[str]:
    """
    Ermittelt System-Uptime
    
    Returns:
        str: Uptime-String oder None
    """
    output = run_command(["uptime", "-p"])
    if output:
        return output.replace("up ", "")
    
    return None

def get_system_status() -> Dict[str, Any]:
    """
    Sammelt alle System-Informationen
    
    Returns:
        dict: Kompletter System-Status
    """
    return {
        "cpu_temperature": get_cpu_temperature(),
        "disk_usage": get_disk_usage(),
        "memory_usage": get_memory_usage(),
        "system_load": get_system_load(),
        "uptime": get_uptime(),
        "timestamp": datetime.now().isoformat(),
        "hostname": run_command(["hostname"]),
        "kernel": run_command(["uname", "-r"])
    }

def get_status_emoji(value: float, thresholds: Dict[str, float], reverse: bool = False) -> str:
    """
    Gibt Status-Emoji basierend auf Schwellenwerten zurück
    
    Args:
        value: Zu prüfender Wert
        thresholds: Dict mit good/warning/critical Schwellen
        reverse: Falls True, niedrigere Werte = schlechter (für freien Speicher)
        
    Returns:
        str: Emoji
    """
    if reverse:
        if value >= thresholds['good']:
            return "🟢"
        elif value >= thresholds['warning']:
            return "🟡"
        else:
            return "🔴"
    else:
        if value < thresholds['good']:
            return "🟢"
        elif value < thresholds['warning']:
            return "🟡"
        elif value < thresholds['critical']:
            return "🟠"
        else:
            return "🔴"

def get_status_color(value: float, thresholds: Dict[str, float]) -> str:
    """
    Gibt ANSI-Farbe basierend auf Schwellenwerten zurück
    
    Args:
        value: Zu prüfender Wert
        thresholds: Dict mit good/warning/critical Schwellen
        
    Returns:
        str: ANSI Color Code
    """
    if value < thresholds['good']:
        return Colors.GREEN
    elif value < thresholds['warning']:
        return Colors.YELLOW
    else:
        return Colors.RED

def is_system_healthy(status: Dict[str, Any]) -> bool:
    """
    Prüft ob System-Status insgesamt gesund ist
    
    Args:
        status: System-Status Dict
        
    Returns:
        bool: True wenn alle Werte im grünen Bereich
    """
    healthy = True
    
    # CPU-Temperatur
    if status['cpu_temperature'] is not None:
        if status['cpu_temperature'] >= THRESHOLDS['cpu_temp']['critical']:
            healthy = False
    
    # Festplatte
    if status['disk_usage'] is not None:
        if status['disk_usage']['use_percent'] >= THRESHOLDS['disk_usage']['critical']:
            healthy = False
    
    # CPU-Last
    if status['system_load'] is not None:
        if status['system_load']['load_1min'] >= THRESHOLDS['cpu_load']['critical']:
            healthy = False
    
    # RAM
    if status['memory_usage'] is not None:
        if status['memory_usage']['use_percent'] >= THRESHOLDS['memory_percent']['critical']:
            healthy = False
    
    return healthy

def print_formatted_status(status: Dict[str, Any], show_thresholds: bool = False):
    """
    Gibt formatierten Status mit Farben und Emojis aus
    
    Args:
        status: System-Status Dict
        show_thresholds: Falls True, zeige auch Schwellenwerte
    """
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}📊 Lokaler System-Status{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    
    # Hostname und Timestamp
    if status['hostname']:
        print(f"🖥️  Host: {Colors.BOLD}{status['hostname']}{Colors.RESET}")
    print(f"🕐 Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if status['uptime']:
        print(f"⏱️  Uptime: {status['uptime']}")
    if status['kernel']:
        print(f"🐧 Kernel: {status['kernel']}")
    
    print(f"\n{Colors.BOLD}Hardware & Ressourcen:{Colors.RESET}")
    
    # CPU-Temperatur
    if status['cpu_temperature'] is not None:
        temp = status['cpu_temperature']
        emoji = get_status_emoji(temp, THRESHOLDS['cpu_temp'])
        color = get_status_color(temp, THRESHOLDS['cpu_temp'])
        print(f"   🌡️  CPU-Temp: {color}{temp:.1f}°C {emoji}{Colors.RESET}")
        if show_thresholds:
            print(f"      ├─ Gut: <{THRESHOLDS['cpu_temp']['good']}°C")
            print(f"      ├─ Warnung: <{THRESHOLDS['cpu_temp']['warning']}°C")
            print(f"      └─ Kritisch: >{THRESHOLDS['cpu_temp']['critical']}°C")
    else:
        print(f"   🌡️  CPU-Temp: {Colors.YELLOW}N/A{Colors.RESET}")
    
    # CPU-Last
    if status['system_load'] is not None:
        load = status['system_load']['load_1min']
        emoji = get_status_emoji(load, THRESHOLDS['cpu_load'])
        color = get_status_color(load, THRESHOLDS['cpu_load'])
        print(f"   ⚡ CPU-Load: {color}{load:.2f} {emoji}{Colors.RESET} "
              f"(5min: {status['system_load']['load_5min']:.2f}, "
              f"15min: {status['system_load']['load_15min']:.2f})")
        if show_thresholds:
            print(f"      ├─ Gut: <{THRESHOLDS['cpu_load']['good']}")
            print(f"      ├─ Warnung: <{THRESHOLDS['cpu_load']['warning']}")
            print(f"      └─ Kritisch: >{THRESHOLDS['cpu_load']['critical']}")
    else:
        print(f"   ⚡ CPU-Load: {Colors.YELLOW}N/A{Colors.RESET}")
    
    # RAM
    if status['memory_usage'] is not None:
        mem = status['memory_usage']
        percent = mem['use_percent']
        emoji = get_status_emoji(percent, THRESHOLDS['memory_percent'])
        color = get_status_color(percent, THRESHOLDS['memory_percent'])
        print(f"   💭 RAM: {color}{mem['used']} / {mem['total']} ({percent:.1f}%) {emoji}{Colors.RESET}")
        print(f"      └─ Verfügbar: {mem['available']}")
        if show_thresholds:
            print(f"      ├─ Gut: <{THRESHOLDS['memory_percent']['good']}%")
            print(f"      ├─ Warnung: <{THRESHOLDS['memory_percent']['warning']}%")
            print(f"      └─ Kritisch: >{THRESHOLDS['memory_percent']['critical']}%")
    else:
        print(f"   💭 RAM: {Colors.YELLOW}N/A{Colors.RESET}")
    
    # Festplatte
    if status['disk_usage'] is not None:
        disk = status['disk_usage']
        percent = disk['use_percent']
        emoji = get_status_emoji(percent, THRESHOLDS['disk_usage'])
        color = get_status_color(percent, THRESHOLDS['disk_usage'])
        print(f"   💾 Festplatte: {color}{disk['used']} / {disk['size']} ({percent}%) {emoji}{Colors.RESET}")
        print(f"      ├─ Verfügbar: {disk['available']}")
        print(f"      └─ Mount: {disk['mount_point']} ({disk['filesystem']})")
        if show_thresholds:
            print(f"      ├─ Gut: <{THRESHOLDS['disk_usage']['good']}%")
            print(f"      ├─ Warnung: <{THRESHOLDS['disk_usage']['warning']}%")
            print(f"      └─ Kritisch: >{THRESHOLDS['disk_usage']['critical']}%")
    else:
        print(f"   💾 Festplatte: {Colors.YELLOW}N/A{Colors.RESET}")
    
    # Gesamt-Status
    print(f"\n{Colors.BOLD}System-Status:{Colors.RESET}")
    if is_system_healthy(status):
        print(f"   ✅ {Colors.GREEN}System läuft im normalen Bereich{Colors.RESET}")
    else:
        print(f"   ⚠️  {Colors.RED}WARNUNG: System-Ressourcen kritisch!{Colors.RESET}")
    
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description='Lokaler System-Status Monitor für Vogel-Kamera-Linux',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s                    # Standard-Ausgabe mit Farben
  %(prog)s --json             # JSON-Format für Automatisierung
  %(prog)s --check            # Exit-Code 0=OK, 1=Warnung
  %(prog)s --thresholds       # Zeige Schwellenwerte an
  
Exit-Codes:
  0 - System gesund
  1 - System-Ressourcen kritisch
        """
    )
    
    parser.add_argument('--json', action='store_true',
                       help='Ausgabe als JSON')
    parser.add_argument('--check', action='store_true',
                       help='Nur Status prüfen (Exit-Code 0=OK, 1=Kritisch)')
    parser.add_argument('--thresholds', action='store_true',
                       help='Zeige Schwellenwerte in der Ausgabe')
    parser.add_argument('--version', action='version',
                       version='Vogel-Kamera-Linux local-system-status v1.2.0')
    
    args = parser.parse_args()
    
    # Hole System-Status
    status = get_system_status()
    
    # JSON-Ausgabe
    if args.json:
        # Füge Health-Status und Schwellenwerte hinzu
        status['healthy'] = is_system_healthy(status)
        status['thresholds'] = THRESHOLDS
        print(json.dumps(status, indent=2, ensure_ascii=False))
        sys.exit(0 if status['healthy'] else 1)
    
    # Check-Modus (nur Exit-Code)
    if args.check:
        healthy = is_system_healthy(status)
        if healthy:
            print("✅ System-Status: OK")
        else:
            print("⚠️  System-Status: KRITISCH")
        sys.exit(0 if healthy else 1)
    
    # Standard-Ausgabe mit Formatierung
    print_formatted_status(status, show_thresholds=args.thresholds)
    
    # Exit-Code basierend auf Health
    sys.exit(0 if is_system_healthy(status) else 1)

if __name__ == "__main__":
    main()
