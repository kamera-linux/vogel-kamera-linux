# 📺 YouTube Video Statistics Updater

Automatisches Tool zum Aktualisieren der YouTube-Video-Statistiken in der README.md.

## ✨ Features

- 🎬 **Automatisches Abrufen** aller Videos vom Kanal
- 📊 **Aktuelle Statistiken**: Views, Likes, Kommentare
- 📅 **Veröffentlichungsdatum** in deutschem Format
- ⏱️ **Video-Dauer** übersichtlich formatiert
- 🔄 **Automatisches README-Update** mit Markdown-Tabelle
- 🎯 **Sortierung** nach Erscheinungsdatum (neueste zuerst)

## 🛠️ Installation

```bash
# Abhängigkeiten installieren
pip install google-api-python-client python-dotenv

# Oder mit requirements.txt
pip install -r config/requirements.txt
```

## 🔑 API-Key erhalten

1. Gehe zu [Google Cloud Console](https://console.cloud.google.com/)
2. Erstelle ein neues Projekt (z.B. "vogel-kamera-youtube")
3. Aktiviere **YouTube Data API v3**:
   - Navigation → APIs & Services → Library
   - Suche "YouTube Data API v3"
   - Klicke "Enable"
4. Erstelle API-Credentials:
   - APIs & Services → Credentials
   - Create Credentials → API Key
   - Kopiere den generierten Key
5. Speichere Key in `.env`:
   ```bash
   # In Projekt-Root erstellen: .env
   YOUTUBE_API_KEY=dein_api_key_hier
   ```

## 🚀 Verwendung

### Basis-Verwendung
```bash
# Mit API-Key aus .env Datei
python3 tools/update_youtube_stats.py

# Mit API-Key als Argument
python3 tools/update_youtube_stats.py --api-key YOUR_YOUTUBE_API_KEY
```

### Erweiterte Optionen
```bash
# Nur 10 neueste Videos
python3 tools/update_youtube_stats.py --max-videos 10

# Trockentest (keine README-Änderung)
python3 tools/update_youtube_stats.py --dry-run

# Mit allen Optionen
python3 tools/update_youtube_stats.py \
    --api-key YOUR_KEY \
    --max-videos 20 \
    --dry-run
```

## 📊 Ausgabe-Beispiel

Das Tool generiert eine Markdown-Tabelle wie diese:

```markdown
| 🎬 Video | 📅 Datum | ⏱️ Dauer | 👁️ Views | 👍 Likes |
|----------|----------|----------|----------|----------|
| [**Vogel-Erkennung mit YOLOv8**](https://youtube.com/...) | 03.10.2025 | 5:30 | 1,2K | 45 |
| [**4K Zeitlupe Aufnahme**](https://youtube.com/...) | 28.09.2025 | 3:15 | 850 | 32 |
```

## 🔄 Automatisierung

### GitHub Actions (empfohlen)

Erstelle `.github/workflows/update-youtube-stats.yml`:

```yaml
name: Update YouTube Statistics

on:
  schedule:
    # Täglich um 06:00 UTC
    - cron: '0 6 * * *'
  workflow_dispatch:  # Manueller Trigger

jobs:
  update-stats:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install google-api-python-client python-dotenv
      
      - name: Update YouTube Stats
        env:
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
        run: |
          python3 tools/update_youtube_stats.py
      
      - name: Commit changes
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add README.md
          git diff --quiet && git diff --staged --quiet || \
            git commit -m "docs: Update YouTube video statistics [skip ci]"
          git push
```

**Wichtig:** Füge `YOUTUBE_API_KEY` als Repository Secret hinzu:
- GitHub → Settings → Secrets and variables → Actions
- New repository secret → Name: `YOUTUBE_API_KEY`

### Cron-Job (Linux/macOS)

```bash
# Crontab bearbeiten
crontab -e

# Täglich um 6:00 Uhr ausführen
0 6 * * * cd /pfad/zu/vogel-kamera-linux && python3 tools/update_youtube_stats.py && git add README.md && git commit -m "docs: Update YouTube stats" && git push
```

## 📝 README.md Marker

Das Tool sucht nach folgenden Markern in der README.md:

```markdown
<!-- YOUTUBE_VIDEOS_START -->
Hier wird die automatisch generierte Tabelle eingefügt
<!-- YOUTUBE_VIDEOS_END -->
```

**Wichtig:** Diese Marker müssen in der README.md vorhanden sein, damit das Tool funktioniert!

## 🔧 Troubleshooting

### Fehler: "API key not found"
```bash
# Prüfe .env Datei
cat .env | grep YOUTUBE_API_KEY

# Oder setze Umgebungsvariable
export YOUTUBE_API_KEY="dein_key_hier"
```

### Fehler: "googleapiclient not installed"
```bash
pip install google-api-python-client
```

### Fehler: "YouTube-Video-Marker nicht gefunden"
Füge folgende Zeilen in die README.md ein:
```markdown
<!-- YOUTUBE_VIDEOS_START -->
<!-- YOUTUBE_VIDEOS_END -->
```

### API Quota überschritten
- YouTube Data API v3 hat ein tägliches Quota (10.000 Einheiten)
- 1 Video-Abruf = ~6 Einheiten
- Bei 20 Videos = ~120 Einheiten pro Tag
- **Lösung:** Reduziere `--max-videos` oder führe seltener aus

## 📊 API-Kosten

Die YouTube Data API v3 ist **kostenlos**, hat aber tägliche Limits:

| Operation | Kosten (Einheiten) | Limit |
|-----------|-------------------|-------|
| Channel Details | 1 | 10.000/Tag |
| Video List | 1-3 | 10.000/Tag |
| Video Statistics | 3 | 10.000/Tag |
| **Gesamt (20 Videos)** | **~120** | **83x täglich möglich** |

## 🤝 Beitragen

Verbesserungsvorschläge:
- [ ] Unterstützung für YouTube Shorts
- [ ] Kategorisierung nach Playlists
- [ ] Thumbnail-Integration
- [ ] View-Trend-Analyse (Δ letzte 7 Tage)
- [ ] Like/View-Ratio

Pull Requests willkommen!

## 📄 Lizenz

Siehe [LICENSE](../LICENSE) - MIT License
