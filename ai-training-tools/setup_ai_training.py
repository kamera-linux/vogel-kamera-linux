#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements-Installation für AI-Training-Tools

Installiert alle benötigten Python-Pakete für das Training von Vogelarten-AI-Modellen.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Führt einen Befehl aus und zeigt den Fortschritt"""
    
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} erfolgreich")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler bei {description}")
        print(f"   Kommando: {command}")
        print(f"   Fehler: {e.stderr}")
        return False

def install_requirements():
    """Installiert alle AI-Training Requirements"""
    
    print("🚀 AI-Training Requirements Installation")
    print("=" * 50)
    
    # Requirements Liste
    requirements = [
        # Core ML Libraries
        ("torch", "PyTorch (Deep Learning Framework)"),
        ("torchvision", "PyTorch Vision (Bildverarbeitung)"),
        ("ultralytics", "YOLOv8 Framework"),
        
        # Data Processing
        ("opencv-python", "OpenCV (Computer Vision)"),
        ("pillow", "PIL (Bildverarbeitung)"),
        ("numpy", "NumPy (Numerische Berechnungen)"),
        
        # Configuration & Utils
        ("pyyaml", "YAML Parser (Konfigurationsdateien)"),
        ("matplotlib", "Plotting (Visualisierungen)"),
        ("tqdm", "Progress Bars"),
        
        # Optional but useful
        ("tensorboard", "TensorBoard (Training-Monitoring)"),
        ("seaborn", "Seaborn (Statistik-Plots)"),
    ]
    
    # System-Info
    print(f"🖥️ System: Python {sys.version}")
    print(f"📁 Arbeitsverzeichnis: {os.getcwd()}")
    
    # pip updaten
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", 
                       "pip Update"):
        print("⚠️ pip Update fehlgeschlagen, aber wir machen weiter...")
    
    # Requirements installieren
    failed_packages = []
    
    for package, description in requirements:
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installiere {package} ({description})"
        )
        
        if not success:
            failed_packages.append(package)
    
    # Zusammenfassung
    print("\n" + "=" * 50)
    print("📊 INSTALLATION ZUSAMMENFASSUNG")
    print("=" * 50)
    
    if failed_packages:
        print(f"❌ Fehlgeschlagen: {len(failed_packages)} Pakete")
        for package in failed_packages:
            print(f"   • {package}")
        
        print(f"\n💡 Manuelle Installation versuchen:")
        for package in failed_packages:
            print(f"   pip install {package}")
    else:
        print("✅ Alle Pakete erfolgreich installiert!")
    
    # Verification
    print(f"\n🔍 Verifikation...")
    test_imports()
    
    return len(failed_packages) == 0

def test_imports():
    """Testet ob alle wichtigen Imports funktionieren"""
    
    test_cases = [
        ("torch", "PyTorch"),
        ("cv2", "OpenCV"),
        ("yaml", "PyYAML"), 
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
        ("matplotlib", "Matplotlib"),
    ]
    
    print("📦 Import-Tests:")
    
    for module, name in test_cases:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
    
    # Spezialtest: Ultralytics (kann länger dauern)
    print("   🔄 Ultralytics (kann länger dauern)...")
    try:
        from ultralytics import YOLO
        print("   ✅ Ultralytics/YOLO")
    except ImportError as e:
        print(f"   ❌ Ultralytics: {e}")

def create_virtual_env():
    """Erstellt eine virtuelle Umgebung für AI-Training"""
    
    venv_path = Path("bird_ai_env")
    
    if venv_path.exists():
        print(f"📁 Virtual Environment existiert bereits: {venv_path}")
        return str(venv_path)
    
    print(f"🔄 Erstelle Virtual Environment: {venv_path}")
    
    success = run_command(
        f"{sys.executable} -m venv {venv_path}",
        "Virtual Environment erstellen"
    )
    
    if success:
        print(f"✅ Virtual Environment erstellt: {venv_path}")
        
        # Aktivierungs-Anweisungen
        if os.name == 'nt':  # Windows
            activate_script = venv_path / "Scripts" / "activate.bat"
            print(f"\n💡 Zum Aktivieren (Windows):")
            print(f"   {activate_script}")
        else:  # Linux/Mac
            activate_script = venv_path / "bin" / "activate"
            print(f"\n💡 Zum Aktivieren (Linux/Mac):")
            print(f"   source {activate_script}")
        
        return str(venv_path)
    
    return None

def show_next_steps():
    """Zeigt die nächsten Schritte nach der Installation"""
    
    print("\n" + "🎯 NÄCHSTE SCHRITTE" + "\n" + "=" * 50)
    
    steps = [
        "1. 📸 Bilder sammeln:",
        "   python extract_frames.py video.mp4 frames/ --interval 10",
        "",
        "2. 🏷️ Dataset vorbereiten:", 
        "   python split_dataset.py images/ labels/ bird_dataset/",
        "",
        "3. 🧠 Training starten:",
        "   python train_bird_model.py bird_dataset/data.yaml",
        "",
        "4. 📈 Training überwachen:",
        "   tensorboard --logdir bird_training/",
        "",
        "5. 📖 Vollständige Anleitung:",
        "   Siehe: ANLEITUNG-EIGENES-AI-MODELL.md"
    ]
    
    for step in steps:
        print(step)

def main():
    print("🤖 AI-Training Setup für Vogelarten-Erkennung")
    print("=" * 60)
    
    # Optionen
    import argparse
    parser = argparse.ArgumentParser(description='Setup AI-Training Umgebung')
    parser.add_argument('--venv', action='store_true',
                       help='Erstelle Virtual Environment')
    parser.add_argument('--test-only', action='store_true',
                       help='Nur Import-Tests durchführen')
    
    args = parser.parse_args()
    
    # Nur Tests?
    if args.test_only:
        test_imports()
        return 0
    
    # Virtual Environment erstellen?
    if args.venv:
        venv_path = create_virtual_env()
        if not venv_path:
            print("❌ Virtual Environment konnte nicht erstellt werden")
            return 1
        
        print(f"\n⚠️ Aktivieren Sie das Virtual Environment und führen Sie das Skript erneut aus:")
        if os.name == 'nt':
            print(f"   {venv_path}\\Scripts\\activate")
        else:
            print(f"   source {venv_path}/bin/activate")
        print(f"   python setup_ai_training.py")
        return 0
    
    # Requirements installieren
    success = install_requirements()
    
    if success:
        show_next_steps()
        return 0
    else:
        print("\n❌ Setup nicht vollständig erfolgreich")
        print("💡 Versuchen Sie eine manuelle Installation der fehlgeschlagenen Pakete")
        return 1

if __name__ == "__main__":
    exit(main())