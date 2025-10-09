#!/bin/bash
# ============================================================================
# Wiki Pull Script - Holt neueste Wiki-Inhalte vom GitHub Repository
# ============================================================================

set -e  # Beende bei Fehlern

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
WIKI_SYNC_DIR="$SCRIPT_DIR"

echo "🔄 Wiki Pull gestartet..."
echo "Repository Root: $REPO_ROOT"

# Wechsle ins wiki-sync Verzeichnis
cd "$WIKI_SYNC_DIR"

# Führe Wiki-Pull aus
echo "📥 Hole neueste Wiki-Inhalte..."
python3 wiki_sync.py pull

echo "✅ Wiki Pull abgeschlossen!"