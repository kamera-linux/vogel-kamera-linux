#!/bin/bash
# =============================================================================
# Geführter Test: Auto-Trigger System
# =============================================================================
# Schritt-für-Schritt-Anleitung mit Prüfungen
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

clear

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🐦 VOGEL-KAMERA AUTO-TRIGGER - GEFÜHRTER TEST 🎥               ║
║                                                                  ║
║   Ich führe dich jetzt Schritt für Schritt durch den Test!      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo -e "${CYAN}Dieser Test dauert ca. 5 Minuten und besteht aus:${NC}"
echo ""
echo "  1️⃣  Preview-Stream auf Raspberry Pi starten"
echo "  2️⃣  Stream-Verbindung testen (10 Sekunden)"
echo "  3️⃣  AI-Erkennung testen"
echo "  4️⃣  Auto-Trigger im Echtbetrieb testen (30 Sekunden)"
echo "  5️⃣  Ergebnisse auswerten"
echo ""
read -p "$(echo -e ${GREEN}Bereit? Drücke ENTER zum Starten...${NC})" -r
echo ""

# =============================================================================
# Schritt 1: Preview-Stream starten
# =============================================================================

clear
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}  SCHRITT 1/5: Preview-Stream auf Raspberry Pi starten${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Der Preview-Stream liefert die Video-Frames für die AI-Erkennung.${NC}"
echo ""

# Prüfe ob Stream-Skript auf Raspberry Pi existiert
echo -e "${BLUE}� Prüfe ob Stream-Skript auf Raspberry Pi existiert...${NC}"
if ! ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had '[ -f ~/start-rtsp-stream.sh ]' 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Stream-Skript nicht gefunden, kopiere es jetzt...${NC}"
    
    if [ -f "raspberry-pi-scripts/start-rtsp-stream.sh" ]; then
        if scp -i ~/.ssh/id_rsa_ai-had raspberry-pi-scripts/start-rtsp-stream.sh roimme@raspberrypi-5-ai-had:~/; then
            echo -e "${GREEN}✅ Stream-Skript erfolgreich kopiert!${NC}"
        else
            echo -e "${RED}❌ Fehler beim Kopieren des Skripts!${NC}"
            echo ""
            echo "Bitte kopiere es manuell:"
            echo -e "${GREEN}scp -i ~/.ssh/id_rsa_ai-had raspberry-pi-scripts/start-rtsp-stream.sh roimme@raspberrypi-5-ai-had:~/${NC}"
            echo ""
            read -p "Drücke ENTER wenn kopiert..." -r
        fi
    else
        echo -e "${RED}❌ Lokale Datei 'raspberry-pi-scripts/start-rtsp-stream.sh' nicht gefunden!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Stream-Skript existiert bereits auf Raspberry Pi${NC}"
fi

# Räume alte Prozesse auf
echo ""
echo -e "${BLUE}🧹 Räume alte Stream-Prozesse auf...${NC}"
if ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had 'pkill -f rpicam-vid 2>/dev/null; pkill -f stream-wrapper 2>/dev/null; rm -f /tmp/*.pid 2>/dev/null; echo "OK"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Alte Prozesse aufgeräumt${NC}"
else
    echo -e "${YELLOW}⚠️  Konnte alte Prozesse nicht aufräumen (evtl. laufen keine)${NC}"
fi

echo ""
echo -e "${CYAN}📋 ANLEITUNG:${NC}"
echo ""
echo "1. Öffne ein NEUES Terminal-Fenster"
echo ""
echo "2. Führe folgende Befehle aus:"
echo ""
echo -e "${GREEN}   ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had${NC}"
echo -e "${GREEN}   ./start-rtsp-stream.sh${NC}"
echo ""
echo "3. Du solltest diese Ausgabe sehen:"
echo ""
echo -e "   ${GREEN}✅ RTSP-Stream gestartet (PID: xxxxx)${NC}"
echo -e "   ${GREEN}ℹ️  Stream-URL: tcp://192.168.178.59:8554${NC}"
echo -e "   ${GREEN}ℹ️  Auto-Restart aktiviert${NC}"
echo ""
echo "4. WICHTIG: Lass dieses Terminal-Fenster OFFEN!"
echo "   Der Stream muss die ganze Zeit laufen."
echo ""
read -p "$(echo -e ${CYAN}Läuft der Stream? Drücke ENTER wenn ja...${NC})" -r
echo ""

# Prüfe ob Stream erreichbar ist
echo -e "${BLUE}🔍 Prüfe Stream-Verbindung...${NC}"
sleep 2

if timeout 5 bash -c "python3 << 'PYEOF'
import socket
import sys
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
try:
    sock.connect(('raspberrypi-5-ai-had', 8554))
    print('OK')
    sys.exit(0)
except:
    sys.exit(1)
PYEOF" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Stream-Port 8554 ist erreichbar!${NC}"
else
    echo -e "${RED}❌ Kann Port 8554 nicht erreichen!${NC}"
    echo ""
    echo "Mögliche Probleme:"
    echo "  • Stream läuft nicht auf dem Raspberry Pi"
    echo "  • Firewall blockiert Port 8554"
    echo "  • Netzwerk-Probleme"
    echo ""
    read -p "Trotzdem fortfahren? (j/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        echo "Test abgebrochen."
        exit 1
    fi
fi

echo ""
read -p "$(echo -e ${GREEN}Weiter zu Schritt 2? Drücke ENTER...${NC})" -r

# =============================================================================
# Schritt 2: Stream-Test
# =============================================================================

clear
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}  SCHRITT 2/5: Stream-Verbindung testen (10 Sekunden)${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Jetzt teste ich ob der Stream funktioniert und Frames empfangen werden.${NC}"
echo ""
echo -e "${CYAN}Das YOLOv8-Model wird beim ersten Mal heruntergeladen (~6 MB).${NC}"
echo ""
echo -e "${GREEN}Starte Stream-Test...${NC}"
echo ""

if ./run-stream-test.sh --duration 10; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Stream-Test ERFOLGREICH!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Schau dir die Statistiken an:"
    echo "  • Wie viele Frames wurden verarbeitet?"
    echo "  • Wurden Vögel erkannt?"
    echo "  • Wie lange dauert die Inferenz?"
    echo ""
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Stream-Test FEHLGESCHLAGEN!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Mögliche Probleme:"
    echo "  • Stream auf Raspberry Pi gestorben"
    echo "  • GStreamer nicht installiert"
    echo "  • Netzwerk-Unterbrechung"
    echo ""
    read -p "Möchtest du trotzdem fortfahren? (j/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        echo "Test abgebrochen."
        exit 1
    fi
fi

echo ""
read -p "$(echo -e ${GREEN}Weiter zu Schritt 3? Drücke ENTER...${NC})" -r

# =============================================================================
# Schritt 3: AI-Erkennungs-Test
# =============================================================================

clear
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}  SCHRITT 3/5: AI-Erkennung testen${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}🎯 Jetzt testen wir ob die AI Objekte erkennt!${NC}"
echo ""
echo -e "${CYAN}📋 ANLEITUNG:${NC}"
echo ""
echo "1. Halte etwas vor die Kamera, z.B.:"
echo "   • Deine Hand"
echo "   • Ein Spielzeug"
echo "   • Ein Bild von einem Vogel"
echo ""
echo "2. Der Test läuft 15 Sekunden"
echo "3. Beobachte die Ausgabe:"
echo "   • Wird etwas erkannt?"
echo "   • Als welche Klasse wird es erkannt?"
echo ""
read -p "$(echo -e ${CYAN}Bereit? Drücke ENTER zum Starten...${NC})" -r
echo ""

echo -e "${GREEN}Starte 15-Sekunden Erkennungs-Test...${NC}"
echo -e "${YELLOW}(Halte jetzt etwas vor die Kamera!)${NC}"
echo ""

./run-stream-test.sh --duration 15

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}💡 ANALYSE:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Wurden Vögel erkannt? Schaue auf '🐦 Vogel erkannt!' Meldungen"
echo ""
echo "WICHTIG zu wissen:"
echo "  • YOLOv8 wurde auf COCO-Dataset trainiert"
echo "  • Es erkennt 80 verschiedene Klassen"
echo "  • 'bird' ist Klasse 14"
echo "  • Manchmal wird auch anderes als Vogel erkannt (false positives)"
echo ""
echo "Threshold anpassen:"
echo "  • Standard: 0.45 (balanciert)"
echo "  • Weniger false positives: 0.55 oder höher"
echo "  • Mehr Erkennungen: 0.35"
echo ""
read -p "$(echo -e ${GREEN}Verstanden? Weiter zu Schritt 4...${NC})" -r

# =============================================================================
# Schritt 4: Auto-Trigger-Test
# =============================================================================

clear
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}  SCHRITT 4/5: Auto-Trigger im Echtbetrieb (30 Sekunden)${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}🚀 Jetzt läuft das komplette Auto-Trigger-System!${NC}"
echo ""
echo -e "${CYAN}Was passiert:${NC}"
echo ""
echo "  1. System überwacht den Stream kontinuierlich"
echo "  2. Bei Vogel-Erkennung → automatischer Trigger"
echo "  3. HD-Aufnahme wird gestartet (1 Minute)"
echo "  4. Cooldown von 10 Sekunden nach Aufnahme"
echo "  5. Status-Report wird ausgegeben"
echo ""
echo -e "${CYAN}Test-Einstellungen:${NC}"
echo "  • Laufzeit: 30 Sekunden"
echo "  • Trigger-Dauer: 1 Minute (bei Erkennung)"
echo "  • Cooldown: 10 Sekunden"
echo "  • AI-Model: bird-species (nur Vögel)"
echo "  • Threshold: 0.45"
echo ""
echo -e "${YELLOW}Tipp: Halte wieder etwas vor die Kamera um einen Trigger auszulösen!${NC}"
echo ""
read -p "$(echo -e ${GREEN}Bereit? Drücke ENTER zum Starten...${NC})" -r
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🐦 AUTO-TRIGGER STARTET...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

timeout 30 ./run-auto-trigger.sh \
    --trigger-duration 1 \
    --ai-model bird-species \
    --cooldown 10 \
    --status-interval 1 || true

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Auto-Trigger-Test abgeschlossen!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
read -p "$(echo -e ${GREEN}Weiter zu den Ergebnissen...${NC})" -r

# =============================================================================
# Schritt 5: Ergebnisse
# =============================================================================

clear
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}  SCHRITT 5/5: Ergebnisse & Auswertung${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
cat << 'EOF'
  ____  _____ ____  _____ _   _    ___
 |  _ \|  ___|  _ \|  ___| | | |  / _ \
 | |_) | |_  | |_) | |_  | | | | | | | |
 |  __/|  _| |  _ <|  _| | |_| | | |_| |
 |_|   |_|   |_| \_\_|    \___/   \___/

EOF

echo -e "${GREEN}✅ Glückwunsch! Du hast den kompletten Test durchgeführt!${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📊 ZUSAMMENFASSUNG:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Was funktioniert:"
echo "  ✅ Preview-Stream auf Raspberry Pi"
echo "  ✅ Stream-Verbindung über Netzwerk"
echo "  ✅ YOLOv8 AI-Erkennung"
echo "  ✅ Auto-Trigger-System"
echo "  ✅ Ressourcen-Monitoring"
echo "  ✅ Status-Reports"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🎯 NÄCHSTE SCHRITTE:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1️⃣  Produktiv-Betrieb starten:"
echo ""
echo "   Terminal 1 (Raspberry Pi):"
echo -e "   ${GREEN}ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had${NC}"
echo -e "   ${GREEN}./start-rtsp-stream.sh${NC}"
echo ""
echo "   Terminal 2 (Client-PC):"
echo -e "   ${GREEN}./run-auto-trigger.sh --trigger-duration 2${NC}"
echo ""
echo "2️⃣  Threshold anpassen (falls zu viele false positives):"
echo -e "   ${GREEN}./run-auto-trigger.sh --trigger-threshold 0.55${NC}"
echo ""
echo "3️⃣  Aufnahmen finden:"
echo "   Die Videos werden auf dem Raspberry Pi gespeichert:"
echo -e "   ${GREEN}/home/roimme/Videos/${NC}"
echo ""
echo "4️⃣  Als Service einrichten (24/7-Betrieb):"
echo -e "   ${GREEN}Siehe: docs/PREVIEW-STREAM-SETUP.md${NC}"
echo ""
echo "5️⃣  Logs anschauen:"
echo "   Stream-Log (Raspberry Pi):"
echo -e "   ${GREEN}ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had${NC}"
echo -e "   ${GREEN}tail -f /tmp/rtsp-stream.log${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}💡 TIPPS:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "• Stream läuft? Prüfe mit:"
echo -e "  ${BLUE}ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had './start-rtsp-stream.sh --status'${NC}"
echo ""
echo "• Stream neu starten:"
echo -e "  ${BLUE}ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had './start-rtsp-stream.sh --stop && ./start-rtsp-stream.sh'${NC}"
echo ""
echo "• Schnell-Test (nur Stream, ohne Trigger):"
echo -e "  ${BLUE}./run-stream-test.sh --duration 10${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🐦 Viel Erfolg beim Vogel-Filming! 🎥${NC}"
echo ""
echo -e "${YELLOW}Bei Fragen siehe Dokumentation in docs/ oder erstelle ein GitHub Issue.${NC}"
echo ""
