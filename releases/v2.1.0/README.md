# 📦 v2.1.0 - Audio/Video-Synchronisation Release

**Veröffentlichung:** 8. März 2026  

## 🎙️ Was ist neu?

Diese Release konzentriert sich auf **perfekte Audio/Video-Synchronisation** - das Kernproblem des Vogel-Hause-Systems:

### 🎬 Haupt-Feature
**Thread-basierte parallel Audio/Video-Aufnahme** mit exakter Synchronisation:
- Video + Audio starten **gleichzeitig** (nicht sequenziell)
- Beide laufen für **exakt gleiche Dauer**
- ffmpeg Merge mit korrekten Timestamps
- Resultat: MP4 mit perfekt synchem Audio+Video ✅

### 🎙️ Audio-Integration
- USB-Audio-Stick automatisch erkannt (hw:0,0, hw:1,0, etc.)
- arecord: 44.1kHz Mono, S16_LE
- Fallback-Mechanismus für verschiedene Audio-Devices

### 📷 Professionelle Parameter
Alle rpicam-vid-Parameter jetzt verfügbar:
- Rotation 180° (Default - Vogelbild oben)
- Cinema 4K (4096x2160 @ 30fps)
- Codec, HDR, Autofokus konfigurierbar
- Manual Recording Mode

## 📁 Dateien in diesem Release

```
v2.1.0/
├── RELEASE_NOTES_v2.1.0.md        # Detaillierte Release-Notes
├── README.md                        # Dieser Datei
└── (Archiv-Binaries wenn vorhanden)
```

## 🚀 Quickstart

```bash
# Test mit 5 Sekunden Aufnahme
cd raspberry-pi-scripts/
python3 unified-camera-monitor.py --manual-record --recording-duration 5

# Normale 60-Sekunden Aufnahme
python3 unified-camera-monitor.py --manual-record --recording-duration 60 --rotation 180
```

## ✅ Getestet
- ✅ Raspberry Pi 5 + Debian Trixie
- ✅ USB Audio-Stick (C-Media Electronics)
- ✅ 4K @ 30fps + 44.1kHz Audio
- ✅ Perfect Sync (beide Streams exakt gleiche Duration)

## 📖 Dokumentation
Siehe [RELEASE_NOTES_v2.1.0.md](RELEASE_NOTES_v2.1.0.md) für vollständige Details.

---

**Stable Release** ✅ - Produktionsreif
