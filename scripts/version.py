#!/usr/bin/env python3
"""
Version information for Vogel-Kamera-Linux
"""

__version__ = "2.2.6"
__version_info__ = (2, 2, 6)

# Release Information
RELEASE_NAME = "Bugfix: Detection-Prozess & Aufnahmen-Tageszähler"
RELEASE_DATE = "2026-03-31"
RELEASE_TYPE = "patch"  # major, minor, patch

# Build Information
BUILD_NUMBER = "20260331-1"
GIT_TAG = "v2.2.6"

# Feature Flags
FEATURES = {
    "ai_detection": True,
    "audio_recording": True,
    "slow_motion": True,
    "system_monitoring": True,  # Since v1.1.9
    "performance_optimization": True,  # Since v1.1.9
    "load_balancing": True,  # Since v1.1.9
    "auto_trigger": True,  # Since v1.2.0
    "preview_stream": True,  # Since v1.2.0
    "trigger_duration_logic": True,  # Since v1.2.0
    "stream_management": True,  # Since v1.2.0
    "network_diagnostics": True,  # Since v1.2.0
    "unified_camera_monitor": True,  # Since v2.0.0
    "traffic_light_monitoring": True,  # Since v2.0.0
    "auto_shutdown": True,  # Since v2.0.0
    "multilingual_docs": True,  # Since v2.0.0
    "tcp_stream_watchdog": True,  # New in v1.3.0 - Auto-restart bei Verbindungsabbruch
    "trixie_support": True,  # New in v1.3.0 - Debian 13 Trixie kompatibel
    "github_discussions": True,  # Since v1.1.3
    "github_templates": True,  # Since v1.1.2
    "wiki_documentation": True,  # Since v1.1.1
    "cli_parameters": True,  # New in v2.0.1 - Full CLI parameter support
    "cinema_4k": True,  # New in v2.0.1 - Cinema 4K (4096x2160 @ 25fps)
    "ai_had_mode": True,  # New in v2.0.1 - AI-HAD with audio detection
    "auto_video_sync": True,  # New in v2.0.1 - Immediate video sync after conversion
    "ssh_resilience": True,  # New in v2.0.1 - Enhanced SSH error handling
    "yolo26_detection": True,  # New in v2.0.2 - YOLO26 model (yolo26n.pt)
    "monitoring_improvements": True,  # New in v2.0.2 - CPU/RAM display, SSH stability
    "web_interface": False,  # Planned for future
    "mobile_app": False,  # Planned for future
}

# System Requirements
MIN_PYTHON_VERSION = (3, 8)
SUPPORTED_PI_MODELS = ["4B", "5"]
REQUIRED_PACKAGES = [
    "paramiko>=3.0.0",
    "opencv-python>=4.8.0",
    "ultralytics>=26.0.0",
    "qrcode[pil]>=7.4.0",
    "python-dotenv>=1.0.0"
]

def get_version():
    """Return the current version string."""
    return __version__

def get_version_info():
    """Return version information as a tuple."""
    return __version_info__

def get_full_version():
    """Return detailed version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_name": RELEASE_NAME,
        "release_date": RELEASE_DATE,
        "release_type": RELEASE_TYPE,
        "build_number": BUILD_NUMBER,
        "git_tag": GIT_TAG,
        "features": FEATURES
    }

def check_compatibility():
    """Check if current system meets requirements."""
    import sys
    
    compatibility = {
        "python_version": sys.version_info >= MIN_PYTHON_VERSION,
        "python_current": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_required": f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+",
        "compatible": True
    }
    
    if not compatibility["python_version"]:
        compatibility["compatible"] = False
        
    return compatibility

def print_version_info():
    """Print formatted version information."""
    info = get_full_version()
    compat = check_compatibility()
    
    print(f"🐦 Vogel-Kamera-Linux v{info['version']}")
    print(f"📋 Release: {info['release_name']}")
    print(f"📅 Date: {info['release_date']}")
    print(f"🏷️ Tag: {info['git_tag']}")
    print(f"🔧 Build: {info['build_number']}")
    print("")
    print("✨ Features:")
    for feature, enabled in info['features'].items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {feature.replace('_', ' ').title()}")
    print("")
    print("🐍 Python Compatibility:")
    print(f"   Current: {compat['python_current']}")
    print(f"   Required: {compat['python_required']}")
    print(f"   Compatible: {'✅' if compat['compatible'] else '❌'}")

if __name__ == "__main__":
    print_version_info()