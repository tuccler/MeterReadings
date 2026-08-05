Lovelace Custom Card (button-card) - Beispiel & Anleitung

Ziel
- Eine einfache, kompakte Lovelace-Card, die die manuelle Ablesung komfortabel ermöglicht: Auswahl des Geräts, Eingabe des Werts und ein großer Button zum Abschicken.

Vorbereitungen
1. Installiere die community button-card via HACS (Frontend > + > Suche "button-card") oder verwende eine andere Custom-Card deiner Wahl.
2. Lege die Input-Entities an (siehe examples/input_entities.yaml) und das input_select (examples/input_select.yaml).
3. Importiere die Automation examples/automation_with_select.yaml, die beim Start das input_select befüllt und beim Button-Press die Ablesung sendet.

Beispiel YAML (Lovelace, benötigt button-card)

type: custom:button-card
template: card
entities:
  - entity: input_select.meter_device
    name: Gerät
  - entity: input_number.manual_meter_input
    name: Wert
show_name: true
show_state: false
styles:
  card:
    - padding: 12px
  name:
    - font-weight: bold

cards:
  - type: entities
    title: Heizkostenverteiler - Manuelle Ablesung
    entities:
      - entity: input_select.meter_device
      - entity: input_number.manual_meter_input
  - type: custom:button-card
    name: "Ablesung senden"
    show_state: false
    tap_action:
      action: call-service
      service: heater_meter_logger.add_reading
      service_data:
        device_id: "{{ states('input_select.meter_device').split(' — ')[-1] }}"
        value: "{{ states('input_number.manual_meter_input') | float }}"
        timestamp: "{{ utcnow().isoformat() }}"

Anmerkungen
- `tap_action.service_data` templating in button-card may not evaluate templates directly depending on version; in this case implement a Script in Home Assistant that reads the input_select and input_number and calls heater_meter_logger.add_reading, and then use button-card to call that Script.

Script-Beispiel (in configuration.yaml or via UI Scripts):

send_meter_reading:
  alias: "Send Meter Reading"
  sequence:
    - service: heater_meter_logger.add_reading
      data:
        device_id: "{{ states('input_select.meter_device').split(' — ')[-1] }}"
        value: "{{ states('input_number.manual_meter_input') | float }}"
        timestamp: "{{ utcnow().isoformat() }}"

Verwendung
- Nutzer wählt Gerät, trägt den Messwert ein und drückt den Button. Das Script extrahiert die Device-ID aus dem input_select und ruft den Service auf.

Hinweis: Wenn du Unterstützung beim Erstellen des Scriptes in der UI brauchst, schreibe kurz — ich kann ein UI-Snippet bzw. exportierbares Script-JSON anlegen.
