#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netzwerkqualitäts-Test für Vogel-Kamera-System
Testet die Verbindung zwischen lokalem PC und Raspberry Pi

Aufruf: python test-network-quality.py
"""

import paramiko
import time
import subprocess
import os
import tempfile
from datetime import datetime
from config import config

def test_network_quality():
    """Umfassender Netzwerkqualitäts-Test"""
    
    print("=" * 70)
    print("🌐 NETZWERKQUALITÄTS-TEST")
    print("=" * 70)
    print()
    
    # Konfiguration laden
    remote_host = config.get_remote_host_config()
    hostname = remote_host['hostname']
    
    print(f"📍 Ziel: {hostname}")
    print(f"⏰ Test-Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # ========================================================================
    # 1. PING-TEST (Latenz & Paketverlust)
    # ========================================================================
    print("─" * 70)
    print("1️⃣  PING-TEST (Latenz & Paketverlust)")
    print("─" * 70)
    
    try:
        # 20 Ping-Pakete senden
        ping_result = subprocess.run(
            ["ping", "-c", "20", "-i", "0.2", hostname],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if ping_result.returncode == 0:
            output = ping_result.stdout
            
            # Parse Statistiken
            for line in output.split('\n'):
                if 'packets transmitted' in line:
                    print(f"   📦 {line.strip()}")
                elif 'rtt min/avg/max/mdev' in line or 'min/avg/max' in line:
                    parts = line.split('=')
                    if len(parts) > 1:
                        times = parts[1].strip().split()[0]
                        min_t, avg_t, max_t = times.split('/')[:3]
                        
                        print(f"   ⏱️  Latenz:")
                        print(f"      • Minimum:     {min_t} ms")
                        print(f"      • Durchschnitt: {avg_t} ms")
                        print(f"      • Maximum:     {max_t} ms")
                        
                        # Bewertung
                        avg_val = float(avg_t)
                        if avg_val < 2:
                            status = "🟢 Ausgezeichnet (< 2ms)"
                        elif avg_val < 5:
                            status = "🟢 Sehr gut (< 5ms)"
                        elif avg_val < 10:
                            status = "🟡 Gut (< 10ms)"
                        elif avg_val < 50:
                            status = "🟡 Akzeptabel (< 50ms)"
                        else:
                            status = "🔴 Langsam (> 50ms)"
                        
                        print(f"      • Bewertung:   {status}")
        else:
            print("   ❌ Ping fehlgeschlagen!")
    except Exception as e:
        print(f"   ❌ Fehler beim Ping-Test: {e}")
    
    print()
    
    # ========================================================================
    # 2. SSH-VERBINDUNGSZEIT
    # ========================================================================
    print("─" * 70)
    print("2️⃣  SSH-VERBINDUNGSZEIT")
    print("─" * 70)
    
    connection_times = []
    try:
        for i in range(5):
            start = time.time()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                remote_host['hostname'],
                username=remote_host['username'],
                key_filename=remote_host['key_filename'],
                timeout=10
            )
            ssh.close()
            end = time.time()
            
            conn_time = (end - start) * 1000  # in ms
            connection_times.append(conn_time)
            print(f"   Versuch {i+1}: {conn_time:.1f} ms")
        
        avg_conn = sum(connection_times) / len(connection_times)
        min_conn = min(connection_times)
        max_conn = max(connection_times)
        
        print()
        print(f"   📊 Statistik:")
        print(f"      • Minimum:     {min_conn:.1f} ms")
        print(f"      • Durchschnitt: {avg_conn:.1f} ms")
        print(f"      • Maximum:     {max_conn:.1f} ms")
        
        # Bewertung
        if avg_conn < 100:
            status = "🟢 Sehr schnell"
        elif avg_conn < 300:
            status = "🟢 Schnell"
        elif avg_conn < 500:
            status = "🟡 Akzeptabel"
        else:
            status = "🔴 Langsam"
        print(f"      • Bewertung:   {status}")
        
    except Exception as e:
        print(f"   ❌ Fehler beim SSH-Test: {e}")
    
    print()
    
    # ========================================================================
    # 3. BANDBREITEN-TEST (SCP)
    # ========================================================================
    print("─" * 70)
    print("3️⃣  BANDBREITEN-TEST (SCP Upload/Download)")
    print("─" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            remote_host['hostname'],
            username=remote_host['username'],
            key_filename=remote_host['key_filename']
        )
        
        # SCP-Client erstellen
        from scp import SCPClient
        scp = SCPClient(ssh.get_transport())
        
        # Test-Datei erstellen (10 MB)
        test_size_mb = 10
        test_size_bytes = test_size_mb * 1024 * 1024
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(os.urandom(test_size_bytes))
        
        # UPLOAD-Test
        print(f"   📤 Upload-Test ({test_size_mb} MB)...")
        remote_test_file = f"/tmp/network_test_{int(time.time())}.dat"
        
        start = time.time()
        scp.put(tmp_path, remote_test_file)
        end = time.time()
        
        upload_time = end - start
        upload_speed = (test_size_mb / upload_time) if upload_time > 0 else 0
        
        print(f"      • Zeit: {upload_time:.2f} s")
        print(f"      • Geschwindigkeit: {upload_speed:.2f} MB/s ({upload_speed*8:.1f} Mbit/s)")
        
        if upload_speed > 50:
            upload_status = "🟢 Sehr schnell"
        elif upload_speed > 20:
            upload_status = "🟢 Schnell"
        elif upload_speed > 10:
            upload_status = "🟡 Akzeptabel"
        else:
            upload_status = "🔴 Langsam"
        print(f"      • Bewertung: {upload_status}")
        
        print()
        
        # DOWNLOAD-Test
        print(f"   📥 Download-Test ({test_size_mb} MB)...")
        download_path = tmp_path + ".download"
        
        start = time.time()
        scp.get(remote_test_file, download_path)
        end = time.time()
        
        download_time = end - start
        download_speed = (test_size_mb / download_time) if download_time > 0 else 0
        
        print(f"      • Zeit: {download_time:.2f} s")
        print(f"      • Geschwindigkeit: {download_speed:.2f} MB/s ({download_speed*8:.1f} Mbit/s)")
        
        if download_speed > 50:
            download_status = "🟢 Sehr schnell"
        elif download_speed > 20:
            download_status = "🟢 Schnell"
        elif download_speed > 10:
            download_status = "🟡 Akzeptabel"
        else:
            download_status = "🔴 Langsam"
        print(f"      • Bewertung: {download_status}")
        
        # Aufräumen
        ssh.exec_command(f"rm -f {remote_test_file}")
        os.remove(tmp_path)
        if os.path.exists(download_path):
            os.remove(download_path)
        
        scp.close()
        ssh.close()
        
    except Exception as e:
        print(f"   ❌ Fehler beim Bandbreiten-Test: {e}")
    
    print()
    
    # ========================================================================
    # 4. REMOTE-BEFEHLS-LATENZ
    # ========================================================================
    print("─" * 70)
    print("4️⃣  REMOTE-BEFEHLS-LATENZ")
    print("─" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            remote_host['hostname'],
            username=remote_host['username'],
            key_filename=remote_host['key_filename']
        )
        
        command_times = []
        for i in range(5):
            start = time.time()
            stdin, stdout, stderr = ssh.exec_command("echo 'test'")
            stdout.read()
            end = time.time()
            
            cmd_time = (end - start) * 1000  # in ms
            command_times.append(cmd_time)
            print(f"   Befehl {i+1}: {cmd_time:.1f} ms")
        
        avg_cmd = sum(command_times) / len(command_times)
        print()
        print(f"   📊 Durchschnitt: {avg_cmd:.1f} ms")
        
        if avg_cmd < 50:
            status = "🟢 Sehr schnell"
        elif avg_cmd < 100:
            status = "🟢 Schnell"
        elif avg_cmd < 200:
            status = "🟡 Akzeptabel"
        else:
            status = "🔴 Langsam"
        print(f"   📊 Bewertung: {status}")
        
        ssh.close()
        
    except Exception as e:
        print(f"   ❌ Fehler beim Befehls-Latenz-Test: {e}")
    
    print()
    
    # ========================================================================
    # ZUSAMMENFASSUNG
    # ========================================================================
    print("=" * 70)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 70)
    print()
    print("Die Netzwerkverbindung ist entscheidend für:")
    print("   • Video-Streaming (Preview): Niedrige Latenz wichtig")
    print("   • Datei-Transfer (Recordings): Hohe Bandbreite wichtig")
    print("   • Remote-Befehle: Niedrige Latenz wichtig")
    print()
    print("✅ Test abgeschlossen!")
    print()

if __name__ == "__main__":
    try:
        test_network_quality()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n\n❌ Fehler beim Test: {e}")
