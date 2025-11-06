#!/usr/bin/env python3
"""
Analysiert MP4-Videos und berechnet den Vogelanteil

Dieses Skript:
- Lädt ein oder mehrere MP4-Videos
- Analysiert jeden Frame mit YOLOv8 auf Vogelerkennung
- Berechnet Statistiken über Vogelpräsenz
- Erstellt einen detaillierten Report

Verwendung:
    python3 analyze_video_bird_content.py video.mp4
    python3 analyze_video_bird_content.py *.mp4
    python3 analyze_video_bird_content.py --threshold 0.3 --model bird-species video.mp4
"""

import argparse
import cv2
import sys
from pathlib import Path
from datetime import timedelta, datetime
from ultralytics import YOLO
import json

__version__ = "1.0.0"


class TeeOutput:
    """Schreibt Output gleichzeitig in stdout und Log-Datei"""
    
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, 'w', encoding='utf-8')
        
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.flush()
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()
        
    def close(self):
        self.log.close()
        sys.stdout = self.terminal


class VideoAnalyzer:
    """Analysiert Videos auf Vogelanteil"""
    
    def __init__(self, model_path="yolov8n.pt", threshold=0.5, target_class=14):
        """
        Initialisiert den Analyzer
        
        Args:
            model_path: Pfad zum YOLO-Modell (sucht in: models/, config/models/, aktuelles Verzeichnis, Cache)
            threshold: Konfidenz-Schwellenwert (0.0-1.0)
            target_class: COCO-Klasse für Vogel (14=bird)
        """
        # Suche Modell in verschiedenen Verzeichnissen
        model_path = self._find_model(model_path)
        print(f"🤖 Lade YOLO-Modell: {model_path}")
        self.model = YOLO(model_path)
        self.threshold = threshold
        self.target_class = target_class
    
    def _find_model(self, model_name):
        """
        Sucht Modell in verschiedenen Verzeichnissen
        
        Suchpfade (in dieser Reihenfolge):
        1. models/
        2. config/models/
        3. Aktuelles Verzeichnis
        4. Lässt Ultralytics automatisch herunterladen
        
        Args:
            model_name: Name oder Pfad des Modells
            
        Returns:
            Pfad zum Modell oder Original-Name für Auto-Download
        """
        # Wenn absoluter Pfad angegeben wurde
        if Path(model_name).is_absolute() and Path(model_name).exists():
            return model_name
        
        # Suchpfade definieren
        search_paths = [
            Path('models') / model_name,
            Path('config/models') / model_name,
            Path(model_name)
        ]
        
        # Suche in den Verzeichnissen
        for path in search_paths:
            if path.exists():
                return str(path)
        
        # Nicht gefunden → Ultralytics lädt automatisch herunter
        print(f"   ℹ️  Modell '{model_name}' nicht lokal gefunden, wird automatisch heruntergeladen...")
        return model_name
        
    def analyze_video(self, video_path, sample_rate=1):
        """
        Analysiert ein Video Frame für Frame
        
        Args:
            video_path: Pfad zum MP4-Video
            sample_rate: Analysiere jeden N-ten Frame (1=alle, 2=jeden 2., etc.)
            
        Returns:
            dict mit Statistiken
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video nicht gefunden: {video_path}")
            
        print(f"\n📹 Analysiere: {video_path.name}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Kann Video nicht öffnen: {video_path}")
            
        # Video-Eigenschaften
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"   📊 Video-Info: {width}x{height}, {fps:.1f} FPS, {duration:.1f}s, {total_frames} Frames")
        
        # Analyse-Variablen
        frames_analyzed = 0
        frames_with_birds = 0
        bird_detections = []
        current_frame = 0
        
        # Progress
        print(f"   🔍 Analysiere jeden {sample_rate}. Frame...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            current_frame += 1
            
            # Sample-Rate anwenden
            if current_frame % sample_rate != 0:
                continue
                
            frames_analyzed += 1
            
            # YOLO-Inferenz
            results = self.model(frame, verbose=False)
            
            # Vogel-Detektion prüfen
            birds_in_frame = 0
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls == self.target_class and conf >= self.threshold:
                        birds_in_frame += 1
                        
            if birds_in_frame > 0:
                frames_with_birds += 1
                timestamp = current_frame / fps if fps > 0 else 0
                bird_detections.append({
                    'frame': current_frame,
                    'timestamp': timestamp,
                    'birds': birds_in_frame
                })
                
            # Progress alle 30 analysierten Frames
            if frames_analyzed % 30 == 0:
                progress = (frames_analyzed * sample_rate / total_frames) * 100
                print(f"   ⏳ {progress:.1f}% ({frames_analyzed}/{total_frames//sample_rate} Frames)", end='\r')
                
        cap.release()
        
        # Statistiken berechnen
        bird_percentage = (frames_with_birds / frames_analyzed * 100) if frames_analyzed > 0 else 0
        
        # Kontinuierliche Vogel-Segmente finden
        segments = self._find_bird_segments(bird_detections, fps, sample_rate)
        
        stats = {
            'video_file': video_path.name,
            'video_path': str(video_path),
            'resolution': f"{width}x{height}",
            'fps': fps,
            'duration_seconds': duration,
            'total_frames': total_frames,
            'frames_analyzed': frames_analyzed,
            'sample_rate': sample_rate,
            'frames_with_birds': frames_with_birds,
            'bird_percentage': bird_percentage,
            'bird_detections': len(bird_detections),
            'bird_segments': segments,
            'threshold': self.threshold,
            'model': str(self.model.ckpt_path if hasattr(self.model, 'ckpt_path') else 'unknown')
        }
        
        print(f"\n   ✅ Analyse abgeschlossen!")
        return stats
        
    def _find_bird_segments(self, detections, fps, sample_rate):
        """
        Findet kontinuierliche Zeitabschnitte mit Vogel-Präsenz
        
        Args:
            detections: Liste von Vogel-Detektionen
            fps: Video FPS
            sample_rate: Frame-Sample-Rate
            
        Returns:
            Liste von Segmenten mit Start/Ende-Zeiten
        """
        if not detections:
            return []
            
        segments = []
        current_segment = None
        max_gap = 2.0 * sample_rate  # Max 2 Sekunden Lücke
        
        for detection in detections:
            timestamp = detection['timestamp']
            
            if current_segment is None:
                # Neues Segment starten
                current_segment = {
                    'start': timestamp,
                    'end': timestamp,
                    'detections': 1
                }
            elif timestamp - current_segment['end'] <= max_gap:
                # Segment erweitern
                current_segment['end'] = timestamp
                current_segment['detections'] += 1
            else:
                # Segment beenden und neues starten
                segments.append(current_segment)
                current_segment = {
                    'start': timestamp,
                    'end': timestamp,
                    'detections': 1
                }
                
        # Letztes Segment hinzufügen
        if current_segment:
            segments.append(current_segment)
            
        return segments
        
    def print_report(self, stats):
        """
        Gibt einen formatierten Report aus
        
        Args:
            stats: Statistik-Dictionary
        """
        print("\n" + "="*70)
        print(f"📊 VOGEL-ANALYSE REPORT")
        print("="*70)
        
        print(f"\n📹 Video: {stats['video_file']}")
        print(f"   Pfad: {stats['video_path']}")
        print(f"   Auflösung: {stats['resolution']}")
        print(f"   FPS: {stats['fps']:.1f}")
        print(f"   Dauer: {timedelta(seconds=int(stats['duration_seconds']))}")
        
        print(f"\n🔍 Analyse:")
        print(f"   Frames gesamt: {stats['total_frames']}")
        print(f"   Frames analysiert: {stats['frames_analyzed']} (Sample-Rate: 1/{stats['sample_rate']})")
        print(f"   Threshold: {stats['threshold']}")
        print(f"   Modell: {stats['model']}")
        
        print(f"\n🐦 Ergebnisse:")
        print(f"   Frames mit Vögeln: {stats['frames_with_birds']} / {stats['frames_analyzed']}")
        print(f"   Vogelanteil: {stats['bird_percentage']:.1f}%")
        print(f"   Detektionen: {stats['bird_detections']}")
        
        if stats['bird_segments']:
            print(f"\n⏱️  Vogel-Segmente ({len(stats['bird_segments'])}):")
            for i, segment in enumerate(stats['bird_segments'], 1):
                start = timedelta(seconds=int(segment['start']))
                end = timedelta(seconds=int(segment['end']))
                duration = segment['end'] - segment['start']
                print(f"   {i}. {start} - {end} ({duration:.1f}s, {segment['detections']} Detektionen)")
        else:
            print(f"\n❌ Keine Vögel erkannt")
            
        print("\n" + "="*70)
        
    def save_report(self, stats, output_path):
        """
        Speichert Report als JSON
        
        Args:
            stats: Statistik-Dictionary
            output_path: Ausgabe-Pfad
        """
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Report gespeichert: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Analysiert MP4-Videos auf Vogelanteil',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einzelnes Video analysieren
  python3 analyze_video_bird_content.py video.mp4
  
  # Mehrere Videos
  python3 analyze_video_bird_content.py video1.mp4 video2.mp4
  
  # Alle MP4s im Verzeichnis
  python3 analyze_video_bird_content.py ~/Videos/Vogelhaus/AI-HAD/*/*.mp4
  
  # Mit custom Threshold und eigenem Modell (sucht in models/ oder config/models/)
  python3 analyze_video_bird_content.py --threshold 0.3 --model bird-species.pt video.mp4
  
  # Schnellere Analyse (jeden 5. Frame)
  python3 analyze_video_bird_content.py --sample-rate 5 video.mp4
  
  # Report als JSON speichern
  python3 analyze_video_bird_content.py --output report.json video.mp4
  
  # Verzeichnisse mit 0% Vogelanteil automatisch löschen
  python3 analyze_video_bird_content.py --delete --sample-rate 5 *.mp4
  
  # Output in Log-Datei speichern
  python3 analyze_video_bird_content.py --log *.mp4
        """
    )
    
    parser.add_argument('videos', nargs='+', help='MP4-Video(s) zum Analysieren')
    parser.add_argument('--model', default='yolov8n.pt', help='YOLO-Modell (Standard: yolov8n.pt)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Konfidenz-Threshold (Standard: 0.5)')
    parser.add_argument('--sample-rate', type=int, default=1, help='Analysiere jeden N-ten Frame (Standard: 1)')
    parser.add_argument('--output', '-o', help='Speichere Report als JSON')
    parser.add_argument('--delete', action='store_true', help='Lösche Verzeichnisse mit 0%% Vogelanteil automatisch')
    parser.add_argument('--log', action='store_true', help='Speichere Konsolen-Output in Log-Datei')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Log-Datei einrichten wenn gewünscht
    tee_output = None
    if args.log:
        try:
            # Erstelle Log-Verzeichnis-Struktur: /var/log/vogel-kamera-linux/yy/kw/
            now = datetime.now()
            year = now.strftime('%Y')
            week = now.strftime('%V')  # ISO Kalenderwoche
            timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
            
            log_dir = Path(f'/var/log/vogel-kamera-linux/{year}/{week}')
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f'{timestamp}-analyse.log'
            
            # Umleitung einrichten
            tee_output = TeeOutput(log_file)
            sys.stdout = tee_output
            
            print(f"📝 Log-Datei: {log_file}")
            print("="*70 + "\n")
        except PermissionError:
            print("⚠️  WARNUNG: Keine Schreibrechte für /var/log/vogel-kamera-linux/", file=sys.stderr)
            print("   Führe das Skript mit sudo aus oder ändere die Berechtigungen:", file=sys.stderr)
            print("   sudo mkdir -p /var/log/vogel-kamera-linux && sudo chown $USER /var/log/vogel-kamera-linux", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Log-Datei: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        # Analyzer initialisieren
        analyzer = VideoAnalyzer(
            model_path=args.model,
            threshold=args.threshold
        )
        
        # Videos analysieren
        all_stats = []
        for video_path in args.videos:
            try:
                stats = analyzer.analyze_video(video_path, sample_rate=args.sample_rate)
                analyzer.print_report(stats)
                all_stats.append(stats)
            except Exception as e:
                print(f"❌ Fehler bei {video_path}: {e}", file=sys.stderr)
                continue
                
        # Gesamt-Statistik bei mehreren Videos
        if len(all_stats) > 1:
            total_videos = len(all_stats)
            total_duration = sum(s['duration_seconds'] for s in all_stats)
            avg_bird_percentage = sum(s['bird_percentage'] for s in all_stats) / total_videos
            total_frames_analyzed = sum(s['frames_analyzed'] for s in all_stats)
            total_frames_with_birds = sum(s['frames_with_birds'] for s in all_stats)
            
            print("\n" + "="*70)
            print(f"📊 GESAMT-STATISTIK ({total_videos} Videos)")
            print("="*70)
            print(f"   Gesamt-Dauer: {timedelta(seconds=int(total_duration))}")
            print(f"   Gesamt Frames analysiert: {total_frames_analyzed}")
            print(f"   Gesamt Frames mit Vögeln: {total_frames_with_birds}")
            print(f"   Durchschnittlicher Vogelanteil: {avg_bird_percentage:.1f}%")
            
            print(f"\n📋 Video-Übersicht:")
            print(f"   {'Nr.':<4} {'Verzeichnis':<70} {'Vogel':<6} {'Vogel%':<8} {'Frames':<12} {'Dauer':<8}")
            print(f"   {'-'*4} {'-'*70} {'-'*6} {'-'*8} {'-'*12} {'-'*8}")
            
            for i, stats in enumerate(all_stats, 1):
                # Zeige Verzeichnisname statt Dateiname
                video_path = Path(stats['video_path'])
                directory_name = video_path.parent.name
                # Status-Icon: ✅ wenn Vögel erkannt, ❌ wenn keine
                status = "✅" if stats['frames_with_birds'] > 0 else "❌"
                bird_pct = f"{stats['bird_percentage']:.1f}%"
                frames_info = f"{stats['frames_with_birds']}/{stats['frames_analyzed']}"
                duration = f"{int(stats['duration_seconds'])}s"
                
                print(f"   {i:<4} {directory_name:<70} {status:<6} {bird_pct:<8} {frames_info:<12} {duration:<8}")
            
            print("="*70)
            
        # Automatisches Löschen von Videos ohne Vögel
        if args.delete and len(all_stats) > 0:
            import shutil
            
            videos_to_delete = [s for s in all_stats if s['bird_percentage'] == 0.0]
            
            if videos_to_delete:
                print("\n" + "="*70)
                print(f"🗑️  LÖSCHE VERZEICHNISSE MIT 0% VOGELANTEIL ({len(videos_to_delete)} Videos)")
                print("="*70)
                
                for stats in videos_to_delete:
                    video_path = Path(stats['video_path'])
                    directory = video_path.parent
                    
                    try:
                        print(f"   🗑️  Lösche: {directory.name}")
                        shutil.rmtree(directory)
                        print(f"      ✅ Erfolgreich gelöscht")
                    except Exception as e:
                        print(f"      ❌ Fehler beim Löschen: {e}")
                        
                print(f"\n   Gelöschte Verzeichnisse: {len(videos_to_delete)}")
                print(f"   Verbleibende Videos: {len(all_stats) - len(videos_to_delete)}")
                print("="*70)
            else:
                print("\n✅ Keine Videos mit 0% Vogelanteil zum Löschen gefunden")
        
        # JSON-Output
        if args.output:
            output_data = all_stats[0] if len(all_stats) == 1 else {
                'videos': all_stats,
                'summary': {
                    'total_videos': len(all_stats),
                    'total_duration': sum(s['duration_seconds'] for s in all_stats),
                    'average_bird_percentage': sum(s['bird_percentage'] for s in all_stats) / len(all_stats)
                }
            }
            analyzer.save_report(output_data, args.output)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse abgebrochen")
        if tee_output:
            tee_output.close()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fehler: {e}", file=sys.stderr)
        if tee_output:
            tee_output.close()
        sys.exit(1)
    finally:
        # Log-Datei ordentlich schließen
        if tee_output:
            tee_output.close()


if __name__ == '__main__':
    main()
