# 🔐 Git-Automatisierung

Git-Operationen (Commit, Push, Tag, Release) mit verschlüsselt gespeicherter
SSH-Passphrase. Die Passphrase wird mit einem Master-Passwort geschützt und beim
Start automatisch in einen SSH-Agent geladen.

Wird auch von [`scripts/release_workflow.py`](../scripts/release_workflow.py) verwendet.

## 📁 Dateien

| Datei | Zweck |
|-------|-------|
| `git_automation.py` | Klasse `SecureGitAutomation` + Kommandozeilen-Interface |
| `setup_ssh_credentials.py` | Einmalige Einrichtung der verschlüsselten Secrets |
| `test_ssh_agent.py` | Debug-Test der einzelnen SSH-Agent-Methoden |
| `test_ssh_automation.py` | Test: SSH-Agent mit gespeicherten Secrets |
| `test_full_automation.py` | Integrationstest: legt einen Test-Commit an und nimmt ihn lokal zurück (siehe Warnung unten) |
| `git_automation_requirements.txt` | Python-Abhängigkeiten (`cryptography`, `pexpect`) |
| `.git_secrets_encrypted.json` | Verschlüsselte Secrets – wird beim Setup erzeugt, **nicht committen** (steht in `.gitignore`) |

## 🚀 Einrichtung

```bash
pip install -r git-automation/git_automation_requirements.txt
python3 git-automation/setup_ssh_credentials.py
```

Das Setup fragt nach SSH-Key (wird automatisch gesucht), SSH-Passphrase,
Git-Name/E-Mail und einem Master-Passwort für die Verschlüsselung.

Testen:

```bash
python3 git-automation/test_ssh_automation.py   # nur SSH-Agent
python3 git-automation/test_full_automation.py  # kompletter Ablauf
```

> ⚠️ `test_full_automation.py` fragt, ob der Test-Commit gepusht werden soll.
> Mit **n** antworten: Der Commit wird danach nur lokal zurückgenommen – ein
> gepushter Test-Commit (`automation_test.txt`) bliebe auf GitHub.

## 💡 Verwendung

### Kommandozeile

Alle Befehle laufen im Repository-Root, egal von wo aus das Skript gestartet wird.
Das Master-Passwort wird beim Start einmal abgefragt.

```bash
python3 git-automation/git_automation.py --status
python3 git-automation/git_automation.py --commit "Fix: Beschreibung"   # add + commit + push
python3 git-automation/git_automation.py --push                         # aktuellen Branch pushen
python3 git-automation/git_automation.py --push-all                     # alle Branches pushen
python3 git-automation/git_automation.py --tag v2.3.9                   # Tag erstellen + pushen
python3 git-automation/git_automation.py --release v2.3.9               # commit + push + Tag
```

| Option | Wirkung |
|--------|---------|
| `--branch NAME` | Vorher auf diesen Branch wechseln (bei `--commit`, `--release`, `--push`) |
| `--no-push` | Nur lokal committen/taggen |
| `--force` | Force-Push (bei `--push` / `--push-all`) – mit Vorsicht |

> ⚠️ `--commit` und `--release` führen `git add .` aus, nehmen also **alle**
> Änderungen im Repository mit.

### Als Python-Modul

```python
import sys
sys.path.append("git-automation/")
from git_automation import SecureGitAutomation

automation = SecureGitAutomation()          # fragt Master-Passwort ab
success, output = automation.run_command("git status")
```

`run_command` führt den Befehl über die Shell aus. Variable Teile (z. B.
Commit-Nachrichten) deshalb mit `shlex.quote()` absichern.

## 🛡️ Sicherheit

- **AES-256-CBC**, Schlüssel per **PBKDF2-SHA256** (100.000 Iterationen) aus dem
  Master-Passwort abgeleitet; zufälliger Salt und IV pro Wert
- Verschlüsselt wird nur die SSH-Passphrase; Key-Pfad und Git-Name/E-Mail stehen im Klartext
- Master-Passwort wird **nicht** gespeichert – ohne es sind die Secrets unbrauchbar
- Passphrase wird über drei Methoden in den SSH-Agent geladen (der Reihe nach):
  `pexpect` → `SSH_ASKPASS` → stdin
- Git-Befehle haben ein Timeout von 5 Minuten

Aufbau von `.git_secrets_encrypted.json`:

```json
{
  "version": "1.0",
  "encryption": "AES-256-CBC-PBKDF2",
  "encrypted_secrets": {
    "ssh_passphrase": { "encrypted_data": "…", "salt": "…", "iv": "…" },
    "ssh_key_path": "~/.ssh/…",
    "git_name": "…",
    "git_email": "…"
  }
}
```

## 🔍 Fehlersuche

```bash
ssh-add -l              # Welche Keys sind im Agent?
ssh -T git@github.com   # Verbindung zu GitHub testen
echo $SSH_AUTH_SOCK     # Läuft ein Agent?
python3 git-automation/test_ssh_agent.py   # einzelne Agent-Methoden testen
```
