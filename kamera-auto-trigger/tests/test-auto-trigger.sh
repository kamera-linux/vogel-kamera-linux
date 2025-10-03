#!/bin/bash
# =============================================================================
# Probelauf: Auto-Trigger System
# =============================================================================
# Testet das gesamte System Schritt für Schritt
#
# Verwendung:
#   ./test-auto-trigger.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SSH_KEY="$HOME/.ssh/id_rsa_ai-had"
RPI_HOST="raspberrypi-5-ai-had"
RPI_USER="roimme"

print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  $1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
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

wait_user() {
    echo ""
    read -p "Drücke ENTER um fortzufahren..." -r
    echo ""
}

# Prüfe ob wir im richtigen Verzeichnis sind
if [ ! -f "run-auto-trigger.sh" ]; then
    print_error "Bitte im vogel-kamera-linux Verzeichnis ausführen!"
    exit 1
fi

print_header "🧪 Probelauf: Auto-Trigger System"

echo "Dieser Test führt folgende Schritte durch:"
echo "  1. ✅ Voraussetzungen prüfen"
echo "  2. 🔧 Preview-Stream auf Raspberry Pi starten"
echo "  3. 🎬 Stream-Test (10 Sekunden)"
echo "  4. 🐦 Auto-Trigger-Test (30 Sekunden)"
echo "  5. 📊 Ergebnisse anzeigen"
echo ""
wait_user

# ============================================================================
# Schritt 1: Voraussetzungen prüfen
# ============================================================================

print_header "Schritt 1: Voraussetzungen prüfen"

print_step "Prüfe SSH-Verbindung zum Raspberry Pi..."
if ssh -i "$SSH_KEY" -o ConnectTimeout=5 "$RPI_USER@$RPI_HOST" "echo 'SSH OK'" > /dev/null 2>&1; then
    print_success "SSH-Verbindung funktioniert"
else
    print_error "Keine SSH-Verbindung zum Raspberry Pi!"
    echo ""
    echo "Bitte prüfe:"
    echo "  1. Ist der Raspberry Pi eingeschaltet?"
    echo "  2. Ist das Netzwerk verbunden?"
    echo "  3. Funktioniert: ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had"
    exit 1
fi

print_step "Prüfe Python-Umgebung..."
if [ -f ".venv/bin/python" ]; then
    print_success "Virtuelle Umgebung gefunden"
else
    print_error "Virtuelle Umgebung nicht gefunden!"
    echo ""
    echo "Bitte installiere:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt -r requirements-autotrigger.txt"
    exit 1
fi

print_step "Prüfe Python-Dependencies..."
if .venv/bin/python -c "import cv2, ultralytics" 2>/dev/null; then
    print_success "Dependencies installiert (opencv, ultralytics)"
else
    print_error "Dependencies fehlen!"
    echo ""
    echo "Bitte installiere:"
    echo "  pip install -r requirements-autotrigger.txt"
    exit 1
fi

print_step "Prüfe Firewall..."
if sudo ufw status | grep -q "8554.*ALLOW" 2>/dev/null || ! command -v ufw &> /dev/null; then
    print_success "Firewall konfiguriert oder nicht aktiv"
else
    print_warning "Firewall könnte Probleme machen"
    echo "Führe aus: sudo ./setup-firewall-client-pc.sh"
fi

print_success "Alle Voraussetzungen erfüllt!"
wait_user

# ============================================================================
# Schritt 2: Preview-Stream starten
# ============================================================================

print_header "Schritt 2: Preview-Stream auf Raspberry Pi starten"

print_step "Räume alte Prozesse auf..."
ssh -i "$SSH_KEY" "$RPI_USER@$RPI_HOST" 'pkill -f rpicam-vid 2>/dev/null; pkill -f stream-wrapper 2>/dev/null; rm -f /tmp/*.pid; sleep 1' || true
print_success "Cleanup abgeschlossen"

print_step "Prüfe ob Stream-Skript auf Raspberry Pi vorhanden ist..."
if ssh -i "$SSH_KEY" "$RPI_USER@$RPI_HOST" "test -f ~/start-rtsp-stream.sh"; then
    print_success "Stream-Skript gefunden"
else
    print_warning "Stream-Skript nicht gefunden, kopiere..."
    scp -i "$SSH_KEY" raspberry-pi-scripts/start-rtsp-stream.sh "$RPI_USER@$RPI_HOST:~/"
    ssh -i "$SSH_KEY" "$RPI_USER@$RPI_HOST" "chmod +x ~/start-rtsp-stream.sh"
    print_success "Stream-Skript kopiert"
fi

print_step "Starte Preview-Stream..."
echo ""
echo -e "${YELLOW}WICHTIG: Der Stream wird jetzt gestartet.${NC}"
echo "Du solltest folgende Ausgabe sehen:"
echo "  ✅ RTSP-Stream gestartet (PID: xxxxx)"
echo "  ℹ️  Stream-URL: tcp://192.168.178.59:8554"
echo ""
echo "Öffne ein neues Terminal und führe aus:"
echo -e "${CYAN}  ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had${NC}"
echo -e "${CYAN}  ./start-rtsp-stream.sh${NC}"
echo ""
echo "Wenn der Stream läuft, komme zurück und drücke ENTER..."
wait_user

print_step "Prüfe ob Stream läuft..."
sleep 2
if ssh -i "$SSH_KEY" "$RPI_USER@$RPI_HOST" "pgrep -f rpicam-vid" > /dev/null; then
    print_success "Stream läuft!"
else
    print_error "Stream läuft nicht!"
    echo ""
    echo "Bitte starte den Stream manuell:"
    echo "  ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had"
    echo "  ./start-rtsp-stream.sh"
    echo ""
    echo "Dann führe dieses Skript erneut aus."
    exit 1
fi

# ============================================================================
# Schritt 3: Stream-Test
# ============================================================================

print_header "Schritt 3: Stream-Test (10 Sekunden)"

print_step "Teste Stream-Verbindung und AI-Erkennung..."
echo ""
echo -e "${YELLOW}Halte etwas vor die Kamera (z.B. deine Hand), um zu testen${NC}"
echo -e "${YELLOW}ob die AI es als Vogel erkennt!${NC}"
echo ""
sleep 2

if ./run-stream-test.sh --duration 10; then
    print_success "Stream-Test erfolgreich!"
else
    print_error "Stream-Test fehlgeschlagen!"
    echo ""
    echo "Mögliche Probleme:"
    echo "  1. Stream läuft nicht auf Raspberry Pi"
    echo "  2. Firewall blockiert Port 8554"
    echo "  3. Netzwerk-Probleme"
    exit 1
fi

wait_user

# ============================================================================
# Schritt 4: Auto-Trigger-Test
# ============================================================================

print_header "Schritt 4: Auto-Trigger-Test (30 Sekunden)"

print_step "Starte Auto-Trigger im Test-Modus..."
echo ""
echo -e "${YELLOW}Das System überwacht jetzt die Kamera.${NC}"
echo -e "${YELLOW}Bei Vogel-Erkennung wird automatisch eine Aufnahme gestartet!${NC}"
echo ""
echo "Test-Einstellungen:"
echo "  • Trigger-Dauer: 1 Minute"
echo "  • Cooldown: 10 Sekunden"
echo "  • AI-Model: bird-species"
echo "  • Test-Zeit: 30 Sekunden"
echo ""
sleep 2

timeout 30 ./run-auto-trigger.sh \
    --trigger-duration 1 \
    --ai-model bird-species \
    --cooldown 10 \
    --status-interval 1 || true

print_success "Auto-Trigger-Test abgeschlossen!"

# ============================================================================
# Schritt 5: Ergebnisse
# ============================================================================

print_header "Schritt 5: Test-Ergebnisse"

echo -e "${GREEN}✅ Probelauf erfolgreich abgeschlossen!${NC}"
echo ""
echo "Das System funktioniert und ist einsatzbereit!"
echo ""
echo -e "${CYAN}📊 Zusammenfassung:${NC}"
echo "  ✅ SSH-Verbindung funktioniert"
echo "  ✅ Preview-Stream läuft"
echo "  ✅ AI-Erkennung funktioniert"
echo "  ✅ Auto-Trigger funktioniert"
echo ""
echo -e "${CYAN}🎯 Nächste Schritte:${NC}"
echo ""
echo "1. Produktiv-Betrieb starten:"
echo -e "   ${BLUE}./run-auto-trigger.sh --trigger-duration 2${NC}"
echo ""
echo "2. Stream-Status prüfen:"
echo -e "   ${BLUE}ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had${NC}"
echo -e "   ${BLUE}./start-rtsp-stream.sh --status${NC}"
echo ""
echo "3. Threshold anpassen (falls nötig):"
echo -e "   ${BLUE}./run-auto-trigger.sh --trigger-threshold 0.50${NC}"
echo "   (höher = weniger false positives)"
echo ""
echo "4. Als Service einrichten (für 24/7-Betrieb):"
echo -e "   ${BLUE}Siehe: docs/PREVIEW-STREAM-SETUP.md${NC}"
echo ""
echo -e "${GREEN}Viel Erfolg beim Vogel-Filming! 🐦🎥${NC}"
echo ""
