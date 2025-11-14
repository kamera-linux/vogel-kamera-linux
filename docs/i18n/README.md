# 🐦 Bird Camera Linux

**Languages / Sprachen / 言語:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md) | [🇯🇵 日本語](README.ja.md)

[![Version](https://img.shields.io/badge/Version-v2.0.0-brightgreen)](https://github.com/kamera-linux/vogel-kamera-linux/releases/tag/v2.0.0)
[![Trixie Support](https://img.shields.io/badge/Debian-Trixie%20(13)-blue)](../TRIXIE-MIGRATION.md)
[![GitHub Issues](https://img.shields.io/github/issues/kamera-linux/vogel-kamera-linux)](https://github.com/kamera-linux/vogel-kamera-linux/issues)
[![GitHub PRs](https://img.shields.io/github/issues-pr/kamera-linux/vogel-kamera-linux)](https://github.com/kamera-linux/vogel-kamera-linux/pulls)
[![License](https://img.shields.io/github/license/kamera-linux/vogel-kamera-linux)](../../LICENSE)

> ⚠️ **Raspberry Pi OS Trixie (Debian 13):** This version is optimized for **Trixie**.  
> 📘 **For Bookworm (Debian 12):** Use the [bookworm-legacy branch (v1.2.x)](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)  
> 📖 **Migration Guide:** [TRIXIE-MIGRATION.md](../TRIXIE-MIGRATION.md)

![Complete Bird Camera System](../../assets/vogelhaus-kamera-komplett.png)

**🐦 Professional Bird Observation System with AI-powered Object Detection**

`vogel-kamera-linux` is an **open-source project** for remote bird house monitoring using Raspberry Pi 5 camera. The system combines high-resolution video/audio recording with **YOLOv8 AI detection** for automatic bird recognition and recording.

### 🚀 Quickstart
```bash
# RECOMMENDED: Unified Camera Monitor (directly on Raspberry Pi)
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo

# Or via wrapper from Client PC
cd auto-start-kamera
./start-unified-monitoring.sh slowmo

# LEGACY: Old remote control scripts (see legacy/README.md)
python legacy/ai-had-kamera-remote-param-vogel-libcamera-single-AI-Modul.py \
    --duration 5 --width 1920 --height 1080 --ai-modul on
```

> 📺 **Live Demo:** [YouTube Channel](https://www.youtube.com/@vogel-kamera-linux) - Real recordings from the vogel-kamera-linux system!

## 📖 Overview

**vogel-kamera-linux** is a complete remote camera system for nature observation, developed for **Raspberry Pi 5** with Python 3.11+. The project combines modern camera hardware (IMX708) with advanced AI object detection (YOLOv8) for automatic bird recognition.

**🎯 Main Application:** Remote bird house monitoring with automatic recording upon bird detection, including HD video (up to 4K), slow motion (120fps) and synchronized audio recording via USB microphone.

### 🎬 YouTube Channel & Sample Recordings

[![YouTube Channel](https://img.shields.io/badge/📺_YouTube_Channel-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@vogel-kamera-linux)

**Real recordings from the vogel-kamera-linux system!** Watch the camera in action with live bird detection, slow motion recordings and 4K videos from our bird house.

**📱 QR Code for mobile access:**

![YouTube QR Code](../../assets/qr-youtube-channel.png)

## ✨ Features

- 🎥 **High-resolution video recording** (up to 4K)
- 🎵 **Synchronized audio recording** via USB microphone
- 🤖 **AI object detection** with YOLOv8 and custom bird species models
- 🎯 **Auto-trigger system** with automatic bird detection *(New in v1.2.0)*
- 📺 **Preview stream** (RTSP) for live monitoring *(New in v1.2.0)*
- 🌐 **Network diagnostics** for performance analysis *(New in v1.2.0)*
- 📊 **System monitoring** with CPU load and temperature monitoring *(Since v1.1.9)*
- ⚡ **Performance optimization** for various recording modes *(Since v1.1.9)*
- 🌐 **Remote control** via SSH
- 📁 **Automatic file organization** by year/week
- ⚙️ **Flexible configuration** via .env files
- 📊 **Progress display** during recording
- 🔄 **Automatic video/audio synchronization**
- 📱 **YouTube integration** with QR codes for mobile users
- 🔧 **Easy installation** with config/requirements.txt
- ✅ **Automatic configuration validation**
- 🎯 **Custom AI models** trainable for specific bird species

## 📸 Hardware Gallery

**Modular Camera Solution:**
![Single Bird House](../../assets/vogelhaus-kamera-solo.png)
*Flexible placement for optimal recordings*

**Live Recordings & Community:**
![YouTube Channel Impression](../../assets/Youtube-Kanal.png) 
*Real bird observations on YouTube*

> 💡 **3D construction files available!** All CAD files for rebuilding can be found in the [`3d-konstruktion/`](../../3d-konstruktion/) directory

## 🛠️ Requirements

### Hardware
- Raspberry Pi 5 with camera module (recommended: IMX708 Wide)
- USB microphone for audio recording
- Stable network connection (Gigabit LAN recommended)

### Software (Raspberry Pi)
- **Raspberry Pi OS Trixie (Debian 13)** - REQUIRED for this version
- Python 3.13+
- rpicam-apps v1.9.1+
- FFmpeg 7.1.2+
- SSH access configured

> ⚠️ **Trixie-specific:** This version uses TCP Watchdog for preview stream (FFmpeg 7.1.2 compatible)  
> 📘 **Bookworm users:** Use [bookworm-legacy branch (v1.2.x)](https://github.com/kamera-linux/vogel-kamera-linux/tree/bookworm-legacy)

### Software (Client PC)
- Python 3.8+
- SSH client
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Installation on Raspberry Pi

**Automated Setup (Recommended):**
```bash
# Run setup script on Raspberry Pi
curl -sSL https://raw.githubusercontent.com/kamera-linux/vogel-kamera-linux/main/raspberry-pi-scripts/setup-unified-monitor.sh | bash

# Or manually:
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux
bash raspberry-pi-scripts/setup-unified-monitor.sh
```

**Manual Installation:**
```bash
# On Raspberry Pi - Install Python packages (apt, not pip!)
sudo apt-get update
sudo apt-get install -y python3-picamera2 python3-opencv python3-numpy python3-libcamera

# Install YOLOv8
pip install ultralytics --break-system-packages

# Check camera tools
rpicam-hello --version  # Should be v1.9.1+
ffmpeg -version         # Should be 7.1.2+
```

### 2. Client PC Configuration
```bash
# Clone repository
git clone https://github.com/kamera-linux/vogel-kamera-linux.git
cd vogel-kamera-linux

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r config/requirements.txt

# Configure SSH access
cp python-skripte/.env.example python-skripte/.env
nano python-skripte/.env

# Test configuration
python python-skripte/config.py
```

### 3. First Recording
```bash
# Standard mode (4K @ 30fps, 60s recordings)
python3 raspberry-pi-scripts/unified-camera-monitor.py

# Slow motion mode (1536x864 @ 120fps)
python3 raspberry-pi-scripts/unified-camera-monitor.py --slowmo

# Via wrapper from Client PC
cd auto-start-kamera
./start-unified-monitoring.sh slowmo
```

## 🎯 Unified Camera Monitor System (v2.0)

**NEW!** Unified camera process without SSH overhead - runs directly on Raspberry Pi.

### ✨ Advantages
- ✅ **No camera conflicts** - Single process for everything
- ✅ **Faster response** - No SSH/network latency
- ✅ **Easier operation** - CLI parameters instead of .env files
- ✅ **Live monitoring** - Heartbeat every 30s, status every 5min with traffic lights
- ✅ **Auto-shutdown** - At critical temperature (>75°C)

### ⚙️ Available Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--camera` | Camera number | 0 | `--camera 1` |
| `--threshold` | AI detection threshold | 0.4 | `--threshold 0.3` |
| `--cooldown` | Cooldown between recordings (s) | 15 | `--cooldown 10` |
| `--trigger-duration` | Minimum duration for trigger (s) | 1.0 | `--trigger-duration 0.5` |
| `--video-path` | Base path for videos | `/home/roimme/Videos/Vogelhaus` | `--video-path /mnt/nas/birds` |
| `--model` | Path to YOLO model | yolov8n.pt | `--model custom.pt` |
| `--preview-fps` | Preview FPS | 6 | `--preview-fps 10` |
| `--recording-width` | Recording width (px) | 4096 | `--recording-width 1920` |
| `--recording-height` | Recording height (px) | 2160 | `--recording-height 1080` |
| `--recording-fps` | Recording FPS | 30 | `--recording-fps 60` |
| `--recording-duration` | Recording duration (s) | 60 | `--recording-duration 120` |
| `--slowmo` | Enable slow motion mode | - | `--slowmo` |
| `--debug` | Enable debug mode | - | `--debug` |

### 📊 Live Monitoring Output

```
======================================================================
🐦 UNIFIED CAMERA MONITOR - Vogel-Kamera-Linux
======================================================================

======================================================================
📊 INITIAL STATUS REPORT
======================================================================

2025-11-11 19:27:14 - INFO - [✓] Monitor active - 354 frames processed
2025-11-11 19:29:12 - INFO - Status: 0h 5min | Recordings: 0 | Frames: 584 | Temp: 🟢51.0°C | Load: 🟡1.72 | RAM: 🟢7% | Disk: 🟢215.3GB
```

**Traffic Light Thresholds:**
- **Temperature:** 🟢 <55°C | 🟡 55-65°C | 🔴 >65°C | ⛔ STOP >75°C
- **CPU Load:** 🟢 <1.0 | 🟡 1.0-2.0 | 🔴 >2.0
- **RAM:** 🟢 <75% | 🟡 75-90% | 🔴 >90%
- **Disk:** 🟢 <90% | 🟡 90-95% | 🔴 >95%

## 📝 Legacy: Remote-Control Scripts

> ⚠️ **These scripts are deprecated!** Use the **Unified Camera Monitor System** instead (see above).
> 
> The old scripts have been moved to `legacy/`. Details: [`legacy/README.md`](../../legacy/README.md)

## 🤖 AI Object Detection & Bird Species Models

### Immediately Available: Standard Object Detection
```bash
# YOLOv8 with general bird detection
python3 raspberry-pi-scripts/unified-camera-monitor.py --model yolov8n.pt
```

### Advanced: Train Custom Bird Species Models
The system supports training custom AI models for specific bird species:

🎯 **Common European garden birds**: Blackbird, Blue Tit, Great Tit, Robin, Chaffinch...

📋 **Complete Guide**: [`docs/ANLEITUNG-EIGENES-AI-MODELL.md`](../ANLEITUNG-EIGENES-AI-MODELL.md) (German)

🛠️ **Training Tools**: [`ai-training-tools/`](../../ai-training-tools/) - Complete toolkit for custom models

## 📄 License

See [LICENSE](../../LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Create pull request

## 👥 Community & Discussions

[![GitHub Discussions](https://img.shields.io/github/discussions/kamera-linux/vogel-kamera-linux)](https://github.com/kamera-linux/vogel-kamera-linux/discussions)

Connect with other users:
- 🙋 **Ask questions** about installation and configuration  
- 💡 **Share ideas** for new features
- 📸 **Show recordings** from your bird house
- 🔧 **Discuss hardware tips**

## 📞 Support

For questions or issues:
- 💬 **Start discussions** in [GitHub Discussions](https://github.com/kamera-linux/vogel-kamera-linux/discussions)
- 🐛 **Report bugs** via [GitHub Issues](https://github.com/kamera-linux/vogel-kamera-linux/issues)

## 📚 Documentation

### Main Documentation
- **[docs/CHANGELOG.md](../CHANGELOG.md)** - Complete version history
- **[docs/ARCHITEKTUR.md](../ARCHITEKTUR.md)** - 🏗️ **NEW in v1.2.0!** Detailed system architecture with Mermaid diagrams
- **[docs/PROJEKT-REORGANISATION.md](../PROJEKT-REORGANISATION.md)** - Project reorganization history

### Auto-Trigger System *(v1.2.0)*
- **[kamera-auto-trigger/README.md](../../kamera-auto-trigger/README.md)** - Main auto-trigger documentation
- **[kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md](../../kamera-auto-trigger/docs/QUICKSTART-AUTO-TRIGGER.md)** - 3-minute quick start

### AI & Training
- **[docs/AI-MODELLE-VOGELARTEN.md](../AI-MODELLE-VOGELARTEN.md)** - AI model documentation
- **[docs/ANLEITUNG-EIGENES-AI-MODELL.md](../ANLEITUNG-EIGENES-AI-MODELL.md)** - Training custom models

### Security & Development
- **[docs/SECURITY.md](../SECURITY.md)** - Security guidelines
- **[git-automation/README.md](../../git-automation/README.md)** - Git automation documentation

## 📋 Changelog

All changes are documented in **[docs/CHANGELOG.md](../CHANGELOG.md)**.

### 🆕 New in v2.0.0 (November 2025)
- 🎯 **Unified Camera Monitor:** Single-process system without SSH overhead
- 🚦 **Traffic Light System:** Real-time health monitoring (CPU, RAM, disk, temp)
- 🔒 **Auto-Shutdown:** Emergency stop at critical temperature >75°C
- ⏱️ **Configurable Recording:** 60s default, adjustable via `--recording-duration`
- 📊 **Live Feedback:** Heartbeat every 30s, status every 5min
- 📦 **Legacy Archiving:** Old remote scripts moved to `legacy/`
- 🌐 **Multilingual Documentation:** English, German, Japanese READMEs
- 🔧 **Setup Script:** Automated Raspberry Pi installation

### 📡 Trixie Support in v1.3.0 (November 2025)
- 📡 **TCP Watchdog System:** Robust preview stream management (FFmpeg 7.1.2 compatible)
- 🎯 **On-Demand Stream Mode:** Dual camera operation without conflicts
- 🐍 **PEP 668 Compliance:** Python packages via apt instead of pip

### 🎬 Previous Releases
- **v1.3.1:** Live progress bar, TCP watchdog hardening
- **v1.1.9:** System monitoring, performance optimization
- **v1.1.8:** Bird-species models, 3D construction files
- **v1.1.0:** YouTube integration, central configuration system

## 🔖 Versions

- **Current Version:** v2.0.0
- **Branch:** `main` (Trixie)
- **Legacy Branch:** `bookworm-legacy` (v1.2.x for Debian 12)
- **All Releases:** [GitHub Releases](https://github.com/kamera-linux/vogel-kamera-linux/releases) | [Tags](https://github.com/kamera-linux/vogel-kamera-linux/tags)

---

**Made with ❤️ for bird lovers and open-source enthusiasts**
