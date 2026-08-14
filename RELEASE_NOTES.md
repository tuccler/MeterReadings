Heat Cost Allocator — Release Notes

Minimum Home Assistant: 2024.1.0

Version 0.2.1

- Fix: proper Home Assistant config-flow form using standard selectors for device name and area.
- Fix: no dummy initial device is created without user intent; the integration now creates a proper device form in the standard HA modal UI.
- New: Custom integration `heat_cost_allocator` to manage heat cost allocators and manual readings.
- New: Each device exposes two sensors: current monthly reading and yearly total. Values are whole numbers entered manually.
- New: Config Flow asks for an initial device (name + area) using the standard Home Assistant selector modal and creates an initial reading with value 0.
- New: Services in the integration:
  - heat_cost_allocator.add_device
  - heat_cost_allocator.set_current_reading
  - heat_cost_allocator.set_yearly_total
  - heat_cost_allocator.remove_device
- New: Addon HTTP API endpoints:
  - GET /export -> returns JSON with devices and nested readings
  - POST /import -> accepts JSON payload to create devices + readings in addon DB
- New: Prometheus metrics consolidated and documented (heater_meter_value, heater_meter_last_reading_timestamp_seconds, heater_meter_readings_count)
- New: Grafana example dashboard and provisioning files included under grafana/
- New: Examples for manual UI input and automations under examples/
- New: Import/export helpers so addon and integration can exchange data via JSON

Compatibility notes:
- This release targets Home Assistant 2024.1.0 and newer. Legacy compatibility shims for older Home Assistant versions have been removed.

How to create & push a Git tag and release for HACS (PowerShell example)

# from repo root (PowerShell)
git add -A
git commit -m "Release 0.2.0: heat_cost_allocator integration"

git tag 0.2.0
git push origin main
git push origin 0.2.0

# In GitHub: create a release from tag 0.2.0 (or v0.2.0 if you prefer that naming)
# and ensure the release body matches the version you want HACS to see.

Notes for HACS
- Ensure `custom_components/heat_cost_allocator/manifest.json` contains version "0.2.1"
- Ensure `hacs.json` contains "version": "0.2.1"
- Do not set `filename` unless you are intentionally distributing a zip asset.
- For source-based installs, HACS downloads the repository archive from the GitHub tag/release.

If you want, use the helper script `git-tag-and-push.ps1` (PowerShell) to run the commit/tag/push sequence automatically:

  .\git-tag-and-push.ps1 -Message "Release 0.1.0" -Branch "main"

(See the script for details and prompts.)
