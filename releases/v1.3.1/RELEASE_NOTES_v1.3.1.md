# 🎉 Release Notes - v1.3.1

**Release-Name:** Trixie Production Release - TCP Stream Watchdog  
**Release-Datum:** 05. November 2025  
**Release-Typ:** Patch

---

## 📋 Zusammenfassung

Version 1.3.1 bringt wichtige Stabilitätsverbesserungen, optimierte Parameter für WLAN-Betrieb und ein verbessertes Benutzererlebnis mit Live-Progressbars während Aufnahmen. Der TCP Stream Watchdog wurde gehärtet und die Trigger-Parameter für optimale Vogelerkennung auf Raspberry Pi OS Trixie feinabgestimmt.

---

## ✨ Neue Features

### 🎬 Live-Progressbar während Aufnahmen
- **Custom Single-Line Progressbar** für alle Aufnahmemodi
- **Echtzeit-Updates** zeigen Fortschritt während 60-sekündiger Aufnahmen
- **Visuelle Darstellung**: `[████████████░░░░░░] 67% (40/60s, noch 20s)`
- Funktioniert für Zeitlupe, 4K-Video und Audio-Aufnahmen

### 🔧 Optimierte Trigger-Parameter
- **Trigger-Duration:** 1.5s (erhöht von 0.8s für bessere Frame-Statistik)
- **Konsistenz-Rate:** 60% (optimiert für WLAN-Betrieb)
- **Threshold:** 0.4 (ausgewogen zwischen Sensitivität und False Positives)
- **FPS:** 8 (Preview-Stream für optimale Performance)
- **Detaillierte Trigger-Info:** Zeigt Frames und Konsistenz-Rate an

### 🐛 Robustes Cleanup-System
- **SIGTERM → SIGKILL Cascade:** Graceful Shutdown mit 10s Timeout
- **PID-Tracking:** Saubere Prozessverwaltung für Auto-Trigger
- **Remote-Cleanup:** Stoppt Watchdog und rpicam-vid auf dem Pi
- **Keine "Getötet"-Meldungen:** Saubere Terminal-Ausgabe bei CTRL+C

---

## 🔧 Verbesserungen

### 📡 TCP Stream Watchdog Hardening
- **Robuste Error-Handling:** `set +e` und `|| true` für Fehlertoleranz
- **Auto-Restart mit Delay:** 5 Sekunden Cooldown zwischen Restarts
- **Process Cleanup:** Automatisches Beenden von Zombie-Prozessen
- **Längere Initialisierungszeit:** 20s für neuen Start, 5s für laufenden Stream

### 🖥️ Verbesserte Ausgabe
- **Python Unbuffered Mode:** `-u` Flag für Echtzeit-Debug-Output
- **SSH Output Streaming:** `stdout.readline()` → `stdout.read()` für saubere Progressbar
- **Detaillierte Trigger-Logs:** `(1.9s, 100% Rate, 5/5 Frames)`
- **Klare Status-Meldungen:** Farbige Emojis und strukturierte Reports

### ⚡ Performance-Optimierungen
- **Differenziertes Stream-Timing:** 5s vs 20s Wait-Time je nach Watchdog-Status
- **Optimierte Frame-Rate:** Real ~4 FPS bei 245ms Inferenz-Zeit
- **WLAN-Anpassungen:** Parameter für stabile 56/70 Link-Quality

---

## 🐛 Behobene Fehler

### 🔄 Stream-Verbindung
- **Problem:** Python-Output gebuffert, Debug-Meldungen nicht sichtbar
  - **Lösung:** Python mit `-u` Flag für unbuffered stdout
  
- **Problem:** TCP Watchdog crasht bei Connection Reset
  - **Lösung:** Fehlertolerante Loop mit automatischem Neustart

- **Problem:** "Connection refused" nach Aufnahmen
  - **Lösung:** Watchdog-Lifecycle-Management mit proper Timing

### 📊 Progressbar
- **Problem:** tqdm-Progressbar erscheint erst am Ende (gebuffert)
  - **Lösung:** Custom Progressbar mit `\r`, `flush=True` und `stdout.read()`
  
- **Problem:** Remote-Output überschreibt lokale Progressbar
  - **Lösung:** Video-Aufnahme mit `show_output=False` Parameter

### 🧹 Cleanup
- **Problem:** CTRL+C beendet Python nicht sauber
  - **Lösung:** SIGTERM mit 10s Timeout, dann SIGKILL
  
- **Problem:** Watchdog bleibt nach Beenden aktiv
  - **Lösung:** SSH-Cleanup als Fallback mit pkill

---

## 📊 Technische Details

### Trigger-Algorithmus
```python
# Neue Berechnung:
# Real FPS: ~4 FPS (245ms Inferenz-Zeit)
# 1.5s × 4 FPS = ~6 Frames Analysezeitraum
# 60% Konsistenz: Benötigt ~4 positive Frames von 6
# Effekt: Mehr Frames für bessere Statistik, weniger False Positives
```

### Progressbar-Implementation
```python
# Custom Single-Line Progressbar:
bar = '█' * filled + '░' * (bar_length - filled)
print(f"\r   [{bar}] {percent}% ({elapsed}/{recording_duration_s}s, noch {remaining}s)  ", 
      end='', flush=True)
```

### Cleanup-Flow
```bash
# 1. SIGTERM an Python-Prozess
kill -TERM $AUTO_TRIGGER_PID

# 2. Warte max 10 Sekunden
for i in {1..20}; do
    if ! kill -0 $AUTO_TRIGGER_PID 2>/dev/null; then break; fi
    sleep 0.5
done

# 3. SIGKILL bei Timeout
if kill -0 $AUTO_TRIGGER_PID 2>/dev/null; then
    kill -9 $AUTO_TRIGGER_PID 2>/dev/null
fi

# 4. SSH-Cleanup als Fallback
```

---

## 🔄 Kompatibilität

### Getestet auf
- ✅ **Raspberry Pi OS Trixie (Debian 13)** - Primary Target
- ✅ **Python 3.13+**
- ✅ **rpicam-vid** (Trixie-native)
- ✅ **TCP Stream** mit Watchdog

### Netzwerk
- ✅ **WLAN:** 56/70 Quality (80%), -54 dBm Signal
- ✅ **Ethernet:** Empfohlen für beste Performance
- ⚠️ **WLAN-Hinweis:** Gelegentliche Stream-Drops bei 227 Packet Retries

### Hardware
- ✅ **Dual IMX708 Wide Kamera**
- ✅ **Raspberry Pi 5** (8GB RAM empfohlen)
- ✅ **USB Audio Interface** für Audioaufnahmen

---

## 📝 Bekannte Einschränkungen

1. **Frame-Rate:** Real ~4 FPS statt 8 FPS (AI-Inferenz-Zeit: 245ms)
2. **WLAN-Stabilität:** Gelegentliche "Connection refused" bei schlechter Verbindung
3. **Progressbar:** Funktioniert nur mit direktem stdout (nicht über SSH-Redirect)
4. **Trigger-Konsistenz:** Nur 3-6 Frames bei 1.5s Duration (wegen echter 4 FPS)

---

## 🚀 Migration von v1.3.0

### Automatische Änderungen
- ✅ **Keine Breaking Changes** - v1.3.0 Konfigurationen bleiben kompatibel
- ✅ **Parameter automatisch angepasst** - Neue Trigger-Duration und Konsistenz aktiv
- ✅ **Cleanup verbessert** - Sauberes Beenden ohne manuelle Anpassung

### Empfohlene Schritte
```bash
# 1. Update auf v1.3.1
cd ~/vogel-kamera-linux
git pull origin main
git checkout v1.3.1

# 2. Python-Abhängigkeiten aktualisieren (falls nötig)
pip install -r requirements.txt

# 3. Testen mit einem Trigger
cd kamera-auto-trigger
./start-vogel-beobachtung.sh --slowmo
```

---

## 📚 Dokumentation

Aktualisierte Dokumentation:
- ✅ **AUTO-TRIGGER-PERFORMANCE-OPTIMIZATION.md** - Neue Parameter-Erklärungen
- ✅ **AUTO-TRIGGER-STREAM-RESTART.md** - Watchdog-Lifecycle-Management
- ✅ **CHANGELOG.md** - Vollständige Änderungshistorie
- ✅ **README.md** - Quick Start für Trixie

---

## 🙏 Danksagungen

Besonderer Dank an alle Tester und Contributors, die Feedback zu den Trixie-Anpassungen gegeben haben. Diese Version wäre ohne die ausführlichen Tests im WLAN-Betrieb nicht möglich gewesen.

---

## 📞 Support

Bei Fragen oder Problemen:
- **GitHub Issues:** [github.com/kamera-linux/vogel-kamera-linux/issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)
- **Dokumentation:** `docs/` Verzeichnis
- **Quick Start:** `README.md`

---

**Viel Erfolg bei der Vogelbeobachtung mit v1.3.1! 🐦📹**
