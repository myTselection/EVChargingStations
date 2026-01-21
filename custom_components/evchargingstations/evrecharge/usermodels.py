"""Models for pydantic parsing."""

from typing import Literal, Optional

from pydantic import UUID4, BaseModel, Field

DateTimeISO8601 = str
ChargePointStatus = Literal["Available", "Unavailable", "Occupied", "Unknown", "Charging", "Faulted"]
ChargePointDetailedStatus = Literal["available", "preparing", "charging", "suspendedev", "faulted"]
Vendor = Literal["NewMotion"]
UpdatedBy = Literal["Feed", "Admin", "TariffService", "Default", "Hubpp"]


class ChargeToken(BaseModel):
    """Charge card."""

    uuid: str
    rfid: str
    printedNumber: str
    name: str


class OccupyingToken(BaseModel):
    """Charge card occupying a charger"""

    rfid: Optional[str] = None
    printedNumber: Optional[str] = None
    timestamp: DateTimeISO8601


class Evse(BaseModel):
    """Basic EVSE representation for charge points."""

    evseId: str
    number: int
    occupyingToken: OccupyingToken
    status: ChargePointStatus


class ChargePoint(BaseModel):
    """Charge point."""

    evses: list[Evse]
    name: str
    serial: str
    uuid: UUID4


class Assets(BaseModel):
    chargePoints: list[ChargePoint]
    chargeTokens: list[ChargeToken]


class Address(BaseModel):
    """Address."""

    city: str
    country: str
    number: str
    street: str
    zip: str


class Coordinates(BaseModel):
    """Location."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class PlugAndCharge(BaseModel):
    """Plug & charge support."""

    capable: Literal[True, False]


class Tariff(BaseModel):
    """Tariff information."""

    startFee: Optional[float] = 0.0
    perMinute: Optional[float] = 0.0
    perKWh: Optional[float] = 0.0
    currency: str
    updated: DateTimeISO8601
    updatedBy: UpdatedBy
    structure: str


class LatestOnlineStatus(BaseModel):
    """Last time the charger was online."""

    lastChanged: DateTimeISO8601
    online: Literal[True, False]


class Href(BaseModel):
    """API path."""

    href: str


class Links(BaseModel):
    """Self-describing links."""

    self: Href
    evses: Optional[Href] = None


class Connector(BaseModel):
    """Specs of the charger."""

    connectorType: str
    electricCurrentType: Literal["AC", "DC"]
    maxCurrentInAmps: int
    maxPowerInWatts: int = Field(ge=1000)
    number: int
    numberOfPhases: Literal[1, 3]
    tariff: Optional[Tariff] = Field(default=None)


class DetailedEvse(BaseModel):
    """Evse instance."""

    _links: Href
    connectors: list[Connector]
    currentType: Literal["ac", "dc"]
    evseId: str
    id: UUID4
    maxPower: int
    number: int
    status: ChargePointDetailedStatus
    statusDetails: OccupyingToken


class Embedded(BaseModel):
    """Embedded charger details."""

    evses: list[DetailedEvse]


class DetailedChargePoint(BaseModel):
    """Charge point details."""

    _embedded: Embedded
    _links: Links
    address: Address
    connectivity: Literal["online", "offline"]
    coordinates: Coordinates
    firstConnection: DateTimeISO8601
    id: UUID4
    lastConnection: DateTimeISO8601
    lastSession: DateTimeISO8601
    latestOnlineStatus: LatestOnlineStatus
    model: str
    name: str
    plugAndCharge: PlugAndCharge
    protocol: Literal["ocpp 1.6-j"]
    serial: str
    sharing: Literal["private", "public"]
    vendor: Vendor

    def __init__(self, **data):
        super().__init__(**data)
        # Pydantic excludes attributes starting with underscore from the model
        # https://docs.pydantic.dev/latest/concepts/models/#private-model-attributes
        self._embedded = Embedded.model_validate(data["_embedded"])


class DetailedAssets(BaseModel):
    chargePoints: list[DetailedChargePoint]
    chargeTokens: list[ChargeToken]
