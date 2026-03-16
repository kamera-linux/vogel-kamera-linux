#!/usr/bin/env bash
# build_and_deploy.sh – Launcher für build_and_deploy.py
#
# Leitet alle Argumente an das Python-Skript weiter.
# Sucht automatisch den richtigen Python-Interpreter (venv).
#
# Verwendung (identisch zum Python-Skript):
#   ./ansible/build_and_deploy.sh --install
#   ./ansible/build_and_deploy.sh --update
#   ./ansible/build_and_deploy.sh --build
#   ./ansible/build_and_deploy.sh --setup-host
#   ./ansible/build_and_deploy.sh --update --e2e

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/build_and_deploy.py"

# Python-Interpreter suchen (venv bevorzugt)
PYTHON=""
for _candidate in \
    "${HOME}/ansible-venv/bin/python3" \
    "${SCRIPT_DIR}/../.venv/bin/python3" \
    "${HOME}/.local/bin/python3" \
    "$(command -v python3 2>/dev/null || true)"
do
    if [[ -x "$_candidate" ]] && "$_candidate" -c "import dotenv" &>/dev/null 2>&1; then
        PYTHON="$_candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    # Fallback: erstes python3 im PATH (gibt Fehlermeldung aus dem Skript)
    PYTHON="$(command -v python3)"
fi

exec "$PYTHON" "$PY_SCRIPT" "$@"

