#!/bin/bash
# AI-HAD Audio Monitor für Unified System
# Überwacht Audio-Events und loggt diese für Remote-Zugriff

set -euo pipefail

# Konfiguration
AUDIO_DEVICE="${AUDIO_DEVICE:-plughw:5,0}"  # AI-HAD USB Audio
SAMPLE_RATE="48000"
THRESHOLD="${THRESHOLD:-0.3}"
LOG_FILE="/tmp/audio-events.log"
AUDIO_DIR="$HOME/Audio/Vogelhaus"

# Erstelle Verzeichnisse
mkdir -p "$AUDIO_DIR"

# Banner
echo "🎤 AI-HAD Audio Monitor"
echo "   Device: $AUDIO_DEVICE"
echo "   Sample Rate: $SAMPLE_RATE Hz"
echo "   Threshold: $THRESHOLD"
echo ""

# Audio-Level-Monitor mit arecord
monitor_audio() {
    while true; do
        # Nimm 1 Sekunde Audio auf und analysiere Level
        local level=$(arecord -D "$AUDIO_DEVICE" -f S16_LE -r "$SAMPLE_RATE" -d 1 2>/dev/null | \
            od -An -t d2 | \
            awk '{for(i=1;i<=NF;i++)s+=(($i<0)?-$i:$i)}END{print s/NR}')
        
        # Normalisiere auf 0-1 Range (grob)
        local normalized=$(echo "scale=3; $level / 32768" | bc)
        
        # Wenn über Threshold: Event loggen
        if (( $(echo "$normalized > $THRESHOLD" | bc -l) )); then
            local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            local event="$timestamp - Audio-Level: $normalized (Threshold: $THRESHOLD)"
            
            echo "$event"
            echo "$event" >> "$LOG_FILE"
            
            # Optional: Kurze Aufnahme speichern
            local filename="audio_${timestamp//[: -]/_}.wav"
            timeout 5 arecord -D "$AUDIO_DEVICE" -f S16_LE -r "$SAMPLE_RATE" \
                "$AUDIO_DIR/$filename" 2>/dev/null &
        fi
        
        sleep 0.1
    done
}

# Starte Monitoring
echo "🔍 Starte Audio-Monitoring..."
monitor_audio
