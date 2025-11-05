# 🚀 Release Notes v1.2.0

**Release:** Auto-Trigger System & Stream-Management  
**Datum:** 01. Oktober 2025  
**Version:** v1.2.0  
**Branch:** main  

---

## 📋 Übersicht

Version 1.2.0 führt das **Auto-Trigger System** ein - eine vollautomatische Vogel-Überwachung mit KI-gestützter Erkennung und intelligenter Aufnahmesteuerung. Das System erkennt Vögel in Echtzeit über einen Preview-Stream und startet automatisch hochauflösende Aufnahmen.

---

## ✨ Neue Features

### 🎯 Auto-Trigger System
**Kernfunktionalität:** Automatische Vogel-Erkennung und Aufnahmesteuerung

#### Trigger-Duration Logic
- **2-Sekunden-Konsistenz-Check**: Vogel muss 2 Sekunden lang sichtbar sein
- **70% Detection Rate**: Mindestens 70% der Frames müssen Vogel zeigen
- **Vermeidet False Positives**: Keine zufälligen Trigger durch Bewegungen

#### Intelligente Schwellenwerte
- **Standard: 0.60** (balanciert zwischen Präzision und Recall)
- **Getestet mit 0.45** (zu viele False Positives)
- **Getestet mit 0.70** (sehr stabil, aber konservativ)
- **Anpassbar** über Parameter `--trigger-threshold`

#### Status-Reports Optimierung
- **Pausierung während Aufnahme**: Reduziert Systemlast
- **Pausierung während Cooldown**: Keine störenden Meldungen
- **Automatische Wiederaufnahme**: Nach erfolgreicher Aufnahme
- **Gesamtdauer Pause**: ~3 Minuten (Aufnahme + Transfer + Neustart + Cooldown)

### 📺 Preview-Stream System
**RTSP-Stream für Echtzeit-Überwachung**

#### Technische Specs
- **Auflösung**: 640x480 @ 5fps
- **Codec**: H.264 TCP
- **Bitrate**: 1 Mbps
- **Port**: 8554
- **URL**: `rtsp://raspberry-pi-ip:8554/stream`

#### Stream-Management
- **Automatischer Start**: Stream startet bei Bedarf
- **Watchdog**: Überwacht Stream-Stabilität
- **Auto-Restart**: Nach HD-Aufnahmen automatisch neu gestartet
- **Persistenz**: `bash -c` mit `disown` für zuverlässigen Hintergrund-Betrieb

#### Stream-Wrapper
- **PID-Management**: Saubere Prozess-Verwaltung
- **Status-Checks**: `--status` für Monitoring
- **Cleanup**: Automatisches Beenden bei System-Shutdown

### 🔧 Stream-Lifecycle Management

#### Kamera-Exklusivität
- **Problem gelöst**: HD-Aufnahmen blockierten durch Preview-Stream
- **Lösung**: Automatisches Stoppen des Streams vor HD-Aufnahme
- **Neustart**: Stream wird nach Aufnahme wieder gestartet

#### Cleanup-Automation
- **Bash Traps**: SIGINT, SIGTERM, EXIT
- **Remote Process Cleanup**: Alle Prozesse inkl. Watchdog
- **PID-File Cleanup**: `/tmp/*.pid` werden aufgeräumt

### 🎨 Benutzerfreundlichkeit

#### Wrapper-Skript: `start-vogel-beobachtung.sh`
```bash
./kamera-auto-trigger/start-vogel-beobachtung.sh
```
**Features:**
- ✅ Interaktive Parameter-Auswahl
- ✅ Voreinstellungen (Standard: 0.60)
- ✅ Automatisches Stream-Management
- ✅ Status-Anzeige
- ✅ Cleanup bei Beendigung

#### Guided Test System
```bash
./kamera-auto-trigger/tests/guided-test.sh
```
**Testszenarien:**
- Stream-Verbindung prüfen
- Trigger-System mit niedrigem Threshold (0.2)
- Produktions-Setup mit 0.60

### 🌐 Netzwerk-Diagnostics

#### Network Quality Test Tool
```bash
python3 network-tools/test-network-quality.py
```
**Messungen:**
- 🏓 **Ping-Test**: Latenz und Paketverlust
- 🔐 **SSH-Verbindungszeit**: 5 Versuche
- 📊 **Bandbreiten-Test**: 10 MB Upload/Download
- ⚡ **Befehls-Latenz**: Remote-Command Performance

**Ausgabe:**
- Farbcodierte Status-Anzeigen (🟢🟡🔴)
- Durchschnittswerte und Bewertungen
- Handlungsempfehlungen bei Problemen

### 🗂️ YOLO-Modell Zentralisierung

#### Neue Struktur
```
config/
└── models/
    └── yolov8n.pt  (6.3 MB, zentral verwaltet)
```
**Vorteile:**
- ✅ Kein wiederholtes Herunterladen
- ✅ Explizite Pfadangabe in allen Skripten
- ✅ Versionskontrolle möglich

### 🎤 Audio-Recording Fixes

#### Problem: Stereo nicht unterstützt
- USB-Gerät hw:2,0 unterstützt nur Mono

#### Lösung: Mono-Format
```bash
arecord -D hw:2,0 -f S16_LE -r 44100 -c 1 -t wav
```
**Format-Details:**
- `-f S16_LE`: Signed 16-bit Little Endian
- `-r 44100`: 44.1 kHz Samplerate
- `-c 1`: Mono (1 Kanal)
- `-t wav`: WAV Container

### 🔒 Firewall-Setup

#### Client-PC
```bash
./kamera-auto-trigger/setup-firewall-client-pc.sh
```
**Regeln:**
- Ausgehend: Port 8554 (RTSP)
- Ausgehend: Port 22 (SSH)

#### Raspberry Pi
```bash
./kamera-auto-trigger/setup-firewall-raspberry-pi.sh
```
**Regeln:**
- Eingehend: Port 8554 (RTSP)
- Eingehend: Port 22 (SSH)

---

## 🐛 Bugfixes

### Video-Recording Kamera-Blocking
- **Problem**: HD-Aufnahmen schlugen fehl wenn Preview-Stream lief
- **Root Cause**: `stream-wrapper.sh` mit Auto-Restart Loop
- **Fix**: Wrapper wird ZUERST beendet, dann rpicam-vid

### Audio-Recording Failure
- **Problem**: `arecord` Fehler "Kanalanzahl nicht unterstützt"
- **Root Cause**: Stereo `-c 2` auf Mono-only Gerät
- **Fix**: Mono-Format `-c 1 -f S16_LE`

### Stream-Restart Nicht Persistent
- **Problem**: `nohup ~/start-rtsp-stream.sh &` starb nach SSH-Disconnect
- **Root Cause**: SSH-Session wurde mit Prozess beendet
- **Fix**: `bash -c 'nohup ~/start-rtsp-stream.sh > /tmp/stream-restart.log 2>&1 & disown'`

### False Positive Triggers
- **Problem**: Sofortige Trigger ohne Wartezeit
- **Root Cause**: Keine Trigger-Duration Logic
- **Fix**: 2s Konsistenz-Check mit 70% Detection Rate

---

## 📁 Neue Dateien

### Kamera-Auto-Trigger System
```
kamera-auto-trigger/
├── README.md                                  # Hauptdokumentation
├── start-vogel-beobachtung.sh               # User-friendly Wrapper ⭐
├── run-auto-trigger.sh                      # Core-Skript
├── run-stream-test.sh                       # Stream-Verbindungstest
├── setup-firewall-client-pc.sh             # Firewall Client
├── setup-firewall-raspberry-pi.sh          # Firewall Raspberry Pi
├── requirements.txt                         # Python-Dependencies
├── scripts/
│   ├── ai-had-kamera-auto-trigger.py      # Haupt-Orchestrierung
│   └── stream_processor.py                 # AI-Detection Logic
├── docs/
│   ├── AUTO-TRIGGER-DOKUMENTATION.md      # Technische Details
│   ├── QUICKSTART-AUTO-TRIGGER.md         # Schnellstart-Anleitung
│   ├── PREVIEW-STREAM-SETUP.md            # Stream-Konfiguration
│   ├── FIREWALL-SETUP-SUMMARY.md          # Firewall-Übersicht
│   └── AUTO-TRIGGER-OVERVIEW.md           # System-Überblick
└── tests/
    ├── guided-test.sh                      # Interaktiver Test
    └── test-auto-trigger.sh               # Automatisierter Test
```

### Raspberry Pi Scripts
```
raspberry-pi-scripts/
├── start-rtsp-stream.sh                    # RTSP-Stream Management ⭐
├── start-preview-stream.sh                 # Preview-Stream Alt
├── start-preview-stream-v2.sh             # Preview-Stream v2
└── start-preview-stream-watchdog.sh       # Stream-Watchdog
```

### Configuration
```
config/
├── README.md                               # Config-Dokumentation
├── models/
│   └── yolov8n.pt                         # YOLO-Modell (6.3 MB)
└── ssh-config.sh                          # SSH-Key Setup
```

### Network Tools
```
network-tools/
├── test-network-quality.py                 # Netzwerk-Qualitäts-Test ⭐
└── README.md                               # Tool-Dokumentation ⭐
```

### Root Level
```
requirements.txt                            # Root-Level Dependencies
```

### Documentation
```
docs/
└── SYSTEM-READY.md                        # Production-Ready Status
```

---

## 🔧 Technische Änderungen

### scripts/version.py
- Version: `1.1.9` → `1.2.0`
- Release Name: `"Auto-Trigger System & Stream-Management"`
- Build Number: `20250930` → `20251001`
- Git Tag: `v1.1.9` → `v1.2.0`
- Neue Features: `auto_trigger`, `preview_stream`, `trigger_duration_logic`, `stream_management`, `network_diagnostics`

### python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py
- **Kein** Stream-Restart im Fehlerfall (für Auto-Trigger)
- `--no-stream-restart` Flag hinzugefügt und implementiert (v1.2.0)
- Stream-Neustart nur wenn Skript vorhanden
- Parameter empfohlen für On-Demand Aufnahmen (spart 2 Sekunden)
- Auto-Trigger setzt Parameter automatisch
- Dokumentation: [`docs/PARAMETER-NO-STREAM-RESTART.md`](../docs/PARAMETER-NO-STREAM-RESTART.md)

---

## 📊 Testing

### Threshold-Tests (durchgeführt)
| Threshold | Ergebnis | Bewertung |
|-----------|----------|-----------|
| 0.45 | Sofortige False Positives | ❌ Zu niedrig |
| 0.60 | Balanciert | ✅ **Empfohlen** |
| 0.70 | Keine Trigger in 60s, 28 Frames | ✅ Sehr stabil |

### Stream-Restart Tests
- ✅ `bash -c` mit `disown` funktioniert
- ✅ Stream persistiert nach SSH-Disconnect
- ✅ PID-Management funktioniert
- ✅ Status-Checks verlässlich

### Trigger-Duration Tests
- ✅ 2s Konsistenz-Check verhindert False Positives
- ✅ 70% Detection Rate ist optimal
- ✅ Status-Reports pausieren korrekt

---

## 🚀 Migration von v1.1.9

### Erforderliche Schritte

1. **Branch wechseln:**
   ```bash
   git checkout devel-v1.2.0
   git pull origin devel-v1.2.0
   ```

2. **Dependencies installieren:**
   ```bash
   pip install -r kamera-auto-trigger/requirements.txt
   ```

3. **YOLO-Modell platzieren:**
   ```bash
   # Modell wird automatisch heruntergeladen nach config/models/
   # beim ersten Start des Auto-Trigger Systems
   ```

4. **Firewall konfigurieren (optional):**
   ```bash
   # Client-PC
   ./kamera-auto-trigger/setup-firewall-client-pc.sh
   
   # Raspberry Pi
   ./kamera-auto-trigger/setup-firewall-raspberry-pi.sh
   ```

5. **Stream-Skript auf Raspberry Pi kopieren:**
   ```bash
   scp raspberry-pi-scripts/start-rtsp-stream.sh \
       user@raspberry-pi:~/
   ```

### Rückwärts-Kompatibilität
- ✅ Alle v1.1.9 Skripte funktionieren weiterhin
- ✅ Keine Breaking Changes in bestehenden APIs
- ✅ Neue Features sind opt-in

---

## 📚 Dokumentation

### Neue Anleitungen
- [`QUICKSTART-AUTO-TRIGGER.md`](../kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md) - Schnellstart
- [`AUTO-TRIGGER-DOKUMENTATION.md`](../kamera-auto-trigger/docs/AUTO-TRIGGER-DOKUMENTATION.md) - Technische Details
- [`PREVIEW-STREAM-SETUP.md`](../kamera-auto-trigger/docs/PREVIEW-STREAM-SETUP.md) - Stream-Setup
- [`FIREWALL-SETUP-SUMMARY.md`](../kamera-auto-trigger/docs/FIREWALL-SETUP-SUMMARY.md) - Firewall-Konfiguration

### Aktualisierte Dokumentation
- [`README.md`](../README.md) - Hauptdokumentation mit v1.2.0 Features
- [`SYSTEM-READY.md`](../docs/SYSTEM-READY.md) - Production-Ready Status

---

## 🎯 Bekannte Limitationen

### Netzwerk
- WLAN: Niedrige Bandbreite (~1-2 MB/s Upload/Download)
- SSH-Verbindungszeit: Hoch (Ø 7.3s, max 22.7s)
- **Empfehlung**: Ethernet-Kabel verwenden für bessere Performance

### Hardware
- Raspberry Pi 5 empfohlen (getestet)
- Raspberry Pi 4B funktioniert, aber langsamer
- USB-Audio: Nur Mono-Geräte getestet

### Software
- Python 3.11.2 getestet (ältere Versionen ungetestet)
- VLC Player empfohlen für RTSP-Streams
- Linux-basiertes Client-System empfohlen

---

## ⚡ Performance-Optimierungen (v1.2.0 Updates)

### CPU-Last Optimierung (Oktober 2025)

**Problem:** Nach Aktivierung der CPU-Thread-Limitierung (`OMP_NUM_THREADS=2`) sank die Auto-Trigger Performance dramatisch:
- ❌ Von 33 Trigger in 10h 52min → 3 Trigger in 4h (-75%)
- ❌ Grund: 3 FPS × 2s = nur 6 Frames (zu wenig für 70% Konsistenz)

**Lösung 1 - Aggressive Optimierung:**
```bash
--preview-fps 5           # 3 → 5 (+67% Frames)
--preview-width 480       # 320 → 480 (+50% Breite)
--preview-height 360      # 240 → 360 (+50% Höhe)
--trigger-threshold 0.38  # 0.45 → 0.38 (sensitiver)
```
- ✅ Trigger-Rate wiederhergestellt
- ❌ CPU-Last: 82.6% (zu hoch für Dauerbetrieb)

**Lösung 2 - CPU-optimierter Kompromiss (AKTUELL):**
```bash
--preview-fps 4           # 5 → 4 (-20% Frames)
--preview-width 400       # 480 → 400 
--preview-height 300      # 360 → 300 (-30% Pixel)
--trigger-threshold 0.40  # 0.38 → 0.40 (weniger sensitiv)
```

**Mathematik:**
- 4 FPS × 2s = 8 Frames
- 65% Konsistenz = 5.2 Frames müssen Vogel zeigen
- 400×300 = 120.000 Pixel/Frame × 4 FPS = 480.000 Pixel/Sek
- Vergleich zu aggressiv: 576.000 Pixel/Sek → **-16.7% Daten**

**Erwartete Ergebnisse:**
- 🎯 CPU-Auslastung: 50-60% (statt 82.6%)
- 🐦 Trigger-Rate: 2-2.5 pro Stunde
- ⚡ Erkennungsqualität: Gut (400x300 > 320x240 ursprünglich)

### Stream-Restart Optimierung

**Neuer Parameter:** `--no-stream-restart` (v1.2.0)

**Anwendung:**
- ✅ **On-Demand Aufnahmen**: Spart 2 Sekunden, Stream nicht benötigt
- ⚙️ **Auto-Trigger**: Automatisch gesetzt, Stream-Management durch Auto-Trigger

**Dokumentation:**
- 📄 `docs/PARAMETER-NO-STREAM-RESTART.md`
- 📄 `docs/AUTO-TRIGGER-STREAM-RESTART.md`

---

## 🔮 Ausblick auf v1.3.0

### Geplante Features
- **Web-Interface**: Browser-basierte Steuerung
- **Mobile App**: Android/iOS Companion App
- **Multi-Stream**: Mehrere Kameras gleichzeitig
- **Cloud-Upload**: Automatischer Upload zu Cloud-Speicher
- **Vogelarten-Erkennung**: Spezifische Arten identifizieren

---

## 👥 Contributors

Vielen Dank an alle, die zu diesem Release beigetragen haben!

- **Development & Testing**: @kamera-linux
- **Documentation**: @kamera-linux
- **QA & Bug Reports**: Community Members

---

## 📝 Changelog (Detailliert)

### Added
- ✨ Auto-Trigger System mit Trigger-Duration Logic
- ✨ Preview-Stream mit RTSP (640x480@5fps)
- ✨ Status-Reports Optimierung (Pause während Aufnahme)
- ✨ Stream-Restart Persistenz (bash -c mit disown)
- ✨ Netzwerk-Qualitäts-Test Tool
- ✨ YOLO-Modell Zentralisierung (config/models/)
- ✨ Firewall-Setup Skripte
- ✨ Guided Test System
- ✨ User-friendly Wrapper-Skript

### Fixed
- 🐛 Video-Recording Kamera-Blocking (Stream-Wrapper Auto-Restart)
- 🐛 Audio-Recording Mono-Format (S16_LE, 1 Kanal)
- 🐛 Stream-Neustart nicht persistent (bash -c + disown)
- 🐛 False Positive Triggers (Trigger-Duration Logic)
- 🐛 Cleanup-Traps für Remote-Prozesse

### Changed
- 🔧 Threshold Standard: 0.45 → 0.40 (CPU-optimiert)
- 🔧 Preview-FPS: 3 → 4 (CPU/Performance Balance)
- 🔧 Preview-Auflösung: 320x240 → 400x300 (bessere Erkennung)
- 🔧 Konsistenz-Rate: 70% → 65% (realistischer mit niedrigem FPS)
- 🔧 Stream-Management verbessert
- 🔧 Audio-Format: Stereo → Mono
- 🔧 SSH-Persistenz für Background-Prozesse

### Documentation
- 📝 AUTO-TRIGGER-DOKUMENTATION.md
- 📝 AUTO-TRIGGER-PERFORMANCE-OPTIMIZATION.md (Performance-Analyse)
- 📝 PARAMETER-NO-STREAM-RESTART.md (Stream-Management)
- 📝 AUTO-TRIGGER-STREAM-RESTART.md (Auto-Trigger Verhalten)
- 📝 QUICKSTART-AUTO-TRIGGER.md
- 📝 PREVIEW-STREAM-SETUP.md
- 📝 FIREWALL-SETUP-SUMMARY.md
- 📝 SYSTEM-READY.md

---

## 🔗 Links

- **GitHub Release**: https://github.com/kamera-linux/vogel-kamera-linux/releases/tag/v1.2.0
- **Branch**: `devel-v1.2.0`
- **Wiki**: https://github.com/kamera-linux/vogel-kamera-linux/wiki
- **Issues**: https://github.com/kamera-linux/vogel-kamera-linux/issues
- **Discussions**: https://github.com/kamera-linux/vogel-kamera-linux/discussions

---

**🎉 Viel Spaß mit dem Auto-Trigger System! Happy Bird Watching! 🐦**
