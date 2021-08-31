"""VControld integration"""

import enum
import logging
import telnetlib
import time
import sys
import re

from threading import Lock
from datetime import datetime

import voluptuous as vol

from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL
)
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

#PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]
PLATFORMS = ["climate", "sensor", "water_heater"]

DOMAIN = "vcontrold"
VC_API = "api"
VC_NAME = "name"
VC_HEATING_TYPE = "heating_type"

CONF_HEATING_TYPE = "heating_type"
DEFAULT_HEATING_TYPE = "generic"
DEFAULT_PORT = 3002

class HeatingType(enum.Enum):
    """Possible options for heating type."""

    generic = "generic"
    gas = "gas"
    heatpump = "heatpump"
    fuelcell = "fuelcell"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_NAME, default="Vitodens"): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(
                    cv.time_period, lambda value: value.total_seconds()
                ),
                vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): cv.enum(
                    HeatingType
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

class Device:
    """This class connects to VControld"""

    def __init__(self, port):
      """Init function"""
      self.mutex = Lock()
      self._port = port
      self.tn = None

    def connect(self):
        global tn
        retry=3
        while retry!=0:
            try:
               _LOGGER.info("Connecting to 127.0.0.1:" + str(self._port))
               self.tn = telnetlib.Telnet('127.0.0.1', self._port)
               _LOGGER.info("Connected")
               #self.tn.read_until(b"vctrld>", 5)
               #print("Get prompt")
               return
            except:
               #print("Connection ERROR " , sys.exc_info()[0])
               _LOGGER.warn("Failed to connect to port "+str(self._port) + " %s" , sys.exc_info()[1])
               time.sleep(1)
               retry-=1
        if retry==0:
            _LOGGER.warn("Failed to connect to port "+str(self._port))
            raise ConnectionError

    def read(self, key):
      with self.mutex:
        _LOGGER.info("Read " + key)
        if self.tn is None:
          self.connect()
        if self.tn is None:
          return 0
        value=""
        #print("wait prompt")
        self.tn.read_until(b"vctrld>", 1)
        #print("send command :"+key)
        self.tn.write(bytes(key, 'ascii') + b"\r\n")
        #print("wait return")
        value=self.tn.read_until(b"\n", 1).decode().strip("\n")
        val = value.split(' ', 1)[0]
#        if re.match('(\d+).(\d+)', val) is not None:
#            val = str(round(float(val),1))
        _LOGGER.info(str(datetime.now().time()) + " read:"+key + " val:"+val)
        return val

    def readint(self, key):
      return int(self.read(key))

    def readfloat(self, key):
      return float(self.read(key))

def setup(hass, config):
    """Create the VControld component."""
    conf = config[DOMAIN]

    heating_type = conf[CONF_HEATING_TYPE]

    try:
        #if heating_type == HeatingType.gas:
        #    vicare_api = GazBoiler(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        #elif heating_type == HeatingType.heatpump:
        #    vicare_api = HeatPump(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        #elif heating_type == HeatingType.fuelcell:
        #    vicare_api = FuelCell(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        #else:
            vc_api = Device(conf[CONF_PORT])
    except AttributeError:
        _LOGGER.error(
            "Failed to create API client."
        )
        return False

    vc_api = Device(conf[CONF_PORT])

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][VC_API] = vc_api
    hass.data[DOMAIN][VC_NAME] = conf[CONF_NAME]
    hass.data[DOMAIN][VC_HEATING_TYPE] = heating_type

    for platform in PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN, {}, config)

    return True

def main():
    dev = Device(3002)
    dev.read("getTempA")

if __name__ == "__main__":
	main()
