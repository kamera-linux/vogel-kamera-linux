# Raspberry Pi Bird Camera Daemon
# Cross-compile auf x86 mit:
#   docker buildx build --platform linux/arm64 \
#     -f docker/Dockerfile -t vogel-pi:latest .
#
# Build-Kontext = Repo-Root (nicht docker/)

FROM python:3.13-slim-trixie

# ── System-Pakete ──────────────────────────────────────────────────────────
# rpicam-apps wird NICHT im Container installiert –
# /usr/bin/rpicam-vid und /lib/aarch64-linux-gnu werden per Bind-Mount
# aus dem Pi-Host eingebunden (docker-compose.yml volumes).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      alsa-utils \
      curl \
      ca-certificates \
      openssh-client \
      rsync \
      libgl1 \
      libglib2.0-0 \
      libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Wrapper-Scripts: Trixie-Base teilt dieselbe glibc wie der Pi-Host (Trixie).
# Kein ld-linux.so.1-Trick mehr nötig – einfaches LD_LIBRARY_PATH reicht.

# rpicam-vid: Host-Binary mit Host-Libs (libcamera, libpisp etc.)
RUN printf '#!/bin/sh\nexport LD_LIBRARY_PATH=/host/lib:/host/usr/lib:/host/usr/lib/pulseaudio\nexec /opt/rpicam-vid "$@"\n' \
    > /usr/local/bin/rpicam-vid && chmod +x /usr/local/bin/rpicam-vid

# rpicam-hello: Hailo-NPU Detection; dlopen() findet hailo-postproc.so über LD_LIBRARY_PATH
RUN printf '#!/bin/sh\nexport LD_LIBRARY_PATH=/host/lib:/host/usr/lib:/host/usr/lib2:/host/usr/lib/pulseaudio\nexec /opt/rpicam-hello "$@"\n' \
    > /usr/local/bin/rpicam-hello && chmod +x /usr/local/bin/rpicam-hello

# rpicam-still: Snapshot-Aufnahme
RUN printf '#!/bin/sh\nexport LD_LIBRARY_PATH=/host/lib:/host/usr/lib\nexec /opt/rpicam-still "$@"\n' \
    > /usr/local/bin/rpicam-still && chmod +x /usr/local/bin/rpicam-still

# Entrypoint: Einfaches Startskript (kein devicetree-Remount nötig – privileged: true im Container)
RUN printf '#!/bin/bash\nexec python3 /app/pi_daemon_secure.py\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

# ── Python-Abhängigkeiten ──────────────────────────────────────────────────
WORKDIR /app
COPY unified-monitor-client/requirements_daemon.txt .
RUN pip install --no-cache-dir -r requirements_daemon.txt

# Wrapper-Script: Host-Python 3.13 (Trixie) mit Host-Libs (picamera2, libcamera, ultralytics).
# Trixie-Base teilt dieselbe glibc wie der Host → kein ld-linux.so.1-Trick nötig.
RUN printf '#!/bin/sh\nexport LD_LIBRARY_PATH=/host/lib:/host/usr/lib:/host/usr/lib2\nexec /opt/python3-host "$@"\n' \
    > /usr/local/bin/python3-trixie && chmod +x /usr/local/bin/python3-trixie

# ── App-Code ───────────────────────────────────────────────────────────────
COPY unified-monitor-client/pi_daemon_secure.py .
COPY unified-monitor-client/web/               ./web/

# ── Raspberry-Pi-Skripte (werden vom Daemon als Subprocess gestartet) ──────
COPY raspberry-pi-scripts/unified-camera-monitor-detect-only.py \
     /home/roimme/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-detect-only.py
# Hailo-NPU Detection-Script (Standard ab v2.3.0 – ersetzt CPU-YOLO)
COPY raspberry-pi-scripts/unified-camera-monitor-hailo.py \
     /home/roimme/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-hailo.py
# Nicht-root User anlegen (wird nicht aktiviert: dedizierte, privilegierte Kamera
# benötigt root für sysfs-Kamera-Reset /sys/bus/i2c/drivers/imx708/unbind)
RUN groupadd -r appuser \
    && useradd -r -g appuser -G video,audio appuser
# USER appuser  ← bewusst als root laufen (privileged container, dedizierter Pi)

EXPOSE 8443

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request, ssl; \
    ctx=ssl.create_default_context(); ctx.check_hostname=False; \
    ctx.verify_mode=ssl.CERT_NONE; \
    urllib.request.urlopen('https://localhost:8443/', context=ctx)"

ENTRYPOINT ["/entrypoint.sh"]
