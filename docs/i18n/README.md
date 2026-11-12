# 🐦 Bird Camera Linux (vogel-kamera-linux)

**Languages / Sprachen / 言語:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md) | [🇯🇵 日本語](README.ja.md)

> **The project documentation is maintained in German.** This page is a short English
> summary. For details, use the links below with your browser's translation feature.

## What it is

A bird-watching camera built on a **Raspberry Pi 5** with the **AI HAT+ (Hailo-8)**. A YOLOv8
model on the NPU detects birds (or people, dogs, cats) and starts a recording automatically.
Everything is operated from a web interface in the browser.

- **Automatic recording** on detection, or manual recording from 10 seconds to 10 minutes
- **Video up to 4K** with sound, two slow-motion profiles, audio-only recording
- **Web interface** over HTTPS with password + TOTP login; play, download and delete recordings
- **Automatic transfer** of recordings to other machines via rsync/SSH
- **Power bank monitoring** over Bluetooth with low-battery warning and clean shutdown
- **Optional monitoring** with Prometheus and Grafana, directly on the Pi
- **One-command deployment** from your own machine with Ansible and Docker

## Quick start

```bash
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
cp ansible/.env.example ansible/.env   # set the Pi's address, user and SSH key
./ansible/build_and_deploy.sh --install
# then open https://<pi-host>:8443/
```

## Documentation (German)

| Topic | Where |
|-------|-------|
| Overview, features, quick start | [README.md](../../README.md) |
| Step-by-step guides | [Wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki) |
| Architecture | [ARCHITEKTUR.md](../ARCHITEKTUR.md) |
| Security | [SECURITY.md](../SECURITY.md) |
| Monitoring with Grafana | [monitoring/README.md](../../monitoring/README.md) |
| Changes per version | [CHANGELOG.md](../../CHANGELOG.md) · [Releases](https://github.com/kamera-linux/vogel-kamera-linux/releases) |

Questions are welcome in English in the [Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions).
