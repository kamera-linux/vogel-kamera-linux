# 🐧 Release v2.3.6 - Ansible Toolchain Verbesserung

**Release Date:** 27. Juli 2026  
**Version:** 2.3.6  
**Status:** ✅ Production Ready

---

## 📋 Übersicht

v2.3.6 behebt kritische Probleme in der Ansible-Toolchain und verbessert die Zuverlässigkeit bei der Bereitstellung auf verschiedenen Build-Hosts.

---

## 🔧 Bug Fixes

### Ansible Tool-Lookup priorisiert lokale Venvs

**Problem:**
- Alte, beschädigte Python-Installationen in `~/.local/bin/` würden Ansible-Playbooks überlagern
- Konnte zu unerklärten Fehlern beim Deployment führen

**Lösung:**
```python
# Neue Tool-Lookup Priorität:
1. Lokale Venvs: ansible-venv-local/bin/
2. Lokale Venvs: .venv/bin/
3. Home Venvs: ~/ansible-venv/bin/
4. System PATH
5. Fallback: ~/.local/bin/ (alte Installationen)
```

**Auswirkung:**
- ✅ Zuverlässigere Ansible-Ausführung
- ✅ Lokale Venvs haben Vorrang vor veralteten Systeminstallationen
- ✅ Verhindert Versionskonlikte

---

## 📦 Technische Details

| Komponente | Details |
|-----------|---------|
| **Ansible** | Lokale Venv-Priorisierung |
| **Build** | Docker buildx default builder |
| **Target** | Raspberry Pi 5 (ARM64) |
| **Python** | 3.13 (Host) |

---

## 🚀 Deployment

```bash
# Schnell-Update
./ansible/build_and_deploy.sh --update

# Oder mit Cache-Invalidierung
./ansible/build_and_deploy.sh --update --no-cache
```

---

## 📝 Commits

- `4802642` - fix: Ansible Tool-Lookup priorisiert lokale Venvs über alte Installationen

---

## ⚠️ Bekannte Probleme

Keine neuen bekannten Probleme.

---

## 📚 Dokumentation

Siehe `docs/` für Konfiguration und Troubleshooting.
