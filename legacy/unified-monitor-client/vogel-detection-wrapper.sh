#!/bin/bash
# Vogel Detection Autostart Wrapper
# Standort: /home/roimme/vogel-kamera-linux/unified-monitor-client/vogel-detection-wrapper.sh
# Synced via: version_manager.py sync_remote_scripts()

# Kill alle alten Detection-Prozesse (WICHTIG: alle Varianten!)
pkill -9 -f 'unified-camera-monitor-detect-only' 2>/dev/null || true
pkill -9 -f 'unified-camera-monitor' 2>/dev/null || true
sleep 2

# Setze LD_LIBRARY_PATH für Hailo
export LD_LIBRARY_PATH=/opt/hailo/lib:$LD_LIBRARY_PATH

# Wechsle zum Skript-Verzeichnis
cd /home/roimme/vogel-kamera-linux/raspberry-pi-scripts

# Lösche altes Log falls vorhanden (für sauberen Start)
rm -f /tmp/unified-camera-monitor.log

# Starte ONNX-Detection mit nohup im Hintergrund (WICHTIG: -ONNX.py variante!)
nohup /usr/bin/python3 unified-camera-monitor-detect-only-ONNX.py \
  --threshold 0.4 \
  --cooldown 15 \
  --trigger-duration 1.0 \
  > /tmp/unified-camera-monitor.log 2>&1 &

DPID=$!

# Gib dem Prozess Zeit, um zu starten
sleep 3

# Überprüfe ob ONNX-Skript läuft (nicht nur irgendein detect-Skript)
if pgrep -f 'detect-only-ONNX.py' > /dev/null; then
    exit 0
else
    exit 1
fi
