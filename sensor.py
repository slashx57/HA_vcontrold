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
SENSOR_BOILER_TARGET = "boiler_target"
SENSOR_BOILER_TEMPERATURE = "boiler_temperature"
SENSOR_BURNER_MODULATION = "burner_modulation"
SENSOR_BURNER_STATUS = "burner_status"
SENSOR_BURNER_STARTS = "burner_starts"
SENSOR_BURNER_HOURS = "burner_hours"
SENSOR_PUMP_STATUS = "pump_status"
SENSOR_HEAT_MODE = "heat_mode"
SENSOR_ROOM_TEMPERATURE = "room_temperature"
SENSOR_ROOM_TARGET = "room_target"
SENSOR_COMFORT_MODE = "party_mode"
SENSOR_COMFORT_TEMP = "party_temp"
SENSOR_ECO_MODE = "eco_mode"
SENSOR_RED_TEMP = "red_target"

VC_GET_OUTSIDE_TEMP = "getTempA"                        # "getToutdoor_vito"
VC_GET_SUPPLY_TEMP= "getTempWWist"                      # "getWarmwaterTcurrent"
VC_GET_BOILER_TARGET = "getTempWWsoll"                  # "getWarmwaterTtarget"
VC_GET_BOILER_TEMP = "getTempStp2"                      # "getWarmwaterTout"
VC_GET_BURNER_MODULATION = "getBrennerStatus"           # "getModulationDegree"
VC_GET_BURNER_STARTS = "getBrennerStarts"               # "getBurnerStarts"
VC_GET_BURNER_HOURS = "getBrennerStunden1"              # "getBurnerHop"
VC_GET_PUMP_STATUS = "getPumpeStatusIntern"             # "getInternalPump"
VC_GET_HEAT_MODE = "getBetriebArtM1"                    # "getOpModeM1_vito"
VC_GET_ROOM_TEMPERATURE = "getTempRaumtemperaturA1M1"   # "getTroomA1M1"
VC_GET_ROOM_TARGET = "getTempRaumNorSollM1"             # "getRequestedRoomTnormalA1M1"
VC_GET_COMFORT_MODE = "getBetriebPartyM1"               # "getPartyModeA1M1"
VC_GET_COMFORT_TEMP = "getTempPartyM1"                  # "getPartyTtargetA1M1"
VC_GET_ECO_MODE = "getBetriebSparM1"                    # "getSavingsModeA1M1"
VC_GET_RED_TEMP = "getTempRaumRedSollM1"

SENSOR_TYPES = {
    SENSOR_OUTSIDE_TEMPERATURE: {
        CONF_NAME: "Outside Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_OUTSIDE_TEMP),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_SUPPLY_TEMPERATURE: {
        CONF_NAME: "Water Temp current",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_SUPPLY_TEMP),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_BOILER_TARGET: {
        CONF_NAME: "Boiler Temp target",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_BOILER_TARGET),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_BOILER_TEMPERATURE: {
        CONF_NAME: "Boiler Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_BOILER_TEMP),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_BURNER_MODULATION: {
        CONF_NAME: "Burner modulation",
        CONF_ICON: "mdi:percent",
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_BURNER_MODULATION),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_BURNER_STARTS: {
        CONF_NAME: "Burner Starts",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: int(api.readfloat(VC_GET_BURNER_STARTS)),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_BURNER_HOURS: {
        CONF_NAME: "Burner Hours",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: int(api.readfloat(VC_GET_BURNER_HOURS)),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_PUMP_STATUS: {
        CONF_NAME: "Pump status",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: api.read(VC_GET_PUMP_STATUS),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_HEAT_MODE: {
        CONF_NAME: "Heat mode",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: api.read(VC_GET_HEAT_MODE),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_ROOM_TEMPERATURE: {
        CONF_NAME: "Room Temp",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_ROOM_TEMPERATURE),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_ROOM_TARGET: {
        CONF_NAME: "Room Temp target",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_ROOM_TARGET),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_COMFORT_MODE: {
        CONF_NAME: "Comfort Mode",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: api.read(VC_GET_COMFORT_MODE),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_COMFORT_TEMP: {
        CONF_NAME: "Comfort Temp target",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_COMFORT_TEMP),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    SENSOR_ECO_MODE: {
        CONF_NAME: "Eco Mode",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: api.read(VC_GET_ECO_MODE),
        CONF_DEVICE_CLASS: None,
    },
    SENSOR_RED_TEMP: {
        CONF_NAME: "Reduced Temp target",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.readfloat(VC_GET_RED_TEMP),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
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
      return f"{self._api.id}-{self._sensor_type}"

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
