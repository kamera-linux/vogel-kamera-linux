#!/usr/bin/env python3
"""
container_health_monitor.py – Überwacht Gesundheit des pi-daemon Containers

Nutzen:
  python3 container_health_monitor.py      # Einmalige Kontrolle
  systemctl start pi-daemon-health-check   # Via systemd Timer
  systemctl status pi-daemon-health-check.service

Features:
  - Prüft Health-Status des pi-daemon Containers
  - Speichert Health-Historie in JSON-Log
  - Sendet Alerts bei Statusänderung (unhealthy → healthy oder umgekehrt)
  - Läuft auf dem Pi als cron/systemd-Timer
  - Optional: E-Mail/Webhook-Alerts (siehe ALERT_WEBHOOK)
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ─── Konfiguration ────────────────────────────────────────────────────────
LOG_DIR = Path("/var/log/pi-daemon")
LOG_FILE = LOG_DIR / "health_history.json"
STATUS_FILE = LOG_DIR / ".health_status"  # Letzter Status für State-Vergleich
ALERT_LOG = LOG_DIR / "health_alerts.log"

# Optional: Webhook für externe Alerts (z.B. Discord, Slack)
ALERT_WEBHOOK = os.environ.get("PI_DAEMON_ALERT_WEBHOOK")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(ALERT_LOG),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_container_health() -> dict | None:
    """Ruft Docker-Inspect auf und extrahiert Health-Status."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{json .State.Health}}", "pi-daemon"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            logger.warning(f"Docker inspect fehlgeschlagen: {result.stderr}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Container-Abfrage fehlgeschlagen: {e}")
        return None


def get_container_status() -> str | None:
    """Prüft ob Container läuft (running, paused, exited)."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", "pi-daemon"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception:
        return None


def record_health_check(status: str, details: dict | None = None) -> None:
    """Speichert Health-Check in JSON-Log."""
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "container_status": get_container_status(),
        "details": details or {},
    }
    
    # Anhängen an JSON-Array
    history = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f:
                history = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"{LOG_FILE} ist kein valides JSON, überschreibe")
            history = []
    
    history.append(entry)
    
    # Behalte nur letzte 1000 Einträge (12+ Stunden bei 30s-Check)
    if len(history) > 1000:
        history = history[-1000:]
    
    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=2)


def send_alert(old_status: str, new_status: str, reason: str = "") -> None:
    """Sendet Alert bei Statusänderung."""
    logger.warning(
        f"🚨 ALERT: pi-daemon Health {old_status} → {new_status}. Grund: {reason}"
    )
    
    if not ALERT_WEBHOOK:
        return
    
    # Optional: Discord/Slack Webhook
    try:
        import urllib.request
        
        color = "danger" if new_status == "unhealthy" else "good"
        emoji = "❌" if new_status == "unhealthy" else "✅"
        
        payload = json.dumps({
            "attachments": [{
                "color": color,
                "title": f"{emoji} pi-daemon Health Check",
                "text": f"Status: {old_status} → {new_status}\n{reason}",
                "timestamp": int(datetime.now().timestamp()),
            }]
        }).encode()
        
        req = urllib.request.Request(
            ALERT_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        logger.info(f"Alert gesendet an {ALERT_WEBHOOK}")
    except Exception as e:
        logger.error(f"Alert-Webhook fehlgeschlagen: {e}")


def main() -> int:
    """Hauptfunktion: Prüfe Container-Health."""
    # Lese letzten bekannten Status
    old_status = "unknown"
    if STATUS_FILE.exists():
        try:
            old_status = STATUS_FILE.read_text().strip()
        except Exception as e:
            logger.warning(f"Kann {STATUS_FILE} nicht lesen: {e}")
    
    # Prüfe aktuellen Status
    container_status = get_container_status()
    if not container_status:
        new_status = "stopped"
        reason = "Container nicht erreichbar"
    elif container_status != "running":
        new_status = container_status
        reason = f"Container Status: {container_status}"
    else:
        health = get_container_health()
        if not health:
            new_status = "unknown"
            reason = "Health-Daten nicht verfügbar"
        else:
            new_status = health.get("Status", "unknown")
            reason = f"Health-Status: {new_status}"
            
            # Extra Details bei unhealthy
            if new_status == "unhealthy":
                failing = health.get("FailingStreak", 0)
                reason += f" (failing streak: {failing})"
                
                # Letzter Health-Check Log
                logs = health.get("Log", [])
                if logs:
                    last_check = logs[-1]
                    reason += f"\nLetzter Check: {last_check.get('End', 'N/A')}, Exit-Code: {last_check.get('ExitCode', '?')}"
    
    # Speichern
    record_health_check(new_status, {"reason": reason})
    
    # Status-Datei aktualisieren
    STATUS_FILE.parent.mkdir(exist_ok=True, parents=True)
    STATUS_FILE.write_text(new_status)
    
    # Alert bei Statusänderung
    if new_status != old_status:
        send_alert(old_status, new_status, reason)
    
    # Return-Code: 0 wenn healthy, 1 wenn nicht
    return 0 if new_status == "healthy" else 1


if __name__ == "__main__":
    sys.exit(main())
