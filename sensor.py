"""Viessmann VControld sensor device."""
import sys
import time
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
    TIME_HOURS,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from . import (
    DOMAIN as VC_DOMAIN,
    VC_API,
    VC_NAME
)

_LOGGER = logging.getLogger(__name__)

CONF_GETTER = "getter"
SENSOR_OUTSIDE_TEMPERATURE = "outside_temperature"
SENSOR_SUPPLY_TEMPERATURE = "supply_temperature"
SENSOR_ECS_TEMPERATURE = "ecs_temperature"
SENSOR_BURNER_HOURS = "burner_hours"
SENSOR_BURNER_STARTS = "burner_starts"

SENSOR_TYPES = {
    SENSOR_OUTSIDE_TEMPERATURE: {
        CONF_NAME: "Outside Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat("getTempA"),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_SUPPLY_TEMPERATURE: {
        CONF_NAME: "Water Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat("getTempWWist"),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_ECS_TEMPERATURE: {
        CONF_NAME: "Ecs Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat("getTempStp2"),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_BURNER_STARTS: {
        CONF_NAME: "Burner Starts",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: int(api.readfloat("getBrennerStarts")),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_BURNER_HOURS: {
        CONF_NAME: "Burner Hours",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: int(api.readfloat("getBrennerStunden1")),
        CONF_DEVICE_CLASS: None,
    },
}

def setup_platform(hass, config, add_entities, discovery_info=None):
  """Setup sensors"""
  if discovery_info is None:
    return
  
  _LOGGER.info("Setup VC sensor platform")

  entities = []
  vc_api = hass.data[VC_DOMAIN][VC_API]

  for sensor_type in SENSOR_TYPES:
    entities.append(VCSensor(hass.data[VC_DOMAIN][VC_NAME],vc_api,sensor_type))

  add_entities(entities, True)


class VCSensor(Entity):
  """Implementation of the Vcontrold sensor."""

  def __init__(self, name, api, sensor_type):
    """Initialize the sensor."""
    self._sensor = SENSOR_TYPES[sensor_type]
    self._name = f"{name} {self._sensor[CONF_NAME]}"
    self._api = api
    self._sensor_type = sensor_type
    self._state = None

  @property
  def available(self):
      """Return True if entity is available."""
      return self._state is not None

  @property
  def unique_id(self):
      """Return a unique ID."""
      return f"{self._api.read('getInventory')}-{self._sensor_type}"

  @property
  def name(self):
      """Return the name of the sensor."""
      return self._name

  @property
  def icon(self):
      """Icon to use in the frontend, if any."""
      return self._sensor[CONF_ICON]

  @property
  def state(self):
      """Return the state of the sensor."""
      return self._state

  @property
  def unit_of_measurement(self):
      """Return the unit of measurement."""
      return self._sensor[CONF_UNIT_OF_MEASUREMENT]

  @property
  def device_class(self):
      """Return the class of this device, from component DEVICE_CLASSES."""
      return self._sensor[CONF_DEVICE_CLASS]

  def update(self):
      """Update state of sensor."""
      try:
        self._state = self._sensor[CONF_GETTER](self._api)
      except ConnectionError:
          _LOGGER.error("Unable to retrieve sensor data")
      except ValueError:
          _LOGGER.error("Unable to decode sensor data")
