#!/bin/bash
# Setup-Script für Unified Camera Monitor
# Installiert alle Abhängigkeiten auf dem Raspberry Pi

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║   🔧 Unified Camera Monitor - Setup                         ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    print_error "Dieses Script sollte auf einem Raspberry Pi ausgeführt werden"
    exit 1
fi

print_info "Raspberry Pi Model:"
cat /proc/device-tree/model
echo ""

# 1. System-Packages installieren
print_info "Installiere System-Packages..."
sudo apt update
sudo apt install -y python3-full python3-venv python3-picamera2

print_success "System-Packages installiert"
echo ""

# 2. Erstelle virtuelle Umgebung
VENV_DIR="$HOME/.venv/vogel-camera"

if [ -d "$VENV_DIR" ]; then
    print_info "Virtuelle Umgebung existiert bereits: $VENV_DIR"
    read -p "Neu erstellen? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -rf "$VENV_DIR"
        print_info "Alte Umgebung gelöscht"
    else
        print_info "Überspringe Erstellung"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    print_info "Erstelle virtuelle Umgebung: $VENV_DIR"
    python3 -m venv "$VENV_DIR" --system-site-packages
    print_success "Virtuelle Umgebung erstellt"
fi
echo ""

# 3. Aktiviere venv und installiere Python-Packages
print_info "Installiere Python-Packages in virtueller Umgebung..."
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install ultralytics opencv-python numpy

print_success "Python-Packages installiert"
echo ""

# 4. Teste Installation
print_info "Teste Installation..."

if python3 -c "import picamera2" 2>/dev/null; then
    print_success "picamera2 verfügbar"
else
    print_error "picamera2 nicht verfügbar"
fi

if python3 -c "import ultralytics" 2>/dev/null; then
    print_success "ultralytics verfügbar"
else
    print_error "ultralytics nicht verfügbar"
fi

if python3 -c "import cv2" 2>/dev/null; then
    print_success "opencv-python verfügbar"
else
    print_error "opencv-python nicht verfügbar"
fi

echo ""

# 5. Erstelle Video-Verzeichnis
VIDEO_DIR="$HOME/Videos/Vogelhaus"
mkdir -p "$VIDEO_DIR"
print_success "Video-Verzeichnis erstellt: $VIDEO_DIR"
echo ""

# 6. Zusammenfassung
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║   ✅ Setup abgeschlossen!                                    ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
print_info "Virtuelle Umgebung: $VENV_DIR"
print_info "Video-Verzeichnis: $VIDEO_DIR"
echo ""
print_info "Starte den Monitor mit:"
echo "  cd ~/vogel-kamera-linux/raspberry-pi-scripts"
echo "  ./start-unified-monitor.sh"
echo ""
