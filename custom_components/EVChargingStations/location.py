import json
import logging
import requests
import uuid
import re
import locale
import math
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import urllib.parse
from enum import Enum
import urllib3
from ratelimit import limits, sleep_and_retry
from typing import TypedDict

import voluptuous as vol

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"
_DATE_FORMAT = "%d/%m/%Y"

_COORD_MATCH = re.compile(
        r"^([-+]?)([\d]{1,2})(((\.)(\d+)(,)))(\s*)(([-+]?)([\d]{1,3})((\.)(\d+))?)$"
    )

def check_settings(config, hass):
    errors_found = False
    if not any(config.get(i) for i in ["country"]):
        _LOGGER.error("country was not set")
        errors_found = True
    
    if not any(config.get(i) for i in ["postalcode"]):
        _LOGGER.error("postalcode was not set")
        errors_found = True

    if errors_found:
        raise vol.Invalid("Missing settings to setup the sensor.")
    else:
        return True
        


class ConnectorTypes(Enum):
    ELECTRIC_T1 = "ET1",0,"","","",""
    ELECTRIC_T2 = "ET2",0,"","","",""
    ELECTRIC_DC = "EDC",0,"","","",""
    
    @property
    def name_lowercase(self):
        return self.name.lower()
    

class Coords(TypedDict):
    """Coordinates and bounds."""

    lat: float
    lon: float
    bounds: dict[str, float]

class LocationSession(object):
    def __init__(self, GEO_API_KEY=""):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        self.s.headers["Referer"] = "https://homeassistant.io"
        # self.API_KEY_GEOCODIFY = GEO_API_KEY
        # self.GEOCODIFY_BASE_URL = "https://api.geocodify.com/v2/"
        self.API_KEY_GEOAPIFY = GEO_API_KEY
        self.GEOAPIFY_BASE_URL = "https://api.geoapify.com/v1/geocode"
        
    # Country = country code: BE/FR/LU/DE/IT
    
        
    @sleep_and_retry
    @limits(calls=1, period=1)
    def convertLocationBoundingBox(self, postalcode, country, town):
        country_name = "Italy"
        if country.lower() == 'it':
            country_name = "Italy"
        if country.lower() == 'nl':
            country_name = "Netherlands"
        if country.lower() == 'es':
            country_name = "Spain"
        if country.lower() == 'us':
            country_name = "United States of America"
        if country.lower() == 'be':
            country_name = "Belgium"
        orig_location = self.searchGeocode(postalcode, town, country_name)
        _LOGGER.debug(f"searchGeocodeOSM({postalcode}, {town}, {country_name}): {orig_location}")
        if orig_location is None:
            return []
        orig_boundingbox = orig_location.get('boundingbox')
        boundingboxes = {"lat": orig_location.get('lat'), "lon": orig_location.get('lon'), "boundingbox": [orig_boundingbox, [float(orig_boundingbox[0])-0.045, float(orig_boundingbox[1])+0.045, float(orig_boundingbox[2])-0.045, float(orig_boundingbox[3])+0.045], [float(orig_boundingbox[0])-0.09, float(orig_boundingbox[1])+0.09, float(orig_boundingbox[2])-0.09, float(orig_boundingbox[3])+0.09]]}
        return boundingboxes
    
    
    def convertLatLonBoundingBox(self, lat, lon):
        f_lat = float(lat)
        f_lon = float(lon)
        boundingboxes = [[f_lat-0.020, f_lat+0.020,f_lon-0.020, f_lon+0.02], [f_lat-0.045, f_lat+0.045, f_lon-0.045, f_lon+0.045], [f_lat-0.09, f_lat+0.09, f_lon-0.09, f_lon+0.09]]
        return boundingboxes
    
        
    def ensure_coords(self, address: str) -> Coords:
        coords = None
        if self.already_coords(address):
            coords = self.coords_string_parser(address)
        else:
            coords = self.address_to_coords(address)
        return coords

    def already_coords(self, address: str) -> bool:
        """Already coordinates or address."""

        m = re.search(_COORD_MATCH, address)
        return m is not None

    def coords_string_parser(self, coords: str) -> Coords:
        """Parse the address string into coordinates to match address_to_coords return object."""

        lat, lon = coords.split(",")
        return {"lat": float(lat.strip()), "lon": float(lon.strip()), "bounds": [float(lat.strip())+0.045,  #0
                                                                                 float(lon.strip())-0.045,  #1
                                                                                 float(lat.strip())-0.045,  #2
                                                                                 float(lon.strip())+0.045]} #3

    def address_to_coords(self, address: str) -> Coords:
        """Convert address to coordinates."""
        orig_location = self.searchGeocode(address)
        _LOGGER.debug(f"searchGeocode({address}): {orig_location}")
        if orig_location is None:
            return {}
        orig_boundingbox = orig_location.get('boundingbox')
        # boundingboxes = {"lat": orig_location.get('lat'), "lon": orig_location.get('lon'), "bounds": [orig_boundingbox, [float(orig_boundingbox[0])-0.045, float(orig_boundingbox[1])+0.045, float(orig_boundingbox[2])-0.045, float(orig_boundingbox[3])+0.045], [float(orig_boundingbox[0])-0.09, float(orig_boundingbox[1])+0.09, float(orig_boundingbox[2])-0.09, float(orig_boundingbox[3])+0.09]]}
        boundingboxes = {"lat": orig_location.get('lat'), "lon": orig_location.get('lon'), "bounds": orig_boundingbox}
        return boundingboxes
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    # def getChargingStations(self, postalcode, country, town, locationinfo, fueltype: ConnectorTypes, single):
    def getChargingStations(self, resolved_origin, connector_types, filter):
        _LOGGER.info(f"Eneco charge points Fueltype: {connector_types} filter {filter} origin: {resolved_origin}")
        # header = {"Content-Type": "application/json","Accept": "application/json", "Origin": "https://www.eneco-emobility.com", "Referer": "https://www.eneco-emobility.com/be-nl/chargemap", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36", "X-Requested-With": "XMLHttpRequest"}
        # https://www.eneco-emobility.com/be-nl/chargemap#

        header = self.getEnecoHttpHeaders()
        
        all_stations = []
        all_ids = {}
        radius = 0.0044
        origin_coordinates = self.ensure_coords(resolved_origin)
        locationInfoLat = float(str(origin_coordinates.get('lat')).replace(',','.'))
        locationInfoLon = float(str(origin_coordinates.get('lon')).replace(',','.'))
        # for boundingbox in origin_coordinates.get('bounds'):
        if origin_coordinates.get('bounds'):
            boundingbox = origin_coordinates.get('bounds')
            #TODO check if needs to be retrieved 3 times 0, 5 & 10km or radius can be set to 0.09 to get all at once
            _LOGGER.debug(f"Retrieving eneco data, boundingbox: {boundingbox}, radius: {radius}")

            # response = self.s.get('https://www.eneco-emobility.com/be-nl/chargemap', headers=header, timeout=50)
            # if response.status_code != 200:
            #     _LOGGER.error(f"ERROR: Eneco URL: {eneco_url}, {payload}, {response.text}")
            
            # min_lat={boundingbox[0]}&max_lat={boundingbox[2]}&min_long={boundingbox[1]}&max_long={boundingbox[3]}
            # payload = {"bounds":{"northWest":[boundingbox[2],boundingbox[1]],"northEast":[boundingbox[2],boundingbox[3]],"southEast":[boundingbox[0],boundingbox[3]],"southWest":[boundingbox[0],boundingbox[1]]},"filters":{"fastCharging":"false","ultraFastCharging":"false"},"zoomLevel":7}
            deault_payload = self.defaultEnecoPayload(boundingbox)
            totalEves = self.countChargingStationsPayload(deault_payload)
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
                response_polygon = self.s.post(eneco_url_polygon,headers=header, json=payload,timeout=50)
                if response_polygon.status_code != 200:
                    _LOGGER.error(f"ERROR: Eneco URL: {eneco_url_polygon}, {payload}, {response_polygon.text}")
                assert response_polygon.status_code == 200
                eneco_eves = response_polygon.json()
                for eneco_eve in eneco_eves:
                    if eneco_eve.get('id') in all_ids:
                        continue
                    all_ids[eneco_eve.get('id')] = eneco_eve
                    evses = eneco_eve.get('evses',[])
                    station_lat = eneco_eve['lat'] = eneco_eve.get('coordinates',{}).get('lat')
                    station_lon = eneco_eve['lon'] = eneco_eve.get('coordinates',{}).get('lng')

                    distance = self.haversine_distance(float(str(station_lat).replace(',','.')), float(str(station_lon).replace(',','.')), locationInfoLat, locationInfoLon)
                    eneco_eve["distance"] = distance
                    for evse in evses:
                        evseId = evse.get('evseId')
                        if evseId in all_ids:
                            continue
                        evse_price_url = "https://www.eneco-emobility.com/api/chargemap/evse-pricing"
                        payload = {"evseId": evseId, "country": "be"}
                        response_price = self.s.post(evse_price_url,headers=header, json=payload,timeout=50)
                        if response_price.status_code != 200:
                            _LOGGER.error(f"ERROR: Eneco URL: {evse_price_url}, {payload}, {response_price.text}")
                        else:
                            eneco_prices = response_price.json()
                            if eneco_prices:
                                _LOGGER.debug(f"Eneco prices: {eneco_prices}, distance: {distance}, {payload}")
                                evse['prices'] = eneco_prices
                                all_ids[evseId] = eneco_eve

                all_stations.extend(eneco_eves)
            radius = radius + 0.0045


        # _LOGGER.debug(f"NL All station data retrieved: {all_stations}")

        # self.add_station_distance(all_stations, 'lat', 'lon', float(str(locationinfo.get('lat')).replace(',','.')), float(str(locationinfo.get('lon')).replace(',','.')))
        

        stationdetails = []
        for station in all_stations:

            station_block = {
                'id': station.get('id'),
                'name': station.get('naam'),
                'url': station.get('owner',{}).get('website',f'https://www.eneco-emobility.com/be-nl/chargemap#loc={station.get('coordinates',{}).get('lat')}%2C{station.get('coordinates',{}).get('lng')}%2C16&selected={station.get('id','')}'),
                'brand': f"{station.get('owner',{}).get('name')} (via Eneco)",
                'address': station.get('address',{}).get('streetAndHouseNumber',''),
                'postalcode': station.get('address',{}).get('postcode'),
                'locality': station.get('address',{}).get('city'),
                'price': 999 if len(station.get('eves',[])) == 0 or not station.get('eves',[])[0].get('prices') else station.get('eves',[])[0].get('prices',{}).get('chargingCosts'),
                'price1h': 999 if len(station.get('eves',[])) == 0 or not station.get('eves',[])[0].get('prices') else float(station.get('eves',[])[0].get('prices',{}).get('startTariff',0)) + float(station.get('eves',[])[0].get('prices',{}).get('chargingCosts')),
                # 'price_changed': block.get('fuelPrice').get('datum'),
                'lat': station.get('coordinates',{}).get('lat'),
                'lon': station.get('coordinates',{}).get('lng'),
                'connector_type': "TODO",
                'distance': station.get('distance'),
                # 'date': block.get('fuelPrice').get('datum'), 
                # 'country': country
                'facilities': ", ".join(station.get('facilities',[])),
            }
            stationdetails.append(station_block)
        return stationdetails, origin_coordinates

    def defaultEnecoPayload(self, boundingbox):
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

    def countChargingStations(self, resolved_origin):
        origin_coordinates = self.ensure_coords(resolved_origin)
        default_payload = self.defaultEnecoPayload(origin_coordinates)
        return self.countChargingStationsPayload(default_payload)
    
    def countChargingStationsPayload(self, payload):
        eneco_url = "https://www.eneco-emobility.com/api/chargemap/search-clusters"
        header = self.getEnecoHttpHeaders()
        response_clusters = self.s.post(eneco_url,headers=header, json=payload,timeout=50)
        if response_clusters.status_code != 200:
            _LOGGER.error(f"ERROR: Eneco URL: {eneco_url}, {payload}, {response_clusters.text}")
        assert response_clusters.status_code == 200

        totalEves = 0
        clusters = response_clusters.json()
        for cluster in clusters:
            totalEves += cluster.get("evseTotal",0)
        return totalEves



    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPrices(self, resolved_origin, connector_types: ConnectorTypes, single, filter=""):
        # _LOGGER.debug(f"getFuelPrices(self, {postalcode}, {country}, {town}, {locationinfo}, {fueltype}: FuelType, {single})")
        self.s = requests.Session()        
        if connector_types in (ConnectorTypes.ELECTRIC_T1, ConnectorTypes.ELECTRIC_T2, ConnectorTypes.ELECTRIC_DC):
            return self.getChargingStations(resolved_origin, ConnectorTypes.ELECTRIC_T2, filter)
        
        else:
            _LOGGER.info(f"Not supported connector type: {connector_types}")
            return []

    
    
    @sleep_and_retry
    @limits(calls=10, period=5)
    def getStationInfo(self, resolved_origin, connector_types: ConnectorTypes, single, filter=""):

        stationdetails, origin_coordinates = self.getFuelPrices(resolved_origin, connector_types, single, filter)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(stationdetails, connector_types, filter=filter)
    
    

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getStationInfoLatLon(self,latitude, longitude, fuel_type: ConnectorTypes, max_distance=0, filter=""):
        postal_code_country = self.reverseGeocode(longitude, latitude)
        town = None
        locationinfo = None
        if postal_code_country.get('country_code').lower() in ["be","fr","lu"]:        
            carbuLocationInfo = self.convertPostalCode(postal_code_country.get('postal_code'), postal_code_country.get('country_code'))
            if not carbuLocationInfo:
                raise Exception(f"Location not found country: {postal_code_country.get('country_code')}, postalcode: {postal_code_country.get('postal_code')}")
            town = carbuLocationInfo.get("n")
            city = carbuLocationInfo.get("pn")
            countryname = carbuLocationInfo.get("cn")
            locationinfo = carbuLocationInfo.get("id")
            _LOGGER.debug(f"convertPostalCode postalcode: {postal_code_country.get('postal_code')}, town: {town}, city: {city}, countryname: {countryname}, locationinfo: {locationinfo}")
        if postal_code_country.get('country_code').lower() in ["it","nl","es"]: 
            #TODO calc boudingboxes for known lat lon
            town = postal_code_country.get('town')
            itLocationInfo = self.convertLocationBoundingBox(postal_code_country.get('postal_code'), postal_code_country.get('country_code'), town)
            locationinfo = itLocationInfo
        price_info = self.getFuelPrices(postal_code_country.get('postal_code'), postal_code_country.get('country_code'), town, locationinfo, fuel_type, False)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(price_info, postal_code_country.get('postal_code'), fuel_type, max_distance, filter)
        

    def getStationInfoFromPriceInfo(self,price_info, connector_types: ConnectorTypes, max_distance=0, filter="", individual_station=""):
        # _LOGGER.debug(f"getStationInfoFromPriceInfo(self,{price_info}, {postalcode}, {fuel_type}: FuelType, {max_distance}=0, {filter}='', {individual_station}='')")
        data = {
            "price" : None,
            "distance" : 0,
            "region" : max_distance,
            "localPrice" : 0,
            "diff" : 0,
            "diff30" : 0,
            "diffPct" : 0,
            "supplier" : None,
            "supplier_brand" : None,
            "url" : None,
            "entity_picture" : None,
            "address" : None,
            "postalcode" : None,
            "postalcodes" : [postalcode],
            "city" : None,
            "latitude" : None,
            "longitude" : None,
            "fuelname" : None,
            "fueltype" : connector_types,
            "date" : None,
            "country": None,
            "id": None
        }
        # _LOGGER.debug(f"getStationInfoFromPriceInfo {fuel_type.name}, postalcode: {postalcode}, max_distance : {max_distance}, filter: {filter}, price_info: {price_info}")

        if price_info is None or len(price_info) == 0:
            return data
        
        filterSet = False
        if filter is not None and filter.strip() != "":
            filterSet = filter.strip().lower()



        for station in price_info:
            # _LOGGER.debug(f"getStationInfoFromPriceInfo station: {station} , {filterSet}, {individual_station}")
            if filterSet:
                match = re.search(filterSet, station.get("brand").lower())
                if not match:
                    continue
            if individual_station != "":
                # _LOGGER.debug(f"utils individual_station {individual_station}: {station.get('name')}, {station.get('address')}")
                if f"{station.get('name')}, {station.get('address')}" != individual_station:
                    # _LOGGER.debug(f"No match found for individual station, checking next")
                    continue
                
            # if max_distance == 0 and str(postalcode) not in station.get("address"):
            #     break
            try:
                currDistance = float(station.get("distance"))
                currPrice = float(station.get("price"))
            except ValueError:
                continue
            _LOGGER.debug(f"getStationInfoFromPriceInfo maxDistance: {max_distance}, currDistance: {currDistance}, postalcode: {station.get("postalcode")}, currPrice: {currPrice} new price: {data.get("price")}")
            
            data_recently_updated = True
            if station.get("date") is not None:
                try:
                    station_date = datetime.strptime(station.get("date"), "%d/%m/%y") #assuming the date is in the format dd/mm/yy
                    six_months_ago = datetime.now() - timedelta(days=180)  # 180 days = 6 months
                    if station_date >= six_months_ago:
                        data_recently_updated = True
                    else:
                        # The date is older than 6 months
                        data_recently_updated = False
                except:
                    _LOGGER.debug(f"date validation not possible since non matching date notation: {station.get("date")}")
            if station.get('country').lower() == 'it' and max_distance == 0:
                # IT results are not sorted by price, so don't expect the first to be the best match for local price
                max_distance = 0.1
            # _LOGGER.debug(f'if (({max_distance} == 0 and ({currDistance} <= 5 or {postalcode} == {station.get("postalcode")})) or {currDistance} <= {max_distance}) and ({data.get("price")} is None or {currPrice} < {float(data.get("price"))})')
            if ((max_distance == 0  and (currDistance <= 5 or postalcode == station.get("postalcode"))) or currDistance <= max_distance) and data_recently_updated and (data.get("price") is None or currPrice < float(data.get("price"))):
                data["distance"] = float(station.get("distance"))
                data["price"] = 0 if station.get("price") == '' else float(station.get("price"))
                data["localPrice"] = 0 if price_info[0].get("price") == '' else float(price_info[0].get("price"))
                data["diff"] = round(data["price"] - data["localPrice"],3)
                data["diff30"] = round(data["diff"] * 30,3)
                data["diffPct"] = 0 if data["price"] == 0 else round(100*((data["price"] - data["localPrice"])/data["price"]),3)
                data["supplier"]  = station.get("name")
                data["supplier_brand"]  = station.get("brand")
                data["url"]   = station.get("url")
                data["entity_picture"] = station.get("logo_url")
                data["address"] = station.get("address")
                data["postalcode"] = station.get("postalcode")
                data["city"] = station.get("locality")
                data["latitude"] = station.get("lat")
                data["longitude"] = station.get("lon")
                data["fuelname"] = station.get("fuelname")
                data["date"] = station.get("date")
                if data["postalcode"] not in data["postalcodes"]:
                    data["postalcodes"].append(data["postalcode"])
                data['country'] = station.get('country')
                data['id'] = station.get('id')
                # _LOGGER.debug(f"before break {max_distance}, country: {station.get('country') }, postalcode: {station.get('postalcode')} required postalcode {postalcode}")
                if max_distance == 0:
                        #if max distance is 0, we expect the first result to be the cheapest and no need to loop over the rest
                        # _LOGGER.debug(f"break {max_distance}, country: {station.get('country') }, postalcode: {station.get('postalcode')} required postalcode {postalcode}")
                        break
            # else:
                # _LOGGER.debug(f'no match found: if (({max_distance} == 0 and ({currDistance} <= 5 or {postalcode} == {station.get("postalcode")})) or {currDistance} <= {max_distance}) and ({data.get("price")} is None or {currPrice} < {float(data.get("price"))})')
        if data["supplier"] is None and filterSet:
            _LOGGER.warning(f"{postalcode} the station filter '{filter}' may result in no results found, if needed, please review filter")
        
        _LOGGER.debug(f"get_lowest_fuel_price info found: {data}")
        return data
        
    # NOT USED
    def geocodeHere(self, country, postalcode, here_api_key):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}
        country_fullname = ""
        if country == "BE":
            country_fullname = "Belgium"
        elif country == "FR":
            country_fullname = "France"
        elif country == "LU":
            country_fullname = "Luxembourg"
        else:
            raise Exception(f"Country {country} not supported, only BE/FR/LU is currently supported")
        
        response = self.s.get(f"https://geocode.search.hereapi.com/v1/geocode?q={postalcode}+{country_fullname}&apiKey={here_api_key}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        location = response.json()["items"][0]["position"]
        return location
    
    # NOT USED
    def getPriceOnRouteORS(self, country, fuel_type: ConnectorTypes, from_postalcode, to_postalcode, ors_api_key, filter = ""):
        from_location = self.geocodeORS(country, from_postalcode, ors_api_key)
        assert from_location is not None
        to_location = self.geocodeORS(country, to_postalcode, ors_api_key)
        assert to_location is not None
        route = self.getOrsRoute(from_location, to_location, ors_api_key)
        assert route is not None
        _LOGGER.debug(f"route: {route}, lenght: {len(route)}")

        processedPostalCodes = []
        
        bestPriceOnRoute = None
        bestStationOnRoute = None

        for i in range(1, len(route), 20):
            _LOGGER.debug(f"point: {route[i]}")
            postal_code = self.reverseGeocodeORS({"latitude":route[i][1], "longitude": route[i][0]}, ors_api_key)
            if postal_code is not None and postal_code not in processedPostalCodes:
                bestAroundPostalCode = self.getStationInfo(postal_code, country, fuel_type, '', 3, filter)
                processedPostalCodes.append(bestAroundPostalCode.get('postalcodes'))                    
                if bestPriceOnRoute is None or bestAroundPostalCode.get('price') < bestPriceOnRoute:
                    bestStationOnRoute = bestAroundPostalCode

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route info found: {processedPostalCodes}")
        return bestStationOnRoute


    #USED BY Service: handle_get_lowest_fuel_price_on_route
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getPriceOnRoute(self, country, fuel_type: ConnectorTypes, from_postalcode, to_postalcode, to_country = "", filter = ""):
        from_location = self.geocode(country, from_postalcode)
        assert from_location is not None
        if to_country == "":
            to_country = country
        to_location = self.geocode(to_country, to_postalcode)
        assert to_location is not None
        return self.getPriceOnRouteLatLon(fuel_type, from_location[1], from_location[0], to_location[1], to_location[0], filter)

    
    #USED BY Service: handle_get_lowest_fuel_price_on_route_coor
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getPriceOnRouteLatLon(self, fuel_type: ConnectorTypes, from_latitude, from_longitude, to_latitude, to_longitude, filter = ""):
        from_location = (from_latitude, from_longitude)
        assert from_location is not None
        to_location = (to_latitude, to_longitude)
        assert to_location is not None
        route = self.getOSMRoute(from_location, to_location)
        assert route is not None
        _LOGGER.debug(f"route lenght: {len(route)}, from_location {from_location}, to_location {to_location}, route: {route}")

        # Calculate the number of elements to process (30% of the total)
        elements_to_process = round((30 / 100) * len(route))
        # Calculate the step size to evenly spread the elements
        step_size = len(route) // elements_to_process

        if len(route) < 8:
            step_size = 1

        processedPostalCodes = []
        
        bestPriceOnRoute = None
        bestStationOnRoute = None

        for i in range(0, len(route), step_size):
            _LOGGER.debug(f"point: {route[i]}, step_size {step_size} of len(route): {len(route)}")
            postal_code_country = self.reverseGeocode(route[i]['maneuver']['location'][0], route[i]['maneuver']['location'][1])
            if postal_code_country.get('postal_code') is not None and postal_code_country.get('postal_code') not in processedPostalCodes:
                _LOGGER.debug(f"Get route postalcode {postal_code_country.get('postal_code')}, processedPostalCodes {processedPostalCodes}")
                bestAroundPostalCode = None
                try:
                    bestAroundPostalCode = self.getStationInfo(postal_code_country.get('postal_code'), postal_code_country.get('country_code'), fuel_type, postal_code_country.get('town'), 3, filter, False)
                except Exception as e:
                    _LOGGER.error(f"ERROR: getStationInfo failed : {e}")
                if bestAroundPostalCode is None:
                    continue
                processedPostalCodes.extend(bestAroundPostalCode.get('postalcodes'))                    
                if (bestPriceOnRoute is None) or (bestAroundPostalCode.get('price') is not None and bestAroundPostalCode.get('price',999) < bestPriceOnRoute):
                    bestStationOnRoute = bestAroundPostalCode
                    bestPriceOnRoute = bestAroundPostalCode.get('price',999)
            else:
                _LOGGER.debug(f"skipped route postalcode {postal_code_country.get('postal_code')}, processedPostalCodes {processedPostalCodes}")

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route info found: {processedPostalCodes}")
        return bestStationOnRoute
    
    # set the maximum number of requests per minute
    @sleep_and_retry
    @limits(calls=1, period=1)
    def make_api_request(self, url,headers="",timeout=30):
        response = self.s.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
            return response
        else:
            return response
    
    # NOT USED
    @sleep_and_retry
    @limits(calls=100, period=60)
    def geocodeORS(self, country_code, postalcode, ors_api_key):
        _LOGGER.debug(f"geocodeORS request: country_code: {country_code}, postalcode: {postalcode}, ors_api_key: {ors_api_key}")
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}
        
        response = self.make_api_request(f"https://api.openrouteservice.org/geocode/search?api_key={ors_api_key}&text={postalcode}&boundary.country={country_code}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        else:
            _LOGGER.debug(f"geocodeORS response: {response.text}")
        assert response.status_code == 200
        # parse the response as JSON
        response_json = json.loads(response.text)
        # extract the latitude and longitude coordinates from the response
        if response_json.get('features') and len(response_json.get('features')) > 0:
            coordinates = response_json['features'][0]['geometry']['coordinates']
            location = { 
                "latitude" : coordinates[1],
                "longitude" : coordinates[0]
                }
            return location
        else:
            _LOGGER.debug(f"geocodeORS response no features found: {response_json}")
            return
    
    # USED by services on route
    @sleep_and_retry
    @limits(calls=1, period=1)
    def geocode(self, country_code, postal_code):
        _LOGGER.debug(f"geocode request: country_code: {country_code}, postalcode: {postal_code}")
        try:
            # header = {"Content-Type": "application/x-www-form-urlencoded"}
            # header = {"Accept-Language": "nl-BE"}
            address = f"{postal_code}, {country_code}"

            if self.API_KEY_GEOAPIFY in ["","GEO_API_KEY"]:
                raise Exception("Geocode failed: GEO_API_KEY not set!")
            # GEOCODIFY
        #     response = self.s.get(f"{self.GEOCODIFY_BASE_URL}geocode?api_key={self.API_KEY_GEOCODIFY}&q={address}")
        #     response = response.json()
        #     status = response.get('meta').get('code')
        #     if response and status == 200:
        #         # print(response)
        #         location = response.get('response').get('features')[0].get('geometry').get('coordinates') # extract the latitude and longitude coordinates from the response
        #         _LOGGER.debug(f"geocode lat: {location[1]}, lon {location[0]}")
        #         return location
        #     else:
        #         _LOGGER.error(f"ERROR: {location}, country_code: {country_code}, postalcode: {postal_code}")
        #         return None
        # except:
        #     _LOGGER.error(f"ERROR: {response.text}")
        #     return None

            response = self.s.get(f"{self.GEOAPIFY_BASE_URL}/search?text={address}&api_key={self.API_KEY_GEOAPIFY}&format=json")

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract the first result's coordinates
                if data['results'] and len(data['results']) > 0:
                    location = [data['results'][0]['lon'],data['results'][0]['lat']] # extract the latitude and longitude coordinates from the response
                    _LOGGER.debug(f"geocode lat: {location[1]}, lon {location[0]}")
                    return location
                else:
                    return None
            else:
                return None, f"Error searching: {address}: {response.status_code}: {response.text}"
        except Exception as e:
            _LOGGER.error(f"ERROR: geocode : {e}")
            return None
        
    
     
    # NOT USED by services on route
    @sleep_and_retry
    @limits(calls=1, period=1)
    def geocodeOSMNominatim(self, country_code, postal_code):
        _LOGGER.debug(f"geocodeOSM request: country_code: {country_code}, postalcode: {postal_code}")
        # header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}

        geocode_url = 'https://nominatim.openstreetmap.org/search'
        params = {'format': 'json', 'postalcode': postal_code, 'country': country_code, 'limit': 1}
        response = self.s.get(geocode_url, params=params)
        geocode_data = response.json()
        if geocode_data:
            location = (geocode_data[0]['lat'], geocode_data[0]['lon'])
            _LOGGER.debug(f"geocodeOSM lat: {location[0]}, lon {location[1]}")
            return location
        else:
            _LOGGER.error(f"ERROR: {response.text}")
            return None       
    
    # NOT USED
    @sleep_and_retry
    @limits(calls=100, period=60)
    def reverseGeocodeORS(self, location, ors_api_key):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}
        
        response = self.make_api_request(f"https://api.openrouteservice.org/geocode/reverse?api_key={ors_api_key}&point.lat={location.get('latitude')}&point.lon={location.get('longitude')}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        # parse the response as JSON
        response_json = json.loads(response.text)
        if response_json['features'][0]['properties'].get('postalcode'):
            return response_json['features'][0]['properties']['postalcode']
        else:
            return
    
    #USED for different countries to create a bounding box
    @sleep_and_retry
    @limits(calls=1, period=2)
    # def searchGeocode(self, postalcode, city, country):
        # address = f"{postalcode}, {city}, {country}}"
    def searchGeocode(self, address):
        try:
            # GEOCODIFY
            # response = self.s.get(f"{self.GEOCODIFY_BASE_URL}geocode?api_key={self.API_KEY_GEOCODIFY}&q={address}")
            
            # response = response.json()
            # status = response.get('meta').get('code')
            # if response and status == 200:
            #     # print(response)
            #     location = response.get('response').get('features')[0].get('geometry').get('coordinates') # extract the latitude and longitude coordinates from the response
            #     _LOGGER.debug(f"geocode lat: {location[1]}, lon {location[0]}")
            #     bbox = response.get('response').get('bbox')
            #     return {"lat": location[1], "lon": location[0], "boundingbox": [bbox[1],bbox[0],bbox[3],bbox[2]]}


            if self.API_KEY_GEOAPIFY in ["","GEO_API_KEY"]:
                raise Exception("Geocode failed: GEO_API_KEY not set!")
            # GEOAPIFY
            response = self.s.get(f"{self.GEOAPIFY_BASE_URL}/search?text={address}&api_key={self.API_KEY_GEOAPIFY}&format=json")

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract the first result's coordinates
                if data['results'] and len(data['results']) > 0:
                    location = [data['results'][0]['lon'],data['results'][0]['lat']] # extract the latitude and longitude coordinates from the response
                    bbox = data['results'][0]['bbox']
                    return {"lat": location[1], "lon": location[0], "boundingbox": [bbox['lat1'],bbox['lon1'],bbox['lat2'],bbox['lon2']]}
                else:
                    return None
            else:
                return None, f"Error searching: {address}: {response.status_code}: {response.text}"
        except Exception as e:
            _LOGGER.error(f"ERROR: searchGeocode : {e}")
    
    #NOT USED for different countries to create a bounding box
    @sleep_and_retry
    @limits(calls=1, period=2)
    def searchGeocodeOSMNominatim(self, postalcode, city, country):

        # https://nominatim.openstreetmap.org/search?postalcode=1212VG&city=Hilversum&country=Netherlands&format=json
        # [{"place_id":351015506,"licence":"Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright","osm_type":"relation","osm_id":271108,"boundingbox":["52.1776807","52.2855452","5.1020133","5.2189603"],"lat":"52.2241375","lon":"5.1719396","display_name":"Hilversum, North Holland, Netherlands","class":"boundary","type":"administrative","importance":0.7750020206490176,"icon":"https://nominatim.openstreetmap.org/ui/mapicons/poi_boundary_administrative.p.20.png"},{"place_id":351015507,"licence":"Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright","osm_type":"relation","osm_id":419190,"boundingbox":["52.1776807","52.2855452","5.1020133","5.2189603"],"lat":"52.23158695","lon":"5.173493524521531","display_name":"Hilversum, North Holland, Netherlands","class":"boundary","type":"administrative","importance":0.7750020206490176,"icon":"https://nominatim.openstreetmap.org/ui/mapicons/poi_boundary_administrative.p.20.png"}]
        nominatim_url = f"https://nominatim.openstreetmap.org/search?postalcode={postalcode}&city={city}&country={country}&format=json"
        nominatim_response = self.s.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        # _LOGGER.debug(f"nominatim_data {nominatim_data}")
        location = []
        if len(nominatim_data) > 0:
            location = nominatim_data[0]
            # lat = location.get('lat')
            # lon = location.get('lon')
            # boundingbox = location.get('boundingbox')
            # min_lat = boundingbox[0]
            # max_lat = boundingbox[1]
            # min_lon = boundingbox[2]
            # max_lon = boundingbox[3]
            return location
    
    # NOT USED for converting lat lon to postal code
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocodeOSMNominatim(self, longitude, latitude):
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        nominatim_response = self.s.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        # _LOGGER.debug(f"nominatim_data {nominatim_data}")

        # Extract the postal code from the Nominatim response
        postal_code = nominatim_data['address'].get('postcode', None)
        country_code = nominatim_data['address'].get('country_code', None)
        town = nominatim_data['address'].get('town', None)
        address = nominatim_data['address']
        # _LOGGER.debug(f"nominatim_data postal_code {postal_code}, country_code {country_code}, town {town}")

        return (postal_code, country_code, town, address)
    
    # USED for converting lat lon to postal code
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocode(self, longitude, latitude):
        try:
            # GECODIFY
            # response = self.s.get(f"{self.GEOCODIFY_BASE_URL}reverse?api_key={self.API_KEY_GEOCODIFY}&lat={latitude}&lng={longitude}")
            
            # response = response.json()
            # status = response.get('meta').get('code')
            # if response and status == 200:
            #     # print(response)

            #     # Extract the postal code from the response
            #     extracted_response = {
            #         "postal_code": response.get('response').get('features')[0].get('properties').get('postalcode'),
            #         "country_code": response.get('response').get('features')[0].get('properties').get('country_code'),
            #         "town": response.get('response').get('features')[0].get('properties').get('locality'),
            #         "address": f"{response.get('response').get('features')[0].get('properties').get('street')} {response.get('response').get('features')[0].get('properties').get('housenumber')}, {response.get('response').get('features')[0].get('properties').get('postalcode')} {response.get('response').get('features')[0].get('properties').get('locality')}, {response.get('response').get('features')[0].get('properties').get('country')}",
            #         "region": response.get('response').get('features')[0].get('properties').get('region')
            #     }
            #     _LOGGER.debug(f"geodata extracted_response {extracted_response}")

            #     return extracted_response

            # GEOAPIFY
            
            response = self.s.get(f"{self.GEOAPIFY_BASE_URL}/reverse?lat={latitude}&lon={longitude}&api_key={self.API_KEY_GEOAPIFY}&format=json")

            _LOGGER.debug(f"reverseGeocode geodata response {response}, {self.GEOAPIFY_BASE_URL}/reverse?lat={latitude}&lon={longitude}&api_key={self.API_KEY_GEOAPIFY}&format=json")
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract the first result's coordinates
                if data['results'] and len(data['results']) > 0:
                    # Extract the postal code from the response
                    extracted_response = {
                        "postal_code": data['results'][0].get('postcode',''),
                        "country_code": data['results'][0].get('country_code',''),
                        "town": data['results'][0].get('city',''),
                        "address": data['results'][0].get('formatted',''),
                        "region": data['results'][0].get('state','')
                    }
                    return extracted_response
                else:
                    return None
        except Exception as e:
            _LOGGER.error(f"ERROR: reverseGeocode: {e}")


    # NOT USED for converting lat lon to postal code
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocodeNominatim(self, longitude, latitude):
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        nominatim_response = self.s.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        # _LOGGER.debug(f"nominatim_data {nominatim_data}")

        # Extract the postal code from the Nominatim response
        postal_code = nominatim_data['address'].get('postcode', None)
        country_code = nominatim_data['address'].get('country_code', None)
        town = nominatim_data['address'].get('town', None)
        address = nominatim_data['address']
        # _LOGGER.debug(f"nominatim_data postal_code {postal_code}, country_code {country_code}, town {town}")

        return (postal_code, country_code, town, address)

    # NOT USED
    @sleep_and_retry
    @limits(calls=1, period=15)
    def getOrsRoute(self, from_location, to_location, ors_api_key):

        header = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': ors_api_key,
            'Content-Type': 'application/json; charset=utf-8'
        }
        # # header = {"Accept-Language": "nl-BE"}
        # # set the minimum distance between locations in meters
        # min_distance = 10000

        # # set the radius around each waypoint
        # radius = min_distance / 2

        # # set the parameters for the OpenRouteService routing API
        # params = {
        #     "coordinates": [[from_location.get('longitude'),from_location.get('latitude')],[to_location.get('longitude'),to_location.get('latitude')]],
        #     "radiuses": [5000]
        # }
        # url = "https://api.openrouteservice.org/v2/directions/driving-car/json"
        # response = self.s.post(url, json=params, headers=header, timeout=30)
        response = self.make_api_request(f"https://api.openrouteservice.org/v2/directions/driving-car?api_key={ors_api_key}&start={from_location.get('longitude')},{from_location.get('latitude')}&end={to_location.get('longitude')},{to_location.get('latitude')}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        response_json = json.loads(response.text)
        
        # Extract the geometry (i.e. the points along the route) from the response
        geometry = response_json["features"][0]["geometry"]["coordinates"]
        return geometry

    #  USED by services on route 
    @sleep_and_retry
    @limits(calls=1, period=15)
    def getOSMRoute(self, from_location, to_location):

        #location expected (lat, lon)

        # Request the route from OpenStreetMap API
        # 'https://router.project-osrm.org/route/v1/driving/<from_lon>,<from_lat>;<to_lon>,<to_lat>?steps=true
        
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        url = f'https://router.project-osrm.org/route/v1/driving/{from_location[1]},{from_location[0]};{to_location[1]},{to_location[0]}?steps=true'
        _LOGGER.debug(f"getOSMRoute: {url}")
        response = self.s.get(url,headers=header, timeout=30)
        route_data = response.json()
        _LOGGER.debug(f"route_data {route_data}")


        if route_data.get('routes') is None:
            _LOGGER.error(f"ERROR: route not found: {route_data}")
            return
        # Extract the waypoints (towns) along the route
        waypoints = route_data['routes'][0]['legs'][0]['steps']
        
        _LOGGER.debug(f"waypoints {waypoints}")
        return waypoints

    #  NOT USED by services on route 
    @sleep_and_retry
    @limits(calls=1, period=15)
    def getRoute(self, from_location, to_location):

        #location expected (lat (50.XX), lon (4.XX))

        # Request the route from GeoApify.com API
        
        # 'https://router.project-osrm.org/route/v1/driving/<from_lon>,<from_lat>;<to_lon>,<to_lat>?steps=true
        url = f'https://router.project-osrm.org/route/v1/driving/{from_location[1]},{from_location[0]};{to_location[1]},{to_location[0]}?steps=true'
        url = f"https://api.geoapify.com/v1/routing?waypoints={from_location[0]},{from_location[1]}|{to_location[0]},{to_location[1]}&mode=drive&apiKey={self.API_KEY_GEOAPIFY}"
        #NOT WORKING: steps contain no coordinates
        response = self.s.get(url)
        route_data = response.json()
        _LOGGER.debug(f"route_data {route_data}")
        
        # Extract the waypoints (towns) along the route
        waypoints = route_data['routes'][0]['legs'][0]['steps']
        
        _LOGGER.debug(f"waypoints {waypoints}")
        return waypoints    


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

    def add_station_distance(self, stations, stationLatName, stationLonName, lat, lon):
        for station in stations:
            latitude = str(self.get_nested_element(station, stationLatName))
            longitude = str(self.get_nested_element(station, stationLonName))
            distance = self.haversine_distance(float(str(latitude).replace(',','.')), float(str(longitude).replace(',','.')), lat, lon)
            station["distance"] = distance
    def get_nested_element(self, json_obj, key_string):
        keys = key_string.split('.')
        nested_value = json_obj
        try:
            for key in keys:
                nested_value = nested_value[key]
            return nested_value
        except (KeyError, TypeError):
            return None
    

#manual tests - enable debug logging

# _LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)
# if not logging.getLogger().hasHandlers():
#     logging.basicConfig(level=logging.DEBUG)
# _LOGGER.debug("Debug logging is now enabled.")

# session = ComponentSession("GEO_API_KEY")

#LOCAL TESTS

# session.geocode("BE", "1000")

#  test route
# print(session.getPriceOnRoute("BE", FuelType.DIESEL, 1000, 2000))


# test nl official
#print(session.getFuelOfficial(FuelType.DIESEL_OFFICIAL_B7, "NL"))
# session.getFuelOfficial(FuelType.DIESEL_OFFICIAL_B7, "NL")
# session.getFuelOfficial(FuelType.ELECTRIC_T2, "NL")

#test US
# ZIP Code 10001 - New York, New York
# ZIP Code 90210 - Beverly Hills, California
# ZIP Code 60611 - Chicago, Illinois
# ZIP Code 02110 - Boston, Massachusetts
# ZIP Code 33109 - Miami Beach, Florida

# locationinfo= session.convertLocationBoundingBox("90210", "US", "Beverly Hills")
# print(session.getFuelPrices("90210", "US", "Beverly Hills", locationinfo, FuelType.DIESEL, False))


#test SP


# locationinfo= session.convertLocationBoundingBox("28500", "ES", "Madrid")
# print(session.getFuelPrices("28500", "ES", "Madrid", locationinfo, FuelType.DIESEL, False))

# #test BE
# locationinfo= session.convertPostalCode("3300", "BE", "Bost")
# print(session.getOilPrice(locationinfo.get("id"), 1000, FuelType.OILSTD.code))
# locationinfo= session.convertPostalCode("3300", "BE", "Bost")
# print(session.getFuelPrices("3300", "BE", "Bost", locationinfo.get("id"), FuelType.LPG, False))
# #test2
# locationinfo= session.convertPostalCode("8380", "BE", "Brugge")
# if locationinfo:
#     print(session.getFuelPrices("8380", "BE", "Brugge", locationinfo.get("id"), FuelType.SUPER95, False))
# #test3
# locationinfo= session.convertPostalCode("31830", "FR")
# if locationinfo:
#     # print(session.getFuelPrices("31830", "FR", "Plaisance-du-Touch", locationinfo.get("id"), FuelType.SUPER95, True))
#     print(session.getStationInfo("31830", "FR", FuelType.SUPER95, "Plaisance-du-Touch", 0, "", True))
# test IT
# locationinfo= session.convertLocationBoundingBox("07021", "IT", "Arzachena")
# print(session.getFuelPrices("07021", "IT", "Arzachena", locationinfo, FuelType.SUPER95, False))
#locationinfo= session.convertLocationBoundingBox("09040", "IT", "Settimo San Pietro")
#print(session.getFuelPrices("09040", "IT", "Settimo San Pietro", locationinfo, FuelType.SUPER95, False))
# test NL
# locationinfo= session.convertLocationBoundingBox("2627AR", "NL", "Delft")
# if len(locationinfo) > 0: 
#     print(session.getFuelPrices("2627AR", "NL", "Delft", locationinfo, FuelType.ELECTRIC_T2, False))
    # print(session.getFuelPrices("2627AR", "NL", "Delft", locationinfo, FuelType.DIESEL, False))
    # print(session.getStationInfo("2627AR", "NL", FuelType.DIESEL, "Delft", 0, "", False))
            
# print(FuelType.DIESEL.code)
# print(FuelType.SUPER95_PREDICTION.code)
# print("FuelType.DIESEL_OFFICIAL_B10")
# print(session.getFuelOfficial(FuelType.DIESEL_OFFICIAL_B10, "NL"))
# print("FuelType.SUPER95_OFFICIAL_E10")
# print(session.getFuelOfficial(FuelType.SUPER95_OFFICIAL_E10, "NL"))

# print(FuelType.DIESEL.code)
