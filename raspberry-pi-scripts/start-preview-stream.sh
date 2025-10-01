#!/bin/bash
# =============================================================================
# RTSP Preview-Stream für Auto-Trigger System
# =============================================================================
# Dieses Skript startet einen RTSP-Server auf dem Raspberry Pi 5,
# der einen Low-Latency Preview-Stream für die Vogel-Erkennung bereitstellt.
#
# Verwendung:
#   ./start-preview-stream.sh [OPTIONS]
#
# Optionen:
#   --port PORT          RTSP-Port (default: 8554)
#   --width WIDTH        Stream-Breite (default: 640)
#   --height HEIGHT      Stream-Höhe (default: 480)
#   --fps FPS            Framerate (default: 5)
#   --rotation DEG       Rotation in Grad (default: 180)
#   --bitrate KBPS       Bitrate in kbps (default: 1000)
#   --stop               Beendet laufenden Preview-Stream
#   --status             Zeigt Status des Streams
# =============================================================================

set -e

# Defaults
PORT=8554
WIDTH=640
HEIGHT=480
FPS=5
ROTATION=180
BITRATE=1000
CAMERA=0
PIDFILE="/tmp/preview-stream.pid"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
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

# Status prüfen
check_status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_success "Preview-Stream läuft (PID: $PID)"
            echo ""
            print_info "Stream-URL: rtsp://$(hostname -I | awk '{print $1}'):$PORT/preview"
            echo ""
            print_info "Prozess-Info:"
            ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,cmd --no-headers
            return 0
        else
            print_warning "PID-File existiert, aber Prozess läuft nicht"
            rm -f "$PIDFILE"
            return 1
        fi
    else
        print_warning "Preview-Stream läuft nicht"
        return 1
    fi
}

# Stream stoppen
stop_stream() {
    print_info "Stoppe Preview-Stream..."
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 2
            
            # Force kill falls noch läuft
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
            fi
            
            rm -f "$PIDFILE"
            print_success "Preview-Stream gestoppt"
        else
            print_warning "Prozess läuft bereits nicht mehr"
            rm -f "$PIDFILE"
        fi
    else
        print_warning "Kein laufender Stream gefunden"
    fi
    
    # Cleanup: Alle rpicam-vid Prozesse für Preview beenden
    pkill -f "rpicam-vid.*preview" || true
}

# Stream starten
start_stream() {
    # Prüfe ob bereits läuft
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_error "Preview-Stream läuft bereits (PID: $PID)"
            echo ""
            check_status
            exit 1
        else
            rm -f "$PIDFILE"
        fi
    fi
    
    print_info "Starte Preview-Stream..."
    echo ""
    echo "  📹 Kamera: $CAMERA"
    echo "  📐 Auflösung: ${WIDTH}x${HEIGHT}"
    echo "  🎬 FPS: $FPS"
    echo "  🔄 Rotation: ${ROTATION}°"
    echo "  📊 Bitrate: ${BITRATE} kbps"
    echo "  🔌 Port: $PORT"
    echo ""
    
    # rpicam-vid mit RTSP
    # --inline: H.264 Inline-Headers für bessere Kompatibilität
    # --listen: RTSP-Server-Modus
    # -t 0: Unbegrenzte Laufzeit
    # --flush: Buffer sofort leeren für niedrige Latenz
    # --codec h264: H.264-Codec
    # --profile baseline: Baseline-Profile für Kompatibilität
    # --level 4.2: H.264 Level
    # --framerate: FPS
    # --width/height: Auflösung
    # --rotation: Rotation in Grad
    # --bitrate: Bitrate in bits/s (daher * 1000)
    
    nohup rpicam-vid \
        --camera "$CAMERA" \
        --width "$WIDTH" \
        --height "$HEIGHT" \
        --framerate "$FPS" \
        --rotation "$ROTATION" \
        --bitrate $((BITRATE * 1000)) \
        --inline \
        --listen \
        --codec h264 \
        --profile baseline \
        --level 4.2 \
        --flush \
        -t 0 \
        -o "tcp://0.0.0.0:$PORT" \
        --nopreview \
        > /tmp/preview-stream.log 2>&1 &
    
    PID=$!
    echo "$PID" > "$PIDFILE"
    
    # Warte kurz und prüfe ob Prozess läuft
    sleep 2
    
    if ps -p "$PID" > /dev/null 2>&1; then
        print_success "Preview-Stream gestartet (PID: $PID)"
        echo ""
        IP=$(hostname -I | awk '{print $1}')
        print_info "Stream-URL: tcp://$IP:$PORT"
        echo ""
        print_info "Verwende auf dem Client-PC:"
        echo "  python python-skripte/ai-had-kamera-auto-trigger.py \\"
        echo "      --trigger-duration 2 \\"
        echo "      --ai-model bird-species"
        echo ""
        print_info "Log-Datei: /tmp/preview-stream.log"
    else
        print_error "Stream konnte nicht gestartet werden"
        rm -f "$PIDFILE"
        echo ""
        print_info "Log-Ausgabe:"
        cat /tmp/preview-stream.log
        exit 1
    fi
}

# Parameter parsen
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --width)
            WIDTH="$2"
            shift 2
            ;;
        --height)
            HEIGHT="$2"
            shift 2
            ;;
        --fps)
            FPS="$2"
            shift 2
            ;;
        --rotation)
            ROTATION="$2"
            shift 2
            ;;
        --bitrate)
            BITRATE="$2"
            shift 2
            ;;
        --camera)
            CAMERA="$2"
            shift 2
            ;;
        --stop)
            stop_stream
            exit 0
            ;;
        --status)
            check_status
            exit $?
            ;;
        --help|-h)
            echo "Verwendung: $0 [OPTIONS]"
            echo ""
            echo "Optionen:"
            echo "  --port PORT          RTSP-Port (default: 8554)"
            echo "  --width WIDTH        Stream-Breite (default: 640)"
            echo "  --height HEIGHT      Stream-Höhe (default: 480)"
            echo "  --fps FPS            Framerate (default: 5)"
            echo "  --rotation DEG       Rotation in Grad (default: 180)"
            echo "  --bitrate KBPS       Bitrate in kbps (default: 1000)"
            echo "  --camera ID          Kamera-ID (default: 0)"
            echo "  --stop               Beendet laufenden Preview-Stream"
            echo "  --status             Zeigt Status des Streams"
            echo "  --help, -h           Zeigt diese Hilfe"
            exit 0
            ;;
        *)
            print_error "Unbekannte Option: $1"
            echo "Verwende --help für Hilfe"
            exit 1
            ;;
    esac
done

# Stream starten
start_stream
