# 📚 Dokumentations-Übersicht (v2.1.0)

## 🎯 Schnelleinstieg (NEU!)

### Für Einsteiger (Unified Monitor Client)
1. **[../README.md](../README.md)** - Haupt-Übersicht, Features, Zwei Modi
2. **[../QUICK-START-PYTHON.md](../QUICK-START-PYTHON.md)** - Installation und erste Befehle
3. **[../unified-monitor-client/README.md](../unified-monitor-client/README.md)** - Client Details

### Für erfahrene Nutzer
1. **[ARCHITEKTUR.md](ARCHITEKTUR.md)** - Technische Architektur (AUTO-RECORD vs MANUAL-RECORD)
2. **[AI-MODELLE-VOGELARTEN.md](AI-MODELLE-VOGELARTEN.md)** - KI-Modelle für Vogelarten
3. **[ANLEITUNG-EIGENES-AI-MODELL.md](ANLEITUNG-EIGENES-AI-MODELL.md)** - Custom Training

---

## 📖 Dokumentations-Kategorien (v2.1.0)

### 🖥️ Unified Monitor Client (Standard ab v2.1.0)

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[../QUICK-START-PYTHON.md](../QUICK-START-PYTHON.md)** | Schnellstart mit --auto-record und --manual-record | Alle |
| **[../unified-monitor-client/README.md](../unified-monitor-client/README.md)** | Vollständige Client-Dokumentation | Alle |
| **[ARCHITEKTUR.md](ARCHITEKTUR.md)** | Detaillierte Architektur: picamera2 vs rpicam-vid | Entwickler |

### 🤖 KI-Erkennung mit YOLO26n

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[AI-MODELLE-VOGELARTEN.md](AI-MODELLE-VOGELARTEN.md)** | Vortrainierte Vogelarten-Modelle | Alle |
| **[ANLEITUNG-EIGENES-AI-MODELL.md](ANLEITUNG-EIGENES-AI-MODELL.md)** | Training eigener Modelle | Fortgeschritten |

### 🔐 Sicherheit & Wartung

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[SECURITY.md](SECURITY.md)** | SSH-Sicherheit & Best Practices | Sysadmin |
| **[TRIXIE-MIGRATION.md](TRIXIE-MIGRATION.md)** | Debian 13 Trixie Migration | Sysadmin |

### 🎬 Legacy Auto-Trigger Dokumentation (< v2.0)

> ⚠️ **Veraltet:** Diese Dokumentation bezieht sich auf alte Versionen. Für v2.1.0+ nutzen Sie die Unified Monitor Client Dokumentation oben.

#### Auto-Trigger System (v1.x)
| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| **[AUTO-TRIGGER-DOKUMENTATION.md](AUTO-TRIGGER-DOKUMENTATION.md)** | Auto-Trigger Dokumentation | ⚠️ Legacy |
| **[QUICKSTART-AUTO-TRIGGER.md](QUICKSTART-AUTO-TRIGGER.md)** | Auto-Trigger Quickstart | ⚠️ Legacy |

#### Stream & Performance (v1.x)
| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| **[PREVIEW-STREAM-SETUP.md](PREVIEW-STREAM-SETUP.md)** | RTSP Stream Setup | ⚠️ Legacy |
| **[AUTO-TRIGGER-PERFORMANCE-OPTIMIZATION.md](AUTO-TRIGGER-PERFORMANCE-OPTIMIZATION.md)** | Performance Tuning | ⚠️ Legacy |

### 📋 Release Notes

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| **[../releases/v2.1.0/RELEASE_NOTES_v2.1.0.md](../releases/v2.1.0/RELEASE_NOTES_v2.1.0.md)** | v2.1.0: Audio/Video Sync | 🟢 Aktuell |
| **[../AUDIO-FIX-CHANGELOG.md](../AUDIO-FIX-CHANGELOG.md)** | Audio-Integration Changelog | 🟢 Aktuell |
| **[../CHANGELOG.md](../CHANGELOG.md)** | Kompletter Changelog | 🟢 Aktuell |

---

## 🎓 Lernpfade (v2.1.0)

### Pfad 1: Erste Schritte (Einsteiger)
```
1. README.md (Überblick, Features, Zwei Modi)
   └─> 2. QUICK-START-PYTHON.md (Installation)
       └─> 3. unified-monitor-client/README.md (Client Details)
           └─> 4. Erste --auto-record oder --manual-record Session
```

### Pfad 2: Auto-Record Monitoring optimal nutzen
```
1. QUICK-START-PYTHON.md (--auto-record Beispiele)
   └─> 2. ARCHITEKTUR.md (Verstehen: picamera2 + YOLO26n)
       └─> 3. AI-MODELLE-VOGELARTEN.md (KI-Modelle)
           └─> 4. ANLEITUNG-EIGENES-AI-MODELL.md (Custom Models)
```

### Pfad 3: Manual-Record für geplante Sessions
```
1. QUICK-START-PYTHON.md (--manual-record Beispiele)
   └─> 2. ARCHITEKTUR.md (Verstehen: rpicam-vid Backend)
       └─> 3. Eigene Record-Automatisierung bauen
```

### Pfad 4: Erweitert & Troubleshooting
```
1. ARCHITEKTUR.md (Systemverständnis)
   └─> 2. SECURITY.md (SSH & Sicherheit)
       └─> 3. TRIXIE-MIGRATION.md (Betriebssystem)
           └─> 4. Log-Analyse & Debugging
```

---

## 🔍 Häufige Fragen & Wegweiser

### Frage: Welchen Modus soll ich nutzen?
→ **Siehe:** [../README.md > Zwei Modi - Eine Lösung](../README.md#-zwei-modi---eine-lösung)

### Frage: Wie installiere ich?
→ **Siehe:** [../QUICK-START-PYTHON.md > Vorbereitungen](../QUICK-START-PYTHON.md)

### Frage: Ich möchte Auto-Record (Vogel-Erkennung) nutzen
→ **Siehe:** [../QUICK-START-PYTHON.md > AUTO-RECORD](../QUICK-START-PYTHON.md)

### Frage: Ich möchte Manual-Record (geplante Aufnahmen)
→ **Siehe:** [../QUICK-START-PYTHON.md > MANUAL-RECORD](../QUICK-START-PYTHON.md)

### Frage: Wie trainiere ich ein eigenes KI-Modell?
→ **Siehe:** [ANLEITUNG-EIGENES-AI-MODELL.md](ANLEITUNG-EIGENES-AI-MODELL.md)

### Frage: Wie funktioniert das System technisch?
→ **Siehe:** [ARCHITEKTUR.md > Dual-Architecture](ARCHITEKTUR.md)

### Frage: Ich nutze noch Bookworm (Debian 12)
→ **Siehe:** [TRIXIE-MIGRATION.md](TRIXIE-MIGRATION.md) oder nutze Branch `bookworm-legacy`
- **Emoji:** 📊

### Stream-Management
**Problem:** Stream startet nicht oder stoppt
- **Siehe:** [PREVIEW-STREAM-SETUP.md](PREVIEW-STREAM-SETUP.md)
- **Emoji:** 📺

### Netzwerk-Probleme
**Problem:** Verbindungsfehler, Timeouts
- **Siehe:** [network-tools/README.md](../network-tools/README.md)
- **Emoji:** 🌐

### Parameter-Verwirrung
**Problem:** Welche Parameter wofür?
- **Siehe:** [PARAMETER-NO-STREAM-RESTART.md](PARAMETER-NO-STREAM-RESTART.md)
- **Emoji:** 🔧

---

## 📝 Emoji-Legende

### Status-Emojis
- ✅ **Erfolgreich / Aktiviert**
- ❌ **Fehler / Deaktiviert**
- ⚠️ **Warnung / Vorsicht**
- ℹ️ **Information**
- 🔧 **Konfiguration / Einstellung**
- 📝 **Dokumentation**
- 🧪 **Testing / Experimental**

### Funktions-Emojis
- 🐦 **Vogel-Erkennung**
- 🎬 **Video-Aufnahme**
- 🎤 **Audio-Aufnahme**
- 📡 **Stream / RTSP**
- 🔄 **Neustart / Reload**
- 🚀 **Start / Launch**
- 🛑 **Stop / Beenden**
- ⏸️ **Pause**
- ⏭️ **Überspringen**

### System-Emojis
- 🖥️ **Client-PC**
- 🍓 **Raspberry Pi**
- 🌐 **Netzwerk**
- 🔥 **Firewall**
- 🔐 **SSH / Sicherheit**
- 💾 **Speicher / Dateien**
- 📊 **Performance / Statistiken**
- 🎯 **Trigger / Schwellenwert**

### Qualitäts-Emojis
- ⭐⭐⭐⭐⭐ **Exzellent (5/5)**
- ⭐⭐⭐⭐ **Gut (4/5)**
- ⭐⭐⭐ **OK (3/5)**
- ⭐⭐ **Schwach (2/5)**
- ⭐ **Sehr schwach (1/5)**

### Status-Farben (Text)
- 🟢 **Grün: Gut / Aktiv / Production**
- 🟡 **Gelb: Warnung / Limitiert**
- 🔴 **Rot: Fehler / Kritisch**
- 🔵 **Blau: Information**
- ⚫ **Grau: Inaktiv / Deaktiviert**

---

## 🔄 Dokumentations-Updates

### Letzte Änderungen (v1.2.0)
- ✅ **03.10.2025**: Performance-Optimierung dokumentiert
- ✅ **02.10.2025**: `--no-stream-restart` Parameter hinzugefügt
- ✅ **01.10.2025**: Auto-Trigger System vollständig dokumentiert

### Geplante Updates
- 📝 Web-Interface Dokumentation (v1.3.0)
- 📝 Mobile App Guide (v1.3.0)
- 📝 Multi-Kamera Setup (v1.3.0)

---

## 💡 Dokumentations-Tipps

### Beim Lesen
1. **Starte mit dem README.md** für Überblick
2. **Nutze die Emoji-Legende** zum schnellen Erfassen
3. **Folge den internen Links** für Details
4. **Prüfe das Datum** der Dokumentation

### Beim Schreiben
1. **Nutze Emojis konsistent** (siehe Legende)
2. **Verlinke verwandte Docs** für Kontext
3. **Füge Code-Beispiele hinzu** wo sinnvoll
4. **Update DOKUMENTATION-UEBERSICHT.md** bei neuen Docs

### Beim Troubleshooting
1. **Prüfe Release Notes** für bekannte Probleme
2. **Nutze Guided Tests** zum Debugging
3. **Aktiviere Debug-Logs** für Details
4. **Suche in GitHub Issues** nach Lösungen

---

## 📞 Hilfe & Support

### Dokumentation fehlt?
- **Erstelle ein Issue**: [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
- **Schlage Änderungen vor**: [Pull Request](https://github.com/kamera-linux/vogel-kamera-linux/pulls)

### Fragen?
- **Diskussionen**: [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)
- **Wiki**: [GitHub Wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki)

---

**📚 Viel Erfolg mit der Dokumentation! Bei Fragen einfach melden! 🙋‍♂️**
