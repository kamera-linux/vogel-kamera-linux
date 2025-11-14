#!/bin/bash
# Unified Monitoring System - Wrapper für Vogel-Beobachtung
# Startet Remote Monitor + lokale Überwachung + automatische Video-Übertragung

set -euo pipefail

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Konfiguration
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa_ai-had}"
SSH_USER="${SSH_USER:-roimme}"
SSH_HOST="${SSH_HOST:-raspberrypi-5-ai-had}"
REMOTE_DIR="~/vogel-kamera-linux/raspberry-pi-scripts"

# Lokale Pfade
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLIENT_VIDEO_BASE="$HOME/Videos/Vogelhaus"
REMOTE_VIDEO_BASE="/home/roimme/Videos/Vogelhaus"

# Parameter
MODE="${1:-normal}"  # normal oder slowmo
THRESHOLD="0.5"
COOLDOWN="15"
TRIGGER_DURATION="1.0"
STATUS_INTERVAL="300"  # 5 Minuten

# Audio-Erkennung (AI-HAD)
ENABLE_AUDIO="${ENABLE_AUDIO:-false}"
AUDIO_THRESHOLD="0.3"

# PIDs für Cleanup
MONITOR_PID=""
EVENT_LOG_FOLLOWER_PID=""
VIDEO_WATCHER_PID=""
STATUS_REPORTER_PID=""
AUDIO_MONITOR_PID=""

# Cleanup-Funktion
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Beende Unified Monitoring System...${NC}"
    
    # Stoppe lokale Prozesse
    if [ -n "$EVENT_LOG_FOLLOWER_PID" ]; then
        kill $EVENT_LOG_FOLLOWER_PID 2>/dev/null || true
    fi
    if [ -n "$VIDEO_WATCHER_PID" ]; then
        kill $VIDEO_WATCHER_PID 2>/dev/null || true
    fi
    if [ -n "$STATUS_REPORTER_PID" ]; then
        kill $STATUS_REPORTER_PID 2>/dev/null || true
    fi
    if [ -n "$AUDIO_MONITOR_PID" ]; then
        kill $AUDIO_MONITOR_PID 2>/dev/null || true
    fi
    
    # Stoppe Remote Monitor
    echo -e "${CYAN}📡 Stoppe Remote Monitor...${NC}"
    "$SCRIPT_DIR/remote-unified-control.sh" --stop || true
    
    echo -e "${GREEN}✅ Alle Prozesse beendet${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# SSH-Kommando
ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "${SSH_USER}@${SSH_HOST}" "$@"
}

# System-Status mit Ampelsystem
check_system_status() {
    echo ""
    echo "======================================================================"
    echo "📊 SYSTEM-STATUS"
    echo "======================================================================"
    
    # CPU-Last ermitteln (mit Timeout)
    local cpu_load=$(timeout 3 ssh_exec "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\1/' | awk '{print 100 - \$1}'" 2>/dev/null || echo "0")
    local cpu_int=$(printf "%.0f" "$cpu_load" 2>/dev/null || echo "0")
    
    # RAM-Nutzung
    local mem_info=$(timeout 3 ssh_exec "free | grep Mem" 2>/dev/null || echo "")
    if [ -n "$mem_info" ]; then
        local mem_total=$(echo "$mem_info" | awk '{print $2}')
        local mem_used=$(echo "$mem_info" | awk '{print $3}')
        local mem_percent=$(awk "BEGIN {printf \"%.1f\", ($mem_used/$mem_total)*100}" 2>/dev/null || echo "0")
        local mem_percent_int=$(printf "%.0f" "$mem_percent" 2>/dev/null || echo "0")
    else
        local mem_percent="0"
        local mem_percent_int=0
    fi
    
    # CPU-Temperatur
    local cpu_temp=$(timeout 3 ssh_exec "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null" 2>/dev/null || echo "0")
    local cpu_temp_c=$((cpu_temp / 1000))
    
    # Festplatte
    local disk_info=$(timeout 3 ssh_exec "df -h /home | tail -1" 2>/dev/null || echo "")
    if [ -n "$disk_info" ]; then
        local disk_used=$(echo "$disk_info" | awk '{print $5}' | tr -d '%')
        local disk_avail=$(echo "$disk_info" | awk '{print $4}')
    else
        local disk_used=0
        local disk_avail="N/A"
    fi
    
    # Ampel-Logik für CPU
    local cpu_status cpu_color
    if [ $cpu_int -lt 50 ]; then
        cpu_status="🟢"
        cpu_color="${GREEN}"
    elif [ $cpu_int -lt 80 ]; then
        cpu_status="🟡"
        cpu_color="${YELLOW}"
    else
        cpu_status="🔴"
        cpu_color="${RED}"
    fi
    
    # Ampel-Logik für RAM
    local mem_status mem_color
    if [ $mem_percent_int -lt 70 ]; then
        mem_status="🟢"
        mem_color="${GREEN}"
    elif [ $mem_percent_int -lt 85 ]; then
        mem_status="🟡"
        mem_color="${YELLOW}"
    else
        mem_status="🔴"
        mem_color="${RED}"
    fi
    
    # Ampel-Logik für Temperatur
    local temp_status temp_color
    if [ $cpu_temp_c -lt 65 ]; then
        temp_status="🟢"
        temp_color="${GREEN}"
    elif [ $cpu_temp_c -lt 75 ]; then
        temp_status="🟡"
        temp_color="${YELLOW}"
    else
        temp_status="🔴"
        temp_color="${RED}"
    fi
    
    # Ampel-Logik für Festplatte
    local disk_status disk_color
    if [ $disk_used -lt 80 ]; then
        disk_status="🟢"
        disk_color="${GREEN}"
    elif [ $disk_used -lt 90 ]; then
        disk_status="🟡"
        disk_color="${YELLOW}"
    else
        disk_status="🔴"
        disk_color="${RED}"
    fi
    
    # Ausgabe
    echo -e "${cpu_color}${cpu_status} CPU-Last:     ${cpu_load}%${NC}"
    echo -e "${mem_color}${mem_status} RAM-Nutzung:   ${mem_percent}%${NC}"
    echo -e "${temp_color}${temp_status} CPU-Temp:      ${cpu_temp_c}°C${NC}"
    echo -e "${disk_color}${disk_status} Festplatte:    ${disk_used}% belegt (${disk_avail} frei)${NC}"
    echo "======================================================================"
    echo ""
}

# System-Status
get_remote_status() {
    local temp=$(ssh_exec "vcgencmd measure_temp 2>/dev/null | grep -oP '\d+\.\d+' || echo '0'")
    local cpu_load=$(ssh_exec "uptime | awk -F'load average:' '{print \$2}' | awk '{print \$1}' | tr -d ','")
    local disk=$(ssh_exec "df -h /home | tail -1 | awk '{print \$5}'")
    local mem=$(ssh_exec "free -h | grep Mem | awk '{print \$3 \"/\" \$2}'")
    
    echo "🖥️  Remote-Host ($SSH_HOST):"
    echo "   🌡️  CPU-Temp: ${temp}°C"
    echo "   ⚡ CPU-Load: ${cpu_load}"
    echo "   💾 Festplatte: ${disk}"
    echo "   💭 RAM: ${mem}"
}

# Video-Übertragung (OHNE Konvertierung - Pi macht das)
process_video() {
    local remote_video_dir="$1"  # Verzeichnis auf dem Pi
    local dir_name=$(basename "$remote_video_dir")
    
    # Erstelle lokale Ordnerstruktur
    local year=$(echo "$remote_video_dir" | grep -oP '202\d')
    local week=$(echo "$remote_video_dir" | grep -oP '/\d+/' | tr -d '/')
    local mode_dir="Zeitlupe"
    [ "$MODE" = "normal" ] && mode_dir="AI-HAD"
    
    local local_dir="${CLIENT_VIDEO_BASE}/${mode_dir}/${year}/${week}/${dir_name}"
    mkdir -p "$local_dir"
    
    echo -e "${CYAN}📥 Synchronisiere: $dir_name${NC}"
    
    # Kopiere alle MP4-Dateien vom Pi (bereits konvertiert)
    if rsync -avz --progress -e "ssh -i $SSH_KEY" \
        "${SSH_USER}@${SSH_HOST}:${remote_video_dir}/*.mp4" \
        "${local_dir}/" 2>/dev/null; then
        
        local mp4_count=$(ls -1 "${local_dir}"/*.mp4 2>/dev/null | wc -l)
        echo -e "${GREEN}✅ ${mp4_count} Video(s) übertragen: $local_dir${NC}"
        echo ""
    else
        echo -e "${YELLOW}⏳ Konvertierung auf Pi läuft noch... (erneuter Versuch in 10s)${NC}"
    fi
}

# Event-Log-Follower (zeigt wichtige Events in Echtzeit)
follow_event_log() {
    echo -e "${CYAN}📡 Starte Live-Event-Monitor...${NC}"
    
    # Markiere aktuelle Log-Position
    local log_file="/tmp/unified-camera-monitor.log"
    local lines_read=$(ssh_exec "wc -l < $log_file 2>/dev/null || echo 0")
    local recording_active=false
    local recording_start=0
    local recording_duration=60
    
    while true; do
        sleep 2
        
        # Hole neue Log-Zeilen
        local current_lines=$(ssh_exec "wc -l < $log_file 2>/dev/null || echo 0")
        
        if [ -n "$current_lines" ] && [ "$current_lines" -gt "$lines_read" ]; then
            local new_lines=$((current_lines - lines_read))
            
            # Verwende Process Substitution um Subshell zu vermeiden
            while IFS= read -r line; do
                # Filtere wichtige Events
                if echo "$line" | grep -qE "Vogel erkannt|Starte Aufnahme|Aufnahme beendet|Trigger-Bedingungen"; then
                    local timestamp=$(echo "$line" | awk '{print $1, $2}' | cut -d',' -f1)
                    local message=$(echo "$line" | sed 's/^[^-]*- [A-Z]* - //')
                    
                    # Setze Recording-Status
                    if echo "$line" | grep -qE "Starte Aufnahme"; then
                        recording_active=true
                        recording_start=$(date +%s)
                        echo -e "${GREEN}[$timestamp]${NC} $message"
                    elif echo "$line" | grep -qE "Aufnahme beendet"; then
                        recording_active=false
                        echo -e "${GREEN}[$timestamp]${NC} $message"
                    else
                        echo -e "${GREEN}[$timestamp]${NC} $message"
                    fi
                # Zeige Heartbeat nur wenn NICHT aufgenommen wird
                elif echo "$line" | grep -qE "Monitor aktiv.*aktuell aufgenommen"; then
                    if [ "$recording_active" = false ]; then
                        local timestamp=$(echo "$line" | awk '{print $1, $2}' | cut -d',' -f1)
                        local message=$(echo "$line" | sed 's/^[^-]*- [A-Z]* - //')
                        echo -e "${BLUE}[$timestamp]${NC} $message"
                    fi
                # Zeige Status mit Ampeln (kompakt)
                elif echo "$line" | grep -qE "Status:.*Temp:.*🟢|Status:.*Temp:.*🟡|Status:.*Temp:.*🔴"; then
                    local timestamp=$(echo "$line" | awk '{print $1, $2}' | cut -d',' -f1)
                    local message=$(echo "$line" | sed 's/^[^-]*- [A-Z]* - //')
                    echo ""
                    echo -e "${CYAN}[$timestamp]${NC} $message"
                    echo ""
                fi
            done < <(ssh_exec "tail -${new_lines} $log_file")
            
            lines_read=$current_lines
        fi
        
        # Zeige Live-Fortschrittsbalken während der Aufnahme
        if [ "$recording_active" = true ]; then
            local now=$(date +%s)
            local elapsed=$((now - recording_start))
            
            if [ $elapsed -le $recording_duration ]; then
                local percent=$((elapsed * 100 / recording_duration))
                local bar_length=20
                local filled=$((elapsed * bar_length / recording_duration))
                local empty=$((bar_length - filled))
                
                local bar=$(printf '█%.0s' $(seq 1 $filled))$(printf '░%.0s' $(seq 1 $empty))
                
                printf "\r${CYAN}🎥 Aufnahme läuft... ${bar} ${percent}%% (${elapsed}/${recording_duration}s)${NC}" >&2
            else
                recording_active=false
                echo "" >&2
            fi
        fi
    done
}

# Video-Watcher (läuft im Hintergrund)
watch_for_videos() {
    local last_check=0
    
    while true; do
        sleep 10
        
        # Hole Liste neuer Videos
        local videos=$(ssh_exec "find ${REMOTE_VIDEO_BASE} -name '*.h264' -newer /tmp/last_video_check 2>/dev/null || true")
        
        if [ -n "$videos" ]; then
            while IFS= read -r video; do
                [ -z "$video" ] && continue
                process_video "$video"
            done <<< "$videos"
            
            # Update Timestamp
            ssh_exec "touch /tmp/last_video_check"
        fi
    done
}

# Status-Reporter (deaktiviert - Monitor gibt eigenen Status aus)
status_reporter() {
    # Monitor gibt alle 5 Minuten eigenen Status-Report mit Ampeln aus
    # Dieser Wrapper-Status ist nicht mehr nötig
    while true; do
        sleep 3600  # Stündlich aufwachen aber nichts tun
    done
}

# Audio-Monitor (AI-HAD)
audio_monitor() {
    echo -e "${MAGENTA}🎤 Starte Audio-Monitoring (AI-HAD)...${NC}"
    
    # Hier würde die AI-HAD Integration kommen
    # Beispiel: SSH-Tunnel für Audio-Stream oder lokale Analyse
    
    while true; do
        # Prüfe Audio-Events auf Pi
        local audio_events=$(ssh_exec "tail -1 /tmp/audio-events.log 2>/dev/null || echo ''")
        
        if [ -n "$audio_events" ]; then
            echo -e "${MAGENTA}🔊 Audio-Event: $audio_events${NC}"
            # Hier könnte man zusätzliche Aktionen triggern
        fi
        
        sleep 5
    done
}

# Banner
echo ""
echo "======================================================================"
echo "🎥 UNIFIED MONITORING SYSTEM - Vogel-Beobachtung"
echo "======================================================================"
echo ""

# Modus-Info
if [ "$MODE" = "slowmo" ]; then
    echo -e "${CYAN}🎬 Modus: Zeitlupe (1536x864 @ 120fps)${NC}"
else
    echo -e "${CYAN}📹 Modus: Normal (1920x1080 @ 30fps)${NC}"
fi
echo ""

# System-Check
echo -e "${CYAN}🔍 System-Check...${NC}"
echo ""

# Prüfe SSH-Verbindung
echo -n "📡 SSH-Verbindung zu $SSH_HOST... "
if ssh_exec "echo 'OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo -e "${RED}FEHLER: Keine SSH-Verbindung!${NC}"
    exit 1
fi

# Prüfe Scripts
echo -n "📄 Remote Scripts... "
if ssh_exec "[ -f ${REMOTE_DIR}/unified-camera-monitor.py ]"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo -e "${RED}FEHLER: Scripts fehlen auf Pi!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ System-Check erfolgreich${NC}"
echo ""

# Initialisiere Video-Timestamp
ssh_exec "touch /tmp/last_video_check"

# Starte Remote Monitor
echo -e "${CYAN}🚀 Starte Remote Monitor...${NC}"
if "$SCRIPT_DIR/remote-unified-control.sh" --start "$MODE"; then
    echo -e "${GREEN}✅ Remote Monitor gestartet${NC}"
else
    echo -e "${RED}❌ Konnte Monitor nicht starten${NC}"
    exit 1
fi

sleep 2

# Zeige initialen System-Status (DEAKTIVIERT - hängt beim Start)
# check_system_status

# Starte lokale Dienste
echo -e "${CYAN}📊 Starte lokale Monitoring-Dienste...${NC}"
echo ""

# Event-Log-Follower (zeigt wichtige Events in Echtzeit)
follow_event_log &
EVENT_LOG_FOLLOWER_PID=$!
echo -e "${GREEN}✅ Event-Monitor gestartet (PID: $EVENT_LOG_FOLLOWER_PID)${NC}"

# Video-Watcher
watch_for_videos &
VIDEO_WATCHER_PID=$!
echo -e "${GREEN}✅ Video-Watcher gestartet (PID: $VIDEO_WATCHER_PID)${NC}"

# Status-Reporter
status_reporter &
STATUS_REPORTER_PID=$!
echo -e "${GREEN}✅ Status-Reporter gestartet (PID: $STATUS_REPORTER_PID)${NC}"

# Audio-Monitor (optional)
if [ "$ENABLE_AUDIO" = "true" ]; then
    audio_monitor &
    AUDIO_MONITOR_PID=$!
    echo -e "${GREEN}✅ Audio-Monitor gestartet (PID: $AUDIO_MONITOR_PID)${NC}"
fi

echo ""
echo "======================================================================"
echo "✅ SYSTEM BEREIT - Alle Komponenten gestartet"
echo "======================================================================"
echo ""

# Warte kurz damit Monitor initialisiert ist
sleep 3

# Zeige initialen Status vom Monitor
echo "======================================================================"
echo "📊 INITIALER STATUS-REPORT"
echo "======================================================================"
ssh_exec "tail -20 /tmp/unified-camera-monitor.log 2>/dev/null | grep -E '(Laufzeit|Aufnahmen|Frames|FPS|Festplatte|Überwache)' | tail -5" || echo "Monitor startet noch..."
echo "======================================================================"
echo ""

echo "======================================================================"
echo "🔍 Live-Logs vom Remote Monitor"
echo "======================================================================"
echo ""

# Folge Remote-Logs (Hauptprozess)
ssh_exec "tail -f /tmp/unified-camera-monitor.log 2>/dev/null" &
LOG_FOLLOWER_PID=$!

# Warte auf Beendigung
wait $LOG_FOLLOWER_PID
