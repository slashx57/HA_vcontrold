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
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL
)
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]

DOMAIN = "vcontrold"
VC_API = "api"
VC_NAME = "name"
VC_HEATING_TYPE = "heating_type"

CONF_HEATING_TYPE = "heating_type"
DEFAULT_HEATING_TYPE = "generic"
DEFAULT_HOST = "127.0.0.1"
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
                vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
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

VC_GET_INVENTORYID = "getInventory"

class Device:
    """This class connects to VControld"""

    def __init__(self, host, port):
      """Init function"""
      self.mutex = Lock()
      self._host = host
      self._port = port
      self._inventory = None
      self.tn = None
      self._prompt = "vctrld>"

    def connect(self):
        global tn
        retry=3
        while retry!=0:
            try:
               _LOGGER.info("Connecting to " + self._host + ":" + str(self._port))
               self.tn = telnetlib.Telnet(self._host, self._port)
               _LOGGER.info("Connected")
               self.tn.read_until(self._prompt.encode(), 1)
               return
            except:
               #print("Connection ERROR " , sys.exc_info()[0])
               _LOGGER.warn("Failed to connect to port "+str(self._port) + " %s" , sys.exc_info()[1])
               time.sleep(1)
               retry-=1
        if retry==0:
            _LOGGER.warn("Failed to connect to port "+str(self._port))
            tn.close()
            raise ConnectionError

    def read(self, key):
      with self.mutex:
        #_LOGGER.info("Read [" + key + "]")
        retry = 3
        value = ""
        while retry!=0:
          if self.tn is None:
            self.connect()
          if self.tn is None:
            _LOGGER.warn("Failed to reconnect during read, cancel")
            return ""
          try:
            ru = self.tn.read_until(self._prompt.encode(), 1)
            if ru == "":
              self.tn.write(b"\r\n")
              ru = self.tn.read_until(self._prompt.encode(), 1)

            #_LOGGER.debug("Read1 ["+ru.decode()+"]")
            self.tn.write(key.encode() + b"\r\n")
            value=self.tn.read_until(self._prompt.encode(), 1).decode().strip("\n"+self._prompt)
            #_LOGGER.debug("Read2 ["+value+"]")
            if value != "":
              break;
          except:
            _LOGGER.warn("Failed to read, retry")
          retry-=1
        if retry==0:
          _LOGGER.warn("Failed to read "+key+", cancel")
          self.tn.close()
          self.tn = None
          return ""
        if value.startswith("ERR"):
            self.tn.write(bytes('close', 'ascii') + b"\r\n")
            self.tn = None
            return ""
        value = value.strip("\n"+self._prompt)
        _LOGGER.debug("Read ["+key + "] value=[" + value + "]")
        return value

    def readint(self, key):
      value = self.read(key)
      val = int(value.split(' ', 1)[0])
      _LOGGER.debug(" int val="+str(val))
      return val

    def readfloat(self, key):
      value = self.read(key)
      val = round(float(value.split(' ', 1)[0]), 2)
      _LOGGER.debug(" float val="+str(val))
      return val

    def write(self, key, val):
      with self.mutex:
        #_LOGGER.debug("Write " + key +" "+ val)
        retry = 3
        value=""
        while retry!=0:
          if self.tn is None:
            self.connect()
          if self.tn is None:
            _LOGGER.warn("Failed to reconnect during write, cancel")
            return 
          #try:
          msg = key+" "+val + "\r\n"
          _LOGGER.debug("Write : "+msg)
          self.tn.write(msg.encode())
          response = self.tn.read_until(self._prompt.encode(), 1).decode()
          #_LOGGER.debug("Read1 ["+ru.decode()+"]")
          #response = self.read(key)
          _LOGGER.debug("Response : ["+response+"]")
          if response.startswith('OK'):
            _LOGGER.debug("Success")
            return
          #except:
          #  _LOGGER.warn("Failed to write, reconnect")
          #  self.tn.close()
          #  self.tn = None
          _LOGGER.warn("retry")
          retry-=1
        if retry==0:
          _LOGGER.warn("Failed to write, cancel")
          if (self.tn is not None):
            self.tn.close()
            self.tn = None

    @property
    def id(self):
      """Return ID of device."""
      if (self._inventory is None):
        self._inventory = self.read(VC_GET_INVENTORYID).split(' ', 1)[0]
        _LOGGER.debug("Id = " + self._inventory)
      if (self._inventory is None):
        return None
      return self._inventory

def setup(hass, config):
    """Create the VControld component."""
    conf = config[DOMAIN]

    heating_type = conf[CONF_HEATING_TYPE]

    try:
        vc_api = Device(conf[CONF_HOST],conf[CONF_PORT])
    except AttributeError:
        _LOGGER.error(
            "Failed to create API client."
        )
        return False

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][VC_API] = vc_api
    hass.data[DOMAIN][VC_NAME] = conf[CONF_NAME]
    hass.data[DOMAIN][VC_HEATING_TYPE] = heating_type

    for platform in PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN, {}, config)

    return True

def main():
    dev = Device('127.0.0.1',3002)
    dev.read("getTempA")

if __name__ == "__main__":
	main()
