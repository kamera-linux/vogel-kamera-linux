#!/bin/bash
# Update beim Systemstart – läuft VOR boot-health-check und Docker.
# Die Kamera läuft nur tagsüber, deshalb kein nächtlicher Zeitplan.
#
#  1. Höchstens alle MIN_HOURS Stunden (nach einem Update-Neustart nicht gleich wieder)
#  2. Auf Netz warten (max. 2 min), sonst überspringen
#  3. apt update + unattended-upgrade (Regeln: /etc/apt/apt.conf.d/52vogelkamera-unattended)
#  4. Neustart, wenn ein Update es verlangt
#
# Docker/containerd dürfen währenddessen nicht gestartet werden: docker.service wartet
# auf boot-health-check, das auf dieses Skript wartet → sonst gegenseitige Blockade.

export LC_ALL=C.UTF-8 LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive
STATE_DIR=/var/lib/boot-health-check
STAMP=$STATE_DIR/last-update
MIN_HOURS=6
POLICY=/usr/sbin/policy-rc.d
mkdir -p "$STATE_DIR"

log() { logger -t boot-update "$*"; echo "$*"; }

if [ -f /etc/vogelkamera/skip-boot-update ]; then
    log "Update übersprungen (/etc/vogelkamera/skip-boot-update vorhanden)"
    exit 0
fi

if [ -f "$STAMP" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "$STAMP") ))
    if [ "$age" -ge 0 ] && [ "$age" -lt $(( MIN_HOURS * 3600 )) ]; then
        log "Letztes Update vor $(( age / 60 )) min – übersprungen"
        exit 0
    fi
fi

online=0
for _ in $(seq 1 24); do
    gw=$(ip route show default 2>/dev/null | awk '{print $3; exit}')
    if [ -n "$gw" ] && ping -c1 -W2 "$gw" &>/dev/null; then online=1; break; fi
    sleep 5
done
if [ "$online" = 0 ]; then
    log "Kein Netz nach 2 min – Update übersprungen"
    exit 0
fi

# Start von docker/containerd während des Updates verbieten (nur diese beiden)
if [ ! -e "$POLICY" ]; then
    cat > "$POLICY" <<'EOF'
#!/bin/sh
# temporär von boot-update.sh – verhindert Start von Docker während des Boot-Updates
case "$1" in docker*|containerd*) exit 101 ;; esac
exit 0
EOF
    chmod 755 "$POLICY"
    trap 'rm -f "$POLICY"' EXIT
fi

log "Starte Update"
if ! apt-get update -q >/dev/null 2>&1; then
    log "apt-get update fehlgeschlagen – Update übersprungen"
    exit 0
fi
touch /var/lib/apt/periodic/update-success-stamp   # für "Paketlisten aktualisiert" in Grafana
unattended-upgrade
rc=$?
touch "$STAMP"
log "unattended-upgrade beendet (exit $rc)"
/usr/local/bin/update-status.py || true

if [ -f /run/reboot-required ]; then
    log "Update verlangt Neustart ($(tr '\n' ' ' < /run/reboot-required.pkgs 2>/dev/null)) – starte neu"
    rm -f "$POLICY"
    systemctl reboot
    exit 1
fi
exit 0
