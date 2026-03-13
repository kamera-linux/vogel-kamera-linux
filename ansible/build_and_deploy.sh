#!/usr/bin/env bash
# build_and_deploy.sh – Docker-Image bauen und auf Pi deployen
#
# Verwendung (aus dem ansible/-Ordner oder Repo-Root):
#   ./ansible/build_and_deploy.sh --install      # Vollständiges Erstdeployment
#   ./ansible/build_and_deploy.sh --update       # Nur Image aktualisieren (schnell)
#   ./ansible/build_and_deploy.sh --build        # Nur bauen, nicht deployen
#   ./ansible/build_and_deploy.sh --setup-host   # Gentoo Build-Host einrichten (Docker, QEMU, buildx)
#
# Voraussetzungen (einmalig):
#   1. docker buildx create --use --name pi-builder  (oder: --setup-host)
#   2. ansible-vault encrypt ansible/group_vars/all/vault.yml
#   3. echo 'VaultPasswort' > ~/.pi-daemon-vault-pass && chmod 600 ~/.pi-daemon-vault-pass

set -euo pipefail

# Skript liegt in ansible/ → Repo-Root ist ein Verzeichnis höher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ANSIBLE_DIR="${SCRIPT_DIR}"
DOCKERFILE="${REPO_ROOT}/docker/Dockerfile"
IMAGE_NAME="vogel-pi"
IMAGE_TAG="latest"
ARCHIVE="/tmp/vogel-pi.tar.gz"

# ── .env einlesen (persönliche Einstellungen) ───────────────────────────────
ENV_FILE="${SCRIPT_DIR}/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a; source "$ENV_FILE"; set +a
else
    echo -e "${RED}❌ Keine .env gefunden: ${ENV_FILE}${RESET}" >&2
    echo    "   Einmalig anlegen:" >&2
    echo    "   cp ansible/.env.example ansible/.env && \${EDITOR:-nano} ansible/.env" >&2
    exit 1
fi

PI_HOST="${PI_HOST:?PI_HOST nicht in .env gesetzt}"
PI_USER="${PI_USER:?PI_USER nicht in .env gesetzt}"
PI_SSH_KEY="${PI_SSH_KEY:?PI_SSH_KEY nicht in .env gesetzt}"
PI_SSH_KEY="$(eval echo "$PI_SSH_KEY")"   # ~ expandieren

BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; RESET="\033[0m"

MODE="deploy"
[[ "${1:-}" == "--install"    ]] && MODE="deploy"
[[ "${1:-}" == "--update"     ]] && MODE="update"
[[ "${1:-}" == "--build"      ]] && MODE="build"
[[ "${1:-}" == "--setup-host" ]] && MODE="setup-host"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Verwendung: $0 [--install|--update|--build|--setup-host]"
    echo "  --install     Vollständiges Erstdeployment (Docker, SSL, Firewall, systemd)"
    echo "  --update      Nur Image + .env aktualisieren (schnell, Standard bei Update)"
    echo "  --build       Nur Docker-Image bauen, kein Deploy"
    echo "  --setup-host  Gentoo Build-Host einrichten (Docker, QEMU aarch64, buildx)"
    exit 0
fi

echo -e "${BOLD}🐦 Vogel-Kamera – Build & Deploy (${MODE})${RESET}"
echo "────────────────────────────────────────────────"

# ── Build-Host einrichten (kein Pi-Zugriff nötig) ───────────────────────────
if [[ "$MODE" == "setup-host" ]]; then
    check_cmd ansible-playbook
    echo -e "${BOLD}🔧 Gentoo Build-Host einrichten (Docker, QEMU, buildx)...${RESET}"
    echo "   Benötigt sudo/become – bitte Passwort eingeben."
    echo ""
    ansible-playbook \
        "${ANSIBLE_DIR}/playbooks/setup-build-host.yml" \
        --ask-become-pass
    echo ""
    echo -e "${GREEN}${BOLD}✅ Build-Host eingerichtet.${RESET}"
    echo "   Bitte neu einloggen oder 'newgrp docker' ausführen."
    echo "   Danach: ./ansible/build_and_deploy.sh --install"
    exit 0
fi

# ── Voraussetzungen prüfen ──────────────────────────────────────────────────
check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}❌ '$1' nicht gefunden. Bitte installieren.${RESET}" >&2
        exit 1
    fi
}
check_cmd docker
check_cmd ssh
check_cmd scp

if [[ "$MODE" != "build" ]]; then
    check_cmd ansible-playbook
fi

# SSH-Verbindung prüfen
echo -n "🔗 SSH-Verbindung zum Pi... "
if ! ssh -i "$PI_SSH_KEY" -o ConnectTimeout=5 -o BatchMode=yes \
        "${PI_USER}@${PI_HOST}" echo ok &>/dev/null; then
    echo -e "${RED}FEHLER${RESET}"
    echo "   Kann ${PI_USER}@${PI_HOST} nicht erreichen." >&2
    exit 1
fi
echo -e "${GREEN}OK${RESET}"

# docker buildx Kontext prüfen
if ! docker buildx inspect pi-builder &>/dev/null; then
    echo -e "${YELLOW}⚙ Erstelle docker buildx Kontext 'pi-builder'...${RESET}"
    docker buildx create --name pi-builder --use
    docker buildx inspect --bootstrap
fi
docker buildx use pi-builder

# ── Build ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}📦 Baue Docker-Image für linux/arm64...${RESET}"
echo "   Dockerfile: ${DOCKERFILE}"
echo "   Build-Kontext: ${REPO_ROOT}"
echo ""

docker buildx build \
    --platform linux/arm64 \
    --file "${DOCKERFILE}" \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --load \
    "${REPO_ROOT}"

echo -e "${GREEN}✅ Image gebaut: ${IMAGE_NAME}:${IMAGE_TAG}${RESET}"

if [[ "$MODE" == "build" ]]; then
    echo "Build-Only Modus – Deploy übersprungen."
    exit 0
fi

# ── Export & Transfer ────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}📤 Image komprimieren und auf Pi kopieren...${RESET}"
docker save "${IMAGE_NAME}:${IMAGE_TAG}" | gzip > "${ARCHIVE}"

ARCHIVE_SIZE=$(du -sh "${ARCHIVE}" | cut -f1)
echo "   Archiv: ${ARCHIVE} (${ARCHIVE_SIZE})"

scp -i "$PI_SSH_KEY" "${ARCHIVE}" "${PI_USER}@${PI_HOST}:/tmp/vogel-pi.tar.gz"
rm -f "${ARCHIVE}"
echo -e "${GREEN}✅ Image übertragen${RESET}"

# ── Ansible Deploy / Update ──────────────────────────────────────────────────
echo ""
cd "${ANSIBLE_DIR}"

VAULT_FILE="group_vars/all/vault.yml"
VAULT_PASS_FILE="${VAULT_PASS_FILE:-${HOME}/.pi-daemon-vault-pass}"

# Vault-Passwort-Option bestimmen
if [[ -f "$VAULT_PASS_FILE" ]]; then
    VAULT_OPT="--vault-password-file ${VAULT_PASS_FILE}"
    echo -e "🔐 Vault-Passwort: aus ${VAULT_PASS_FILE}"
else
    VAULT_OPT="--ask-vault-pass"
    echo -e "${YELLOW}🔐 Vault-Passwort wird interaktiv abgefragt.${RESET}"
    echo "   Tipp: Schreibe es nach ${VAULT_PASS_FILE} für automatischen Betrieb:"
    echo "         echo 'MeinVaultPasswort' > ${VAULT_PASS_FILE} && chmod 600 ${VAULT_PASS_FILE}"
fi

echo ""
if [[ "$MODE" == "deploy" ]]; then
    echo -e "${BOLD}🚀 Ansible – Voll-Deployment (Erstinstall)...${RESET}"
    ansible-playbook playbooks/deploy.yml $VAULT_OPT
else
    echo -e "${BOLD}🔄 Ansible – Image-Update...${RESET}"
    ansible-playbook playbooks/update.yml $VAULT_OPT
fi

echo ""
echo -e "${GREEN}${BOLD}✅ Fertig!${RESET}"
echo "   Web-GUI: https://${PI_HOST}:8443/"
echo "   Beim ersten Aufruf Browser-Zertifikat-Ausnahme bestätigen (self-signed)."
