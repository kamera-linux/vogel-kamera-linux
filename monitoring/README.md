# 📈 Monitoring: Prometheus + Grafana

Verläufe der Vogel-Kamera über Tage und Wochen: Akkustand, Temperaturen, Erkennungen,
freier Speicher. Prometheus fragt den Pi alle 30 Sekunden ab, Grafana zeigt das Dashboard
„Vogel-Kamera".

Es gibt zwei Wege. **Variante A ist der einfache** und braucht keinen zweiten Rechner.

## Variante A: direkt auf dem Pi (empfohlen für den Einstieg)

Prometheus und Grafana laufen als Container neben dem pi-daemon. Zwei Zeilen in `ansible/.env`:

```bash
PI_MONITORING=true
PI_GRAFANA_ADMIN_PASSWORD=MindestensAchtZeichen
```

Danach deployen:

```bash
./ansible/build_and_deploy.sh --update      # oder --install beim ersten Mal
```

Das war alles. Die Ansible-Rolle `monitoring` erledigt den Rest:

- erzeugt das Token für `/metrics` und hinterlegt es bei Daemon und Prometheus
- startet Prometheus und Grafana (`/opt/pi-monitoring` auf dem Pi), öffnet Port 3000
- lädt das Dashboard „Vogel-Kamera" als Startseite

**Öffnen:** Knopf „📈 Monitoring" in der Kopfzeile der Kamera-GUI, oder direkt
`http://<pi>:3000` – Benutzer `admin`, Passwort aus `ansible/.env`.

Gut zu wissen:

- **Internet beim ersten Mal:** Der Pi lädt die beiden Images von Docker Hub (zusammen rund 1 GB).
- **Ressourcen:** etwa 350 MB Arbeitsspeicher und wenige Prozent CPU; die Container haben feste
  Obergrenzen (384 MB und 512 MB), damit sie die Kamera nie verdrängen.
- **Speicher:** Messwerte werden 90 Tage oder bis 1 GB aufbewahrt.
- **Akkubetrieb:** Ist der Pi aus, ist auch das Dashboard nicht erreichbar, und für diese Zeit
  gibt es eine Lücke im Verlauf. Die bis dahin gesammelten Daten bleiben erhalten. Wer das
  vermeiden will, nimmt Variante B.
- **Abschalten:** `PI_MONITORING` entfernen und deployen (Knopf und Endpunkt verschwinden), dann
  auf dem Pi einmalig `cd /opt/pi-monitoring && sudo docker compose down`.

## Variante B: auf einem anderen Rechner im Heimnetz

Sinnvoll, wenn ohnehin ein Server läuft: Die Verläufe bleiben sichtbar, auch wenn der Pi aus ist,
und der Pi wird gar nicht belastet. Dafür ist dieses Verzeichnis gedacht.

**1. Auf dem Pi den Endpunkt einschalten** – in `ansible/.env`, danach deployen:

```bash
echo "PI_METRICS_TOKEN=$(openssl rand -hex 32)" >> ansible/.env
./ansible/build_and_deploy.sh --update
```

**2. Auf dem Server** (in diesem Verzeichnis):

```bash
cp .env.example .env                    # GRAFANA_ADMIN_PASSWORD eintragen
cp prometheus/targets/kamera.yml.example prometheus/targets/kamera.yml
#   → in kamera.yml Hostname oder IP des Pi eintragen (so wie im Zertifikat)

# Token (dasselbe wie PI_METRICS_TOKEN) und Zertifikat des Pi ablegen
printf '%s' '<token>' > prometheus/secrets/metrics.token
curl -k https://<pi>:8443/cert.pem -o prometheus/secrets/kamera.pem
chmod 644 prometheus/secrets/*          # Prometheus läuft im Container als anderer Benutzer

docker compose up -d
```

**3. Öffnen:** `http://<server>:3002` – Benutzer `admin`, Passwort aus `.env`.

**4. Knopf in der Web-GUI der Kamera** (optional) – in `ansible/.env`, danach deployen:

```bash
PI_GRAFANA_URL=http://<server>:3002/d/vogel-kamera
```

## Prüfen (Variante B)

```bash
# Antwortet der Pi?
curl -s --cacert prometheus/secrets/kamera.pem \
     -H "Authorization: Bearer $(cat prometheus/secrets/metrics.token)" https://<pi>:8443/metrics | head

# Sieht Prometheus den Pi? ("health": "up")
curl -s http://127.0.0.1:9091/api/v1/targets | grep -o '"health":"[a-z]*"'
```

| Fehler in Prometheus | Ursache |
|---|---|
| `server returned HTTP status 404` | `PI_METRICS_TOKEN` auf dem Pi nicht gesetzt oder noch nicht deployt |
| `server returned HTTP status 401` | Token in `metrics.token` stimmt nicht (Zeilenumbruch am Ende?) |
| `x509: certificate is valid for …` | Name in `kamera.yml` steht nicht im Zertifikat – Hostname/IP des Pi verwenden |
| `x509: certificate signed by unknown authority` | `kamera.pem` veraltet (Zertifikat erneuert) – neu herunterladen |
| `permission denied` beim Token | `chmod 644 prometheus/secrets/*` |

## Hinweise

- **Ports (Variante B):** Grafana `3002`, Prometheus `9091` (nur lokal). Beides in `.env`
  änderbar – so gewählt, dass es neben dem Monitoring der Modellbahn-Kamera (3001/9090) laufen kann.
- **Aufbewahrung (Variante B):** 180 Tage oder 2 GB, je nachdem was zuerst greift (`.env`).
- **Auf dem Pi prüfen (Variante A):** `sudo docker ps` zeigt `vogelkamera-prometheus` und
  `vogelkamera-grafana`; `curl -s http://127.0.0.1:9090/api/v1/targets | grep -o '"health":"[a-z]*"'`
  muss `up` melden.
- **Dashboard ändern:** Änderungen in Grafana halten bis zum Neustart. Dauerhaft: als JSON
  exportieren und `grafana/dashboards/vogelkamera.json` ersetzen.
- **Sicherheit:** Das Token kann nur Messwerte lesen. Die Dateien in `prometheus/secrets/`,
  `.env` und `targets/kamera.yml` werden nicht eingecheckt.
- **Zähler „Ausgelöste Aufnahmen":** beginnt bei jedem Start des Detection-Modus bei 0. Das
  Dashboard rechnet deshalb mit `increase()`.
