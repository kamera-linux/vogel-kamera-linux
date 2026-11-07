# 🔒 Release v2.4.1 - Security-Audit

**Release Date:** 7. November 2026  
**Version:** 2.4.1  
**Vorgänger:** [v2.4.0](../v2.4.0/RELEASE_NOTES_v2.4.0.md)

---

## 📋 Übersicht

v2.4.1 behebt alle Funde aus dem [Security-Audit November 2026](../../docs/SECURITY-AUDIT-2026-11.md):
2 hohe, 5 mittlere und 6 niedrige. Keine Lücke war ohne Login ausnutzbar. Neue Funktionen gibt
es nicht. **Update dringend empfohlen.**

---

## 🔒 Wichtigste Fixes

| Schwere | Fix |
|---------|-----|
| 🟠 Hoch | **Sync-Ziele:** Host, Benutzer und Pfad werden geprüft, `--` vor ssh/rsync-Zielen. Vorher konnte jemand mit Login über einen Benutzernamen wie `-oProxyCommand=…` Befehle als root ausführen. |
| 🟠 Hoch | **`/etc/pi-daemon`** war für alle beschreibbar (`0757`) → jetzt `0750` |
| 🟡 Mittel | **Host-Key-Prüfung** bei Video-Übertragung (`accept-new` + `/etc/pi-daemon/known_hosts`) statt keiner Prüfung |
| 🟡 Mittel | **SSH** nur noch mit Schlüssel, kein root-Login (vorher Passwort-Login bei sudo ohne Passwort) |
| 🟡 Mittel | **TLS-Schlüssel** nicht mehr für alle lesbar (`0644` → `0640`) |
| 🟡 Mittel | **Feste Paketversionen** in `requirements_daemon.txt` (Supply-Chain-Schutz) |
| 🟡 Mittel | **SECURITY.md** neu – die alte beschrieb eine längst ersetzte Architektur |
| 🟢 Niedrig | Security-Header (CSP, `X-Frame-Options`, `nosniff`), vollständiges HTML-Escaping in der Web-GUI, SSH-Keys direkt mit `0600`, keine HTTP-500 bei ungültigen Zahlen, Video-Verzeichnis nicht mehr world-writable, veraltete Firewall-Regeln entfernt |

Details zu jedem Fund, zur Nachprüfung und zu bewusst akzeptierten Risiken stehen im
[Audit-Bericht](../../docs/SECURITY-AUDIT-2026-11.md).

### Neue Ansible-Rolle `hardening`

Läuft bei `--install` **und** bei jedem `--update`, damit auch bestehende Installationen
korrigiert werden: Dateirechte, SSH-Härtung, alte Firewall-Regeln.

### Tests

22 neue Sicherheitstests in `tests/test_security.py` (Injection-Versuche, Host-Key-Optionen,
Security-Header, Dateirechte) – insgesamt 59.

---

## ⚠️ Was sich für dich ändert

- **SSH auf den Pi nur noch mit Schlüssel.** Vor dem Update prüfen, dass
  `ssh -i <dein-key> <user>@<pi>` funktioniert. Abschalten:
  `pi_ssh_hardening: false` in `ansible/group_vars/all/vars.yml`.
- **Sync-Ziele:** Beim ersten Transfer nach dem Update wird der Host-Key jedes Ziels gespeichert.
  Wird ein Zielrechner später neu installiert, die passende Zeile in
  `/etc/pi-daemon/known_hosts` löschen.
- **Sync-Ziele mit Leerzeichen oder Sonderzeichen im Pfad** werden abgelehnt bzw. beim Transfer
  übersprungen (siehe Log) – Pfad anpassen.
- **Paket-Updates** kommen nicht mehr automatisch, sondern werden bewusst in
  `requirements_daemon.txt` angehoben.

---

## 🚀 Update

```bash
./ansible/build_and_deploy.sh --update
```

Danach Browser-Tab neu laden – oben neben „Vogel-Kamera“ steht dann **v2.4.1**.

---

## 📝 Commits

- `b3554d9` fix(security): Funde aus dem Security-Audit 2026-11 behoben
- `b8b3534` docs: SECURITY.md neu, Audit-Bericht, Powerbank-Screenshot
