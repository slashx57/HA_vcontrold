"""Viessmann VControld sensor device."""
import logging

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_POWER,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME

from . import (
    DOMAIN as VC_DOMAIN,
    VC_API,
    VC_NAME
)

_LOGGER = logging.getLogger(__name__)

CONF_GETTER = "getter"

SENSOR_CIRCULATION_PUMP_ACTIVE = "circulationpump_active"
SENSOR_BURNER_ACTIVE = "burner_active"
SENSOR_COMFORT_MODE_ACTIVE = "comfort_active"
SENSOR_ECO_MODE_ACTIVE = "eco_active"

VC_GET_PUMP_STATUS = "getPumpeStatusIntern"             # "getInternalPump"
VC_GET_BURNER_STATUS = "getPumpeStatusZirku"            # "getWarmwaterCirculationPump"
VC_GET_COMFORT_MODE = "getBetriebPartyM1"               # "getPartyModeA1M1"
VC_GET_ECO_MODE = "getBetriebSparM1"                    # "getSavingsModeA1M1"

# heatpump sensors
#SENSOR_COMPRESSOR_ACTIVE = "compressor_active"

VC_STATE_ON = "1"
VC_STATE_OFF = "0"

SENSOR_TYPES = {
    SENSOR_CIRCULATION_PUMP_ACTIVE: {
        CONF_NAME: "Circulation pump active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.read(VC_GET_PUMP_STATUS)!=VC_STATE_OFF,
    },
    SENSOR_BURNER_ACTIVE: {
        CONF_NAME: "Burner active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.read(VC_GET_BURNER_STATUS)!=VC_STATE_OFF,
    },
    SENSOR_COMFORT_MODE_ACTIVE: {
        CONF_NAME: "Comfort mode active",
        CONF_DEVICE_CLASS: None,
        CONF_GETTER: lambda api: api.read(VC_GET_COMFORT_MODE)!=VC_STATE_OFF,
    },
    SENSOR_ECO_MODE_ACTIVE: {
        CONF_NAME: "Eco mode active",
        CONF_DEVICE_CLASS: None,
        CONF_GETTER: lambda api: api.read(VC_GET_ECO_MODE)!=VC_STATE_OFF,
    },
    # heatpump sensors
    #SENSOR_COMPRESSOR_ACTIVE: {
    #    CONF_NAME: "Compressor active",
    #    CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
    #    CONF_GETTER: lambda api: api.getCompressorActive(),
    #},
}

#SENSORS_GENERIC = [SENSOR_CIRCULATION_PUMP_ACTIVE]

#SENSORS_BY_HEATINGTYPE = {
#    HeatingType.gas: [SENSOR_BURNER_ACTIVE],
#    HeatingType.heatpump: [
#        SENSOR_COMPRESSOR_ACTIVE,
#    ],
#    HeatingType.fuelcell: [SENSOR_BURNER_ACTIVE],
#}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create the VC sensor devices."""
    if discovery_info is None:
        return

    _LOGGER.info("Setup VC binary_sensor platform")

    vc_api = hass.data[VC_DOMAIN][VC_API]

    #sensors = SENSORS_GENERIC.copy()

    add_entities(
        [
            VCBinarySensor(
                hass.data[VC_DOMAIN][VC_NAME], vc_api, sensor
            )
            for sensor in SENSOR_TYPES
        ]
    )


class VCBinarySensor(BinarySensorEntity):
    """Representation of a VControld sensor."""

    def __init__(self, name, api, sensor_type):
        """Initialize the sensor."""
        self._sensor = SENSOR_TYPES[sensor_type]
        self._name = f"{name} {self._sensor[CONF_NAME]}"
        self._api = api
        self._sensor_type = sensor_type
        self._state = None
        self._inventory = None

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
    def is_on(self):
        """Return the state of the sensor."""
        return self._state

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

