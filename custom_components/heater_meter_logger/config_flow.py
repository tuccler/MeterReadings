from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from datetime import datetime, timezone
import uuid

from .const import DOMAIN

# New flow: ask for initial device (name + area)
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("device_name"): str,
    vol.Required("device_area"): str,
})


class HeaterMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        """
        Ask the user for an initial device. No host/port required.
        """
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        # create a local device record stored in the config entry
        device_id = f"local-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()
        device = {
            "id": device_id,
            "name": user_input["device_name"],
            "area": user_input["device_area"],
            "created_at": created_at,
            "latest_reading": {"value": 0.0, "timestamp": created_at},
            "readings": [
                {"id": f"r-{uuid.uuid4().hex[:8]}", "value": 0.0, "timestamp": created_at, "created_at": created_at}
            ],
        }

        entry_data = {
            "devices": [device]
        }

        return self.async_create_entry(title=f"Heater Meter Logger (local)", data=entry_data)

    async def async_step_import(self, import_config):
        # support import flow (e.g., from YAML) - fallback to default behavior
        return await self.async_step_user(import_config)
