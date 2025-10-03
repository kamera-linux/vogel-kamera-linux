#!/bin/bash
# =============================================================================
# SSH-Konfiguration für Vogel-Kamera-System
# =============================================================================
# Zentrale SSH-Konfiguration für alle Skripte
# Wird von anderen Skripten eingebunden
# =============================================================================

# SSH-Konfiguration
export SSH_USER="roimme"
export SSH_HOST="raspberrypi-5-ai-had"
export SSH_KEY="$HOME/.ssh/id_rsa_ai-had"
export SSH_OPTS="-i $SSH_KEY"

# SSH-Funktion
ssh_cmd() {
    ssh $SSH_OPTS "${SSH_USER}@${SSH_HOST}" "$@"
}

# SCP-Funktion
scp_to_remote() {
    local_file="$1"
    remote_path="$2"
    scp $SSH_OPTS "$local_file" "${SSH_USER}@${SSH_HOST}:${remote_path}"
}

scp_from_remote() {
    remote_file="$1"
    local_path="$2"
    scp $SSH_OPTS "${SSH_USER}@${SSH_HOST}:${remote_file}" "$local_path"
}

# Export Funktionen
export -f ssh_cmd
export -f scp_to_remote
export -f scp_from_remote
