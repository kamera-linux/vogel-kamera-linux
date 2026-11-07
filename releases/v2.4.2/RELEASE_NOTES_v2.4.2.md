# 🐕 Release v2.4.2 - Erkennungsziele & Online-Hilfe

**Release Date:** 7. November 2026  
**Version:** 2.4.2  
**Vorgänger:** [v2.4.1](../v2.4.1/RELEASE_NOTES_v2.4.1.md)

---

## 🔧 Bug Fix

**Erkennungsziel ging nach Neustart verloren:** Wer in der Web-GUI 🐕 Hund, 🐈 Katze oder
„Alle 4“ gewählt hatte, fand nach einem Neustart des Containers (Update, Stromausfall) wieder
🐦 Vogel eingestellt. Beim Laden der gespeicherten Einstellung waren nur `bird` und `person`
erlaubt. Jetzt werden alle fünf Ziele korrekt übernommen. Mit Test.

---

## 📚 Online-Hilfe (❓ in der Web-GUI)

- **Zeitlupe:** richtige Profile – *Zeitlupe HQ* (2304×1296, 56 fps) und *Zeitlupe 120fps*
  (1536×864, 120 fps) – statt der alten Angaben 720p/120 fps und 1080p/60 fps; dazu die vier
  automatisch erzeugten Wiedergabe-Versionen (`_pb10fps`, `_pb20fps`, `_pb30fps`, Original)
- **Erkennungsziele:** alle fünf (Vogel, Mensch, Hund, Katze, Alle 4)
- **Neue Gruppe „Powerbank“** mit Farben, Warnung und automatischem Shutdown
- **Sync-Ziele:** erlaubte Pfade und Host-Key-Prüfung
- **Sicherheit:** Login-Limit, 8 h gültiger Login, Hinweis auf VPN statt Portfreigabe

## 📖 Wiki

Das [Wiki](https://github.com/kamera-linux/vogel-kamera-linux/wiki) ist komplett aktualisiert
(vorher Stand v2.2.6–v2.3.7), mit neuen Seiten **Powerbank** und **Security**.

---

## 🚀 Update

```bash
./ansible/build_and_deploy.sh --update
```

Nur Code und Web-GUI geändert – `--hotpatch` reicht ebenfalls. Danach Browser-Tab neu laden.

> Wer vor dem Update Hund, Katze oder „Alle 4“ eingestellt hatte: nach dem Update einmal neu wählen.
