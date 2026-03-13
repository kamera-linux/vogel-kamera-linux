#!/usr/bin/env bash
# pi_daemon_setup.sh – Einmalige Erstkonfiguration der Secrets
# Läuft LOKAL (nicht auf dem Pi).
# Generiert die Initialwerte für das Ansible-Vault.
#
# Verwendung:
#   ./unified-monitor-client/pi_daemon_setup.sh
#   → gibt fertige vault.yml-Werte aus und bietet an, die Datei zu befüllen

set -euo pipefail

VAULT_FILE="$(dirname "$0")/../ansible/group_vars/all/vault.yml"
BOLD="\033[1m"; RESET="\033[0m"; GREEN="\033[32m"; YELLOW="\033[33m"

echo -e "${BOLD}🐦 Vogel-Kamera Pi-Daemon – Erstkonfiguration${RESET}"
echo "──────────────────────────────────────────────────"

# ── Python-Abhängigkeiten prüfen ────────────────────────────────────────────
if ! python3 -c "import bcrypt, pyotp" 2>/dev/null; then
    echo "Installiere benötigte Python-Pakete..."
    pip3 install --quiet bcrypt pyotp
fi

# ── Passwort eingeben ───────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}1. Passwort für Web-GUI${RESET}"
read -rs -p "   Neues Passwort: " PASSWORD
echo ""
read -rs -p "   Bestätigen:    " PASSWORD2
echo ""

if [[ "$PASSWORD" != "$PASSWORD2" ]]; then
    echo "❌ Passwörter stimmen nicht überein." >&2
    exit 1
fi

if [[ ${#PASSWORD} -lt 12 ]]; then
    echo "❌ Passwort muss mindestens 12 Zeichen lang sein." >&2
    exit 1
fi

# ── Secrets generieren ──────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}2. Generiere Secrets...${RESET}"

PW_HASH=$(python3 -c "
import bcrypt, sys
h = bcrypt.hashpw(b'${PASSWORD}', bcrypt.gensalt()).decode()
print(h)
")

TOTP_SECRET=$(python3 -c "import pyotp; print(pyotp.random_base32())")

JWT_SECRET=$(python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '!@#$%^&*'
print(''.join(secrets.choice(chars) for _ in range(48)))
")

# ── QR-Code für TOTP ausgeben ───────────────────────────────────────────────
TOTP_URI="otpauth://totp/VogelKamera:admin?secret=${TOTP_SECRET}&issuer=VogelKamera"

echo "   ✅ Passwort-Hash generiert"
echo "   ✅ TOTP-Secret: ${YELLOW}${TOTP_SECRET}${RESET}"
echo "   ✅ JWT-Secret generiert"
echo ""
echo -e "${BOLD}3. Google Authenticator einrichten:${RESET}"
echo "   TOTP-Secret manuell eingeben: ${YELLOW}${TOTP_SECRET}${RESET}"
echo "   Account-Name: VogelKamera"
echo ""
echo "   Oder QR-Code generieren:"
echo "   python3 -c \"import qrcode; qrcode.make('${TOTP_URI}').show()\""
echo ""

# ── vault.yml befüllen ──────────────────────────────────────────────────────
echo -e "${BOLD}4. ansible/group_vars/all/vault.yml befüllen?${RESET}"
read -r -p "   [j/N] " CONFIRM

if [[ "${CONFIRM,,}" == "j" ]]; then
    cat > "$VAULT_FILE" << VAULT
# Generiert von pi_daemon_setup.sh am $(date '+%Y-%m-%d %H:%M')
# Verschlüsseln mit: ansible-vault encrypt ansible/group_vars/all/vault.yml
vault_pi_daemon_jwt_secret:    "${JWT_SECRET}"
vault_pi_daemon_totp_secret:   "${TOTP_SECRET}"
vault_pi_daemon_password_hash: "${PW_HASH}"
VAULT
    echo "   ✅ vault.yml geschrieben: $VAULT_FILE"
    echo ""
    echo -e "${BOLD}5. Jetzt vault.yml verschlüsseln:${RESET}"
    echo "   cd ansible && ansible-vault encrypt group_vars/all/vault.yml"
    echo ""
    echo -e "${GREEN}Fertig! Nächster Schritt: ./build_and_deploy.sh${RESET}"
else
    echo ""
    echo "Nicht gespeichert. Manuelle Werte:"
    echo "vault_pi_daemon_jwt_secret:    \"${JWT_SECRET}\""
    echo "vault_pi_daemon_totp_secret:   \"${TOTP_SECRET}\""
    echo "vault_pi_daemon_password_hash: \"${PW_HASH}\""
fi
