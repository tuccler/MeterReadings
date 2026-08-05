# Heizkostenverteiler Dokumentation Addon

Dieses Home Assistant Addon erlaubt die Dokumentation und Verwaltung von Heizkostenverteiler-Ablesewerten.

## Funktionen
- Geräte anlegen mit Namen, Bereich und initialem Stichtagswert 0
- Manuelle Ablesungen für Geräte erfassen
- Historische Werte speichern
- Fehlerhafte Einträge löschen
- Grafana-kompatible Metriken über `/metrics`

## API

### Geräte
- `GET /devices` - Liste aller Geräte
- `POST /devices` - Neues Gerät anlegen
  - Body: `{ "name": "Wohnzimmer", "area": "EG" }`
- `GET /devices/{device_id}` - Gerät anzeigen

### Ablesungen
- `GET /devices/{device_id}/readings` - Historie eines Geräts
- `POST /devices/{device_id}/readings` - Neue Ablesung hinzufügen
  - Body: `{ "value": 123.45, "timestamp": "2026-08-05T12:00:00Z" }`
- `DELETE /devices/{device_id}/readings/{reading_id}` - Ablesung löschen

### Metriken
- `GET /metrics` - Prometheus-kompatibles Endpunkt mit dem aktuellen Wert jedes Geräts

## Grafana-Anbindung

Grafana kann die Daten über einen Prometheus-Scrape-Job auslesen, der auf den Addon-Endpoint `/metrics` zugreift. Alternativ ist die Grafana JSON-Datenquelle einsetzbar.

## Persistenz

Die Daten werden in `/data/meter_readings.db` gespeichert. In Home Assistant Addons wird der Ordner `/data` dauerhaft abgelegt.

## Home Assistant Addon Packaging

1. Lege das Addon-Verzeichnis in `addons/` deines Home Assistant Supervisors ab, z. B. `config/addons/heater-meter-logger`.
2. Kopiere die Dateien `config.json`, `build.json`, `Dockerfile`, `run.py`, `requirements.txt` und optional `README.md` in das Addon-Verzeichnis.
3. Stelle sicher, dass `run.py` ausführbar ist und Python im Container installiert ist.
4. Laden den Home Assistant Supervisor neu oder gehe in die Add-on-Repository-Verwaltung und verwende das lokale Repository.
5. Installiere das Addon in Home Assistant und starte es.

### Konfiguration

- `server_port` kann über die Addon-Optionen gesetzt werden. Der Standardwert ist `8100`.
- Der Web-UI-Link lautet: `http://[HOST]:[PORT:8100]`

### Zugriff

- `GET /devices` - alle Geräte
- `POST /devices` - neues Gerät anlegen
- `GET /devices/{device_id}/readings` - Historie abfragen
- `POST /devices/{device_id}/readings` - neue Ablesung erfassen
- `DELETE /devices/{device_id}/readings/{reading_id}` - Ablesung löschen
- `GET /metrics` - Prometheus/Grafana-Metriken

### Grafana

Erstelle in Grafana eine Prometheus-Datenquelle und verwende den Addon-Endpoint `/metrics` als Ziel. Damit können die aktuellen Werte der Heizkostenverteiler visualisiert werden.
