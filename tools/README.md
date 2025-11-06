# 🛠️ Development & Testing Tools

Dieses Verzeichnis enthält verschiedene Entwicklungs- und Test-Tools für das Vogel-Kamera-Linux Projekt.

## 🔧 Installation

```bash
# Dependencies installieren (im venv empfohlen)
source venv/bin/activate
pip install -r tools/requirements.txt
```

## ❓ Übersicht

| Tool | Beschreibung | Verwendung |
|------|--------------|------------|
| `analyze_video_bird_content.py` | Video-Analyse mit YOLOv8 | Analysiert MP4-Videos auf Vogelanteil |
| `local-system-status.py` | Lokaler System-Monitor | Prüft CPU, RAM, Festplatte, Last (ohne SSH) |
| `check_emojis.py` | Emoji-Validator für Markdown-Dateien | Prüft alle Dokumente auf defekte Emojis |
| `test_ai_features.py` | AI-Feature Tests | Testet KI-Funktionen |
| `automation_test.txt` | Automatisierungs-Tests | Test-Dokumentation |

---

## 🎬 analyze_video_bird_content.py - Video-Analyse

### Beschreibung
Analysiert MP4-Videos auf Vogelanteil mit YOLOv8-basierter KI-Erkennung. Perfekt zum Filtern von Aufnahmen mit geringem Vogelanteil.

### Features
- 🐦 **YOLOv8-Erkennung**: State-of-the-art Bird Detection
- 📊 **Statistiken**: Vogelanteil, Detektionen, Segmente
- ⚡ **Sample-Rate**: Analyse jeden N-ten Frame für höhere Geschwindigkeit
- 🗑️ **Auto-Delete**: Lösche Verzeichnisse mit 0% Vogelanteil
- 📝 **Logging**: Speichere Output in `/var/log/vogel-kamera-linux/`
- 💾 **JSON-Export**: Strukturierte Reports für Automatisierung
- 🎯 **Batch-Processing**: Mehrere Videos gleichzeitig analysieren
- 🔍 **Modell-Suche**: Automatisches Finden von Modellen in `models/` oder `config/models/`

### Verwendung

```bash
# Einzelnes Video analysieren
python3 tools/analyze_video_bird_content.py video.mp4

# Mehrere Videos mit Sample-Rate (schneller)
python3 tools/analyze_video_bird_content.py --sample-rate 5 *.mp4

# Mit Logging
python3 tools/analyze_video_bird_content.py --log *.mp4

# Verzeichnisse mit 0% automatisch löschen
python3 tools/analyze_video_bird_content.py --delete --sample-rate 5 *.mp4

# Eigenes Modell verwenden (sucht in models/ oder config/models/)
python3 tools/analyze_video_bird_content.py --model bird-species.pt video.mp4

# JSON-Report exportieren
python3 tools/analyze_video_bird_content.py --output report.json video.mp4
```

**Beispiel-Ausgabe:**
```
🤖 Lade YOLO-Modell: yolov8n.pt
📝 Log-Datei: /var/log/vogel-kamera-linux/2025/45/2025-11-06_14-30-15-analyse.log
======================================================================

📊 VOGEL-ANALYSE REPORT
======================================================================

📹 Video: video.mp4
   Dauer: 0:02:45
   
🐦 Ergebnisse:
   Vogelanteil: 12.5%
   Detektionen: 234
   
======================================================================
🎯 GESAMTSTATISTIK (2 Videos)
======================================================================

Verzeichnis                              Dauer    Vögel   Status
────────────────────────────────────────────────────────────────────
Mittwoch__2025-11-05__14-02-06          02:45    12.5%   ✅
Donnerstag__2025-11-06__09-15-32        01:30     0.0%   ❌

Gesamt: 2 Videos, 04:15 Minuten, ⌀ 6.3% Vogelanteil
======================================================================
```

### Modell-Verwaltung

Das Skript sucht Modelle automatisch in dieser Reihenfolge:
1. `models/` (für eigene trainierte Modelle)
2. `config/models/` (alternative Location)
3. Aktuelles Verzeichnis
4. Ultralytics Cache (`~/.cache/ultralytics/`)

Standard-Modelle (yolov8n.pt) werden beim ersten Aufruf automatisch heruntergeladen.

---

## 📊 local-system-status.py - Lokaler System-Monitor

### Beschreibung
Liest lokale Systemparameter aus (CPU-Temperatur, RAM, Festplatte, Last) direkt auf dem Host - analog zu den Remote-Status-Abfragen, aber **ohne SSH**. Ideal für Preflight-Checks, lokales Debugging und System-Monitoring.

### Features
- 🌡️ **CPU-Temperatur**: vcgencmd (Raspberry Pi) oder /sys/class/thermal (Linux)
- 💾 **Festplattenbelegung**: df-basiert mit Prozent-Anzeige
- 💭 **RAM-Auslastung**: free-basiert mit Prozent-Berechnung
- ⚡ **System-Last**: Load Average (1min, 5min, 15min)
- 🎨 **Farbcodierte Ausgabe**: Status-Emojis (🟢 🟡 🔴)
- 📊 **JSON-Export**: Für Automatisierung und Skript-Integration
- ⚠️ **Schwellenwert-Prüfung**: Warnungen bei kritischen Werten
- 🔄 **Exit-Codes**: 0=OK, 1=Kritisch (für Bash-Integration)

### Verwendung

#### Standard-Ausgabe (formatiert mit Farben)
```bash
python3 tools/local-system-status.py
```

**Beispiel-Ausgabe:**
```
======================================================================
📊 Lokaler System-Status
======================================================================
🖥️  Host: raspberrypi-5-nvme-04
🕐 Zeit: 2025-10-01 23:33:12
⏱️  Uptime: 1 hour, 11 minutes
🐧 Kernel: 6.12.47+rpt-rpi-2712

Hardware & Ressourcen:
   🌡️  CPU-Temp: 45.5°C 🟢
   ⚡ CPU-Load: 0.89 🟢 (5min: 0.92, 15min: 0.87)
   💭 RAM: 2.5Gi / 8Gi (31.3%) 🟢
      └─ Verfügbar: 5.2Gi
   💾 Festplatte: 45G / 197G (23%) 🟢
      ├─ Verfügbar: 142G
      └─ Mount: / (/dev/nvme0n1p2)

System-Status:
   ✅ System läuft im normalen Bereich
======================================================================
```

#### JSON-Format (für Automatisierung)
```bash
python3 tools/local-system-status.py --json
```

**Beispiel-Ausgabe:**
```json
{
  "cpu_temperature": 45.5,
  "disk_usage": {
    "filesystem": "/dev/nvme0n1p2",
    "size": "197G",
    "used": "45G",
    "available": "142G",
    "use_percent": 23,
    "mount_point": "/"
  },
  "memory_usage": {
    "total": "8Gi",
    "used": "2.5Gi",
    "free": "4.8Gi",
    "available": "5.2Gi",
    "use_percent": 31.3
  },
  "system_load": {
    "load_1min": 0.89,
    "load_5min": 0.92,
    "load_15min": 0.87
  },
  "uptime": "1 hour, 11 minutes",
  "timestamp": "2025-10-01T23:33:12.123456",
  "hostname": "raspberrypi-5-nvme-04",
  "kernel": "6.12.47+rpt-rpi-2712",
  "healthy": true,
  "thresholds": {
    "cpu_temp": {"good": 50.0, "warning": 60.0, "critical": 70.0},
    "disk_usage": {"good": 70, "warning": 80, "critical": 90},
    "cpu_load": {"good": 1.0, "warning": 2.0, "critical": 3.0},
    "memory_percent": {"good": 70, "warning": 85, "critical": 95}
  }
}
```

#### Health-Check (nur Exit-Code)
```bash
python3 tools/local-system-status.py --check
# Exit-Code: 0=OK, 1=Kritisch
```

**Verwendung in Bash-Skripten:**
```bash
if python3 tools/local-system-status.py --check; then
    echo "✅ System OK - starte Aufnahme..."
    python3 ai-had-kamera-auto-trigger.py
else
    echo "⚠️ System kritisch - Aufnahme übersprungen"
    exit 1
fi
```

#### Mit Schwellenwerten
```bash
python3 tools/local-system-status.py --thresholds
```

Zeigt die konfigurierten Schwellenwerte für jeden Parameter an.

### Schwellenwerte

| Parameter | Gut 🟢 | Warnung 🟡 | Kritisch 🔴 |
|-----------|--------|------------|-------------|
| CPU-Temp | < 50°C | 50-60°C | > 70°C |
| CPU-Load | < 1.0 | 1.0-2.0 | > 3.0 |
| RAM | < 70% | 70-85% | > 95% |
| Festplatte | < 70% | 70-80% | > 90% |

### Anwendungsfälle

#### 1. Preflight-Check vor Aufnahme
```bash
#!/bin/bash
echo "🔍 Prüfe System-Status..."
if python3 tools/local-system-status.py --check; then
    echo "✅ System bereit"
    python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py
else
    echo "❌ System nicht bereit - bitte prüfen"
    python3 tools/local-system-status.py  # Zeige Details
    exit 1
fi
```

#### 2. Monitoring-Dashboard (JSON)
```bash
# Hole Status als JSON und verarbeite mit jq
python3 tools/local-system-status.py --json | jq '.cpu_temperature'
python3 tools/local-system-status.py --json | jq '.memory_usage.use_percent'
```

#### 3. Cron-Job für Alarm
```bash
# /etc/cron.d/system-check
*/15 * * * * user cd /path/to/vogel-kamera && python3 tools/local-system-status.py --check || mail -s "System kritisch" admin@example.com
```

#### 4. Integration in Auto-Trigger
```python
import subprocess
import json

# Hole System-Status
result = subprocess.run(
    ["python3", "tools/local-system-status.py", "--json"],
    capture_output=True, text=True
)
status = json.loads(result.stdout)

if status['healthy']:
    print("✅ System OK - starte Auto-Trigger")
else:
    print(f"⚠️ CPU-Temp: {status['cpu_temperature']}°C - überspringe Trigger")
```

### Kompatibilität

- ✅ **Raspberry Pi**: Volle Unterstützung mit vcgencmd
- ✅ **Linux (generic)**: Fallback auf /sys/class/thermal
- ✅ **Debian/Ubuntu**: Getestet
- ⚠️ **macOS/Windows**: Eingeschränkte Unterstützung (keine CPU-Temp)

### Unterschied zu Remote-Monitoring

| Feature | `local-system-status.py` | Remote-Monitoring (SSH) |
|---------|-------------------------|-------------------------|
| **Ausführung** | Lokal auf Host | Remote via SSH |
| **Benötigt SSH** | ❌ Nein | ✅ Ja |
| **Verwendung** | Preflight, Debugging | Remote-Host Status |
| **Authentifizierung** | Keine | SSH-Keys |
| **Latenz** | Minimal | Abhängig von Netzwerk |
| **Use-Case** | Lokale Checks | Raspberry Pi Monitoring |

---

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
