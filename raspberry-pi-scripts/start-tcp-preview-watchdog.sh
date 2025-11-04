#!/bin/bash
# =============================================================================
# TCP Preview-Stream Watchdog für Auto-Trigger System (Trixie/Bookworm)
# =============================================================================
# Hält den TCP Preview-Stream am Laufen, auch wenn Verbindungen getrennt werden
# Startet rpicam-vid/libcamera-vid automatisch neu bei Fehlern
#
# Verwendung:
#   ./start-tcp-preview-watchdog.sh [OPTIONS]
# =============================================================================

set -e

PORT=8554
WIDTH=640
HEIGHT=480
FPS=5
ROTATION=180
CAMERA=0
PIDFILE="/tmp/tcp-preview-watchdog.pid"
LOGFILE="/tmp/tcp-preview-watchdog.log"

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

# Erkenne Trixie vs Bookworm
CAMERA_CMD=""
if command -v rpicam-vid &> /dev/null; then
    CAMERA_CMD="rpicam-vid"
    SYSTEM_NAME="Trixie"
elif command -v libcamera-vid &> /dev/null; then
    CAMERA_CMD="libcamera-vid"
    SYSTEM_NAME="Bookworm"
else
    print_error "Weder rpicam-vid noch libcamera-vid gefunden!"
    exit 1
fi

check_status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_success "TCP Preview Watchdog läuft (PID: $PID, System: $SYSTEM_NAME)"
            echo ""
            print_info "Stream-URL: tcp://$(hostname -I | awk '{print $1}'):$PORT"
            print_info "Log: tail -f $LOGFILE"
            return 0
        else
            print_warning "PID-File existiert, aber Watchdog läuft nicht"
            rm -f "$PIDFILE"
            return 1
        fi
    else
        print_warning "TCP Preview Watchdog läuft nicht"
        return 1
    fi
}

stop_watchdog() {
    print_info "Stoppe TCP Preview Watchdog..."
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID" 2>/dev/null || true
            sleep 2
            
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID" 2>/dev/null || true
            fi
            
            rm -f "$PIDFILE"
            print_success "Watchdog gestoppt"
        fi
    fi
    
    # Stoppe alle Stream-Prozesse
    pkill -f "rpicam-vid.*tcp" 2>/dev/null || true
    pkill -f "libcamera-vid.*tcp" 2>/dev/null || true
    print_success "Alle Stream-Prozesse beendet"
}

start_stream_once() {
    $CAMERA_CMD \
        --camera "$CAMERA" \
        --width "$WIDTH" \
        --height "$HEIGHT" \
        --framerate "$FPS" \
        --rotation "$ROTATION" \
        --inline \
        --flush \
        --codec h264 \
        --profile baseline \
        --level 4.0 \
        -t 0 \
        -o "tcp://0.0.0.0:$PORT?listen=1" \
        --nopreview \
        2>&1
}

watchdog_loop() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Watchdog gestartet ($SYSTEM_NAME: $CAMERA_CMD)" >> "$LOGFILE"
    
    while true; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starte TCP Stream..." >> "$LOGFILE"
        
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
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║   🔄 TCP PREVIEW WATCHDOG ($SYSTEM_NAME)                        ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    print_info "Konfiguration:"
    echo "  📹 Kamera: $CAMERA"
    echo "  📐 Auflösung: ${WIDTH}x${HEIGHT}"
    echo "  🎬 FPS: $FPS"
    echo "  🔄 Rotation: ${ROTATION}°"
    echo "  🔌 Port: $PORT"
    echo "  🤖 System: $SYSTEM_NAME ($CAMERA_CMD)"
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
        print_info "Log-Datei: $LOGFILE"
        print_info "Log anzeigen: tail -f $LOGFILE"
        echo ""
        print_success "Watchdog läuft!"
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
            if [ -f "$LOGFILE" ]; then
                tail -f "$LOGFILE"
            else
                print_warning "Log-Datei nicht gefunden: $LOGFILE"
            fi
            exit 0
            ;;
        --help|-h)
            echo "Verwendung: $0 [OPTIONS]"
            echo ""
            echo "TCP Preview-Stream Watchdog für Bookworm/Trixie"
            echo ""
            echo "Optionen:"
            echo "  --port PORT          TCP-Port (default: 8554)"
            echo "  --width WIDTH        Stream-Breite (default: 640)"
            echo "  --height HEIGHT      Stream-Höhe (default: 480)"
            echo "  --fps FPS            Framerate (default: 5)"
            echo "  --rotation DEG       Rotation in Grad (default: 180)"
            echo "  --camera ID          Kamera-ID (default: 0)"
            echo "  --stop               Beendet Watchdog"
            echo "  --status             Zeigt Status"
            echo "  --logs               Zeigt Live-Logs"
            echo "  --help, -h           Zeigt diese Hilfe"
            echo ""
            echo "Beispiele:"
            echo "  $0                   Startet Watchdog mit Defaults"
            echo "  $0 --camera 1        Startet mit Kamera 1"
            echo "  $0 --stop            Stoppt Watchdog"
            echo "  $0 --logs            Zeigt Live-Logs"
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
