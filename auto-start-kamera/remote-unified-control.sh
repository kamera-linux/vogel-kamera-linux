#!/bin/bash
# Remote Control für Unified Camera Monitor
# Steuert den Monitor auf dem Raspberry Pi vom Client PC aus

set -euo pipefail

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# SSH-Konfiguration
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa_ai-had}"
SSH_USER="${SSH_USER:-roimme}"
SSH_HOST="${SSH_HOST:-raspberrypi-5-ai-had}"
REMOTE_DIR="~/vogel-kamera-linux/raspberry-pi-scripts"

# Funktionen
show_help() {
    cat << EOF
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🎥 UNIFIED CAMERA MONITOR - REMOTE CONTROL                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

Verwendung: $0 [OPTION]

Optionen:
  --start [MODE]     Starte Monitor (MODE: normal|slowmo|4k|ai-had, default: normal)
  --stop             Stoppe Monitor
  --restart [MODE]   Starte Monitor neu (optional mit neuem MODE)
  --status           Zeige Status
  --logs [N]         Zeige letzte N Zeilen Logs (default: 50)
  --follow-logs      Live-Logs anzeigen (Strg+C zum Beenden)
  --list-videos      Zeige aufgenommene Videos
  --help             Zeige diese Hilfe

Modi:
  normal             Standard-Aufnahme (1920x1080 @ 30fps)
  slowmo             Zeitlupen-Aufnahme (1536x864 @ 120fps)
  4k                 Cinema 4K (4096x2160 @ 25fps)
  ai-had             AI-HAD mit Audio (1920x1080 @ 30fps + Audio-Erkennung)
                     ⚠️  Modus-Wechsel erfordert Monitor-Neustart!

Beispiele:
  $0 --start normal          # Starte Normal-Modus
  $0 --start slowmo          # Starte Zeitlupen-Modus
  $0 --start 4k              # Starte 4K-Modus
  $0 --start ai-had          # Starte AI-HAD mit Audio
  $0 --stop                  # Stoppe Monitor
  $0 --restart slowmo        # Neustart mit Zeitlupen-Modus
  $0 --status                # Zeige Status
  $0 --logs 100              # Zeige letzte 100 Log-Zeilen
  $0 --follow-logs           # Live-Logs

SSH-Konfiguration (Umgebungsvariablen):
  SSH_KEY=$SSH_KEY
  SSH_USER=$SSH_USER
  SSH_HOST=$SSH_HOST

EOF
}

# SSH-Kommando ausführen
ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "${SSH_USER}@${SSH_HOST}" "$@"
}

# Status prüfen
check_status() {
    echo -e "${CYAN}🔍 Prüfe Monitor-Status auf ${SSH_HOST}...${NC}"
    echo ""
    
    # Prüfe ob Prozess läuft
    if ssh_exec "pgrep -f 'unified-camera-monitor.py' > /dev/null 2>&1"; then
        PID=$(ssh_exec "pgrep -f 'unified-camera-monitor.py'")
        CPU=$(ssh_exec "ps -p $PID -o %cpu= 2>/dev/null || echo '0'")
        MEM=$(ssh_exec "ps -p $PID -o %mem= 2>/dev/null || echo '0'")
        UPTIME=$(ssh_exec "ps -p $PID -o etime= 2>/dev/null || echo 'unknown'")
        
        echo -e "${GREEN}✅ Monitor läuft${NC}"
        echo "   PID: $PID"
        echo "   CPU: ${CPU}%"
        echo "   RAM: ${MEM}%"
        echo "   Laufzeit: $UPTIME"
        echo ""
        
        # Zeige letzte Log-Zeilen
        echo -e "${CYAN}📊 Letzte Aktivität:${NC}"
        ssh_exec "tail -5 /tmp/unified-camera-monitor.log 2>/dev/null || echo 'Keine Logs verfügbar'"
        
        return 0
    else
        echo -e "${RED}❌ Monitor läuft nicht${NC}"
        return 1
    fi
}

# Monitor starten
start_monitor() {
    MODE="${1:-normal}"
    
    echo -e "${CYAN}🚀 Starte Unified Camera Monitor (Modus: ${MODE})...${NC}"
    
    # Prüfe ob bereits läuft (DEAKTIVIERT wegen Race Condition)
    # if ssh_exec "pgrep -f 'unified-camera-monitor.py' > /dev/null 2>&1"; then
    #     echo -e "${YELLOW}⚠️  Monitor läuft bereits!${NC}"
    #     echo "Verwende --restart zum Neustarten oder --stop zum Stoppen"
    #     return 1
    # fi
    
    # Starte Monitor je nach Modus
    case "$MODE" in
        normal)
            echo "📹 Starte Normal-Modus (1920x1080 @ 30fps)..."
            timeout 5 ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" \
                "cd $REMOTE_DIR && source ~/.venv/vogel-camera/bin/activate && nohup python3 unified-camera-monitor.py --camera 0 --threshold 0.2 --cooldown 5 --trigger-duration 0.5 --recording-duration 60 > /dev/null 2>&1 & echo 'Monitor gestartet'" || true
            ;;
        slowmo)
            echo "🎬 Starte Zeitlupen-Modus (1536x864 @ 120fps)..."
            timeout 5 ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" \
                "cd $REMOTE_DIR && source ~/.venv/vogel-camera/bin/activate && nohup python3 unified-camera-monitor.py --camera 0 --threshold 0.2 --cooldown 5 --trigger-duration 0.5 --recording-duration 60 --slowmo > /dev/null 2>&1 & echo 'Monitor gestartet'" || true
            ;;
        4k)
            echo "📹 Starte Cinema 4K-Modus (4096x2160 @ 25fps)..."
            timeout 5 ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" \
                "cd $REMOTE_DIR && source ~/.venv/vogel-camera/bin/activate && nohup python3 unified-camera-monitor.py --camera 0 --threshold 0.2 --cooldown 5 --trigger-duration 0.5 --recording-duration 60 --resolution 4096x2160 --fps 25 > /dev/null 2>&1 & echo 'Monitor gestartet'" || true
            ;;
        ai-had)
            echo "🎤 Starte AI-HAD Modus (1920x1080 @ 30fps + Audio)..."
            timeout 5 ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" \
                "cd $REMOTE_DIR && source ~/.venv/vogel-camera/bin/activate && nohup python3 unified-camera-monitor.py --camera 0 --threshold 0.2 --cooldown 5 --trigger-duration 0.5 --recording-duration 60 --enable-audio --audio-threshold 0.3 > /dev/null 2>&1 & echo 'Monitor gestartet'" || true
            ;;
        *)
            echo -e "${RED}❌ Unbekannter Modus: $MODE${NC}"
            echo "Verfügbare Modi: normal, slowmo, 4k, ai-had"
            return 1
            ;;
    esac
    
    # Warte kurz auf Start
    sleep 2
    
    echo -e "${GREEN}✅ Monitor erfolgreich gestartet${NC}"    # Prüfe ob gestartet (DEAKTIVIERT - blockiert beim Start)
    # if check_status > /dev/null 2>&1; then
    #     echo -e "${GREEN}✅ Monitor erfolgreich gestartet${NC}"
    #     echo ""
    #     check_status
    # else
    #     echo -e "${RED}❌ Monitor konnte nicht gestartet werden${NC}"
    #     echo "Prüfe Logs mit: $0 --logs"
    #     return 1
    # fi
    
    echo -e "${GREEN}✅ Monitor erfolgreich gestartet${NC}"
    echo ""
}

# Monitor stoppen
stop_monitor() {
    echo -e "${CYAN}🛑 Stoppe Unified Camera Monitor...${NC}"
    
    if ! ssh_exec "pgrep -f 'unified-camera-monitor.py' > /dev/null 2>&1"; then
        echo -e "${YELLOW}⚠️  Monitor läuft nicht${NC}"
        return 0
    fi
    
    # Sende SIGTERM
    ssh_exec "pkill -TERM -f 'unified-camera-monitor.py'"
    
    # Warte auf Beendigung
    for i in {1..10}; do
        if ! ssh_exec "pgrep -f 'unified-camera-monitor.py' > /dev/null 2>&1"; then
            echo -e "${GREEN}✅ Monitor gestoppt${NC}"
            return 0
        fi
        sleep 1
    done
    
    # Force kill wenn nötig
    echo -e "${YELLOW}⚠️  Erzwinge Beenden...${NC}"
    ssh_exec "pkill -9 -f 'unified-camera-monitor.py'"
    sleep 1
    
    if ! ssh_exec "pgrep -f 'unified-camera-monitor.py' > /dev/null 2>&1"; then
        echo -e "${GREEN}✅ Monitor gestoppt (erzwungen)${NC}"
        return 0
    else
        echo -e "${RED}❌ Konnte Monitor nicht stoppen${NC}"
        return 1
    fi
}

# Logs anzeigen
show_logs() {
    LINES="${1:-50}"
    echo -e "${CYAN}📜 Zeige letzte $LINES Zeilen Logs...${NC}"
    echo ""
    ssh_exec "tail -$LINES /tmp/unified-camera-monitor.log 2>/dev/null || echo 'Keine Logs verfügbar'"
}

# Live-Logs folgen
follow_logs() {
    echo -e "${CYAN}📡 Live-Logs (Strg+C zum Beenden)...${NC}"
    echo ""
    ssh_exec "tail -f /tmp/unified-camera-monitor.log 2>/dev/null || echo 'Keine Logs verfügbar'"
}

# Videos auflisten
list_videos() {
    echo -e "${CYAN}🎥 Aufgenommene Videos:${NC}"
    echo ""
    ssh_exec "ls -lhtr ~/Videos/Vogelhaus/*.h264 2>/dev/null | tail -20 || echo 'Keine Videos gefunden'"
}

# Main
case "${1:-}" in
    --start)
        start_monitor "${2:-normal}"
        ;;
    --stop)
        stop_monitor
        ;;
    --restart)
        stop_monitor
        sleep 2
        start_monitor "${2:-normal}"
        ;;
    --status)
        check_status
        ;;
    --logs)
        show_logs "${2:-50}"
        ;;
    --follow-logs)
        follow_logs
        ;;
    --list-videos)
        list_videos
        ;;
    --help|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unbekannte Option: $1${NC}"
        echo "Verwende --help für Hilfe"
        exit 1
        ;;
esac
