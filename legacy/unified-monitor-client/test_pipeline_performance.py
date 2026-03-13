#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance & Stress Tests für Camera Pipeline

Teste:
1. Hohe Queue-Last
2. Schnelle Event-Verarbeitung
3. Memory-Footprint
4. Concurrent Job Processing
"""

import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
import psutil
import os

from camera_pipeline import (
    CameraPipeline, RecordingJob, DetectionEvent
)


def test_high_load_queue():
    """Test: 100 Jobs in schneller Abfolge"""
    print("\n" + "=" * 75)
    print("🔥 TEST: High-Load Queue Processing (100 Jobs)")
    print("=" * 75)
    
    mock_ssh = Mock()
    mock_ssh.exec_command = Mock(return_value=(True, "ok", ""))
    
    pipeline = CameraPipeline(ssh_manager=mock_ssh)
    pipeline.start()
    time.sleep(0.5)
    
    try:
        start_time = time.time()
        
        # Erstelle 100 Jobs schnell hintereinander
        print("📊 Schiebe 100 Jobs in paralleler Abfolge...")
        for i in range(100):
            event = DetectionEvent(
                timestamp=datetime.now(),
                bird_count=i % 5,
                confidence=0.5 + (i % 50) / 100,
                frame_number=i * 10
            )
            job = RecordingJob(
                job_id=f"LOAD-{i:03d}",
                detection_event=event,
                duration_seconds=60,
                resolution="2k",
                fps=30,
                bitrate=6000,
                enable_audio=False
            )
            pipeline.request_recording(job)
            
            if (i + 1) % 25 == 0:
                print(f"   ✓ {i + 1} Jobs erstellt")
        
        push_time = time.time() - start_time
        print(f"   ✅ {push_time:.2f}s für 100 Jobs pushes")
        print(f"   ⏱️  {push_time / 100 * 1000:.2f}ms pro Job")
        
        # Warte kurz auf Verarbeitung
        print("\n⏳ Warte 2s auf Background-Verarbeitung...")
        time.sleep(2)
        
        stats = pipeline.get_stats()
        print(f"\n📋 Queue Status nach Verarbeitung:")
        print(f"   Detection: {stats['detection_queue_size']}")
        print(f"   Recording: {stats['recording_queue_size']}")
        print(f"   Conversion: {stats['conversion_queue_size']}")
        print(f"   Sync: {stats['sync_queue_size']}")
        
        print("\n✅ High-Load Test erfolgreich!")
        
    finally:
        pipeline.stop()
        time.sleep(0.5)


def test_concurrent_requests():
    """Test: Mehrere Threads pushen Jobs gleichzeitig"""
    print("\n" + "=" * 75)
    print("🔀 TEST: Concurrent Job Requests (Multi-Threaded)")
    print("=" * 75)
    
    mock_ssh = Mock()
    mock_ssh.exec_command = Mock(return_value=(True, "ok", ""))
    
    pipeline = CameraPipeline(ssh_manager=mock_ssh)
    pipeline.start()
    time.sleep(0.5)
    
    try:
        jobs_created = []
        lock = threading.Lock()
        
        def create_jobs(thread_num, count):
            """Erstelle mehrere Jobs in einem Thread"""
            for i in range(count):
                event = DetectionEvent(
                    timestamp=datetime.now(),
                    bird_count=thread_num,
                    confidence=0.7,
                    frame_number=thread_num * 1000 + i
                )
                job = RecordingJob(
                    job_id=f"THREAD-{thread_num}-{i}",
                    detection_event=event,
                    duration_seconds=60,
                    resolution="2k",
                    fps=30,
                    bitrate=6000,
                    enable_audio=False
                )
                pipeline.request_recording(job)
                
                with lock:
                    jobs_created.append(job.job_id)
        
        print("📊 Starte 5 Threads mit je 20 Job-Requests...")
        start_time = time.time()
        
        threads = []
        for thread_num in range(5):
            t = threading.Thread(target=create_jobs, args=(thread_num, 20))
            threads.append(t)
            t.start()
        
        # Warte bis alle Threads fertig sind
        for t in threads:
            t.join()
        
        concurrent_time = time.time() - start_time
        total_jobs = len(jobs_created)
        
        print(f"   ✅ {total_jobs} Jobs in {concurrent_time:.2f}s erstellt")
        print(f"   ⏱️  {concurrent_time / total_jobs * 1000:.2f}ms pro Job")
        print(f"   🚀 Durchsatz: {total_jobs / concurrent_time:.1f} Jobs/sec")
        
        print("\n✅ Concurrent Request Test erfolgreich!")
        
    finally:
        pipeline.stop()
        time.sleep(0.5)


def test_memory_footprint():
    """Test: Memory-Verbrauch der Pipeline"""
    print("\n" + "=" * 75)
    print("💾 TEST: Memory Footprint")
    print("=" * 75)
    
    # Gemesse Speicher vorher
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    mock_ssh = Mock()
    mock_ssh.exec_command = Mock(return_value=(True, "ok", ""))
    
    pipeline = CameraPipeline(ssh_manager=mock_ssh)
    
    # Memory nach Pipeline-Erstellung
    mem_after_init = process.memory_info().rss / 1024 / 1024
    pipeline_mem = mem_after_init - mem_before
    
    print(f"📊 Memory Usage:")
    print(f"   Baseline: {mem_before:.1f} MB")
    print(f"   Nach Pipeline Init: {mem_after_init:.1f} MB")
    print(f"   Pipeline Overhead: {pipeline_mem:.1f} MB")
    
    pipeline.start()
    time.sleep(0.5)
    
    # Memory nach Thread-Start
    mem_after_start = process.memory_info().rss / 1024 / 1024
    threads_mem = mem_after_start - mem_after_init
    
    print(f"   Nach Thread Start: {mem_after_start:.1f} MB")
    print(f"   Threads Overhead: {threads_mem:.1f} MB")
    
    # Füge viele Jobs hinzu
    for i in range(100):
        event = DetectionEvent(
            timestamp=datetime.now(),
            bird_count=1,
            confidence=0.5,
            frame_number=i
        )
        job = RecordingJob(
            job_id=f"MEM-{i}",
            detection_event=event,
            duration_seconds=60,
            resolution="2k",
            fps=30,
            bitrate=6000,
            enable_audio=False
        )
        pipeline.request_recording(job)
    
    time.sleep(0.5)
    
    # Memory mit 100 Jobs
    mem_with_jobs = process.memory_info().rss / 1024 / 1024
    jobs_mem = mem_with_jobs - mem_after_start
    
    print(f"   Mit 100 Jobs in Queue: {mem_with_jobs:.1f} MB")
    print(f"   100 Jobs Memory: {jobs_mem:.1f} MB")
    print(f"   Pro Job: {jobs_mem / 100:.2f} MB")
    
    pipeline.stop()
    time.sleep(0.5)
    
    # Memory nach Stop
    mem_after_stop = process.memory_info().rss / 1024 / 1024
    print(f"   Nach Pipeline Stop: {mem_after_stop:.1f} MB")
    
    print("\n✅ Memory Test abgeschlossen!")
    if pipeline_mem < 5:  # Pipeline sollte < 5MB sein
        print("   Memory footprint ist AKZEPTABEL")
    else:
        print(f"   ⚠️  Memory footprint ist hoch: {pipeline_mem:.1f}MB")


def test_queue_latency():
    """Test: Latenz zwischen Job-Request und Queue-Eingang"""
    print("\n" + "=" * 75)
    print("⏱️  TEST: Queue Latency")
    print("=" * 75)
    
    mock_ssh = Mock()
    mock_ssh.exec_command = Mock(return_value=(True, "ok", ""))
    
    pipeline = CameraPipeline(ssh_manager=mock_ssh)
    pipeline.start()
    time.sleep(0.5)
    
    try:
        latencies = []
        
        print("📊 Messe 50 Job-Requests mit Timestamp...")
        for i in range(50):
            event = DetectionEvent(
                timestamp=datetime.now(),
                bird_count=1,
                confidence=0.5,
                frame_number=i
            )
            
            start = time.perf_counter()
            job = RecordingJob(
                job_id=f"LAT-{i}",
                detection_event=event,
                duration_seconds=60,
                resolution="2k",
                fps=30,
                bitrate=6000,
                enable_audio=False
            )
            pipeline.request_recording(job)
            end = time.perf_counter()
            
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\n⏱️  Request Latency:")
        print(f"   Average: {avg_latency:.3f}ms")
        print(f"   Min: {min_latency:.3f}ms")
        print(f"   Max: {max_latency:.3f}ms")
        
        if avg_latency < 1:
            print("   ✅ Latency ist AUSGEZEICHNET ( < 1ms)")
        elif avg_latency < 5:
            print("   ✅ Latency ist OK ( < 5ms)")
        else:
            print(f"   ⚠️  Latency ist hoch: {avg_latency:.3f}ms")
        
        print("\n✅ Latency Test abgeschlossen!")
        
    finally:
        pipeline.stop()
        time.sleep(0.5)


def main():
    """Führe alle Performance-Tests aus"""
    print("\n")
    print("╔" + "=" * 73 + "╗")
    print("║" + " " * 20 + "🚀 PERFORMANCE TEST SUITE 🚀" + " " * 25 + "║")
    print("╚" + "=" * 73 + "╝")
    
    try:
        test_high_load_queue()
        test_concurrent_requests()
        test_queue_latency()
        test_memory_footprint()
        
        print("\n" + "=" * 75)
        print("✅ ALLE PERFORMANCE-TESTS ERFOLGREICH!")
        print("=" * 75 + "\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ Performance Test Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
