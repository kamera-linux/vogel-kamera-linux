# Security Policy

## 🔒 Sicherheitsrichtlinien für Vogel-Kamera-Linux

Wir nehmen die Sicherheit unseres Projekts ernst und schätzen die Hilfe der Community beim Auffinden und Beheben von Sicherheitsproblemen.

## 🚨 Unterstützte Versionen

Wir bieten Sicherheits-Updates für die folgenden Versionen:

| Version | Unterstützt        | OS-Basis | Architektur |
| ------- | ------------------ | -------- | ----------- |
| 2.0.x   | ✅ Vollständig     | Trixie (Debian 13) | Unified Monitor |
| 1.3.x   | ⚠️ Kritische Fixes | Trixie (Debian 13) | Legacy Remote-Control |
| 1.2.x   | ⚠️ Kritische Fixes | Bookworm (Debian 12) | Legacy Remote-Control |
| 1.1.x   | ❌ Nicht mehr unterstützt | Bookworm | Legacy |
| 1.0.x   | ❌ Nicht mehr unterstützt | Bookworm | Legacy |
| < 1.0   | ❌ Nicht mehr unterstützt | - | - |

> ⚠️ **Wichtig:** v2.0.x verwendet **Unified Camera Monitor** ohne SSH-Overhead. Legacy-Versionen (v1.x) sind in `legacy/` archiviert.
> 
> 📘 **Für Bookworm (Debian 12):** Verwenden Sie [bookworm-legacy Branch v1.2.x](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)

## 🐛 Sicherheitslücken melden

### 🔐 Vertrauliche Meldung (Bevorzugt)

Für **kritische Sicherheitsprobleme** nutzen Sie bitte eine der folgenden vertraulichen Kanäle:

- **GitHub Security Advisories:** [Private Vulnerability Report](https://github.com/kamera-linux/vogel-kamera-linux/security/advisories/new)
- **E-Mail:** vogel-kamera.linux@gmail.com *(falls verfügbar)*

### 📋 Informationen für Sicherheitsberichte

Bitte geben Sie folgende Informationen an:

**🎯 Problembeschreibung:**
- Art der Sicherheitslücke (z.B. RCE, XSS, Privilege Escalation)
- Betroffene Komponenten (SSH, Kamera-Scripts, AI-Module)
- Potenzielle Auswirkungen

**🔄 Reproduktion:**
- Schritt-für-Schritt Anleitung
- Proof-of-Concept (falls möglich)
- Betroffene Konfigurationen

**🌐 Umgebung:**
- Betriebssystem und Version
- Python-Version
- Vogel-Kamera-Linux Version
- Hardware (Raspberry Pi Modell)

**💡 Lösungsvorschlag (optional):**
- Mögliche Fixes oder Workarounds
- Code-Patches (falls entwickelt)

## ⚡ Schweregrade

### 🔴 **Kritisch (Critical)**
- Remote Code Execution ohne Authentifizierung
- Vollständige Systemkompromittierung
- Datenlecks mit persönlichen Informationen

### 🟠 **Hoch (High)**
- Privilege Escalation
- SSH-Schlüssel-Kompromittierung
- Netzwerk-basierte Angriffe

### 🟡 **Mittel (Medium)**
- Denial of Service
- Informationslecks
- Schwache Kryptografie

### 🟢 **Niedrig (Low)**
- Client-seitige Probleme
- Konfigurationsprobleme
- Nicht-kritische Informationslecks

## 🔄 Response-Prozess

### ⏱️ Antwortzeiten

- **Kritisch:** 24 Stunden
- **Hoch:** 48 Stunden  
- **Mittel:** 1 Woche
- **Niedrig:** 2 Wochen

### 📋 Ablauf

1. **Eingangsbeste:** Wir bestätigen den Erhalt innerhalb der Antwortzeit
2. **Analyse:** Bewertung der Schwere und Auswirkungen
3. **Entwicklung:** Erstellung und Test eines Fixes
4. **Koordination:** Abstimmung der Veröffentlichung mit dem Melder
5. **Release:** Veröffentlichung des Security-Updates
6. **Disclosure:** Öffentliche Bekanntgabe nach koordinierter Disclosure

## 🛡️ Sicherheits-Best-Practices

### 🔧 Für Entwickler

- **SSH-Schlüssel:** Verwenden Sie starke Ed25519-Schlüssel
- **Netzwerk:** Nutzen Sie Firewalls und VPN für Remote-Zugriff
- **Updates:** Halten Sie System und Dependencies aktuell
- **Credentials:** Niemals Passwörter/Schlüssel in Code committen

### 👥 Für Nutzer

**🔐 SSH-Sicherheit:**
```bash
# Starke SSH-Konfiguration
ssh-keygen -t ed25519 -b 4096
echo "PasswordAuthentication no" >> ~/.ssh/config
echo "PermitRootLogin no" >> /etc/ssh/sshd_config
```

**🌐 Netzwerk-Sicherheit:**
```bash
# Firewall für Raspberry Pi
sudo ufw enable
sudo ufw allow ssh
sudo ufw deny 22/tcp from 0.0.0.0/0  # Nur bekannte IPs erlauben

# MediaMTX RTSP-Server absichern (v1.3.0+)
sudo ufw allow from 192.168.178.0/24 to any port 8554 proto tcp  # Nur lokales Netzwerk
sudo ufw deny 8554/tcp  # Blockiere alle anderen

# Optional: MediaMTX mit Authentifizierung
sudo nano /etc/mediamtx/mediamtx.yml
# authMethod: internal
# authInternalUsers:
#   - user: vogel
#     pass: <sicheres-passwort>
```

**⚙️ System-Härtung:**
```bash
# Regelmäßige Updates
sudo apt update && sudo apt upgrade
pip install --upgrade -r requirements.txt

# Monitoring
sudo fail2ban-client status
```

## 🚫 Responsible Disclosure

### ✅ Erwartungen an Sicherheitsforscher

- **Keine öffentliche Disclosure** vor koordinierter Veröffentlichung
- **Keine Datenexfiltration** oder destruktive Tests
- **Respekt vor Privatsphäre** anderer Nutzer
- **Konstruktive Zusammenarbeit** bei der Problemlösung

### 🎖️ Anerkennung

- **Security.md Credits:** Auflistung in Sicherheitsdokumentation
- **Release Notes:** Erwähnung in Danksagungen (nach Wunsch)
- **GitHub Advisories:** Offizielle CVE-Anerkennung

## ⚠️ Bekannte Sicherheitsüberlegungen

### 🔍 Architektur-spezifische Risiken

**v2.0.x - Unified Camera Monitor:**
- Direkter Kamera-Zugriff auf Raspberry Pi (kein SSH)
- YOLOv8 AI-Inferenz lokal (keine Netzwerk-Übertragung)
- Automatische Aufnahmen bei Trigger (Datenschutz beachten)
- System-Monitoring mit Auto-Shutdown (>75°C)

**v1.x - Legacy Remote-Control (archiviert):**
- SSH-basierte Architektur mit Remote-Zugriff
- TCP-Stream über Netzwerk (Port 8888)
- MediaMTX RTSP-Server (Port 8554)
- Potenzielle Man-in-the-Middle Angriffe

### 🛡️ Sicherheitsverbesserungen in v2.0

✅ **Kein SSH-Overhead** - Eliminiert Remote-Angriffsvektoren
✅ **Lokale AI-Verarbeitung** - Keine sensitiven Daten über Netzwerk
✅ **Kein TCP-Stream** - Reduzierte Netzwerk-Exposition
✅ **Direkter Kamera-Zugriff** - Weniger Komplexität, weniger Angriffsfläche
✅ **CLI-Parameter** - Keine .env-Dateien mit Credentials

### 🔒 Allgemeine Sicherheitsaspekte

**AI-Module Dependencies:**
- Externe Python-Pakete (YOLOv8, OpenCV)
- Potenzielle Supply-Chain-Angriffe
- Memory-intensive Operationen

**Raspberry Pi Absicherung:**
- Physischer Zugriff kann System kompromittieren
- SD-Karte verschlüsseln für sensitive Aufnahmen
- Updates regelmäßig installieren

### 🛠️ Mitigationen

**v2.0 (Unified Monitor):**
- **Keine SSH-Keys benötigt** (Standard-Modus)
- **start-unified-monitoring.sh** für optionalen Remote-Start
- **Traffic Light Monitoring** für System-Health
- **Auto-Shutdown** bei kritischer Temperatur
- **Dependency-Pinning** in requirements-pi.txt
- **Input-Validation** für alle CLI-Parameter

**v1.x Legacy (falls noch verwendet):**
- **SSH-Schlüssel-Authentifizierung** standardmäßig aktiviert
- **RTSP-Port-Restriktion** über Firewall (nur vertrauenswürdige Clients)
- **MediaMTX Authentication** konfigurierbar
- **Error-Handling** verhindert Information Disclosure

## 📚 Sicherheits-Ressourcen

### 🔗 Externe Referenzen

- [OWASP IoT Security](https://owasp.org/www-project-iot-security-guidance/)
- [Raspberry Pi Security](https://www.raspberrypi.org/documentation/configuration/security.md)
- [Python Security Guide](https://python-security.readthedocs.io/)

### 📖 Projekt-spezifische Dokumentation

- [[Security Guidelines]] - Detaillierte Sicherheitsrichtlinien (Wiki)
- [[Installation Guide]] - Sichere Installations-Praktiken
- [[Configuration]] - Sichere Konfigurationsempfehlungen

## 📞 Kontakt

**🚨 Für Sicherheitsprobleme:**
- GitHub Security Advisories (bevorzugt)
- E-Mail: vogel-kamera.linux@gmail.com

**💬 Für allgemeine Fragen:**
- [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
- [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)

---

**🔒 Diese Security Policy wird regelmäßig überprüft und aktualisiert.**

*Letzte Aktualisierung: 5. November 2025 (v1.3.1 - Production Release)*