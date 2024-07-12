import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF
)
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE

from . import KoolnovaAPI, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    sensors = api.get_sensors().get('data', [])
    entities = [KoolnovaClimate(api, sensor) for sensor in sensors]
    async_add_entities(entities, True)

class KoolnovaClimate(ClimateEntity):
    def __init__(self, api, sensor):
        self.api = api
        self._sensor = sensor
        self._name = sensor['name']
        self._state = sensor['status']
        self._temperature = sensor['temperature']
        self._target_temperature = sensor['setpoint_temperature']

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        return True

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self._temperature

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def hvac_mode(self):
        return HVAC_MODE_HEAT if self._state == '02' else HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_OFF:
            self.api.set_sensor_value(self._sensor['id'], {"status": "02"})
        else:
            self.api.set_sensor_value(self._sensor['id'], {"status": "03"})

    def set_temperature(self, **kwargs):
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            self.api.set_sensor_value(self._sensor['id'], {"setpoint_temperature": temperature})

    def update(self):
        sensors = self.api.get_sensors().get('data', [])
        for sensor in sensors:
            if sensor['id'] == self._sensor['id']:
                self._sensor = sensor
                self._state = sensor['status']
                self._temperature = sensor['temperature']
                self._target_temperature = sensor['setpoint_temperature']
                break
