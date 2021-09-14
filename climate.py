"""Viessmann Vcontrold climate device."""
import sys
import logging

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_COMFORT,
    PRESET_NONE,
    PRESET_ECO,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, TEMP_CELSIUS
from homeassistant.helpers import entity_platform

from . import (
    DOMAIN as VC_DOMAIN,
    VC_API,
    VC_HEATING_TYPE,
    VC_NAME,
    HeatingType,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_VC_MODE = "set_vc_mode"
SERVICE_SET_VC_MODE_ATTR_MODE = "vc_mode"

VC_MODE_DHW = "WW"                                        # "Warm-Water"
#VC_MODE_HEATING = "Heating"
VC_MODE_DHWANDHEATING = "H+WW"                            # "Heating and Warm-Water"
#VC_MODE_DHWANDHEATINGCOOLING = "water & Heating/Cooling"
VC_MODE_FORCEDREDUCED = "RED"                             # "Reduced"
VC_MODE_FORCEDNORMAL = "NORM"                             # "Normal"
VC_MODE_OFF = "ABSCHALT"                                  # "Shut down"

VC_GET_CURRENT_TEMP = "getTempRaumtemperaturA1M1"         # "getTroomA1M1"
VC_GET_TARGET_TEMP = "getTempRaumNorSollM1"               # "getRequestedRoomTnormalA1M1"
VC_GET_MODE = "getBetriebArtM1"                           # "getOpModeM1_vito"
VC_GET_ECO_MODE = "getBetriebSparM1"                      # "getSavingsModeA1M1"
VC_GET_COMFORT_MODE = "getBetriebPartyM1"                 # "getPartyModeA1M1"
VC_GET_CURRENT_ACTION = "getBrennerStatus"                # "getBurnerStatus"

VC_SET_TARGET_TEMP = "setTempRaumNorSollM1"               # "setRequestedRoomTnormalA1M1"
VC_SET_MODE = "setBetriebArtM1"                           # "setOpModeA1M1"
VC_SET_ECO_MODE = "setBetriebSparM1"                      # "setSavingsModeA1M1"
VC_SET_COMFORT_MODE = "setBetriebPartyM1"                 # "setPartyModeA1M1"

#VC_PROGRAM_ACTIVE = "active"
#VC_PROGRAM_COMFORT = "comfort"
#VC_PROGRAM_ECO = "eco"
#VC_PROGRAM_EXTERNAL = "external"
#VC_PROGRAM_HOLIDAY = "holiday"
#VC_PROGRAM_NORMAL = "normal"
#VC_PROGRAM_REDUCED = "reduced"
#VC_PROGRAM_STANDBY = "standby"

#VC_HOLD_MODE_AWAY = "away"
#VC_HOLD_MODE_HOME = "home"
#VC_HOLD_MODE_OFF = "off"

VC_MODE_ON = "1"
VC_MODE_OFF = "0"

VC_TEMP_HEATING_MIN = 3
VC_TEMP_HEATING_MAX = 37

SUPPORT_FLAGS_HEATING = SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE 

#VC_TO_HA_HVAC_HEATING = {
#    VC_MODE_DHW: HVAC_MODE_OFF,
#    VC_MODE_HEATING: HVAC_MODE_HEAT,
#    VC_MODE_DHWANDHEATING: HVAC_MODE_AUTO,
#    VC_MODE_DHWANDHEATINGCOOLING: HVAC_MODE_AUTO,
#    VC_MODE_FORCEDREDUCED: HVAC_MODE_OFF,
#    VC_MODE_FORCEDNORMAL: HVAC_MODE_HEAT,
#    VC_MODE_OFF: HVAC_MODE_OFF,
#}

#HA_TO_VC_HVAC_HEATING = {
#    HVAC_MODE_HEAT: VC_MODE_FORCEDNORMAL,
#    HVAC_MODE_OFF: VC_MODE_FORCEDREDUCED,
#    HVAC_MODE_AUTO: VC_MODE_DHWANDHEATING,
#}

#VC_TO_HA_PRESET_HEATING = {
#    VC_PROGRAM_COMFORT: PRESET_COMFORT,
#    VC_PROGRAM_ECO: PRESET_ECO,
#}

#HA_TO_VC_PRESET_HEATING = {
#    PRESET_COMFORT: VC_PROGRAM_COMFORT,
#    PRESET_ECO: VC_PROGRAM_ECO,
#}


async def async_setup_platform(
    hass, hass_config, async_add_entities, discovery_info=None
):
    """Create the VC climate devices."""
    if discovery_info is None:
        return

    _LOGGER.info("Setup VC climate platform")

    vc_api = hass.data[VC_DOMAIN][VC_API]
    heating_type = hass.data[VC_DOMAIN][VC_HEATING_TYPE]
    async_add_entities(
        [
            VCClimate(
                f"{hass.data[VC_DOMAIN][VC_NAME]} Heating",
                vc_api,
                heating_type,
            )
        ]
    )

    platform = entity_platform.async_get_current_platform()

    #platform.async_register_entity_service(
    #    SERVICE_SET_VC_MODE,
    #    {
    #        vol.Required(SERVICE_SET_VC_MODE_ATTR_MODE): vol.In(
    #            VC_TO_HA_HVAC_HEATING
    #        )
    #    },
    #    "set_vc_mode",
    #)


class VCClimate(ClimateEntity):
    """Representation of the heating climate device."""

    def __init__(self, name, api, heating_type):
        """Initialize the climate device."""
        self._name = name
        self._state = None
        self._api = api
        self._attributes = {}
        self._target_temperature = None
        self._current_mode = None
        self._current_temperature = None
        self._current_program = None
        self._heating_type = heating_type
        self._current_action = None

    def update(self):
        """Get data from VControld."""
        try:

            self._current_temperature = self._api.readfloat(VC_GET_CURRENT_TEMP)

            if self._api.read(VC_GET_ECO_MODE)==VC_MODE_ON:
              self._current_program = PRESET_ECO
            elif self._api.read(VC_GET_COMFORT_MODE)==VC_MODE_ON:
              self._current_program = PRESET_COMFORT
            else:
              self._current_program = PRESET_NONE
            _LOGGER.info("preset=%s",self._current_program)

            self._target_temperature = self._api.readfloat(VC_GET_TARGET_TEMP)

            if VC_MODE_DHWANDHEATING in self._api.read(VC_GET_MODE):
              self._current_mode = HVAC_MODE_HEAT
            else:
              self._current_mode = HVAC_MODE_OFF
            _LOGGER.info("mode=%s",self._current_mode)

            # Update the generic device attributes
            self._attributes = {}

            self._attributes["room_temperature"] = self._current_temperature
            self._attributes["active_vc_program"] = self._current_program
            self._attributes["active_vc_mode"] = self._current_mode

            #self._attributes[
            #    "heating_curve_slope"
            #] = self._api.getHeatingCurveSlope()

            #self._attributes[
            #    "heating_curve_shift"
            #] = self._api.getHeatingCurveShift()

            # Update the specific device attributes
            #if self._heating_type == HeatingType.gas:
            #  self._current_action = self._api.getBurnerActive()
            #elif self._heating_type == HeatingType.heatpump:
            #  self._current_action = self._api.getCompressorActive()

            if int(self._api.readfloat(VC_GET_CURRENT_ACTION))==0:
              self._current_action = 0
            else:
              self._current_action = 1

        except ConnectionError:
            _LOGGER.error("Unable to retrieve data : %s",sys.exc_info()[1])
        except ValueError:
            _LOGGER.error("Unable to decode climate data : %s",sys.exc_info()[1])

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS_HEATING

    @property
    def name(self):
        """Return the name of the climate device."""
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

    @property
    def hvac_mode(self):
        """Return current hvac mode."""
        return self._current_mode

    def set_hvac_mode(self, hvac_mode):
        """Set a new hvac mode on the API."""
        act_mode = self._api.read(VC_GET_MODE)
        vc_mode = None
        if (hvac_mode == HVAC_MODE_HEAT):
          vc_mode = VC_MODE_DHWANDHEATING;
        else:
          if act_mode == VC_MODE_DHWANDHEATING:
            vc_mode = VC_MODE_DHW;
        if vc_mode is None:
          return
        _LOGGER.debug("Setting hvac mode to %s / %s", hvac_mode, vc_mode)
        self._api.write(VC_SET_MODE, vc_mode)
        self._current_mode = hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available hvac modes."""
        return [HVAC_MODE_HEAT,HVAC_MODE_OFF]

    @property
    def hvac_action(self):
        """Return the current hvac action."""
        if self._current_action:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return VC_TEMP_HEATING_MIN

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return VC_TEMP_HEATING_MAX

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temp = int(kwargs.get(ATTR_TEMPERATURE))
        if temp is not None:
            #self._api.setProgramTemperature(self._current_program, temp)
            self._api.write(VC_SET_TARGET_TEMP, str(temp))
            _LOGGER.debug("Setting target temp to %i", temp)
            self._target_temperature = float(temp)

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        return self._current_program

    @property
    def preset_modes(self):
        """Return the available preset mode."""
        return [PRESET_COMFORT,PRESET_NONE,PRESET_ECO]

    def set_preset_mode(self, preset_mode):
        """Set new preset mode and deactivate any existing programs."""
        _LOGGER.debug("Setting preset to %s")
        if (preset_mode == PRESET_COMFORT):
          self._api.write(VC_SET_COMFORT_MODE, VC_MODE_ON)
        elif (preset_mode == PRESET_ECO):
          self._api.write(VC_SET_ECO_MODE, VC_MODE_ON)
        else:
          self._api.write(VC_SET_ECO_MODE, VC_MODE_OFF)
          self._api.write(VC_SET_COMFORT_MODE, VC_MODE_OFF)

    @property
    def extra_state_attributes(self):
        """Show Device Attributes."""
        return self._attributes

    def set_vc_mode(self, vc_mode):
        """Service function to set vc modes directly."""
        self._api.write(VC_SET_MODE, vc_mode)
