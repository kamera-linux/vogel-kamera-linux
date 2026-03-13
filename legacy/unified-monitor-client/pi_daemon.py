#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Daemon - Verwaltet ALLE Vogel-Kamera-Operationen lokal
HTTP REST API für lokale Prozesssteuerung

Läuft als systemd-Service auf dem Pi, antwortet auf HTTP-Anfragen vom Client
"""

import os
import sys
import subprocess
import threading
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/pi_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Globale States
class DaemonState:
    detection_running = False
    recording_running = False
    detection_process = None
    recording_process = None
    last_error = None
    recording_file = None

state = DaemonState()
lock = threading.Lock()


class CameraManager:
    """Verwaltet Camera-Operationen lokal auf Pi"""
    
    @staticmethod
    def start_detection():
        """Starte Detection-Prozess lokal"""
        with lock:
            if state.detection_running:
                logger.warning("Detection läuft bereits")
                return True
            
            try:
                logger.info("🟢 Starte Detection-Prozess...")
                cmd = [
                    'python3',
                    '/home/roimme/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-detect-only.py',
                    '--use-hailo'
                ]
                state.detection_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp  # Detach process group
                )
                state.detection_running = True
                logger.info(f"✅ Detection gestartet (PID: {state.detection_process.pid})")
                return True
            except Exception as e:
                logger.error(f"❌ Detection-Start fehlgeschlagen: {e}")
                state.last_error = str(e)
                return False
    
    @staticmethod
    def stop_detection():
        """Stoppe Detection-Prozess lokal"""
        with lock:
            if not state.detection_running:
                logger.info("Detection läuft nicht")
                return True
            
            try:
                logger.info("🛑 Stoppe Detection-Prozess...")
                os.killpg(os.getpgid(state.detection_process.pid), 15)  # SIGTERM
                state.detection_process.wait(timeout=5)
                state.detection_running = False
                logger.info("✅ Detection gestoppt")
                return True
            except Exception as e:
                logger.error(f"❌ Detection-Stop fehlgeschlagen: {e}")
                try:
                    os.killpg(os.getpgid(state.detection_process.pid), 9)  # SIGKILL
                except:
                    pass
                state.detection_running = False
                state.last_error = str(e)
                return False
    
    @staticmethod
    def record(duration_seconds=10, resolution='2k', fps=30, bitrate=6000):
        """Starte Recording LOKAL auf Pi"""
        with lock:
            if state.recording_running:
                logger.warning("Recording läuft bereits")
                return False, "Recording läuft bereits"
            
            # Stoppe Detection während Recording
            if state.detection_running:
                logger.info("🛑 Stoppe Detection für Recording...")
                os.killpg(os.getpgid(state.detection_process.pid), 15)
                try:
                    state.detection_process.wait(timeout=3)
                except:
                    os.killpg(os.getpgid(state.detection_process.pid), 9)
                state.detection_running = False
                time.sleep(1)  # Gebe libcamera Zeit zum Release
            
            try:
                logger.info(f"📹 Starte Recording ({duration_seconds}s @ {resolution})...")
                
                # Resolution mapping
                res_map = {
                    '480p': (854, 480),
                    '720p': (1280, 720),
                    '1080p': (1920, 1080),
                    '2k': (2560, 1440),
                    '4k': (4096, 2160)
                }
                w, h = res_map.get(resolution, (2560, 1440))
                
                # Erstelle Output-Verzeichnis
                recording_dir = Path.home() / "Videos" / "Vogelhaus" / "AI-HAD"
                recording_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_file = recording_dir / f"recording_{timestamp}.h264"
                audio_file = recording_dir / f"recording_{timestamp}.wav"
                
                # Starte rpicam-vid + arecord PARALLEL
                video_cmd = [
                    'rpicam-vid',
                    '-t', str(duration_seconds * 1000),
                    '-w', str(w),
                    '-h', str(h),
                    '-fps', str(fps),
                    '--bitrate', str(bitrate * 1000),
                    '-o', str(video_file),
                    '--inline'
                ]
                
                audio_cmd = [
                    'arecord',
                    '-f', 'S16_LE',
                    '-r', '44100',
                    '-d', str(duration_seconds),
                    str(audio_file)
                ]
                
                logger.info(f"   Video: {video_file.name}")
                logger.info(f"   Audio: {audio_file.name}")
                
                # Starte beide prozesse parallel
                state.recording_process = subprocess.Popen(
                    video_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                audio_proc = subprocess.Popen(
                    audio_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                state.recording_running = True
                logger.info(f"   Recording PID: {state.recording_process.pid}")
                
                # Warte auf Completion
                state.recording_process.wait()
                audio_proc.wait()
                
                state.recording_running = False
                
                # Checke ob Files erstellt wurden
                if video_file.exists() and audio_file.exists():
                    state.recording_file = {
                        'video': str(video_file),
                        'audio': str(audio_file),
                        'timestamp': timestamp
                    }
                    logger.info(f"✅ Recording abgeschlossen: {video_file.name}")
                    return True, state.recording_file
                else:
                    logger.error(f"❌ Video/Audio nicht erstellt")
                    return False, "Video/Audio nicht erstellt"
                    
            except Exception as e:
                logger.error(f"❌ Recording fehlgeschlagen: {e}")
                state.recording_running = False
                state.last_error = str(e)
                return False, str(e)
            finally:
                # Starte Detection wieder
                CameraManager.start_detection()
    
    @staticmethod
    def convert_to_mp4():
        """Konvertiere H.264→MP4"""
        if not state.recording_file:
            return False, "Keine Recording-Datei"
        
        try:
            video_file = Path(state.recording_file['video'])
            audio_file = Path(state.recording_file['audio'])
            mp4_file = video_file.with_suffix('.mp4')
            
            logger.info(f"🔄 Konvertiere zu MP4...")
            
            cmd = [
                'ffmpeg',
                '-i', str(video_file),
                '-i', str(audio_file),
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-c:a', 'aac',
                '-y',
                str(mp4_file)
            ]
            
            proc = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if proc.returncode == 0 and mp4_file.exists():
                logger.info(f"✅ Konvertierung fertig: {mp4_file.name}")
                state.recording_file['mp4'] = str(mp4_file)
                return True, str(mp4_file)
            else:
                logger.error(f"❌ Konvertierung fehlgeschlagen")
                return False, proc.stderr.decode()
        except Exception as e:
            logger.error(f"❌ Conversion Exception: {e}")
            return False, str(e)


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler für Daemon API"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == '/status':
            self._respond_json(200, {
                'detection_running': state.detection_running,
                'recording_running': state.recording_running,
                'last_error': state.last_error,
                'recording_file': state.recording_file
            })
        
        elif path == '/start-detection':
            success = CameraManager.start_detection()
            self._respond_json(200 if success else 500, {
                'success': success,
                'message': 'Detection gestartet' if success else 'Detection-Start fehlgeschlagen'
            })
        
        elif path == '/stop-detection':
            success = CameraManager.stop_detection()
            self._respond_json(200 if success else 500, {
                'success': success,
                'message': 'Detection gestoppt' if success else 'Detection-Stop fehlgeschlagen'
            })
        
        elif path.startswith('/record'):
            qs = parse_qs(urlparse(self.path).query)
            duration = int(qs.get('duration', [10])[0])
            resolution = qs.get('resolution', ['2k'])[0]
            fps = int(qs.get('fps', [30])[0])
            bitrate = int(qs.get('bitrate', [6000])[0])
            
            success, result = CameraManager.record(duration, resolution, fps, bitrate)
            self._respond_json(200 if success else 500, {
                'success': success,
                'result': result if success else None,
                'error': result if not success else None
            })
        
        elif path == '/convert':
            success, result = CameraManager.convert_to_mp4()
            self._respond_json(200 if success else 500, {
                'success': success,
                'mp4_file': result if success else None,
                'error': result if not success else None
            })
        
        else:
            self._respond_json(404, {'error': 'Unbekannter Endpoint'})
    
    def _respond_json(self, status, data):
        """Sende JSON Response"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(response))
        self.end_headers()
        self.wfile.write(response)
    
    def log_message(self, format, *args):
        """Suppress HTTP server logging"""
        pass


def run_daemon(port=8888):
    """Starte HTTP Daemon"""
    logger.info(f"🚀 PI DAEMON startet auf Port {port}...")
    
    # Starte Detection beim Start
    CameraManager.start_detection()
    
    # Starte HTTP Server
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    logger.info(f"✅ HTTP Server läuft auf port {port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Daemon beendet")
        CameraManager.stop_detection()
        sys.exit(0)


if __name__ == '__main__':
    run_daemon()
