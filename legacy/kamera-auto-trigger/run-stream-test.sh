#!/bin/bash
# =============================================================================
# Stream-Test Wrapper
# =============================================================================
# Testet die Stream-Verbindung und AI-Erkennung
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
STREAM_PROCESSOR="$SCRIPT_DIR/scripts/stream_processor.py"

# Prüfe Python venv
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Python venv nicht gefunden: $VENV_PYTHON"
    exit 1
fi

# Prüfe ob Skript existiert
if [ ! -f "$STREAM_PROCESSOR" ]; then
    echo "❌ Stream-Processor nicht gefunden: $STREAM_PROCESSOR"
    exit 1
fi

echo "🎬 Starte Stream-Test..."
echo "   Python: $VENV_PYTHON"
echo ""

# Wechsle ins Projektverzeichnis
cd "$PROJECT_ROOT"

# Führe Stream-Test aus
exec "$VENV_PYTHON" "$STREAM_PROCESSOR" "$@"
