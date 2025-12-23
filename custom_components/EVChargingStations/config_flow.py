"""Adds config flow for component."""
import logging
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import selector, SelectSelector, SelectSelectorConfig
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.location import find_coordinates
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME
)

from . import DOMAIN, NAME
from .utils import *

_LOGGER = logging.getLogger(__name__)


def create_schema(entry, option=False):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """

    if option and entry :
        # We use .get here incase some of the texts gets changed.
        default_origin = entry.get("origin","")
        default_filter = entry.get("filter","")
        default_connector_types = entry.get("connector_types",[ConnectorTypes.ELECTRIC_T2.name_lowercase])
        default_friendly_name_template = entry.get("friendly_name_template","")
        default_logo_with_price = entry.get("default_logo_with_price", True)
    else:
        default_filter = ""

    connector_types = [
        ConnectorTypes.ELECTRIC_T1.name_lowercase,
        ConnectorTypes.ELECTRIC_T2.name_lowercase,
        ConnectorTypes.ELECTRIC_DC.name_lowercase
    ]

    data_schema = OrderedDict()
    data_schema[
        vol.Optional("origin", default=default_origin, description="Origin eg: 51.330436, 3.802043 or person.fred")
    ] = str
    data_schema[
        vol.Optional("filter", default=default_filter, description="Supplier brand filter (optional)")
    ] = str
    data_schema[vol.Required("connector_types", default=default_connector_types, description="Connector Type(s)")] = SelectSelector(
                        SelectSelectorConfig(
                            multiple=True,  # Enables multi-select
                            options=[{"value": opt, "label": opt} for opt in connector_types]
                        )
                    )
    return data_schema


class ComponentFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    _init_info = {}
    _carbuLocationInfo = {}
    _towns = []
    _stations = []
    _session = None

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""

        if user_input is not None:
            self._init_info = user_input
            _LOGGER.debug(f"user_input: {user_input}")
            self._session = ComponentSession(user_input.get('GEO_API_KEY'))
            resolved_origin = find_coordinates(self.hass, user_input.get('origin'))
            try:
                await self._session.countChargingStations(resolved_origin)
                custom_title = f"{NAME} {user_input.get('origin')} {" ".join(user_input.get('connector_types'))}"
                return self.async_create_entry(title=custom_title, data=self._init_info)
            except Exception as error:
                _LOGGER.error("Error trying to validate entry: %s", error)
                # If we get here, it's because we couldn't connect
                self._errors["base"] = "cannot_connect"
        return await self._show_config_form(user_input)
        

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        data_schema = create_schema(user_input, True)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )
    