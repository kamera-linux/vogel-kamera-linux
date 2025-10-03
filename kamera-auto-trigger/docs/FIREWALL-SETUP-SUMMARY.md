# 🚀 Auto-Trigger System - Quick Reference

## ✅ Setup abgeschlossen!

Die Firewall-Regeln wurden erfolgreich konfiguriert und das System ist einsatzbereit.

## 📋 Konfigurierte Ports

### Raspberry Pi 5
- ✅ Port 22 (TCP) - SSH
- ✅ Port 8554 (TCP) - Preview-Stream ⭐
- ✅ Port 8554 (UDP) - RTSP Stream (optional)

### Client-PC
- ✅ Port 22 (TCP) - SSH
- ✅ Ausgehende Verbindungen erlaubt (Standard)

## 🎯 Schnellstart

### 1. Preview-Stream starten (Raspberry Pi)
```bash
ssh roimme@raspberrypi-5-ai-had
./start-preview-stream.sh

# Status prüfen:
./start-preview-stream.sh --status

# Stream stoppen:
./start-preview-stream.sh --stop
```

### 2. Stream-Test (Client-PC)
```bash
# Kurzer Test (10 Sekunden):
python python-skripte/stream_processor.py \
    --host raspberrypi-5-ai-had \
    --duration 10

# Mit Debug-Output:
python python-skripte/stream_processor.py \
    --host raspberrypi-5-ai-had \
    --duration 30 \
    --debug
```

### 3. Auto-Trigger starten (Client-PC)
```bash
# Standard-Modus:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --ai-model bird-species

# Mit Custom-Einstellungen:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 3 \
    --trigger-threshold 0.50 \
    --cooldown 60 \
    --status-interval 10
```

## 🔥 Firewall-Management

### Client-PC
```bash
# Status prüfen:
sudo ufw status verbose

# Firewall neu laden:
sudo ufw reload

# Regel hinzufügen:
sudo ufw allow from 192.168.178.59 comment "Raspberry Pi"

# Regel löschen:
sudo ufw status numbered
sudo ufw delete [NUMMER]
```

### Raspberry Pi
```bash
# Status prüfen:
ssh roimme@raspberrypi-5-ai-had
sudo ufw status verbose

# Firewall neu laden:
sudo ufw reload

# Port 8554 prüfen:
sudo ufw status | grep 8554
```

## 🐛 Troubleshooting

### Problem: "Connection refused"
```bash
# 1. Stream läuft auf Raspberry Pi?
ssh roimme@raspberrypi-5-ai-had
./start-preview-stream.sh --status

# 2. Firewall OK?
sudo ufw status | grep 8554

# 3. Stream neu starten:
./start-preview-stream.sh --stop
./start-preview-stream.sh
```

### Problem: "Connection timeout"
```bash
# 1. Netzwerk erreichbar?
ping raspberrypi-5-ai-had

# 2. Port erreichbar? (mit nmap)
nmap -p 8554 raspberrypi-5-ai-had

# 3. Firewall-Logs prüfen:
sudo tail -f /var/log/ufw.log
```

### Problem: Stream laggt
```bash
# Auflösung/FPS reduzieren:
./start-preview-stream.sh --stop
./start-preview-stream.sh --width 480 --height 360 --fps 3
```

### Problem: Zu viele false positives
```bash
# Threshold erhöhen:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-threshold 0.55 \
    --ai-model bird-species
```

## 📊 Performance-Metriken (getestet)

| Metrik | Wert |
|--------|------|
| Stream-Verbindung | ✅ Erfolgreich |
| Backend | GStreamer (1900) |
| Frame-Size | 640x480 |
| Frames/10s | 19 (~2 fps effektiv) |
| Inferenz-Zeit | ~438ms (CPU) |
| Model | YOLOv8n (bird-species) |

## 🎯 Optimale Einstellungen (empfohlen)

### Standard (ausgew

ogen)
```bash
# Raspberry Pi:
./start-preview-stream.sh

# Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --trigger-threshold 0.45 \
    --cooldown 30
```

### Hohe Genauigkeit
```bash
# Raspberry Pi:
./start-preview-stream.sh --width 800 --height 600 --fps 10

# Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --trigger-duration 3 \
    --trigger-threshold 0.55 \
    --cooldown 60
```

### Niedrige Bandbreite
```bash
# Raspberry Pi:
./start-preview-stream.sh --width 480 --height 360 --fps 3 --bitrate 500

# Client-PC:
python python-skripte/ai-had-kamera-auto-trigger.py \
    --preview-fps 3 \
    --trigger-threshold 0.40
```

## 🔄 Als Service einrichten

### Raspberry Pi (Preview-Stream)
```bash
# Service-File erstellen:
sudo nano /etc/systemd/system/preview-stream.service

# Inhalt siehe: PREVIEW-STREAM-SETUP.md

# Aktivieren:
sudo systemctl daemon-reload
sudo systemctl enable preview-stream
sudo systemctl start preview-stream

# Status:
sudo systemctl status preview-stream
```

### Client-PC (Auto-Trigger)
```bash
# Service-File erstellen:
sudo nano /etc/systemd/system/vogel-auto-trigger.service

# Inhalt siehe: PREVIEW-STREAM-SETUP.md

# Aktivieren:
sudo systemctl daemon-reload
sudo systemctl enable vogel-auto-trigger
sudo systemctl start vogel-auto-trigger

# Logs:
sudo journalctl -u vogel-auto-trigger -f
```

## 📚 Dokumentation

- **[QUICKSTART-AUTO-TRIGGER.md](QUICKSTART-AUTO-TRIGGER.md)** - 5-Minuten-Setup
- **[PREVIEW-STREAM-SETUP.md](PREVIEW-STREAM-SETUP.md)** - Detaillierte Anleitung
- **[AUTO-TRIGGER-DOKUMENTATION.md](AUTO-TRIGGER-DOKUMENTATION.md)** - Features
- **[AUTO-TRIGGER-OVERVIEW.md](AUTO-TRIGGER-OVERVIEW.md)** - Architektur

## ✨ Features

- ✅ Echte AI-Erkennung mit YOLOv8
- ✅ bird-species Model (nur Vögel)
- ✅ Automatische HD-Aufnahme bei Erkennung
- ✅ Ressourcen-Monitoring
- ✅ Status-Reports
- ✅ Cooldown-System
- ✅ Firewall-konfiguriert
- ✅ Produktionsreif!

Viel Erfolg! 🐦🎥
