#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frame-Extraktion aus Vogelhaus-Videos für AI-Training

Verwendung:
  python extract_frames.py input_video.mp4 output_dir/ --interval 10
"""

import cv2
import os
import argparse
from pathlib import Path

def extract_frames(video_path, output_dir, interval=30, max_frames=None):
    """
    Extrahiert Frames aus einem Video in regelmäßigen Abständen
    
    Args:
        video_path: Pfad zum Input-Video
        output_dir: Ausgabe-Verzeichnis für Frames
        interval: Intervall in Sekunden zwischen Frames
        max_frames: Maximum Anzahl Frames (None = unbegrenzt)
    """
    
    # Ausgabe-Verzeichnis erstellen
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Video öffnen
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Fehler: Kann Video nicht öffnen: {video_path}")
        return False
    
    # Video-Eigenschaften
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    frame_interval = int(fps * interval)
    
    print("📹 Video-Info:")
    print(f"   FPS: {fps:.2f}")
    print(f"   Dauer: {duration:.1f} Sekunden")
    print(f"   Frames gesamt: {total_frames}")
    print(f"   Extrahiere alle {interval} Sekunden (alle {frame_interval} Frames)")
    
    # Frame-Extraktion
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Alle X Frames einen Frame speichern
        if frame_count % frame_interval == 0:
            # Dateiname mit Zeitstempel
            timestamp = frame_count / fps
            filename = f"frame_{saved_count:04d}_t{timestamp:.1f}s.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # Frame speichern
            success = cv2.imwrite(filepath, frame)
            if success:
                saved_count += 1
                print(f"✅ Gespeichert: {filename} ({saved_count} Frames)")
            else:
                print(f"❌ Fehler beim Speichern: {filename}")
            
            # Maximum erreicht?
            if max_frames and saved_count >= max_frames:
                print(f"🎯 Maximum von {max_frames} Frames erreicht")
                break
                
        frame_count += 1
    
    cap.release()
    
    print("\n✅ Extraktion abgeschlossen:")
    print(f"   Extrahiert: {saved_count} Frames")
    print(f"   Ausgabe: {output_dir}")
    
    return True

def process_multiple_videos(video_dir, output_base_dir, **kwargs):
    """Verarbeitet mehrere Videos in einem Verzeichnis"""
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(Path(video_dir).glob(f'*{ext}'))
        video_files.extend(Path(video_dir).glob(f'*{ext.upper()}'))
    
    if not video_files:
        print(f"❌ Keine Videos gefunden in: {video_dir}")
        return False
    
    print(f"📂 Gefundene Videos: {len(video_files)}")
    
    for video_file in video_files:
        print(f"\n🎬 Verarbeite: {video_file.name}")
        
        # Ausgabe-Unterverzeichnis für jedes Video
        output_dir = Path(output_base_dir) / video_file.stem
        
        success = extract_frames(str(video_file), str(output_dir), **kwargs)
        if not success:
            print(f"❌ Fehler bei: {video_file.name}")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Frame-Extraktion aus Vogelhaus-Videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einzelnes Video, alle 10 Sekunden
  python extract_frames.py video.mp4 frames/ --interval 10
  
  # Alle Videos in einem Ordner
  python extract_frames.py videos/ frames/ --batch --interval 5 --max-frames 100
  
  # Hochfrequente Extraktion für Action-Szenen
  python extract_frames.py feeding_time.mp4 frames/ --interval 1 --max-frames 200
        """
    )
    
    parser.add_argument('input', help='Input-Video oder Verzeichnis mit Videos')
    parser.add_argument('output', help='Ausgabe-Verzeichnis für Frames')
    parser.add_argument('--interval', type=float, default=30, 
                       help='Intervall zwischen Frames in Sekunden (default: 30)')
    parser.add_argument('--max-frames', type=int, 
                       help='Maximum Anzahl Frames pro Video (default: unbegrenzt)')
    parser.add_argument('--batch', action='store_true',
                       help='Verarbeite alle Videos im Input-Verzeichnis')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    # Prüfen ob Input existiert
    if not input_path.exists():
        print(f"❌ Input nicht gefunden: {args.input}")
        return 1
    
    # Batch-Verarbeitung oder einzelnes Video
    if args.batch or input_path.is_dir():
        success = process_multiple_videos(
            args.input, args.output,
            interval=args.interval,
            max_frames=args.max_frames
        )
    else:
        success = extract_frames(
            args.input, args.output,
            interval=args.interval,
            max_frames=args.max_frames
        )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())