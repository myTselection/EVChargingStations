"""Constants for the shell_recharge integration."""

from datetime import timedelta
from enum import IntFlag

DOMAIN = "evchargingstations"
SerialNumber = str
EvseId = str
UPDATE_INTERVAL = timedelta(minutes=5)


class EVRechargeEntityFeature(IntFlag):
    """Supported features of the Shell Recharge entity."""

    TOGGLE_SESSION = 1
    PAY_FOR_ELECTRICITY = 2
