Heater Meter Logger — Release Notes

Minimum Home Assistant: 2024.1.0

Version 0.1.0

- New: Integration operates in local-only mode (no host/port). Devices and readings are managed and persisted in the Integration Config-Entry.
- New: Config Flow now asks for an initial device (name + area) and creates an initial reading with value 0.
- New: Services in the integration:
  - heater_meter_logger.add_device
  - heater_meter_logger.add_reading
  - heater_meter_logger.delete_reading
  - heater_meter_logger.delete_device
  - heater_meter_logger.export_data (exports to HA config folder or provided path)
  - heater_meter_logger.import_data (import from JSON payload or file)
  - heater_meter_logger.populate_device_select (fills an input_select with current devices)
- New: Addon HTTP API endpoints:
  - GET /export -> returns JSON with devices and nested readings
  - POST /import -> accepts JSON payload to create devices + readings in addon DB
- New: Prometheus metrics consolidated and documented (heater_meter_value, heater_meter_last_reading_timestamp_seconds, heater_meter_readings_count)
- New: Grafana example dashboard and provisioning files included under grafana/
- New: Examples for manual UI input and automations under examples/
- New: Import/export helpers so addon and integration can exchange data via JSON

Compatibility notes:
- This release targets Home Assistant 2024.1.0 and newer. Legacy compatibility shims for older Home Assistant versions have been removed.

How to create & push a Git tag (PowerShell example)

# from repo root (PowerShell)
# set user-visible tag
git add -A
git commit -m "Release 0.1.0: local-only integration, export/import & UI examples"

git tag v0.1.0
git push origin main
git push origin v0.1.0

Notes for HACS
- Ensure `custom_components/heater_meter_logger/manifest.json` contains version "0.1.0" (already set)
- Ensure `hacs.json` contains "version": "0.1.0"
- After pushing the tag, HACS will detect the new release.

If you want, use the helper script `git-tag-and-push.ps1` (PowerShell) to run the commit/tag/push sequence automatically:

  .\git-tag-and-push.ps1 -Message "Release 0.1.0" -Branch "main"

(See the script for details and prompts.)
