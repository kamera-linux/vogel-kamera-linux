#!/bin/bash
# =============================================================================
# Vogel-Beobachtung Starter
# =============================================================================
# Komfort-Wrapper mit System-Checks und optimierten Einstellungen
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_TRIGGER="$SCRIPT_DIR/run-auto-trigger.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
                                                                  
   🐦 VOGEL-BEOBACHTUNG - PRODUKTIV-BETRIEB 🎥                    
                                                                  
╚══════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo -e "${CYAN}📋 SYSTEM-CHECK...${NC}"
echo ""

# Prüfe Stream
echo -n "🔍 Preview-Stream... "
if ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had './start-rtsp-stream.sh --status' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ läuft bereits${NC}"
else
    echo -e "${YELLOW}⚠️  läuft nicht${NC}"
    echo -n "   🚀 Starte Stream automatisch... "
    if ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had 'nohup ./start-rtsp-stream.sh > /dev/null 2>&1 &' && sleep 3; then
        if ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had './start-rtsp-stream.sh --status' > /dev/null 2>&1; then
            echo -e "${GREEN}✅ gestartet${NC}"
        else
            echo -e "${RED}❌ fehlgeschlagen${NC}"
            echo ""
            echo -e "${RED}Stream konnte nicht gestartet werden!${NC}"
            echo -e "${YELLOW}Bitte prüfe manuell auf dem Raspberry Pi.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ fehlgeschlagen${NC}"
        exit 1
    fi
fi

# Prüfe Auto-Trigger
echo -n "🐍 Auto-Trigger... "
if [ -f "$AUTO_TRIGGER" ]; then
    echo -e "${GREEN}✅ gefunden${NC}"
else
    echo -e "${RED}❌ nicht gefunden!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ System bereit!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}⚙️  EINSTELLUNGEN:${NC}"
echo ""
echo "  📹 Aufnahme-Dauer:      2 Minuten"
echo "  🎯 Erkennungs-Schwelle: 0.60 (präzise)"
echo "  ⏱️  Cooldown:           10 Sekunden"
echo "  🤖 AI-Model:            bird-species (nur Vögel)"
echo ""
echo -e "${CYAN}📊 STATUS-UPDATES:      Alle 5 Sekunden${NC}"
echo ""
echo -e "${YELLOW}💡 TIPP: Beobachte die Ausgabe!${NC}"
echo "   Bei Vogel-Erkennung siehst du:"
echo "   🐦 Vogel-Trigger wird aktiviert!"
echo "   📹 Starte HD-Aufnahme..."
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
read -p "$(echo -e ${GREEN}Bereit? Drücke ENTER zum Starten...${NC})" -r
echo ""

# Cleanup-Funktion für sauberes Beenden
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Beende Vogel-Beobachtung...${NC}"
    echo -n "🧹 Räume Remote-Prozesse auf... "
    
    # Beende alle Kamera-Prozesse inklusive Watchdog auf dem Remote-Host
    ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had 'pkill -9 -f stream-wrapper.sh; pkill -9 -f rpicam-vid; pkill -9 -f libcamera-vid; pkill -9 -f ffmpeg; pkill -9 -f arecord; rm -f /tmp/*.pid' > /dev/null 2>&1
    
    echo -e "${GREEN}✅${NC}"
    echo ""
    echo -e "${GREEN}👋 Auf Wiedersehen!${NC}"
    exit 0
}

# Trap für SIGINT (CTRL+C) und EXIT
trap cleanup SIGINT SIGTERM EXIT

# Starte Auto-Trigger
echo -e "${GREEN}🚀 Starte Vogel-Beobachtung...${NC}"
echo -e "${YELLOW}   (Drücke CTRL+C zum Beenden)${NC}"
echo ""

"$AUTO_TRIGGER" \
    --trigger-duration 2 \
    --trigger-threshold 0.60 \
    --cooldown 10 \
    --status-interval 5

# Cleanup wird durch trap automatisch ausgeführt
