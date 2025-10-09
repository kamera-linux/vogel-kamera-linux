# 📚 Wiki-Syn├── wiki-sync/
│   ├── wiki-pull.sh      # Einfaches Pull-Skript
│   ├── wiki-push.sh      # Einfaches Push-Skript
│   └── WIKI-SYNC-SETUP.md # Diese Dokumentationetup - Anleitung

Das Wiki-Sync-System ist jetzt vollständig eingerichtet und funktional!

## 🔧 **Eingerichtete Struktur**

```
vogel-kamera-linux/
├── wiki-sync/
│   ├── wiki_sync.py      # Haupt-Sync-Skript
│   └── README.md         # Dokumentation
├── wiki-repo/            # Geklontes GitHub Wiki Repository  
├── wiki-content -> wiki-repo  # Softlink für einfachen Zugriff
└── tools/
    ├── wiki-pull.sh      # Einfaches Pull-Skript
    └── wiki-push.sh      # Einfaches Push-Skript
```

## 🚀 **Verwendung**

### **Wiki-Inhalte vom GitHub holen**
```bash
wiki-sync/wiki-pull.sh
# oder direkt:
cd wiki-sync && python3 wiki_sync.py pull
```

### **Lokale Änderungen zu GitHub synchronisieren**
```bash  
wiki-sync/wiki-push.sh
# oder direkt:
cd wiki-sync && python3 wiki_sync.py sync
```

### **Wiki-Dateien bearbeiten**
```bash
# Direkter Zugriff über Softlink
ls wiki-content/
nano wiki-content/Home.md
```

## ✅ **Status: FUNKTIONAL**

- ✅ Wiki-Repository geklont
- ✅ Softlink erstellt (`wiki-content` → `wiki-repo`)  
- ✅ Pull-Funktionalität getestet
- ✅ Push-Funktionalität getestet
- ✅ SSH-Authentifizierung funktioniert

Das System ist bereit für den produktiven Einsatz!