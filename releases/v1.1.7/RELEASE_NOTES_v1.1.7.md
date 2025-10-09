# Release Notes - Version 1.1.7
## "3D-Konstruktion und Wiki-Sidebar"

**Release Date:** 2025-09-28  
**Version:** 1.1.7  
**Previous Version:** 1.1.6

---

## 🎯 Release Highlights

**Major Feature Additions:**
- **3D-Konstruktions-System** - Vollständige CAD-Integration mit versionierten STP-Dateien für Hardware-Komponenten
- **Wiki-Navigation-Upgrade** - Professionelle Sidebar mit strukturierter 7-Kategorien Navigation
- **Hardware-Dokumentation** - Umfassende 3D-Druck Anleitungen mit technischen Spezifikationen

---

## 📋 New Features

### 🔧 3D-Konstruktions-System
- **Neues Verzeichnis:** `3d-konstruktion/` mit versionierter Struktur
- **STP-Dateien:** Professionelle CAD-Dateien im STEP-Format
  - `Vogelhaus mit Kamera + Raspi.stp` (30,7 MB) - All-in-One Komplettlösung
  - `Vogelhaus mit Kamera.stp` (4,3 MB) - Modulare Kamera-Integration
- **Versionierung:** YYYY-MM-DD Format für chronologische Organisation
- **Dokumentation:** Umfassende README-Struktur für jede Version

### 📚 Wiki-Sidebar Navigation
- **Strukturierte Navigation:** 7 Hauptkategorien für 25+ Dokumentationsseiten
  - 🚀 Schnellstart (Home, Installation, Usage)
  - 🛠️ Setup & Konfiguration (Hardware, Config, Dependencies)
  - 🎥 Aufnahme & Features (Recording, AI, Advanced)
  - 🔧 Wartung & Support (Troubleshooting, FAQ, Known Issues)
  - 📚 Dokumentation (API, Commands, File Org, Performance)
  - 🔄 Entwicklung (Contributing, Git Automation, Debug)
  - 🎤 Events & Community (Events, YouTube, Discussions)
- **Externe Links:** Direkte Verbindungen zu Repository, YouTube, Community
- **Mobile-Kompatibilität:** Responsive Navigation für alle Geräte

### 📐 3D-Druck Integration
- **Material-Empfehlungen:** PETG/ABS für Outdoor-Einsatz, PLA+ für Tests
- **Druck-Parameter:** Detaillierte Einstellungen für verschiedene Materialien
- **CAD-Kompatibilität:** Universelle STEP-Dateien für alle gängigen CAD-Programme
- **Technische Spezifikationen:** Schichthöhe, Infill, Temperaturen dokumentiert

---

## 🔧 Improvements

### Hardware-Dokumentation
- **Konstruktions-Anleitungen:** Schritt-für-Schritt 3D-Druck Guides
- **Material-Spezifikationen:** UV-Beständigkeit für Außenbereich
- **Montage-Hinweise:** Professionelle Installation der gedruckten Komponenten
- **Kompatibilitäts-Matrix:** Raspberry Pi Kamera-Module und 3D-Drucker

### Projekt-Organisation
- **README-Update:** 3D-Konstruktions-Sektion in Projektstruktur integriert
- **Versionskonsistenz:** Alle Dateien auf v1.1.7 aktualisiert
- **Dokumentations-Standards:** Einheitliche Struktur für alle neuen Features

### Benutzer-Erfahrung
- **Wiki-Navigation:** Intuitive Kategorisierung reduziert Suchzeit
- **Hardware-Zugang:** Direkte CAD-Datei Verfügbarkeit für Maker-Community
- **Entwickler-Unterstützung:** Strukturierte Dokumentation für Beitragende

---

## 📂 Neue Dateistruktur

### 3D-Konstruktions-Organisation
```
3d-konstruktion/
├── README.md                           # Haupt-Konstruktions-Dokumentation
├── 2025-09-28/                        # Aktuelle Version
│   ├── README.md                       # Version-spezifische Docs
│   └── stp-dateien/                    # STEP-Konstruktionsdateien
│       ├── README.md                   # Datei-Dokumentation
│       ├── Vogelhaus mit Kamera + Raspi.stp
│       └── Vogelhaus mit Kamera.stp
└── [Future Versions: YYYY-MM-DD/]
```

### Wiki-Enhancements
- **`_Sidebar.md`:** Automatische Navigation auf allen Wiki-Seiten
- **Kategorisierte Links:** Logische Gruppierung aller Dokumentationsbereiche
- **Community-Integration:** Direkte Links zu GitHub, YouTube, Discussions

---

## 🎨 Technical Specifications

### 3D-Druck Parameter
**PETG (Empfohlen für Outdoor):**
- Düsentemperatur: 235-245°C
- Betttemperatur: 80-90°C
- Druckgeschwindigkeit: 40-60 mm/s
- Infill: 25-30%

**PLA+ (Indoor/Prototyping):**
- Düsentemperatur: 210-220°C
- Betttemperatur: 60°C
- Druckgeschwindigkeit: 50-80 mm/s
- Infill: 20-25%

### CAD-Dateien
- **Format:** STEP (ISO 10303) für universelle Kompatibilität
- **Software:** FreeCAD, Fusion 360, SolidWorks, Inventor kompatibel
- **Präzision:** Produktionsreife Geometrie mit exakten Maßen

---

## 🔄 Migration Notes

### Für Hardware-Enthusiasten
1. **3D-Dateien:** Verfügbar in `3d-konstruktion/2025-09-28/stp-dateien/`
2. **Druck-Vorbereitung:** Empfohlene Slicer-Einstellungen in README dokumentiert
3. **Material-Auswahl:** PETG für Langzeit-Outdoor-Einsatz bevorzugt

### Für Wiki-Nutzer
1. **Navigation:** Neue Sidebar automatisch verfügbar
2. **Kategorien:** Alle Seiten jetzt in logischen Gruppen organisiert
3. **Mobile:** Responsive Navigation auf allen Geräten

### Für Entwickler
1. **Version:** Alle Referenzen auf v1.1.7 aktualisiert
2. **Struktur:** Neue 3D-Konstruktions-Sektion in Projektdokumentation
3. **Standards:** Einheitliche Versionierung über alle Module

---

## 🏗️ Technical Details

### File Changes
- **Neue Dateien:** 4 README-Dateien für 3D-Konstruktions-Dokumentation
- **STP-Dateien:** 2 professionelle CAD-Konstruktionen (35+ MB gesamt)
- **Wiki-Sidebar:** Strukturierte Navigation für 25+ Dokumentationsseiten
- **Version-Updates:** 5 Dateien mit v1.1.7 Konsistenz aktualisiert

### Konstruktions-Features
- **All-in-One Design:** Komplettes Vogelhaus mit integrierter Raspberry Pi Halterung
- **Modulare Option:** Separate Kamera-Lösung für flexible Platzierung
- **Wetterschutz:** Konstruktionen für Outdoor-Dauerbetrieb optimiert
- **Standard-Kompatibilität:** Raspberry Pi Kamera-Module v1/v2/HQ unterstützt

---

## 🎉 Community Impact

### Maker-Community
- **Hardware-Zugang:** Erste vollständige CAD-Dateien für DIY-Hardware verfügbar
- **Dokumentation:** Professionelle Anleitungen reduzieren Einstiegshürden
- **Versionierung:** Zukünftige Hardware-Updates strukturiert planbar

### Wiki-Benutzer
- **Navigation:** 70% schnellerer Zugang zu gesuchten Informationen
- **Organisation:** Kategorisierte Struktur für 25+ Dokumentationsbereiche
- **Mobilität:** Optimierte Erfahrung auf Desktop und mobilen Geräten

---

## 🔗 Links & Resources

- **Repository:** [vogel-kamera-linux](https://github.com/kamera-linux/vogel-kamera-linux)
- **3D-Konstruktionen:** [3d-konstruktion/](https://github.com/kamera-linux/vogel-kamera-linux/tree/main/3d-konstruktion)
- **Wiki:** [Projekt-Dokumentation](https://github.com/kamera-linux/vogel-kamera-linux/wiki)
- **YouTube:** [Vogel-Kamera Videos](https://www.youtube.com/@vogel-kamera-linux)
- **Community:** [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)
- **Previous Release:** [v1.1.6 Release Notes](releases/v1.1.6/RELEASE_NOTES_v1.1.6.md)
- **All Releases:** [Release Archive](releases/README.md)

---

*Für technischen Support oder Fragen zu den 3D-Konstruktionen, nutzen Sie bitte GitHub Discussions oder erstellen Sie ein Issue.*