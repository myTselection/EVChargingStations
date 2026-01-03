"""Shell Recharge data update coordinators."""

import logging
from asyncio.exceptions import CancelledError

from aiohttp.client_exceptions import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.location import find_coordinates
from .evrecharge import EVApi, ShellChargingStation, LocationEmptyError
from .evrecharge.models import NearestChargingStations, Coords
from .evrecharge.user import AssetsEmptyError, DetailedChargePointEmptyError, User
from .evrecharge.usermodels import DetailedAssets
# from .location import LocationSession
from pywaze.route_calculator import CalcRoutesResponse, WazeRouteCalculator, WRCError


from .const import DOMAIN, UPDATE_INTERVAL, SerialNumber,CONF_ORIGIN, CONF_API_KEY, CONF_PASSWORD, CONF_EMAIL, CONF_SERIAL_NUMBER, CONF_SINGLE, CONF_PUBLIC, CONF_ONLY_ENECO

_LOGGER = logging.getLogger(__name__)
_GEO_API_KEY = ""


class EVRechargeUserDataUpdateCoordinator(DataUpdateCoordinator[DetailedAssets]):
    """Handles data updates for private chargers."""

    def __init__(self, hass: HomeAssistant, api: User) -> None:
        """Initialize coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        self.api = api

    async def _async_update_data(self) -> DetailedAssets:
        """Fetch data from API endpoint.

        Fetches charge point information to cache for entities.
        """
        data = None
        try:
            data = await self.api.get_detailed_assets()
        except AssetsEmptyError as exc:
            _LOGGER.info("User has no charger(s) or card(s)")
            raise UpdateFailed() from exc
        except DetailedChargePointEmptyError as exc:
            _LOGGER.info("User has no charger(s)")
            raise UpdateFailed() from exc
        except CancelledError as exc:
            _LOGGER.error(
                "CancelledError occurred while fetching user's for charger(s)"
            )
            raise UpdateFailed() from exc
        except TimeoutError as exc:
            _LOGGER.error("TimeoutError occurred while fetching user's for charger(s)")
            raise UpdateFailed() from exc
        except ClientError as exc:
            _LOGGER.error("ClientError occurred while fetching user's for charger(s)")
            raise UpdateFailed() from exc
        except Exception as exc:
            _LOGGER.error(
                "Unexpected error occurred while fetching user's for charger(s): %s",
                exc,
                exc_info=True,
            )
            raise UpdateFailed() from exc

        if data is None:
            _LOGGER.error("API returned None data for user's charger(s)")
            raise UpdateFailed("API returned None data")

        return data

    async def toggle_session(
        self, charge_point: str, charge_token: str, toggle: str
    ) -> bool:
        """Toggle a charger session."""
        return bool(
            await self.api.toggle_charger(
                charger_id=charge_point, card_rfid=charge_token, action=toggle
            )
        )


class EVRechargePublicDataUpdateCoordinator(DataUpdateCoordinator[ShellChargingStation]):
    """Handles data updates for public chargers."""

    def __init__(
        self, hass: HomeAssistant, api: EVApi, serial_number: SerialNumber
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.serial_number = serial_number

    async def _async_update_data(self) -> ShellChargingStation:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        data = None
        try:
            data = await self.api.station_by_id(self.serial_number)
        except LocationEmptyError as exc:
            _LOGGER.error(
                "Error occurred while fetching data for charger(s) %s, not found, or serial is invalid",
                self.serial_number,
            )
            raise UpdateFailed() from exc
        except CancelledError as exc:
            _LOGGER.error(
                "CancelledError occurred while fetching data for charger(s) %s",
                self.serial_number,
            )
            raise UpdateFailed() from exc
        except TimeoutError as exc:
            _LOGGER.error(
                "TimeoutError occurred while fetching data for charger(s) %s",
                self.serial_number,
            )
            raise UpdateFailed() from exc
        except ClientError as exc:
            _LOGGER.error(
                "ClientError occurred while fetching data for charger(s) %s",
                self.serial_number,
            )
            raise UpdateFailed() from exc
        except Exception as exc:
            _LOGGER.error(
                "Unexpected error occurred while fetching data for charger(s) %s: %s",
                self.serial_number,
                exc,
                exc_info=True,
            )
            raise UpdateFailed() from exc

        if data is None:
            _LOGGER.error(
                "API returned None data for charger(s) %s",
                self.serial_number,
            )
            raise UpdateFailed("API returned None data")

        return data



class StationsPublicDataUpdateCoordinator(DataUpdateCoordinator):
    """Handles data updates for public chargers."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, api: EVApi, config_entry: ConfigEntry, routeCalculatorClient: WazeRouteCalculator
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self._origin = config_entry.data[CONF_PUBLIC].get(CONF_ORIGIN)
        self._onlyEnecoStations = config_entry.data[CONF_PUBLIC].get(CONF_ONLY_ENECO)
        self._routeCalculatorClient = routeCalculatorClient

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        data: NearestChargingStations = None
        
        resolved_origin = find_coordinates(self.hass, self._origin)
        origin_coordinates = await self._routeCalculatorClient._ensure_coords(resolved_origin)
        _LOGGER.info(f"coordinator origin_coordinates: {origin_coordinates}, resolved_origin: {resolved_origin}, origin: {self._origin}")
        try:
            data = await self.api.nearby_stations(self._origin, origin_coordinates, self._onlyEnecoStations)
            # _LOGGER.debug(f"nearby_stations: {data}")

        except LocationEmptyError as exc:
            _LOGGER.error(
                "Error occurred while fetching data for charger(s) %s, not found, or coordinates are invalid, %s",
                resolved_origin, exc
            )
            raise UpdateFailed() from exc
        except CancelledError as exc:
            _LOGGER.error(
                "CancelledError occurred while fetching data for charger(s) %s, %s",
                resolved_origin, exc
            )
            raise UpdateFailed() from exc
        except TimeoutError as exc:
            _LOGGER.error(
                "TimeoutError occurred while fetching data for charger(s) %s, %s",
                resolved_origin, exc
            )
            raise UpdateFailed() from exc
        except ClientError as exc:
            _LOGGER.error(
                "ClientError occurred while fetching data for charger(s) %s: %s",
                resolved_origin,
                exc,
                exc_info=True,
            )
            raise UpdateFailed() from exc
        except Exception as exc:
            _LOGGER.error(
                "Unexpected error occurred while fetching data for charger(s) %s: %s",
                resolved_origin,
                exc,
                exc_info=True,
            )
            raise UpdateFailed() from exc

        if data is None:
            _LOGGER.error(
                "API returned None data for charger(s) %s",
                resolved_origin,
            )
            raise UpdateFailed("API returned None data")

        return data
