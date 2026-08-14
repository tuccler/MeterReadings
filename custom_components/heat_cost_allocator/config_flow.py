from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from datetime import datetime, timezone
import uuid

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Optional("device_name", default=""): str,
    vol.Optional("device_area", default=""): str,
})


class HeatCostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        devices = []
        name = user_input.get("device_name")
        area = user_input.get("device_area")
        if name:
            created_at = datetime.now(timezone.utc).isoformat()
            device_id = f"local-{uuid.uuid4().hex[:8]}"
            dev = {
                "id": device_id,
                "name": name,
                "area": area,
                "created_at": created_at,
                "current_reading": 0,
                "yearly_total": 0,
            }
            devices.append(dev)

        return self.async_create_entry(title="Heat Cost Allocator", data={"devices": devices})
