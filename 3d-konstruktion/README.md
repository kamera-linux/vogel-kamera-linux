# 🔧 3D-Konstruktion - Vogel-Kamera-Linux

Konstruktionsunterlagen für 3D-gedruckte Komponenten der Vogel-Kamera-Hardware.

## 📁 Versionsübersicht

### 🗓️ Version 2025-09-27 (Aktuell)
- **Verzeichnis:** `2025-09-27/`
- **Dateiformat:** STP-Dateien (STEP-Format)
- **Status:** Aktuelle Konstruktionsversion
- **Beschreibung:** Initiale 3D-Konstruktionsdateien für Kamera-Hardware

## 📐 Dateistruktur

```
3d-konstruktion/
├── README.md                           # Diese Dokumentation
├── 2025-09-27/                        # Version vom 27. September 2025
│   ├── README.md                       # Version-spezifische Dokumentation
│   └── stp-dateien/                    # STEP-Konstruktionsdateien
│       └── *.stp                       # 3D-CAD Dateien im STEP-Format
└── YYYY-MM-DD/                        # Zukünftige Versionen
    ├── README.md
    └── stp-dateien/
        └── *.stp
```

## 🛠️ Dateiformate

### STP/STEP-Dateien
- **Format:** Standard for the Exchange of Product Data (ISO 10303)
- **Kompatibilität:** Universeller 3D-CAD Standard
- **Software:** Kompatibel mit allen gängigen CAD-Programmen:
  - FreeCAD (Open Source)
  - Fusion 360
  - SolidWorks
  - Inventor
  - OnShape
  - Blender (mit Import-Addon)

## 🎯 Verwendungszweck

Die 3D-Konstruktionsdateien enthalten:
- 📷 **Kamera-Halterungen** für Raspberry Pi Kamera-Module
- 🏠 **Gehäuse-Komponenten** für Schutz vor Witterung
- 🔧 **Montage-Hardware** für Vogelhäuser und Ständer
- 📐 **Befestigungselemente** für stabile Installation

## 📝 Neue Version hinzufügen

1. **Neues Verzeichnis erstellen:**
   ```bash
   mkdir -p 3d-konstruktion/YYYY-MM-DD/stp-dateien
   ```

2. **README erstellen:**
   ```bash
   cp 3d-konstruktion/2025-09-27/README.md 3d-konstruktion/YYYY-MM-DD/
   ```

3. **STP-Dateien kopieren:**
   ```bash
   cp ihre-dateien/*.stp 3d-konstruktion/YYYY-MM-DD/stp-dateien/
   ```

4. **Dokumentation aktualisieren:**
   - Diese README.md erweitern
   - Versions-spezifische README.md anpassen

## 🔄 Versionsverwaltung

- **Datierung:** Verwendung von YYYY-MM-DD Format für klare Chronologie
- **Rückwärtskompatibilität:** Alle Versionen bleiben verfügbar
- **Änderungsprotokoll:** Jede Version hat eigene Dokumentation
- **Archivierung:** Alte Versionen werden nicht gelöscht

## 📖 Lizenz

Die 3D-Konstruktionsdateien stehen unter der gleichen MIT-Lizenz wie das Hauptprojekt.
Siehe [LICENSE](../LICENSE) für Details.

## 🤝 Beitrag leisten

Verbesserungen an den 3D-Konstruktionen sind willkommen:

1. Fork des Repositories
2. Neue Version in `3d-konstruktion/YYYY-MM-DD/` erstellen
3. STP-Dateien und Dokumentation hinzufügen
4. Pull Request erstellen

## 📞 Support

Bei Fragen zu den 3D-Konstruktionen:
- 💬 [GitHub Discussions](https://github.com/roimme65/vogel-kamera-linux/discussions)
- 🐛 [Issues](https://github.com/roimme65/vogel-kamera-linux/issues) für Konstruktionsfehler