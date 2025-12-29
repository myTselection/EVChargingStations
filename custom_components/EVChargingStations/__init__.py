"""The shell_recharge integration."""

from __future__ import annotations

import logging

# import evrecharge
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.location import find_coordinates
from .evrecharge import EVApi

from .const import DOMAIN, CONF_ORIGIN, CONF_SINGLE, CONF_PUBLIC, CONF_SHELL, CONF_SERIAL_NUMBER, CONF_EMAIL, CONF_PASSWORD, CONF_API_KEY
from .coordinator import (
    EVRechargePublicDataUpdateCoordinator,
    EVRechargeUserDataUpdateCoordinator,
    StationsPublicDataUpdateCoordinator
)
from pywaze.route_calculator import WazeRouteCalculator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from %s", entry.version)

    if entry.version == 2:
        new_data = dict(entry.data)
        new_data["single"] = {"serial_number": new_data.pop("serial_number")}
    else:
        return True

    hass.config_entries.async_update_entry(entry, data=new_data, version=3)

    _LOGGER.debug("Migration to configuration version %s successful", entry.version)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = EVApi(websession=async_get_clientsession(hass))

    coordinator: EVRechargePublicDataUpdateCoordinator | EVRechargeUserDataUpdateCoordinator | StationsPublicDataUpdateCoordinator
    if entry.data.get(CONF_PUBLIC) and entry.data[CONF_PUBLIC].get(CONF_ORIGIN):
        resolved_origin = find_coordinates(hass, entry.data[CONF_PUBLIC].get(CONF_ORIGIN))
        # user_input[PUBLIC][CONF_ORIGIN] = origin_coordinates
        httpx_client = get_async_client(hass)
        routeCalculatorClient = WazeRouteCalculator(region="EU", client=httpx_client)
        coordinator = StationsPublicDataUpdateCoordinator(
            hass, api, entry, routeCalculatorClient
        )
    elif entry.data.get(CONF_SINGLE) and entry.data[CONF_SINGLE].get(CONF_SERIAL_NUMBER):
        coordinator = EVRechargePublicDataUpdateCoordinator(
            hass, api, entry.data[CONF_SINGLE][CONF_SERIAL_NUMBER]
        )
    else:
        coordinator = EVRechargeUserDataUpdateCoordinator(
            hass,
            await api.get_user(
                entry.data[CONF_SHELL][CONF_EMAIL],
                entry.data[CONF_SHELL][CONF_PASSWORD],
                entry.data[CONF_SHELL].get(CONF_API_KEY),
            ),
        )

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
