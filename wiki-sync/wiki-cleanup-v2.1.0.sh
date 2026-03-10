#!/bin/bash
# Wiki Cleanup für v2.1.0
# Entfernt alte Seiten und bereitet Wiki für neue Version vor

WIKI_REPO="/media/imme/ENCRYPTSSD/daten/git/kamera-linux-github/vogel-kamera-linux/wiki-repo"

echo "=========================================================="
echo "🧹 Wiki-Cleanup für v2.1.0"
echo "=========================================================="
echo ""

cd "$WIKI_REPO" || exit 1

# ALTE SEITEN LÖSCHEN (nicht mehr relevant für v2.1.0)
echo "🗑️  Lösche alte Seiten..."
OLD_FILES=(
    "3D-Konstruktion.md"
    "API-Reference.md"
    "Advanced-Features.md"
    "Contributing.md"
    "Debug-Guide.md"
    "Dependencies.md"
    "Event-Management.md"
    "FAQ.md"
    "Feature-Requests.md"
    "File-Organization.md"
    "Git-Automation.md"
    "GitHub-Discussions.md"
    "Legacy-Systems.md"
    "Performance-Tuning.md"
    "Video-Analysis-Tool.md"
    "Wiki-Sync-Test.md"
    "YouTube-Channel.md"
)

for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        git rm "$file" 2>/dev/null
        echo "   ✅ Gelöscht: $file"
    fi
done

echo ""
echo "=========================================================="
echo "✅ Wiki-Cleanup abgeschlossen!"
echo "=========================================================="
echo ""
echo "📝 Verbleibende Seiten:"
ls -1 *.md | head -20
echo ""
echo "Nächste Schritte:"
echo "  1. Home.md & _Sidebar.md für v2.1.0 aktualisieren"
echo "  2. Neue Seiten erstellen (AUTO-RECORD, 4K-Modus, etc.)"
echo "  3. git commit -m 'v2.1.0: Wiki cleanup'"
echo "  4. ./wiki-push.sh"
