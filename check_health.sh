#!/bin/bash
# pi-daemon Health Monitor Script
# Manuelles Monitoring ohne externe Services
# Verwendung: ./check_health.sh oder in Cron: */5 * * * * /path/to/check_health.sh

set -euo pipefail

RASPI_IP="192.168.178.75"
RASPI_USER="roimme"
SSH_KEY="$HOME/.ssh/id_rsa_ai-had"
HEALTH_LOG="$HOME/.pi-daemon-monitor.log"

# Zeitstempel hinzufügen
log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$HEALTH_LOG"
}

# Health-Check durchführen
check_health() {
    ssh -i "$SSH_KEY" "$RASPI_USER@$RASPI_IP" \
        "docker inspect pi-daemon --format='{{.State.Health.Status}}'" 2>/dev/null || echo "ERROR"
}

# Container Status
get_container_status() {
    ssh -i "$SSH_KEY" "$RASPI_USER@$RASPI_IP" \
        "docker inspect pi-daemon --format='{{.State.Status}}'" 2>/dev/null || echo "ERROR"
}

# Failing Streak
get_failing_streak() {
    ssh -i "$SSH_KEY" "$RASPI_USER@$RASPI_IP" \
        "docker inspect pi-daemon --format='{{.State.Health.FailingStreak}}'" 2>/dev/null || echo "0"
}

# API Health-Check
check_api() {
    ssh -i "$SSH_KEY" "$RASPI_USER@$RASPI_IP" \
        "curl -sk https://localhost:8443/api/health 2>&1 | python3 -m json.tool | grep -o '\"status\": \"[^\"]*\"'" 2>/dev/null || echo "UNREACHABLE"
}

# Main
log_msg "=== Health Check Start ==="

HEALTH=$(check_health)
STATE=$(get_container_status)
STREAK=$(get_failing_streak)
API=$(check_api)

log_msg "Container State: $STATE | Health: $HEALTH | FailingStreak: $STREAK"
log_msg "API Status: $API"

# Alert bei Problemen
if [[ "$HEALTH" != "healthy" ]]; then
    log_msg "⚠️  WARNUNG: Container ist unhealthy!"
    log_msg "Detailed Info:"
    ssh -i "$SSH_KEY" "$RASPI_USER@$RASPI_IP" \
        "docker logs pi-daemon --tail 20" >> "$HEALTH_LOG"
    exit 1
fi

log_msg "✅ OK - Alles läuft"
exit 0
