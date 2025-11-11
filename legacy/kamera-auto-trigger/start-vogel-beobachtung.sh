#!/bin/bash
# =============================================================================
# Vogel-Beobachtung Starter
# =============================================================================
# Komfort-Wrapper mit System-Checks und optimierten Einstellungen
# 
# Verwendung:
#   ./start-vogel-beobachtung.sh           # Ohne KI-Aufnahme (Standard, schnell)
#   ./start-vogel-beobachtung.sh --with-ai # Mit KI-Aufnahme (Objekterkennung)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_TRIGGER="$SCRIPT_DIR/run-auto-trigger.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Hilfe-Funktion
show_help() {
    cat << 'EOF'
🐦 Vogel-Beobachtung Starter

Verwendung:
  ./start-vogel-beobachtung.sh              Standard-Modus (ohne KI-Aufnahme)
  ./start-vogel-beobachtung.sh --with-ai    Mit KI-Aufnahme
  ./start-vogel-beobachtung.sh --slowmo     Zeitlupen-Aufnahme

Modi:
  📹 Standard (ohne Parameter):
     - Trigger MIT KI (erkennt Vögel)
     - Aufnahme OHNE KI (nur Video + Audio)
     - 4096x2160 @ 30fps
     - Audio: 44.1kHz Mono (falls USB-Mikrofon vorhanden)
     - Schneller, weniger CPU-Last
     - Empfohlen für längere Sessions

  🤖 Mit KI (--with-ai):
     - Trigger MIT KI (erkennt Vögel)
     - Aufnahme MIT KI (Objekterkennung während Aufnahme + Audio)
     - 4096x2160 @ 30fps
     - Audio: 44.1kHz Mono (falls USB-Mikrofon vorhanden)
     - Höhere CPU-Last auf Raspberry Pi
     - Objekt-Metadaten in Videos

  🎬 Zeitlupe (--slowmo):
     - Trigger MIT KI (erkennt Vögel)
     - Aufnahme in Zeitlupe (120fps + Audio)
     - 1536x864 @ 120fps
     - Audio: 44.1kHz Mono (falls USB-Mikrofon vorhanden)
     - Für spektakuläre Zeitlupen-Aufnahmen
     - Niedrigere Auflösung für Performance

Hinweis:
  🎤 Audio wird automatisch aufgenommen, wenn ein USB-Mikrofon
     am Raspberry Pi angeschlossen ist. Ohne Mikrofon wird nur
     Video aufgenommen (mit Warnung im Log).

Optionen:
  -h, --help     Zeige diese Hilfe

Beispiele:
  ./start-vogel-beobachtung.sh              # Standard, schnell
  ./start-vogel-beobachtung.sh --with-ai    # Mit KI-Analyse
  ./start-vogel-beobachtung.sh --slowmo     # Zeitlupe 120fps

EOF
    exit 0
}

# Parse Parameter
WITH_AI=false
SLOWMO=false
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
elif [[ "$1" == "--with-ai" ]]; then
    WITH_AI=true
elif [[ "$1" == "--slowmo" ]]; then
    SLOWMO=true
elif [[ -n "$1" ]]; then
    echo "❌ Unbekannter Parameter: $1"
    echo "Nutze --help für Hilfe"
    exit 1
fi

clear

if [ "$SLOWMO" = true ]; then
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
                                                                  
   🐦 VOGEL-BEOBACHTUNG - ZEITLUPEN-MODUS 🎬🐦                 
                                                                  
╚══════════════════════════════════════════════════════════════════╝
EOF
elif [ "$WITH_AI" = true ]; then
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
                                                                  
   🐦 VOGEL-BEOBACHTUNG - MIT KI-AUFNAHME 🤖🎥                    
                                                                  
╚══════════════════════════════════════════════════════════════════╝
EOF
else
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
                                                                  
   🐦 VOGEL-BEOBACHTUNG - PRODUKTIV-BETRIEB 🎥                    
                                                                  
╚══════════════════════════════════════════════════════════════════╝
EOF
fi

echo ""
echo -e "${CYAN}📋 SYSTEM-CHECK...${NC}"
echo ""

# TCP Watchdog Check (wird vom Python-Script automatisch gestartet)
echo -n "🔍 TCP Watchdog Skript... "
if ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had '[ -f ~/vogel-kamera-linux/raspberry-pi-scripts/start-tcp-preview-watchdog.sh ]'; then
    echo -e "${GREEN}✅ vorhanden${NC}"
else
    echo -e "${RED}❌ nicht gefunden${NC}"
    echo ""
    echo -e "${RED}FEHLER: TCP Watchdog Skript fehlt auf dem Raspberry Pi!${NC}"
    echo "Stelle sicher dass das Skript existiert:"
    echo "  ~/vogel-kamera-linux/raspberry-pi-scripts/start-tcp-preview-watchdog.sh"
    exit 1
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
echo "  📹 Aufnahme-Dauer:      1 Minute"
echo "  🎯 Erkennungs-Schwelle: 5 (optimiert für CPU-Limit)"
echo "  📺 Preview-Auflösung:   640x480 @ 5fps (CPU-optimiert)"
echo "  ⏱️  Cooldown:           15 Sekunden"
echo "  🤖 Trigger-AI:          bird-species (nur Vögel)"

if [ "$WITH_AI" = true ]; then
    echo -e "  ${MAGENTA}🤖 Aufnahme-Modus:      MIT KI (Objekterkennung während Aufnahme)${NC}"
    echo -e "  ${YELLOW}⚠️  CPU-Last:            Höher (KI läuft auf Raspberry Pi)${NC}"
else
    echo -e "  ${GREEN}📹 Aufnahme-Modus:      OHNE KI (nur Video, schneller)${NC}"
    echo -e "  ${GREEN}✅ CPU-Last:            Niedriger (optimiert)${NC}"
fi

echo ""
echo -e "${CYAN}📊 STATUS-UPDATES:      Alle 5 Minuten${NC}"
echo ""
echo -e "${YELLOW}💡 TIPP: Beobachte die Ausgabe!${NC}"
echo "   Bei Vogel-Erkennung siehst du:"
echo "   🐦 Vogel-Trigger wird aktiviert!"
if [ "$WITH_AI" = true ]; then
    echo "   🤖 Starte HD-Aufnahme MIT KI-Analyse..."
else
    echo "   📹 Starte HD-Aufnahme (nur Video)..."
fi
echo ""

if [ "$WITH_AI" = true ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  HINWEIS: KI-Aufnahme-Modus aktiviert${NC}"
    echo -e "${YELLOW}   - Objekterkennung läuft während der Aufnahme${NC}"
    echo -e "${YELLOW}   - Höhere CPU-Last auf Raspberry Pi${NC}"
    echo -e "${YELLOW}   - Erkannte Objekte werden in Video-Metadaten gespeichert${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Standard-Modus: Schnelle Aufnahmen ohne KI-Overhead${NC}"
    echo -e "${GREEN}   - Trigger nutzt KI (erkannt = Aufnahme startet)${NC}"
    echo -e "${GREEN}   - Aufnahme ohne KI = weniger CPU-Last${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi

echo ""
read -p "$(echo -e ${GREEN}Bereit? Drücke ENTER zum Starten...${NC})" -r
echo ""

# Cleanup-Funktion für sauberes Beenden
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Beende Vogel-Beobachtung...${NC}"
    
    # Sende SIGTERM an Auto-Trigger (ermöglicht sauberes Shutdown mit Watchdog-Stop)
    if [ -n "$AUTO_TRIGGER_PID" ] && kill -0 "$AUTO_TRIGGER_PID" 2>/dev/null; then
        echo "📡 Sende Shutdown-Signal an Auto-Trigger..."
        kill -TERM "$AUTO_TRIGGER_PID" 2>/dev/null
        
        # Warte max 10 Sekunden auf sauberes Beenden (inkl. Watchdog-Stop via SSH)
        for i in {1..20}; do
            if ! kill -0 "$AUTO_TRIGGER_PID" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        
        # Falls noch aktiv, erzwinge Beenden
        if kill -0 "$AUTO_TRIGGER_PID" 2>/dev/null; then
            echo "⚠️  Erzwinge Beenden..."
            kill -9 "$AUTO_TRIGGER_PID" 2>/dev/null
        fi
    fi
    
    # Zusätzliche Bereinigung (falls Python-Cleanup fehlschlug)
    echo -n "🧹 Bereinige Remote-Prozesse... "
    ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had 'cd ~/vogel-kamera-linux/raspberry-pi-scripts && ./start-tcp-preview-watchdog.sh --stop 2>/dev/null; pkill -9 -f rpicam-vid 2>/dev/null; pkill -9 -f ffmpeg 2>/dev/null; pkill -9 -f arecord 2>/dev/null' > /dev/null 2>&1
    
    echo -e "${GREEN}✅${NC}"
    echo ""
    echo -e "${GREEN}👋 Auf Wiedersehen!${NC}"
    exit 0
}

# Trap nur für SIGINT (CTRL+C) und SIGTERM - NICHT für EXIT
trap cleanup SIGINT SIGTERM

# Starte Auto-Trigger
if [ "$SLOWMO" = true ]; then
    echo -e "${CYAN}🚀 Starte Vogel-Beobachtung ZEITLUPEN-MODUS (120fps)...${NC}"
elif [ "$WITH_AI" = true ]; then
    echo -e "${MAGENTA}🚀 Starte Vogel-Beobachtung MIT KI-Aufnahme...${NC}"
else
    echo -e "${GREEN}🚀 Starte Vogel-Beobachtung (Standard-Modus)...${NC}"
fi
echo -e "${YELLOW}   (Drücke CTRL+C zum Beenden)${NC}"
echo ""

if [ "$SLOWMO" = true ]; then
    # ZEITLUPE (120fps, 1536x864) - gleiche Trigger-Parameter wie Standard
    "$AUTO_TRIGGER" \
        --trigger-duration 1 \
        --trigger-threshold 0.50 \
        --cooldown 15 \
        --status-interval 5 \
        --recording-slowmo \
        --preview-fps 5 \
        --preview-width 640 \
        --preview-height 480 &
    AUTO_TRIGGER_PID=$!
    wait $AUTO_TRIGGER_PID 2>/dev/null
elif [ "$WITH_AI" = true ]; then
    # MIT KI-Aufnahme mit CPU-optimierten Parametern
    "$AUTO_TRIGGER" \
        --trigger-duration 1 \
        --trigger-threshold 0.50 \
        --cooldown 15 \
        --status-interval 5 \
        --recording-ai \
        --recording-ai-model bird-species \
        --preview-fps 5 \
        --preview-width 640 \
        --preview-height 480 &
    AUTO_TRIGGER_PID=$!
    wait $AUTO_TRIGGER_PID 2>/dev/null
else
    # OHNE KI-Aufnahme (Standard) mit CPU-optimierten Parametern
    "$AUTO_TRIGGER" \
        --trigger-duration 1 \
        --trigger-threshold 0.50 \
        --cooldown 15 \
        --status-interval 5 \
        --preview-fps 5 \
        --preview-width 640 \
        --preview-height 480 &
    AUTO_TRIGGER_PID=$!
    wait $AUTO_TRIGGER_PID 2>/dev/null
fi

# Cleanup wird durch trap bei SIGINT/SIGTERM automatisch ausgeführt
