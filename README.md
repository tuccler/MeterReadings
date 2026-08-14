# Heizkostenverteiler Dokumentation Addon

Dieses Repository enthält ein Home Assistant Addon und eine Custom Integration zur Verwaltung von Heizkostenverteilern.

Minimum Home Assistant: 2024.1.0 — integrations in this repo require HA 2024.1.0 or newer.

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
4. Lade den Home Assistant Supervisor neu oder gehe in die Add-on-Repository-Verwaltung und verwende das lokale Repository.
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

---

## HACS & Custom Integration (Integrationen)

Das Repository enthält zusätzlich eine Home Assistant Custom Integration, die mit HACS installiert werden kann und unter "Einstellungen -> Geräte & Dienste" (Integrationen) erscheint. Die Integration liest die in diesem Addon verwalteten Geräte und legt pro Gerät eine Sensor-Entität für den aktuellen Ablesewert an. Geräte werden im Device Registry angelegt, so dass sie in Home Assistant als Geräte sichtbar sind.

Dateien im Repository:

- `custom_components/heat_cost_allocator/` – die Custom Integration (manifest, __init__, sensor, config_flow, const)
- `hacs.json` – HACS Metadaten für die integration

Installation via HACS (lokales Repo oder GitHub):

1. Wenn das Repo auf GitHub liegt: füge es in HACS (Integrationen -> + -> Suche nach deinem Repo oder "Custom repositories" und Kategorie "Integration").
2. Wenn lokal: kopiere den Ordner `custom_components/heat_cost_allocator` in `config/custom_components/` deines Home Assistant (nur für Tests, für HACS-Installation nutze GitHub).
3. Nach Installation: Neustart von Home Assistant.
4. Integration konfigurieren: Einstellungen -> Geräte & Dienste -> Integration hinzufügen -> "Heater Meter Logger". Im Setup wirst du nach einem initialen Messgerät (Name und Bereich) gefragt; es werden keine Host- oder Port-Angaben benötigt.

Welche Entitäten werden erstellt:

- sensor.<device_name> - aktueller Ablesewert des Geräts (State = numerischer Wert)
- Jedes Gerät wird als Device registriert (Geräteinformationen enthalten area und device_id)
- Sensor-Attribute enthalten: area, device_id, readings_count, last_value, last_timestamp

Services (unter dem Integrations-Domain-Namen verfügbar):

- `heat_cost_allocator.add_device` - Parameter: `name` (string), `area` (string)
- `heat_cost_allocator.set_current_reading` - Parameter: `device_id` (string), `value` (number), `timestamp` (optional ISO8601 string)
- `heat_cost_allocator.set_yearly_total` - Parameter: `device_id` (string), `value` (number)
- `heat_cost_allocator.remove_device` - Parameter: `device_id` (string)

Anmerkungen:

- Alle Geräte und Ablesungen werden lokal in der Integration (Config-Entry) gespeichert. Es gibt keine automatische Kommunikation mit einem externen Addon.
- Historische Werte werden in der Addon-DB (Addon-Mode) oder in der Integration (local-only) gespeichert; die Integration zeigt per Sensor nur den aktuellen Wert an. Grafana/Scraping sollte auf den Addon `/metrics`-Endpoint zugreifen, um Zeitreihen zu sammeln.
- HACS erkennt das Repository als Integration dank `hacs.json` und dem Ordner `custom_components/`.

Beispiele / UI-Automation

- Beispiele zur manuellen Eingabe und Automation befinden sich im Ordner `examples/`:
  - `examples/input_entities.yaml` – Beispiel-Definitionen für `input_number.manual_meter_input` und `input_button.send_manual_reading`.
  - `examples/input_select.yaml` – Beispiel `input_select.meter_device` zur Auswahl eines Geräts. Die Optionen können über den Service `heat_cost_allocator.populate_device_select` befüllt werden.
  - `examples/lovelace_manual_input.yaml` – Lovelace-Card-Beispiel (Entities Card) zur Anzeige und zum Auslösen einer manuellen Ablesung.
  - `examples/automation_add_reading.yaml` – Automation, die beim Drücken des Buttons den Service `heat_cost_allocator.set_current_reading` aufruft. Ersetze in dieser Automation `"<your_device_id>"` durch die tatsächliche `device_id` deines Geräts (z. B. `local-abcdef12`).
  - `examples/automation_with_select.yaml` – Automationen: (1) befüllt `input_select.meter_device` beim HA-Start, (2) sendet beim Button-Drücken die Ablesung für das ausgewählte Gerät.

Anwendungsablauf (kurz):

1. Lege per Integration (Einstellungen → Geräte & Dienste → +) ein initiales Gerät an.
2. Lege die Input-Entities aus `examples/input_entities.yaml` an (oder per UI erzeugen) und das `input_select` aus `examples/input_select.yaml`.
3. Füge die Lovelace-Card aus `examples/lovelace_manual_input.yaml` zu deinem Dashboard hinzu.
4. Importiere die Automation aus `examples/automation_with_select.yaml`.
5. Beim HA-Start wird die `input_select.meter_device` automatisch mit vorhandenen Geräten befüllt.
6. Gib einen Wert in der Eingabe ein und drücke den Button — die Automation schreibt die Ablesung in die Integration für das ausgewählte Gerät.

Hinweis: Die `input_select`-Optionen haben das Format `<name> — <device_id>`. In der Automation wird der Device-ID-Teil automatisch extrahiert.

## Langzeit-Speicherung und Visualisierung (Prometheus / Grafana)

Empfohlene Architektur für langfristige Speicherung und Visualisierung:

1. Addon exposiert Prometheus-kompatible Metriken unter `/metrics`.
2. Richte einen Prometheus-Server ein, der regelmäßig (`scrape_interval`) dein Addon `/metrics` scrapt.
3. Grafana nutzt die Prometheus-Datenquelle, um Dashboards mit Zeitreihen der Ablesewerte zu erstellen.

Prometheus Metriken (konsolidiert)

Das Addon stellt folgende Metriken zur Verfügung (Prometheus Exposition):

- heater_meter_value (gauge)
  - Beschreibung: Aktueller Ablesewert des Heizkostenverteilers.
  - Labels: device_id, name, area
  - Beispiel: heater_meter_value{device_id="1",name="Wohnzimmer",area="EG"} 123.45

- heater_meter_last_reading_timestamp_seconds (gauge)
  - Beschreibung: Unix-Epoch (Seconds) der Zeit der letzten Ablesung.
  - Labels: device_id, name, area
  - Beispiel: heater_meter_last_reading_timestamp_seconds{device_id="1",name="Wohnzimmer",area="EG"} 1690000000

- heater_meter_readings_count (gauge)
  - Beschreibung: Anzahl der gespeicherten Ablesungen für das Gerät.
  - Labels: device_id, name, area
  - Beispiel: heater_meter_readings_count{device_id="1",name="Wohnzimmer",area="EG"} 42

Beispiel Prometheus-Scrape-Konfiguration (`prometheus.yml`):

scrape_configs:
  - job_name: 'heat_cost_allocator'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['homeassistant-host:8100']

Hinweis: Ersetze `homeassistant-host:8100` durch die tatsächlich erreichbare Adresse deines Addons vom Prometheus-Server aus.

### Beispiel Grafana-Abfragen (PromQL)

- Aktueller Wert eines Geräts:
  - heater_meter_value{device_id="<device_id>"}

- Letzte Ablesung als Zeitstempel (Unix):
  - heater_meter_last_reading_timestamp_seconds{device_id="<device_id>"}

- Anzahl gespeicherter Ablesungen:
  - heater_meter_readings_count{device_id="<device_id>"}

- Durchschnittlicher Wert über 30 Tage:
  - avg_over_time(heater_meter_value{device_id="<device_id>"}[30d])

Grafana Dashboard / Provisioning

Im Repo befindet sich ein Beispiel‑Dashboard und Provisioning-Konfiguration unter `grafana/`:

- `grafana/dashboards/heater_meter_dashboard.json` – Beispiel-Dashboard (importierbar oder per Provisioning)
- `grafana/provisioning/datasources/prometheus.yml` – Beispiel Datasource Provisioning (setze die URL zu deinem Prometheus)
- `grafana/provisioning/dashboards/dashboards.yml` – Beispiel Dashboard Provider (passt ggf. den Pfad an)

Provisioning-Quickstart (Grafana Container):

1. Kopiere `grafana/provisioning/datasources/prometheus.yml` nach `/etc/grafana/provisioning/datasources/`.
2. Kopiere `grafana/provisioning/dashboards/dashboards.yml` nach `/etc/grafana/provisioning/dashboards/`.
3. Kopiere `grafana/dashboards/heater_meter_dashboard.json` nach dem in `dashboards.yml` konfigurierten Pfad (z. B. `/var/lib/grafana/dashboards/`).
4. Starte Grafana neu — das Dashboard wird automatisch importiert.

Beispiel-Panel-Query im Dashboard verwendet: `heater_meter_value{device_id=~"$device"}` (Variable `device` bezieht sich auf label_values(heater_meter_value, device_id)).

## InfluxDB-Option (über Home Assistant)

Alternativ kann Home Assistant die Messwerte in eine InfluxDB schreiben (Add-on oder Cloud). Vorgehen:

1. Installiere InfluxDB und richte eine Datenbank/Retention Policy ein.
2. Aktiviere Integration `influxdb` in Home Assistant und konfiguriere die Influx-Instanz.
3. Verwende Home Assistant Automatisierungen oder Recorder/Logger, um die Sensor-Entitäten (`sensor.<device_name>`) in InfluxDB zu schreiben.

Beispiel `configuration.yaml` (InfluxDB v1):

influxdb:
  host: 127.0.0.1
  port: 8086
  database: home_assistant
  max_retries: 3
  default_measurement: state

Konfiguriere in den Influx-Einstellungen, welche Entitäten geschrieben werden sollen (oder nutze `include`/`exclude`).

## Beispiel-Automatisierung: Ablesung per Service anlegen

Wenn ein Gerät per UI/Script neu abgelesen wurde, kann folgende Automation den Wert in das Addon schreiben (nutzt das von der Integration registrierte Service):

alias: "Neue Ablesung an Addon senden"
trigger:
  - platform: state
    entity_id: sensor.manual_meter_input
action:
  - service: heat_cost_allocator.set_current_reading
    data:
      device_id: "<device_id>"
      value: "{{ states('sensor.manual_meter_input') | float }}"
      timestamp: "{{ utcnow().isoformat() }}"
  - service: heat_cost_allocator.set_current_reading
    data:
      device_id: "<device_id>"
      value: "{{ states('sensor.manual_meter_input') | float }}"
      timestamp: "{{ utcnow().isoformat() }}"

Passe `sensor.manual_meter_input` an das UI-Element oder Input-Number an, das du für die Erfassung verwendest.

## HACS Release Checklist & GitHub-Workflow

Für HACS-Distribution (empfohlen: GitHub Public Repository):

1. Stelle sicher, dass `custom_components/heat_cost_allocator/` und `hacs.json` im Root des Repos vorhanden sind.
2. Aktuelle Version: 0.2.0. Die Integration manifestiert die Version in `custom_components/heat_cost_allocator/manifest.json` und `hacs.json`.
3. Erstelle ein Tag im Format `vX.Y.Z` (z. B. `v0.1.0`) und pushe es zu GitHub. HACS nutzt Tags zur Versionierung.
4. Optional: Erstelle ein GitHub-Release (Tags lösen den Release-Workflow aus). Das mitgelieferte GitHub Action Workflow `.github/workflows/release.yml` erstellt bei Tag-Push ein Release und lädt ein ZIP-Archiv hoch.
5. HACS wird das Repo scannen und die neue Version als Release/Update erkennen.

Hinweis: Das Commit-Tag `v0.2.0` signalisiert HACS, dass ein neues Release verfügbar ist. Stelle sicher, dass das Manifest in `custom_components/heat_cost_allocator/manifest.json` die korrekte Version (`0.2.0`) enthält.

## Addon HTTP Export/Import Endpoints

Das Addon bietet jetzt zwei HTTP-Endpunkte zum Datenaustausch:

- GET /export — liefert alle Geräte mit eingebetteten Ablesungen im JSON-Format:
  {
    "devices": [ { "id": 1, "name": "Wohnzimmer", "area": "EG", "created_at": "...", "readings": [ {...}, ... ] }, ... ]
  }

- POST /import — erwartet ein JSON-Payload im gleichen Format (key: devices). Für jedes Gerät im Payload wird ein neues Gerät in der Addon-DB angelegt und die enthaltenen Ablesungen werden eingefügt. Rückgabe: { "created_device_ids": [ ... ] }

Hinweis: Importiert werden jeweils neue Geräte (mit neuen numerischen IDs); es erfolgt keine automatische Duplikatserkennung außer der Pflichtfelder `name` und `area`.

Diese Endpunkte erleichtern die Synchronisation zwischen dem Addon und anderen Systemen (z. B. Backup/Restore oder Bulk-Import über JSON). Die Integration bietet ebenfalls `export_data`/`import_data` Services von der HA-Seite aus — nutze entweder die Addon-API oder die Integration-Services je nach Workflow.

## Weiteres / ToDos

- Optional: Endpoint-Authentifizierung (API-Key) hinzufügen, falls dein Addon nicht lokal frei zugänglich sein soll.
- Optional: Separate Entities für historische Werte oder Differenzen, falls du sie in Home Assistant direkt analysieren möchtest.

