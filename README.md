[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/release/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/EVChargingStations.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/graphs/commit-activity)

# Public EV Charging Stations Home Assistant integration
Home Assistant custom component to create sensors with information on the available EV Charging Station in a chosen area. This custom component has been built from the ground up to bring public site data to compare and save on your EV prices and integrate this information into Home Assistant. This integration is built against the public websites provided by Eneco.com and other similar sites. Sensors will be created for nearest stations of different speeds and availability. 

**Currently supporting charging stations in from [Eneco](https://www.eneco-emobility.com/be-nl/chargemap) and [Shell](https://ui-map.shellrecharge.com/).**

This integration is in no way affiliated with Eneco.com. This integration is based on my other [Carbu.com](https://github.com/myTselection/Carbu_com) custom integration, which brings similar functionality for fuel/gas stations.

Large parts of the code base has been based on the [Shell Recharge](https://github.com/cyberjunky/home-assistant-shell_recharge) custom integration. The same functionality is available, but has been extended to support Eneco charging stations and to automatically find the stations that matches criteria.

| :warning: Please don't report issues with this integration to other platforms, they will not be able to support you. |
| ---------------------------------------------------------------------------------------------------------------------|


For electricity price expectations [this Entso-E HACS integration](https://github.com/JaccoR/hass-entso-e) can be used.


<p align="center"><img src="https://raw.githubusercontent.com/myTselection/EVChargingStations/master/logo.png"/></p>

With this integration it will be possible to:
- subscribe to specific charging point, to make it possible to get notified once available
- get sensors (can be shown on map) with:
   - charging station **nearest** to location
   - **available** charging station **nearest** to location
   - **high** speed charging station **nearest** to location
   - **high** speed **available** charging station **nearest** to location
   - **super high** speed charging station **nearest** to location
   - **super high** speed **available** charging station **nearest** to

Optional also:
   - **cheapest** charging stations and nearest to location
   - **available** **cheapest** charging stations and nearest to location
   - **high** speed charging station **cheapest** and nearest to location
   - **high** speed **available** **cheapest** charging stations and nearest to location
   - **super high** speed **cheapest** charging station and nearest to location
   - **super high** speed **available** **cheapest** charging station and nearest to location



## Installation
- [HACS](https://hacs.xyz/): search for Carbu in the default HACS repo list or use below button to navigate directly to it on your local system and install via HACS. 
   -    [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myTselection&repository=EVChargingStations&category=integration)
- Restart Home Assistant
- Add 'EV Charging Stations' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Choose the type of charging station to setup: nearest public station, specific station or Shell station with credentials.
- For 'Public nearest station':
   - Provid any 'origin': this can be a coordinate eg: "51.330436, 3.802043" or "street, city, country" or any sensor name which has latitude and longitutde coordinate attributes eg "person.fred" or "device_tracker.car_position"
- TODO: After setting up the integration, the configuration can be updated using the 'Configure' button of the integration. The usage of a station filter can be enabled and set, the usage of a template to set the 'friendly name' of each sensor type can be enabled and set and the usage of icons with price indication can be enabled or disabled.
  - The checkboxes are required since else clearing the text of the configuration was not recorded (HA bug?) and filter or templates could no longer be removed once set.
  - When setting a sensor 'friendly name' template, any sensor attribute can be used as a placeholder which will be replaced with the actual value. Eg: `Price {fueltype} {fuelname} {supplier}` could be used as a template for the Price sensor. All available attributes can be fetched using the 'Developer Tools' > 'States' > 'Attributes' view in HA or using the tables listed below.



### Setup screenshot

![Carbu com setup config](https://github.com/myTselection/EVChargingStations/blob/ac496efdba41d4efd64aac7c46395df0f7722121/setup.png) 





## Integration

### Sensors
- <code>sensor.nearest_station_[origin]</code>: sensor with info of nearest charging station
- <code>sensor.nearest_available_station_[origin]</code>: sensor with info of nearest available charging station
- <code>sensor.nearest_highspeed_station_[origin]</code>: sensor with info of nearest highspeed charging station (+50kWh)
- <code>sensor.nearest_available_highspeed_station_[origin]</code>: sensor with info of nearest available highspeed charging station (+50kWh)
- <code>sensor.nearest_available_superhighspeed_station_[origin]</code>: sensor with info of nearest superhighspeed charging station (+100kWh)
- <code>sensor.nearest_available_superhighspeed_station_[origin]</code>: sensor with info of nearest available superhighspeed charging station (+100kWh)
- <details><summary>Sensor attributes</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | **Status** |
    | `name`    | Name of the charging station, ofter referring to the location |
    | `type`    | Type of the charging station, eg nearest_available_superhighspeed_station |
    | `address`  | Address of the charging station |
    | `postal_code`  | Postal code of the charging station |
    | `city`  | City of the charging station |
    | `country`  | Country of the charging station |
    | `latitude`  | Latitude of the charging station |
    | `longitude`  | Longitude of the charging station |
    | `distance`  | Approximate distance between charging station and set `origin` |
    | `operator_name`  | Name of the operator of the charging station |
    | `url`  | Direct URL to the Eneco chargemap with details of the charging station |
    | `facilities`  | Facilities available close to the charging station |
    | `avaialbe_connectors`  | Total number of connectors available at the charging station |
    | `number_of_connectors`  | Total number of connectors at the charging station |
    | `max_speed_kWh`  | Max speed connector at the charging station |
    | `min_speed_kWh`  | Min speed connector at the charging station |
    | `is_unlimited`  | Indication if any limitation applies at the charging station |
    | `is_limited`  | Indication if any limitation applies at the charging station |
    | `is_unkown`  | Indication if the charging station is unknown |
    | `allowed`  | Indication if the charging station is allowed for Eneco charging card holders |
    | `external_id`  | External unique technical id of the charging station |
    | `evse_id`  | Functional id of the charging station |
    | `status`  | Status indication of the charging station, any of "AVAILABLE", "CHARGING", "OUTOFORDER", "UNAVAILABLE", "UNKNOWN", "BLOCKED" |
    | `last update `   | Timestamp of latest status info of charging station |
    | `physical_reference`  | Physical reference id of the charging station |
    | `connector_standard`  | Connector standard info of the charging station, eg IEC_62196_T2 |
    | `connector_type`  | Connector power type info of the charging station, eg AC_3_PHASE |
    | `connector_format`  | Connector info of the charging station |
    | `connector_max_power`  | Connector info max power in kWh of the charging station, eg 17kWh|
    | `opentwentyfourseven`  | Indication if the charging station is open 24/7, true or false|
    | `charging_costs`  | Price charging cost info of the charging station per Watt of charging or false |
    | `charging_time_costs`  | Price charging cost info of the charging station per minute of charging or false |
    | `start_tariff`  | Price charging cost info of the charging station to start charging session or false |
    | `parking_time_costs`  | Price charging cost info of the charging station for parking during charging or false |
    | `price_description`  | Price charging cost info of the charging station |
    
    </details>
    

## Show map

### Nearest map

To show a map in Home Assistant with all nearest charging stations you can use a setup such as shown below. It will show the max kWh charging power on map.

   ```
   type: map
   entities:
     - entity: sensor.nearest_station_device_tracker_car_position
       label_mode: attribute
       attribute: connector_max_power
       focus: false
     - entity: >-
         sensor.nearest_available_station_device_tracker_car_position
       label_mode: attribute
       attribute: connector_max_power
       focus: true
     - entity: >-
         sensor.nearest_highspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: connector_max_power
       focus: false
     - entity: >-
         sensor.nearest_available_highspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: connector_max_power
       focus: true
     - entity: >-
         sensor.nearest_superhighspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: connector_max_power
       focus: false
     - entity: >-
         sensor.nearest_available_superhighspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: connector_max_power
       focus: true
     - entity: device_tracker.car_position
   theme_mode: auto

   ```

### Eneco map

To show the [Eneco charging map](https://www.eneco-emobility.com/be-nl/chargemap) for a specific location linked to some sensor in Home Assistant IFrame you can:
- install [Config Template Card HACS](https://github.com/iantrich/config-template-card)
- define a template sensor to dynamically build the website url based on sensor coordinates
   - in `configuration.yaml`
   ```
   template:
     - sensor:
      - name: "Car Eneco Charging Station URL"
        state: >
          https://www.eneco-emobility.com/be-nl/chargemap#loc={{ state_attr('device_tracker.car_position', 'latitude') }}%2C{{ state_attr('device_tracker.car_position', 'longitude') }}%2C16

   ```
   
- create a new card in frontend with config such as shown below:
     
   ```
   type: custom:config-template-card
   entities:
     - sensor.car_eneco_charging_station_url
   variables:
     - states
   card:
     type: iframe
     aspect_ratio: 50%
     url: ${states['sensor.car_eneco_charging_station_url'].state}

   ```



# TODO, UNDER CONSTRUCTION
### Services / Actions
A **service `EVChargingStations.get_lowest_fuel_price`** to get the lowest fuel price in the area of a postalcode is available. For a given fuel type and a distance in km, the lowest fuel price will be fetched and an event will be triggered with all the details found. Similar, the service **`EVChargingStations.get_lowest_fuel_price_coor`** can be called providing latitude and longitude coordinates instead of country, postalcode and town.

- <details><summary>Event data returned, event name: <code>EVChargingStations_lowest_fuel_price</code> /  <code>EVChargingStations_lowest_fuel_price_coor</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | `supplier`  | Name of the supplier of the fuel |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier Not supported for DE |
    | `longitude`  | Longitude of the supplier Not supported for DE |
    | `region`  | Distand 5km or 10km around postal code in which cheapest prices is found |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT ) |
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    </details>

- <details><summary>Example service call using iphone gecoded user location</summary>

   ```
   service: EVChargingStations.get_lowest_fuel_price
   data:
     fuel_type: diesel
     country: BE
     postalcode: "{{state_attr('sensor.iphone_geocoded_location','Postal Code')}}"
     town: "{{state_attr('sensor.iphone_geocoded_location','Locality')}}"
     max_distance: 5
     filter: Total

   ```

    </details>

- <details><summary>Example service call using iphone lat lon coordinates location</summary>

   ```
   service: EVChargingStations.get_lowest_fuel_price_coor
   data:
     fuel_type: diesel
     latitude: "{{state_attr('device_tracker.iphone','latitude')}}"
     longitude: "{{state_attr('device_tracker.iphone','longitude')}}"
     max_distance: 5
     filter: Total

   ```

    </details>
    
- <details><summary>Example automation triggered by event</summary>

   ```
   alias: Carbu event
   description: ""
   trigger:
     - platform: event
       event_type: EVChargingStations_lowest_fuel_price # or EVChargingStations_lowest_fuel_price_coor
   condition: []
   action:
     - service: notify.persistent_notification
       data:
         message: >-
           {{ trigger.event.data.supplier_brand }}: {{ trigger.event.data.price }}€
           at {{ trigger.event.data.distance }}km, {{ trigger.event.data.address }}
   mode: single

   ```

    </details>
    
    
A **service `EVChargingStations.get_lowest_fuel_price_on_route`** (**BETA**) to get the lowest fuel price on the route in between two postal codes. Can be used for example to get the lowest price between your current location and your home, or between office and home etc. The lowest fuel price will be fetched and an event will be triggered with all the details found. The route is retrieved using [Open Source Routing Machine](https://project-osrm.org/). For performance and request limitations, 30% of the locations (evenly distributed) are used for which the best price of each on a distance of 3km is fetched. So no guarantee this would be the absolute best price. If too long routes are searched, it might get stuck because of the limitations of the quota of the free API. Similar, the service **`EVChargingStations.get_lowest_fuel_price_on_route_coor`** can be called providing latitude and longitude coordinates instead of country, postalcode and town.

- <details><summary>Event data returned, Event name: <code>EVChargingStations_lowest_fuel_price_on_route</code> or <code>EVChargingStations_lowest_fuel_price_on_route_coor</code></summary>

    | Attribute | Description |
    | --------- | ----------- |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | `supplier`  | Name of the supplier of the fuel |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier Not supported for DE |
    | `longitude`  | Longitude of the supplier Not supported for DE |
    | `region`  | Distand 5km or 10km around postal code in which cheapest prices is found |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT ) |
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** ( Not supported for IT ) |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price ( Not supported for IT ) |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    </details>

- <details><summary>Example service call</summary>

   ```
   service: EVChargingStations.get_lowest_fuel_price_on_route
   data:
     fuel_type: diesel
     country: BE
     from_postalcode: 3620 #"{{state_attr('sensor.iphone_geocoded_location','Postal Code')}}"
     to_postalcode: 3660

   ```

    </details>

- <details><summary>Example service call using lat lon coordinates location</summary>

   ```
   service: EVChargingStations.get_lowest_fuel_price_on_route
   data:
     fuel_type: diesel
     from_latitude: 50.8503
     from_longitude: 4.3517
     to_latitude: 51.2194
     to_longitude: 4.4025

   ```

    </details>
    
- <details><summary>Example automation triggered by event</summary>

   ```
   alias: Carbu event
   description: ""
   trigger:
     - platform: event
       event_type: EVChargingStations_lowest_fuel_price_on_route # or EVChargingStations_lowest_fuel_price_on_route_coor
   condition: []
   action:
     - service: notify.persistent_notification
       data:
         message: >-
           {{ trigger.event.data.supplier_brand }}: {{ trigger.event.data.price }}€
           at {{ trigger.event.data.distance }}km, {{ trigger.event.data.address }}
   mode: single

   ```

    </details>
    

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/EVChargingStations/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code Carbu.com/custom_components/Carbu.com:
- [sensor.py](https://github.com/myTselection/EVChargingStations/blob/master/custom_components/EVChargingStations/sensor.py)
- [utils.py](https://github.com/myTselection/EVChargingStations/blob/master/custom_components/EVChargingStations/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

If you would encounter some issues with this custom component, you can enable extra debug logging by adding below into your `configuration.yaml`:
```
logger:
  default: info
  logs:
     custom_components.EVChargingStations: debug
```

## Example usage:
### Gauge & Markdown
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/EVChargingStations/master/Markdown%20Gauge%20Card%20example.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: markdown
        content: >
          ## Diesel

          <img
          src="{{state_attr('sensor.EVChargingStations_diesel_1000_5km','entity_picture')}}"
          width="40"/>
          [{{state_attr('sensor.EVChargingStations_diesel_1000_5km','supplier')}}]({{state_attr('sensor.EVChargingStations_diesel_1000_5km','url')}} "{{state_attr('sensor.EVChargingStations_diesel_1000_5km','address')}}")

          #### Coming days: {% if
          states('sensor.EVChargingStations_diesel_prediction')|float < 0 %}<font
          color=green>{{states('sensor.EVChargingStations_diesel_prediction')}}%</font>{%
          else %}<font
          color=red>{{states('sensor.EVChargingStations_diesel_prediction')}}%</font>{%
          endif %}

          Best price in region (10km vs local):
          {{states('sensor.EVChargingStations_diesel_1000_10km')}},
          {{state_attr('sensor.EVChargingStations_diesel_1000_10km','supplier')}}
          {{state_attr('sensor.EVChargingStations_diesel_1000_10km','price diff %')}}
          ({{state_attr('sensor.EVChargingStations_diesel_1000_10km','price diff 30l')}}
          on 30l)

          Best price in region (10km vs 5km):
          {{states('sensor.EVChargingStations_diesel_1000_10km')}}€/l:
          {{state_attr('sensor.EVChargingStations_diesel_1000_10km','supplier')}}
          {{(states('sensor.EVChargingStations_diesel_1000_5km')|float -
          states('sensor.EVChargingStations_diesel_1000_10km')|float)|round(2)}}€
          ({{(states('sensor.EVChargingStations_diesel_1000_5km')|float -
          states('sensor.EVChargingStations_diesel_1000_10km')|float)|round(2)*30}}€ on
          30l)
      - type: markdown
        content: >-
          ## Mazout

          [{{state_attr('sensor.EVChargingStations_oilstd_1000_1000l_price','supplier')}}]({{state_attr('sensor.EVChargingStations_oilstd_1000_1000l_price','url')}})


          #### Coming days: {% if
          states('sensor.EVChargingStations_oilextra_1000l_prediction')|float < 0 %}<font
          color=green>{{states('sensor.EVChargingStations_oilextra_1000l_prediction')}}%</font>{%
          else %}<font
          color=red>{{states('sensor.EVChargingStations_oilextra_1000l_prediction')}}%</font>{%
          endif %}
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.EVChargingStations_diesel_1000_5km
        min: 0
        max: 5
        needle: true
        unit: €/l
        name: Diesel prijs
        severity:
          green: 0
          yellow: 0.8
          red: 2
      - type: gauge
        entity: sensor.EVChargingStations_oilstd_1000_1000l_price
        min: 0
        max: 5
        needle: true
        unit: €/l
        name: Mazout prijs
        severity:
          green: 0
          yellow: 0.8
          red: 2
  - type: history-graph
    entities:
      - entity: sensor.EVChargingStations_diesel_1000_5km
        name: Diesel
      - entity: sensor.EVChargingStations_oilextra_1000_1000l_price
        name: Oil extra (per 1000l)
    hours_to_show: 500
    refresh_interval: 60
    
```
</details>


### Markdown example card with prices for local, 5 & 10 km (by @bavala3010)
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/EVChargingStations/master/Markdown%20Gauge%20Card%20example2.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: vertical-stack
cards:
  - type: markdown
    content: >
      ## Super95 benzine

      #### Komende dagen: {% if
      states('sensor.EVChargingStations_super95_prediction')|float < 0 %}<font
      color=green>{{states('sensor.EVChargingStations_super95_prediction')}}%</font>{%
      else %}<font
      color=red>{{states('sensor.EVChargingStations_super95_prediction')}}%</font>{%
      endif %}
  - type: horizontal-stack
    cards:
      - type: markdown
        content: >
          #### <center>lokaal </center>


          <center><img
          src="{{state_attr('sensor.EVChargingStations_super95_3010_price','entity_picture')}}"
          width="45"/> </center>


          <center>


          [{{state_attr('sensor.EVChargingStations_super95_3010_price','supplier')}}]({{state_attr('sensor.EVChargingStations_super95_3010_price','url')}})

          ### <center>{{states('sensor.EVChargingStations_super95_3010_price')}} €/l
      - type: markdown
        content: >
          #### <center>5 km</center>

          <center><img
          src="{{state_attr('sensor.EVChargingStations_super95_3010_5km','entity_picture')}}"
          width="45"/></center>


          <center>


          [{{state_attr('sensor.EVChargingStations_super95_3010_5km','supplier')}}]({{state_attr('sensor.EVChargingStations_super95_3010_5km','url')}})

          ### <center>{{states('sensor.EVChargingStations_super95_3010_5km')}} €/l

          Besparing tov lokaal =
          {{state_attr('sensor.EVChargingStations_super95_3010_5km','price diff %')}} of
          **{{state_attr('sensor.EVChargingStations_super95_3010_5km','price diff
          30l')}}** op 30l
      - type: markdown
        content: >
          #### <center>10 km

          <center><img
          src="{{state_attr('sensor.EVChargingStations_super95_3010_10km','entity_picture')}}"
          width="45"/></center>


          <center>


          [{{state_attr('sensor.EVChargingStations_super95_3010_10km','supplier')}}]({{state_attr('sensor.EVChargingStations_super95_3010_10km','url')}})

          ### <center>{{states('sensor.EVChargingStations_super95_3010_10km')}} €/l

          Besparing tov lokaal =
          {{state_attr('sensor.EVChargingStations_super95_3010_10km','price diff %')}} of
          **{{state_attr('sensor.EVChargingStations_super95_3010_10km','price diff
          30l')}}** op 30l


```
</details>



### Markdown example card on map
The sensors contain latitude and longitude attributes and entity_picture attributes to allow the sensors to be shown nicely on a map
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/EVChargingStations/master/Markdown%20Map%20Card%20example.png"/></p>
<details><summary>Click to show Mardown code example</summary>

```
type: map
entities:
  - entity: sensor.EVChargingStations_diesel_1000_price
  - entity: sensor.EVChargingStations_diesel_1000_5km
  - entity: sensor.EVChargingStations_diesel_1000_10km
title: carbu
```
</details>
