# 🔍 Security-Audit November 2026

**Datum:** 7. November 2026  
**Version:** v2.4.0 (Audit) → behoben in v2.4.1  
**Umfang:** pi-daemon (API, Web-GUI, Prozessaufrufe), Docker/Compose, Ansible-Rollen,
CI-Workflows, Repository/Git-History und das laufende System auf dem Raspberry Pi
**Methode:** Code-Review, Prüfung des laufenden Pi (Dateirechte, sshd, Firewall, offene Ports,
Paketversionen), Tests gegen die laufende API, Suche nach Secrets in Repo und History

---

## Zusammenfassung

| Schwere | Gefunden | Behoben | Akzeptiert |
|---------|---------:|--------:|-----------:|
| 🟠 Hoch | 2 | 2 | – |
| 🟡 Mittel | 5 | 5 | – |
| 🟢 Niedrig | 7 | 6 | 1 |
| ℹ️ Hinweis | 6 | – | 6 |

**Keine** Lücke war ohne Login ausnutzbar. Die beiden „hohen“ Funde setzen entweder ein
gültiges Login oder einen lokalen Benutzer auf dem Pi voraus – sie führten dann aber zu
Befehlsausführung als root.

Positiv: Login mit bcrypt + TOTP und Rate-Limit, JWT nur im Header, Path-Traversal-Schutz,
alle API-Routen außer Login/Health geschützt, Secrets verschlüsselt per ansible-vault,
keine Secrets in Repo oder Git-History, CI mit minimalen Workflow-Rechten.

---

## Funde

### 🟠 H1 – Befehlsausführung über Sync-Ziele (Option-Injection in ssh/rsync)

**Wo:** `api.py` (`/api/settings/targets`, `/api/settings/test`), `camera.py` (`transfer_all`)  
**Problem:** Host, Benutzer und Pfad eines Sync-Ziels wurden ungeprüft als `user@host:path`
an `ssh` und `rsync` übergeben, ohne `--` als Trenner. Ein Benutzername wie
`-oProxyCommand=…` oder ein Pfad wie `-e sh -c …` hätte einen beliebigen Befehl
**als root im privilegierten Container** (= root auf dem Pi) ausgeführt.  
**Voraussetzung:** gültiges Login.  
**Fix:** `sync.validate_target()` erlaubt nur Hostnamen/IPs, POSIX-Benutzernamen und Pfade
ohne Leer-/Shell-Zeichen und ohne führendes `-`. Prüfung beim Speichern (HTTP 400) und vor
jedem Transfer (ungültige Altziele werden übersprungen und geloggt). `ssh … -- user@host` und
`rsync … -- quelle ziel`. Hochgeladene SSH-Keys werden auf Format und Größe geprüft.

### 🟠 H2 – Konfigurationsverzeichnis für alle beschreibbar

**Wo:** `/etc/pi-daemon` auf dem Pi (Ansible-Rolle `pi-daemon`: `mode: 0757`)  
**Problem:** Jeder lokale Benutzer konnte Dateien anlegen, ersetzen oder löschen – auch
`app.env` (Secrets) und `sync-config.json`. Zusammen mit H1 wäre das root-Zugriff gewesen.  
**Voraussetzung:** lokaler Benutzer auf dem Pi.  
**Fix:** `0750 root:roimme` (der Container läuft als root und braucht kein Schreibrecht für
andere). Neue Rolle `hardening` setzt das bei jedem `--update`.

### 🟡 M1 – Keine Host-Key-Prüfung bei Video-Übertragung

**Wo:** `camera.py`, `api.py` – `StrictHostKeyChecking=no`, `UserKnownHostsFile=/dev/null`  
**Problem:** Ein Angreifer im Netz konnte sich als Sync-Ziel ausgeben (Man-in-the-Middle)
und Videos abgreifen.  
**Fix:** `StrictHostKeyChecking=accept-new` mit `/etc/pi-daemon/known_hosts`: Der Host-Key
wird beim ersten Kontakt gespeichert, ein späterer Wechsel wird abgelehnt.

### 🟡 M2 – SSH-Passwort-Login bei sudo ohne Passwort

**Wo:** sshd auf dem Pi (`PasswordAuthentication yes`, `PermitRootLogin without-password`)  
**Problem:** `roimme` hat sudo ohne Passwort (Raspberry-Pi-OS-Standard). Ein erratenes
Passwort hätte direkt root bedeutet.  
**Fix:** `/etc/ssh/sshd_config.d/10-vogel-kamera.conf`: nur Schlüssel, kein root-Login
(abschaltbar mit `pi_ssh_hardening: false`). Vorher geprüft: Login per Key funktioniert,
keine anderen sshd-Drop-ins, `sshd -t` vor dem Neuladen.

### 🟡 M3 – Privater TLS-Schlüssel für alle lesbar

**Wo:** `/etc/pi-daemon/certs/key.pem` (`0644`, Verzeichnis gehörte `roimme`)  
**Fix:** `key.pem` `0640 root:roimme`, Verzeichnis `0750 root:roimme`. Die Rolle `ssl` setzte
die Rechte vorher nur beim ersten Erzeugen – jetzt immer.

### 🟡 M4 – Abhängigkeiten ohne feste Versionen

**Wo:** `requirements_daemon.txt` (`>=`), zusätzlich `--extra-index-url` für PyTorch  
**Problem:** Jeder Build zog die neueste Version. Bei `ultralytics` gab es im Dezember 2024
kompromittierte Releases (Krypto-Miner) – so etwas wäre ungeprüft im Image gelandet.  
**Fix:** Alle Pakete auf die im Container laufenden Versionen festgelegt (`==`);
Test-Abhängigkeiten ebenso.

### 🟡 M5 – Hinweis auf nicht vorhandene Meldewege / falsche SECURITY.md

**Wo:** `docs/SECURITY.md`  
**Problem:** Beschrieb v2.2.x als aktuell, eine Architektur „ohne Netzwerk“, Port 8888 und
MediaMTX, empfahl falsche Befehle (`ssh-keygen -t ed25519 -b 4096`, `PasswordAuthentication`
in `~/.ssh/config`). Der verlinkte „Private Vulnerability Report“ ist auf GitHub **deaktiviert**.  
**Fix:** SECURITY.md neu geschrieben (aktuelle Architektur, Schutzmaßnahmen, akzeptierte
Risiken, Betriebsempfehlungen). **Offen:** Private Vulnerability Reporting muss in den
GitHub-Einstellungen aktiviert werden (siehe unten).

### 🟢 L1 – HTML-Escaping unvollständig (XSS über Dateinamen)

**Wo:** `web/index.html` – `escHtml()` maskierte `'` nicht; Download/Löschen-Buttons setzten
Dateinamen in `onclick="…('…')"`. Ein Dateiname mit `\'` hätte JavaScript ausführen können.
Die Anzeige „Objekt erkannt“ setzte Werte ungeprüft per `innerHTML`.  
**Voraussetzung:** präparierte Datei im Video-Verzeichnis.  
**Fix:** `escHtml()` maskiert `'`; Pfade stehen in `data-path`, der Handler liest
`this.dataset.path`; Detektionswerte werden maskiert.

### 🟢 L2 – Keine Security-Header

**Fix:** `Content-Security-Policy` (nur eigene Quellen, keine Frames, kein `eval`),
`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
`Permissions-Policy`, `Cache-Control: no-store` für `/api/*`.

### 🟢 L3 – SSH-Key kurzzeitig mit Standardrechten

**Wo:** `api.py` – `write_text()` und danach `chmod 600`  
**Fix:** `sync.write_private_key()` legt die Datei direkt mit `0600` an.

### 🟢 L4 – Ungültige Zahlen führten zu HTTP 500

**Wo:** `int(data.get(...))` bei Dauer, FPS, Bitrate, `target_id`  
**Fix:** `_int_arg()` – ungültige Werte werden zum Standardwert. Unbekannte Auflösungen → 400.

### 🟢 L5 – Video-Verzeichnis für alle beschreibbar

**Wo:** `~/Videos` (`0777` laut Rolle `pi-daemon`)  
**Fix:** `0755` (Container schreibt als root).

### 🟢 L6 – Veraltete offene Firewall-Regeln

**Wo:** UFW erlaubte 8554 (RTSP aus v1.x) und 5201 (iperf3) – dort lauschte nichts mehr.  
**Fix:** Regeln entfernt (Rolle `hardening`).

### ℹ️ Hinweise (bewusst akzeptiert, in SECURITY.md dokumentiert)

| # | Thema | Kommentar |
|---|-------|-----------|
| I1 | Container privileged als root | Für Kamera, Hailo-NPU und sysfs-Reset nötig. Seit v2.4.0 zusätzlich Host-D-Bus (Bluetooth, Shutdown) – ändert nichts, da privileged ohnehin Vollzugriff bedeutet. |
| I2 | Flask-Entwicklungsserver | Einzelnutzer im Heimnetz. Umstieg auf Gunicorn wäre ein größerer Umbau (Threads, Hotpatch) – Empfehlung: nicht ins Internet stellen. |
| I3 | Docker umgeht UFW | Veröffentlichte Ports trägt Docker selbst in iptables ein. Schutz über Router/VPN. |
| I4 | `/api/health` ohne Login | Zeigt Version, RAM, freien Speicher – für den Docker-Health-Check nötig. |
| I5 | Powerbank per BLE lesbar | Fester Schlüssel in der Anker-Firmware, nicht änderbar. Nur Statusdaten. |
| I6 | Actions per Tag statt SHA | Nur offizielle `actions/*`, Workflows mit minimalen Rechten. |

Nicht behoben (L-Kategorie, akzeptiert): **TOTP-Codes** sind innerhalb ihres 30-s-Fensters
mehrfach verwendbar. Ausnutzbar nur mit Passwort *und* abgefangenem Code; der Aufwand für
einen Replay-Schutz steht in keinem Verhältnis.

---

## Nachprüfung (Re-Audit)

Nach dem Ausrollen (`build_and_deploy.sh --update`) am 7. November 2026 erneut geprüft:

| Prüfung | Ergebnis |
|---------|----------|
| `/etc/pi-daemon`, `certs/`, `key.pem`, `app.env` | ✅ `0750` / `0750` / `0640` / `0640`, Eigentümer root |
| `~/Videos` | ✅ `0755` |
| `sshd -T` | ✅ `passwordauthentication no`, `permitrootlogin no`, `kbdinteractiveauthentication no` |
| SSH-Login mit Passwort | ✅ abgelehnt (`Permission denied (publickey)`); Login mit Key funktioniert |
| UFW | ✅ nur noch 22 und 8443 |
| Paketversionen im Container | ✅ entsprechen den festen Versionen |
| `/api/status`, `/api/download` ohne Token | ✅ 401 |
| Path Traversal `../../etc/passwd` mit Token | ✅ 403 |
| Sync-Ziel mit `-oProxyCommand=…` | ✅ 400 mit Fehlermeldung, nichts gespeichert |
| Bestehende 5 Sync-Ziele | ✅ alle gültig, unverändert |
| Security-Header | ✅ CSP, `X-Frame-Options: DENY` vorhanden |
| Web-GUI mit CSP (Chrome) | ✅ Login, Status, Aufnahmen, Powerbank – keine Konsolenfehler |
| Tests | ✅ 59 bestanden (22 neue in `tests/test_security.py`), ruff ohne Befund |

### Kommentar

- Die wichtigste Änderung ist H1: Die Web-GUI hatte bisher die Möglichkeit, Befehle als root
  auszuführen, sobald jemand eingeloggt war. Das Login (Passwort + TOTP) blieb die einzige
  Schranke. Jetzt ist es zusätzlich ausgeschlossen.
- Durch M1 wird der Host-Key eines Sync-Ziels beim nächsten Transfer gespeichert
  („trust on first use“). Wird ein Zielrechner neu installiert, schlägt der Transfer fehl, bis
  die Zeile in `/etc/pi-daemon/known_hosts` gelöscht ist – das ist gewollt.
- Durch M2 ist SSH-Login nur noch mit Schlüssel möglich. Wer ohne Schlüssel arbeiten muss,
  setzt `pi_ssh_hardening: false` in `ansible/group_vars/all/vars.yml`.
- Durch M4 kommen Paket-Updates nicht mehr automatisch. Updates in
  `requirements_daemon.txt` bewusst anheben, testen und ausrollen.
- Beim Re-Audit wurde ein Test mit ungültiger Aufnahmedauer gegen die laufende API
  geschickt. Er hat die gespeicherte Aufnahme-Einstellung auf `normal_hd` / 15 s gesetzt;
  der vorherige Wert ließ sich nicht wiederherstellen. Künftige Prüfungen ändern keine
  Einstellungen auf dem Produktivsystem.

### Offen (manuell)

- **GitHub → Settings → Code security → Private vulnerability reporting → Enable**,
  damit der Meldeweg aus SECURITY.md funktioniert.
