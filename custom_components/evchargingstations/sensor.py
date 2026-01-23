"""Sensors for the shell_recharge integration."""

from __future__ import annotations

import logging
import typing
from typing import Any

# import evrecharge
import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .evrecharge.models import ShellChargingStation, ShellStatus, ShellConnector, NearestChargingStations, EnecoStatus, EnecoConnector, EnecoChargingStation, EnecoEvse
from .evrecharge.usermodels import ChargePointDetailedStatus, ChargeToken, DetailedAssets, DetailedChargePoint, DetailedEvse

from . import (
    EVRechargePublicDataUpdateCoordinator,
    EVRechargeUserDataUpdateCoordinator,
    StationsPublicDataUpdateCoordinator
)
from .const import DOMAIN, EvseId, EVRechargeEntityFeature, StationSensorType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a sensor entry."""

    if not hass.data[DOMAIN].get("_service_registered"):
        platform = entity_platform.async_get_current_platform()
        platform.async_register_entity_service(
            name="toggle_session",
            schema={
                vol.Required("card"): str,
                vol.Required("toggle"): str,
            },
            func="toggle_session",
        )
        hass.data[DOMAIN]["_service_registered"] = True

    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[Entity] = []
    evse_id = ""

    if coordinator.data:
        if isinstance(coordinator, StationsPublicDataUpdateCoordinator):
            for nearestStationType in StationSensorType:
                sensor: SensorEntity = NearestSensor(coordinator=coordinator, type=nearestStationType)
                entities.append(sensor)

        elif isinstance(coordinator, EVRechargePublicDataUpdateCoordinator):
            for evse in coordinator.data.evses:
                evse_id = evse.uid
                sensor: SensorEntity = EVShellRechargeSensor(
                    evse_id=evse_id, coordinator=coordinator
                )
                entities.append(sensor)
        else:
            for charger in coordinator.data.chargePoints:
                for evse in charger._embedded.evses:  # pylint: disable=protected-access
                    evse_id = evse.evseId
                    sensor = EVRechargePrivateSensor(
                        evse_id=evse_id, coordinator=coordinator
                    )
                    entities.append(sensor)
            for card in coordinator.data.chargeTokens:
                text = EVCardText(card_id=card.uuid, coordinator=coordinator)
                entities.append(text)

        async_add_entities(entities, True)

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("sensor async_remove_entry " + entry.entry_id)
    try:
        await hass.config_entries.async_forward_entry_unload(entry, Platform.SENSOR)
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass


class EVRechargePrivateSensor(
    CoordinatorEntity[EVRechargeUserDataUpdateCoordinator],
    SensorEntity,
):
    """This sensor represent a private charger."""

    def __init__(
        self, evse_id: EvseId, coordinator: EVRechargeUserDataUpdateCoordinator
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.evse_id = evse_id
        self.coordinator = coordinator
        self.charger = self._get_charger()
        self.evse = self._get_evse()
        self._attr_unique_id = f"{evse_id}-charger"
        self._attr_attribution = "account.shellrecharge.com"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None
        self._attr_has_entity_name = False
        self._attr_name = f"{self.charger.name} {self.charger.address.street} {self.charger.address.number} {self.charger.address.city}"
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, self._attr_name)},
            entry_type=None,
            manufacturer=self.charger.vendor,
            model=self.charger.model,
        )
        self._attr_options = list(
            typing.get_args(ChargePointDetailedStatus)
        )
        self._attr_supported_features = EVRechargeEntityFeature.TOGGLE_SESSION
        self._read_coordinator_data()

    def _get_charger(self) -> DetailedChargePoint:
        assets: DetailedAssets = self.coordinator.data
        if assets:
            for charger in assets.chargePoints:
                for evse in charger._embedded.evses:  # pylint: disable=protected-access
                    if evse.evseId == self.evse_id:
                        return charger
        raise HomeAssistantError("Charger not found in coordinator cache")

    def _get_evse(self) -> DetailedEvse:
        assets: DetailedAssets = self.coordinator.data
        if assets:
            for charger in assets.chargePoints:
                for evse in charger._embedded.evses:  # pylint: disable=protected-access
                    if evse.evseId == self.evse_id:
                        return evse
        raise HomeAssistantError("Evse not found in coordinator cache")

    def _read_coordinator_data(self) -> None:
        """Read data from shell recharge charger."""
        self.charger = self._get_charger()
        self.evse = self._get_evse()

        _LOGGER.debug(self.charger)
        _LOGGER.debug(self.evse)

        try:
            if self.charger and self.evse:
                self._attr_native_value = self.evse.status
                self._attr_icon = "mdi:ev-plug-type2"
                extra_data = {
                    "evse_id": self.evse.evseId,
                    "evse_uuid": self.evse.id,
                    "city": self.charger.address.city,
                    "country": self.charger.address.country,
                    "number": self.charger.address.number,
                    "street": self.charger.address.street,
                    "zip": self.charger.address.zip,
                    "connectivity": self.charger.connectivity,
                    "longitude": self.charger.coordinates.longitude,
                    "latitude": self.charger.coordinates.latitude,
                    "uuid": self.charger.id,
                    "model": self.charger.model,
                    "name": self.charger.name,
                    "plug_and_charge_capable": self.charger.plugAndCharge.capable,
                    "serial": self.charger.serial,
                    "sharing": self.charger.sharing,
                    "vendor": self.charger.vendor,
                }
                if self.evse.connectors:
                    connector = self.evse.connectors[0]
                    extra_data["connector_power_type"] = connector.electricCurrentType
                    extra_data["connector_max_current"] = connector.maxCurrentInAmps
                    extra_data["connector_max_power"] = connector.maxPowerInWatts
                    extra_data["connector_phases"] = connector.numberOfPhases

                if self.evse.statusDetails.rfid:
                    extra_data["connected_card_rfid"] = self.evse.statusDetails.rfid
                if self.evse.statusDetails.printedNumber:
                    extra_data[
                        "connected_card_number"
                    ] = self.evse.statusDetails.printedNumber
                self._attr_extra_state_attributes = extra_data

        except AttributeError as err:
            _LOGGER.error(err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self.async_write_ha_state()

    async def toggle_session(self, **kwargs: str) -> bool:
        """Handle the service call to toggle the charge point session."""
        toggle = kwargs.get("toggle", "")
        if toggle not in ["start", "stop"]:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_toggle",
                translation_placeholders={"toggle": toggle},
            )

        card = kwargs.get("card", "")

        success = await self.coordinator.toggle_session(self.charger.id, card, toggle)
        if not success:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="session_toggle",
                translation_placeholders={
                    "toggle": toggle,
                    "charger": self.charger.id,
                    "rfid": card,
                },
            )
        return True


class EVCardText(
    CoordinatorEntity[EVRechargeUserDataUpdateCoordinator],
    TextEntity,
):
    """This sensor represent a charge card."""

    def __init__(
        self, card_id: str, coordinator: EVRechargeUserDataUpdateCoordinator
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.card_id = card_id
        self.card = self._get_card()
        self._attr_unique_id = self.card.uuid
        self._attr_attribution = "account.shellrecharge.com"
        self._attr_has_entity_name = False
        self._attr_name = self.card.name
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, str(self._attr_name))},
            entry_type=None,
            manufacturer="Shell",
        )
        self._attr_native_value = self.card.rfid
        self._attr_icon = "mdi:account-credit-card"

    def _get_card(self) -> ChargeToken:
        assets: DetailedAssets = self.coordinator.data
        if assets:
            for card in assets.chargeTokens:
                if card.uuid == self.card_id:
                    return card
        raise HomeAssistantError("Charge card not found in coordinator cache")

class NearestSensor(
    CoordinatorEntity[StationsPublicDataUpdateCoordinator],
    SensorEntity,
):
    """Main feature of this integration. This sensor represents an EVSE and shows its realtime availability status."""

    def __init__(
        self,
        # evse_id: EvseId,
        coordinator: StationsPublicDataUpdateCoordinator,
        type: StationSensorType,
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        # self.evse_id = evse_id
        self.coordinator = coordinator
        self.type = type
        self.type_snake = " ".join(word.capitalize() for word in self.type.value.split("_"))  #snake_to_title(self.type.value)
        self.nearestChargingStations: NearestChargingStations = self.coordinator.data
        self.origin = self.nearestChargingStations.origin
        
        self.station: EnecoChargingStation = self.getStationForType(self.nearestChargingStations, type)
        
        # self._attr_name = f"{operator} {self.station.address.streetAndNumber} {self.station.address.city}{' ' + self.station.address.country if hasattr(self.station.address, "country") else ''}"
        # self._attr_name = self.station.name
        self._attr_name = f"{self.type_snake} {self.origin}"
        self._attr_has_entity_name = False
        self._attr_unique_id = f"{self.type_snake} {self.origin}"
        self._attr_attribution = "eneco-emobility.com"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None
        # if hasattr(self.station, "ownerName") and self.station.ownerName:
        #     operator = self.station.ownerName
        # else:
        #     operator = self.station.owner.name
        operator = self.type_snake
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, self._attr_unique_id)},
            entry_type=None,
            manufacturer=operator,
        )
        self._attr_options = list(typing.get_args(EnecoStatus))
        self._read_coordinator_data()

    def getStationForType(self, nearestChargingStations: NearestChargingStations, type: str) -> EnecoChargingStation | None:
        # _LOGGER.debug(f"getStationForType: nearestChargingStations: {nearestChargingStations}, type: {type}")
        station: EnecoChargingStation = None
        if type == StationSensorType.NEAREST_STATION:
            station = nearestChargingStations.nearest_station
        elif type == StationSensorType.NEAREST_AVAILABLE_STATION:
            station = nearestChargingStations.nearest_available_station
        elif type == StationSensorType.NEAREST_HIGHSPEED_STATION:
            station = nearestChargingStations.nearest_highspeed_station
        elif type == StationSensorType.NEAREST_AVAILABLE_HIGHSPEED_STATION:
            station = nearestChargingStations.nearest_available_highspeed_station
        elif type == StationSensorType.NEAREST_SUPERHIGHSPEED_STATION:
            station = nearestChargingStations.nearest_superhighspeed_station
        elif type == StationSensorType.NEAREST_AVAILABLE_SUPERHIGHSPEED_STATION:
            station = nearestChargingStations.nearest_available_superhighspeed_station
        return station


    def _choose_icon(self, connectors: list[EnecoConnector]) -> str:
        iconmap: dict[str, str] = {
            "Type1": "mdi:ev-plug-type1",
            "Type2": "mdi:ev-plug-type2",
            "IEC_62196_T2": "mdi:ev-plug-type2",
            "Type3": "mdi:ev-plug-type2",
            "Type1Combo": "mdi:ev-plug-ccs1",
            "Type2Combo": "mdi:ev-plug-ccs2",
            "IEC_62196_T2_COMBO": "mdi:ev-plug-ccs2",
            "SAEJ1772": "mdi:ev-plug-chademo",
            "TepcoCHAdeMO": "mdi:ev-plug-chademo",
            "Tesla": "mdi:ev-plug-tesla",
            "Domestic": "mdi:power-socket-eu",
            "Unspecified": "mdi:ev-station",
        }
        if len(connectors) != 1:
            return "mdi:ev-station"
        return iconmap.get(connectors[0].standard, "mdi:ev-station")

    STATUS_PRIORITY = {
        "AVAILABLE": 0,
        "CHARGING": 1,
        "BLOCKED": 2,
        "UNAVAILABLE": 3,
        "OUTOFORDER": 4,
        "UNKNOWN": 5,
    }
    def evse_sort_key(self,evse):
        max_power = max(
            (connector.maxPower for connector in evse.connectors),
            default=0,
        )
        status_rank = self.STATUS_PRIORITY.get(evse.status, 99)

        return (-max_power, status_rank)
    def _get_evse(self) -> EnecoEvse | None:
        # self.station = self.getStationForType(self.coordinator.data, type)
        if self.station:
            
            filtered_sorted = sorted(self.station.evses, key=self.evse_sort_key)
            for evse in filtered_sorted:
                if self.station.evseSummary.available > 0:
                    if evse.status == "AVAILABLE":
                        return evse
                else:
                    if evse.status != "OUTOFORDER":
                        return evse
        return None
    def _read_coordinator_data(self) -> None:
        """Read data from ev station."""
        self.station = self.getStationForType(self.coordinator.data, self.type)
        evse: EnecoEvse = self._get_evse()
        _LOGGER.debug(f"_read_coordinator_data: evse: {evse}, station: {self.station}")

        try:
            if evse:
                # self._attr_name = self.station.name
                self._attr_native_value = evse.status
                self._attr_icon = self._choose_icon(evse.connectors)
                connector: EnecoConnector = evse.connectors[0]
                extra_data = {
                    "name": self.station.name,
                    "type": self.type.value,
                    "origin": self.origin,
                    "address": self.station.address.streetAndHouseNumber,
                    "city": self.station.address.city,
                    "postal_code": self.station.address.postcode,
                    "country": self.station.address.country,
                    "latitude": self.station.coordinates.lat,
                    "longitude": self.station.coordinates.lng,
                    "straight_line_distance": self.station.straight_line_distance,
                    "route_distance": self.station.route_distance,
                    "route_duration": self.station.route_duration,
                    "route_name": self.station.route_name,
                    "operator_name": self.station.ownerName,
                    # "suboperator_name": self.station.owner.name,
                    "url": self.station.url,
                    "facilities": ", ".join(self.station.facilities),
                    "available_connectors": self.station.evseSummary.available,
                    "number_of_connectors": self.station.evseSummary.total,
                    "max_speed_kWh": self.station.evseSummary.maxSpeed/1000 if self.station.evseSummary.maxSpeed else None,
                    "min_speed_kWh": self.station.evseSummary.minSpeed/1000 if self.station.evseSummary.minSpeed else None,
                    "is_unlimited": self.station.evseSummary.isUnlimited,
                    "is_limited": self.station.evseSummary.isLimited,
                    "is_unkown": self.station.evseSummary.isUnknown,
                    "allowed": self.station.isAllowed,
                    "external_id": str(self.station.id),
                    "evse_id": str(evse.evseId),
                    "status": evse.status,
                    "last_updated": evse.lastUpdated,
                    "physical_reference": evse.physicalReference,
                    "connector_standard": connector.standard,
                    "connector_type": connector.powerType,
                    "connector_format": connector.format,
                    "connector_max_power": connector.maxPower/1000 if connector.maxPower else None,
                    "opentwentyfourseven": self.station.isTwentyFourSeven,
                    "charging_costs": evse.prices.chargingCosts if evse.prices else None,
                    "charging_time_costs": evse.prices.chargingTimeCosts if evse.prices else None,
                    "start_tariff": evse.prices.startTariff if evse.prices else None,
                    "parking_time_costs": evse.prices.parkingTimeCosts if evse.prices else None,
                    "price_description": evse.prices.description if evse.prices else None,
                    "map_label": f"{self.station.evseSummary.available}/{self.station.evseSummary.total}{' ' + str(int(connector.maxPower/1000)) + 'kWh' if connector.maxPower else ''}",
                }
                self._attr_extra_state_attributes = extra_data
        except AttributeError as err:
            _LOGGER.error(err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self._attr_name = f"{self.station.name}"
        self.async_write_ha_state()

    
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + self.entity_id)

class EVShellRechargeSensor(
    CoordinatorEntity[EVRechargePublicDataUpdateCoordinator],
    SensorEntity,
):
    """Main feature of this integration. This sensor represents an EVSE and shows its realtime availability status."""

    def __init__(
        self,
        evse_id: EvseId,
        coordinator: EVRechargePublicDataUpdateCoordinator,
    ) -> None:
        """Initialize the Sensor."""
        super().__init__(coordinator)
        self.evse_id = evse_id
        self.coordinator = coordinator
        self.location: ShellChargingStation = self.coordinator.data
        self._attr_unique_id = f"{evse_id}-charger"
        self._attr_attribution = "shellrecharge.com"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None
        if hasattr(self.location, "suboperatorName") and self.location.suboperatorName:
            operator = self.location.suboperatorName
        else:
            operator = self.location.operatorName
        self._attr_has_entity_name = False
        self._attr_name = f"{operator} {self.location.address.streetAndNumber} {self.location.address.city}"
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            identifiers={(DOMAIN, self._attr_name)},
            entry_type=None,
            manufacturer=operator,
        )
        self._attr_options = list(typing.get_args(ShellStatus))
        self._read_coordinator_data()

    def _get_evse(self) -> Any:
        location: ShellChargingStation = self.coordinator.data
        if location:
            for evse in location.evses:
                if evse.uid == self.evse_id:
                    return evse
        return None

    def _choose_icon(self, connectors: list[ShellConnector]) -> str:
        iconmap: dict[str, str] = {
            "Type1": "mdi:ev-plug-type1",
            "Type2": "mdi:ev-plug-type2",
            "Type3": "mdi:ev-plug-type2",
            "Type1Combo": "mdi:ev-plug-ccs1",
            "Type2Combo": "mdi:ev-plug-ccs2",
            "SAEJ1772": "mdi:ev-plug-chademo",
            "TepcoCHAdeMO": "mdi:ev-plug-chademo",
            "Tesla": "mdi:ev-plug-tesla",
            "Domestic": "mdi:power-socket-eu",
            "Unspecified": "mdi:ev-station",
        }
        if len(connectors) != 1:
            return "mdi:ev-station"
        return iconmap.get(connectors[0].connectorType, "mdi:ev-station")

    def _read_coordinator_data(self) -> None:
        """Read data from shell recharge ev."""
        evse = self._get_evse()
        location: ShellChargingStation = self.coordinator.data
        _LOGGER.debug(evse)

        try:
            if evse:
                self._attr_native_value = evse.status
                self._attr_icon = self._choose_icon(evse.connectors)
                connector = evse.connectors[0]
                extra_data = {
                    "address": location.address.streetAndNumber,
                    "city": location.address.city,
                    "postal_code": location.address.postalCode,
                    "country": location.address.country,
                    "latitude": location.coordinates.latitude,
                    "longitude": location.coordinates.longitude,
                    "operator_name": location.operatorName,
                    "suboperator_name": location.suboperatorName,
                    "support_phonenumber": location.supportPhoneNumber,
                    "tariff_startfee": connector.tariff.startFee,
                    "tariff_per_kwh": connector.tariff.perKWh,
                    "tariff_per_minute": connector.tariff.perMinute,
                    "tariff_currency": connector.tariff.currency,
                    "tariff_updated": connector.tariff.updated,
                    "tariff_updated_by": connector.tariff.updatedBy,
                    "tariff_structure": connector.tariff.structure,
                    "connector_power_type": connector.electricalProperties.powerType,
                    "connector_voltage": connector.electricalProperties.voltage,
                    "connector_ampere": connector.electricalProperties.amperage,
                    "connector_max_power": connector.electricalProperties.maxElectricPower,
                    "connector_fixed_cable": connector.fixedCable,
                    "accessibility": location.accessibilityV2.status,
                    "external_id": str(location.externalId),
                    "evse_id": str(evse.evseId),
                    "opentwentyfourseven": location.openTwentyFourSeven,
                    # "opening_hours": location.openingHours,
                    # "predicted_occupancies": location.predictedOccupancies,
                }
                self._attr_extra_state_attributes = extra_data
        except AttributeError as err:
            _LOGGER.error(err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._read_coordinator_data()
        self.async_write_ha_state()
