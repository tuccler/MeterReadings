import logging
from typing import Any
from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    devices = entry.data.get("devices", [])

    async def _update_data():
        return entry.data.get("devices", [])

    coordinator = DataUpdateCoordinator(hass, _LOGGER, name=DOMAIN, update_method=_update_data)
    coordinator.async_set_updated_data(devices)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # services
    async def async_service_add_device(call):
        data = call.data
        name = data.get("name")
        area = data.get("area")
        import uuid

        created_at = datetime.now(timezone.utc).isoformat()
        device_id = f"local-{uuid.uuid4().hex[:8]}"
        dev = {
            "id": device_id,
            "name": name,
            "area": area,
            "created_at": created_at,
            "last_updated": created_at,
            "current_reading": 0,
            "yearly_total": 0,
        }
        updated = dict(entry.data)
        devices = list(updated.get("devices", []))
        devices.append(dev)
        updated["devices"] = devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(devices)

    async def async_service_remove_device(call):
        device_id = call.data.get("device_id")
        if not device_id:
            _LOGGER.warning("remove_device called without device_id")
            return
        updated = dict(entry.data)
        devices = [d for d in updated.get("devices", []) if d.get("id") != device_id]
        updated["devices"] = devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(devices)

    async def async_service_set_current(call):
        device_id = call.data.get("device_id")
        value = call.data.get("value")
        if device_id is None or value is None:
            _LOGGER.warning("set_current_reading requires device_id and value")
            return
        updated = dict(entry.data)
        devices = list(updated.get("devices", []))
        for d in devices:
            if d.get("id") == device_id:
                try:
                    d["current_reading"] = int(value)
                except Exception:
                    d["current_reading"] = value
                d["last_updated"] = datetime.now(timezone.utc).isoformat()
                break
        updated["devices"] = devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(devices)

    async def async_service_set_yearly(call):
        device_id = call.data.get("device_id")
        value = call.data.get("value")
        if device_id is None or value is None:
            _LOGGER.warning("set_yearly_total requires device_id and value")
            return
        updated = dict(entry.data)
        devices = list(updated.get("devices", []))
        for d in devices:
            if d.get("id") == device_id:
                try:
                    d["yearly_total"] = int(value)
                except Exception:
                    d["yearly_total"] = value
                d["last_updated"] = datetime.now(timezone.utc).isoformat()
                break
        updated["devices"] = devices
        hass.config_entries.async_update_entry(entry, data=updated)
        coordinator.async_set_updated_data(devices)

    async def async_service_populate_device_select(call):
        input_select_entity = call.data.get("input_select")
        if not input_select_entity:
            _LOGGER.error("populate_device_select called without 'input_select' parameter")
            return
        devices = coordinator.data or []
        options = [f"{d.get('name')} — {d.get('id')}" for d in devices]
        await hass.services.async_call(
            "input_select",
            "set_options",
            {"entity_id": input_select_entity, "options": options},
        )

    hass.services.async_register(DOMAIN, "add_device", async_service_add_device)
    hass.services.async_register(DOMAIN, "remove_device", async_service_remove_device)
    hass.services.async_register(DOMAIN, "set_current_reading", async_service_set_current)
    hass.services.async_register(DOMAIN, "set_yearly_total", async_service_set_yearly)
    hass.services.async_register(DOMAIN, "populate_device_select", async_service_populate_device_select)

    # forward platforms
    if hasattr(hass.config_entries, "async_forward_entry_setups"):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    elif hasattr(hass.config_entries, "async_forward_entry_setup"):
        for platform in PLATFORMS:
            await hass.config_entries.async_forward_entry_setup(entry, platform)
    else:
        _LOGGER.error("No supported forward API available for platforms")
        return False

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, "add_device")
    hass.services.async_remove(DOMAIN, "remove_device")
    hass.services.async_remove(DOMAIN, "set_current_reading")
    hass.services.async_remove(DOMAIN, "set_yearly_total")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
