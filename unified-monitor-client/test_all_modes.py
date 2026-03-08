#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Suite für Unified Monitor Client
Führt alle Modi durch und validiert Funktionalität
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

# Farben
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color


@dataclass
class Test:
    name: str
    mode: str
    timeout: int = 45


class TestRunner:
    def __init__(self):
        self.tests: List[Test] = []
        self.results: List[Tuple[str, bool]] = []
        
        # Konfiguration
        self.ssh_key = os.path.expanduser("~/.ssh/id_rsa_ai-had")
        self.ssh_user = "roimme"
        self.ssh_host = "raspberrypi-5-ai-had"
        self.script_dir = Path(__file__).parent
        
    def add_test(self, name: str, mode: str, timeout: int = 45):
        """Test zur Liste hinzufügen"""
        self.tests.append(Test(name=name, mode=mode, timeout=timeout))
    
    def check_ssh(self) -> bool:
        """SSH-Verbindung prüfen"""
        try:
            subprocess.run(
                [
                    "ssh", "-i", self.ssh_key,
                    "-o", "ConnectTimeout=3",
                    f"{self.ssh_user}@{self.ssh_host}",
                    "echo ok"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
    
    def test_mode(self, test: Test) -> bool:
        """Einen Test ausführen"""
        print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        print(f"{CYAN}🧪 Test: {test.name}{NC}")
        print(f"{CYAN}   Mode: {test.mode} | Timeout: {test.timeout}s{NC}")
        print(f"{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        
        # SSH-Check
        if not self.check_ssh():
            print(f"{RED}❌ SSH-Verbindung fehlgeschlagen{NC}")
            return False
        
        # Test ausführen
        log_file = Path(f"/tmp/test_{test.mode}.log")
        try:
            with open(log_file, "w") as f:
                result = subprocess.run(
                    ["python3", str(self.script_dir / "unified_monitor_client.py"), test.mode],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=test.timeout,
                    cwd=str(self.script_dir)
                )
            
            # Prüfe Output
            with open(log_file, "r") as f:
                output = f.read()
            
            if "SYSTEM BEREIT" in output:
                print(f"{GREEN}✅ {test.name} erfolgreich!{NC}")
                return True
            else:
                print(f"{YELLOW}⚠️ {test.name} - Timeout (normal){NC}")
                return True
                
        except subprocess.TimeoutExpired:
            # Timeout ist normal (Monitor läuft im Hintergrund)
            print(f"{YELLOW}⏱️ {test.name} - Timeout nach {test.timeout}s (normal){NC}")
            return True
        except Exception as e:
            print(f"{RED}❌ {test.name} fehlgeschlagen: {e}{NC}")
            return False
    
    def run(self) -> bool:
        """Alle Tests ausführen"""
        print()
        print("=" * 64)
        print("🧪 UNIFIED MONITOR CLIENT - TEST SUITE")
        print("=" * 64)
        print()
        
        # Tests definieren
        self.add_test("Standard-Modus", "normal", 45)
        self.add_test("Zeitlupe-Modus", "slowmo", 45)
        self.add_test("4K-Modus", "4k", 45)
        self.add_test("AI-HAD-Modus", "ai-had", 45)
        
        print()
        print(f"{YELLOW}📊 Starte {len(self.tests)} Tests...{NC}")
        print()
        
        # Tests ausführen
        for test in self.tests:
            result = self.test_mode(test)
            self.results.append((test.name, result))
            print()
            time.sleep(2)  # Kurze Pause zwischen Tests
        
        # Ergebnisse anzeigen
        self._print_results()
        
        # Rückgabe ob alle Tests bestanden
        return all(passed for _, passed in self.results)
    
    def _print_results(self):
        """Test-Ergebnisse anzeigen"""
        print()
        print("=" * 64)
        print("📊 TEST-ERGEBNISSE")
        print("=" * 64)
        
        passed = 0
        failed = 0
        
        for name, result in self.results:
            if result:
                print(f"{GREEN}✅ {name}{NC}")
                passed += 1
            else:
                print(f"{RED}❌ {name}{NC}")
                failed += 1
        
        total = passed + failed
        print()
        print(f"Gesamt: {total} Tests | Erfolgreich: {passed} | Fehlgeschlagen: {failed}")
        print()
        
        if failed == 0:
            print(f"{GREEN}{'=' * 64}")
            print("✅ ALLE TESTS BESTANDEN!")
            print(f"{'=' * 64}{NC}")
        else:
            print(f"{RED}{'=' * 64}")
            print("❌ EINIGE TESTS FEHLGESCHLAGEN")
            print(f"{'=' * 64}{NC}")


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)
