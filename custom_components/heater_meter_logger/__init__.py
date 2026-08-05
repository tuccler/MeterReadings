import logging

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
        from datetime import datetime, timezone

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
        from datetime import datetime, timezone

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

    hass.services.async_register(DOMAIN, "add_device", async_service_add_device)
    hass.services.async_register(DOMAIN, "add_reading", async_service_add_reading)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, "add_device")
    hass.services.async_remove(DOMAIN, "add_reading")
    hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
