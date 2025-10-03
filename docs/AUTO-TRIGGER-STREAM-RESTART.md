# 🎬 Zeitlupe im Auto-Trigger Modus

## ✅ Antwort: JA, Preview-Stream wird immer neu gestartet!

### 🔄 Ablauf im Auto-Trigger (mit/ohne Zeitlupe):

```
1. 🐦 Vogel erkannt → Trigger ausgelöst
   
2. 📡 Preview-Stream STOPPEN
   ├─ Client trennen (stream_processor.disconnect())
   └─ Stream-Prozess auf Pi killen (pkill -9 rpicam-vid)
   
3. 🎬 Aufnahme starten
   ├─ Zeitlupe: ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py
   ├─ Mit AI: ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py (--ai-modul on)
   └─ Ohne AI: ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py (--ai-modul off)
   
4. ✅ Aufnahme abgeschlossen
   
5. 📡 Preview-Stream NEU STARTEN (IMMER!)
   ├─ Stream auf Pi starten (~/start-rtsp-stream.sh)
   ├─ 8 Sekunden warten (Stream-Initialisierung)
   └─ Client verbinden (stream_processor.connect())
   
6. ⏳ Cooldown-Phase (z.B. 60 Sekunden)
   
7. 🔄 Weiter überwachen
```

## 🎯 Auto-Trigger managed den Stream selbst!

### Wichtig: `--no-stream-restart` Parameter

Alle Aufnahme-Skripte werden vom Auto-Trigger mit `--no-stream-restart` aufgerufen:

```python
# Zeile 398 im Auto-Trigger Code:
cmd = [
    'python3',
    recording_script,
    '--duration', str(args.trigger_duration),
    # ... weitere Parameter ...
    '--no-stream-restart'  # ← Auto-Trigger managed Stream-Neustart selbst!
]
```

**Warum?**
- ❌ Das Aufnahme-Skript soll den Stream **NICHT** selbst neu starten
- ✅ Der Auto-Trigger startet den Stream **selbst** neu (Zeile 418-434)
- ✅ Der Auto-Trigger wartet auf vollständige Stream-Initialisierung (8 Sekunden)
- ✅ Der Auto-Trigger verbindet den Client wieder

## 🎥 Zeitlupe mit Auto-Trigger starten

### Parameter für Zeitlupe im Auto-Trigger:

```bash
python3 kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --cooldown 60 \
    --recording-slowmo  # ← WICHTIG: Aktiviert Zeitlupen-Modus
```

### Was passiert bei Zeitlupe?

```python
# Zeile 346-364 im Auto-Trigger Code:
if args.recording_slowmo:
    # ZEITLUPE: Nutze Zeitlupen-Skript (120fps, 1536x864)
    print(f"   🎬 Modus: Zeitlupen-Aufnahme (120fps, 1536x864)")
    
    recording_script = os.path.join(script_dir, 'python-skripte', 
                                   'ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py')
    
    cmd = [
        'python3',
        recording_script,
        '--duration', str(args.trigger_duration),
        '--width', '1536',      # Feste Auflösung für Performance
        '--height', '864',
        '--fps', '120',         # 120 fps für Zeitlupe
        '--rotation', str(args.rotation),
        '--cam', str(args.cam),
        '--slowmotion'          # Aktiviert Zeitlupen-Konvertierung
    ]
    # KEIN --no-stream-restart hier, da Zeitlupen-Skript Stream nie neu startet!
```

### ⚠️ Wichtig: Zeitlupen-Skript hat KEINEN Stream-Neustart!

Das Zeitlupen-Skript (`ai-had-kamera-remote-param-vogel-libcamera-zeitlupe.py`):
- ❌ Hat **keinen** `--no-stream-restart` Parameter
- ❌ Startet **nie** den Preview-Stream neu
- ✅ Ist daher **perfekt** für Auto-Trigger (kein Konflikt)

Das Standard-Skript (`ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py`):
- ✅ Hat `--no-stream-restart` Parameter
- ✅ **Muss** mit `--no-stream-restart` aufgerufen werden im Auto-Trigger
- ⚠️ Sonst würde es Stream neu starten → Konflikt mit Auto-Trigger!

## 📊 Vergleich: On-Demand vs Auto-Trigger

| Aspekt | On-Demand | Auto-Trigger |
|--------|-----------|--------------|
| **Preview-Stream** | Optional (--no-stream-restart) | **Immer neu gestartet** |
| **Stream-Management** | Skript selbst | Auto-Trigger übernimmt |
| **Wartezeit** | 2 Sek (wenn aktiviert) | 8 Sek (Stream-Init) |
| **Cooldown** | Keins | 60+ Sek zwischen Aufnahmen |
| **Zeitlupe-Modus** | ✅ Ja | ✅ Ja (--recording-slowmo) |

## 🎯 Empfehlung:

### On-Demand Aufnahmen:
```bash
# OHNE Stream-Neustart (spart Zeit)
python3 python-skripte/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 1 \
    --ai-modul on \
    --no-stream-restart  # ← Empfohlen für On-Demand
```

### Auto-Trigger:
```bash
# Stream-Neustart erfolgt AUTOMATISCH durch Auto-Trigger
python3 kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --recording-slowmo  # Optional: Zeitlupen-Modus
```

## ✅ Zusammenfassung:

1. **Auto-Trigger startet Stream IMMER neu** (unabhängig vom Modus)
2. **Zeitlupen-Skript hat keinen Stream-Neustart** (perfekt für Auto-Trigger)
3. **Standard-Skript braucht `--no-stream-restart`** im Auto-Trigger
4. **On-Demand sollte `--no-stream-restart` nutzen** (spart Ressourcen)

Der Preview-Stream wird also **garantiert** nach jeder Auto-Trigger Aufnahme neu gestartet - egal ob Zeitlupe, mit AI oder ohne AI! 🚀
