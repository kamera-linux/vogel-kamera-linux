#!/usr/bin/env python3
"""
Version-Check und Sync Test
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from version_manager import VersionManager

def main():
    print("\n" + "="*70)
    print("🔍 VERSION CHECK & SYNC TEST")
    print("="*70 + "\n")
    
    vm = VersionManager()
    
    # Check Versionen
    result = vm.compare_versions()
    
    if not result:
        print("\n⚠️  Version-Mismatch erkannt!")
        print("🔄 Synchronisiere Remote-Skripte...\n")
        
        # Synchronisiere
        sync_result = vm.sync_remote_scripts()
        
        if sync_result:
            print("\n🔄 Nach Sync - Überprüfe nochmal...\n")
            result = vm.compare_versions()
    
    print("\n" + "="*70)
    if result:
        print("✅ VERSION CHECK ERFOLGREICH - Alles ist konsistent!")
    else:
        print("❌ VERSION-MISMATCH - Überprüfe die Fehler oben")
    print("="*70 + "\n")
    
    return 0 if result else 1

if __name__ == '__main__':
    sys.exit(main())
