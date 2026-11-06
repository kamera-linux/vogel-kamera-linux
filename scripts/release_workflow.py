#!/usr/bin/env python3
"""
Vollständiger Release-Workflow mit Git-Automatisierung
Erstellt Branches, Tags und führt kompletten Release-Prozess durch

Version History:
- v2.1.2: Sichere Konfiguration, Datenschutz, dynamische SSH-Pfade
- v2.1.1: Graceful Shutdown & Process Management, Detect-and-Record Mode
- v2.1.0: Audio/Video-Synchronisation, rpicam-vid Integration
- v2.0.2: YOLO26 Migration, Trixie Support
- v2.0.1: rpicam-vid Integration
"""
import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Git-Automation importieren (unabhängig vom aktuellen Arbeitsverzeichnis)
sys.path.append(str(REPO_ROOT / 'git-automation'))
from git_automation import SecureGitAutomation


def read_current_version():
    """Liest die aktuelle Version aus der VERSION-Datei im Repo-Root"""
    try:
        return (REPO_ROOT / 'VERSION').read_text().strip()
    except OSError:
        return None


def complete_release_workflow(version):
    """Vollständiger Release-Workflow"""
    print(f"🚀 Vollständiger Release-Workflow für v{version}")
    print("=" * 60)
    
    try:
        automation = SecureGitAutomation()
        print("✅ Git-Automation erfolgreich initialisiert")
        
        # 1. Aktuellen Branch prüfen
        success, current_branch = automation.run_command("git branch --show-current")
        print(f"📍 Aktueller Branch: {current_branch}")
        
        # 2. Status prüfen
        success, status = automation.run_command("git status --porcelain")
        if status.strip():
            print("📝 Unversionierte Änderungen gefunden:")
            for line in status.strip().split('\n')[:5]:
                print(f"   {line}")
                
            # Änderungen hinzufügen
            print("\n📦 Füge alle Änderungen hinzu...")
            automation.run_command("git add .")
            
            # Commit für die Version
            commit_msg = f"🔖 Release v{version}"
            success, output = automation.run_command(f'git commit -m {shlex.quote(commit_msg)}')
            
            if success:
                print(f"✅ Commit erstellt: {commit_msg}")
            else:
                print(f"❌ Commit fehlgeschlagen: {output}")
                return False
        else:
            print("✅ Repository ist sauber")
        
        # 3. Push aktuellen Branch
        print(f"\n🚀 Push {current_branch} Branch...")
        success, output = automation.run_command(f"git push origin {current_branch}")
        if success:
            print(f"✅ {current_branch} Branch gepusht")
        else:
            print(f"❌ Push fehlgeschlagen: {output}")
            return False
        
        # 4. Tag erstellen
        print(f"\n🏷️ Erstelle Tag v{version}...")
        success, output = automation.run_command(f"git tag -a v{version} -m 'Release v{version}'")
        if success:
            print(f"✅ Tag v{version} erstellt")
        else:
            print(f"❌ Tag-Erstellung fehlgeschlagen: {output}")
            # Tag könnte bereits existieren - prüfen
            success, existing = automation.run_command(f"git tag -l v{version}")
            if existing.strip():
                print(f"ℹ️ Tag v{version} existiert bereits")
            else:
                return False
        
        # 5. Tag pushen
        print(f"\n📤 Push Tag v{version}...")
        success, output = automation.run_command(f"git push origin v{version}")
        if success:
            print(f"✅ Tag v{version} gepusht")
        else:
            print(f"❌ Tag-Push fehlgeschlagen: {output}")
            return False
        
        # 6. Merge zu main (falls wir auf devel sind)
        if current_branch == "devel":
            merge_choice = input(f"\n🔄 Merge {current_branch} → main? (j/n): ").lower()
            if merge_choice in ['j', 'ja', 'y', 'yes']:
                
                # Zu main wechseln
                print("🔄 Wechsle zu main Branch...")
                success, output = automation.run_command("git checkout main")
                if not success:
                    print(f"❌ Checkout main fehlgeschlagen: {output}")
                    return False
                
                # main pullen
                print("⬇️ Pull latest main...")
                automation.run_command("git pull origin main")
                
                # devel mergen
                print(f"🔄 Merge {current_branch} → main...")
                success, output = automation.run_command(f"git merge {current_branch}")
                if success:
                    print("✅ Merge erfolgreich")
                    
                    # main pushen
                    print("🚀 Push main...")
                    success, output = automation.run_command("git push origin main")
                    if success:
                        print("✅ main Branch gepusht")
                    else:
                        print(f"❌ main Push fehlgeschlagen: {output}")
                        return False
                else:
                    print(f"❌ Merge fehlgeschlagen: {output}")
                    return False
                
                # Zurück zu original branch
                print(f"🔄 Wechsle zurück zu {current_branch}...")
                automation.run_command(f"git checkout {current_branch}")
        
        print(f"\n🎉 Vollständiger Release v{version} abgeschlossen!")
        print(f"✅ Branch {current_branch} gepusht")
        print(f"✅ Tag v{version} erstellt und gepusht")
        if current_branch == "devel":
            print("✅ Merge zu main durchgeführt")
        
        # GitHub Release mit Notes erstellen
        print("\n" + "=" * 60)
        create_github_release(version)
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler im Release-Workflow: {e}")
        return False

def create_github_release(version):
    """Erstellt automatisch GitHub Release mit Release-Notes"""
    print(f"\n🚀 GitHub Release v{version} erstellen...")
    print("=" * 50)
    
    def gh(*args):
        # Ohne Shell aufrufen: Notes-Inhalt (Backticks, $, Anführungszeichen)
        # wird so weder interpretiert noch verfälscht.
        result = subprocess.run(['gh', *args], cwd=REPO_ROOT,
                                capture_output=True, text=True)
        return result.returncode == 0, (result.stdout + result.stderr).strip()

    try:
        tag = f"v{version}"

        # Release-Notes Datei suchen
        release_notes_file = REPO_ROOT / "releases" / tag / f"RELEASE_NOTES_{tag}.md"

        if release_notes_file.exists():
            print(f"✅ Release-Notes gefunden: {release_notes_file.relative_to(REPO_ROOT)}")
            notes_args = ['--notes-file', str(release_notes_file)]
        else:
            print(f"⚠️ Release-Notes nicht gefunden: {release_notes_file.relative_to(REPO_ROOT)}")
            print("   Erstelle Release ohne Notes...")
            notes_args = ['--notes', f"## {tag}\n\nSiehe CHANGELOG.md für Details."]

        # GitHub Release erstellen mit gh CLI
        print(f"\n📤 Erstelle GitHub Release für Tag {tag}...")
        success, output = gh('release', 'create', tag, '--title', tag, *notes_args)

        if success:
            print(f"✅ GitHub Release {tag} erstellt!")
            print(f"   🔗 https://github.com/kamera-linux/vogel-kamera-linux/releases/tag/{tag}")
        else:
            # Release könnte bereits existieren
            if "already exists" in output:
                print(f"ℹ️ Release {tag} existiert bereits")
                # Versuche zu updaten
                success, output = gh('release', 'edit', tag, *notes_args)
                if success:
                    print("✅ Release-Notes aktualisiert!")
                else:
                    print(f"⚠️ Konnte Release-Notes nicht aktualisieren: {output}")
            else:
                print(f"❌ Release-Erstellung fehlgeschlagen: {output}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Release erstellen: {e}")
        return False

def simple_commit_and_push():
    """Einfacher Commit und Push ohne Release-Features"""
    print("📝 Einfacher Commit & Push")
    print("=" * 30)
    
    try:
        automation = SecureGitAutomation()
        
        # Status prüfen
        success, status = automation.run_command("git status --porcelain")
        if not status.strip():
            print("✅ Keine Änderungen vorhanden")
            return
        
        print("📝 Änderungen gefunden:")
        for line in status.strip().split('\n')[:5]:
            print(f"   {line}")
        
        # Add und Commit
        automation.run_command("git add .")
        
        commit_msg = input("💬 Commit-Nachricht: ") or "🔄 Automatisches Update"
        success, output = automation.run_command(f'git commit -m {shlex.quote(commit_msg)}')
        
        if success:
            print("✅ Commit erstellt")
            
            # Push
            success, output = automation.run_command("git push")
            if success:
                print("✅ Push erfolgreich!")
            else:
                print(f"❌ Push fehlgeschlagen: {output}")
        else:
            print(f"❌ Commit fehlgeschlagen: {output}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

def main():
    """Hauptmenü für Git-Automatisierung"""
    current_version = read_current_version()
    print(f"🔐 Git-Automatisierung (aktuelle Version: {current_version or 'unbekannt'})")
    print("=" * 50)
    print("1️⃣ Vollständiger Release-Workflow (mit Tags & Branches)")
    print("2️⃣ Einfacher Commit & Push")
    print("3️⃣ Nur Status anzeigen")
    print("4️⃣ GitHub Release mit Notes erstellen (Tag bereits vorhanden)")
    
    choice = input("\nWahl (1-4): ").strip()
    
    if choice == "1":
        default = f" (Standard: {current_version})" if current_version else ""
        version = input(f"Version eingeben{default}: ").strip() or current_version
        if version:
            complete_release_workflow(version)
        else:
            print("❌ Version erforderlich")
    elif choice == "2":
        simple_commit_and_push()
    elif choice == "3":
        automation = SecureGitAutomation()
        success, output = automation.run_command("git status")
        print(f"\n📊 Git Status:\n{output}")
    elif choice == "4":
        default = f" (Standard: {current_version})" if current_version else ""
        version = input(f"Version eingeben{default}: ").strip() or current_version
        if version:
            create_github_release(version)
        else:
            print("❌ Version erforderlich")
    else:
        print("❌ Ungültige Wahl")

if __name__ == "__main__":
    main()