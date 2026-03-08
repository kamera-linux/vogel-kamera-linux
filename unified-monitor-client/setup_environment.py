#!/usr/bin/env python3
"""
Setup-Skript für Unified Monitor Client
Richtet Remote Pi und lokalen Client automatisch ein
Unterstützt auch --uninstall für Cleanup

Verwendung:
  python3 setup_environment.py          # Installation
  python3 setup_environment.py --uninstall  # Deinstallation
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv

# Konfiguration laden
ENV_FILE = Path(__file__).parent / '.env'
if not ENV_FILE.exists():
    print("❌ FEHLER: .env-Datei nicht gefunden!")
    print(f"   Bitte erstellen Sie: {ENV_FILE}")
    sys.exit(1)

load_dotenv(ENV_FILE)

SSH_KEY = os.getenv('SSH_KEY', os.path.expanduser('~/.ssh/id_rsa_pi'))
SSH_USER = os.getenv('SSH_USER', 'pi_user')
SSH_HOST = os.getenv('SSH_HOST', 'raspberry-pi-monitor')
SSH_TIMEOUT = 10
SSH_RETRIES = 3

# Farbcodes
COLORS = {
    'green': '\033[0;32m',
    'red': '\033[0;31m',
    'yellow': '\033[1;33m',
    'blue': '\033[1;34m',
    'cyan': '\033[0;36m',
    'reset': '\033[0m',
}

def log(color, message):
    """Farbige Log-Ausgabe"""
    print(f"{COLORS.get(color, '')}{message}{COLORS['reset']}")

def run_cmd(cmd, check=True):
    """Führt Kommando aus und gibt Output zurück"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        if check and result.returncode != 0:
            log('red', f"❌ Kommando fehlgeschlagen: {cmd}")
            log('red', f"   Fehler: {result.stderr}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        log('red', f"⏱️  Timeout bei Kommando: {cmd}")
        return None
    except Exception as e:
        log('red', f"❌ Fehler: {e}")
        return None

def ssh_cmd(cmd):
    """Führt Kommando auf Remote Pi aus"""
    ssh_cmd_full = f"ssh -i {SSH_KEY} -o ConnectTimeout={SSH_TIMEOUT} {SSH_USER}@{SSH_HOST} '{cmd}'"
    return run_cmd(ssh_cmd_full, check=False)

def test_ssh_connection():
    """Testet SSH-Verbindung"""
    log('cyan', "\n🔗 Teste SSH-Verbindung...")
    print(f"   Host: {SSH_HOST}, User: {SSH_USER}, Key: {SSH_KEY}")
    
    result = ssh_cmd("echo 'SSH OK'")
    if result and 'OK' in result:
        log('green', "✅ SSH-Verbindung OK")
        return True
    else:
        log('red', "❌ SSH-Verbindung fehlgeschlagen!")
        log('yellow', "   Tipps:")
        print("   1. Überprüfen Sie .env-Datei (SSH_KEY, SSH_USER, SSH_HOST)")
        print(f"   2. SSH-Key vorhanden? ls {SSH_KEY}")
        print("   3. Öffentlichen Key auf Pi registriert?")
        print(f"      ssh-copy-id -i {SSH_KEY}.pub {SSH_USER}@{SSH_HOST}")
        return False

def setup_remote_pi():
    """Richtet Remote Pi ein"""
    log('cyan', "\n📦 Richte Remote Pi ein...")
    
    # System aktualisieren
    log('yellow', "   [1/6] Aktualisiere Pakete...")
    ssh_cmd("sudo apt-get update -q")
    ssh_cmd("sudo apt-get upgrade -y -q")
    
    # Python-Pakete installieren
    log('yellow', "   [2/6] Installiere Python-Abhängigkeiten...")
    packages = [
        "python3-pip",
        "python3-venv",
        "python3-dev",
        "python3-paramiko",
        "python3-dotenv",
        "python3-picamera2",
        "python3-opencv",
        "python3-numpy",
        "python3-libcamera",
        "ffmpeg",
        "git",
        "nano",
    ]
    
    for pkg in packages:
        result = ssh_cmd(f"sudo apt-get install -y -q {pkg}")
        if result is not None:
            log('green', f"   ✓ {pkg}")
        else:
            log('yellow', f"   ⚠️  {pkg} (Installation fehlgeschlagen, wird übersprungen)")
    
    # Kamera-Tools prüfen
    log('yellow', "   [3/6] Prüfe Kamera-Tools...")
    rpicam_version = ssh_cmd("rpicam-hello --version 2>/dev/null")
    if rpicam_version:
        log('green', f"   ✓ rpicam-apps: {rpicam_version}")
    else:
        log('yellow', "   ⚠️  rpicam-apps nicht gefunden (wird übersprungen)")
    
    # FFmpeg prüfen
    log('yellow', "   [4/6] Prüfe FFmpeg...")
    ffmpeg_version = ssh_cmd("ffmpeg -version 2>/dev/null | head -1")
    if ffmpeg_version:
        log('green', f"   ✓ FFmpeg: {ffmpeg_version}")
    else:
        log('yellow', "   ⚠️  FFmpeg nicht gefunden")
    
    # YOLO installieren
    log('yellow', "   [5/6] Installiere YOLO...")
    ssh_cmd("pip install ultralytics --break-system-packages -q 2>/dev/null")
    log('green', "   ✓ YOLO installiert")
    
    # Repository klonen/updaten
    log('yellow', "   [6/6] Klone/Update Repository...")
    home = ssh_cmd("echo $HOME")
    if home:
        repo_path = f"{home}/vogel-kamera-linux"
        check_repo = ssh_cmd(f"test -d {repo_path} && echo 'exists' || echo 'missing'")
        
        if check_repo and 'exists' in check_repo:
            ssh_cmd(f"cd {repo_path} && git pull -q")
            log('green', "   ✓ Repository aktualisiert")
        else:
            ssh_cmd(f"cd {home} && git clone -q https://github.com/kamera-linux/vogel-kamera-linux.git")
            log('green', "   ✓ Repository geklont")
    
    log('green', "✅ Remote Pi Setup abgeschlossen")

def setup_local_client():
    """Richtet lokalen Client ein"""
    log('cyan', "\n📱 Richte lokalen Client ein...")
    
    client_dir = Path(__file__).parent.parent
    
    # Virtuelle Umgebung
    log('yellow', "   [1/3] Erstelle Virtuelle Umgebung...")
    venv_path = client_dir / 'venv'
    if not venv_path.exists():
        run_cmd(f"cd {client_dir} && python3 -m venv venv")
        log('green', "   ✓ Virtuelle Umgebung erstellt")
    else:
        log('yellow', "   ℹ️  Virtuelle Umgebung existiert bereits")
    
    # Abhängigkeiten installieren
    log('yellow', "   [2/3] Installiere Python-Abhängigkeiten...")
    python_exe = venv_path / 'bin' / 'python'
    pip_exe = venv_path / 'bin' / 'pip'
    
    run_cmd(f"{pip_exe} install -q --upgrade pip setuptools wheel")
    
    # Config-Anforderungen
    requirements_local = [
        "paramiko>=2.11.0",
        "click>=8.0.0",
        "python-dotenv>=0.19.0",
        "qrcode[pil]>=7.3.1",
    ]
    
    for req in requirements_local:
        run_cmd(f"{pip_exe} install -q '{req}'")
        log('green', f"   ✓ {req}")
    
    # Skripte ausführbar machen
    log('yellow', "   [3/3] Konfiguriere Skripte...")
    script_dir = client_dir / 'unified-monitor-client'
    for script in script_dir.glob('*.py'):
        if script.name.startswith('_'):
            continue
        run_cmd(f"chmod +x {script}")
    
    log('green', "   ✓ Skripte konfiguriert")
    log('green', "✅ Lokaler Client Setup abgeschlossen")

def verify_setup():
    """Verifiziert Setup"""
    log('cyan', "\n✔️  Verifiziere Setup...")
    
    # Remote Python-Test
    log('yellow', "   Teste Remote Python...")
    python_version = ssh_cmd("python3 --version")
    if python_version:
        log('green', f"   ✓ {python_version}")
    else:
        log('red', "   ❌ Python3 nicht gefunden")
        return False
    
    # Remote Module testen
    modules = ["paramiko", "dotenv", "cv2", "numpy"]
    log('yellow', "   Teste Remote Python-Module...")
    for module in modules:
        cmd = f"python3 -c 'import {module}' 2>/dev/null && echo 'OK' || echo 'MISSING'"
        result = ssh_cmd(cmd)
        if result and 'OK' in result:
            log('green', f"   ✓ {module}")
        else:
            log('yellow', f"   ⚠️  {module} (nicht kritisch)")
    
    # Local venv testen
    log('yellow', "   Teste lokales venv...")
    venv_path = Path(__file__).parent.parent / 'venv'
    python_local = venv_path / 'bin' / 'python'
    
    if python_local.exists():
        result = run_cmd(f"{python_local} --version")
        if result:
            log('green', f"   ✓ {result}")
        else:
            log('red', "   ❌ Lokales venv nicht funktionsfähig")
            return False
    else:
        log('red', "   ❌ Lokales venv nicht gefunden")
        return False
    
    log('green', "✅ Verifikation abgeschlossen")
    return True

def print_summary():
    """Zeigt Summary an"""
    log('cyan', "\n" + "="*70)
    log('cyan', "🎉 SETUP ABGESCHLOSSEN!")
    log('cyan', "="*70)
    
    print("\n📋 Nächste Schritte:\n")
    
    print("1️⃣  Starten Sie den Client (lokal):")
    print('   cd unified-monitor-client')
    print('   source ../venv/bin/activate')
    print('   python3 unified_monitor_client.py normal\n')
    
    print("2️⃣  Oder über Wrapper (vom Client-PC):")
    print('   cd auto-start-kamera')
    print('   ./start-unified-monitoring.sh\n')
    
    print("3️⃣  Test-Verbindung auf Remote Pi:")
    print(f'   ssh -i {SSH_KEY} {SSH_USER}@{SSH_HOST} "uname -a"\n')
    
    print("📚 Dokumentation:")
    print('   - unified-monitor-client/README.md')
    print('   - docs/ARCHITEKTUR.md')
    print('   - raspberry-pi-scripts/UNIFIED-MONITOR-README.md\n')

def uninstall_environment():
    """Deinstalliert alle Komponenten"""
    log('cyan', "\n" + "="*70)
    log('cyan', "🗑️  UNIFIED MONITOR CLIENT - Deinstallation")
    log('cyan', "="*70)
    
    # SSH-Verbindung testen
    if not test_ssh_connection():
        log('yellow', "⚠️  Kann Remote-Komponenten nicht löschen (SSH-Fehler)")
        response = input("\nWeitermachen und nur lokale Komponenten löschen? (ja/nein): ").strip().lower()
        if response not in ['ja', 'yes', 'y']:
            log('yellow', "Deinstallation abgebrochen.")
            return False
        remote_cleanup = False
    else:
        remote_cleanup = True
    
    # Bestätigung
    print("\n" + "="*70)
    log('yellow', "⚠️  WARNUNG - Dies wird folgende Daten LÖSCHEN:")
    print("   REMOTE (Raspberry Pi):")
    print("   • Python Virtual Environment und Abhängigkeiten")
    if remote_cleanup:
        print(f"   • Optional: Repository ({SSH_USER}@{SSH_HOST})")
    print("\n   LOKAL (Client-PC):")
    print("   • Python Virtual Environment (.venv)")
    print("   • Alle installierten Abhängigkeiten")
    print("   • NICHT gelöscht: .env und Konfigurationsdatei")
    print("="*70)
    
    response = input("\nSind Sie sicher? (ja/nein): ").strip().lower()
    if response not in ['ja', 'yes', 'y']:
        log('yellow', "Deinstallation abgebrochen.")
        return False
    
    # Remote Cleanup
    if remote_cleanup:
        log('cyan', "\n🗑️  Räume Remote Pi auf...")
        
        log('yellow', "   [1/2] Entferne venv und Abhängigkeiten...")
        home = ssh_cmd("echo $HOME")
        if home:
            # Entferne Remote venv
            ssh_cmd(f"rm -rf {home}/.local/lib/python3*/site-packages/paramiko* 2>/dev/null")
            ssh_cmd(f"rm -rf {home}/.local/lib/python3*/site-packages/dotenv* 2>/dev/null")
            ssh_cmd(f"pip uninstall -y ultralytics paramiko python-dotenv 2>/dev/null")
            log('green', "   ✓ Remote Dependencies entfernt")
        
        # Optional: Repository löschen
        log('yellow', "   [2/2] Frage nach Repository...")
        remove_repo = input(f"\n   Repository '{home}/vogel-kamera-linux' löschen? (ja/nein): ").strip().lower()
        if remove_repo in ['ja', 'yes', 'y']:
            ssh_cmd(f"rm -rf {home}/vogel-kamera-linux")
            log('green', "   ✓ Repository gelöscht")
        else:
            log('yellow', "   ℹ️  Repository behalten")
        
        log('green', "✅ Remote Cleanup abgeschlossen")
    
    # Lokales Cleanup
    log('cyan', "\n🗑️  Räume lokalen Client auf...")
    
    client_dir = Path(__file__).parent.parent
    venv_path = client_dir / 'venv'
    
    log('yellow', "   [1/2] Entferne venv...")
    if venv_path.exists():
        run_cmd(f"rm -rf {venv_path}", check=False)
        log('green', "   ✓ venv gelöscht")
    else:
        log('yellow', "   ℹ️  venv nicht gefunden")
    
    log('yellow', "   [2/2] Entferne Caches...")
    pycache_dirs = list(client_dir.rglob('__pycache__'))
    for pycache in pycache_dirs:
        run_cmd(f"rm -rf {pycache}", check=False)
    
    if pycache_dirs:
        log('green', f"   ✓ {len(pycache_dirs)} Caches gelöscht")
    else:
        log('yellow', "   ℹ️  Keine Caches gefunden")
    
    log('green', "✅ Lokales Cleanup abgeschlossen")
    
    # Summary
    log('cyan', "\n" + "="*70)
    log('green', "✨ Deinstallation abgeschlossen!")
    log('cyan', "="*70)
    
    print("\n📌 Noch vorhanden:")
    print("   • .env - Konfigurationsdatei (behalten für späteren Re-Setup)")
    print("   • Source-Code und Dokumentation")
    
    if remote_cleanup:
        print(f"   • Belieferungen auf {SSH_HOST}")
    
    print("\n🔄 Bei Bedarf neu installieren: ./setup_environment.sh\n")
    
    return True

def main():
    """Hauptprogramm"""
    # Argument Parser
    parser = argparse.ArgumentParser(
        description='Unified Monitor Client - Setup/Uninstall',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 setup_environment.py              # Installation
  python3 setup_environment.py --uninstall  # Deinstallation
  ./setup_environment.sh                    # Via Wrapper (empfohlen)
        """
    )
    parser.add_argument(
        '--uninstall', 
        action='store_true',
        help='Deinstalliert alle Komponenten (Remote + Lokal)'
    )
    
    args = parser.parse_args()
    
    # Uninstall-Modus
    if args.uninstall:
        try:
            if uninstall_environment():
                log('green', "\n✨ Deinstallation erfolgreich!")
                sys.exit(0)
            else:
                log('red', "\n❌ Deinstallation fehlgeschlagen")
                sys.exit(1)
        except KeyboardInterrupt:
            log('yellow', "\n\n⏹️  Deinstallation unterbrochen")
            sys.exit(1)
        except Exception as e:
            log('red', f"\n\n❌ Fehler: {e}")
            sys.exit(1)
    
    # Normal Setup-Modus
    log('blue', "\n" + "="*70)
    log('blue', "🐦 UNIFIED MONITOR CLIENT - Setup-Assistent")
    log('blue', "="*70)
    
    # SSH-Verbindung testen
    if not test_ssh_connection():
        sys.exit(1)
    
    # Bestätigung
    print("\n" + "="*70)
    log('yellow', "⚠️  Dieses Skript wird:")
    print("   • System-Pakete auf dem Remote Pi aktualisieren (apt-get)")
    print("   • Python-Abhängigkeiten installieren")
    print("   • Das Repository auf den Remote Pi klonen/updaten")
    print("   • Lokale venv und Dependencies installieren")
    print("="*70)
    
    response = input("\nMöchten Sie fortfahren? (ja/nein): ").strip().lower()
    if response not in ['ja', 'yes', 'y']:
        log('yellow', "Setup abgebrochen.")
        sys.exit(0)
    
    # Setup durchführen
    try:
        setup_remote_pi()
        setup_local_client()
        
        # Verifikation
        time.sleep(2)
        if verify_setup():
            print_summary()
            log('green', "\n✨ Setup erfolgreich abgeschlossen!")
        else:
            log('yellow', "\n⚠️  Setup teilweise erfolgreich, aber mit Fehlern")
            sys.exit(1)
    except KeyboardInterrupt:
        log('yellow', "\n\n⏹️  Setup unterbrochen")
        sys.exit(1)
    except Exception as e:
        log('red', f"\n\n❌ Fehler: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
