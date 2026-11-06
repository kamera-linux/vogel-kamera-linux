#!/usr/bin/env python3
"""
Test der vollständigen Git-Automatisierung
"""
import sys
from pathlib import Path

# Git-Automation importieren
sys.path.append(str(Path(__file__).parent))
from git_automation import SecureGitAutomation

def test_full_automation():
    """Teste vollständige Git-Automatisierung"""
    print("🚀 Test: Vollständige Git-Automatisierung")
    print("=" * 50)
    
    try:
        # SecureGitAutomation initialisieren
        automation = SecureGitAutomation()
        
        print("1️⃣  SSH-Agent Setup testen...")
        ssh_success, ssh_message = automation.setup_ssh_agent()
        print(f"   SSH-Setup: {ssh_message}")
        
        if not ssh_success:
            print("❌ SSH-Setup fehlgeschlagen - Abbruch")
            return False
        
        print("\n2️⃣  Git-Status prüfen...")
        status_success, status_output = automation.run_command("git status --porcelain")
        
        if status_success:
            if status_output.strip():
                print("   📝 Unversionierte Änderungen vorhanden:")
                for line in status_output.strip().split('\n')[:5]:  # Max 5 Zeilen
                    print(f"      {line}")
                if len(status_output.strip().split('\n')) > 5:
                    print("      ...")
            else:
                print("   ✅ Repository ist sauber (keine Änderungen)")
        else:
            print(f"   ❌ Git-Status Fehler: {status_output}")
            return False
        
        print("\n3️⃣  Remote-Verbindung testen...")
        remote_success, remote_output = automation.run_command("git remote -v")
        
        if remote_success and remote_output.strip():
            print("   📡 Git-Remotes:")
            for line in remote_output.strip().split('\n'):
                print(f"      {line}")
        else:
            print("   ⚠️  Keine Git-Remotes konfiguriert")
        
        print("\n4️⃣  SSH-Verbindung zu GitHub testen...")
        ssh_test_success, ssh_test_output = automation.run_command("ssh -T git@github.com")
        
        # SSH zu GitHub gibt immer exit code 1 zurück, aber mit erfolgreicher Nachricht
        if "successfully authenticated" in ssh_test_output:
            print("   ✅ SSH-Verbindung zu GitHub erfolgreich")
        else:
            print(f"   ❌ SSH-Verbindung Test: {ssh_test_output}")
            print("   ⚠️  Möglicherweise SSH-Key nicht zu GitHub hinzugefügt")
        
        print("\n📊 Test-Zusammenfassung:")
        print(f"✅ SSH-Agent Setup: {'OK' if ssh_success else 'FEHLER'}")
        print(f"✅ Git-Status: {'OK' if status_success else 'FEHLER'}")
        print(f"✅ Git-Remotes: {'OK' if remote_success else 'FEHLER'}")
        print(f"✅ SSH zu GitHub: {'OK' if 'successfully authenticated' in ssh_test_output else 'FEHLER'}")
        
        return ssh_success and status_success
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        return False

def test_push_dry_run():
    """Prüft den Push-Weg (SSH-Auth + Remote-Rechte) mit git push --dry-run.

    Es wird nichts committet und nichts auf den Server übertragen.
    """
    print("\n" + "=" * 50)
    print("🎯 Test: Push-Berechtigung (git push --dry-run)")
    print("=" * 50)

    try:
        automation = SecureGitAutomation()
        success, output = automation.run_command("git push --dry-run")
        if success:
            print("✅ Push wäre möglich – SSH-Auth und Schreibrechte OK")
            if output.strip():
                print(f"   {output.strip()}")
        else:
            print(f"❌ Push-Test fehlgeschlagen: {output}")
        return success
    except Exception as e:
        print(f"❌ Push-Test Fehler: {e}")
        return False

def main():
    """Haupttest-Funktion"""
    print("🔐 Git-Automatisierung Volltest")
    print("=" * 50)
    
    # Test 1: Vollständige Automatisierung
    automation_ok = test_full_automation()
    
    if automation_ok:
        # Test 2: Push-Weg prüfen (ohne echten Push)
        test_push_dry_run()
    else:
        print("\n❌ Grundlegende Tests fehlgeschlagen")
        print("Führe zuerst 'python3 setup_ssh_credentials.py' aus")

if __name__ == "__main__":
    main()