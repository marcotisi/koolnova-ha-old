import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

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
            username = user_input["username"]
            password = user_input["password"]
            if username in configured_instances(self.hass):
                errors["base"] = "username_exists"
            else:
                try:
                    await self.hass.async_add_executor_job(self.authenticate, username, password)
                    return self.async_create_entry(title=username, data=user_input)
                except Exception as e:
                    errors["base"] = "auth"

        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    def authenticate(self, username, password):
        import requests
        response = requests.post('https://api.koolnova.com/auth/v2/login/', json={
            'username': username,
            'password': password
        })
        response.raise_for_status()
