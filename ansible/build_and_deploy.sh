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

# UTF-8 sicherstellen (verhindert \u00fc-Escapes in Ansible-Ausgabe bei Pipes)
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LANG="${LANG:-de_DE.UTF-8}"

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
NO_CACHE=""
E2E=false

# Argumente parsen (Reihenfolge egal: Modus + optionale Flags)
for arg in "$@"; do
    case "$arg" in
        --install)    MODE="deploy" ;;
        --update)     MODE="update" ;;
        --build)      MODE="build" ;;
        --setup-host) MODE="setup-host" ;;
        --no-cache)   NO_CACHE="--no-cache" ;;
        --e2e)        E2E=true
                      # Ohne weiteren Modus: nur E2E-Test, kein Build/Deploy
                      [[ "$MODE" == "deploy" ]] && MODE="e2e" ;;
        --help|-h)
            echo "Verwendung: $0 [--install|--update|--build|--setup-host] [--no-cache] [--e2e]"
            echo "  --install     Vollständiges Erstdeployment (Docker, SSL, Firewall, systemd)"
            echo "  --update      Nur Image + .env aktualisieren (schnell, Standard bei Update)"
            echo "  --build       Nur Docker-Image bauen, kein Deploy"
            echo "  --setup-host  Gentoo Build-Host einrichten (Docker, QEMU aarch64, buildx)"
            echo "  --no-cache    Docker Build-Cache ignorieren (sauberer Rebuild)"
            echo "  --e2e         E2E-Test nach Deploy (oder solo: nur testen, kein Build)"
            echo "                Volltest: E2E_PASSWORD + E2E_TOTP_SECRET in ansible/.env setzen"
            exit 0
            ;;
    esac
done

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

if [[ "$MODE" != "build" && "$MODE" != "e2e" ]]; then
    check_cmd ansible-playbook
fi

# ── E2E-Test Funktion ───────────────────────────────────────────────────────
run_e2e() {
    local ERRORS=0
    echo ""
    echo -e "${BOLD}🧪 E2E-Test gegen https://${PI_HOST}:8443/ ...${RESET}"
    echo "────────────────────────────────────────────────"

    # ── [1] Container läuft? ──────────────────────────────────────────────
    echo -n "   [1] Container 'pi-daemon' läuft... "
    if ssh -i "$PI_SSH_KEY" -o BatchMode=yes "${PI_USER}@${PI_HOST}" \
            'docker ps --filter name=pi-daemon --filter status=running --format "{{.Names}}"' \
            2>/dev/null | grep -q 'pi-daemon'; then
        echo -e "${GREEN}OK${RESET}"
    else
        echo -e "${RED}FEHLER – Container läuft nicht!${RESET}"
        ((ERRORS++))
    fi

    # ── [2] HTTPS-Endpoint erreichbar (401 = Server läuft, Auth fehlt) ─────
    echo -n "   [2] HTTPS Port 8443 erreichbar... "
    HTTP_CODE=$(curl -sk --max-time 5 -o /dev/null -w "%{http_code}" \
                "https://${PI_HOST}:8443/api/status" 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "200" ]]; then
        echo -e "${GREEN}OK (HTTP ${HTTP_CODE})${RESET}"
    else
        echo -e "${RED}FEHLER – HTTP ${HTTP_CODE} (erwartet 401)${RESET}"
        ((ERRORS++))
    fi

    # ── [3–5] Volltest: Login + Aufnahme ──────────────────────────────────
    if [[ -z "${E2E_PASSWORD:-}" || -z "${E2E_TOTP_SECRET:-}" ]]; then
        echo -e "${YELLOW}   ⚠ E2E_PASSWORD / E2E_TOTP_SECRET nicht in .env → Volltest übersprungen${RESET}"
        echo    "     Tipp: Beide Variablen in ansible/.env eintragen für vollständigen Test."
    else
        # TOTP generieren (oathtool bevorzugt, Fallback python3+pyotp)
        local TOTP=""
        if command -v oathtool &>/dev/null; then
            TOTP=$(oathtool --base32 --totp "${E2E_TOTP_SECRET}" 2>/dev/null || echo "")
        elif command -v python3 &>/dev/null; then
            TOTP=$(python3 -c "import pyotp; print(pyotp.TOTP('${E2E_TOTP_SECRET}').now())" 2>/dev/null || echo "")
        fi

        if [[ -z "$TOTP" ]]; then
            echo -e "${YELLOW}   ⚠ TOTP konnte nicht generiert werden.${RESET}"
            echo    "     Bitte 'oathtool' (oath-toolkit) oder python3+pyotp installieren."
        else
            # [3] Login → JWT
            echo -n "   [3] Login (JWT-Token)... "
            local TOKEN
            TOKEN=$(curl -sk --max-time 5 -X POST \
                    -H 'Content-Type: application/json' \
                    -d "{\"password\":\"${E2E_PASSWORD}\",\"totp\":\"${TOTP}\"}" \
                    "https://${PI_HOST}:8443/api/login" 2>/dev/null \
                    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))" 2>/dev/null \
                    || echo "")
            if [[ -n "$TOKEN" ]]; then
                echo -e "${GREEN}OK${RESET}"
            else
                echo -e "${RED}FEHLER – Login fehlgeschlagen (Passwort/TOTP prüfen)${RESET}"
                ((ERRORS++))
                TOKEN=""
            fi

            if [[ -n "$TOKEN" ]]; then
                # [4] Status
                echo -n "   [4] /api/status (kein Recording aktiv)... "
                local REC_RUNNING
                REC_RUNNING=$(curl -sk --max-time 5 \
                             -H "Authorization: Bearer ${TOKEN}" \
                             "https://${PI_HOST}:8443/api/status" 2>/dev/null \
                             | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('recording_running','?'))" 2>/dev/null \
                             || echo "err")
                if [[ "$REC_RUNNING" == "False" || "$REC_RUNNING" == "false" ]]; then
                    echo -e "${GREEN}OK${RESET}"
                else
                    echo -e "${YELLOW}WARNUNG – recording_running=${REC_RUNNING}${RESET}"
                fi

                # [5] 10s-Testaufnahme
                echo -n "   [5] 10s-Testaufnahme starten (HD)... "
                local REC_OK
                REC_OK=$(curl -sk --max-time 5 -X POST \
                         -H "Authorization: Bearer ${TOKEN}" \
                         -H 'Content-Type: application/json' \
                         -d '{"duration":10,"profile":"normal_hd"}' \
                         "https://${PI_HOST}:8443/api/record" 2>/dev/null \
                         | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('success','false'))" 2>/dev/null \
                         || echo "false")
                if [[ "$REC_OK" == "True" || "$REC_OK" == "true" ]]; then
                    # Polling: max 60s warten (Aufnahme 10s + ffmpeg-Konvertierung ~10-30s)
                    echo -e "${GREEN}gestartet – warte auf Abschluss (max 60s)...${RESET}"
                    local FINAL="True"
                    local WAITED=0
                    while [[ $WAITED -lt 60 ]]; do
                        sleep 3
                        WAITED=$((WAITED + 3))
                        FINAL=$(curl -sk --max-time 5 \
                                -H "Authorization: Bearer ${TOKEN}" \
                                "https://${PI_HOST}:8443/api/status" 2>/dev/null \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('recording_running','?'))" 2>/dev/null \
                                || echo "err")
                        if [[ "$FINAL" == "False" || "$FINAL" == "false" ]]; then
                            break
                        fi
                        echo -n "."
                    done
                    echo ""
                    if [[ "$FINAL" == "False" || "$FINAL" == "false" ]]; then
                        echo -e "        ${GREEN}✅ Aufnahme abgeschlossen (nach ${WAITED}s)${RESET}"
                    else
                        echo -e "        ${RED}✗ Timeout – Aufnahme nach 60s noch nicht fertig (recording_running=${FINAL})${RESET}"
                        ((ERRORS++))
                    fi
                else
                    echo -e "${RED}FEHLER – Aufnahme konnte nicht gestartet werden${RESET}"
                    ((ERRORS++))
                fi
            fi
        fi
    fi

    echo ""
    if [[ "$ERRORS" -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}✅ E2E-Test bestanden!${RESET}"
    else
        echo -e "${RED}${BOLD}❌ E2E-Test fehlgeschlagen (${ERRORS} Fehler)${RESET}"
        exit 1
    fi
}

# SSH-Verbindung prüfen
echo -n "🔗 SSH-Verbindung zum Pi... "
if ! ssh -i "$PI_SSH_KEY" -o ConnectTimeout=5 -o BatchMode=yes \
        "${PI_USER}@${PI_HOST}" echo ok &>/dev/null; then
    echo -e "${RED}FEHLER${RESET}"
    echo "   Kann ${PI_USER}@${PI_HOST} nicht erreichen." >&2
    exit 1
fi
echo -e "${GREEN}OK${RESET}"

# Nur E2E: Build/Deploy überspringen
if [[ "$MODE" == "e2e" ]]; then
    run_e2e
    exit $?
fi

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

[[ -n "$NO_CACHE" ]] && echo -e "${YELLOW}⚠ --no-cache: Build-Cache wird ignoriert${RESET}"

docker buildx build \
    --platform linux/arm64 \
    --file "${DOCKERFILE}" \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    ${NO_CACHE} \
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

# E2E-Test nach Deploy (wenn --e2e mitgegeben)
if [[ "$E2E" == "true" ]]; then
    run_e2e
fi
