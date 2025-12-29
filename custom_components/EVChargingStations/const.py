"""Constants for the shell_recharge integration."""

from datetime import timedelta
from enum import IntFlag

DOMAIN = "evchargingstations"
SerialNumber = str
Origin = str
EvseId = str
UPDATE_INTERVAL = timedelta(minutes=5)
CONF_ORIGIN = "origin"
CONF_PUBLIC = "public"
CONF_SINGLE = "single"
CONF_SHELL = "shell"
CONF_SERIAL_NUMBER = "serial_number"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_API_KEY = "api_key"


class EVRechargeEntityFeature(IntFlag):
    """Supported features of the Shell Recharge entity."""

    TOGGLE_SESSION = 1
    PAY_FOR_ELECTRICITY = 2
