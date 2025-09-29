# Security Policy

## 🔒 Sicherheitsrichtlinien für Vogel-Kamera-Linux

Wir nehmen die Sicherheit unseres Projekts ernst und schätzen die Hilfe der Community beim Auffinden und Beheben von Sicherheitsproblemen.

## 🚨 Unterstützte Versionen

Wir bieten Sicherheits-Updates für die folgenden Versionen:

| Version | Unterstützt        |
| ------- | ------------------ |
| 1.1.x   | ✅ Vollständig     |
| 1.0.x   | ⚠️ Kritische Fixes |
| < 1.0   | ❌ Nicht mehr      |

## 🐛 Sicherheitslücken melden

### 🔐 Vertrauliche Meldung (Bevorzugt)

Für **kritische Sicherheitsprobleme** nutzen Sie bitte eine der folgenden vertraulichen Kanäle:

- **GitHub Security Advisories:** [Private Vulnerability Report](https://github.com/roimme65/vogel-kamera-linux/security/advisories/new)
- **E-Mail:** security@vogel-kamera-linux.de *(falls verfügbar)*

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

**AI-Module Dependencies:**
- Externe Python-Pakete (YOLOv8, OpenCV)
- Potenzielle Supply-Chain-Angriffe
- Memory-intensive Operationen

### 🛠️ Mitigationen

- **SSH-Schlüssel-Authentifizierung** standardmäßig aktiviert
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
- E-Mail: security@vogel-kamera-linux.de

**💬 Für allgemeine Fragen:**
- [GitHub Issues](https://github.com/roimme65/vogel-kamera-linux/issues)
- [GitHub Discussions](https://github.com/roimme65/vogel-kamera-linux/discussions)

---

**🔒 Diese Security Policy wird regelmäßig überprüft und aktualisiert.**

*Letzte Aktualisierung: 23. September 2025*