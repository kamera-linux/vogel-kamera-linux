#!/bin/bash
# =============================================================================
# Preview-Stream Watchdog für Auto-Trigger System
# =============================================================================
# Hält den Preview-Stream am Laufen, auch wenn Verbindungen getrennt werden
# Startet rpicam-vid automatisch neu bei Fehlern
#
# Verwendung:
#   ./start-preview-stream-watchdog.sh [OPTIONS]
# =============================================================================

set -e

PORT=8554
WIDTH=640
HEIGHT=480
FPS=5
ROTATION=180
BITRATE=1000
CAMERA=0
PIDFILE="/tmp/preview-stream-watchdog.pid"
LOGFILE="/tmp/preview-stream-watchdog.log"

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

check_status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_success "Preview-Stream Watchdog läuft (PID: $PID)"
            echo ""
            print_info "Stream-URL: tcp://$(hostname -I | awk '{print $1}'):$PORT"
            return 0
        else
            print_warning "PID-File existiert, aber Watchdog läuft nicht"
            rm -f "$PIDFILE"
            return 1
        fi
    else
        print_warning "Preview-Stream Watchdog läuft nicht"
        return 1
    fi
}

stop_watchdog() {
    print_info "Stoppe Preview-Stream Watchdog..."
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 2
            
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
            fi
            
            rm -f "$PIDFILE"
            print_success "Watchdog gestoppt"
        fi
    fi
    
    # Stoppe alle rpicam-vid Prozesse
    pkill -f "rpicam-vid.*preview" || true
    print_success "Alle Stream-Prozesse beendet"
}

start_stream_once() {
    rpicam-vid \
        --camera "$CAMERA" \
        --width "$WIDTH" \
        --height "$HEIGHT" \
        --framerate "$FPS" \
        --rotation "$ROTATION" \
        --bitrate $((BITRATE * 1000)) \
        --inline \
        --codec h264 \
        --profile baseline \
        --level 4.2 \
        --flush \
        -t 0 \
        -o "tcp://0.0.0.0:$PORT?listen=1" \
        --nopreview \
        2>&1
}

watchdog_loop() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Watchdog gestartet" >> "$LOGFILE"
    
    while true; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starte Stream..." >> "$LOGFILE"
        
        # Starte Stream und logge Output
        start_stream_once >> "$LOGFILE" 2>&1
        
        EXIT_CODE=$?
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stream beendet (Exit: $EXIT_CODE)" >> "$LOGFILE"
        
        # Warte 2 Sekunden vor Neustart
        sleep 2
    done
}

start_watchdog() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_error "Watchdog läuft bereits (PID: $PID)"
            check_status
            exit 1
        fi
    fi
    
    print_info "Starte Preview-Stream Watchdog..."
    echo ""
    echo "  📹 Kamera: $CAMERA"
    echo "  📐 Auflösung: ${WIDTH}x${HEIGHT}"
    echo "  🎬 FPS: $FPS"
    echo "  🔄 Rotation: ${ROTATION}°"
    echo "  📊 Bitrate: ${BITRATE} kbps"
    echo "  🔌 Port: $PORT"
    echo "  🔄 Auto-Restart: Aktiv"
    echo ""
    
    # Starte Watchdog im Hintergrund
    watchdog_loop &
    
    WATCHDOG_PID=$!
    echo "$WATCHDOG_PID" > "$PIDFILE"
    
    sleep 3
    
    if ps -p "$WATCHDOG_PID" > /dev/null 2>&1; then
        print_success "Watchdog gestartet (PID: $WATCHDOG_PID)"
        echo ""
        IP=$(hostname -I | awk '{print $1}')
        print_info "Stream-URL: tcp://$IP:$PORT"
        echo ""
        print_info "Stream wird automatisch neu gestartet bei Verbindungsabbrüchen"
        echo ""
        print_info "Verwende auf dem Client-PC:"
        echo "  ./run-auto-trigger.sh --trigger-duration 2 --ai-model bird-species"
        echo ""
        print_info "Log-Datei: $LOGFILE"
        print_info "Log anzeigen: tail -f $LOGFILE"
    else
        print_error "Watchdog konnte nicht gestartet werden"
        rm -f "$PIDFILE"
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
            stop_watchdog
            exit 0
            ;;
        --status)
            check_status
            exit $?
            ;;
        --logs)
            tail -f "$LOGFILE"
            exit 0
            ;;
        --help|-h)
            echo "Verwendung: $0 [OPTIONS]"
            echo ""
            echo "Optionen:"
            echo "  --port PORT          TCP-Port (default: 8554)"
            echo "  --width WIDTH        Stream-Breite (default: 640)"
            echo "  --height HEIGHT      Stream-Höhe (default: 480)"
            echo "  --fps FPS            Framerate (default: 5)"
            echo "  --rotation DEG       Rotation in Grad (default: 180)"
            echo "  --bitrate KBPS       Bitrate in kbps (default: 1000)"
            echo "  --camera ID          Kamera-ID (default: 0)"
            echo "  --stop               Beendet Watchdog"
            echo "  --status             Zeigt Status"
            echo "  --logs               Zeigt Live-Logs"
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

start_watchdog
