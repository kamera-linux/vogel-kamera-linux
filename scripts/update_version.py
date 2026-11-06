#!/usr/bin/env python3
"""
Automatisches Version-Update mit Git-Automatisierung
Beispiel-Skript für die Verwendung der sicheren Git-Automation
"""
import sys

# Git-Automation importieren
sys.path.append('git-automation/')
from git_automation import SecureGitAutomation

def main():
    """Hauptfunktion für automatisches Version-Update"""
    print("🔐 Git-Automatisierung v1.1.4 - Version Update")
    print("=" * 50)
    
    try:
        # Automatisierung initialisieren
        automation = SecureGitAutomation()
        print("✅ Git-Automation erfolgreich initialisiert")
        
        # Git-Status prüfen
        success, output = automation.run_command("git status --porcelain")
        if output.strip():
            print("📝 Unversionierte Änderungen gefunden:")
            for line in output.strip().split('\n')[:5]:
                print(f"   {line}")
            
            # Dateien hinzufügen
            print("\n📦 Füge Dateien hinzu...")
            automation.run_command("git add .")
            
            # Commit erstellen
            commit_msg = input("💬 Commit-Nachricht eingeben: ") or "🔖 Automatisches Update v1.1.4"
            success, output = automation.run_command(f'git commit -m "{commit_msg}"')
            
            if success:
                print("✅ Commit erfolgreich erstellt")
                
                # Push durchführen
                push_choice = input("🚀 Änderungen pushen? (j/n): ").lower()
                if push_choice in ['j', 'ja', 'y', 'yes']:
                    success, output = automation.run_command("git push")
                    if success:
                        print("✅ Push erfolgreich!")
                        print("🎉 Git-Automatisierung abgeschlossen!")
                    else:
                        print(f"❌ Push fehlgeschlagen: {output}")
                else:
                    print("Push übersprungen")
            else:
                print(f"❌ Commit fehlgeschlagen: {output}")
        else:
            print("✅ Repository ist sauber (keine Änderungen)")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    main()