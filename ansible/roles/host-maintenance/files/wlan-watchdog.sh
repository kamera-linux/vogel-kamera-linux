#!/bin/bash
# WLAN-Watchdog: prüft die Verbindung zum Router und stellt sie bei Ausfall
# stufenweise wieder her. Läuft jede Minute über wlan-watchdog.timer.
#
# Stufe 1: Verbindung über NetworkManager neu aufbauen
#          (hebt auch die dauerhafte Autoconnect-Sperre nach "no-secrets" auf)
# Stufe 2: WLAN-Treiber neu laden (hängender WLAN-Chip, ASSOC-REJECT status 16)
# Stufe 3: Neustart, wenn das Netz trotz allem lange weg bleibt

INTERFACE=wlan0
CONNECTION=preconfigured
FALLBACK_GW=192.168.178.1
STATE=/run/wlan-watchdog.fails
REBOOT_AFTER=30   # Minuten ohne Netz, bevor neu gestartet wird

log() { logger -t wlan-watchdog "$*"; }

gateway() {
    local gw
    gw=$(ip route show default dev "$INTERFACE" 2>/dev/null | awk '{print $3; exit}')
    echo "${gw:-$FALLBACK_GW}"
}

online() {
    ping -c2 -W3 -I "$INTERFACE" "$(gateway)" &>/dev/null
}

if online; then
    if [ -f "$STATE" ]; then
        log "WLAN wieder erreichbar nach $(cat "$STATE") Fehlversuch(en)"
        rm -f "$STATE"
    fi
    exit 0
fi

fails=$(( $(cat "$STATE" 2>/dev/null || echo 0) + 1 ))
echo "$fails" > "$STATE"
log "Router nicht erreichbar (Fehlversuch $fails)"

# Stufe 1: Verbindung neu aktivieren
nmcli device set "$INTERFACE" autoconnect yes &>/dev/null
nmcli --wait 40 connection up "$CONNECTION" ifname "$INTERFACE" &>/dev/null
sleep 5
if online; then
    log "Reconnect über NetworkManager erfolgreich"
    rm -f "$STATE"
    exit 0
fi

# Stufe 2: ab dem 2. Fehlversuch WLAN-Treiber neu laden
if [ "$fails" -ge 2 ]; then
    log "Reconnect fehlgeschlagen – lade WLAN-Treiber neu"
    modprobe -r brcmfmac_cyw brcmfmac
    sleep 3
    modprobe brcmfmac
    sleep 10
    nmcli --wait 40 connection up "$CONNECTION" ifname "$INTERFACE" &>/dev/null
    sleep 5
    if online; then
        log "WLAN nach Treiber-Neustart wieder da"
        rm -f "$STATE"
        exit 0
    fi
fi

# Stufe 3: letzter Ausweg
if [ "$fails" -ge "$REBOOT_AFTER" ]; then
    log "WLAN seit $fails Versuchen weg – starte neu"
    systemctl reboot
fi
