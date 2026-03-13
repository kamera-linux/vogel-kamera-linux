# Raspberry Pi Bird Camera Daemon
# Cross-compile auf x86 mit:
#   docker buildx build --platform linux/arm64 \
#     -f docker/Dockerfile -t vogel-pi:latest .
#
# Build-Kontext = Repo-Root (nicht docker/)

FROM --platform=linux/arm64 python:3.11-slim-bookworm

# ── System-Pakete ──────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      alsa-utils \
      curl \
      gpg \
      ca-certificates \
      openssh-client \
      rsync \
    && curl -fsSL https://archive.raspberrypi.com/debian/raspberrypi.gpg.key \
       | gpg --dearmor -o /usr/share/keyrings/raspberrypi-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] \
       https://archive.raspberrypi.com/debian/ bookworm main" \
       > /etc/apt/sources.list.d/raspi.list \
    && apt-get update && apt-get install -y --no-install-recommends \
      rpicam-apps \
    && rm -rf /var/lib/apt/lists/*

# ── Python-Abhängigkeiten ──────────────────────────────────────────────────
WORKDIR /app
COPY unified-monitor-client/requirements_daemon.txt .
RUN pip install --no-cache-dir -r requirements_daemon.txt

# ── App-Code ───────────────────────────────────────────────────────────────
COPY unified-monitor-client/pi_daemon_secure.py .
COPY unified-monitor-client/web/               ./web/

# ── Raspberry-Pi-Skripte (werden vom Daemon als Subprocess gestartet) ──────
COPY raspberry-pi-scripts/unified-camera-monitor-detect-only.py \
     /home/roimme/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-detect-only.py

# ── Nicht-root User ────────────────────────────────────────────────────────
RUN groupadd -r appuser \
    && useradd -r -g appuser -G video,audio appuser
USER appuser

EXPOSE 8443

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request, ssl; \
    ctx=ssl.create_default_context(); ctx.check_hostname=False; \
    ctx.verify_mode=ssl.CERT_NONE; \
    urllib.request.urlopen('https://localhost:8443/', context=ctx)"

CMD ["python3", "pi_daemon_secure.py"]
