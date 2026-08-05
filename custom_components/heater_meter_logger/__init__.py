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


async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    base_url = f"http://{host}:{port}"

    session = async_get_clientsession(hass)

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

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

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

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, "add_device")
    hass.services.async_remove(DOMAIN, "add_reading")
    hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
