from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    devices = coordinator.data or []
    entities = []
    for dev in devices:
        device_id = dev.get("id") or dev.get("device_id") or dev.get("uuid")
        name = dev.get("name", "Heater Meter")
        entities.append(HeaterMeterSensor(coordinator, device_id, name))

    async_add_entities(entities)


class HeaterMeterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id: str, name: str):
        super().__init__(coordinator)
        self._device_id = str(device_id)
        self._attr_name = f"{name}"
        self._unique_id = f"heater_meter_{self._device_id}_latest"

    @property
    def state(self) -> Any:
        # coordinator data is list of devices; find this device
        devices = self.coordinator.data or []
        for dev in devices:
            dev_id = dev.get("id") or dev.get("device_id") or dev.get("uuid")
            if str(dev_id) == self._device_id:
                # assume device has `latest` or `latest_reading` field or compute from readings
                if "latest" in dev:
                    return dev["latest"]
                if "latest_reading" in dev:
                    return dev["latest_reading"].get("value")
                # fallback to last in readings list
                readings = dev.get("readings") or []
                if readings:
                    try:
                        return readings[-1].get("value")
                    except Exception:
                        return None
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._attr_name,
            "manufacturer": "Heater Meter Logger",
        }

    @property
    def extra_state_attributes(self):
        # expose device metadata and last timestamp
        devices = self.coordinator.data or []
        for dev in devices:
            dev_id = dev.get("id") or dev.get("device_id") or dev.get("uuid")
            if str(dev_id) == self._device_id:
                attrs = {
                    "area": dev.get("area"),
                    "device_id": self._device_id,
                }
                lr = dev.get("latest_reading") or dev.get("latest")
                if isinstance(lr, dict):
                    attrs.update({"last_value": lr.get("value"), "last_timestamp": lr.get("timestamp")})
                # include full readings list reference count
                readings = dev.get("readings") or []
                attrs["readings_count"] = len(readings)
                return attrs
        return {}
