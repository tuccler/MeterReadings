import logging
from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


class SimpleCoordinator:
    """Minimal coordinator-like object for local-only mode."""

    def __init__(self, hass, data):
        self.hass = hass
        self.data = data

    async def async_refresh(self):
        # nothing to refresh for local-only stored data
        return True


async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Always operate in local-only mode. Devices and readings are stored in the integration config entry.
    """
    devices = entry.data.get("devices", [])
    coordinator = SimpleCoordinator(hass, devices)
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
        coordinator.data = updated_devices

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
        coordinator.data = updated_devices

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
        coordinator.data = updated_devices

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
        coordinator.data = updated_devices

    hass.services.async_register(DOMAIN, "add_device", async_service_add_device)
    hass.services.async_register(DOMAIN, "add_reading", async_service_add_reading)
    hass.services.async_register(DOMAIN, "delete_reading", async_service_delete_reading)
    hass.services.async_register(DOMAIN, "delete_device", async_service_delete_device)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, "add_device")
    hass.services.async_remove(DOMAIN, "add_reading")
    hass.services.async_remove(DOMAIN, "delete_reading")
    hass.services.async_remove(DOMAIN, "delete_device")
    hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
