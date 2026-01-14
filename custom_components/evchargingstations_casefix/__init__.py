"""The shell_recharge integration."""

from __future__ import annotations

import logging

# import evrecharge
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.location import find_coordinates
from .evrecharge import EVApi

from .const import DOMAIN, CONF_ORIGIN, CONF_SINGLE, CONF_PUBLIC, CONF_SHELL, CONF_SERIAL_NUMBER, CONF_EMAIL, CONF_PASSWORD, CONF_API_KEY, CONF_ONLY_ENECO, CONF_MIN_POWER, CONF_AVAILABLE
from .coordinator import (
    EVRechargePublicDataUpdateCoordinator,
    EVRechargeUserDataUpdateCoordinator,
    StationsPublicDataUpdateCoordinator,
    async_find_nearest
)
from pywaze.route_calculator import WazeRouteCalculator
import voluptuous as vol
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    NumberSelector,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

SERVICE_FIND_NEAREST = "find_nearest"
SERVICE_FIND_NEAREST_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ORIGIN): TextSelector(),
        vol.Optional(CONF_ONLY_ENECO, default=False): BooleanSelector(),
        vol.Optional(CONF_MIN_POWER, default=0): NumberSelector(),
        vol.Optional(CONF_AVAILABLE, default=False): BooleanSelector()
    }
)

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

    evapi = EVApi(websession=async_get_clientsession(hass))

    coordinator: EVRechargePublicDataUpdateCoordinator | EVRechargeUserDataUpdateCoordinator | StationsPublicDataUpdateCoordinator
    if entry.data.get(CONF_PUBLIC) and entry.data[CONF_PUBLIC].get(CONF_ORIGIN):
        httpx_client = get_async_client(hass)
        routeCalculatorClient = WazeRouteCalculator(region="EU", client=httpx_client)
        coordinator = StationsPublicDataUpdateCoordinator(
            hass, evapi, entry, routeCalculatorClient
        )
    elif entry.data.get(CONF_SINGLE) and entry.data[CONF_SINGLE].get(CONF_SERIAL_NUMBER):
        coordinator = EVRechargePublicDataUpdateCoordinator(
            hass, evapi, entry.data[CONF_SINGLE][CONF_SERIAL_NUMBER]
        )
    else:
        coordinator = EVRechargeUserDataUpdateCoordinator(
            hass,
            await evapi.get_user(
                entry.data[CONF_SHELL][CONF_EMAIL],
                entry.data[CONF_SHELL][CONF_PASSWORD],
                entry.data[CONF_SHELL].get(CONF_API_KEY),
            ),
        )

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


    async def async_find_nearest_service(service: ServiceCall) -> ServiceResponse:
        httpx_client = get_async_client(hass)
        routeCalculatorClient = WazeRouteCalculator(region="EU", client=httpx_client)

        origin = service.data[CONF_ORIGIN]
        only_eneco = service.data[CONF_ONLY_ENECO]
        min_power = service.data[CONF_MIN_POWER]
        available = service.data[CONF_AVAILABLE]



        response = await async_find_nearest(
            hass=hass,
            evapi=evapi,
            origin=origin,
            only_eneco=only_eneco,
            min_power=min_power,
            available=available,
            routeCalculatorClient=routeCalculatorClient
        )
        return {"nearest_station": response}

    hass.services.async_register(
        DOMAIN,
        SERVICE_FIND_NEAREST,
        async_find_nearest_service,
        SERVICE_FIND_NEAREST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    try:
        for platform in PLATFORMS:
            await hass.config_entries.async_forward_entry_unload(entry, platform)
            _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Flag that a reload is in progress
    _LOGGER.info("async_remove_entry " + entry.entry_id)
    hass.data[DOMAIN]["reloading"] = True

    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    hass.data[DOMAIN].pop("reloading", None)

    for entry in hass.config_entries.async_entries(DOMAIN):
        _LOGGER.info("async_unload_entry still set: " + entry.entry_id)
    for entry in hass.data[DOMAIN].keys():
        _LOGGER.info("async_unload_entry still set: " + entry)
    return unload_ok