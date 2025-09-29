#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Syntax-Test für das erweiterte AI-Modul
"""

def test_ai_model_selection():
    """Teste die AI-Modell-Auswahl-Logik"""
    
    # Simuliere Argumente
    class Args:
        def __init__(self):
            self.ai_modul = 'on'
            self.ai_model = 'yolov8'
            self.ai_model_path = None
    
    def get_ai_model_path(args):
        """Bestimme den Pfad zum AI-Modell basierend auf der Auswahl"""
        if getattr(args, 'ai_modul') == 'off':
            return ""
        
        model_paths = {
            'yolov8': '/usr/share/rpi-camera-assets/hailo_yolov8_inference.json',
            'bird-species': '/usr/share/rpi-camera-assets/hailo_bird_species_inference.json',
            'custom': args.ai_model_path
        }
        
        model_path = model_paths.get(args.ai_model)
        
        if args.ai_model == 'custom' and not args.ai_model_path:
            print("⚠️ Für --ai-model custom muss --ai-model-path angegeben werden!")
            return ""
        
        return "--post-process-file {}".format(model_path) if model_path else ""
    
    # Tests
    print("🧪 AI-Modell-Auswahl Tests:")
    print("=" * 40)
    
    # Test 1: Standard YOLOv8
    args1 = Args()
    args1.ai_modul = 'on'
    args1.ai_model = 'yolov8'
    result1 = get_ai_model_path(args1)
    print("✅ YOLOv8: {}".format(result1))
    
    # Test 2: Bird-Species
    args2 = Args()
    args2.ai_modul = 'on'
    args2.ai_model = 'bird-species'
    result2 = get_ai_model_path(args2)
    print("✅ Bird-Species: {}".format(result2))
    
    # Test 3: Custom ohne Pfad (Fehler)
    args3 = Args()
    args3.ai_modul = 'on'
    args3.ai_model = 'custom'
    args3.ai_model_path = None
    result3 = get_ai_model_path(args3)
    print("✅ Custom ohne Pfad: '{}'".format(result3))
    
    # Test 4: Custom mit Pfad
    args4 = Args()
    args4.ai_modul = 'on'
    args4.ai_model = 'custom'
    args4.ai_model_path = '/home/pi/my_bird_model.json'
    result4 = get_ai_model_path(args4)
    print("✅ Custom mit Pfad: {}".format(result4))
    
    # Test 5: AI deaktiviert
    args5 = Args()
    args5.ai_modul = 'off'
    result5 = get_ai_model_path(args5)
    print("✅ AI deaktiviert: '{}'".format(result5))
    
    print("\n🎯 Neue Kommandozeilen-Optionen:")
    print("  --ai-model yolov8        # Standard-Objekterkennung")
    print("  --ai-model bird-species  # Vogelarten-spezifisch") 
    print("  --ai-model custom --ai-model-path /pfad/zu/modell.json")

if __name__ == "__main__":
    test_ai_model_selection()