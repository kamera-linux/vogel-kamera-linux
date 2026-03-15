# Raspberry Pi Bird Camera Daemon
# Cross-compile auf x86 mit:
#   docker buildx build --platform linux/arm64 \
#     -f docker/Dockerfile -t vogel-pi:latest .
#
# Build-Kontext = Repo-Root (nicht docker/)

FROM python:3.13-slim-bookworm

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

# Wrapper-Script: ruft rpicam-vid über den trixie Dynamic Linker auf,
# damit die trixie libc (aus /host/lib + /host/usr/lib) korrekt geladen wird ohne
# den bookworm-Python zu beeinflussen.
RUN printf '#!/bin/sh\nexec /host/lib/ld-linux-aarch64.so.1 --library-path /host/lib:/host/usr/lib:/host/usr/lib/pulseaudio /opt/rpicam-vid "$@"\n' \
    > /usr/local/bin/rpicam-vid && chmod +x /usr/local/bin/rpicam-vid

# Entrypoint: Einfaches Startskript (kein devicetree-Remount nötig – privileged: true im Container)
RUN printf '#!/bin/bash\nexec python3 /app/pi_daemon_secure.py\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

# ── Python-Abhängigkeiten ──────────────────────────────────────────────────
WORKDIR /app
COPY unified-monitor-client/requirements_daemon.txt .
RUN pip install --no-cache-dir -r requirements_daemon.txt

# Wrapper-Script: ruft das HOST-Python 3.13 (Trixie) via host ld-linux auf.
# host libs + host Python → gleiche glibc → kein GLIBC_PRIVATE Fehler.
# /host/usr/lib2 = Host /usr/lib (enthält z.B. libarmadillo.so.14 für picamera2)
RUN printf '#!/bin/sh\nexec /host/lib/ld-linux-aarch64.so.1 --library-path /host/lib:/host/usr/lib:/host/usr/lib2 /opt/python3-host "$@"\n' \
    > /usr/local/bin/python3-trixie && chmod +x /usr/local/bin/python3-trixie

# ── App-Code ───────────────────────────────────────────────────────────────
COPY unified-monitor-client/pi_daemon_secure.py .
COPY unified-monitor-client/web/               ./web/

# ── Raspberry-Pi-Skripte (werden vom Daemon als Subprocess gestartet) ──────
COPY raspberry-pi-scripts/unified-camera-monitor-detect-only.py \
     /home/roimme/vogel-kamera-linux/raspberry-pi-scripts/unified-camera-monitor-detect-only.py

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
