#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO Training-Skript für Vogelarten-Erkennung

Verwendet YOLOv8 für das Training eines spezialisierten Vogelarten-Detektors.
"""

import argparse
import yaml
from pathlib import Path
import torch
from datetime import datetime

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    print("⚠️ Ultralytics nicht installiert. Installieren Sie mit: pip install ultralytics")

def check_requirements():
    """Prüft ob alle Requirements erfüllt sind"""
    
    print("🔍 Prüfe System-Requirements...")
    
    # Python Version
    import sys
    python_version = sys.version_info
    print(f"✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # PyTorch
    try:
        torch_version = torch.__version__
        print(f"✅ PyTorch: {torch_version}")
        
        # CUDA verfügbar?
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ CUDA GPU: {gpu_name}")
        else:
            print("ℹ️ CUDA nicht verfügbar - Training wird auf CPU durchgeführt")
            
    except Exception as e:
        print(f"❌ PyTorch Problem: {e}")
        return False
    
    # Ultralytics
    if ULTRALYTICS_AVAILABLE:
        print("✅ Ultralytics verfügbar")
    else:
        print("❌ Ultralytics fehlt")
        return False
    
    return True

def load_dataset_config(config_path):
    """Lädt und validiert Dataset-Konfiguration"""
    
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"❌ Dataset-Konfiguration nicht gefunden: {config_path}")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validierung
        required_keys = ['path', 'train', 'val', 'nc', 'names']
        for key in required_keys:
            if key not in config:
                print(f"❌ Fehlender Schlüssel in data.yaml: {key}")
                return None
        
        # Pfade prüfen
        dataset_path = Path(config['path'])
        train_path = dataset_path / config['train']
        val_path = dataset_path / config['val']
        
        if not train_path.exists():
            print(f"❌ Training-Pfad nicht gefunden: {train_path}")
            return None
            
        if not val_path.exists():
            print(f"❌ Validierungs-Pfad nicht gefunden: {val_path}")
            return None
        
        # Bilder zählen
        train_images = len(list(train_path.glob('*.jpg'))) + len(list(train_path.glob('*.png')))
        val_images = len(list(val_path.glob('*.jpg'))) + len(list(val_path.glob('*.png')))
        
        print("📊 Dataset-Info:")
        print(f"   Klassen: {config['nc']}")
        print(f"   Training-Bilder: {train_images}")
        print(f"   Validierungs-Bilder: {val_images}")
        print(f"   Klassen: {list(config['names'].values())}")
        
        return config
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return None

def train_bird_model(config_path, **training_args):
    """Trainiert das Vogelarten-Erkennungsmodell"""
    
    if not ULTRALYTICS_AVAILABLE:
        print("❌ Ultralytics ist nicht installiert")
        return False
    
    # Dataset-Config laden
    config = load_dataset_config(config_path)
    if not config:
        return False
    
    # Modell-Auswahl
    model_size = training_args.get('model_size', 'n')
    model_name = f'yolov8{model_size}.pt'
    
    print(f"🤖 Lade Basis-Modell: {model_name}")
    try:
        model = YOLO(model_name)
    except Exception as e:
        print(f"❌ Fehler beim Laden des Modells: {e}")
        return False
    
    # Training-Parameter
    epochs = training_args.get('epochs', 100)
    batch_size = training_args.get('batch_size', 16)
    imgsz = training_args.get('imgsz', 640)
    device = training_args.get('device', 'auto')
    
    # Auto-Device bei CUDA-Verfügbarkeit
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Projekt-Name mit Zeitstempel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = training_args.get('project', 'bird_training')
    experiment_name = f"bird_detector_{model_size}_{timestamp}"
    
    print("🚀 Starte Training:")
    print(f"   Modell: YOLOv8{model_size}")
    print(f"   Epochen: {epochs}")
    print(f"   Batch-Größe: {batch_size}")
    print(f"   Bildgröße: {imgsz}")
    print(f"   Device: {device}")
    print(f"   Experiment: {experiment_name}")
    
    try:
        # Training starten
        model.train(
            data=config_path,
            epochs=epochs,
            batch=batch_size,
            imgsz=imgsz,
            device=device,
            project=project_name,
            name=experiment_name,
            save=True,
            plots=True,
            val=True,
            patience=training_args.get('patience', 20),
            workers=training_args.get('workers', 4),
            optimizer=training_args.get('optimizer', 'auto'),
            lr0=training_args.get('learning_rate', 0.01),
            weight_decay=training_args.get('weight_decay', 0.0005)
        )
        
        print("✅ Training erfolgreich abgeschlossen!")
        
        # Modell-Info
        best_model_path = Path(project_name) / experiment_name / 'weights' / 'best.pt'
        print(f"📁 Bestes Modell: {best_model_path}")
        
        # Export-Empfehlungen
        print("\n📤 Nächste Schritte:")
        print(f"   1. Modell testen: python test_model.py {best_model_path}")
        print(f"   2. ONNX Export: python export_model.py {best_model_path}")
        print("   3. Integration: Siehe ANLEITUNG-EIGENES-AI-MODELL.md")
        
        return True
        
    except Exception as e:
        print(f"❌ Training-Fehler: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='YOLOv8 Training für Vogelarten-Erkennung',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Training
  python train_bird_model.py data.yaml
  
  # Schnelles Training für Tests
  python train_bird_model.py data.yaml --epochs 50 --model-size n
  
  # High-Quality Training
  python train_bird_model.py data.yaml --epochs 200 --model-size s --batch-size 8
        """
    )
    
    parser.add_argument('dataset_config', help='Pfad zur data.yaml Datei')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Anzahl Training-Epochen (default: 100)')
    parser.add_argument('--batch-size', type=int, default=16,
                       help='Batch-Größe (default: 16)')
    parser.add_argument('--model-size', choices=['n', 's', 'm', 'l', 'x'], default='n',
                       help='YOLOv8 Modell-Größe: n(ano), s(mall), m(edium), l(arge), x(large) (default: n)')
    parser.add_argument('--imgsz', type=int, default=640,
                       help='Eingabe-Bildgröße (default: 640)')
    parser.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto',
                       help='Training-Device (default: auto)')
    parser.add_argument('--project', default='bird_training',
                       help='Projekt-Name für Ausgabe (default: bird_training)')
    parser.add_argument('--patience', type=int, default=20,
                       help='Early stopping patience (default: 20)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Anzahl Worker-Threads (default: 4)')
    parser.add_argument('--learning-rate', type=float, default=0.01,
                       help='Initiale Lernrate (default: 0.01)')
    parser.add_argument('--optimizer', choices=['SGD', 'Adam', 'AdamW', 'auto'], default='auto',
                       help='Optimizer (default: auto)')
    parser.add_argument('--check-only', action='store_true',
                       help='Nur Requirements und Dataset prüfen, nicht trainieren')
    
    args = parser.parse_args()
    
    # Requirements prüfen
    if not check_requirements():
        print("❌ Requirements nicht erfüllt")
        return 1
    
    # Dataset prüfen
    config = load_dataset_config(args.dataset_config)
    if not config:
        return 1
    
    # Nur Check?
    if args.check_only:
        print("✅ Alle Checks erfolgreich - bereit für Training!")
        return 0
    
    # Training starten
    success = train_bird_model(
        args.dataset_config,
        epochs=args.epochs,
        batch_size=args.batch_size,
        model_size=args.model_size,
        imgsz=args.imgsz,
        device=args.device,
        project=args.project,
        patience=args.patience,
        workers=args.workers,
        learning_rate=args.learning_rate,
        optimizer=args.optimizer
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())