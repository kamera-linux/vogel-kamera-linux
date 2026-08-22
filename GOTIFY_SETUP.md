# 🚀 Gotify Alert-System Setup

Gotify ist eine **selbst-gehostete, open-source** Alert-Plattform. Keine Abhängigkeit von externen Services, keine Kosten, maximale Sicherheit.

---

## 📋 Komponenten

```
[pi-daemon Container]
    ↓ (HTTP POST)
[Gotify Server] (läuft auf NAS/Pi/192.168.178.36:8080)
    ↓
[Gotify Android/iOS App]
    ↓
🔔 Push-Notification auf dein Handy
```

---

## 🔧 Schritt 1: Gotify Server starten

### Option A: Auf NAS/Server (empfohlen - separate Maschine)

```bash
# Auf NAS/Server (z.B. 192.168.178.36):
docker run -d \
  --name gotify \
  -p 8080:80 \
  -v /opt/gotify/data:/app/data \
  gotify/gotify-server:latest
```

Dann ist Gotify erreichbar unter: **http://192.168.178.36:8080**

### Option B: Auf dem Raspberry Pi (Alternative)

```bash
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had

# Gotify Container starten
docker run -d \
  --name gotify \
  -p 8081:80 \
  -v /home/roimme/gotify/data:/app/data \
  gotify/gotify-server:latest

# Prüfe ob es läuft:
docker logs gotify
```

Dann ist Gotify erreichbar unter: **http://raspberrypi-5-ai-had:8081** oder **http://192.168.178.75:8081**

---

## 🔐 Schritt 2: Gotify Admin-Konto erstellen

1. Öffne Browser: **http://192.168.178.36:8080** (oder deine Adresse)
2. Standard-Credentials:
   - Username: `admin`
   - Password: `admin`
3. **WICHTIG:** Ändere das Passwort sofort!
   - Oben rechts: ⚙️ → "Settings"
   - Gib neues Passwort ein

---

## 📱 Schritt 3: Gotify Mobile App installieren

1. **Android:** Play Store → "Gotify"
2. **iOS:** App Store → "Gotify"
3. App öffnen:
   - **URL:** http://192.168.178.36:8080
   - **Username:** admin
   - **Password:** (dein neues Passwort)
4. ✅ Push-Notifications sollten funktionieren

---

## 🔑 Schritt 4: API-Token generieren

1. Im Gotify-Dashboard: **Apps** (linkes Menü)
2. **CREATE APPLICATION**
   - Name: `pi-daemon`
   - Priority: `10` (höchste)
3. Token wird angezeigt → **KOPIEREN!**
   - Sieht aus wie: `AXxxxxxxxxxxxx`

**Sicher speichern:** `GOTIFY_TOKEN=AXxxxxxxxxxxxx`

---

## 🐳 Schritt 5: In docker-compose.yml konfigurieren

Datei: [ansible/roles/pi-daemon/templates/docker-compose.yml.j2](ansible/roles/pi-daemon/templates/docker-compose.yml.j2)

Füge in `environment:` diese Variablen ein:

```yaml
services:
  pi-daemon:
    environment:
      # ... bestehende Variablen ...
      - GOTIFY_URL=http://192.168.178.36:8080
      - GOTIFY_TOKEN=AXxxxxxxxxxxxx
```

**WICHTIG:** Ersetze:
- `192.168.178.36` mit deiner Gotify-Adresse
- `AXxxxxxxxxxxxx` mit deinem Token (siehe Schritt 4)

---

## 📝 Schritt 6: ansible/.env aktualisieren

Auf deinem Laptop in [ansible/.env](ansible/.env):

```bash
# Gotify Alert-Konfiguration
GOTIFY_URL=http://192.168.178.36:8080
GOTIFY_TOKEN=AXxxxxxxxxxxxx
```

**Oder:** Direkt in docker-compose.yml hardcoden (falls .env nicht genutzt wird)

---

## 🚀 Schritt 7: Deployen

```bash
cd /run/media/imme/ENCRYPTSSD/daten/git/kamera-linux-github/vogel-kamera-linux
cd ansible && bash build_and_deploy.sh --update --no-cache
```

Dies wird:
1. ✅ Neues Image mit Gotify-Integration bauen
2. ✅ Auf Raspi deployen
3. ✅ Container starten

---

## ✅ Schritt 8: Test-Alert senden

```bash
# Auf Raspi:
ssh -i ~/.ssh/id_rsa_ai-had roimme@raspberrypi-5-ai-had

# Im Container testen:
docker exec pi-daemon python3 << 'PYTHON_EOF'
import os
import requests

GOTIFY_URL = os.environ.get('GOTIFY_URL')
GOTIFY_TOKEN = os.environ.get('GOTIFY_TOKEN')

if GOTIFY_URL and GOTIFY_TOKEN:
    url = f'{GOTIFY_URL.rstrip("/")}/message'
    headers = {'Authorization': f'Bearer {GOTIFY_TOKEN}'}
    data = {
        'title': '🧪 pi-daemon Test',
        'message': 'Gotify-Integration funktioniert!',
        'priority': 10
    }
    resp = requests.post(url, json=data, headers=headers, timeout=5)
    print(f'Status: {resp.status_code}')
    if resp.status_code in (200, 201):
        print('✅ Alert erfolgreich gesendet!')
    else:
        print(f'❌ Fehler: {resp.text}')
else:
    print('❌ GOTIFY_URL oder GOTIFY_TOKEN nicht gesetzt')
PYTHON_EOF
```

Du solltest auf deinem Handy eine Benachrichtigung erhalten:
```
🧪 pi-daemon Test
Gotify-Integration funktioniert!
```

---

## 🔄 Wenn Container unhealthy wird

Automatisch wird ein Alert gesendet:

```
🚨 pi-daemon unhealthy
Health-Cache konnte 5x nicht aktualisiert werden: [Fehler]
```

**Alert-Logik:**
- Threshold: 5 aufeinanderfolgende Fehler
- Cooldown: 5 Minuten (verhindert Spam)
- Priority: 10 (höchste Priorität)

---

## 🛠️ Debugging

### Health-Check Logs ansehen:
```bash
docker logs pi-daemon --tail 50 | grep -i gotify
```

### Gotify Server-Logs ansehen:
```bash
# Auf dem Gotify-Server:
docker logs gotify --tail 50
```

### Manuelle Gotify-API Test:
```bash
curl -X POST http://192.168.178.36:8080/message \
  -H "Authorization: Bearer AXxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","message":"Hello from curl","priority":10}'
```

---

## 🔒 Sicherheit

| Aspekt | Status |
|--------|--------|
| **Self-Hosted** | ✅ Keine externen Dependencies |
| **API-Token** | ✅ In Environment (docker inspect sichtbar, aber nur für root) |
| **DSGVO** | ✅ Daten bleiben in deinem Netzwerk |
| **Rate-Limiting** | ✅ 5 Min Cooldown zwischen Alerts |
| **Quellcode** | ✅ Open-Source, audit-bar |

### Hardening (Optional):
Nutze Secret-Files statt Environment-Variablen:
```bash
echo "AXxxxxxxxxxxxx" > /etc/secrets/gotify_token
chmod 400 /etc/secrets/gotify_token

# In docker-compose:
volumes:
  - /etc/secrets/gotify_token:/app/secrets/gotify_token:ro
```

---

## 📊 Weitere Gotify-Features

- **Message History:** Alle Alerts sind im Gotify-Dashboard archiviert
- **Webhook-Support:** Integriere mit IFTTT, Zapier, etc.
- **Custom Priority:** Verschiedene Prioritäten für verschiedene Events
- **Channel Support:** Mehrere Channels wenn du mehrere Services hast

---

## ❓ FAQ

**Q: Gotify-Server antwortet nicht?**
A: Prüfe:
```bash
# Ist Container am Leben?
docker ps | grep gotify

# Logs prüfen:
docker logs gotify

# Netzwerk prüfen:
curl http://192.168.178.36:8080/
```

**Q: Alert wird nicht empfangen?**
A: 
1. Prüfe Token im docker-compose.yml
2. Prüfe GOTIFY_URL (stimmt die IP?)
3. Teste manuell: `curl` Befehl oben
4. Schau in Gotify-Logs

**Q: Mehrere Services monitoren?**
A: Erstelle mehrere Apps in Gotify:
- App 1: `pi-daemon`
- App 2: `mosquitto`
- App 3: `nginx`

Jeder bekommt sein eigenes Token.

---

## 🎯 Next Steps

1. ✅ Gotify Server starten
2. ✅ Admin-Account sichern
3. ✅ Mobile App installieren
4. ✅ API-Token generieren
5. ✅ docker-compose.yml updaten
6. ✅ Deploy: `bash build_and_deploy.sh --update --no-cache`
7. ✅ Test-Alert senden
8. ✅ Container unhealthy machen (optional zum Testen)

Fertig! 🚀
