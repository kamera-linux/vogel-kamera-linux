# 🤖 Git Automation für Vogel-Kamera-Linux

Automatisches Python-Skript für Git-Operationen mit SSH-Secret-Management.

## 🚀 Features

- ✅ **Automatische Branch-Synchronisation** (main, devel)
- ✅ **Tag-Updates** für alle Versionen
- ✅ **SSH-Secret-Management** mit verschlüsselten Passphrases
- ✅ **Batch-Commits** mit automatischen Push-Operationen
- ✅ **Sichere Konfiguration** über .gitignore-geschützte Dateien

## 📋 Installation & Setup

### 1. **Abhängigkeiten installieren:**
```bash
# Python-Verschlüsselungs-Bibliothek
pip install -r git_automation_requirements.txt

# System-Tools
sudo apt install expect
```

### 2. **Verschlüsselte Secrets erstellen:**
```bash
# Interaktive Einrichtung mit Master-Password
python3 git_automation.py --setup

# Das Skript fragt ab:
# - Master-Password (wird NICHT gespeichert!)
# - SSH-Key-Pfad
# - SSH-Passphrase (wird verschlüsselt)
# - Git-User-Daten
```

### 3. **Secrets aktualisieren:**
```bash
# SSH-Passphrase ändern
python3 git_automation.py --update-secret ssh_passphrase

# Master-Password wird dabei abgefragt
```

## 🎯 Verwendung

### **Git-Status anzeigen:**
```bash
python3 git_automation.py --status
```

### **Aktuellen Branch pushen:**
```bash
python3 git_automation.py --push
```

### **Spezifischen Branch pushen:**
```bash
python3 git_automation.py --push --branch devel-v1.2.0
```

### **Alle Branches pushen:**
```bash
python3 git_automation.py --push-all
```

### **Tag erstellen und pushen:**
```bash
python3 git_automation.py --tag v1.1.4
```

### **Committen mit Nachricht:**
```bash
# Auf aktuellem Branch
python3 git_automation.py --commit "🔧 Feature: Neue Funktionalität hinzugefügt"

# Auf spezifischem Branch
python3 git_automation.py --commit "✨ Feature" --branch devel-v1.2.0
```

### **Vollständiger Release-Workflow:**
```bash
# Auf aktuellem Branch
python3 git_automation.py --release v1.1.4

# Auf spezifischem Branch
python3 git_automation.py --release v1.2.0 --branch devel-v1.2.0
```

### **Nur lokale Operationen (ohne Push):**
```bash
python3 git_automation.py --commit "Test" --no-push
```

## 🔐 Sicherheit

### **Geschützte Dateien (.gitignore):**
```
git_automation.py      # Das Skript selbst
.git_secrets.json      # SSH-Secrets und Konfiguration
.ssh_secrets.json      # Alternative Secrets-Datei
```

### **SSH-Agent Integration:**
- ✅ **Automatische SSH-Agent-Konfiguration** beim Start
- ✅ **Passphrase-Handling** über pexpect (keine manuelle Eingabe!)
- ✅ **Timeout-Schutz** für lange Operationen (5 Minuten)
- ✅ **Drei Fallback-Methoden**: pexpect → SSH_ASKPASS → stdin

## ⚙️ Funktionen im Detail

### **Branch-Synchronisation:**
1. Checkout zu jedem konfigurierten Branch
2. Pull latest changes von origin
3. Automatischer Push (wenn aktiviert)
4. Fehlerbehandlung und Logging

### **Tag-Management:**
1. Alle Version-Tags abrufen (v*)
2. Tags löschen und neu erstellen auf main Branch
3. Force-Push der aktualisierten Tags
4. Zeitstempel-basierte Tag-Messages

### **Commit-Automation:**
1. Alle Änderungen staged (git add -A)
2. Commit mit benutzerdefinierten/automatischen Messages
3. Push zum entsprechenden Remote-Branch
4. Status-Feedback für alle Operationen

## 🛠️ Abhängigkeiten

```bash
# System-Abhängigkeiten
sudo apt install expect  # Für automatische Passphrase-Eingabe

# Python-Abhängigkeiten
pip install -r git_automation_requirements.txt
# Enthält: cryptography>=41.0.0 für AES-256-Verschlüsselung

# Python-Module
import subprocess, json, os, sys, base64, hashlib, getpass
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
```

## 🔐 Verschlüsselungs-Features

### **AES-256-CBC Verschlüsselung:**
- ✅ **SSH-Passphrases** niemals im Klartext gespeichert
- ✅ **PBKDF2** mit 100.000 Iterationen (OWASP-Standard)
- ✅ **Zufällige Salts und IVs** für jede Verschlüsselung
- ✅ **Master-Password** für Zugriff auf alle Secrets

### **Sichere Speicherung:**
```json
{
  "version": "1.0",
  "encryption": "AES-256-CBC-PBKDF2",
  "encrypted_secrets": {
    "ssh_passphrase": {
      "encrypted_data": "base64-verschlüsselte-daten",
      "salt": "base64-salt",
      "iv": "base64-iv",
      "algorithm": "AES-256-CBC-PBKDF2"
    }
  }
}
```

### **Memory Security:**
- ✅ **Automatische Speicher-Bereinigung** nach Verwendung
- ✅ **Temporäre Dateien** werden sicher gelöscht
- ✅ **Passphrase-Überschreibung** im RAM

## 📊 Beispiel-Workflows

### **Workflow 1: Feature auf Development-Branch**
```bash
# 1. Git-Status überprüfen
python3 git_automation.py --status

# 2. Auf devel-v1.2.0 Branch committen
python3 git_automation.py --commit "✨ Feature: Zeitlupen-Modus" --branch devel-v1.2.0

# 3. Spezifischen Branch pushen
python3 git_automation.py --push --branch devel-v1.2.0
```

### **Workflow 2: Release auf spezifischem Branch**
```bash
# 1. Vollständiger Release auf devel-v1.2.0
python3 git_automation.py --release v1.2.0 --branch devel-v1.2.0

# 2. Tag für Version erstellen
python3 git_automation.py --tag v1.2.0

# 3. Oder alles pushen
python3 git_automation.py --push-all
```

### **Workflow 3: Multi-Branch Development**
```bash
# Feature auf Development-Branch
python3 git_automation.py --commit "✨ Neue Feature" --branch devel-v1.2.0

# Bugfix auf Main-Branch
python3 git_automation.py --commit "🐛 Bugfix" --branch main

# Kompletter Release
python3 git_automation.py --release v1.2.0 --branch devel-v1.2.0
```

## ⚠️ Wichtige Hinweise

### **Sicherheit:**
- ❌ **NIEMALS** `.git_secrets.json` committen oder teilen
- ❌ **NIEMALS** das Skript mit Secrets öffentlich machen
- ✅ Verwenden Sie starke SSH-Passphrases
- ✅ Regelmäßige Rotation der SSH-Keys

### **Backup:**
- 💾 Lokale Backups der Secrets-Datei anlegen
- 🔄 Regelmäßige Überprüfung der Git-Remote-Verbindungen
- 📋 Logging für Troubleshooting aktivieren

### **Fehlerbehandlung:**
- 🕐 5-Minuten Timeout für alle Git-Operationen
- 🔄 Automatische Retry-Logik bei Netzwerkfehlern
- 📝 Detaillierte Error-Messages für Debugging

---

**💡 Tipp:** Führen Sie zuerst `--setup` aus, konfigurieren Sie die Secrets, und testen Sie dann mit `--branches` vor der vollständigen `--sync` Operation.