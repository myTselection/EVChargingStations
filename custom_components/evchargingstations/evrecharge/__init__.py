"""The shellrecharge API code."""

import logging
import math

from asyncio import CancelledError, TimeoutError
from typing import Optional
import math

import pydantic
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError
from aiohttp_retry import ExponentialRetry, RetryClient
from pydantic import ValidationError
from yarl import URL

from .models import ShellChargingStation, Coords, EnecoChargingStation, NearestChargingStations, EnecoTariff
from .user import User

import logging

_LOGGER = logging.getLogger(__name__)
_RADIUS = 100

class EVApi:
    """Class to make API requests."""

    def __init__(self, websession: ClientSession, source: str = "eneco"):
        """Initialize the session."""
        self.websession = websession
        self.logger = logging.getLogger("evrecharge")
        self.retry_client = RetryClient(
            client_session=self.websession,
            retry_options=ExponentialRetry(attempts=3, start_timeout=5),
        )
        self.source = source

    async def station_by_id(self, station_id: str) -> ShellChargingStation | EnecoChargingStation | None:
        """
        Perform API request.
        Usually yields just one Location object with one or multiple chargers.
        """

        if self.source == "eneco":
            return await self.getEnecoChargingStation(station_id)
        
        if self.source == "shell":
            return await self.getShellChargingStation(station_id)(station_id)

    async def getShellChargingStation(self, station_id):
        url = URL(
            "https://ui-map.shellrecharge.com/api/map/v2/locations/search/{}".format(
                station_id
            )
        )
        response = await self.json_get_with_retry_client(url)
        
        if pydantic.version.VERSION.startswith("1"):
            station = ShellChargingStation.parse_obj(response[0])
        else:
            station = ShellChargingStation.model_validate(response[0])

        return station

    async def getEnecoChargingStation(self, station_id):
        url = URL(
            "https://ui-map.shellrecharge.com/api/map/v2/locations/search/{}".format(
                station_id
            )
        )
        response = await self.json_get_with_retry_client(url)
        
        if pydantic.version.VERSION.startswith("1"):
            station = ShellChargingStation.parse_obj(response[0])
        else:
            station = ShellChargingStation.model_validate(response[0])

        return station


    # async def nearby_stations(self, coordinates: Coords) -> list[ChargingStation] | None :
    async def nearby_stations(self, origin: str, origin_coordinates: Coords, onlyEnecoStations: bool, filter:str = "") -> NearestChargingStations | None :
        """
        Perform API request.
        Usually yields list of station object with one or multiple chargers.
        """
        stations: list[EnecoChargingStation]
        _LOGGER.debug(f"searching nearby_stations for coordinates {origin_coordinates}")
        stations = await self.getEnecoChargingStations(origin_coordinates, onlyEnecoStations)
        # _LOGGER.debug(f"nearby_stations found {stations}")

        # sorted_locations = sorted(stations, key=lambda x: x.get("distance", float("inf"), reverse=False))
        filtered_sorted = sorted(
            stations if filter == "" else (station for station in stations if filter in station.owner.name.lower()),
            key=lambda x: x.straight_line_distance if hasattr(x, "distance") and x.straight_line_distance is not None else float("inf"), reverse=False
        )

        # _LOGGER.debug(f"filtered_sorted: {filtered_sorted}")
        
        nearestChargingStations: NearestChargingStations = NearestChargingStations()
        nearestChargingStations.origin = origin

        for station in filtered_sorted:
            # _LOGGER.debug(f"station: {station}")
            if nearestChargingStations.nearest_station == None:
                await self.addEnecoPrices(station)
                nearestChargingStations.nearest_station = station
            if nearestChargingStations.nearest_available_station == None and station.evseSummary.available > 0:
                await self.addEnecoPrices(station)
                nearestChargingStations.nearest_available_station = station
            if nearestChargingStations.nearest_highspeed_station == None and station.evseSummary.maxSpeed > 50000:
                await self.addEnecoPrices(station)
                nearestChargingStations.nearest_highspeed_station = station
            if nearestChargingStations.nearest_available_highspeed_station == None and station.evseSummary.maxSpeed > 50000 and station.evseSummary.available > 0:
                await self.addEnecoPrices(station)
                nearestChargingStations.nearest_available_highspeed_station = station
            if nearestChargingStations.nearest_superhighspeed_station == None and station.evseSummary.maxSpeed > 100000:
                await self.addEnecoPrices(station)
                nearestChargingStations.nearest_superhighspeed_station = station
            if nearestChargingStations.nearest_available_superhighspeed_station == None and station.evseSummary.maxSpeed > 100000 and station.evseSummary.available > 0:
                await self.addEnecoPrices(station)
                nearestChargingStations.nearest_available_superhighspeed_station = station

            #break when all set
            if nearestChargingStations.nearest_station != None and nearestChargingStations.nearest_available_station != None and nearestChargingStations.nearest_highspeed_station != None and nearestChargingStations.nearest_available_highspeed_station != None and nearestChargingStations.nearest_superhighspeed_station != None and nearestChargingStations.nearest_available_superhighspeed_station != None:
                # _LOGGER.debug(f"nearestChargingStations: {nearestChargingStations}")
                break


        _LOGGER.debug(f"nearestChargingStations: {nearestChargingStations}")

        return nearestChargingStations
    
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the Earth in kilometers
        earth_radius = 6371

        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Calculate the distance
        distance = round(earth_radius * c, 2)
        # _LOGGER.debug(f"distance: {distance}, lat1: {lat1}, lon1: {lon1}, lat2: {lat2}, lon2: {lon2}")

        return distance

        # # Example usage
        # lat1 = 52.5200  # Latitude of location 1
        # lon1 = 13.4050  # Longitude of location 1
        # lat2 = 48.8566  # Latitude of location 2
        # lon2 = 2.3522   # Longitude of location 2

        # distance = haversine_distance(lat1, lon1, lat2, lon2)
        # print(f"Approximate distance: {distance:.2f} km")


    
    # def getChargingStations(self, postalcode, country, town, locationinfo, fueltype: ConnectorTypes, single):
    async def getEnecoChargingStations(self, origin_coordinates, onlyEnecoStations: bool) -> list[EnecoChargingStation] | None:
        # _LOGGER.debug(f"Eneco charge points Fueltype: {connector_types} filter {filter} origin: {resolved_origin}")
        # header = {"Content-Type": "application/json","Accept": "application/json", "Origin": "https://www.eneco-emobility.com", "Referer": "https://www.eneco-emobility.com/be-nl/chargemap", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36", "X-Requested-With": "XMLHttpRequest"}
        # https://www.eneco-emobility.com/be-nl/chargemap#

        header = self.getEnecoHttpHeaders()
        
        all_stations = []
        locationInfoLat = float(str(origin_coordinates.get('lat')).replace(',','.'))
        locationInfoLon = float(str(origin_coordinates.get('lon')).replace(',','.'))
        
        # _LOGGER.debug(f"coordinates: {origin_coordinates}")
        # boundingbox = origin_coordinates.get('bounds')
        # if boundingbox == None or len(boundingbox) == 0:
            # boundingbox = self.convertLatLonBoundingBox(origin_coordinates.get('lat'), origin_coordinates.get('lon'))
        someTypesMissing = True
        standardSpeedFound = False
        highspeedFound = False
        superHighSpeedFound = False
        standardAvailableSpeedFound = False
        highspeedAvailableFound = False
        superHighSpeedAvailableFound = False
        loop = 1
        while someTypesMissing:
            if loop > 15:
                _LOGGER.warning(f"No required stations found in current radius, currRadius {currRadius}, loop {loop}, standardSpeedFound: {standardSpeedFound}and highspeedFound {highspeedFound} and superHighSpeedFound {superHighSpeedFound}, onlyEnecoStations {onlyEnecoStations}, highspeedAvailableFound {highspeedAvailableFound} and standardAvailableSpeedFound {standardAvailableSpeedFound} and superHighSpeedAvailableFound {superHighSpeedAvailableFound}. Ending loop.")
                break
            currRadius = _RADIUS * loop
            loop += 1
            boundingbox = self.create_boundingbox_array(locationInfoLat,locationInfoLon, currRadius)
            origin_coordinates['bounds'] = boundingbox
            # _LOGGER.debug(f"boundingbox: {boundingbox}, coordinates: {origin_coordinates}, radius: {currRadius}")

            deault_payload = self.defaultEnecoPayload(origin_coordinates)
            try:
                totalEves = await self.countChargingStationsPayload(deault_payload)
            except Exception as e:
                _LOGGER.debug(f"No stations found in current radius. Eneco countChargingStationsPayload, currRadius {currRadius}, exception: {e}")
                continue
            _LOGGER.info(f"Total Eneco EVs: {totalEves}")
            if totalEves == 0:
                continue
            eneco_url_polygon = "https://www.eneco-emobility.com/api/chargemap/search-polygon"
            payload = {
                "bounds": deault_payload.get('bounds'),
                "filters": {
                    "availableNow": True if standardSpeedFound and highspeedFound and superHighSpeedFound else False, 
                    "isAllowed": onlyEnecoStations, 
                    "speed": [11 if not standardSpeedFound else 50 if not highspeedFound else 100, 350], 
                    "connectorTypes": []},
                "zoomLevel": 16
            }
            lon_min = boundingbox[1]
            lon_max = boundingbox[3]
            lat_min = boundingbox[0]
            lat_max = boundingbox[2]
            zoomlevel = 17
            #return [
            #     lat - lat_delta,  # south
            #     lon - lon_delta,  # west
            #     lat + lat_delta,  # north
            #     lon + lon_delta   # east
            # ]
            url_shell = f"https://ui-map.shellrecharge.com/api/map/v2/markers/{lon_min}/{lon_max}/{lat_min}/{lat_max}/{zoomlevel}"
            #only shell card
            url_shell = f"https://ui-map.shellrecharge.com/api/map/v2/markers/4.807961539062489/4.972756460937489/52.35012933719833/52.39786576367266/14/available,unavailable,occupied,unknown/TepcoCHAdeMO,Type2,Type3,Type1,Type2Combo,Domestic/3.3/excludeUnsupportedTokens"
            #only available and shell card
            url_shell = f"https://ui-map.shellrecharge.com/api/map/v2/markers/4.807961539062489/4.972756460937489/52.35012933719833/52.39786576367266/14/available/TepcoCHAdeMO,Type2,Type3,Type1,Type2Combo,Domestic/3.3/excludeUnsupportedTokens"
            #using locationUid
            locationUid = 5293763
            url_shell_location_details = f"https://ui-map.shellrecharge.com/api/map/v2/locations/{locationUid}"
            try:
                eneco_stations = await self.json_post_with_retry_client(eneco_url_polygon, payload, header)
            except Exception as e:
                _LOGGER.debug(f"ERROR: Eneco URL: {eneco_url_polygon}, {payload}, {e}")
                continue
            # _LOGGER.debug(f"Eneco EVs: {eneco_stations}")
            standardSpeedFound = True
            # if response_polygon.status_code != 200:
                # _LOGGER.error(f"ERROR: Eneco URL: {eneco_url_polygon}, {payload}, {response_polygon.text}")
            # assert response_polygon.status_code == 200
            for eneco_station in eneco_stations[:1000]:
                station: EnecoChargingStation = EnecoChargingStation.model_validate(eneco_station)
                # if station.id in all_ids:
                    # continue
                station_lat = station.coordinates.lat
                station_lon = station.coordinates.lng
                station.url = f"https://www.eneco-emobility.com/be-nl/chargemap#loc={station_lat}%2C{station_lon}%2C17&selected={station.id}"
                if station.address.country is None and station.evses is not None and len(station.evses) > 0 and station.evses[0].evseId is not None:
                    station.address.country = station.evses[0].evseId[:2]

                distance = self.haversine_distance(float(str(station_lat).replace(',','.')), float(str(station_lon).replace(',','.')), locationInfoLat, locationInfoLon)
                station.straight_line_distance = distance
                station.source = "Eneco"
                if station.evseSummary is not None:
                    if station.evseSummary.available > 0:
                        standardAvailableSpeedFound = True
                    if station.evseSummary.maxSpeed >= 50000:
                        highspeedFound = True
                        if station.evseSummary.available > 0:
                            highspeedAvailableFound = True
                    if station.evseSummary.maxSpeed >= 100000:
                        superHighSpeedFound = True
                        if station.evseSummary.available > 0:
                            superHighSpeedAvailableFound = True               
                all_stations.append(station)
                if highspeedFound and standardSpeedFound and superHighSpeedFound and highspeedAvailableFound and standardAvailableSpeedFound and superHighSpeedAvailableFound:
                    someTypesMissing = False
                    break
        return all_stations

    async def addEnecoPrices(self, station: EnecoChargingStation)-> EnecoChargingStation | None:
        header = self.getEnecoHttpHeaders()
        evses = station.evses
        lastConnector = None
        lastConnectorMaxPower = None
        lastPrices:EnecoTariff = None
        for evse in evses:
            evseId = evse.evseId
            if evse.prices is not None:
                continue
            if evse.connectors is not None and len(evse.connectors) > 0:
                connector = evse.connectors[0]
                currConnector = connector.standard
                currConnectorMaxPower = connector.maxPower
                if lastPrices is None or currConnector != lastConnector or currConnectorMaxPower != lastConnectorMaxPower:
                    lastConnector = currConnector
                    lastConnectorMaxPower = currConnectorMaxPower
                    evse_price_url = "https://www.eneco-emobility.com/api/chargemap/evse-pricing"
                    payload = {"evseId": evseId, "country": "be"}
                    # _LOGGER.debug(f"Eneco prices: {evse_price_url}, payload: {payload}")
                    eneco_prices = await self.json_post_with_retry_client(evse_price_url, payload, header)
                    if eneco_prices:
                        _LOGGER.debug(f"Eneco prices: {eneco_prices}, payload {payload}")
                        eneco_prices_model = EnecoTariff.model_validate(eneco_prices)
                        evse.prices = eneco_prices_model
                        lastPrices = eneco_prices_model
                else:
                    evse.prices = lastPrices
            else:
                _LOGGER.debug(f"Eneco prices no connectors found: {evse}")
        return station
    
    
    def create_boundingbox_array(self, lat, lon, radius_m):
        earth_radius_m = 6371000

        lat_delta = (radius_m / earth_radius_m) * (180 / math.pi)
        lon_delta = (radius_m / earth_radius_m) * (180 / math.pi) / math.cos(math.radians(lat))

        return [
            lat - lat_delta,  # south
            lon - lon_delta,  # west
            lat + lat_delta,  # north
            lon + lon_delta   # east
        ]
    
    def defaultEnecoPayload(self, coordinates: Coords):
        _LOGGER.debug(f"coordinates: {coordinates}")
        boundingbox = coordinates.get('bounds')
        bounds =  {
                    "northWest": [boundingbox[2],boundingbox[1]],
                    "northEast": [boundingbox[2],boundingbox[3]],
                    "southEast": [boundingbox[0],boundingbox[3]],
                    "southWest": [boundingbox[0],boundingbox[1]]
            }
        payload = {
                "bounds": bounds,
                "filters": {
                    "fastCharging": False,
                    "ultraFastCharging": False
                },
                "zoomLevel": 15
            }
        
        return payload

    def getEnecoHttpHeaders(self):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/142.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Referer": "https://www.eneco-emobility.com/be-nl/chargemap",
            "Origin": "https://www.eneco-emobility.com",
        }
        
        return header

    def countChargingStations(self, origin_coordinates):
        
        _LOGGER.debug(f"coordinates: {origin_coordinates}")
        boundingbox = origin_coordinates.get('bounds')
        if boundingbox == None or len(boundingbox) == 0:
            # boundingbox = self.convertLatLonBoundingBox(origin_coordinates.get('lat'), origin_coordinates.get('lon'))
            boundingbox = self.create_boundingbox_array(origin_coordinates.get('lat'), origin_coordinates.get('lon'), 5000)
            origin_coordinates['bounds'] = boundingbox
        _LOGGER.debug(f"boundingbox: {boundingbox}, coordinates: {origin_coordinates}")
        default_payload = self.defaultEnecoPayload(origin_coordinates)
        return self.countChargingStationsPayload(default_payload)
    
    async def countChargingStationsPayload(self, payload):
        eneco_url = "https://www.eneco-emobility.com/api/chargemap/search-clusters"
        header = self.getEnecoHttpHeaders()
        totalEves = 0
        clusters = await self.json_post_with_retry_client(eneco_url, payload, header)
        for cluster in clusters:
            totalEves += cluster.get("evseTotal",0)
        return totalEves


    async def json_get_with_retry_client(self, url, header=None):
        json_response = None
        try:
            async with self.retry_client.get(url, headers=header) as response:
                _LOGGER.debug(f"response url {url}, status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    _LOGGER.debug(f"response get url {url}, status: {response.status}, response: {result}")
                    if result:
                        json_response = result
                    else:
                        raise LocationEmptyError()
                elif response.status == 429:
                    raise RateLimitHitError("Rate limit of API has been hit")
                else:
                    self.logger.exception(
                        "HTTPError %s occurred while requesting %s",
                        response.status,
                        url,
                    )
        except ValidationError as err:
            raise LocationValidationError(err)
        except (
            ClientError,
            TimeoutError,
            CancelledError,
            ) as err:
            # Something else failed
            raise err
        return json_response


    async def json_post_with_retry_client(self, url, payload, header):
        json_response = None
        try:
            async with self.retry_client.post(url, headers=header, json=payload) as response:
                _LOGGER.debug(f"response post url {url}, status: {response.status}, payload: {payload}")
                if response.status == 200:
                    result = await response.json()
                    _LOGGER.debug(f"response post url {url}, status: {response.status}, payload: {payload}, response: {result}")
                    if result:
                        json_response = result
                    else:
                        raise LocationEmptyError()
                elif response.status == 429:
                    raise RateLimitHitError("Rate limit of API has been hit")
                else:
                    self.logger.exception(
                        "HTTPError %s occurred while requesting %s",
                        response.status,
                        url,
                    )
        except ValidationError as err:
            _LOGGER.error(err)
            raise LocationValidationError(err)
        except (
            ClientError,
            TimeoutError,
            CancelledError,
        ) as err:
            _LOGGER.warning(err)
            # Something else failed
            raise err
        return json_response


    async def get_user(self, email: str, pwd: str, api_key: Optional[str] = None) -> User:
        user = User(email, pwd, self.websession, api_key)
        if not api_key:
            await user.authenticate()
        return user
    

class LocationEmptyError(Exception):
    """Raised when returned Location API data is empty."""

    pass


class LocationValidationError(Exception):
    """Raised when returned Location API data is in the wrong format."""

    pass


class RateLimitHitError(Exception):
    """Raised when the rate limit of the API has been hit."""

    pass
