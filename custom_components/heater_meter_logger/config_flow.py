from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import asyncio

from .const import DOMAIN, CONF_HOST, CONF_PORT, DEFAULT_PORT

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
})


class HeaterMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        errors = {}
        host = user_input.get(CONF_HOST)
        port = user_input.get(CONF_PORT, DEFAULT_PORT)
        session = async_get_clientsession(self.hass)

        try:
            # try contacting the addon endpoint to validate host/port
            url = f"http://{host}:{port}/devices"
            resp = await session.get(url, timeout=10)
            if resp.status != 200:
                errors["base"] = "cannot_connect"
            else:
                # optionally try parsing JSON to ensure endpoint works
                try:
                    await resp.json()
                except Exception:
                    errors["base"] = "invalid_response"
        except asyncio.TimeoutError:
            errors["base"] = "timeout"
        except Exception:
            errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

        return self.async_create_entry(title=f"Heater Meter Logger @ {host}", data=user_input)
