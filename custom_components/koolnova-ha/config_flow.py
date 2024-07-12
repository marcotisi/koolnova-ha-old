import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN

@callback
def configured_instances(hass):
    return set(entry.data["username"] for entry in hass.config_entries.async_entries(DOMAIN))

class KoolnovaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if user_input["username"] in configured_instances(self.hass):
                errors["base"] = "username_exists"
            else:
                return self.async_create_entry(title=user_input["username"], data=user_input)

        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
