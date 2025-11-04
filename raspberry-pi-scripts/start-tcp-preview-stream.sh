#!/bin/bash
# =============================================================================
# TCP Preview-Stream für Auto-Trigger System (Bookworm-Kompatibilität)
# =============================================================================
# Startet einen TCP-basierten Preview-Stream für synchrones Frame-Reading.
# Dies verhindert Buffer-Lag bei langsamer YOLO-Inferenz.
#
# Verwendung:
#   ./start-tcp-preview-stream.sh [OPTIONS]
#
# Optionen:
#   --port PORT          TCP-Port (default: 8554)
#   --width WIDTH        Stream-Breite (default: 640)
#   --height HEIGHT      Stream-Höhe (default: 480)
#   --fps FPS            Framerate (default: 5)
#   --rotation DEG       Rotation in Grad (default: 180)
#   --camera CAM         Kamera-ID (default: 0)
#   --stop               Beendet laufenden Stream
#   --status             Zeigt Status
# =============================================================================

set -e

# Defaults
PORT=8554
WIDTH=640
HEIGHT=480
FPS=5
ROTATION=180
CAMERA=0
PIDFILE="/tmp/tcp-preview-stream.pid"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Argument-Parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --width) WIDTH="$2"; shift 2 ;;
        --height) HEIGHT="$2"; shift 2 ;;
        --fps) FPS="$2"; shift 2 ;;
        --rotation) ROTATION="$2"; shift 2 ;;
        --camera) CAMERA="$2"; shift 2 ;;
        --stop)
            if [ -f "$PIDFILE" ]; then
                PID=$(cat "$PIDFILE")
                print_info "Stoppe TCP Preview-Stream (PID: $PID)..."
                kill $PID 2>/dev/null && print_success "Stream gestoppt" || print_warning "Prozess nicht gefunden"
                rm -f "$PIDFILE"
            else
                print_warning "Kein laufender Stream gefunden"
            fi
            exit 0
            ;;
        --status)
            if [ -f "$PIDFILE" ]; then
                PID=$(cat "$PIDFILE")
                if ps -p $PID > /dev/null 2>&1; then
                    print_success "TCP Preview-Stream läuft (PID: $PID)"
                    echo ""
                    print_info "Port: $PORT"
                    print_info "Verbindung: tcp://$(hostname):$PORT"
                else
                    print_warning "PID-File existiert, aber Prozess läuft nicht"
                    rm -f "$PIDFILE"
                fi
            else
                print_info "Kein TCP Preview-Stream aktiv"
            fi
            exit 0
            ;;
        *) print_error "Unbekannte Option: $1"; exit 1 ;;
    esac
done

# Prüfe ob bereits läuft
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p $PID > /dev/null 2>&1; then
        print_error "TCP Preview-Stream läuft bereits (PID: $PID)"
        print_info "Stoppe mit: $0 --stop"
        exit 1
    else
        print_warning "Stale PID-File gefunden, entferne..."
        rm -f "$PIDFILE"
    fi
fi

# Banner
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║   📹 TCP PREVIEW-STREAM (Bookworm-Modus)                        ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

print_info "Konfiguration:"
echo "   📹 Auflösung: ${WIDTH}x${HEIGHT} @ ${FPS}fps"
echo "   🔄 Rotation: ${ROTATION}°"
echo "   📷 Kamera: ${CAMERA}"
echo "   🌐 Port: ${PORT}"
echo ""

# Prüfe rpicam/libcamera (Trixie vs Bookworm)
CAMERA_CMD=""
if command -v rpicam-vid &> /dev/null; then
    CAMERA_CMD="rpicam-vid"
    print_info "Trixie-Modus: rpicam-vid"
elif command -v libcamera-vid &> /dev/null; then
    CAMERA_CMD="libcamera-vid"
    print_info "Bookworm-Modus: libcamera-vid"
else
    print_error "Weder rpicam-vid noch libcamera-vid gefunden!"
    exit 1
fi

print_info "Starte TCP Preview-Stream..."
echo ""

# Starte mit TCP Streaming (Bookworm-kompatibel)
# WICHTIG: --inline für Low-Latency
# WICHTIG: --flush für sofortiges Schreiben
$CAMERA_CMD \
    --camera $CAMERA \
    --width $WIDTH \
    --height $HEIGHT \
    --framerate $FPS \
    --rotation $ROTATION \
    --timeout 0 \
    --inline \
    --flush \
    --codec h264 \
    --profile baseline \
    --level 4.0 \
    --listen \
    -o "tcp://0.0.0.0:${PORT}" &

STREAM_PID=$!
echo $STREAM_PID > "$PIDFILE"

# Warte auf Stream-Start
sleep 2

if ps -p $STREAM_PID > /dev/null 2>&1; then
    print_success "TCP Preview-Stream gestartet!"
    echo ""
    print_info "Verbindung:"
    echo "   tcp://$(hostname):${PORT}"
    echo "   tcp://$(hostname -I | awk '{print $1}'):${PORT}"
    echo ""
    print_info "Stoppen mit: $0 --stop"
    print_info "Status mit: $0 --status"
    echo ""
    print_success "Stream läuft (PID: $STREAM_PID)"
else
    print_error "Stream-Start fehlgeschlagen!"
    rm -f "$PIDFILE"
    exit 1
fi
