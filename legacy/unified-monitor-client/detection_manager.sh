#!/bin/bash
# Detection Process Manager für Raspberry Pi
# Verwaltet Vogel-Erkennungs-Prozesse sauber

DETECTION_PIDFILE="/tmp/detection_process.pid"
DETECTION_LOG="/tmp/detection_manager.log"

case "$1" in
    start)
        # Checke ob schon läuft
        if [ -f "$DETECTION_PIDFILE" ]; then
            OLD_PID=$(cat "$DETECTION_PIDFILE")
            if kill -0 "$OLD_PID" 2>/dev/null; then
                echo "[$(date '+%H:%M:%S')] Detection läuft bereits (PID: $OLD_PID)" >> "$DETECTION_LOG"
                exit 0
            fi
        fi
        
        # Starte Detection
        cd ~/vogel-kamera-linux/raspberry-pi-scripts
        nohup python3 unified-camera-monitor-detect-only.py --use-hailo >> "$DETECTION_LOG" 2>&1 &
        NEW_PID=$!
        echo "$NEW_PID" > "$DETECTION_PIDFILE"
        echo "[$(date '+%H:%M:%S')] Detection gestartet (PID: $NEW_PID)" >> "$DETECTION_LOG"
        exit 0
        ;;
    stop)
        # Stoppe alle Detection-Prozesse
        pkill -f "unified-camera-monitor-detect-only"
        pkill -f "hailo_onnx"
        pkill -f "python3.*detect"
        rm -f "$DETECTION_PIDFILE"
        echo "[$(date '+%H:%M:%S')] Detection gestoppt" >> "$DETECTION_LOG"
        exit 0
        ;;
    status)
        if [ -f "$DETECTION_PIDFILE" ]; then
            PID=$(cat "$DETECTION_PIDFILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "RUNNING:$PID"
                exit 0
            fi
        fi
        echo "STOPPED"
        exit 1
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
