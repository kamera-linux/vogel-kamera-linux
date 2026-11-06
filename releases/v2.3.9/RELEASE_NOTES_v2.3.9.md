# 🔒 Release v2.3.9 - Sicherheit, Code-Struktur & CI

**Release Date:** 6. November 2026  
**Version:** 2.3.9  
**Vorgänger:** [v2.3.8](../v2.3.8/RELEASE_NOTES_v2.3.8.md)

---

## 📋 Übersicht

v2.3.9 bringt keine neuen Funktionen in der Web-GUI, sondern macht das System sicherer und
wartbarer: Das Login-Token steht nicht mehr in URLs, der Daemon ist in übersichtliche Module
aufgeteilt, und jede Änderung wird jetzt automatisch geprüft (Lint + Tests).

---

## 🔒 Sicherheit

### Login-Token nicht mehr in der URL

**Vorher:** Download und Live-Vorschau übergaben das 8 Stunden gültige JWT als
`?token=…` in der URL. URLs landen in Server-Logs, im Browser-Verlauf und ggf. in Proxys.

**Jetzt:** `/api/download` und `/api/snapshot` akzeptieren das Token nur noch im
`Authorization: Bearer …`-Header. Die Web-GUI holt beides per `fetch()` und schickt den
Header mit – für Nutzer ändert sich nichts.

> ⚠️ Eigene Skripte, die `?token=` verwenden, müssen auf den Header umgestellt werden.

---

## 🏗️ Code-Struktur

`pi_daemon_secure.py` (2400 Zeilen) ist jetzt das Paket `unified-monitor-client/pi_daemon/`:

| Modul | Inhalt |
|-------|--------|
| `config.py` | Umgebungsvariablen, Logging, Startprüfung |
| `runtime.py` | Gemeinsamer Zustand (`_lock`, `state`) |
| `settings.py` | Engine-, Detection-, Kamera- und Aufnahme-Einstellungen |
| `camera.py` | Detection-Prozess, Aufnahme, Konvertierung, Transfer, Watchdog |
| `api.py` | Flask-App: Login (Passwort + TOTP → JWT) und alle Routen |
| `hailo.py` | Hailo-NPU Hardware-Info |
| `monitoring.py` | Health-Cache, Gotify-Alerts, Thread-Diagnose |
| `sync.py` | Sync-Ziele (rsync) |
| `main.py` | Start: Threads + HTTPS-Server |

`pi_daemon_secure.py` bleibt als Startpunkt erhalten – Docker-Entrypoint und Health-Check
sind unverändert. Der Code wurde zeilengenau übernommen; alte und neue Version liefern auf
alle getesteten Endpunkte identische Antworten. Auf dem Pi getestet.

---

## ✅ CI & Tests

- Neuer Workflow [`ci.yml`](../../.github/workflows/ci.yml) bei jedem Push und Pull Request:
  - **ruff** (Syntaxfehler, undefinierte Namen, ungenutzte Imports)
  - **shellcheck** für alle Shell-Skripte
  - **28 pytest-Tests** für den pi-daemon – ohne Pi und ohne Kamera:
    Login (Passwort + TOTP), Rate-Limit, JWT (Signatur, Ablauf, `alg=none`),
    Path Traversal bei Download/Löschen, Einstellungen aus der API erreichen die Kamera
- YouTube-Statistik-Workflow: feste Paketversionen, bei blockiertem Push schlägt er sichtbar
  fehl statt täglich einen neuen Branch anzulegen
- GitHub Actions auf v7 (Node 24)

---

## 🔧 Bug Fixes

- **`scripts/release_workflow.py`:** GitHub-Release-Notes wurden mit wörtlichen `\n`
  angelegt und Backticks/`$` von der Shell interpretiert → jetzt `gh … --notes-file`.
  Standardversion kommt aus `VERSION` statt fest „2.1.2“.
- **Commit-Nachrichten** in `release_workflow.py` und `git_automation.py` werden sicher
  gequotet (Anführungszeichen brachen den Befehl ab).
- **`git-automation/test_full_automation.py`** konnte einen Test-Commit auf GitHub pushen
  und nahm ihn nur lokal zurück → prüft jetzt mit `git push --dry-run`.

---

## 📚 Dokumentation

- CHANGELOG zusammengeführt (`docs/CHANGELOG.md` entfällt); falsch datierte Alt-Einträge
  korrigiert, fehlende Einträge 1.3.2, 2.3.6 und 2.3.7 ergänzt
- git-automation: drei READMEs zu einer zusammengeführt, passend zum Code
- Audio-Upgrade-Doku aus dem Hauptverzeichnis ins Archiv [`releases/v2.3.4/`](../v2.3.4/)

---

## 🚀 Update

```bash
./ansible/build_and_deploy.sh --update
```

Das Image muss neu gebaut werden (neues Paket `pi_daemon/`). Alternativ funktioniert auch
`--hotpatch` – es kopiert jetzt `pi_daemon_secure.py`, `pi_daemon/` und `web/index.html`
in den laufenden Container.

Web-GUI und Daemon müssen zusammen aktualisiert werden (Token-Header), beides passiert
bei `--update` und `--hotpatch` automatisch. Danach Browser-Tab einmal neu laden.

---

## 📝 Commits

- `05e4fac` fix: Release-Workflow – GitHub-Release, Versionen, Aufräumen
- `015898a` ci: Lint (ruff, shellcheck) und Tests für pi-daemon
- `6afcf97` docs: Doku zusammengeführt und korrigiert
- `90268ec` ci: actions/checkout und setup-python auf v7 (Node 24)
- `3c6b821` docs: CHANGELOG-Eintrag v1.3.2, veraltete Tool-Doku korrigiert
- `e142e4e` fix(git-automation): Volltest pusht keinen Test-Commit mehr
- `60fbee0` ci(youtube): feste Paketversionen, kein täglicher Fallback-Branch
- `f7cb6e4` fix(pi-daemon): Login-Token nicht mehr in der URL
- `60467a7` chore: ansible-venv-local/ ausdrücklich in .gitignore
- `eb596e1` refactor(pi-daemon): pi_daemon_secure.py in Paket pi_daemon/ aufgeteilt
