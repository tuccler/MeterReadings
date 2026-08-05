import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_HOST, CONF_PORT, DEFAULT_PORT, UPDATE_INTERVAL

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
    If host/port provided in entry.data use network coordinator.
    Otherwise use simple in-memory devices stored in the entry data (local-only mode).
    """
    session = async_get_clientsession(hass)

    host = entry.data.get(CONF_HOST)
    if host:
        port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        base_url = f"http://{host}:{port}"

        async def async_update_data():
            try:
                resp = await session.get(f"{base_url}/devices")
                resp.raise_for_status()
                return await resp.json()
            except Exception as err:
                raise UpdateFailed(err)

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=async_update_data,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

        # Fetch initial data
        await coordinator.async_refresh()

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "base_url": base_url,
            "session": session,
        }

        # register services to add device / add reading via the addon API
        async def async_service_add_device(call):
            data = call.data
            name = data.get("name")
            area = data.get("area")
            payload = {"name": name, "area": area}
            await session.post(f"{base_url}/devices", json=payload)
            await coordinator.async_refresh()

        async def async_service_add_reading(call):
            data = call.data
            device_id = data.get("device_id")
            value = data.get("value")
            timestamp = data.get("timestamp")
            payload = {"value": value}
            if timestamp:
                payload["timestamp"] = timestamp
            await session.post(f"{base_url}/devices/{device_id}/readings", json=payload)
            await coordinator.async_refresh()

        hass.services.async_register(DOMAIN, "add_device", async_service_add_device)
        hass.services.async_register(DOMAIN, "add_reading", async_service_add_reading)

    else:
        # local-only mode: use devices saved in the config entry
        devices = entry.data.get("devices", [])
        coordinator = SimpleCoordinator(hass, devices)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "base_url": None, "session": None}

        # register services that operate on local storage
        async def async_service_add_device_local(call):
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

        async def async_service_add_reading_local(call):
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

        hass.services.async_register(DOMAIN, "add_device", async_service_add_device_local)
        hass.services.async_register(DOMAIN, "add_reading", async_service_add_reading_local)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, "add_device")
    hass.services.async_remove(DOMAIN, "add_reading")
    hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
