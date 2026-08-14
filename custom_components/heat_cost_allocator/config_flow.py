from __future__ import annotations

from datetime import datetime, timezone
import uuid

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

DEVICE_AREA_OPTIONS = [
    "EG",
    "OG",
    "DG",
    "Living Room",
    "Kitchen",
    "Bedroom",
    "Office",
    "Other",
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("device_name"): str,
        vol.Required("device_area", default="EG"): vol.In(DEVICE_AREA_OPTIONS),
    }
)


class HeatCostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        name = user_input.get("device_name", "").strip()
        area = user_input.get("device_area", "")

        if not name:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": "invalid_device_name"},
            )

        created_at = datetime.now(timezone.utc).isoformat()
        device_id = f"local-{uuid.uuid4().hex[:8]}"
        device = {
            "id": device_id,
            "name": name,
            "area": area,
            "created_at": created_at,
            "current_reading": 0,
            "yearly_total": 0,
        }

        return self.async_create_entry(title="Heat Cost Allocator", data={"devices": [device]})
