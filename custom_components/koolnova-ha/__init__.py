import logging
from datetime import timedelta
import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

DOMAIN = "koolnova"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    coordinator = KoolnovaDataUpdateCoordinator(
        hass,
        username=entry.data["username"],
        password=entry.data["password"]
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
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
        self.refresh_token = None
        self.authenticate()

    def authenticate(self):
        response = self.session.post(f'{self.base_url}/auth/v2/login/', json={
            'username': self.username,
            'password': self.password
        })
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})

    def refresh_auth_token(self):
        response = self.session.post(f'{self.base_url}/auth/v2/refresh/', json={
            'refresh_token': self.refresh_token
        })
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})

    def request_with_refresh(self, method, url, **kwargs):
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as err:
            if err.response.status_code == 401:
                self.refresh_auth_token()
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            else:
                raise

    def get_sensors(self):
        response = self.request_with_refresh('GET', f'{self.base_url}/topics/sensors/')
        return response.json()

    def set_sensor_value(self, sensor_id, value):
        response = self.request_with_refresh('PATCH', f'{self.base_url}/topics/sensors/{sensor_id}/', json=value)
        return response.json()

class KoolnovaDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, username, password):
        self.api = KoolnovaAPI(username, password)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self):
        try:
            return self.api.get_sensors()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
