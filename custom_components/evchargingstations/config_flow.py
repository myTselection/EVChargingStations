"""Config flow for integration."""

from __future__ import annotations

from asyncio import CancelledError
from typing import Any


import voluptuous as vol
from aiohttp.client_exceptions import ClientError
from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.helpers.location import find_coordinates
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    selector, SelectSelector, SelectSelectorConfig
)
from .evrecharge import EVApi, LocationEmptyError, LocationValidationError
from .evrecharge.user import LoginFailedError
# from .location import LocationSession
from pywaze.route_calculator import WazeRouteCalculator

from .const import DOMAIN, CONF_ORIGIN, CONF_API_KEY, CONF_PASSWORD, CONF_EMAIL, CONF_SERIAL_NUMBER, CONF_SHELL, CONF_PUBLIC, CONF_SINGLE, UPDATE_INTERVAL, CONF_ONLY_ENECO, CONF_SOURCE, CONF_SOURCE_ENCECO, CONF_SOURCE_SHELL
import logging

_LOGGER = logging.getLogger(__name__)

RECHARGE_SCHEMA = vol.Schema(
    {
        # vol.Required(CONF_SOURCE, default=CONF_SOURCE_ENCECO, description="Source"):
        #     selector({
        #         "select": {
        #             "options": [CONF_SOURCE_ENCECO],
        #             # "options": [CONF_SOURCE_ENCECO, CONF_SOURCE_SHELL],
        #             "mode": "dropdown"
        #         }
        #     }),
        vol.Optional(CONF_PUBLIC): section(
            vol.Schema(
                {
                    vol.Optional(CONF_ORIGIN): str,
                    vol.Optional(CONF_ONLY_ENECO, default=False, description="Only Eneco card supported stations?"): bool
                }
            ),
            {"collapsed": True},
        ),
        vol.Optional(CONF_SINGLE): section(
            vol.Schema(
                {
                    vol.Optional(CONF_SERIAL_NUMBER): str,
                }
            ),
            {"collapsed": True},
        ),
        vol.Optional(CONF_SHELL): section(
            vol.Schema(
                {
                    vol.Optional(CONF_EMAIL): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.EMAIL)
                    ),
                    vol.Optional(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            {"collapsed": True},
        ),
    }
)


class EVRechargeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EV charging stations."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=RECHARGE_SCHEMA)

        try:
            # source = user_input.get(CONF_SOURCE)
            source = CONF_SOURCE_ENCECO
            if user_input.get(CONF_PUBLIC) and user_input[CONF_PUBLIC].get(CONF_ORIGIN):
                origin = user_input[CONF_PUBLIC][CONF_ORIGIN]
                unique_id = origin
                resolved_origin = find_coordinates(self.hass, user_input[CONF_PUBLIC].get(CONF_ORIGIN))
                api = EVApi(websession=async_get_clientsession(self.hass), source=source)
                httpx_client = get_async_client(self.hass)
                # session = LocationSession()
                self.routeCalculatorClient = WazeRouteCalculator(region="EU", client=httpx_client)
                _LOGGER.debug(f"resolved origin: {resolved_origin}, {user_input[CONF_PUBLIC].get(CONF_ORIGIN)}")
                origin_coordinates = await self.routeCalculatorClient._ensure_coords(resolved_origin)
                _LOGGER.debug(f"resolved origin: {resolved_origin}, {user_input[CONF_PUBLIC].get(CONF_ORIGIN)}, origin_coordinates: {origin_coordinates}")
                await api.countChargingStations(origin_coordinates)
            elif user_input.get(CONF_SINGLE) and user_input[CONF_SINGLE].get(CONF_SERIAL_NUMBER):
                unique_id = user_input[CONF_SINGLE][CONF_SERIAL_NUMBER]
                api = EVApi(websession=async_get_clientsession(self.hass), source=source)
                await api.station_by_id(unique_id)
            elif (
                user_input.get(CONF_SHELL)
                and user_input[CONF_SHELL].get(CONF_EMAIL)
                and user_input[CONF_SHELL].get(CONF_PASSWORD)
            ):
                unique_id = user_input[CONF_SHELL][CONF_EMAIL]
                api = EVApi(websession=async_get_clientsession(self.hass), source=source)
                user = await api.get_user(
                    email=unique_id,
                    pwd=user_input[CONF_SHELL][CONF_PASSWORD],
                )
                user_input[CONF_SHELL][CONF_API_KEY] = user.cookies["tnm_api"]
            else:
                errors["base"] = "missing_data"
                return self.async_show_form(
                    step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
                )
        except LoginFailedError:
            errors["base"] = "login_failed"
        except LocationEmptyError:
            errors["base"] = "empty_response"
        except LocationValidationError:
            errors["base"] = "validation"
        except (ClientError, TimeoutError, CancelledError):
            errors["base"] = "cannot_connect"

        if not errors:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(
                title=f"EVCS {unique_id}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=RECHARGE_SCHEMA, errors=errors
        )
