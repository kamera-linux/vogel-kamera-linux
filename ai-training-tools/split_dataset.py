#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset-Aufteilung für AI-Training

Teilt ein Dataset in Training- und Validierungssets auf.
"""

import os
import shutil
import random
import argparse
from pathlib import Path

def split_dataset(image_dir, label_dir, output_dir, train_ratio=0.8, val_ratio=0.2, seed=42):
    """
    Teilt Dataset in Training/Validation auf
    
    Args:
        image_dir: Verzeichnis mit Bildern
        label_dir: Verzeichnis mit Labels (YOLO-Format)
        output_dir: Ausgabe-Verzeichnis
        train_ratio: Anteil Training (0.0-1.0)
        val_ratio: Anteil Validation (0.0-1.0)
        seed: Random seed für Reproduzierbarkeit
    """
    
    # Random seed setzen
    random.seed(seed)
    
    # Pfade vorbereiten
    image_path = Path(image_dir)
    label_path = Path(label_dir)
    output_path = Path(output_dir)
    
    # Alle Bilder finden (verschiedene Formate)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    images = []
    for ext in image_extensions:
        images.extend(image_path.glob(f'*{ext}'))
        images.extend(image_path.glob(f'*{ext.upper()}'))
    
    if not images:
        print(f"❌ Keine Bilder gefunden in: {image_dir}")
        return False
    
    print(f"📸 Gefunden: {len(images)} Bilder")
    
    # Zufällige Reihenfolge
    random.shuffle(images)
    
    # Aufteilung berechnen
    total_images = len(images)
    train_count = int(total_images * train_ratio)
    val_count = int(total_images * val_ratio)
    
    # Sicherstellen dass train + val <= total
    if train_count + val_count > total_images:
        val_count = total_images - train_count
    
    train_images = images[:train_count]
    val_images = images[train_count:train_count + val_count]
    
    print(f"📊 Aufteilung:")
    print(f"   Training: {len(train_images)} Bilder ({len(train_images)/total_images*100:.1f}%)")
    print(f"   Validation: {len(val_images)} Bilder ({len(val_images)/total_images*100:.1f}%)")
    
    # Verzeichnisstruktur erstellen
    splits = ['train', 'val']
    for split in splits:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)
    
    # Dateien kopieren
    def copy_split(images_list, split_name):
        copied_images = 0
        copied_labels = 0
        
        for img_path in images_list:
            # Bild kopieren
            dest_img = output_path / 'images' / split_name / img_path.name
            shutil.copy2(img_path, dest_img)
            copied_images += 1
            
            # Entsprechendes Label suchen und kopieren
            label_file = img_path.stem + '.txt'
            label_src = label_path / label_file
            
            if label_src.exists():
                dest_label = output_path / 'labels' / split_name / label_file
                shutil.copy2(label_src, dest_label)
                copied_labels += 1
            else:
                print(f"⚠️  Label fehlt für: {img_path.name}")
        
        return copied_images, copied_labels
    
    # Training-Set kopieren
    train_imgs, train_lbls = copy_split(train_images, 'train')
    print(f"✅ Training: {train_imgs} Bilder, {train_lbls} Labels kopiert")
    
    # Validation-Set kopieren
    val_imgs, val_lbls = copy_split(val_images, 'val')
    print(f"✅ Validation: {val_imgs} Bilder, {val_lbls} Labels kopiert")
    
    # Dataset-Konfiguration erstellen
    create_dataset_config(output_path, train_imgs, val_imgs)
    
    return True

def create_dataset_config(output_dir, train_count, val_count):
    """Erstellt data.yaml Konfigurationsdatei"""
    
    config_content = f"""# Dataset-Konfiguration für YOLO Training
# Generiert automatisch von split_dataset.py

path: {output_dir.absolute()}  # Dataset-Wurzelverzeichnis
train: images/train   # Training-Bilder (relativ zu 'path')
val: images/val       # Validierungs-Bilder (relativ zu 'path')

# Statistiken
train_images: {train_count}
val_images: {val_count}

# Anzahl der Klassen (ANPASSEN!)
nc: 8

# Klassennamen (ANPASSEN AN IHRE VÖGEL!)
names: 
  0: Amsel
  1: Blaumeise  
  2: Kohlmeise
  3: Rotkehlchen
  4: Buchfink
  5: Grünfink
  6: Haussperling
  7: Star

# Weitere mögliche Klassen:
#  8: Elster
#  9: Rabenkrähe
#  10: Eichelhäher
#  11: Feldsperling
"""

    config_path = output_dir / 'data.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"📄 Konfiguration erstellt: {config_path}")
    print("⚠️  WICHTIG: Passen Sie die Klassennamen in data.yaml an!")

def analyze_dataset(image_dir, label_dir):
    """Analysiert ein Dataset und gibt Statistiken aus"""
    
    image_path = Path(image_dir)
    label_path = Path(label_dir)
    
    # Bilder zählen
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    images = []
    for ext in image_extensions:
        images.extend(image_path.glob(f'*{ext}'))
        images.extend(image_path.glob(f'*{ext.upper()}'))
    
    # Labels zählen
    labels = list(label_path.glob('*.txt'))
    
    # Klassen-Statistiken
    class_counts = {}
    total_objects = 0
    
    for label_file in labels:
        with open(label_file, 'r') as f:
            for line in f:
                if line.strip():
                    class_id = int(line.split()[0])
                    class_counts[class_id] = class_counts.get(class_id, 0) + 1
                    total_objects += 1
    
    print(f"📊 Dataset-Analyse:")
    print(f"   Bilder: {len(images)}")
    print(f"   Labels: {len(labels)}")
    print(f"   Bilder ohne Label: {len(images) - len(labels)}")
    print(f"   Objekte gesamt: {total_objects}")
    print(f"   Klassen: {len(class_counts)}")
    
    if class_counts:
        print(f"\n📈 Klassen-Verteilung:")
        for class_id, count in sorted(class_counts.items()):
            percentage = count / total_objects * 100
            print(f"   Klasse {class_id}: {count} Objekte ({percentage:.1f}%)")

def main():
    parser = argparse.ArgumentParser(
        description='Dataset-Aufteilung für AI-Training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Aufteilung 80/20
  python split_dataset.py images/ labels/ bird_dataset/
  
  # Custom-Aufteilung 70/30 
  python split_dataset.py images/ labels/ bird_dataset/ --train-ratio 0.7 --val-ratio 0.3
  
  # Dataset analysieren
  python split_dataset.py images/ labels/ --analyze-only
        """
    )
    
    parser.add_argument('image_dir', help='Verzeichnis mit Bildern')
    parser.add_argument('label_dir', help='Verzeichnis mit Labels (YOLO-Format)')
    parser.add_argument('output_dir', nargs='?', help='Ausgabe-Verzeichnis')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                       help='Anteil Training-Daten (default: 0.8)')
    parser.add_argument('--val-ratio', type=float, default=0.2,
                       help='Anteil Validierungs-Daten (default: 0.2)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Nur Dataset-Analyse, keine Aufteilung')
    
    args = parser.parse_args()
    
    # Pfade prüfen
    if not Path(args.image_dir).exists():
        print(f"❌ Bild-Verzeichnis nicht gefunden: {args.image_dir}")
        return 1
    
    if not Path(args.label_dir).exists():
        print(f"❌ Label-Verzeichnis nicht gefunden: {args.label_dir}")
        return 1
    
    # Nur Analyse?
    if args.analyze_only:
        analyze_dataset(args.image_dir, args.label_dir)
        return 0
    
    # Output-Verzeichnis erforderlich für Split
    if not args.output_dir:
        print("❌ Ausgabe-Verzeichnis erforderlich (außer bei --analyze-only)")
        return 1
    
    # Ratio validieren
    if args.train_ratio + args.val_ratio > 1.0:
        print("❌ train_ratio + val_ratio darf nicht > 1.0 sein")
        return 1
    
    # Dataset analysieren
    print("📊 Analysiere Dataset...")
    analyze_dataset(args.image_dir, args.label_dir)
    
    print(f"\n🔄 Teile Dataset auf...")
    success = split_dataset(
        args.image_dir, args.label_dir, args.output_dir,
        args.train_ratio, args.val_ratio, args.seed
    )
    
    if success:
        print(f"\n✅ Dataset erfolgreich aufgeteilt in: {args.output_dir}")
        print("📝 Nächste Schritte:")
        print("   1. Klassennamen in data.yaml anpassen")
        print("   2. Training starten mit: python train_bird_model.py")
    else:
        print("❌ Fehler beim Aufteilen des Datasets")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())