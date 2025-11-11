# 📋 Release Documentation

Hier finden Sie die vollständige Dokumentation aller Versionen des vogel-kamera-linux Projekts.

## 🚀 Aktuelle Version

**Version 2.0.0** - "Unified Camera Monitor & Multilingual Documentation"
- **Branch:** main
- **Release Notes:** [RELEASE_NOTES_v2.0.0.md](RELEASE_NOTES_v2.0.0.md)
- **Release Date:** 2025-11-11
- **Architecture:** Unified Single-Process Design (direkt auf Raspberry Pi)
- **Breaking Changes:** 
  - Legacy Remote-Control Scripts archiviert → `legacy/`
  - Auto-Trigger System archiviert → `legacy/kamera-auto-trigger/`
  - Network-Tools archiviert → `legacy/network-tools/`
  - CLI-Parameter statt .env-Dateien
- **Features:** 
  - 🎯 Unified Camera Monitor (kein SSH/TCP-Overhead)
  - 🚦 Traffic Light System Monitoring (🟢🟡🔴)
  - 🔥 Auto-Shutdown >75°C
  - 🌐 Multilingual Docs (English, Deutsch, 日本語)
- **Kompatibel:** Raspberry Pi OS Trixie (Debian 13)
- **Migration:** Siehe [legacy/README.md](../legacy/README.md)

## 📚 Archivierte Versionen (Legacy Remote-Control)

### Version 1.3.2 (Legacy Final)
- **Release Notes:** [v1.3.2/RELEASE_NOTES_v1.3.2.md](v1.3.2/RELEASE_NOTES_v1.3.2.md)
- **Release Date:** 2025-11-08
- **Features:** TCP Watchdog Stabilisierung, Emoji-Fix, Parameter-Optimierungen
- **Status:** ⚠️ LEGACY - Ersetzt durch v2.0.0 Unified Monitor
- **Kompatibel:** Raspberry Pi OS Trixie (Debian 13)

### Version 1.3.1
- **Release Notes:** [v1.3.1/RELEASE_NOTES_v1.3.1.md](v1.3.1/RELEASE_NOTES_v1.3.1.md)
- **Release Date:** 2025-11-05
- **Features:** TCP Watchdog mit Auto-Restart, Live-Progressbar
- **Status:** ⚠️ LEGACY
- **Kompatibel:** Raspberry Pi OS Trixie (Debian 13)

### Version 1.3.0
- **Release Notes:** [v1.3.0/RELEASE_NOTES_v1.3.0.md](v1.3.0/RELEASE_NOTES_v1.3.0.md)
- **Release Date:** 2025-11-01
- **Features:** Trixie-Migration, On-Demand Streaming, Dual-Kamera-Strategie
- **Hinweis:** ⚠️ MediaMTX-Referenzen in v1.3.0 Release Notes sind historisch - System nutzt TCP Watchdog (seit v1.3.1)
- **Kompatibel:** Raspberry Pi OS Trixie (Debian 13)

### Version 1.2.0 (Bookworm Legacy)
- **Branch:** [bookworm-legacy](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)
### Version 1.3.0
- **Release Notes:** [v1.3.0/RELEASE_NOTES_v1.3.0.md](v1.3.0/RELEASE_NOTES_v1.3.0.md)
- **Release Date:** 2025-11-01
- **Features:** Trixie-Migration, On-Demand Streaming, Dual-Kamera-Strategie
- **Status:** ⚠️ LEGACY
- **Kompatibel:** Raspberry Pi OS Trixie (Debian 13)

### Version 1.2.0 (Bookworm Legacy)
- **Branch:** [bookworm-legacy](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)
- **Release Notes:** [v1.2.0/RELEASE_NOTES_v1.2.0.md](v1.2.0/RELEASE_NOTES_v1.2.0.md)
- **Release Date:** 2025-10-01
- **Features:** Auto-Trigger System, Preview-Stream (TCP), Trigger-Duration Logic
- **Status:** ⚠️ LEGACY - Für Bookworm (Debian 12)
- **Kompatibel:** Raspberry Pi OS Bookworm (Debian 12)

### Version 1.1.9
- **Release Notes:** [v1.1.9/RELEASE_NOTES_v1.1.9.md](v1.1.9/RELEASE_NOTES_v1.1.9.md)
- **Release Date:** 2025-09-30
- **Features:** System-Monitoring, CPU-Load-Überwachung, Performance-Optimierung

### Version 1.1.8
- **Release Notes:** [v1.1.8/RELEASE_NOTES_v1.1.8.md](v1.1.8/RELEASE_NOTES_v1.1.8.md)
- **Release Date:** 2025-09-29
- **Features:** Projekt-Reorganisation und AI-Modell-Erweiterungen

### Version 1.1.6
- **Release Notes:** [v1.1.6/RELEASE_NOTES_v1.1.6.md](v1.1.6/RELEASE_NOTES_v1.1.6.md)
- **Features:** Erweiterte Funktionalitäten

### Version 1.1.5  
- **Release Notes:** [v1.1.5/RELEASE_NOTES_v1.1.5.md](v1.1.5/RELEASE_NOTES_v1.1.5.md)
- **Features:** Stabilität und Performance-Verbesserungen

### Version 1.1.4
- **Release Notes:** [v1.1.4/RELEASE_NOTES_v1.1.4.md](v1.1.4/RELEASE_NOTES_v1.1.4.md)
- **Features:** Git-Automatisierung und Security-Features

### Version 1.1.3
- **Release Notes:** [v1.1.3/RELEASE_NOTES_v1.1.3.md](v1.1.3/RELEASE_NOTES_v1.1.3.md) 
- **Features:** Komplette Dokumentation und Wiki-System

### Version 1.1.2
- **Release Notes:** [v1.1.2/RELEASE_NOTES_v1.1.2.md](v1.1.2/RELEASE_NOTES_v1.1.2.md)
- **Features:** Erweiterte Konfigurationsmöglichkeiten

### Version 1.1.1  
- **Release Notes:** [v1.1.1/RELEASE-NOTES-v1.1.1.md](v1.1.1/RELEASE-NOTES-v1.1.1.md)
- **Features:** Grundlegende Verbesserungen und Bugfixes

---

## 📖 Navigation

- **Zurück zum Projekt:** [../README.md](../README.md)
- **Changelog:** [../docs/CHANGELOG.md](../docs/CHANGELOG.md) 
- **Aktueller Release:** [../RELEASE_NOTES_v1.1.8.md](../RELEASE_NOTES_v1.1.8.md)

---

## 🔄 Versionierungsrichtlinien

**Aktueller Release:** In `/releases/` Verzeichnis
**Archivierte Releases:** Organisiert in `/releases/vX.X.X/` Struktur  
**Format:** Semantic Versioning (MAJOR.MINOR.PATCH)

*Bei Release von v1.3.0 wird v1.2.0 automatisch in ein Archiv verschoben.*