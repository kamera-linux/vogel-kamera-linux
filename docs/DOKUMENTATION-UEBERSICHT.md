# 📚 Dokumentations-Übersicht (v2.2)

## 🎯 Schnelleinstieg

### Für neue Nutzer (Einrichtung)
1. **[../README.md](../README.md)** - Haupt-Übersicht, Features, Quickstart
2. **[../unified-monitor-client/SETUP_GUIDE.md](../unified-monitor-client/SETUP_GUIDE.md)** - Ansible-Deployment (docker build + deploy)
3. **[../unified-monitor-client/README.md](../unified-monitor-client/README.md)** - Web-API und Container-Dokumentation

### Für erfahrene Nutzer
1. **[ARCHITEKTUR.md](ARCHITEKTUR.md)** - Systemarchitektur Docker + Web API
2. **[AI-MODELLE-VOGELARTEN.md](AI-MODELLE-VOGELARTEN.md)** - KI-Modelle für Vogelarten
3. **[ANLEITUNG-EIGENES-AI-MODELL.md](ANLEITUNG-EIGENES-AI-MODELL.md)** - Custom Training

---

## 📖 Aktive Dokumentation (v2.2)

### 🐳 Docker-Container & Web-API

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[../unified-monitor-client/README.md](../unified-monitor-client/README.md)** | `pi_daemon_secure.py` API-Referenz, Web-GUI, Endpunkte | Alle |
| **[../unified-monitor-client/SETUP_GUIDE.md](../unified-monitor-client/SETUP_GUIDE.md)** | Ansible-Deployment, Konfiguration, Fehlerbehebung | Alle |
| **[../unified-monitor-client/DETECT_AND_RECORD.md](../unified-monitor-client/DETECT_AND_RECORD.md)** | Detection-and-Record Modus | Entwickler |

### 🍓 Raspberry Pi Detection-Skripte

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[../raspberry-pi-scripts/UNIFIED-MONITOR-README.md](../raspberry-pi-scripts/UNIFIED-MONITOR-README.md)** | `unified-camera-monitor-detect-only.py` | Alle |
| **[../raspberry-pi-scripts/HAILO-README.md](../raspberry-pi-scripts/HAILO-README.md)** | Hailo AI Accelerator | Entwickler |

### 🏗️ Architektur & Sicherheit

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[ARCHITEKTUR.md](ARCHITEKTUR.md)** | Docker-Architektur, Datenfluss, Deployment | Entwickler |
| **[SECURITY.md](SECURITY.md)** | JWT, TOTP, TLS, Best Practices | Sysadmin |
| **[VERSIONIERUNG.md](VERSIONIERUNG.md)** | Versionierungsrichtlinien | Entwickler |

### 🤖 KI-Erkennung mit YOLO26n

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[AI-MODELLE-VOGELARTEN.md](AI-MODELLE-VOGELARTEN.md)** | Vortrainierte Vogelarten-Modelle | Alle |
| **[ANLEITUNG-EIGENES-AI-MODELL.md](ANLEITUNG-EIGENES-AI-MODELL.md)** | Training eigener Modelle | Fortgeschritten |

### 📋 Release Notes & Changelog

| Dokument | Beschreibung |
|----------|--------------|
| **[../CHANGELOG.md](../CHANGELOG.md)** | Vollständige Versionshistorie |
| **[../releases/](../releases/)** | Archivierte Release-Notes |

---

## 📦 Legacy-Dokumentation (archiviert, nicht mehr aktiv)

> ⚠️ Diese Dokumente beschreiben **veraltete Architekturen** (SSH-basierter Python-Client, v1.x–v2.1.x).  
> Sie befinden sich in `legacy/docs/` und sind nur noch für Referenz oder Rollback relevant.

| Dokument | Inhalt | Status |
|----------|--------|--------|
| `legacy/docs/TRIXIE-MIGRATION.md` | Debian 13 Migration Guide | ⚠️ Legacy |
| `legacy/docs/QUICK-START-PYTHON.md` | Alter Python-Client Quickstart | ⚠️ Legacy |
| `legacy/docs/HYBRID-DETECT-AND-RECORD.md` | Hybrid Detection Mode | ⚠️ Legacy |
| `legacy/docs/HYBRID-DETECTOR-DEPLOYMENT.md` | Hybrid Deployment | ⚠️ Legacy |
| `legacy/docs/PROJEKT-REORGANISATION.md` | Reorganisations-Dokumentation | ⚠️ Legacy |
| `legacy/docs/QUICK_REFERENCE_v2.1.2.md` | Befehlsreferenz v2.1.x | ⚠️ Legacy |

---

## 🎓 Lernpfade

### Pfad 1: System einrichten (Einsteiger)
```
1. README.md (Überblick, Architektur, Quickstart)
   └─► 2. SETUP_GUIDE.md (Ansible --install)
       └─► 3. Web-GUI im Browser öffnen
           └─► 4. DETECT_AND_RECORD.md (erste Aufnahme)
```

### Pfad 2: KI-Erkennung anpassen
```
1. AI-MODELLE-VOGELARTEN.md (vortrainierte Modelle)
   └─► 2. ANLEITUNG-EIGENES-AI-MODELL.md (eigene Modelle trainieren)
       └─► 3. ARCHITEKTUR.md (Integration in den Container verstehen)
```

### Pfad 3: Sicherheit & Betrieb
```
1. ARCHITEKTUR.md (Systemverständnis)
   └─► 2. SECURITY.md (JWT, TOTP, TLS)
       └─► 3. SETUP_GUIDE.md (Deployment-Details, Vault)
```
