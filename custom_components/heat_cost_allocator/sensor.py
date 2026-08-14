from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
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
        name = dev.get("name") or f"Heat Allocator {device_id}"
        entities.append(CurrentReadingSensor(coordinator, device_id, name))
        entities.append(YearlyTotalSensor(coordinator, device_id, name))

    async_add_entities(entities, True)


class BaseAllocatorSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id: str, name: str):
        super().__init__(coordinator)
        self._device_id = str(device_id)
        self._attr_name = name
        self._attr_should_poll = False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._attr_name,
            "manufacturer": "Heat Cost Allocator",
        }


class CurrentReadingSensor(BaseAllocatorSensor):
    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_current_reading"

    @property
    def state(self) -> Any:
        devices = self.coordinator.data or []
        for d in devices:
            if d.get("id") == self._device_id:
                return d.get("current_reading")
        return None


class YearlyTotalSensor(BaseAllocatorSensor):
    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_yearly_total"

    @property
    def state(self) -> Any:
        devices = self.coordinator.data or []
        for d in devices:
            if d.get("id") == self._device_id:
                return d.get("yearly_total")
        return None
