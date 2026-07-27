#!/usr/bin/env python3
"""
Docker Health-Monitor für pi-daemon Container
─────────────────────────────────────────────────
Überwacht den Health-Status des Docker-Containers und alarmiert bei Problemen.

Verwendung:
  python3 scripts/docker_health_monitor.py                 # Once (für Cron)
  python3 scripts/docker_health_monitor.py --daemon        # Continuous monitoring (systemd Service)
  python3 scripts/docker_health_monitor.py --test          # Test-Alert senden

Features:
  • Docker Health-Status-Änderungen tracken
  • Persistente History in /var/log/pi-daemon/health.log
  • Alert-Mechanismen: Logfile, Email (optional)
  • Failure-Streak Tracking (mehrere Fehler = kritisch)
"""

import argparse
import datetime
import json
import logging
import os
import re
import smtplib
import socket
import subprocess
import sys
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


# ─── Konfiguration ────────────────────────────────────────────────────────────
CONTAINER_NAME = "pi-daemon"
LOG_DIR = Path("/var/log/pi-daemon")
LOG_FILE = LOG_DIR / "health.log"
STATE_FILE = LOG_DIR / ".health_state.json"
CHECK_INTERVAL = 30  # Sekunden (für --daemon Modus)
FAILURE_THRESHOLD = 3  # Alerts nach 3+ consecutiven Fehlern

# Email-Konfiguration (optional, kann leer sein)
ALERT_EMAIL_FROM = os.getenv("PI_DAEMON_ALERT_EMAIL", "").strip()
ALERT_EMAIL_TO = os.getenv("PI_DAEMON_ALERT_RECIPIENT", "").strip()
SMTP_SERVER = os.getenv("PI_DAEMON_SMTP_SERVER", "localhost").strip()
SMTP_PORT = int(os.getenv("PI_DAEMON_SMTP_PORT", "25"))

# ─── Logging ──────────────────────────────────────────────────────────────────
def setup_logging():
    """Setup Logging zu Datei und Konsole"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Datei-Handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Konsolen-Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers = []
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ─── State-Management ─────────────────────────────────────────────────────────
def load_state() -> dict:
    """Lade persiste Health-State aus Datei"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"State-Datei beschädigt: {e}, zurücksetzen")
    
    return {
        "last_status": None,
        "last_timestamp": None,
        "failure_streak": 0,
        "alerted": False,
    }


def save_state(state: dict):
    """Speichere Health-State"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ─── Docker Health Check ──────────────────────────────────────────────────────
def get_container_health() -> dict:
    """
    Lese Container Health-Status aus Docker API
    
    Returns:
        {
            'status': 'healthy' | 'unhealthy' | 'starting' | 'error',
            'failing_streak': int,
            'output': str,
            'timestamp': str,
        }
    """
    try:
        # docker inspect {container} -f '{{json .State.Health}}'
        result = subprocess.run(
            ['docker', 'inspect', CONTAINER_NAME, '-f', '{{json .State.Health}}'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode != 0:
            return {
                'status': 'error',
                'failing_streak': 0,
                'output': f"Container nicht gefunden: {result.stderr}",
                'timestamp': datetime.datetime.now().isoformat(),
            }
        
        health_json = json.loads(result.stdout)
        status = health_json.get('Status', 'unknown').lower()
        
        return {
            'status': status,
            'failing_streak': health_json.get('FailingStreak', 0),
            'output': health_json.get('Log', [])[-1].get('Output', '') if health_json.get('Log') else '',
            'timestamp': datetime.datetime.now().isoformat(),
        }
    
    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'failing_streak': 0,
            'output': "docker inspect timeout",
            'timestamp': datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            'status': 'error',
            'failing_streak': 0,
            'output': str(e),
            'timestamp': datetime.datetime.now().isoformat(),
        }


# ─── Alerting ─────────────────────────────────────────────────────────────────
def send_alert(subject: str, message: str):
    """Sende Alert via Email (optional) und Log"""
    logger.error(f"🚨 ALERT: {subject}\n{message}")
    
    # Email-Alert (optional)
    if ALERT_EMAIL_FROM and ALERT_EMAIL_TO:
        try:
            msg = MIMEMultipart()
            msg['From'] = ALERT_EMAIL_FROM
            msg['To'] = ALERT_EMAIL_TO
            msg['Subject'] = f"[pi-daemon Health Alert] {subject}"
            
            hostname = socket.gethostname()
            body = f"""
Hostname: {hostname}
Zeit: {datetime.datetime.now().isoformat()}

{subject}

────────────────────────────────────────
{message}
────────────────────────────────────────

Container-Logs:
docker logs --tail=50 pi-daemon

Health-Status:
docker inspect -f '{{.State.Health}}' pi-daemon
"""
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
                logger.info(f"Email-Alert gesendet an {ALERT_EMAIL_TO}")
        
        except Exception as e:
            logger.error(f"Email-Alert fehlgeschlagen: {e}")


# ─── Monitoring-Logik ─────────────────────────────────────────────────────────
def check_health():
    """Führe einmaligen Health-Check durch"""
    current = get_container_health()
    state = load_state()
    
    timestamp = current['timestamp']
    
    # Log aktuellen Status
    logger.info(
        f"Status: {current['status']} | "
        f"Failing-Streak: {current['failing_streak']} | "
        f"Output: {current['output'][:100] if current['output'] else 'ok'}"
    )
    
    # Status-Änderung oder Schwelle überschritten
    status_changed = current['status'] != state.get('last_status')
    
    if current['status'] in ['unhealthy', 'error']:
        state['failure_streak'] = (state.get('failure_streak', 0) or 0) + 1
        
        # Alert bei Schwellen-Überschreitung
        if state['failure_streak'] >= FAILURE_THRESHOLD and not state.get('alerted'):
            send_alert(
                f"Container unhealthy ({state['failure_streak']} Fehler)",
                f"""
Status: {current['status']}
Failing-Streak: {current['failing_streak']}
Konsekutive Fehler: {state['failure_streak']}
Output: {current['output']}

Mögliche Lösungen:
1. Container-Logs prüfen: docker logs --tail=200 pi-daemon
2. Ressourcen prüfen: docker stats pi-daemon
3. Health-Check ist zu streng? Timeouts erhöhen (Dockerfile)
4. Container manuell neu starten: docker restart pi-daemon
"""
            )
            state['alerted'] = True
    
    elif current['status'] == 'healthy':
        # Recovery von unhealthy → healthy
        if state.get('failure_streak', 0) > 0:
            logger.warning(
                f"✅ Container wiederhergestellt nach {state['failure_streak']} Fehler(n)"
            )
            send_alert(
                "Container wieder healthy ✅",
                f"Der Container hat sich nach {state['failure_streak']} Fehler(n) wiederhergestellt."
            )
        
        state['failure_streak'] = 0
        state['alerted'] = False
    
    # State aktualisieren
    state['last_status'] = current['status']
    state['last_timestamp'] = timestamp
    save_state(state)


def monitor_daemon():
    """Kontinuierliches Monitoring (für systemd Service)"""
    logger.info(f"🐦 Docker Health-Monitor startet (Intervall: {CHECK_INTERVAL}s)")
    
    try:
        while True:
            check_health()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Monitor beendet")
        sys.exit(0)


def test_alert():
    """Sende Test-Alert"""
    logger.info("📤 Sende Test-Alert...")
    send_alert(
        "Test-Alert vom Docker Health-Monitor",
        "Dies ist ein Test-Alert. Das System funktioniert normal."
    )


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Docker Health-Monitor für pi-daemon",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Kontinuierliches Monitoring-Modus (für systemd)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test-Alert senden'
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_alert()
    elif args.daemon:
        monitor_daemon()
    else:
        # Einmaliger Check (für Cron)
        check_health()


if __name__ == '__main__':
    main()
