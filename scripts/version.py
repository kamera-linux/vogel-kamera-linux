#!/usr/bin/env python3
"""
Version information for Vogel-Kamera-Linux
"""

__version__ = "1.2.0"
__version_info__ = (1, 2, 0)

# Release Information
RELEASE_NAME = "Auto-Trigger System & Stream-Management"
RELEASE_DATE = "2025-10-01"
RELEASE_TYPE = "minor"  # major, minor, patch

# Build Information
BUILD_NUMBER = "20251001"
GIT_TAG = "v1.2.0"

# Feature Flags
FEATURES = {
    "ai_detection": True,
    "audio_recording": True,
    "slow_motion": True,
    "system_monitoring": True,  # Since v1.1.9
    "performance_optimization": True,  # Since v1.1.9
    "load_balancing": True,  # Since v1.1.9
    "auto_trigger": True,  # New in v1.2.0
    "preview_stream": True,  # New in v1.2.0
    "trigger_duration_logic": True,  # New in v1.2.0
    "stream_management": True,  # New in v1.2.0
    "network_diagnostics": True,  # New in v1.2.0
    "github_discussions": True,  # Since v1.1.3
    "github_templates": True,  # Since v1.1.2
    "wiki_documentation": True,  # Since v1.1.1
    "web_interface": False,  # Planned for v1.3.0
    "mobile_app": False,  # Planned for v1.3.0
}

# System Requirements
MIN_PYTHON_VERSION = (3, 8)
SUPPORTED_PI_MODELS = ["4B", "5"]
REQUIRED_PACKAGES = [
    "paramiko>=3.0.0",
    "opencv-python>=4.8.0",
    "ultralytics>=8.0.0",
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