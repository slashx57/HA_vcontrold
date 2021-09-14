
"""Viessmann water_heater device."""
import sys
import logging

from homeassistant.components.water_heater import (
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_OPERATION_MODE,
    WaterHeaterEntity,
)
from homeassistant.const import (
  ATTR_TEMPERATURE, 
  PRECISION_WHOLE, 
  TEMP_CELSIUS,
  STATE_OFF,
  STATE_ON,
)

from . import DOMAIN as VC_DOMAIN, VC_API, VC_HEATING_TYPE, VC_NAME

_LOGGER = logging.getLogger(__name__)

VC_MODE_DHW = "WW"                                        # "Warm-Water"
#VC_MODE_HEATING = "Heating"
VC_MODE_DHWANDHEATING = "H+WW"                            # "Heating and Warm-Water"
#VC_MODE_DHWANDHEATINGCOOLING = "water & Heating/Cooling"
VC_MODE_FORCEDREDUCED = "RED"                             # "Reduced"
VC_MODE_FORCEDNORMAL = "NORM"                             # "Normal"
VC_MODE_OFF = "ABSCHALT"                                  # "Shut down"

VC_GET_CURRENT_TEMP = "getTempWWist"                      # "getWarmwaterTcurrent"
VC_GET_TARGET_TEMP = "getTempWWsoll"                      # "getWarmwaterTtarget"
VC_GET_MODE = "getBetriebArtM1"                           # "getOpModeM1_vito"

VC_SET_MODE = "setBetriebArtM1"                           # "setOpModeA1M1"
VC_SET_TARGET_TEMP = "setTempWWsoll"                      # "setWarmwaterTtarget"

VC_TEMP_WATER_MIN = 10
VC_TEMP_WATER_MAX = 60

#OPERATION_MODE_ON = "on"
#OPERATION_MODE_OFF = "off"

SUPPORT_FLAGS_HEATER = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

#VC_TO_HA_HVAC_DHW = {
#    VC_MODE_WW: OPERATION_MODE_ON,
#    #VC_MODE_DHWANDHEATING: OPERATION_MODE_ON,
#    #VC_MODE_FORCEDREDUCED: OPERATION_MODE_OFF,
#    #VC_MODE_FORCEDNORMAL: OPERATION_MODE_ON,
#    VC_MODE_OFF: OPERATION_MODE_OFF,
#}

#HA_TO_VC_HVAC_DHW = {
#    OPERATION_MODE_OFF: VC_MODE_OFF,
#    OPERATION_MODE_ON: VC_MODE_WW,
#}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create the VC water_heater devices."""

    if discovery_info is None:
        return

    _LOGGER.info("Setup VC waterheater platform")

    vc_api = hass.data[VC_DOMAIN][VC_API]
    heating_type = hass.data[VC_DOMAIN][VC_HEATING_TYPE]
    add_entities(
        [
            VCWater(
                f"{hass.data[VC_DOMAIN][VC_NAME]} Water Heater",
                vc_api,
                heating_type,
            )
        ]
    )


class VCWater(WaterHeaterEntity):
    """Representation of the domestic hot water device."""

    def __init__(self, name, api, heating_type):
        """Initialize the DHW water_heater device."""
        self._name = name
        self._state = None
        self._api = api
        self._attributes = {}
        self._target_temperature = None
        self._current_temperature = None
        self._current_mode = None
        self._heating_type = heating_type

    def update(self):
        """Let HA know there has been an update from the API."""
        try:
              self._current_temperature = (
                  self._api.readfloat(VC_GET_CURRENT_TEMP)
              )

              self._target_temperature = (
                  self._api.readfloat(VC_GET_TARGET_TEMP)
              )

              if VC_MODE_DHW in self._api.read(VC_GET_MODE):
                self._current_mode = STATE_ON
              else:
                self._current_mode = STATE_OFF

        except ConnectionError:
            _LOGGER.error("Unable to retrieve data from VControld")
        except ValueError:
            _LOGGER.error("Unable to decode data from VControld")

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS_HEATER

    @property
    def name(self):
        """Return the name of the water_heater device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temp = int(kwargs.get(ATTR_TEMPERATURE))
        if temp is not None:
            self._api.write(VC_SET_TARGET_TEMP, str(temp))
            _LOGGER.debug("Setting target temp to %i", temp)
            self._target_temperature = float(temp)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return VC_TEMP_WATER_MIN

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return VC_TEMP_WATER_MAX

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_mode

    def set_operation_mode(self, op_mode):
        act_mode = self._api.read(VC_GET_MODE)
        vc_mode = None
        if (op_mode == STATE_ON):
          if act_mode != VC_MODE_DHWANDHEATING:
            vc_mode = VC_MODE_DHW;
        else:
          vc_mode = VC_MODE_OFF;
        if vc_mode is None:
          return
        _LOGGER.debug("Setting water mode to %s / %s", op_mode, vc_mode)
        self._api.write(VC_SET_MODE, vc_mode)
        self._current_mode = op_mode

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_ON,STATE_OFF]
