#!/bin/bash
# Start-Script für Unified Camera Monitor
# Startet den vereinheitlichten Kamera-Prozess auf dem Raspberry Pi

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktionen
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Standard-Parameter
CAMERA=0
THRESHOLD=0.4
COOLDOWN=15
TRIGGER_DURATION=1.0
VIDEO_PATH="/home/roimme/Videos/Vogelhaus"
PREVIEW_FPS=6
RECORDING_WIDTH=1920
RECORDING_HEIGHT=1080
RECORDING_FPS=30
MODEL_PATH=""

# Parse Argumente
while [[ $# -gt 0 ]]; do
    case $1 in
        --camera)
            CAMERA="$2"
            shift 2
            ;;
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        --cooldown)
            COOLDOWN="$2"
            shift 2
            ;;
        --trigger-duration)
            TRIGGER_DURATION="$2"
            shift 2
            ;;
        --video-path)
            VIDEO_PATH="$2"
            shift 2
            ;;
        --preview-fps)
            PREVIEW_FPS="$2"
            shift 2
            ;;
        --recording-width)
            RECORDING_WIDTH="$2"
            shift 2
            ;;
        --recording-height)
            RECORDING_HEIGHT="$2"
            shift 2
            ;;
        --recording-fps)
            RECORDING_FPS="$2"
            shift 2
            ;;
        --model)
            MODEL_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Verwendung: $0 [OPTIONEN]"
            echo ""
            echo "Optionen:"
            echo "  --camera NUM              Kamera-Nummer (default: 0)"
            echo "  --threshold FLOAT         AI-Schwelle (default: 0.4)"
            echo "  --cooldown SECONDS        Cooldown zwischen Aufnahmen (default: 15)"
            echo "  --trigger-duration FLOAT  Trigger-Dauer (default: 1.0)"
            echo "  --video-path PATH         Video-Speicher-Pfad"
            echo "  --preview-fps NUM         Preview FPS (default: 6)"
            echo "  --recording-width NUM     Aufnahme-Breite (default: 1920)"
            echo "  --recording-height NUM    Aufnahme-Höhe (default: 1080)"
            echo "  --recording-fps NUM       Aufnahme-FPS (default: 30)"
            echo "  --model PATH              Pfad zum YOLO-Model (optional)"
            echo "  --help                    Diese Hilfe anzeigen"
            exit 0
            ;;
        *)
            print_error "Unbekannte Option: $1"
            echo "Verwende --help für Hilfe"
            exit 1
            ;;
    esac
done

# Banner
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║   🎬 Unified Camera Monitor - Start                         ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Prüfe ob Script existiert
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MONITOR_SCRIPT="$SCRIPT_DIR/unified-camera-monitor.py"

if [ ! -f "$MONITOR_SCRIPT" ]; then
    print_error "Monitor-Script nicht gefunden: $MONITOR_SCRIPT"
    exit 1
fi

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    print_error "python3 nicht gefunden"
    exit 1
fi

# Prüfe picamera2
if ! python3 -c "import picamera2" 2>/dev/null; then
    print_error "picamera2 nicht installiert"
    echo "Installiere mit: sudo apt install -y python3-picamera2"
    exit 1
fi

# Prüfe ultralytics
if ! python3 -c "import ultralytics" 2>/dev/null; then
    print_info "ultralytics (YOLO) nicht installiert"
    echo "Installiere mit: pip install ultralytics"
    echo "Fahre fort im Fallback-Modus..."
fi

# Konfiguration anzeigen
print_info "Konfiguration:"
echo "  📹 Kamera: $CAMERA"
echo "  🎯 Schwelle: $THRESHOLD"
echo "  ⏳ Cooldown: ${COOLDOWN}s"
echo "  ⏱️  Trigger-Dauer: ${TRIGGER_DURATION}s"
echo "  📂 Video-Pfad: $VIDEO_PATH"
echo "  🎬 Preview: ${PREVIEW_FPS} FPS"
echo "  🎥 Recording: ${RECORDING_WIDTH}x${RECORDING_HEIGHT} @ ${RECORDING_FPS}fps"
if [ -n "$MODEL_PATH" ]; then
    echo "  🤖 Model: $MODEL_PATH"
fi
echo ""

# Erstelle Video-Verzeichnis
mkdir -p "$VIDEO_PATH"

# Baue Kommando
CMD="python3 $MONITOR_SCRIPT"
CMD="$CMD --camera $CAMERA"
CMD="$CMD --threshold $THRESHOLD"
CMD="$CMD --cooldown $COOLDOWN"
CMD="$CMD --trigger-duration $TRIGGER_DURATION"
CMD="$CMD --video-path $VIDEO_PATH"
CMD="$CMD --preview-fps $PREVIEW_FPS"
CMD="$CMD --recording-width $RECORDING_WIDTH"
CMD="$CMD --recording-height $RECORDING_HEIGHT"
CMD="$CMD --recording-fps $RECORDING_FPS"

if [ -n "$MODEL_PATH" ]; then
    CMD="$CMD --model $MODEL_PATH"
fi

print_success "Starte Unified Camera Monitor..."
echo ""

# Starte Monitor
exec $CMD
