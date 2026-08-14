from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = coordinator.data or []

    entities = []
    for dev in devices:
        device_id = dev.get("id")
        device_name = dev.get("name") or f"Heat Allocator {device_id}"
        entities.append(CurrentReadingSensor(coordinator, device_id, device_name))
        entities.append(YearlyTotalSensor(coordinator, device_id, device_name))

    async_add_entities(entities, True)


class BaseAllocatorSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id: str, device_name: str):
        super().__init__(coordinator)
        self._device_id = str(device_id)
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_name,
            "manufacturer": "Heat Cost Allocator",
        }

    def _device(self):
        devices = self.coordinator.data or []
        for device in devices:
            if device.get("id") == self._device_id:
                return device
        return {}

    @property
    def extra_state_attributes(self):
        device = self._device()
        return {
            "area": device.get("area"),
            "last_updated": device.get("last_updated"),
        }


class CurrentReadingSensor(BaseAllocatorSensor):
    _attr_name = "Current Reading"

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_current_reading"

    @property
    def state(self) -> Any:
        return self._device().get("current_reading")


class YearlyTotalSensor(BaseAllocatorSensor):
    _attr_name = "Yearly Total"

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_yearly_total"

    @property
    def state(self) -> Any:
        return self._device().get("yearly_total")
