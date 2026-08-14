from __future__ import annotations

from datetime import datetime, timezone
import uuid

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import area_registry as ar

from .const import DOMAIN


class HeatCostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def _area_options(self):
        area_registry = ar.async_get(self.hass)
        areas = area_registry.async_list_areas()
        names = sorted({area.name for area in areas if area.name})
        return names

    def _get_schema(self):
        area_options = self._area_options()
        default_area = area_options[0] if area_options else ""

        if area_options:
            area_field = vol.Required("device_area", default=default_area): vol.In(area_options)
        else:
            area_field = vol.Required("device_area"): str

        return vol.Schema(
            {
                vol.Required("device_name"): str,
                area_field,
            }
        )

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self._get_schema())

        name = user_input.get("device_name", "").strip()
        area = user_input.get("device_area", "")

        if not name:
            return self.async_show_form(
                step_id="user",
                data_schema=self._get_schema(),
                errors={"base": "invalid_device_name"},
            )

        created_at = datetime.now(timezone.utc).isoformat()
        device_id = f"local-{uuid.uuid4().hex[:8]}"
        device = {
            "id": device_id,
            "name": name,
            "area": area,
            "created_at": created_at,
            "last_updated": created_at,
            "current_reading": 0,
            "yearly_total": 0,
        }

        return self.async_create_entry(title="Heat Cost Allocator", data={"devices": [device]})
