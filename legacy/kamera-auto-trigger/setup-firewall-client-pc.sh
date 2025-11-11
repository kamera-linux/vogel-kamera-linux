#!/bin/bash
# =============================================================================
# Firewall-Setup für Client-PC
# =============================================================================
# Konfiguriert UFW auf dem Client-PC für das Vogel-Kamera-System
#
# Verwendung:
#   sudo ./setup-firewall-client-pc.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🔥 Firewall-Setup für Client-PC (Vogel-Kamera)            ║${NC}"
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

# Port 22 (SSH) - Falls SSH-Server läuft
echo -e "${GREEN}→${NC} Erlaube SSH (Port 22) - falls SSH-Server läuft..."
ufw allow 22/tcp comment 'SSH'

# Ausgehende Verbindungen zum Raspberry Pi
echo -e "${GREEN}→${NC} Erlaube ausgehende Verbindungen (TCP Port 8554)..."
# UFW erlaubt standardmäßig ausgehende Verbindungen
echo "   (Ausgehende Verbindungen sind standardmäßig erlaubt)"

# Optional: Spezifische IP des Raspberry Pi erlauben
echo ""
read -p "Möchtest du nur Verbindungen von/zu einer spezifischen IP erlauben? (j/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    echo ""
    read -p "Raspberry Pi IP-Adresse (z.B. 192.168.178.59): " RPI_IP
    
    if [ -n "$RPI_IP" ]; then
        echo -e "${GREEN}→${NC} Erlaube Verbindungen von/zu $RPI_IP..."
        ufw allow from "$RPI_IP" comment "Raspberry Pi Vogel-Kamera"
        ufw allow to "$RPI_IP" comment "Zum Raspberry Pi"
        echo -e "${GREEN}✅ IP-spezifische Regeln hinzugefügt${NC}"
    fi
fi

# Aktiviere UFW falls noch nicht aktiv
echo ""
if ufw status | grep -q "Status: inactive"; then
    echo -e "${YELLOW}⚠️  UFW ist inaktiv!${NC}"
    read -p "UFW jetzt aktivieren? (j/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        echo -e "${GREEN}→${NC} Aktiviere UFW..."
        # Erlaube ausgehende, blockiere eingehende (Standard)
        ufw default deny incoming
        ufw default allow outgoing
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

echo -e "${GREEN}💡 Konfiguration:${NC}"
echo "   • SSH erlaubt (Port 22)"
echo "   • Ausgehende Verbindungen erlaubt (Standard)"
echo "   • Verbindungen zum Raspberry Pi erlaubt"
echo ""

echo -e "${GREEN}🎯 Nächste Schritte:${NC}"
echo "   1. Konfiguriere Firewall auf Raspberry Pi:"
echo "      scp setup-firewall-raspberry-pi.sh roimme@raspberrypi-5-ai-had:~/"
echo "      ssh roimme@raspberrypi-5-ai-had 'sudo bash ~/setup-firewall-raspberry-pi.sh'"
echo ""
echo "   2. Teste Verbindung:"
echo "      python python-skripte/stream_processor.py --host raspberrypi-5-ai-had"
echo ""
