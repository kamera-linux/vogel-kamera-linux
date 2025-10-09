#!/bin/bash
# ============================================================================
# Wiki Push Script - Synchronisiert lokale Wiki-Änderungen mit GitHub
# ============================================================================

set -e  # Beende bei Fehlern

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
WIKI_SYNC_DIR="$SCRIPT_DIR"

echo "🔄 Wiki Push gestartet..."
echo "Repository Root: $REPO_ROOT"

# Wechsle ins wiki-sync Verzeichnis
cd "$WIKI_SYNC_DIR"

# Führe Wiki-Sync aus
echo "📤 Synchronisiere Wiki-Änderungen..."
python3 wiki_sync.py sync

echo "✅ Wiki Push abgeschlossen!"