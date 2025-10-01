# Terminal Emoji Display Fix

## Problem
Git-Log zeigt Emoji-Zeichen als "❓❓" anstatt korrekte Emojis in der Ausgabe:
```
88ecbf9 ❓❓ Release v1.1.5
```

## Lösung

### 1. VS Code Terminal Schriftart konfigurieren
**Manuell via UI:**
1. VS Code öffnen
2. `Ctrl + ,` (Einstellungen)
3. Suchen: `terminal.integrated.fontFamily`
4. Wert setzen: `'DejaVu Sans Mono', 'Noto Color Emoji', monospace`
5. VS Code neustarten

**Via settings.json:**
```json
{
    "terminal.integrated.fontFamily": "'DejaVu Sans Mono', 'Noto Color Emoji', monospace",
    "terminal.integrated.fontSize": 14,
    "terminal.integrated.lineHeight": 1.2
}
```

### 2. Git-Konfiguration optimieren
```bash
# Unicode-Pfade nicht escapen
git config --global core.quotepath false

# Bessere Pager-Konfiguration
git config --global core.pager "less -r"

# Editor für Unicode
git config --global core.editor "code --wait"
```

### 3. System-Schriftarten prüfen
```bash
# Verfügbare Emoji-Fonts prüfen
fc-list | grep -i emoji

# Font-Cache aktualisieren
fc-cache -fv
```

### 4. Terminal-Umgebung
```bash
# Locale prüfen (sollte UTF-8 sein)
locale

# Aktuelle Terminal-Fähigkeiten
echo $TERM
```

## Test
Nach der Konfiguration testen:
```bash
# Emoji-Test
echo "🔖 📱 🎤"

# Git-Log-Test
git log --oneline -2

# Vollständiger Unicode-Test (Bash-kompatibel)
printf "\U1F516 \U1F4F1 \U1F3A4\n"
```

## Erwartetes Ergebnis
```
🔖 Release v1.1.5 - Veranstaltungsmanagement und LinuxDay.at Integration
```

## Hinweis
- Emoji-Support variiert zwischen Systemen
- Ubuntu benötigt manuelle Konfiguration im Gegensatz zu Raspbian
- VS Code Terminal erfordert spezielle Schriftart-Konfiguration
- Nach Änderungen ist ein Neustart von VS Code erforderlich