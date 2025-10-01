#!/usr/bin/env python3
"""
Emoji-Validator für Vogel-Kamera-Linux Projekt
==============================================

Überprüft alle Markdown-Dateien im Projekt auf defekte oder nicht erkannte Emojis.

Features:
- Erkennt defekte Emojis (� Replacement Character)
- Prüft README.md und alle Dokumentationsdateien
- Scannt Wiki-Dateien
- Gibt detaillierte Berichte mit Zeilennummern aus
- Schlägt Korrekturen vor

Verwendung:
    python3 tools/check_emojis.py
    python3 tools/check_emojis.py --fix  # Automatische Korrektur (experimentell)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import unicodedata

class EmojiChecker:
    """Überprüft Dateien auf defekte oder problematische Emojis."""
    
    # Bekannte defekte Emoji-Muster
    BROKEN_PATTERNS = [
        '�',  # Unicode Replacement Character
        '\ufffd',  # Replacement Character (escaped)
        '??',  # Doppelte Fragezeichen (oft bei Encoding-Problemen)
        '\ufe0f\ufe0f',  # Doppelter Variant Selector
    ]
    
    # Häufige Emoji-Korrekturen basierend auf Kontext
    EMOJI_SUGGESTIONS = {
        'System-Monitoring': '📊',
        'Performance-Optimierung': '⚡',
        'Bereitschaftschecks': '🚨',
        'Temperatur-Überwachung': '🌡️',
        'Speicher-Management': '💾',
        'Load-Awareness': '📈',
        'CPU': '🖥️',
        'Warnung': '⚠️',
        'Fehler': '❌',
        'Erfolg': '✅',
        'Info': 'ℹ️',
    }
    
    def __init__(self, project_root: str = None):
        """Initialisiert den Emoji-Checker."""
        if project_root is None:
            # Automatisch das Projekt-Root-Verzeichnis finden
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.issues: List[Dict] = []
        self.files_checked = 0
        self.issues_found = 0
    
    def find_markdown_files(self) -> List[Path]:
        """Findet alle Markdown-Dateien im Projekt."""
        md_files = []
        
        # Hauptverzeichnis und Unterordner
        search_dirs = [
            self.project_root,
            self.project_root / 'docs',
            self.project_root / 'wiki-content',
            self.project_root / 'releases',
            self.project_root / 'veranstaltungen',
            self.project_root / '3d-konstruktion',
            self.project_root / 'assets',
            self.project_root / 'git-automation',
            self.project_root / 'wiki-sync',
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                md_files.extend(search_dir.rglob('*.md'))
        
        # Deduplizieren
        return list(set(md_files))
    
    def check_file(self, file_path: Path) -> List[Dict]:
        """Überprüft eine einzelne Datei auf defekte Emojis."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Prüfe auf bekannte defekte Muster
                for pattern in self.BROKEN_PATTERNS:
                    if pattern in line:
                        # Versuche Kontext zu erkennen
                        suggestion = self._suggest_emoji(line)
                        
                        issues.append({
                            'file': file_path.relative_to(self.project_root),
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern,
                            'suggestion': suggestion
                        })
                
                # Prüfe auf problematische Unicode-Zeichen
                for char_pos, char in enumerate(line):
                    if unicodedata.category(char) == 'Co':  # Private Use Area
                        issues.append({
                            'file': file_path.relative_to(self.project_root),
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': f'Private Use Character: {char}',
                            'suggestion': None
                        })
        
        except UnicodeDecodeError as e:
            issues.append({
                'file': file_path.relative_to(self.project_root),
                'line': 0,
                'content': f'Encoding-Fehler: {str(e)}',
                'pattern': 'ENCODING_ERROR',
                'suggestion': 'Datei mit UTF-8 Encoding neu speichern'
            })
        except Exception as e:
            print(f"⚠️  Fehler beim Lesen von {file_path}: {e}", file=sys.stderr)
        
        return issues
    
    def _suggest_emoji(self, line: str) -> str:
        """Schlägt ein passendes Emoji basierend auf dem Kontext vor."""
        line_lower = line.lower()
        
        for keyword, emoji in self.EMOJI_SUGGESTIONS.items():
            if keyword.lower() in line_lower:
                return emoji
        
        return '❓'  # Fallback
    
    def check_all_files(self) -> None:
        """Überprüft alle Markdown-Dateien im Projekt."""
        print("🔍 Suche nach Markdown-Dateien...")
        md_files = self.find_markdown_files()
        print(f"📄 {len(md_files)} Dateien gefunden\n")
        
        for file_path in sorted(md_files):
            self.files_checked += 1
            file_issues = self.check_file(file_path)
            
            if file_issues:
                self.issues.extend(file_issues)
                self.issues_found += len(file_issues)
    
    def generate_report(self) -> str:
        """Erstellt einen detaillierten Bericht."""
        report = []
        report.append("=" * 80)
        report.append("🔍 EMOJI-VALIDIERUNGS-BERICHT")
        report.append("=" * 80)
        report.append(f"📊 Statistik:")
        report.append(f"   - Überprüfte Dateien: {self.files_checked}")
        report.append(f"   - Gefundene Probleme: {self.issues_found}")
        report.append("")
        
        if not self.issues:
            report.append("✅ Keine defekten Emojis gefunden!")
            report.append("   Alle Dateien sind in Ordnung.")
        else:
            report.append("⚠️  GEFUNDENE PROBLEME:")
            report.append("")
            
            # Gruppiere nach Datei
            by_file = {}
            for issue in self.issues:
                file_str = str(issue['file'])
                if file_str not in by_file:
                    by_file[file_str] = []
                by_file[file_str].append(issue)
            
            for file_path in sorted(by_file.keys()):
                file_issues = by_file[file_path]
                report.append(f"📄 {file_path}")
                report.append("-" * 80)
                
                for issue in file_issues:
                    report.append(f"   Zeile {issue['line']:4d}: {issue['pattern']}")
                    report.append(f"   Inhalt: {issue['content'][:70]}...")
                    if issue['suggestion']:
                        report.append(f"   💡 Vorschlag: {issue['suggestion']}")
                    report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def fix_file(self, file_path: Path, dry_run: bool = True) -> int:
        """Versucht, defekte Emojis in einer Datei zu korrigieren."""
        fixes = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            modified = False
            
            for line in lines:
                new_line = line
                line_modified = False
                
                # Spezialfall: Doppelter Variant Selector (nur einen entfernen)
                if '\ufe0f\ufe0f' in new_line:
                    new_line = new_line.replace('\ufe0f\ufe0f', '\ufe0f')
                    fixes += new_line.count('\ufe0f\ufe0f') + 1
                    line_modified = True
                    modified = True
                
                # Prüfe ob diese Zeile defekte Emojis enthält
                if any(pattern in new_line for pattern in self.BROKEN_PATTERNS if pattern not in ['??', '\ufe0f\ufe0f']):
                    suggestion = self._suggest_emoji(line)
                    
                    # Ersetze alle Vorkommen des Replacement Characters
                    for pattern in self.BROKEN_PATTERNS:
                        if pattern in new_line and pattern not in ['??', '\ufe0f\ufe0f']:
                            # Zähle Vorkommen
                            count = new_line.count(pattern)
                            if count > 0:
                                new_line = new_line.replace(pattern, suggestion)
                                fixes += count
                                line_modified = True
                
                if line_modified:
                    modified = True
                
                new_lines.append(new_line)
            
            if modified and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"✅ {file_path.relative_to(self.project_root)}: {fixes} Korrekturen angewendet")
            elif modified:
                print(f"🔍 {file_path.relative_to(self.project_root)}: {fixes} Korrekturen möglich (Dry-Run)")
        
        except Exception as e:
            print(f"❌ Fehler beim Korrigieren von {file_path}: {e}", file=sys.stderr)
        
        return fixes
    
    def fix_all_files(self, dry_run: bool = True) -> int:
        """Versucht, alle defekten Emojis zu korrigieren."""
        total_fixes = 0
        
        if dry_run:
            print("\n🔍 DRY-RUN: Keine Dateien werden geändert\n")
        else:
            print("\n⚠️  ACHTUNG: Dateien werden automatisch korrigiert!\n")
        
        # Gruppiere Issues nach Datei
        by_file = {}
        for issue in self.issues:
            file_path = self.project_root / issue['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(issue)
        
        for file_path in sorted(by_file.keys()):
            fixes = self.fix_file(file_path, dry_run)
            total_fixes += fixes
        
        return total_fixes


def main():
    """Hauptfunktion."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Überprüft alle Markdown-Dateien auf defekte Emojis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 tools/check_emojis.py                 # Prüfe alle Dateien
  python3 tools/check_emojis.py --fix-dry-run   # Zeige mögliche Korrekturen
  python3 tools/check_emojis.py --fix           # Korrigiere automatisch (Vorsicht!)
        """
    )
    
    parser.add_argument(
        '--fix-dry-run',
        action='store_true',
        help='Zeige mögliche Korrekturen ohne Dateien zu ändern'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Korrigiere defekte Emojis automatisch (VORSICHT!)'
    )
    
    parser.add_argument(
        '--project-root',
        type=str,
        help='Pfad zum Projekt-Root-Verzeichnis (Standard: Auto-Erkennung)'
    )
    
    args = parser.parse_args()
    
    # Erstelle Checker
    checker = EmojiChecker(args.project_root)
    
    # Überprüfe alle Dateien
    checker.check_all_files()
    
    # Generiere Bericht
    report = checker.generate_report()
    print(report)
    
    # Korrigiere falls gewünscht
    if args.fix_dry_run or args.fix:
        print("\n" + "=" * 80)
        print("🔧 KORREKTUR-MODUS")
        print("=" * 80)
        
        dry_run = not args.fix
        total_fixes = checker.fix_all_files(dry_run=dry_run)
        
        print(f"\n📊 Gesamt: {total_fixes} Korrekturen {'möglich' if dry_run else 'angewendet'}")
        
        if dry_run and total_fixes > 0:
            print("\n💡 Tipp: Verwende --fix um die Korrekturen anzuwenden")
    
    # Exit-Code
    sys.exit(1 if checker.issues_found > 0 else 0)


if __name__ == '__main__':
    main()
