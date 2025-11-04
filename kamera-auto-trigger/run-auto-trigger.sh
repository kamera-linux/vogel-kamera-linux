#!/bin/bash
# =============================================================================
# Auto-Trigger Wrapper
# =============================================================================
# Startet das Auto-Trigger-System mit der korrekten Python-Umgebung
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
AUTO_TRIGGER_SCRIPT="$SCRIPT_DIR/scripts/ai-had-kamera-auto-trigger.py"

# Prüfe Python venv
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Python venv nicht gefunden: $VENV_PYTHON"
    echo "Bitte führe zuerst aus: python3 -m venv .venv && .venv/bin/pip install -r kamera-auto-trigger/requirements.txt"
    exit 1
fi

# TCP Watchdog wird vom Python-Script verwaltet
echo "✅ TCP Stream Watchdog wird automatisch gestartet"
echo ""

# Cleanup-Funktion für sauberes Beenden
cleanup() {
    echo ""
    echo "🧹 Räume Remote-Prozesse auf..."
    
    # Beende alle Kamera-Prozesse inklusive Watchdog auf dem Remote-Host
    ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had 'pkill -9 -f stream-wrapper.sh; pkill -9 -f rpicam-vid; pkill -9 -f libcamera-vid; pkill -9 -f ffmpeg; pkill -9 -f arecord; rm -f /tmp/*.pid' > /dev/null 2>&1
    
    echo "✅ Cleanup abgeschlossen"
}

# Trap für SIGINT (CTRL+C) und EXIT
trap cleanup SIGINT SIGTERM EXIT

# Prüfe ob Skript existiert
if [ ! -f "$AUTO_TRIGGER_SCRIPT" ]; then
    echo "❌ Auto-Trigger-Skript nicht gefunden: $AUTO_TRIGGER_SCRIPT"
    exit 1
fi

echo "🐦 Starte Auto-Trigger System..."
echo "   Python: $VENV_PYTHON"
echo "   Skript: $AUTO_TRIGGER_SCRIPT"
echo ""

# Wechsle ins Projektverzeichnis (wichtig für Pfade)
cd "$PROJECT_ROOT"

# Setze Umgebungsvariablen für FFmpeg/H.264-Fehlerunterdrückung
export OPENCV_FFMPEG_CAPTURE_OPTIONS='loglevel;quiet'
export OPENCV_LOG_LEVEL='ERROR'
export AV_LOG_FORCE_NOCOLOR='1'
export FFREPORT='level=quiet'

# Führe Auto-Trigger aus und filtere H.264-Fehler aus stderr
# Cleanup wird durch trap automatisch ausgeführt
exec "$VENV_PYTHON" "$AUTO_TRIGGER_SCRIPT" "$@" 2> >(grep -v '\[h264' >&2)
