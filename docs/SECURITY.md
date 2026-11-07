# Security Policy

## 🚨 Unterstützte Versionen

| Version | Unterstützt | OS-Basis | Architektur |
| ------- | ----------- | -------- | ----------- |
| 2.4.x   | ✅ Sicherheits-Updates | Raspberry Pi OS Trixie (Debian 13) | Docker-Container, HTTPS-Web-GUI (JWT + TOTP) |
| 2.3.x   | ⚠️ Bitte auf 2.4.x aktualisieren | Trixie | wie 2.4.x |
| < 2.3   | ❌ Nicht mehr unterstützt | – | – |

Sicherheits-Fixes erscheinen nur für die aktuelle Version. Ein Update ist ein Befehl:
`./ansible/build_and_deploy.sh --update`

## 🐛 Sicherheitslücken melden

Bitte **nicht** als öffentliches Issue melden, sondern vertraulich:

- **GitHub:** [Private Vulnerability Report](https://github.com/kamera-linux/vogel-kamera-linux/security/advisories/new)
- **E-Mail:** kamera-linux@mailbox.org

Hilfreich sind: betroffene Version, betroffener Endpunkt oder Datei, Schritte zum Nachstellen
und – falls möglich – ein Vorschlag zur Behebung.

Dies ist ein Hobby-Projekt ohne festes Team. Wir bemühen uns, Meldungen innerhalb einer Woche
zu beantworten und kritische Lücken vorrangig zu beheben.

## 🏗️ Architektur und Angriffsfläche

```
Browser ──HTTPS:8443──▶ Docker-Container „pi-daemon“ (root, privileged) auf dem Raspberry Pi 5
                          ├─ Flask-API + Web-GUI (Login: Passwort + TOTP → JWT, 8 h gültig)
                          ├─ Kamera/Hailo-NPU/Mikrofon (Geräte des Hosts)
                          ├─ rsync/ssh zu Sync-Zielen (Videos übertragen)
                          └─ Host-D-Bus: Bluetooth (Powerbank) + systemd-logind (Shutdown)
```

| Bereich | Schutz |
|---------|--------|
| **Anmeldung** | bcrypt-Passworthash + TOTP (2FA); max. 5 Versuche/Minute pro IP; 1 s Verzögerung bei Fehlversuch |
| **Sitzung** | JWT (HS256) nur im `Authorization`-Header, nie in URLs; Token liegt im `sessionStorage` des Tabs |
| **Transport** | HTTPS mit selbst signiertem Zertifikat (beim ersten Aufruf bestätigen oder `/cert.pem` importieren) |
| **Browser** | Content-Security-Policy, `X-Frame-Options: DENY`, `nosniff`, `no-referrer`, `Cache-Control: no-store` für die API |
| **Dateizugriff** | Download/Löschen nur innerhalb des Video-Verzeichnisses (Path-Traversal-Schutz) |
| **Sync-Ziele** | Host, Benutzer und Pfad werden geprüft (keine Optionen/Shell-Zeichen); ssh merkt sich Host-Keys beim ersten Kontakt (`/etc/pi-daemon/known_hosts`) und lehnt danach geänderte Keys ab |
| **Secrets** | in `ansible-vault` (verschlüsselt im Repo); auf dem Pi in `/etc/pi-daemon/app.env` (0640, root) |
| **Abhängigkeiten** | feste Versionen in `requirements_daemon.txt`; CI prüft jeden Push (ruff, shellcheck, pytest) |
| **Pi-Härtung** (Ansible-Rolle `hardening`) | SSH nur mit Schlüssel, kein root-Login; Konfiguration und TLS-Schlüssel nicht für andere Benutzer lesbar/schreibbar; UFW mit Standard „deny“ |

Ohne Login erreichbar sind nur: die Login-Seite, `/api/login`, `/api/health`
(Version, RAM, freier Speicher – für den Docker-Health-Check) und `/cert.pem` (öffentliches Zertifikat).

## ⚠️ Bekannte, bewusst akzeptierte Risiken

| Risiko | Warum akzeptiert | Empfehlung |
|--------|------------------|------------|
| Container läuft **privileged als root** | Kamera-Reset per sysfs, Hailo-NPU, DMA-Heaps und Host-Bibliotheken brauchen vollen Gerätezugriff | Pi als dedizierte Kamera betreiben, keine weiteren Dienste darauf |
| Eingeloggte Nutzer haben **volle Kontrolle** | Es gibt genau einen Admin-Zugang; die Web-GUI kann Aufnahmen löschen, Sync-Ziele und SSH-Keys setzen | Starkes Passwort, TOTP-Secret geheim halten |
| **Flask-Entwicklungsserver** statt Gunicorn | Einzelner Nutzer im Heimnetz; ein Umbau würde den Thread-Start und Hotpatch ändern | Nicht direkt ins Internet stellen |
| **Docker umgeht UFW** für Port 8443 | Docker trägt veröffentlichte Ports selbst in iptables ein; die UFW-Regel ist daher nicht die eigentliche Schranke | Port nur im Heimnetz erreichbar machen (Router); Zugriff von außen nur über VPN |
| `roimme` hat **sudo ohne Passwort** | Standard bei Raspberry Pi OS; Ansible braucht es | Deshalb ist SSH-Passwort-Login abgeschaltet |
| **Powerbank per Bluetooth** auslesbar | Die Anker-Firmware nutzt einen festen, öffentlich bekannten Schlüssel – jeder in Funkreichweite kann den Status lesen | Nur Statusdaten, keine Steuerung durch dieses Projekt |
| GitHub Actions per **Tag statt Commit-SHA** | Nur offizielle `actions/*`; Workflows haben minimale Rechte | – |

## 🛡️ Empfehlungen für den Betrieb

- Port 8443 **nicht** per Portweiterleitung ins Internet freigeben – für Fernzugriff ein VPN
  (z. B. WireGuard) nutzen.
- Regelmäßig aktualisieren: `sudo apt update && sudo apt full-upgrade` auf dem Pi und
  `./ansible/build_and_deploy.sh --update` für den Daemon.
- Für Sync-Ziele eigene SSH-Keys mit eingeschränkten Rechten verwenden (z. B. nur Schreibzugriff
  auf das Zielverzeichnis).
- Wechselt ein Sync-Ziel absichtlich seinen Host-Key (Neuinstallation), die Zeile in
  `/etc/pi-daemon/known_hosts` löschen.
- Gotify einrichten ([GOTIFY_SETUP.md](../GOTIFY_SETUP.md)), um Ausfälle und niedrigen Akku
  mitzubekommen.

## 📋 Audits

- [Security-Audit November 2026](SECURITY-AUDIT-2026-11.md) – Funde, Fixes, Nachprüfung

---

*Letzte Aktualisierung: 7. November 2026 (v2.4.x)*
