#!/bin/bash
# get_pi_status.sh - Ruft Pi System-Status ab (CPU Load, RAM, Disk, Temp)
# Output: load_avg,ram_percent,disk_percent,temp_celsius,proc_count

# Setze Locale auf English (C) um Dezimaltrennzeichen-Probleme zu vermeiden
export LC_NUMERIC=C

# CPU Load (1-Min Average)
LOAD=$(uptime | awk -F'load average:' '{print $2}' | cut -d',' -f1 | xargs)

# RAM Percent
RAM=$(free | awk 'NR==2 {printf "%.1f", ($3/$2)*100}')

# Disk Percent
DISK=$(df /home | awk 'NR==2 {printf "%.1f", ($3/$2)*100}')

# Temperature (°C)
TEMP=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf "%.1f", $1/1000}' || echo "0")

# Prozess-Count (relevant for Kamera)
PROCS=$(ps aux | grep -c -E '(libcamera|ffmpeg|hailo|unified_monitor|unified-camera)' 2>/dev/null || echo "0")

# Output as CSV
echo "$LOAD,$RAM,$DISK,$TEMP,$PROCS"

