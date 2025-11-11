# 🌐 Network Tools

Dieses Verzeichnis enthält Netzwerk-Diagnose- und Test-Tools für das Vogel-Kamera-Linux Projekt.

## 📋 Übersicht

| Tool | Beschreibung | Verwendung |
|------|--------------|------------|
| `test-network-quality.py` | Netzwerk-Qualitäts-Test | Misst Verbindungsqualität zwischen lokalem PC und Raspberry Pi |

## 🔍 test-network-quality.py - Netzwerk-Qualitäts-Test

### Beschreibung
Misst die Netzwerkverbindungsqualität zwischen dem lokalen PC und dem Raspberry Pi. Das Tool führt verschiedene Tests durch, um potenzielle Netzwerkprobleme zu identifizieren.

### Features
- 🏓 **Ping-Test**: Misst Latenz und Paketverlust
- 🔌 **SSH-Verbindungstest**: Prüft SSH-Verbindungsaufbau-Zeiten
- 📊 **Bandbreiten-Test**: Misst Upload/Download-Geschwindigkeit via SCP
- ⚡ **Befehlsausführungs-Test**: Misst Latenz bei Remote-Befehlen

### Verwendung

#### Voraussetzungen
```bash
# Stelle sicher, dass SSH-Key-basierte Authentifizierung konfiguriert ist
ssh-copy-id pi@raspberrypi.local
```

#### Test ausführen
```bash
python3 network-tools/test-network-quality.py
```

#### Konfiguration
Bearbeite die Variablen am Anfang des Skripts:
```python
REMOTE_HOST = "raspberrypi.local"  # oder IP-Adresse
REMOTE_USER = "pi"
REMOTE_PASSWORD = None  # oder dein Passwort
```

### Test-Kategorien

#### 1. 🏓 Ping-Test
- Sendet 10 Ping-Pakete
- Misst: Min/Max/Durchschnitt Latenz
- Erkennt: Paketverlust

#### 2. 🔌 SSH-Verbindungstest
- 5 SSH-Verbindungsversuche
- Misst: Verbindungsaufbau-Zeit
- Empfohlen: < 2 Sekunden
- ⚠️ Warnung bei: > 5 Sekunden

#### 3. 📊 Bandbreiten-Test
- Upload-Test: 1 MB Testdatei
- Download-Test: Remote-Datei herunterladen
- Misst: Upload/Download-Geschwindigkeit in MB/s
- Empfohlen: > 10 MB/s (Gigabit-Ethernet)

#### 4. ⚡ Befehlsausführungs-Test
- Führt 10 einfache Remote-Befehle aus
- Misst: Durchschnittliche Latenz
- Empfohlen: < 0.5 Sekunden

### Beispiel-Ausgabe

```
🌐 NETZWERK-QUALITÄTS-TEST
====================================
Remote-Host: raspberrypi.local
Remote-User: pi
====================================

🏓 PING-TEST
--------------------------------------------------
Ping Statistiken:
  Pakete gesendet: 10
  Empfangen: 10
  Verloren: 0 (0.0%)
  Min: 1.23 ms
  Max: 3.45 ms
  Durchschnitt: 2.34 ms
✅ Ping-Test erfolgreich

🔌 SSH-VERBINDUNGSTEST
--------------------------------------------------
SSH-Verbindungszeiten:
  Versuch 1: 1.234s
  Versuch 2: 1.189s
  Versuch 3: 1.245s
  Versuch 4: 1.198s
  Versuch 5: 1.212s
Durchschnitt: 1.216s
✅ SSH-Verbindung gut (< 2s)

📊 BANDBREITEN-TEST
--------------------------------------------------
Upload (1.00 MB):
  Zeit: 0.089s
  Geschwindigkeit: 11.24 MB/s
✅ Upload-Geschwindigkeit gut

Download (1.00 MB):
  Zeit: 0.078s
  Geschwindigkeit: 12.82 MB/s
✅ Download-Geschwindigkeit gut

⚡ BEFEHLSAUSFÜHRUNGS-TEST
--------------------------------------------------
Remote-Befehl Latenz (10 Versuche):
  Durchschnitt: 0.234s
✅ Befehlsausführung schnell

====================================
📊 ZUSAMMENFASSUNG
====================================
✅ Alle Tests bestanden
Die Netzwerkverbindung ist stabil und schnell.
```

### Interpretation der Ergebnisse

#### ✅ Gute Verbindung (Ethernet)
- Ping: < 5 ms
- SSH-Verbindung: < 2s
- Bandbreite: > 10 MB/s
- Befehlslatenz: < 0.5s

#### ⚠️ Mittlere Verbindung (WLAN)
- Ping: 5-20 ms
- SSH-Verbindung: 2-5s
- Bandbreite: 1-10 MB/s
- Befehlslatenz: 0.5-1s

#### ❌ Schlechte Verbindung
- Ping: > 20 ms oder Paketverlust
- SSH-Verbindung: > 5s
- Bandbreite: < 1 MB/s
- Befehlslatenz: > 1s

### Problemlösung

#### Langsame Verbindung
1. **Prüfe Verbindungsart**: WLAN vs. Ethernet
   ```bash
   # Auf dem Raspberry Pi
   ip addr show
   ```
2. **Wechsle zu Ethernet**: Verwende Ethernet-Kabel für beste Performance
3. **Prüfe WLAN-Signal**: Bei WLAN Router-Nähe überprüfen

#### SSH-Verbindungsprobleme
1. **Prüfe SSH-Konfiguration**:
   ```bash
   ssh -v pi@raspberrypi.local
   ```
2. **Überprüfe Known Hosts**:
   ```bash
   ssh-keygen -R raspberrypi.local
   ```

#### Hohe Latenz
1. **Prüfe Netzwerk-Auslastung**: Andere Geräte/Downloads
2. **Router-Qualität**: Ältere Router können Engpässe verursachen
3. **Interferenzen**: Bei WLAN andere Netzwerke prüfen

### Verwendung im Projekt

Dieses Tool wurde entwickelt, um Netzwerkprobleme bei der Verwendung von:
- **RTSP Preview-Stream** (`preview_stream_manager.py`)
- **Remote-Kamera-Steuerung** (`ai-had-kamera-remote-param-vogel-libcamera-*.py`)
- **SSH-basierte Befehle** zu diagnostizieren

**Empfehlung**: Führe diesen Test aus, bevor du mit der Kamera-Fernsteuerung arbeitest, um sicherzustellen, dass die Netzwerkverbindung stabil genug ist.

### Troubleshooting

#### ImportError: No module named 'paramiko'
```bash
pip install paramiko
```

#### Permission denied (publickey)
```bash
# SSH-Key erstellen und kopieren
ssh-keygen -t ed25519
ssh-copy-id pi@raspberrypi.local
```

#### Timeout-Fehler
- Überprüfe, ob der Raspberry Pi erreichbar ist: `ping raspberrypi.local`
- Stelle sicher, dass SSH auf dem Raspberry Pi aktiviert ist
- Prüfe Firewall-Einstellungen

## 📚 Weitere Informationen

- **Projekt-Wiki**: Siehe Wiki für detaillierte Netzwerk-Setup-Anleitungen
- **Release Notes**: `releases/RELEASE_NOTES_v1.2.0.md` - Network-Diagnostics Feature
- **Konfiguration**: `config/` - Netzwerk-bezogene Konfigurationsdateien

## 🔗 Verwandte Tools

- **Stream-Management**: `scripts/preview_stream_manager.py`
- **Remote-Skripte**: `python-skripte/ai-had-kamera-remote-param-*.py`
- **Raspberry Pi Scripts**: `raspberry-pi-scripts/`

## 📝 Hinweise

- Das Tool benötigt SSH-Zugriff auf den Raspberry Pi
- Für Bandbreiten-Tests werden temporäre Dateien erstellt und wieder gelöscht
- Bei Verwendung von Passwort-Authentifizierung muss `sshpass` installiert sein
- SSH-Key-Authentifizierung wird empfohlen für automatisierte Tests

---

*Teil des Vogel-Kamera-Linux Projekts v1.2.0*
