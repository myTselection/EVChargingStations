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
)
from .evrecharge import EVApi, LocationEmptyError, LocationValidationError
from .evrecharge.user import LoginFailedError
# from .location import LocationSession
from pywaze.route_calculator import WazeRouteCalculator

from .const import DOMAIN, CONF_ORIGIN, CONF_API_KEY, CONF_PASSWORD, CONF_EMAIL, CONF_SERIAL_NUMBER, CONF_SHELL, CONF_PUBLIC, CONF_SINGLE, UPDATE_INTERVAL
import logging

_LOGGER = logging.getLogger(__name__)

RECHARGE_SCHEMA = vol.Schema(
    {
        vol.Optional("public"): section(
            vol.Schema(
                {
                    vol.Optional("origin"): str,
                }
            ),
            {"collapsed": True},
        ),
        vol.Optional("single"): section(
            vol.Schema(
                {
                    vol.Optional("serial_number"): str,
                }
            ),
            {"collapsed": True},
        ),
        vol.Optional("shell"): section(
            vol.Schema(
                {
                    vol.Optional("email"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.EMAIL)
                    ),
                    vol.Optional("password"): TextSelector(
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
            if user_input.get(CONF_PUBLIC) and user_input[CONF_PUBLIC].get(CONF_ORIGIN):
                origin = user_input[CONF_PUBLIC][CONF_ORIGIN]
                unique_id = origin
                resolved_origin = find_coordinates(self.hass, user_input[CONF_PUBLIC].get(CONF_ORIGIN))
                api = EVApi(websession=async_get_clientsession(self.hass))
                httpx_client = get_async_client(self.hass)
                # session = LocationSession()
                self.routeCalculatorClient = WazeRouteCalculator(region="EU", client=httpx_client)
                _LOGGER.debug(f"resolved origin: {resolved_origin}, {user_input[CONF_PUBLIC].get(CONF_ORIGIN)}")
                origin_coordinates = await self.routeCalculatorClient._ensure_coords(resolved_origin)
                _LOGGER.debug(f"resolved origin: {resolved_origin}, {user_input[CONF_PUBLIC].get(CONF_ORIGIN)}, origin_coordinates: {origin_coordinates}")
                await api.countChargingStations(origin_coordinates)
            elif user_input.get(CONF_SINGLE) and user_input[CONF_SINGLE].get(CONF_SERIAL_NUMBER):
                unique_id = user_input[CONF_SINGLE][CONF_SERIAL_NUMBER]
                api = EVApi(websession=async_get_clientsession(self.hass))
                await api.station_by_id(unique_id)
            elif (
                user_input.get(CONF_SHELL)
                and user_input[CONF_SHELL].get(CONF_EMAIL)
                and user_input[CONF_SHELL].get(CONF_PASSWORD)
            ):
                unique_id = user_input[CONF_SHELL][CONF_EMAIL]
                api = EVApi(websession=async_get_clientsession(self.hass))
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
