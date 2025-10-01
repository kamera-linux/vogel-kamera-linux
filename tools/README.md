# 🛠️ Development & Testing Tools

Dieses Verzeichnis enthält verschiedene Entwicklungs- und Test-Tools für das Vogel-Kamera-Linux Projekt.

## 📋 Übersicht

| Tool | Beschreibung | Verwendung |
|------|--------------|------------|
| `check_emojis.py` | Emoji-Validator für Markdown-Dateien | Prüft alle Dokumente auf defekte Emojis |
| `test_ai_features.py` | AI-Feature Tests | Testet KI-Funktionen |
| `automation_test.txt` | Automatisierungs-Tests | Test-Dokumentation |

## 🔍 check_emojis.py - Emoji-Validator

### Beschreibung
Überprüft alle Markdown-Dateien im Projekt (inkl. Wiki) auf defekte oder nicht erkannte Emojis (❓ Replacement Character).

### Features
- ✅ Erkennt defekte Emojis (❓ Unicode Replacement Character)
- 📄 Scannt README.md und alle Dokumentationsdateien
- 📚 Prüft Wiki-Dateien (wiki-content/ und wiki-repo/)
- 🔍 Gibt detaillierte Berichte mit Zeilennummern aus
- 💡 Schlägt passende Emojis basierend auf Kontext vor
- 🔧 Automatische Korrektur-Funktion (experimentell)

### Verwendung

#### Alle Dateien prüfen
```bash
python3 tools/check_emojis.py
```

#### Mögliche Korrekturen anzeigen (Dry-Run)
```bash
python3 tools/check_emojis.py --fix-dry-run
```

#### Automatische Korrektur anwenden
```bash
# VORSICHT: Ändert Dateien automatisch!
python3 tools/check_emojis.py --fix
```

#### Beispiel-Ausgabe
```
🔍 Suche nach Markdown-Dateien...
📄 87 Dateien gefunden

================================================================================
🔍 EMOJI-VALIDIERUNGS-BERICHT
================================================================================
📊 Statistik:
   - Überprüfte Dateien: 87
   - Gefundene Probleme: 30

⚠️  GEFUNDENE PROBLEME:

📄 README.md
--------------------------------------------------------------------------------
   Zeile  522: ❓
   Inhalt: - 📊 **System-Monitoring:** Automatische CPU-Load...
   💡 Vorschlag: 📊

📄 wiki-content/Home.md
--------------------------------------------------------------------------------
   Zeile   18: ❓
   Inhalt: - **💾 Speicher-Management:** Festplatten-Auslastung...
   💡 Vorschlag: 💾
```

### Erkannte Probleme

Das Tool erkennt:
- **❓ Replacement Character** - Das Standard-Symbol für nicht darstellbare Unicode-Zeichen
- **\ufffd** - Escaped Replacement Character
- **❓❓** - Doppelte Fragezeichen (oft bei Encoding-Problemen)
- **Private Use Area Characters** - Problematische Unicode-Zeichen
- **Encoding-Fehler** - Dateien mit falscher Kodierung

### Kontextbasierte Vorschläge

Das Tool schlägt passende Emojis basierend auf Keywords vor:

| Keyword | Vorgeschlagenes Emoji |
|---------|----------------------|
| System-Monitoring | 📊 |
| Performance-Optimierung | ⚡ |
| Bereitschaftschecks | 🚨 |
| Temperatur-Überwachung | 🌡️ |
| Speicher-Management | 💾 |
| Load-Awareness | 📈 |
| CPU | 🖥️ |
| Warnung | ⚠️ |
| Fehler | ❌ |
| Erfolg | ✅ |

### Integration in CI/CD

Das Skript kann in CI/CD-Pipelines integriert werden:

```yaml
# .github/workflows/emoji-check.yml
name: Emoji Validation

on: [push, pull_request]

jobs:
  check-emojis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check Emojis
        run: python3 tools/check_emojis.py
```

### Exit-Codes

- `0` - Keine Probleme gefunden
- `1` - Defekte Emojis gefunden

## 🧪 test_ai_features.py - AI-Feature Tests

### Beschreibung
Testet die KI-Funktionen des Projekts.

### Verwendung
```bash
python3 tools/test_ai_features.py
```

## 📝 automation_test.txt - Automatisierungs-Tests

### Beschreibung
Dokumentation der Automatisierungs-Tests.

## 🤝 Beitragen

Wenn Sie neue Tools hinzufügen möchten:

1. Erstellen Sie das Tool im `tools/` Verzeichnis
2. Dokumentieren Sie es in dieser README
3. Fügen Sie Beispiele zur Verwendung hinzu
4. Erstellen Sie einen Pull Request

## 📄 Lizenz

Siehe [LICENSE](../LICENSE) Datei für Details.
