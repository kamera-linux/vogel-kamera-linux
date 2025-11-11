#!/bin/bash
# =============================================================================
# Firewall-Setup für Raspberry Pi 5
# =============================================================================
# Öffnet benötigte Ports für das Vogel-Kamera-System
#
# Verwendung:
#   Auf Raspberry Pi ausführen:
#   ./setup-firewall-raspberry-pi.sh
#
# Oder remote vom Client-PC:
#   scp setup-firewall-raspberry-pi.sh user@raspberrypi-5-ai-had:~/
#   ssh user@raspberrypi-5-ai-had "sudo bash ~/setup-firewall-raspberry-pi.sh"
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🔥 Firewall-Setup für Raspberry Pi 5 (Vogel-Kamera)       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Prüfe ob UFW installiert ist
if ! command -v ufw &> /dev/null; then
    echo -e "${RED}❌ UFW ist nicht installiert!${NC}"
    echo -e "${YELLOW}Installiere mit: sudo apt install ufw${NC}"
    exit 1
fi

# Prüfe ob Script mit sudo ausgeführt wird
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Bitte mit sudo ausführen!${NC}"
    echo -e "${YELLOW}   sudo bash $0${NC}"
    exit 1
fi

echo -e "${GREEN}✅ UFW gefunden${NC}"
echo ""

# Zeige aktuelle UFW-Regeln
echo -e "${BLUE}📋 Aktuelle UFW-Regeln:${NC}"
ufw status numbered
echo ""

# Frage Benutzer
read -p "Möchtest du die Firewall-Regeln einrichten? (j/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    echo -e "${YELLOW}⛔ Abgebrochen${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🔧 Konfiguriere Firewall-Regeln...${NC}"
echo ""

# Port 22 (SSH) - Sollte bereits erlaubt sein
echo -e "${GREEN}→${NC} Erlaube SSH (Port 22)..."
ufw allow 22/tcp comment 'SSH'

# Port 8554 (TCP Preview-Stream)
echo -e "${GREEN}→${NC} Erlaube TCP Preview-Stream (Port 8554)..."
ufw allow 8554/tcp comment 'Vogel-Kamera Preview-Stream'

# Optional: Port 8554 UDP (falls RTSP verwendet wird)
echo -e "${GREEN}→${NC} Erlaube RTSP Stream optional (Port 8554 UDP)..."
ufw allow 8554/udp comment 'Vogel-Kamera RTSP Stream (optional)'

# Aktiviere UFW falls noch nicht aktiv
echo ""
if ufw status | grep -q "Status: inactive"; then
    echo -e "${YELLOW}⚠️  UFW ist inaktiv!${NC}"
    read -p "UFW jetzt aktivieren? (j/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        echo -e "${GREEN}→${NC} Aktiviere UFW..."
        ufw --force enable
        echo -e "${GREEN}✅ UFW aktiviert${NC}"
    else
        echo -e "${YELLOW}⚠️  UFW bleibt inaktiv. Aktiviere später mit: sudo ufw enable${NC}"
    fi
else
    echo -e "${GREEN}✅ UFW ist bereits aktiv${NC}"
fi

# Reload UFW
echo ""
echo -e "${GREEN}→${NC} Lade UFW-Regeln neu..."
ufw reload

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ✅ Firewall-Setup abgeschlossen!                           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}📋 Aktuelle Regeln:${NC}"
ufw status verbose
echo ""

echo -e "${GREEN}💡 Geöffnete Ports:${NC}"
echo "   • Port 22 (TCP)  - SSH"
echo "   • Port 8554 (TCP) - Preview-Stream"
echo "   • Port 8554 (UDP) - RTSP Stream (optional)"
echo ""

echo -e "${GREEN}🎯 Nächste Schritte:${NC}"
echo "   1. Starte Preview-Stream:"
echo "      ./start-preview-stream.sh"
echo ""
echo "   2. Teste Verbindung vom Client-PC:"
echo "      python python-skripte/stream_processor.py --host $(hostname -I | awk '{print $1}')"
echo ""
