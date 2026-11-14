#!/bin/bash
# Boot-Prüfung der Vogelkamera – läuft beim Start VOR Docker.
# Docker (und damit pi-daemon, Grafana, Prometheus) startet nur, wenn dieses
# Skript mit 0 endet.
#
#  1. Paketsystem sauber? (abgebrochenes Update reparieren)
#  2. Neustart nötig? (neuerer Kernel installiert als der laufende → 1x neu starten)
#  3. Hailo-Beschleuniger vorhanden (/dev/hailo0)?
#  4. Kamera erkannt?
#  5. Netzwerk (nur Warnung, blockiert Docker nicht – das macht der WLAN-Watchdog)
#
# Notausgang: Datei /etc/vogelkamera/skip-boot-check anlegen → Prüfung wird übersprungen.

export LC_ALL=C
STATE_DIR=/var/lib/boot-health-check
STATUS=/run/boot-health-check.status
mkdir -p "$STATE_DIR"

log()  { logger -t boot-health-check "$*"; echo "$*"; }
fail() { log "FEHLER: $* – Docker wird NICHT gestartet"; echo "FEHLER: $*" > "$STATUS"; exit 1; }

if [ -f /etc/vogelkamera/skip-boot-check ]; then
    log "Prüfung übersprungen (/etc/vogelkamera/skip-boot-check vorhanden)"
    echo "übersprungen" > "$STATUS"
    exit 0
fi

# 1. Paketsystem
if [ -n "$(dpkg --audit 2>/dev/null)" ]; then
    log "Paketsystem unvollständig – versuche dpkg --configure -a"
    DEBIAN_FRONTEND=noninteractive dpkg --configure -a --force-confdef --force-confold
    [ -n "$(dpkg --audit 2>/dev/null)" ] && fail "Paketsystem nach Reparatur weiterhin defekt"
    log "Paketsystem repariert"
fi

# 2. Läuft der neueste installierte Kernel?
running=$(uname -r)
flavor=${running##*+}                              # z. B. rpt-rpi-2712
newest=$(for d in /lib/modules/*+"${flavor}"; do [ -d "$d" ] && basename "$d"; done | sort -V | tail -1)
if [ -n "$newest" ] && [ "$newest" != "$running" ]; then
    if [ "$(cat "$STATE_DIR/reboot-tried" 2>/dev/null)" != "$newest" ]; then
        echo "$newest" > "$STATE_DIR/reboot-tried"
        log "Neuerer Kernel $newest installiert, läuft aber $running – starte neu"
        systemctl reboot
        exit 1
    fi
    log "WARNUNG: Kernel $newest bootet nicht (läuft weiter $running) – kein weiterer Neustart"
fi

# 3. Hailo
for _ in $(seq 1 30); do [ -e /dev/hailo0 ] && break; sleep 1; done
if [ ! -e /dev/hailo0 ]; then
    log "/dev/hailo0 fehlt – lade hailo_pci"
    modprobe hailo_pci; sleep 5
    [ -e /dev/hailo0 ] || fail "Hailo-Beschleuniger nicht gefunden (/dev/hailo0)"
fi

# 4. Kamera
cams=""
for _ in 1 2 3; do
    cams=$(timeout 20 rpicam-hello --list-cameras 2>&1)
    echo "$cams" | grep -qE '^[0-9]+ : ' && break
    sleep 5
done
echo "$cams" | grep -qE '^[0-9]+ : ' || fail "Keine Kamera erkannt"
cam=$(echo "$cams" | grep -E '^[0-9]+ : ' | head -1 | sed 's/^[0-9]* : //; s/ \[.*//')

# 5. Netzwerk (nur Warnung)
net="ok"
for _ in $(seq 1 24); do
    gw=$(ip route show default 2>/dev/null | awk '{print $3; exit}')
    [ -n "$gw" ] && ping -c1 -W2 "$gw" &>/dev/null && break
    sleep 5
done
if [ -z "$gw" ] || ! ping -c1 -W2 "$gw" &>/dev/null; then
    net="nicht erreichbar"
    log "WARNUNG: Router nach 2 Minuten nicht erreichbar – Docker startet trotzdem"
fi

[ "$newest" = "$running" ] && rm -f "$STATE_DIR/reboot-tried"
log "OK – Kernel $running, Hailo vorhanden, Kamera $cam, Netz $net"
echo "OK $(date '+%F %T')" > "$STATUS"
exit 0
