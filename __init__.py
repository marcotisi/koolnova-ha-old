import asyncio
import logging

import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "koolnova"

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Koolnova component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Koolnova from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = KoolnovaAPI(entry.data["username"], entry.data["password"])
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "climate")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

class KoolnovaAPI:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://api.koolnova.com'
        self.session = requests.Session()
        self.token = None
        self.authenticate()

    def authenticate(self):
        response = self.session.post(f'{self.base_url}/auth/v2/login/', json={
            'username': self.username,
            'password': self.password
        })
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})

    def get_sensors(self):
        response = self.session.get(f'{self.base_url}/topics/sensors/')
        response.raise_for_status()
        return response.json()

    def set_sensor_value(self, sensor_id, value):
        response = self.session.patch(f'{self.base_url}/topics/sensors/{sensor_id}/', json=value)
        response.raise_for_status()
        return response.json()
