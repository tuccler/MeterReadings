import logging
from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Always operate in local-only mode. Devices and readings are stored in the integration config entry.
    """
    devices = entry.data.get("devices", [])

    async def async_update_data():
        # Return current devices from the config entry data.
        return entry.data.get("devices", [])

    coordinator = DataUpdateCoordinator(hass, _LOGGER, name=DOMAIN, update_method=async_update_data)
    # seed initial data
    coordinator.async_set_updated_data(devices)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # register services that operate on local storage
    async def async_service_add_device(call):
        data = call.data
        name = data.get("name")
        area = data.get("area")
        # create a new local device object and persist it to the entry
        import uuid

        created_at = datetime.now(timezone.utc).isoformat()
        device_id = f"local-{uuid.uuid4().hex[:8]}"
        device = {
            "id": device_id,
            "name": name,
            "area": area,
            "created_at": created_at,
            "latest_reading": {"value": 0.0, "timestamp": created_at},
            "readings": [
                {"id": f"r-{uuid.uuid4().hex[:8]}", "value": 0.0, "timestamp": created_at, "created_at": created_at}
            ],
        }
        # update the entry data (use hass.config_entries.async_update_entry)
        updated = dict(entry.data)
        updated_devices = list(updated.get("devices", []))
        updated_devices.append(device)
        updated["devices"] = updated_devices
        hass.config_entries.async_update_entry(entry, data=updated)

        # refresh in-memory coordinator data
        coordinator.async_set_updated_data(updated_devices)

    async def async_service_add_reading(call):
        data = call.data
        device_id = data.get("device_id")
        value = data.get("value")
        timestamp = data.get("timestamp")
        import uuid

        ts = timestamp
        if ts is None:
            ts = datetime.now(timezone.utc).isoformat()

        # update entry data
        updated = dict(entry.data)
        updated_devices = list(updated.get("devices", []))
        for d in updated_devices:
            if d.get("id") == device_id:
                reading = {"id": f"r-{uuid.uuid4().hex[:8]}", "value": float(value), "timestamp": ts, "created_at": ts}
                d.setdefault("readings", []).append(reading)
                d["latest_reading"] = {"value": float(value), "timestamp": ts}
                break
        updated["devices"] = updated_devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(updated_devices)

    async def async_service_delete_reading(call):
        data = call.data
        device_id = data.get("device_id")
        reading_id = data.get("reading_id")

        if not device_id or not reading_id:
            _LOGGER.warning("delete_reading called without device_id or reading_id")
            return

        updated = dict(entry.data)
        updated_devices = list(updated.get("devices", []))
        for d in updated_devices:
            if d.get("id") == device_id:
                readings = d.get("readings", [])
                # filter out matching reading id
                new_readings = [r for r in readings if str(r.get("id")) != str(reading_id)]
                d["readings"] = new_readings
                # update latest_reading to last reading if exists, else zero
                if new_readings:
                    last = sorted(new_readings, key=lambda x: x.get("timestamp"))[-1]
                    d["latest_reading"] = {"value": last.get("value"), "timestamp": last.get("timestamp")}
                else:
                    ts = datetime.now(timezone.utc).isoformat()
                    d["latest_reading"] = {"value": 0.0, "timestamp": ts}
                break
        updated["devices"] = updated_devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(updated_devices)

    async def async_service_delete_device(call):
        data = call.data
        device_id = data.get("device_id")
        if not device_id:
            _LOGGER.warning("delete_device called without device_id")
            return

        updated = dict(entry.data)
        updated_devices = [d for d in updated.get("devices", []) if d.get("id") != device_id]
        updated["devices"] = updated_devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(updated_devices)

    hass.services.async_register(DOMAIN, "add_device", async_service_add_device)
    hass.services.async_register(DOMAIN, "add_reading", async_service_add_reading)
    hass.services.async_register(DOMAIN, "delete_reading", async_service_delete_reading)
    hass.services.async_register(DOMAIN, "delete_device", async_service_delete_device)

    async def async_service_export_data(call):
        """Export devices and readings to a JSON file in the Home Assistant config directory or to a provided path."""
        path = call.data.get("path")
        conf = hass.config
        import json, time

        data = dict(entry.data)
        payload = {"devices": data.get("devices", [])}
        if not path:
            filename = f"heater_meter_export_{int(time.time())}.json"
            path = conf.path(filename)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            _LOGGER.info("Heater Meter export written to %s", path)
        except Exception as e:
            _LOGGER.error("Failed to write export to %s: %s", path, e)

    async def async_service_import_data(call):
        """Import devices/readings from a JSON payload or file path. Merges into existing devices.
        Service params: 'path' (file path) or 'json' (string with JSON payload)."""
        import json, os

        path = call.data.get("path")
        json_payload = call.data.get("json")
        payload = None
        try:
            if json_payload:
                payload = json.loads(json_payload)
            elif path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            else:
                _LOGGER.error("import_data requires 'json' or existing 'path'")
                return
        except Exception as e:
            _LOGGER.error("Failed to read import payload: %s", e)
            return

        if not isinstance(payload, dict) or "devices" not in payload:
            _LOGGER.error("Import payload must be an object with a 'devices' list")
            return

        updated = dict(entry.data)
        updated_devices = list(updated.get("devices", []))
        # naive merge: append devices that do not have the same id
        existing_ids = {d.get("id") for d in updated_devices}
        for dev in payload.get("devices", []):
            if dev.get("id") in existing_ids:
                _LOGGER.info("Skipping device with existing id %s", dev.get("id"))
                continue
            updated_devices.append(dev)
        updated["devices"] = updated_devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(updated_devices)
        _LOGGER.info("Imported %d devices", len(payload.get("devices", [])))

    async def async_service_populate_device_select(call):
        """Populate an input_select entity with current devices.
        Parameter: 'input_select' (entity_id of the input_select to populate).
        Options are set as: '<name> — <device_id>'"""
        input_select_entity = call.data.get("input_select")
        if not input_select_entity:
            _LOGGER.error("populate_device_select called without 'input_select' parameter")
            return
        devices = coordinator.data or []
        options = [f"{d.get('name')} — {d.get('id')}" for d in devices]
        # call input_select.set_options
        await hass.services.async_call(
            "input_select",
            "set_options",
            {"entity_id": input_select_entity, "options": options},
        )

    hass.services.async_register(DOMAIN, "export_data", async_service_export_data)
    hass.services.async_register(DOMAIN, "import_data", async_service_import_data)
    hass.services.async_register(DOMAIN, "populate_device_select", async_service_populate_device_select)

    # Forward setup to platforms using the Home Assistant entry forwarding API.
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_setup(entry, platform)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, "add_device")
    hass.services.async_remove(DOMAIN, "add_reading")
    hass.services.async_remove(DOMAIN, "delete_reading")
    hass.services.async_remove(DOMAIN, "delete_device")
    hass.services.async_remove(DOMAIN, "export_data")
    hass.services.async_remove(DOMAIN, "import_data")
    hass.services.async_remove(DOMAIN, "populate_device_select")
    hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
