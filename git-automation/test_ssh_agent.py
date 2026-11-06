#!/usr/bin/env python3
"""
SSH-Agent Test-Skript zum Debuggen der automatischen Passphrase-Eingabe
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path

def test_ssh_methods():
    ssh_key = "/home/imme/.ssh/id_ed25519"
    passphrase = getpass.getpass("SSH-Passphrase eingeben: ")
    
    print("🔍 Teste verschiedene SSH-Agent-Methoden...\n")
    
    # Methode 1: SSH_ASKPASS
    print("1️⃣ Teste SSH_ASKPASS Methode...")
    success = test_askpass_method(ssh_key, passphrase)
    print(f"   Ergebnis: {'✅ Erfolgreich' if success else '❌ Fehlgeschlagen'}\n")
    
    # Methode 2: pexpect
    print("2️⃣ Teste pexpect Methode...")
    success = test_pexpect_method(ssh_key, passphrase)
    print(f"   Ergebnis: {'✅ Erfolgreich' if success else '❌ Fehlgeschlagen'}\n")
    
    # Methode 3: subprocess stdin
    print("3️⃣ Teste subprocess stdin Methode...")
    success = test_stdin_method(ssh_key, passphrase)
    print(f"   Ergebnis: {'✅ Erfolgreich' if success else '❌ Fehlgeschlagen'}\n")
    
    # SSH-Agent Status prüfen
    print("🔍 SSH-Agent Status nach Tests:")
    result = subprocess.run(['ssh-add', '-l'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Identitäten im Agent:\n{result.stdout}")
    else:
        print("❌ Keine Identitäten oder Agent nicht verfügbar")

def test_askpass_method(ssh_key, passphrase):
    try:
        # Temporäres askpass-Skript
        askpass_script = Path(".temp_test_askpass.sh")
        askpass_content = f'''#!/bin/bash
echo "{passphrase}"
'''
        
        with open(askpass_script, 'w') as f:
            f.write(askpass_content)
        os.chmod(askpass_script, 0o700)
        
        # SSH_ASKPASS Umgebung
        env = os.environ.copy()
        env.update({
            'SSH_ASKPASS': str(askpass_script.absolute()),
            'DISPLAY': '',  # Kein Display für askpass
            'SSH_ASKPASS_REQUIRE': 'force'
        })
        
        # SSH-Key hinzufügen
        result = subprocess.run(
            ['ssh-add', ssh_key],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Aufräumen
        if askpass_script.exists():
            askpass_script.unlink()
        
        print(f"   ssh-add stdout: {result.stdout}")
        if result.stderr:
            print(f"   ssh-add stderr: {result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"   Fehler: {e}")
        return False

def test_pexpect_method(ssh_key, passphrase):
    try:
        import pexpect
        
        # ssh-add mit pexpect
        child = pexpect.spawn(f'ssh-add {ssh_key}')
        child.logfile = sys.stdout.buffer  # Debug-Output
        
        index = child.expect(['Enter passphrase.*:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        
        if index == 0:  # Passphrase-Prompt erkannt
            child.sendline(passphrase)
            child.expect(pexpect.EOF, timeout=10)
            child.close()
            return child.exitstatus == 0
        else:
            print("   Unerwartete Ausgabe oder Timeout")
            return False
            
    except ImportError:
        print("   pexpect nicht verfügbar")
        return False
    except Exception as e:
        print(f"   Fehler: {e}")
        return False

def test_stdin_method(ssh_key, passphrase):
    try:
        # ssh-add mit stdin
        process = subprocess.Popen(
            ['ssh-add', ssh_key],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=passphrase + '\n', timeout=30)
        
        print(f"   stdout: {stdout}")
        if stderr:
            print(f"   stderr: {stderr}")
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"   Fehler: {e}")
        return False

if __name__ == "__main__":
    print("🔐 SSH-Agent Test-Suite")
    print("=" * 40)
    
    # SSH-Agent Status prüfen
    result = subprocess.run(['ssh-add', '-l'], capture_output=True, text=True)
    if result.returncode != 0 and "no identities" in result.stderr.lower():
        print("📋 SSH-Agent läuft, aber keine Identitäten geladen")
    elif result.returncode != 0:
        print("❌ SSH-Agent nicht verfügbar oder nicht gestartet")
        print("💡 Starten Sie den SSH-Agent mit: eval $(ssh-agent)")
        sys.exit(1)
    else:
        print("✅ SSH-Agent bereits mit Identitäten konfiguriert")
        print(f"   Aktuelle Identitäten:\n{result.stdout}")
    
    print("\n" + "=" * 40)
    test_ssh_methods()