"""Models for pydantic parsing."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

DateTimeISO8601 = str
Status = Literal["Available", "Unavailable", "Occupied", "Unknown"]
ConnectorTypes = Literal[
    "Avcon",
    "Domestic",
    "Industrial2PDc",
    "IndustrialPneAc",
    "Industrial3PEAc",
    "Industrial3PENAc",
    "Type1",
    "Type1Combo",
    "Type2",
    "Type2Combo",
    "Type3",
    "LPI",
    "Nema520",
    "SAEJ1772",
    "SPI",
    "TepcoCHAdeMO",
    "Tesla",
    "Unspecified",
]
UpdatedBy = Literal["Feed", "Admin", "TariffService", "Default", "Hubpp"]


class ElectricalProperties(BaseModel):
    """Plugs and specs."""

    powerType: str
    voltage: int
    amperage: float
    maxElectricPower: float


class Tariff(BaseModel):
    """Tariff information."""

    startFee: Optional[float] = 0.0
    perMinute: Optional[float] = 0.0
    perKWh: Optional[float] = 0.0
    currency: str
    updated: DateTimeISO8601
    updatedBy: UpdatedBy
    structure: str


class Connector(BaseModel):
    """Connector instance."""

    uid: int
    externalId: str
    connectorType: ConnectorTypes
    electricalProperties: ElectricalProperties
    fixedCable: bool
    tariff: Tariff
    updated: DateTimeISO8601
    updatedBy: UpdatedBy
    externalTariffId: Optional[str] = ""


class Evse(BaseModel):
    """Evse instance."""

    uid: int
    externalId: str
    evseId: str
    status: Status
    connectors: list[Connector]
    authorizationMethods: list[str]
    physicalReference: str
    updated: DateTimeISO8601


class Coordinates(BaseModel):
    """Location."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Address(BaseModel):
    """Address."""

    streetAndNumber: str
    postalCode: str
    city: str
    country: str


class Accessibility(BaseModel):
    """Accessibility."""

    status: str
    remark: Optional[str] = ""
    statusV2: str


class AccessibilityV2(BaseModel):
    """Accessibility Version2."""

    status: str


class OpeningHours(BaseModel):
    """Opening Hours."""

    weekDay: str
    startTime: str
    endTime: str


class PredictedOccupancies(BaseModel):
    """Predicted Occupancies."""

    weekDay: str
    occupancy: int
    startTime: str
    endTime: str


class Location(BaseModel):
    """Location data."""

    uid: int
    externalId: int | str
    coordinates: Coordinates
    operatorName: str
    operatorId: Optional[str] = ""
    address: Address
    accessibility: Accessibility
    accessibilityV2: AccessibilityV2
    evses: list[Evse]
    openTwentyFourSeven: Optional[bool] = True
    openingHours: Optional[list[OpeningHours]] = []
    updated: DateTimeISO8601
    locationType: str
    supportPhoneNumber: Optional[str] = ""
    facilities: Optional[list[str]] = []
    predictedOccupancies: Optional[list[PredictedOccupancies]] = []
    suboperatorName: Optional[str] = ""
    countryCode: str
    partyId: str
    roamingSource: str
