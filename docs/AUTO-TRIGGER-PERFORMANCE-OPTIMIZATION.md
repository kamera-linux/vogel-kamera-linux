# 🔧 Auto-Trigger Performance-Optimierung

## 📊 Problem-Analyse

**Gestern:** 33 Trigger in 10h 52min (≈3 Trigger/Stunde)  
**Heute:** 3 Trigger in über 4h (≈0.75 Trigger/Stunde)  
**Performance-Verlust:** ~75% weniger Trigger!

## 🔍 Mögliche Ursachen

### 1. CPU-Thread-Limitierung (OMP_NUM_THREADS=2)

**Was geändert wurde:**
```python
# ai-had-kamera-auto-trigger.py Zeile 21-23
os.environ['OMP_NUM_THREADS'] = '2'  # OpenMP auf 2 Threads begrenzen
os.environ['OPENBLAS_NUM_THREADS'] = '2'  # OpenBLAS auf 2 Threads begrenzen
os.environ['MKL_NUM_THREADS'] = '2'  # Intel MKL auf 2 Threads begrenzen
```

**Auswirkung:**
- ✅ Reduzierte CPU-Last (Ziel erreicht)
- ❌ Langsamere KI-Inferenz (Kollateralschaden)
- ❌ Weniger Frames pro Sekunde verarbeitet
- ❌ Höhere Latenz bei Objekterkennung

**FPS-Vergleich:**
- Vorher (4 Threads): ~5-6 FPS Verarbeitung
- Nachher (2 Threads): ~3-4 FPS Verarbeitung
- **Verlust:** 33-40% weniger Frames

### 2. Preview-Stream Parameter

**Aktuelle Einstellungen:**
```python
# Default-Werte im Auto-Trigger
--preview-fps 3           # Nur 3 FPS (sehr niedrig!)
--preview-width 320       # Sehr kleine Auflösung
--preview-height 240      # Sehr kleine Auflösung
--trigger-threshold 0.45  # Schwelle
```

**Problem:**
- 3 FPS = Nur alle 333ms ein Frame
- 320x240 = Sehr kleine Auflösung → schlechtere Erkennung
- Threshold 0.45 könnte zu niedrig sein für kleinere Auflösung

### 3. Trigger-Duration Logic

**Aktueller Algorithmus:**
```python
# stream_processor.py Zeile 411-421
if detection_duration >= self.trigger_duration:  # 2.0 Sekunden
    recent_detections = [d for t, d in self.detection_history]
    detection_rate = sum(recent_detections) / len(recent_detections)
    
    if detection_rate >= 0.7:  # 70% Konsistenz erforderlich
        return True  # TRIGGER!
```

**Berechnung:**
- 3 FPS × 2 Sekunden = 6 Frames
- 70% Konsistenz = Mindestens 4.2 Frames (≈5 Frames) müssen Vogel zeigen
- **Bei nur 3 FPS ist das sehr anspruchsvoll!**

## 🎯 Optimierungs-Vorschläge

### Lösung 1: FPS erhöhen (EMPFOHLEN)

**Änderung:**
```bash
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --preview-fps 5  # ← Statt 3 FPS
    --trigger-threshold 0.40  # ← Etwas niedriger
```

**Vorteile:**
- 5 FPS × 2 Sek = 10 Frames
- 70% Konsistenz = 7 Frames müssen Vogel zeigen
- **Viel besser erfassbar!**

**CPU-Impact:**
- Erhöhung von 3 auf 5 FPS = +67% CPU (aber von niedrigem Niveau)
- Immer noch deutlich niedriger als vorher

### Lösung 2: Auflösung erhöhen

**Änderung:**
```bash
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --preview-width 640  # ← Statt 320
    --preview-height 480  # ← Statt 240
    --preview-fps 4
```

**Vorteile:**
- Bessere Objekterkennung (größere Vögel im Bild)
- Höhere Confidence-Werte
- Weniger False Negatives

**CPU-Impact:**
- 4× mehr Pixel (640×480 vs 320×240)
- Aber nur 4 FPS statt 5 = Ausgleich

### Lösung 3: Threshold senken + Konsistenz anpassen

**Änderung im Code:**
```python
# stream_processor.py Zeile 418
if detection_rate >= 0.6:  # ← Statt 0.7 (60% statt 70%)
```

**Vorteile:**
- Weniger streng bei Konsistenz
- 3 FPS × 2 Sek = 6 Frames
- 60% = 3.6 Frames (≈4 Frames) müssen Vogel zeigen

**Parameter:**
```bash
--trigger-threshold 0.35  # Niedrigerer Threshold
```

### Lösung 4: Trigger-Duration reduzieren

**Änderung:**
```bash
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 1.5  # ← Statt 2 Sekunden
    --preview-fps 4
    --trigger-threshold 0.40
```

**Vorteile:**
- 4 FPS × 1.5 Sek = 6 Frames
- 70% Konsistenz = 4.2 Frames (≈5 Frames)
- Schnellerer Trigger

**Nachteile:**
- Mehr False Positives möglich
- Weniger Konsistenz-Check

### Lösung 5: Hybrid-Ansatz (BESTE LÖSUNG)

**Kombiniere mehrere Optimierungen:**

```bash
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 1.5 \
    --preview-fps 5 \
    --preview-width 480 \
    --preview-height 360 \
    --trigger-threshold 0.38 \
    --cooldown 45
```

**Begründung:**
- 5 FPS × 1.5 Sek = 7.5 Frames
- 70% Konsistenz = 5.25 Frames (≈6 Frames)
- Mittlere Auflösung (480×360) = Guter Kompromiss
- Threshold 0.38 = Sensitiver aber nicht zu sensitiv
- Cooldown 45s = Etwas länger zwischen Aufnahmen

## 📊 Vergleichstabelle

| Konfiguration | FPS | Auflösung | Trigger-Duration | Frames | Konsistenz | Trigger-Sensitivität |
|---------------|-----|-----------|------------------|---------|------------|---------------------|
| **Gestern (gut)** | ~5-6 | 320×240 | 2.0s | 10-12 | 70% (7-8 Frames) | ⭐⭐⭐⭐⭐ |
| **Heute (schlecht)** | 3 | 320×240 | 2.0s | 6 | 70% (4.2 Frames) | ⭐⭐ |
| **Lösung 1** | 5 | 320×240 | 2.0s | 10 | 70% (7 Frames) | ⭐⭐⭐⭐ |
| **Lösung 2** | 4 | 640×480 | 2.0s | 8 | 70% (5.6 Frames) | ⭐⭐⭐⭐ |
| **Lösung 3** | 3 | 320×240 | 2.0s | 6 | 60% (3.6 Frames) | ⭐⭐⭐ |
| **Lösung 4** | 4 | 320×240 | 1.5s | 6 | 70% (4.2 Frames) | ⭐⭐⭐ |
| **Lösung 5 (BESTE)** | 5 | 480×360 | 1.5s | 7.5 | 70% (5.25 Frames) | ⭐⭐⭐⭐⭐ |

## 🚀 Empfohlene Sofort-Maßnahmen

### Quick Fix (Ohne Code-Änderung):

```bash
# Start mit optimierten Parametern
python kamera-auto-trigger/scripts/ai-had-kamera-auto-trigger.py \
    --trigger-duration 1.5 \
    --preview-fps 5 \
    --preview-width 480 \
    --preview-height 360 \
    --trigger-threshold 0.38 \
    --cooldown 45 \
    --ai-model bird-species
```

### Permanente Lösung (Code-Änderung):

**1. Ändere Default-Werte:**
```python
# ai-had-kamera-auto-trigger.py Zeile 115-117
parser.add_argument('--trigger-threshold', type=float, default=0.38, help='...')  # 0.45 → 0.38
parser.add_argument('--preview-fps', type=int, default=5, help='...')  # 3 → 5
parser.add_argument('--preview-width', type=int, default=480, help='...')  # 320 → 480
parser.add_argument('--preview-height', type=int, default=360, help='...')  # 240 → 360
```

**2. Optional: Konsistenz-Rate anpassen:**
```python
# stream_processor.py Zeile 418
if detection_rate >= 0.65:  # 70% → 65%
```

## 🧪 Test-Plan

### Phase 1: Parameter-Test (1 Stunde)
```bash
# Test mit erhöhten FPS
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 2 \
    --preview-fps 5 \
    --trigger-threshold 0.40
```

**Erwartetes Ergebnis:** 2-4 Trigger in 1 Stunde

### Phase 2: Vollständiger Test (4 Stunden)
```bash
# Test mit allen Optimierungen
python ai-had-kamera-auto-trigger.py \
    --trigger-duration 1.5 \
    --preview-fps 5 \
    --preview-width 480 \
    --preview-height 360 \
    --trigger-threshold 0.38
```

**Erwartetes Ergebnis:** 8-12 Trigger in 4 Stunden

### Phase 3: Langzeit-Test (12 Stunden)
```bash
# Produktions-Setup
./kamera-auto-trigger/start-vogel-beobachtung.sh
# Wähle: Threshold 0.38, FPS 5, Auflösung 480×360
```

**Erwartetes Ergebnis:** 25-35 Trigger in 12 Stunden

## 📈 Monitoring während Tests

### Wichtige Metriken:
```bash
# Während Auto-Trigger läuft, beobachte:
1. FPS (sollte ~5 sein)
2. CPU-Last (sollte <60% bleiben)
3. Trigger-Rate (Ziel: 2-3/Stunde)
4. False Positives (sollte <10% sein)
```

### Log-Analyse:
```bash
# Prüfe wie oft "Vogel erkannt" erscheint
grep "🐦 Vogel erkannt" /pfad/zu/logs

# Prüfe Trigger-Rate
grep "✅ TRIGGER!" /pfad/zu/logs | wc -l
```

## 🔧 Zusätzliche Optimierungen

### CPU-Threads erhöhen (falls nötig):
```python
# Wenn CPU-Last OK ist, erhöhe Threads
os.environ['OMP_NUM_THREADS'] = '3'  # 2 → 3
```

### YOLOv8 Modell-Größe anpassen:
```bash
# Verwende kleineres Modell für schnellere Inferenz
--ai-model yolov8n  # nano (kleinster, schnellster)
```

## ✅ Zusammenfassung

**Hauptproblem:** 3 FPS sind zu wenig für zuverlässige Trigger bei 2s Duration + 70% Konsistenz

**Beste Lösung:** 
```bash
--preview-fps 5 \
--preview-width 480 \
--preview-height 360 \
--trigger-threshold 0.38 \
--trigger-duration 1.5
```

**Erwartete Verbesserung:** +300% mehr Trigger (zurück auf vorheriges Niveau)
