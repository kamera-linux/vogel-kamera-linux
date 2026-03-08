# Versionierung System

Das Unified Monitoring System verwendet ein Versionierungssystem, um die Konsistenz zwischen lokalen und Remote-Skripten zu gewährleisten.

## Versionsnummern Format

Das System verwendet **semantische Versionierung** (MAJOR.MINOR.PATCH):
- **MAJOR**: Große Änderungen (z.B. Audio-Support hinzugefügt)
- **MINOR**: Neue Features (z.B. neue Recording-Modi)
- **PATCH**: Bug-Fixes (z.B. Bash-Fehler korrigiert)

## Version Files

Jedes Verzeichnis hat eine `VERSION`-Datei:

```
auto-start-kamera/           -> VERSION (2.1.0)
├── start-unified-monitoring.sh
├── remote-unified-control.sh
└── VERSION

raspberry-pi-scripts/        -> VERSION (2.1.0)
├── unified-camera-monitor.py
└── VERSION

./                           -> VERSION (2.1.0)
```

## Version-Check beim Start

Beim Ausführen von `./start-unified-monitoring.sh` passiert:

1. **Lokale Version laden** aus `./auto-start-kamera/VERSION`
2. **Remote-Version prüfen** via SSH
3. **Versionen vergleichen**:
   - ✅ Wenn Remote-Version = Lokale Version → Kein Update nötig
   - 🔄 Wenn Remote-Version < Lokale Version → Automatisches Update aller Skripte
   - ❌ Wenn Remote nicht erreichbar → Warnung anzeigen

## Version aktualisieren

Um die Version zu aktualisieren:

1. **VERSION-Datei bearbeiten**:
   ```bash
   echo "2.2.0" > auto-start-kamera/VERSION
   echo "2.2.0" > raspberry-pi-scripts/VERSION
   echo "2.2.0" > VERSION
   ```

2. **Beim nächsten Start** werden die Remote-Skripte automatisch aktualisiert

## Beispiel-Output beim Version-Mismatch

```
🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung
======================================================================
   Version: v2.1.0
======================================================================

🔍 Prüfe Remote-Skript-Versionen...
   📌 Lokale Version:  v2.1.0
   📍 Remote Version:  v2.0.2
   🔄 Update erforderlich: v2.0.2 → v2.1.0

🔄 Prüfe Remote-Skripte auf Aktualität...
   🔄 Aktualisiere: unified-camera-monitor.py
      ✅ Erfolgreich übertragen
   🔄 Aktualisiere: start-unified-monitoring.sh
      ✅ Erfolgreich übertragen
   ...
✅ 3 Datei(en) aktualisiert
```

## Versionsverlauf

- **v2.1.0** - Automatische Versionsprüfung mit Hash-basierter Sync
- **v2.0.2** - Bash-Fehlerfix (grep -c statt wc -l)
- **v2.0.1** - Video-Watcher Optimierung (-mtime -7)
- **v2.0.0** - Vollständige Audio-Support Integration
