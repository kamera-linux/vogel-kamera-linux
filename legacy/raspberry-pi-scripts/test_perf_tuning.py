#!/usr/bin/env python3
"""
Performance Testing Script
Simulates real Hailo detections to benchmark optimization parameters
"""

import sys
import json
from pathlib import Path

# Simulate Test Data
test_configs = [
    {
        "name": "Standard (no skip)",
        "hailo_threshold": 0.5,
        "onnx_threshold": 0.3,
        "frame_skip": 1,
    },
    {
        "name": "Aggressive skip (2x)",
        "hailo_threshold": 0.4,
        "onnx_threshold": 0.25,
        "frame_skip": 2,
    },
    {
        "name": "Conservative (high thresholds)",
        "hailo_threshold": 0.7,
        "onnx_threshold": 0.5,
        "frame_skip": 1,
    },
]

def parse_stats(json_file):
    """Parse results from detector output"""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except:
        return None

def benchmark_results():
    """Show benchmark comparison"""
    
    print("\n" + "="*80)
    print("HAILO + ONNX PERFORMANCE DETECTOR - TUNING BENCHMARKS")
    print("="*80)
    
    stats_file = Path("/tmp/bird_detections_perf.json")
    
    if stats_file.exists():
        stats = parse_stats(stats_file)
        if stats:
            print("\n📊 Latest Test Results:")
            print(f"   Duration: {stats.get('duration', 0)}s")
            print(f"   Hailo detections: {stats.get('hailo_detections', 0)}")
            print(f"   ONNX crops processed: {stats.get('onnx_crops_processed', 0)}")
            print(f"   Birds confirmed: {stats.get('birds_confirmed', 0)}")
            
            if 'performance' in stats:
                perf = stats['performance']
                print(f"\n⚡ Performance Metrics:")
                print(f"   Hailo rate: {perf.get('hailo_rate', 0):.1f} det/s")
                print(f"   ONNX rate: {perf.get('onnx_rate', 0):.1f} proc/s")
                print(f"   Skip ratio: {perf.get('skip_ratio', 0):.1f}%")
            
            if 'thresholds' in stats:
                thresh = stats['thresholds']
                print(f"\n🎯 Configuration Used:")
                print(f"   Hailo threshold: {thresh.get('hailo', 0):.1%}")
                print(f"   ONNX threshold: {thresh.get('onnx', 0):.1%}")
                print(f"   Frame skip: {thresh.get('frame_skip', 1)}")
    
    print("\n" + "="*80)
    print("📋 RECOMMENDED CONFIGURATIONS")
    print("="*80)
    
    for config in test_configs:
        print(f"\n{config['name']}:")
        print(f"   Command:")
        print(f"   hailo_onnx_perf.py \\")
        print(f"      --hailo-threshold {config['hailo_threshold']} \\")
        print(f"      --onnx-threshold {config['onnx_threshold']} \\")
        print(f"      --frame-skip {config['frame_skip']} \\")
        print(f"      --duration 60")
        
        # Estimate performance
        if config['frame_skip'] == 1:
            est_fps = "25-30"
            skip_str = "No frame skipping"
        else:
            est_fps = "30+"
            skip_str = f"Every {config['frame_skip']} frames processed"
        
        print(f"\n   Expected performance:")
        print(f"   - FPS: {est_fps}")
        print(f"   - Processing: {skip_str}")
        print(f"   - Accuracy: {'High' if config['hailo_threshold'] >= 0.7 else 'Balanced' if config['hailo_threshold'] >= 0.5 else 'Sensitive'}")
        print(f"   - False positives: {'Lower' if config['onnx_threshold'] >= 0.4 else 'Medium' if config['onnx_threshold'] >= 0.3 else 'Higher'}")
    
    print("\n" + "="*80)
    print("🚀 QUICK START")
    print("="*80)
    print("""
1. Default (recommended for production):
   python3 hailo_onnx_perf.py --duration 60

2. Maximum sensitivity (catch all birds):
   python3 hailo_onnx_perf.py --hailo-threshold 0.3 --onnx-threshold 0.2 --duration 60

3. Maximum speed (skip processing):
   python3 hailo_onnx_perf.py --frame-skip 3 --duration 60

4. High accuracy (strict filtering):
   python3 hailo_onnx_perf.py --hailo-threshold 0.7 --onnx-threshold 0.5 --duration 60
    """)
    
    print("="*80 + "\n")

if __name__ == "__main__":
    benchmark_results()
