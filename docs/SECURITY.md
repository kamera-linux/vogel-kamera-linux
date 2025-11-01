# Security Policy

## 🔒 Sicherheitsrichtlinien für Vogel-Kamera-Linux

Wir nehmen die Sicherheit unseres Projekts ernst und schätzen die Hilfe der Community beim Auffinden und Beheben von Sicherheitsproblemen.

## 🚨 Unterstützte Versionen

Wir bieten Sicherheits-Updates für die folgenden Versionen:

| Version | Unterstützt        | OS-Basis |
| ------- | ------------------ | -------- |
| 1.3.x   | ✅ Vollständig     | Trixie (Debian 13) |
| 1.2.x   | ⚠️ Kritische Fixes | Bookworm (Debian 12) |
| 1.1.x   | ⚠️ Nur kritische Sicherheitsfixes | Bookworm |
| 1.0.x   | ⚠️ Nur kritische Sicherheitsfixes | Bookworm |
| < 1.0   | ❌ Nicht mehr unterstützt | - |

> ⚠️ **Wichtig:** v1.3.x ist **nicht kompatibel** mit Bookworm (Debian 12). Verwenden Sie [bookworm-legacy Branch](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy) für v1.2.x.

## 🐛 Sicherheitslücken melden

### 🔐 Vertrauliche Meldung (Bevorzugt)

Für **kritische Sicherheitsprobleme** nutzen Sie bitte eine der folgenden vertraulichen Kanäle:

- **GitHub Security Advisories:** [Private Vulnerability Report](https://github.com/kamera-linux/vogel-kamera-linux/security/advisories/new)
- **E-Mail:** kamerawagen.linux@gmail.com *(falls verfügbar)*

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

### 🔍 Inherente Risiken

**SSH-basierte Architektur:**
- Remote-Zugriff erforderlich für Kamera-Steuerung
- Netzwerk-Abhängigkeit für alle Funktionen
- Potenzielle Man-in-the-Middle Angriffe

**MediaMTX RTSP-Server (v1.3.0+):**
- Port 8554 (RTSP) exponiert im Netzwerk
- Potenzielle unbefugte Stream-Zugriffe
- On-Demand Camera-Aktivierung durch externe Clients
- systemd-Service läuft permanent

**AI-Module Dependencies:**
- Externe Python-Pakete (YOLOv8, OpenCV)
- Potenzielle Supply-Chain-Angriffe
- Memory-intensive Operationen

### 🛠️ Mitigationen

- **SSH-Schlüssel-Authentifizierung** standardmäßig aktiviert
- **RTSP-Port-Restriktion** über Firewall (nur vertrauenswürdige Clients)
- **MediaMTX Authentication** konfigurierbar in /etc/mediamtx/mediamtx.yml
- **Dependency-Pinning** in requirements.txt
- **Input-Validation** für alle Parameter
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
- E-Mail: kamerawagen.linux@gmail.com

**💬 Für allgemeine Fragen:**
- [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
- [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)

---

**🔒 Diese Security Policy wird regelmäßig überprüft und aktualisiert.**

*Letzte Aktualisierung: 1. November 2025 (v1.3.0 - Trixie Support)*