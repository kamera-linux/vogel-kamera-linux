#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Video Statistics Updater für vogel-kamera-linux
=======================================================

Aktualisiert automatisch die YouTube-Video-Tabelle in der README.md
mit aktuellen Statistiken (Views, Likes, Datum).

Features:
- 🎬 Automatisches Abrufen aller Videos vom Kanal
- 📊 Aktuelle View-Zahlen und Likes
- 📅 Veröffentlichungsdatum
- 🔄 Automatische README.md Update
- 🎯 Sortierung nach Erscheinungsdatum
- 🕐 Deutsche Zeitzone mit Sommer-/Winterzeit-Erkennung

Verwendung:
    # Mit API-Key als Argument
    python3 tools/update_youtube_stats.py --api-key YOUR_YOUTUBE_API_KEY
    
    # Mit API-Key aus Umgebungsvariable
    export YOUTUBE_API_KEY="YOUR_KEY"
    python3 tools/update_youtube_stats.py
    
    # Trockentest (keine README-Änderung)
    python3 tools/update_youtube_stats.py --dry-run

Requirements:
    pip install google-api-python-client python-dotenv

API-Key erhalten:
    1. Gehe zu: https://console.cloud.google.com/
    2. Erstelle ein neues Projekt
    3. Aktiviere "YouTube Data API v3"
    4. Erstelle API-Credentials (API-Key)
    5. Speichere Key in .env: YOUTUBE_API_KEY=dein_key_hier
"""

import os
import sys
import argparse
import re
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Optionale YouTube API Import
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_YOUTUBE_API = True
except ImportError:
    HAS_YOUTUBE_API = False
    print("⚠️  googleapiclient nicht installiert. Installiere mit:")
    print("   pip install google-api-python-client")

# Lade .env Datei
load_dotenv()

# YouTube Kanal-ID (aus URL: youtube.com/@vogel-kamera-linux)
CHANNEL_HANDLE = "@vogel-kamera-linux"
CHANNEL_ID = None  # Wird automatisch ermittelt

# README Pfad
README_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')

def get_channel_id_by_handle(youtube, handle: str) -> Optional[str]:
    """
    Ermittle Channel-ID anhand des Handles (@vogel-kamera-linux)
    
    Args:
        youtube: YouTube API Client
        handle: Channel Handle (z.B. @vogel-kamera-linux)
    
    Returns:
        Channel-ID oder None
    """
    try:
        # Entferne @ falls vorhanden
        handle = handle.lstrip('@')
        
        # Suche nach Kanal
        request = youtube.search().list(
            part="snippet",
            q=handle,
            type="channel",
            maxResults=1
        )
        response = request.execute()
        
        if response['items']:
            channel_id = response['items'][0]['snippet']['channelId']
            print(f"✅ Kanal gefunden: {handle} → {channel_id}")
            return channel_id
        else:
            print(f"❌ Kanal nicht gefunden: {handle}")
            return None
            
    except HttpError as e:
        print(f"❌ Fehler beim Abrufen der Channel-ID: {e}")
        return None

def get_channel_videos(youtube, channel_id: str, max_results: int = 50) -> List[Dict]:
    """
    Hole alle Videos vom Kanal
    
    Args:
        youtube: YouTube API Client
        channel_id: YouTube Channel ID
        max_results: Maximale Anzahl Videos
    
    Returns:
        Liste mit Video-Informationen
    """
    videos = []
    
    try:
        # Hole Uploads-Playlist ID
        request = youtube.channels().list(
            part="contentDetails,statistics",
            id=channel_id
        )
        response = request.execute()
        
        if not response['items']:
            print(f"❌ Kanal nicht gefunden: {channel_id}")
            return []
        
        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        channel_stats = response['items'][0]['statistics']
        
        print(f"📊 Kanal-Statistiken:")
        print(f"   Videos: {channel_stats.get('videoCount', 'N/A')}")
        print(f"   Abonnenten: {channel_stats.get('subscriberCount', 'N/A')}")
        print(f"   Views gesamt: {channel_stats.get('viewCount', 'N/A')}")
        print()
        
        # Hole Videos aus Uploads-Playlist
        next_page_token = None
        video_count = 0
        
        while video_count < max_results:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - video_count),
                pageToken=next_page_token
            )
            response = request.execute()
            
            # Sammle Video-IDs
            video_ids = [item['contentDetails']['videoId'] for item in response['items']]
            
            # Hole detaillierte Video-Statistiken
            video_request = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=','.join(video_ids)
            )
            video_response = video_request.execute()
            
            for video in video_response['items']:
                video_info = {
                    'id': video['id'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'published_at': video['snippet']['publishedAt'],
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'duration': video['contentDetails']['duration'],
                    'views': int(video['statistics'].get('viewCount', 0)),
                    'likes': int(video['statistics'].get('likeCount', 0)),
                    'comments': int(video['statistics'].get('commentCount', 0)),
                    'url': f"https://www.youtube.com/watch?v={video['id']}"
                }
                videos.append(video_info)
                video_count += 1
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        print(f"✅ {len(videos)} Videos abgerufen\n")
        return videos
        
    except HttpError as e:
        print(f"❌ Fehler beim Abrufen der Videos: {e}")
        return []

def format_views(views: int) -> str:
    """
    Formatiere View-Zahlen leserlich
    
    Args:
        views: Anzahl Views
    
    Returns:
        Formatierter String (z.B. "1,2K" oder "15,3K")
    """
    if views >= 1000000:
        return f"{views/1000000:.1f}M"
    elif views >= 1000:
        return f"{views/1000:.1f}K"
    else:
        return str(views)

def format_date(date_str: str) -> str:
    """
    Formatiere ISO-Datum zu deutschem Format
    
    Args:
        date_str: ISO 8601 Datum (z.B. "2025-09-23T14:30:00Z")
    
    Returns:
        Deutsches Datum (z.B. "23.09.2025")
    """
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y')
    except:
        return date_str

def parse_duration(duration: str) -> str:
    """
    Parse ISO 8601 Duration zu lesbarem Format
    
    Args:
        duration: ISO 8601 Duration (z.B. "PT5M30S")
    
    Returns:
        Lesbares Format (z.B. "5:30")
    """
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return "N/A"
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def generate_video_table(videos: List[Dict]) -> str:
    """
    Generiere Markdown-Tabelle mit Video-Statistiken
    
    Args:
        videos: Liste mit Video-Informationen
    
    Returns:
        Markdown-Tabelle als String
    """
    # Sortiere nach Veröffentlichungsdatum (neueste zuerst)
    sorted_videos = sorted(videos, key=lambda x: x['published_at'], reverse=True)
    
    table = []
    table.append("| 🎬 Video | 📅 Datum | ⏱️ Dauer | 👁️ Views | 👍 Likes |")
    table.append("|----------|----------|----------|----------|----------|")
    
    for video in sorted_videos:
        title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
        date = format_date(video['published_at'])
        duration = parse_duration(video['duration'])
        views = format_views(video['views'])
        likes = format_views(video['likes'])
        url = video['url']
        
        # Escape Pipe-Zeichen in Titel
        title = title.replace('|', '\\|')
        
        table.append(f"| [**{title}**]({url}) | {date} | {duration} | {views} | {likes} |")
    
    return '\n'.join(table)

def update_readme(video_table: str, dry_run: bool = False) -> bool:
    """
    Aktualisiere README.md mit neuer Video-Tabelle
    
    Args:
        video_table: Generierte Markdown-Tabelle
        dry_run: Wenn True, keine Datei-Änderung
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Lese aktuelle README
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Finde YouTube-Kanal Sektion
        # Suche nach: ### 🎬 YouTube-Kanal & Beispielaufnahmen
        pattern = r'(### 🎬 YouTube-Kanal & Beispielaufnahmen\n\n.*?\n\n)(<!-- YOUTUBE_VIDEOS_START -->.*?<!-- YOUTUBE_VIDEOS_END -->)'
        
        # Prüfe ob Marker existieren
        if '<!-- YOUTUBE_VIDEOS_START -->' not in content:
            print("⚠️  YouTube-Video-Marker nicht gefunden in README.md")
            print("   Füge folgende Zeilen nach der YouTube-Kanal Sektion ein:")
            print("   <!-- YOUTUBE_VIDEOS_START -->")
            print("   Hier wird automatisch die Video-Tabelle eingefügt")
            print("   <!-- YOUTUBE_VIDEOS_END -->")
            return False
        
        # Erstelle neue Video-Sektion mit Zeitstempel (IMMER aktualisiert)
        # Format: DD.MM.YYYY HH:MM Uhr (deutsche Zeit mit Sommer-/Winterzeit)
        from zoneinfo import ZoneInfo
        now_de = datetime.now(ZoneInfo('Europe/Berlin'))
        
        # Prüfe ob Sommerzeit oder Winterzeit
        timezone_name = "Sommerzeit (MESZ)" if now_de.dst() else "Winterzeit (MEZ)"
        
        timestamp = now_de.strftime('%d.%m.%Y %H:%M')
        timezone_suffix = f" Uhr ({timezone_name})"
        
        # Prüfe ob sich Video-Daten geändert haben (für Kommentar)
        old_video_section = re.search(
            r'<!-- YOUTUBE_VIDEOS_START -->.*?<!-- YOUTUBE_VIDEOS_END -->',
            content,
            flags=re.DOTALL
        )
        
        # Vergleiche nur die Tabelle (ohne Zeitstempel)
        videos_changed = True
        if old_video_section:
            old_table = re.search(r'\| \*\*.*?\| Views', old_video_section.group(), flags=re.DOTALL)
            new_table = re.search(r'\| \*\*.*?\| Views', video_table, flags=re.DOTALL)
            if old_table and new_table:
                videos_changed = old_table.group() != new_table.group()
        
        # Erstelle Footer mit Status
        if videos_changed:
            footer = f"*Automatisch aktualisiert: {timestamp}{timezone_suffix}*\n"
        else:
            footer = f"*Automatisch aktualisiert: {timestamp}{timezone_suffix} (keine neuen Daten)*\n"
        
        video_section = f"<!-- YOUTUBE_VIDEOS_START -->\n**📺 Aktuelle Videos:**\n\n{video_table}\n\n{footer}<!-- YOUTUBE_VIDEOS_END -->"
        
        # Ersetze Video-Sektion
        new_content = re.sub(
            r'<!-- YOUTUBE_VIDEOS_START -->.*?<!-- YOUTUBE_VIDEOS_END -->',
            video_section,
            content,
            flags=re.DOTALL
        )
        
        if dry_run:
            print("🔍 DRY-RUN Modus - Keine Änderungen an README.md")
            print("\n" + "="*70)
            print("NEUE VIDEO-TABELLE:")
            print("="*70)
            print(video_section)
            print("="*70)
            return True
        
        # Schreibe aktualisierte README
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ README.md erfolgreich aktualisiert: {README_PATH}")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren der README: {e}")
        return False

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description='YouTube Video Statistics Updater für vogel-kamera-linux',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Beispiele:
  python3 tools/update_youtube_stats.py --api-key YOUR_KEY
  python3 tools/update_youtube_stats.py --dry-run
  python3 tools/update_youtube_stats.py --max-videos 20

API-Key erhalten:
  1. https://console.cloud.google.com/
  2. Neues Projekt erstellen
  3. "YouTube Data API v3" aktivieren
  4. API-Credentials erstellen
  5. In .env speichern: YOUTUBE_API_KEY=dein_key_hier
        '''
    )
    
    parser.add_argument('--api-key', type=str, help='YouTube API Key (oder YOUTUBE_API_KEY Umgebungsvariable)')
    parser.add_argument('--max-videos', type=int, default=20, help='Maximale Anzahl Videos (default: 20)')
    parser.add_argument('--dry-run', action='store_true', help='Trockentest - keine README-Änderung')
    
    args = parser.parse_args()
    
    # Prüfe YouTube API Verfügbarkeit
    if not HAS_YOUTUBE_API:
        print("❌ YouTube API Client nicht verfügbar")
        print("   Installiere mit: pip install google-api-python-client")
        sys.exit(1)
    
    # Hole API-Key (Priorität: CLI-Argument > Umgebungsvariable)
    api_key = args.api_key or os.getenv('YOUTUBE_API_KEY')
    
    # Debug: Zeige Quellen
    if args.api_key:
        print("🔑 API-Key Quelle: CLI-Argument\n")
    elif os.getenv('YOUTUBE_API_KEY'):
        print("🔑 API-Key Quelle: Umgebungsvariable YOUTUBE_API_KEY\n")
    
    if not api_key:
        print("❌ Kein YouTube API Key gefunden!")
        print("\n📋 Möglichkeiten:")
        print("   1. CLI: python3 tools/update_youtube_stats.py --api-key YOUR_KEY")
        print("   2. ENV: export YOUTUBE_API_KEY='YOUR_KEY'")
        print("   3. GitHub Actions: Setze YOUTUBE_API_KEY Secret in Repository Settings")
        print("\n🔍 Aktuelle Umgebungsvariablen:")
        print(f"   YOUTUBE_API_KEY: {'✅ gesetzt' if os.getenv('YOUTUBE_API_KEY') else '❌ nicht gesetzt'}")
        sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
  📺 YouTube Video Statistics Updater
╠══════════════════════════════════════════════════════════════╣
  Kanal: {CHANNEL_HANDLE}
  Max Videos: {args.max_videos}
  Dry-Run: {'Ja' if args.dry_run else 'Nein'}
╚══════════════════════════════════════════════════════════════╝
""")
    
    try:
        # Initialisiere YouTube API
        youtube = build('youtube', 'v3', developerKey=api_key)
        print("✅ YouTube API Client initialisiert\n")
        
        # Hole Channel-ID
        channel_id = get_channel_id_by_handle(youtube, CHANNEL_HANDLE)
        if not channel_id:
            print(f"❌ Konnte Channel-ID nicht ermitteln für: {CHANNEL_HANDLE}")
            sys.exit(1)
        
        # Hole Videos
        videos = get_channel_videos(youtube, channel_id, args.max_videos)
        if not videos:
            print("❌ Keine Videos gefunden")
            sys.exit(1)
        
        # Generiere Tabelle
        print("📝 Generiere Video-Tabelle...")
        video_table = generate_video_table(videos)
        
        # Aktualisiere README
        print("📄 Aktualisiere README.md...")
        if update_readme(video_table, dry_run=args.dry_run):
            print("\n✅ Erfolgreich abgeschlossen!")
            if not args.dry_run:
                print("   README.md wurde aktualisiert")
                print("   Committe die Änderungen mit:")
                print("   git add README.md")
                print("   git commit -m 'docs: Update YouTube video statistics'")
        else:
            print("\n❌ Fehler beim Aktualisieren")
            sys.exit(1)
            
    except HttpError as e:
        print(f"\n❌ YouTube API Fehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
