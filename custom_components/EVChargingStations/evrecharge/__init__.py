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

from .models import ShellChargingStation, Coords, EnecoChargingStation
from .user import User

import logging

_LOGGER = logging.getLogger(__name__)
_RADIUS = 1000

class EVApi:
    """Class to make API requests."""

    def __init__(self, websession: ClientSession):
        """Initialize the session."""
        self.websession = websession
        self.logger = logging.getLogger("evrecharge")
        self.retry_client = RetryClient(
            client_session=self.websession,
            retry_options=ExponentialRetry(attempts=3, start_timeout=5),
        )    

    async def station_by_id(self, station_id: str) -> ShellChargingStation | None:
        """
        Perform API request.
        Usually yields just one Location object with one or multiple chargers.
        """
        station = None

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
    async def nearby_stations(self, coordinates: Coords, filter = "") -> list[EnecoChargingStation] | None :
        """
        Perform API request.
        Usually yields list of station object with one or multiple chargers.
        """
        stations: list[EnecoChargingStation]
        _LOGGER.info(f"searching nearby_stations for coordinates {coordinates}")
        stations = await self.getEnecoChargingStations(coordinates)
        _LOGGER.info(f"nearby_stations found {stations}")

        # sorted_locations = sorted(stations, key=lambda x: x.get("distance", float("inf"), reverse=False))
        filtered_sorted = sorted(
            stations if filter == "" else (station for station in stations if filter in station.owner.name.lower()),
            key=lambda x: x.distance if x.distance is not None else float("inf", float("inf")), reverse=False
        )

        nearest_station:EnecoChargingStation = None
        nearest_available_station:EnecoChargingStation = None
        nearest_highspeed_station:EnecoChargingStation = None
        nearest_available_highspeed_station:EnecoChargingStation = None
        nearest_superhighspeed_station:EnecoChargingStation = None
        nearest_available_superhighspeed_station:EnecoChargingStation = None

        for station in filtered_sorted:
            _LOGGER.info(f"station: {station}")
            if nearest_station == None:
                nearest_station = station
            if nearest_available_station == None and station.evseSummary.available > 0:
                nearest_available_station = station
            if nearest_highspeed_station == None and station.evseSummary.maxSpeed > 50000:
                nearest_highspeed_station = station
            if nearest_available_highspeed_station == None and station.evseSummary.maxSpeed > 50000 and station.evseSummary.available > 0:
                nearest_available_highspeed_station = station
            if nearest_superhighspeed_station == None and station.evseSummary.maxSpeed > 100000:
                nearest_superhighspeed_station = station
            if nearest_available_superhighspeed_station == None and station.evseSummary.maxSpeed > 100000 and station.evseSummary.available > 0:
                nearest_available_superhighspeed_station = station

            if nearest_available_station != None and nearest_available_highspeed_station != None and nearest_available_superhighspeed_station != None:
                break

        return {
            "nearest_station":nearest_station,
            "nearest_available_station":nearest_available_station,
            "nearest_highspeed_station":nearest_highspeed_station,
            "nearest_available_highspeed_station":nearest_available_highspeed_station,
            "nearest_superhighspeed_station":nearest_superhighspeed_station,
            "nearest_available_superhighspeed_station":nearest_available_superhighspeed_station
        }
    
    
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

        return distance

        # # Example usage
        # lat1 = 52.5200  # Latitude of location 1
        # lon1 = 13.4050  # Longitude of location 1
        # lat2 = 48.8566  # Latitude of location 2
        # lon2 = 2.3522   # Longitude of location 2

        # distance = haversine_distance(lat1, lon1, lat2, lon2)
        # print(f"Approximate distance: {distance:.2f} km")


    
    # def getChargingStations(self, postalcode, country, town, locationinfo, fueltype: ConnectorTypes, single):
    async def getEnecoChargingStations(self, origin_coordinates) -> list[EnecoChargingStation] | None:
        # _LOGGER.info(f"Eneco charge points Fueltype: {connector_types} filter {filter} origin: {resolved_origin}")
        # header = {"Content-Type": "application/json","Accept": "application/json", "Origin": "https://www.eneco-emobility.com", "Referer": "https://www.eneco-emobility.com/be-nl/chargemap", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36", "X-Requested-With": "XMLHttpRequest"}
        # https://www.eneco-emobility.com/be-nl/chargemap#

        header = self.getEnecoHttpHeaders()
        
        all_stations = []
        all_ids = {}
        # radius = 0.0044
        locationInfoLat = float(str(origin_coordinates.get('lat')).replace(',','.'))
        locationInfoLon = float(str(origin_coordinates.get('lon')).replace(',','.'))
        
        _LOGGER.info(f"coordinates: {origin_coordinates}")
        boundingbox = origin_coordinates.get('bounds')
        if boundingbox == None or len(boundingbox) == 0:
            # boundingbox = self.convertLatLonBoundingBox(origin_coordinates.get('lat'), origin_coordinates.get('lon'))            
            radius = 1000
            boundingbox = self.create_boundingbox_array(origin_coordinates.get('lat'), origin_coordinates.get('lon'), _RADIUS)
            origin_coordinates['bounds'] = boundingbox
        _LOGGER.info(f"boundingbox: {boundingbox}, coordinates: {origin_coordinates}")

        # for boundingbox in origin_coordinates.get('bounds'):
        if boundingbox:
            # boundingbox = origin_coordinates.get('bounds')
            # _LOGGER.debug(f"Retrieving eneco data, boundingbox: {boundingbox}, radius: {radius}")

            # response = self.s.get('https://www.eneco-emobility.com/be-nl/chargemap', headers=header, timeout=50)
            # if response.status_code != 200:
            #     _LOGGER.error(f"ERROR: Eneco URL: {eneco_url}, {payload}, {response.text}")
            
            # min_lat={boundingbox[0]}&max_lat={boundingbox[2]}&min_long={boundingbox[1]}&max_long={boundingbox[3]}
            # payload = {"bounds":{"northWest":[boundingbox[2],boundingbox[1]],"northEast":[boundingbox[2],boundingbox[3]],"southEast":[boundingbox[0],boundingbox[3]],"southWest":[boundingbox[0],boundingbox[1]]},"filters":{"fastCharging":"false","ultraFastCharging":"false"},"zoomLevel":7}
            deault_payload = self.defaultEnecoPayload(origin_coordinates)
            totalEves = await self.countChargingStationsPayload(deault_payload)
            _LOGGER.info(f"Total Eneco EVs: {totalEves}")
            if totalEves > 0 and totalEves < 1000:
                eneco_url_polygon = "https://www.eneco-emobility.com/api/chargemap/search-polygon"
                payload = {
                    "bounds": deault_payload.get('bounds'),
                    "filters": {
                        "availableNow": False, 
                        "isAllowed": True, 
                        "speed": [11, 350], 
                        "connectorTypes": []},
                    "zoomLevel": 16
                }
                eneco_eves = await self.json_post_with_retry_client(eneco_url_polygon, payload, header)
                # if response_polygon.status_code != 200:
                    # _LOGGER.error(f"ERROR: Eneco URL: {eneco_url_polygon}, {payload}, {response_polygon.text}")
                # assert response_polygon.status_code == 200
                for eneco_eve in eneco_eves:
                    if eneco_eve.get('id') in all_ids:
                        continue
                    all_ids[eneco_eve.get('id')] = eneco_eve
                    evses = eneco_eve.get('evses',[])
                    station_lat = eneco_eve['lat'] = eneco_eve.get('coordinates',{}).get('lat')
                    station_lon = eneco_eve['lon'] = eneco_eve.get('coordinates',{}).get('lng')

                    distance = self.haversine_distance(float(str(station_lat).replace(',','.')), float(str(station_lon).replace(',','.')), locationInfoLat, locationInfoLon)
                    eneco_eve["distance"] = distance
                    eneco_eve["source"] = "Eneco"
                    getPrices = False
                    if getPrices:
                        for evse in evses:
                            evseId = evse.get('evseId')
                            if evseId in all_ids:
                                continue
                            evse_price_url = "https://www.eneco-emobility.com/api/chargemap/evse-pricing"
                            payload = {"evseId": evseId, "country": "be"}
                            eneco_prices = await self.json_post_with_retry_client(evse_price_url, payload, header)
                            if eneco_prices:
                                # _LOGGER.debug(f"Eneco prices: {eneco_prices}, distance: {distance}, {payload}")
                                evse['prices'] = eneco_prices
                                all_ids[evseId] = eneco_eve
                    station = EnecoChargingStation.model_validate(eneco_eve)
                all_stations.extend(station)
            radius = radius + 0.0045
        return all_stations

        # _LOGGER.debug(f"NL All station data retrieved: {all_stations}")

        # self.add_station_distance(all_stations, 'lat', 'lon', float(str(locationinfo.get('lat')).replace(',','.')), float(str(locationinfo.get('lon')).replace(',','.')))
        

        # stationdetails = []
        # for station in all_stations:

        #     station_block = {
        #         'id': station.get('id'),
        #         'name': station.get('naam'),
        #         'url': station.get('owner',{}).get('website',f'https://www.eneco-emobility.com/be-nl/chargemap#loc={station.get('coordinates',{}).get('lat')}%2C{station.get('coordinates',{}).get('lng')}%2C16&selected={station.get('id','')}'),
        #         'brand': f"{station.get('owner',{}).get('name')} (via Eneco)",
        #         'address': station.get('address',{}).get('streetAndHouseNumber',''),
        #         'postalcode': station.get('address',{}).get('postcode'),
        #         'locality': station.get('address',{}).get('city'),
        #         'price': 999 if len(station.get('eves',[])) == 0 or not station.get('eves',[])[0].get('prices') else station.get('eves',[])[0].get('prices',{}).get('chargingCosts'),
        #         'price1h': 999 if len(station.get('eves',[])) == 0 or not station.get('eves',[])[0].get('prices') else float(station.get('eves',[])[0].get('prices',{}).get('startTariff',0)) + float(station.get('eves',[])[0].get('prices',{}).get('chargingCosts')),
        #         # 'price_changed': block.get('fuelPrice').get('datum'),
        #         'lat': station.get('coordinates',{}).get('lat'),
        #         'lon': station.get('coordinates',{}).get('lng'),
        #         'connector_type': "TODO",
        #         'distance': station.get('distance'),
        #         # 'date': block.get('fuelPrice').get('datum'), 
        #         # 'country': country
        #         'facilities': ", ".join(station.get('facilities',[])),
        #     }
        #     stationdetails.append(station_block)
        # return stationdetails

    def convertLatLonBoundingBox(self, lat, lon):
        f_lat = float(lat)
        f_lon = float(lon)
        size = 0.002
        boundingbox = [f_lat-size, #0
                       f_lat+size, #1
                       f_lon-size, #2
                       f_lon+size] #3
        return boundingbox
    

    
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
        _LOGGER.info(f"coordinates: {coordinates}")
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
        
        _LOGGER.info(f"coordinates: {origin_coordinates}")
        boundingbox = origin_coordinates.get('bounds')
        if boundingbox == None or len(boundingbox) == 0:
            # boundingbox = self.convertLatLonBoundingBox(origin_coordinates.get('lat'), origin_coordinates.get('lon'))
            boundingbox = self.create_boundingbox_array(origin_coordinates.get('lat'), origin_coordinates.get('lon'), _RADIUS)
            origin_coordinates['bounds'] = boundingbox
        _LOGGER.info(f"boundingbox: {boundingbox}, coordinates: {origin_coordinates}")
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
                if response.status == 200:
                    result = await response.json()
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
                if response.status == 200:
                    result = await response.json()
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
