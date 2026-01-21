"""Constants for the shell_recharge integration."""

from datetime import timedelta
from enum import IntFlag
from enum import Enum

DOMAIN = "evchargingstations"
SerialNumber = str
Origin = str
EvseId = str
UPDATE_INTERVAL = timedelta(minutes=5)
CONF_ORIGIN = "origin"
CONF_ONLY_ENECO = "only_eneco"
CONF_SOURCE = "source"
CONF_SOURCE_ENCECO = "Eneco"
CONF_SOURCE_SHELL = "Shell"
CONF_PUBLIC = "public"
CONF_SINGLE = "single"
CONF_SHELL = "shell"
CONF_SERIAL_NUMBER = "serial_number"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_API_KEY = "api_key"
CONF_MIN_POWER = "min_power"
CONF_AVAILABLE = "available"


class StationSensorType(Enum):
    NEAREST_STATION = 'nearest_station'
    NEAREST_AVAILABLE_STATION = 'nearest_available_station'
    NEAREST_HIGHSPEED_STATION = 'nearest_highspeed_station'
    NEAREST_AVAILABLE_HIGHSPEED_STATION = 'nearest_available_highspeed_station'
    NEAREST_SUPERHIGHSPEED_STATION = 'nearest_superhighspeed_station'
    NEAREST_AVAILABLE_SUPERHIGHSPEED_STATION = 'nearest_available_superhighspeed_station'
    
class EVRechargeEntityFeature(IntFlag):
    """Supported features of the Shell Recharge entity."""

    TOGGLE_SESSION = 1
    PAY_FOR_ELECTRICITY = 2
