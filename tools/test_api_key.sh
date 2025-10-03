#!/bin/bash
# Test-Skript für YouTube API Key Validierung
# Simuliert GitHub Actions Umgebung

set -e

echo "🧪 YouTube API Key Test"
echo "======================================"
echo ""

# Prüfe ob API Key gesetzt ist
if [ -z "${YOUTUBE_API_KEY}" ]; then
    echo "❌ YOUTUBE_API_KEY Umgebungsvariable ist nicht gesetzt!"
    echo ""
    echo "Verwendung:"
    echo "  export YOUTUBE_API_KEY='dein_api_key_hier'"
    echo "  ./tools/test_api_key.sh"
    exit 1
fi

# Zeige API Key Info (ohne den Wert zu zeigen)
echo "✅ YOUTUBE_API_KEY ist gesetzt"
echo "   Länge: ${#YOUTUBE_API_KEY} Zeichen"
echo "   Prefix: ${YOUTUBE_API_KEY:0:10}..."
echo ""

# Aktiviere Python venv falls vorhanden
if [ -d ".venv" ]; then
    echo "🐍 Aktiviere Python venv..."
    source .venv/bin/activate
    echo ""
fi

# Führe Dry-Run aus
echo "🚀 Teste YouTube API Verbindung..."
echo ""

python3 tools/update_youtube_stats.py --dry-run

# Ergebnis
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ Test erfolgreich!"
    echo ""
    echo "Der API Key funktioniert korrekt."
    echo "Du kannst jetzt den echten Update ausführen:"
    echo "  python3 tools/update_youtube_stats.py"
else
    echo ""
    echo "======================================"
    echo "❌ Test fehlgeschlagen!"
    echo ""
    echo "Mögliche Ursachen:"
    echo "  1. API Key ist ungültig"
    echo "  2. YouTube Data API v3 nicht aktiviert"
    echo "  3. API Quota überschritten"
    echo ""
    echo "Überprüfe deinen API Key in:"
    echo "  https://console.cloud.google.com/apis/credentials"
    exit 1
fi
