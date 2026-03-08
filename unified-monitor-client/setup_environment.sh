#!/bin/bash
# Setup-Wrapper für Unified Monitor Client
# macht es einfacher, das Setup zu starten
#
# Verwendung:
#   ./setup_environment.sh              # Installation
#   ./setup_environment.sh --uninstall  # Deinstallation

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Farben
GREEN='\033[0;32m'
BLUE='\033[1;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Bestimme Modus
MODE="SETUP"
if [[ "$1" == "--uninstall" ]]; then
    MODE="UNINSTALL"
fi

echo -e "${BLUE}"
if [ "$MODE" = "UNINSTALL" ]; then
    echo "=================================================="
    echo "🗑️  Unified Monitor Client - Deinstallation"
    echo "=================================================="
else
    echo "=================================================="
    echo "🐦 Unified Monitor Client - Setup"
    echo "=================================================="
fi
echo -e "${NC}"

# Prüfe auf Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python3 nicht gefunden!${NC}"
    echo "Installieren Sie Python3:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-venv"
    echo "  macOS: brew install python3"
    exit 1
fi

# Für Uninstall: .env Datei optional (nicht erforderlich)
# Für Setup: .env Datei erforderlich
if [ "$MODE" = "SETUP" ]; then
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env-Datei nicht gefunden!${NC}"
        echo ""
        echo "Erstellen Sie eine .env-Datei mit:"
        echo "  SSH_KEY=~/.ssh/id_rsa_pi"
        echo "  SSH_USER=pi"
        echo "  SSH_HOST=raspberry-pi.local"
        echo ""
        exit 1
    fi
fi

# Starten Sie Setup/Uninstall
if [ "$MODE" = "UNINSTALL" ]; then
    echo -e "${GREEN}✓ Starte Deinstallation...${NC}"
    echo ""
    python3 setup_environment.py --uninstall
else
    echo -e "${GREEN}✓ Starte Setup-Skript...${NC}"
    echo ""
    python3 setup_environment.py
fi

exit $?
