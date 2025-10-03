# 🔒 Branch Protection für GitHub Actions einrichten

## 🎯 Problem

Dein Repository hat Branch Protection Rules aktiv, die **alle** Pushes auf `main` blockieren:

```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Cannot update this protected ref.
remote: - Changes must be made through a pull request.
```

Das betrifft auch **GitHub Actions** - sie können nicht direkt committen und pushen.

## ✅ Lösung: GitHub Actions von Branch Protection ausnehmen

### Option 1: GitHub Actions als Bypass hinzufügen (EMPFOHLEN)

**Schritt-für-Schritt Anleitung:**

1. **Gehe zu Repository Settings:**
   ```
   https://github.com/roimme65/vogel-kamera-linux/settings
   ```

2. **Navigiere zu Rules:**
   - Sidebar → "Rules" → "Rulesets"
   - Oder direkt: https://github.com/roimme65/vogel-kamera-linux/rules

3. **Finde die aktive Rule für main:**
   - Klicke auf die Ruleset die `main` betrifft
   - Meist heißt sie "main" oder "Branch protection"

4. **Klicke "Edit"** (oben rechts)

5. **Scroll zu "Bypass list":**
   - Klicke "Add bypass"
   - Wähle "Repository role: Actors" 
   - Wähle aus Dropdown: **"GitHub Actions"**
   - Klicke "Add bypass"

6. **Speichern:**
   - Scroll nach unten
   - Klicke "Save changes"

**Ergebnis:**
- ✅ Branch Protection bleibt aktiv für normale Pushes
- ✅ GitHub Actions kann direkt pushen
- ✅ Keine manuellen Merges nötig

---

### Option 2: Branch Protection Rule temporär ändern

Falls du keine Bypass-Option findest:

1. **Gehe zu Settings → Rules → Rulesets**

2. **Bearbeite die Rule:**
   - Finde "Restrict pushes that create matching branches"
   - Oder "Require pull request reviews before merging"

3. **Deaktiviere für Service Accounts:**
   - Suche nach "Allow service accounts to bypass"
   - Aktiviere diese Option

4. **Speichern**

---

### Option 3: Workflow auf anderem Branch laufen lassen

Falls du Branch Protection nicht ändern möchtest:

**`.github/workflows/update-youtube-stats.yml` ändern:**

```yaml
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
  
  # WICHTIG: Nur auf devel-Branch triggern
  push:
    branches:
      - devel-v1.2.0  # Statt main

jobs:
  update-stats:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
```

**Dann:**
1. Workflow pushed auf `devel-v1.2.0`
2. Du mergst manuell `devel-v1.2.0` → `main` wenn gewünscht

---

## 🔍 Aktuelles Verhalten (Workaround aktiv)

Die GitHub Action funktioniert **bereits** mit folgendem Hybrid-Ansatz:

1. ✅ Erstellt Branch: `youtube-stats-update-YYYYMMDD-HHMMSS`
2. ✅ Committed Änderungen auf Branch
3. ✅ Pusht Branch zu GitHub
4. 🔄 Versucht direkten Push auf `main`
5. ❌ Schlägt fehl (Branch Protection)
6. ℹ️ Branch bleibt für manuelles Merge

**Was du tun musst:**
- Gehe zu: https://github.com/roimme65/vogel-kamera-linux/branches
- Finde Branch: `youtube-stats-update-...`
- Klicke "Compare & pull request"
- Merge den PR

**Oder:**
```bash
# Lokal mergen
git checkout main
git pull
git merge origin/youtube-stats-update-YYYYMMDD-HHMMSS
git push origin main
git push origin --delete youtube-stats-update-YYYYMMDD-HHMMSS
```

---

## 🎯 Empfehlung

**Für automatische Updates:** 
→ **Option 1** (GitHub Actions Bypass) ist die beste Lösung!

**Vorteile:**
- ✅ Vollautomatisch
- ✅ Branch Protection bleibt für Entwickler aktiv
- ✅ Nur Service Accounts (wie GitHub Actions) können bypassen
- ✅ Keine manuellen Schritte nötig

**Setup-Zeit:** 2 Minuten

---

## 📚 GitHub Dokumentation

- [Managing rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository)
- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Bypass lists](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets#bypass-lists)

---

## ❓ Fragen?

Öffne ein Issue: https://github.com/roimme65/vogel-kamera-linux/issues

---

**🎉 Nach dem Setup läuft alles vollautomatisch! Keine weiteren manuellen Schritte nötig!**
