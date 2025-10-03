# 📚 Parameter-Dokumentation: --no-stream-restart

## 📋 Übersicht

Der Parameter `--no-stream-restart` wurde in **v1.2.0** eingeführt und steuert, ob der Preview-Stream nach einer Aufnahme automatisch neu gestartet wird.

## 🎯 Verwendung

### Syntax
```bash
--no-stream-restart
```

- **Typ**: Flag (Boolean)
- **Default**: Stream wird neu gestartet
- **Mit Flag**: Stream wird NICHT neu gestartet

## 🔧 Wann verwenden?

### ✅ Verwenden bei On-Demand Aufnahmen

**Empfohlen für:**
- Manuelle Aufnahmen auf Abruf
- Testing/Debugging
- Einzelne Aufnahmen ohne Auto-Trigger
- Wenn Preview-Stream nicht benötigt wird

**Vorteile:**
- ⚡ 2 Sekunden schneller
- 💾 Reduzierte Ressourcen-Nutzung
- 🎯 Kamera wird sofort freigegeben

**Beispiel:**
```bash
python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 1 \
    --width 1920 \
    --height 1080 \
    --ai-modul on \
    --no-stream-restart  # ← Empfohlen für On-Demand
```

### ❌ NICHT verwenden bei Auto-Trigger

**Der Auto-Trigger managed den Stream selbst!**

- Auto-Trigger **ruft IMMER** mit `--no-stream-restart` auf
- Auto-Trigger **startet Stream selbst** nach Aufnahme neu
- Auto-Trigger **wartet auf Stream-Initialisierung** (8 Sekunden)
- Auto-Trigger **verbindet Client** wieder automatisch

**Beispiel:**
```bash
# Auto-Trigger übernimmt Stream-Management
python3 kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --cooldown 60
# → Kein --no-stream-restart nötig!
```

## 📊 Vergleich

| Modus | --no-stream-restart | Stream nach Aufnahme | Managed von |
|-------|---------------------|----------------------|-------------|
| **On-Demand** | ✅ Empfohlen | Gestoppt | User/Skript |
| **Auto-Trigger** | ⚙️ Auto-gesetzt | Automatisch neu gestartet | Auto-Trigger |
| **Zeitlupe** | ➖ Nicht vorhanden | Gestoppt | - |

## 🔍 Technische Details

### Was passiert MIT dem Parameter?

```python
if not args.no_stream_restart:
    # Stream-Neustart wird übersprungen
    print("\n⏭️  Preview-Stream Neustart übersprungen (--no-stream-restart)")
```

**Verhalten:**
- Aufnahme-Skript beendet sich nach Aufnahme
- Preview-Stream bleibt gestoppt
- Kamera ist frei für andere Prozesse
- Keine Wartezeit für Stream-Neustart

### Was passiert OHNE den Parameter?

```python
if not args.no_stream_restart:
    try:
        ssh = paramiko.SSHClient()
        # ... SSH-Verbindung ...
        
        # Prüfe ob Stream-Skript existiert
        stdin, stdout, stderr = ssh.exec_command("test -f ~/start-rtsp-stream.sh && echo 'EXISTS'")
        if 'EXISTS' in stdout.read().decode():
            print("\n🔄 Starte Preview-Stream neu...")
            ssh.exec_command("nohup ~/start-rtsp-stream.sh > /dev/null 2>&1 &")
            time.sleep(2)  # Warte auf Stream-Start
            print("✅ Preview-Stream wurde neu gestartet")
        
        ssh.close()
    except Exception as e:
        pass  # Fehler beim Stream-Neustart nicht kritisch
```

**Verhalten:**
- SSH-Verbindung zum Raspberry Pi
- Prüft ob `~/start-rtsp-stream.sh` existiert
- Startet Stream im Hintergrund (nohup)
- Wartet 2 Sekunden
- Beendet sich

## 🎬 Beispiele

### Beispiel 1: Schnelle Test-Aufnahme

```bash
# OHNE --no-stream-restart (Standard)
python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 1 --width 1920 --height 1080 --ai-modul off

# Ausgabe:
# ✅ Aufnahme erfolgreich abgeschlossen!
# 🔄 Starte Preview-Stream neu...
# ✅ Preview-Stream wurde neu gestartet
# 
# Zeit: 1:02 Minuten (1:00 Aufnahme + 0:02 Stream-Restart)
```

```bash
# MIT --no-stream-restart
python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 1 --width 1920 --height 1080 --ai-modul off \
    --no-stream-restart

# Ausgabe:
# ✅ Aufnahme erfolgreich abgeschlossen!
# ⏭️  Preview-Stream Neustart übersprungen (--no-stream-restart)
# 
# Zeit: 1:00 Minute (nur Aufnahme, 2 Sekunden gespart!)
```

### Beispiel 2: Multiple Aufnahmen

```bash
# 10 Aufnahmen ohne Stream-Restart (effizient)
for i in {1..10}; do
    echo "Aufnahme $i/10"
    python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
        --duration 1 --width 1920 --height 1080 \
        --no-stream-restart
    sleep 5
done

# Zeitersparnis: 10 * 2 Sek = 20 Sekunden
```

### Beispiel 3: Auto-Trigger (wird automatisch gesetzt)

```bash
# Auto-Trigger setzt --no-stream-restart automatisch
python3 kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --cooldown 60

# Intern wird aufgerufen:
# python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
#     --duration 2 \
#     --width 4096 \
#     --height 2160 \
#     --no-stream-restart  ← Auto-Trigger setzt dies!

# Danach startet Auto-Trigger den Stream selbst neu
```

## 🐛 Troubleshooting

### Problem: Stream läuft noch nach Aufnahme

**Symptom:**
```
Kamera ist besetzt, kann keine neue Aufnahme starten
```

**Ursache:**
- `--no-stream-restart` wurde verwendet
- Stream wurde vorher gestartet und läuft noch
- Kamera kann nicht exklusiv genutzt werden

**Lösung:**
```bash
# Stream manuell stoppen auf dem Raspberry Pi
ssh roimme@raspberrypi-5-ai-had
pkill -9 rpicam-vid
```

### Problem: Stream startet nicht nach Aufnahme

**Symptom:**
```
Preview-Stream ist nicht verfügbar nach On-Demand Aufnahme
```

**Ursache:**
- `--no-stream-restart` wurde verwendet
- Stream wurde nicht neu gestartet

**Lösung 1:** Stream manuell starten
```bash
ssh roimme@raspberrypi-5-ai-had
~/start-rtsp-stream.sh
```

**Lösung 2:** Parameter weglassen
```bash
# Stream wird automatisch neu gestartet
python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 1 --width 1920 --height 1080
# (ohne --no-stream-restart)
```

## 🔗 Verwandte Dokumentation

- [`docs/FIX-PREVIEW-STREAM-RESTART.md`](FIX-PREVIEW-STREAM-RESTART.md) - Detaillierte Implementierungs-Dokumentation
- [`docs/AUTO-TRIGGER-STREAM-RESTART.md`](AUTO-TRIGGER-STREAM-RESTART.md) - Stream-Management im Auto-Trigger
- [`README.md`](../README.md) - Hauptdokumentation mit allen Beispielen
- [`releases/RELEASE_NOTES_v1.2.0.md`](../releases/RELEASE_NOTES_v1.2.0.md) - Release-Notes v1.2.0

## 📝 Changelog

### v1.2.0 (2025-10-03)
- ✅ Parameter `--no-stream-restart` hinzugefügt
- ✅ Implementierung in `ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py`
- ✅ Auto-Trigger verwendet Parameter automatisch
- ✅ Dokumentation erstellt

## 💡 Best Practices

### ✅ DO

- Verwende `--no-stream-restart` bei On-Demand Aufnahmen
- Lasse Auto-Trigger das Stream-Management übernehmen
- Teste ohne Parameter bei Problemen mit Preview-Stream
- Nutze Parameter bei Multiple Aufnahmen (spart Zeit)

### ❌ DON'T

- Verwende Parameter NICHT manuell bei Auto-Trigger (wird automatisch gesetzt)
- Vergiss nicht Stream manuell zu starten wenn benötigt
- Kombiniere nicht mit Zeitlupen-Skript (hat keinen Stream-Restart)
