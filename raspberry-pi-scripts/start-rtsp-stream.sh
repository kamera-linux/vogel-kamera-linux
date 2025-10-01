#!/bin/bash
# =============================================================================
# RTSP Stream via GStreamer (Robuste Lösung)
# =============================================================================
# Verwendet libcamera mit GStreamer RTSP-Server für persistente Streams
#
# Installation auf Raspberry Pi:
#   sudo apt install gstreamer1.0-rtsp python3-gi gir1.2-gst-rtsp-server-1.0
#
# Verwendung:
#   ./start-rtsp-stream.sh [--stop|--status]
# =============================================================================

set -e

PORT=8554
WIDTH=640
HEIGHT=480
FPS=5
ROTATION=180
BITRATE=1000
CAMERA=0
PIDFILE="/tmp/rtsp-stream.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

check_status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_success "RTSP-Stream läuft (PID: $PID)"
            echo ""
            print_info "Stream-URL: rtsp://$(hostname -I | awk '{print $1}'):$PORT/stream"
            return 0
        else
            print_warning "PID-File existiert, aber Prozess läuft nicht"
            rm -f "$PIDFILE"
            return 1
        fi
    else
        print_warning "RTSP-Stream läuft nicht"
        return 1
    fi
}

stop_stream() {
    print_info "Stoppe RTSP-Stream..."
    pkill -f "gst-launch.*rtsp" || true
    pkill -f "rpicam-vid" || true
    rm -f "$PIDFILE"
    print_success "RTSP-Stream gestoppt"
}

start_stream() {
    if [ -f "$PIDFILE" ] && ps -p "$(cat "$PIDFILE")" > /dev/null 2>&1; then
        print_error "Stream läuft bereits"
        exit 1
    fi
    
    print_info "Starte RTSP-Stream mit GStreamer..."
    echo ""
    echo "  📹 Kamera: $CAMERA"
    echo "  📐 Auflösung: ${WIDTH}x${HEIGHT} @ ${FPS}fps"
    echo "  🔌 Port: $PORT"
    echo ""
    
    # Verwende einfaches TCP mit libcamera, aber mit Short-Circuit-Schutz
    # Schreibe Wrapper-Skript
    cat > /tmp/stream-wrapper.sh << 'WRAPPER_EOF'
#!/bin/bash
while true; do
    rpicam-vid \
        --camera CAMERA_ID \
        --width STREAM_WIDTH \
        --height STREAM_HEIGHT \
        --framerate STREAM_FPS \
        --rotation STREAM_ROTATION \
        --bitrate STREAM_BITRATE \
        --inline \
        --codec h264 \
        --profile baseline \
        --level 4.2 \
        --flush \
        --listen \
        -t 0 \
        -o "tcp://0.0.0.0:STREAM_PORT?listen=1" \
        --nopreview \
        2>&1 | tee -a /tmp/rtsp-stream.log
    
    echo "[$(date)] Stream beendet, starte in 2 Sekunden neu..." >> /tmp/rtsp-stream.log
    sleep 2
done
WRAPPER_EOF
    
    # Ersetze Platzhalter
    sed -i "s/CAMERA_ID/$CAMERA/g" /tmp/stream-wrapper.sh
    sed -i "s/STREAM_WIDTH/$WIDTH/g" /tmp/stream-wrapper.sh
    sed -i "s/STREAM_HEIGHT/$HEIGHT/g" /tmp/stream-wrapper.sh
    sed -i "s/STREAM_FPS/$FPS/g" /tmp/stream-wrapper.sh
    sed -i "s/STREAM_ROTATION/$ROTATION/g" /tmp/stream-wrapper.sh
    sed -i "s/STREAM_BITRATE/$((BITRATE * 1000))/g" /tmp/stream-wrapper.sh
    sed -i "s/STREAM_PORT/$PORT/g" /tmp/stream-wrapper.sh
    
    chmod +x /tmp/stream-wrapper.sh
    
    # Starte Wrapper im Hintergrund
    nohup /tmp/stream-wrapper.sh > /dev/null 2>&1 &
    
    PID=$!
    echo "$PID" > "$PIDFILE"
    sleep 3
    
    if ps -p "$PID" > /dev/null 2>&1; then
        print_success "RTSP-Stream gestartet (PID: $PID)"
        echo ""
        IP=$(hostname -I | awk '{print $1}')
        print_info "Stream-URL: tcp://$IP:$PORT"
        print_info "Auto-Restart aktiviert"
        echo ""
        print_info "Verwende auf dem Client-PC:"
        echo "  ./run-auto-trigger.sh --trigger-duration 2"
    else
        print_error "Konnte Stream nicht starten"
        rm -f "$PIDFILE"
        exit 1
    fi
}

case "${1:-start}" in
    --stop|stop)
        stop_stream
        ;;
    --status|status)
        check_status
        ;;
    --start|start|*)
        start_stream
        ;;
esac
