[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/release/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/EVChargingStations.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/EVChargingStations.svg)](https://github.com/myTselection/EVChargingStations/graphs/commit-activity)

# Public EV Charging Stations Home Assistant integration
Home Assistant custom component to create sensors with information on the cheapest EV Charging Station in a chosen area. This custom component has been built from the ground up to bring public site data to compare and save on your EV prices and integrate this information into Home Assistant. This integration is built against the public websites provided by Eneco.com and other similar sites. Sensors will be created for the currently **cheapest** station in a region (at location, within 5km and within 10km). The cheapest charging station in between two locations can be retrieved too.

**Currently supporting charging stations in Belgium, France, Luxembourg, Spain, Netherlands, Germany, Italy and on routes.**

This integration is in no way affiliated with Eneco.com. This integration is based on my other [Carbu.com](https://github.com/myTselection/Carbu_com) custom integration, which brings similar functionality for fuel/gas stations.

| :warning: Please don't report issues with this integration to other platforms, they will not be able to support you. |
| ---------------------------------------------------------------------------------------------------------------------|


For electricity price expectations [this Entso-E HACS integration](https://github.com/JaccoR/hass-entso-e) can be used.


<p align="center"><img src="https://raw.githubusercontent.com/myTselection/EVChargingStations/master/logo.png"/></p>

With this integration it will be possible to:
- subscribe to specific charging point, to make it possible to get notified once available
- get sensors (can be shown on map) with:
   - charging stations **nearest** to location
   - **available** charging stations **nearest** to location
   - **high** speed charging station **nearest** to location
   - **high** speed **available** charging stations **nearest** to location
   - **super high** speed charging station **nearest** to location
   - **super high** speed **available** charging station **nearest** to

   - **cheapest** charging stations and nearest to location
   - **available** **cheapest** charging stations and nearest to location
   - **high** speed charging station **cheapest** and nearest to location
   - **high** speed **available** **cheapest** charging stations and nearest to location
   - **super high** speed **cheapest** charging station and nearest to location
   - **super high** speed **available** **cheapest** charging station and nearest to location



# TODO, UNDER CONSTRUCTION

## Installation
- [HACS](https://hacs.xyz/): search for Carbu in the default HACS repo list or use below button to navigate directly to it on your local system and install via HACS. 
   -    [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myTselection&repository=EVChargingStations&category=integration)
- Restart Home Assistant
- Add 'EV Charging Stations' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide country, postal code and select the desired sensors
   - The name of the town can be selected from the dropdown in the next step of the setup config flow. See [carbu.com](https://carbu.com) website for known towns and postal codes. (Only for BE/FR/LU)
   - An extra checkbox can be set to select a specific individual gas station. If set, a station can be selected in a dropdown with known gas stations (for which a price is available) close to the provided postalcode and town. No sensor for 5km and 10km will be created, only the price sensor for the individual selected station. The name of the sensor will contain the name of the supplier.
   - For Italy, Netherlands, Spain and US the town will be requested in the second step of the config flow
- Get an API key at [Geoapify.com](https://myprojects.geoapify.com/register), which has a free tier for 3K geocoding requests per day. If the API key is not set, countries IT, NL, ES and US will not function and services to find fuel price on route or at coordinate will not function. The API key can also be set/updated on existing sensors using the 'Configure' entity option.
- A filter on supplier brand name can be set (optional). If the filter match, the fuel station will be considered, else next will be searched. A python regex filter value can be set
- An option is avaible to show a logo (entity picture) with price or the original logo provided by the source. This is mainly visible when mapping the sensor on a map.
- After setting up the integration, the configuration can be updated using the 'Configure' button of the integration. The usage of a station filter can be enabled and set, the usage of a template to set the 'friendly name' of each sensor type can be enabled and set and the usage of icons with price indication can be enabled or disabled.
  - The checkboxes are required since else clearing the text of the configuration was not recorded (HA bug?) and filter or templates could no longer be removed once set.
  - When setting a sensor 'friendly name' template, any sensor attribute can be used as a placeholder which will be replaced with the actual value. Eg: `Price {fueltype} {fuelname} {supplier}` could be used as a template for the Price sensor. All available attributes can be fetched using the 'Developer Tools' > 'States' > 'Attributes' view in HA or using the tables listed below.



### Setup screenshot
![Carbu com setup config](https://github.com/user-attachments/assets/103221e3-3a0a-48ef-a3ae-00b59ee5e2cb) 

For BE/FR/LU, sensors for mazout/fuel oil can be added too.

![Carbu com BE-FR-LU fuel mazout prices](https://github.com/user-attachments/assets/1b9d0f16-3e88-4797-9e53-c69624a1f35d)


If desired (selection box default off), the fuel price of a specific individual station can be shown. If no individual station is enabled, the cheapest station in the area will be retrieved and price and address details will be shown in the sensor attributes.

![Carbu com optional specific gas station](https://github.com/user-attachments/assets/81cbb120-5b1c-4d25-bdc9-9f6b7c09f209)




## Integration
### Mapping

| Fuel type | BE/FR/LU (carbu) | DE (clever-tanken.de) | IT (prezzibenzina.it) | NL (brandstof-zoeker.nl) | ES (sedeaplicaciones.minetur.gob.es) | US (gas-buddy.com) |
| --------- | ---------------- | --------------------- | --------------------- | ------------------------ | ------------------------------------ | ------------------ |
| SUPER95 (E10)  | E10         | Super E10             | benzina               | euro95                   | Gasolina 95 E10                      | regular_gas        |
| SUPER95 (E5)   | / (E10)     | Super E5              | / (benzina)           | specbenzine              | Gasolina 95 E5 Premium               | / (regular_gas)    |
| SUPER98 (E5)   | SP98        | SuperPlus             | benzinasp             | superplus                | Gasolina 98 E5                       | premium_gas        |
| DIESEL (B7)    | GO          | Diesel                | diesel                | diesel                   | Gasóleo A                            | diesel             |
| LPG            | GPL         | LPG                   | gpl                   | lpg                      | Gases licuados del petróleo          | /                  |


### Sensors
- <details><summary>Sensor with lowest diesel and super <code>sensor.EVChargingStations_[fueltype]_[postalcode]_price</code> and lowest fuel oil <code>sensor.EVChargingStations_[fueltype]_[postalcode]_[quantity]l_price</code> Fuel oil only supported for BE/FR/LU</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | **Price** |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | `postalcode`  | Postalcode at which the price was retrieved |
    | **`supplier`**  | **Name of the supplier of the fuel** |
    | `supplier_brand`  | Brand name of the supplier (eg Shell, Texaco, ...) Not supported for DE |
    | `url`  | Url with details of the supplier |
    | `entity_picture`  | Url with the logo of the supplier |
    | `address`  | Address of the supplier |
    | `city`  | City of the supplier |
    | `latitude`  | Latitude of the supplier |
    | `longitude`  | Longitude of the supplier |
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT ) |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity of fuel (only for fuel oil) |
    | `score`  | Score of the supplier |
    | `id`  | Unique id of the supplier |
    | ~~`suppliers`~~  | ~~Full json list of all suppliers with prices and detials found in neighbourhood around the postal code~~ |
    
    </details>
    
- <details><summary>Sensor with lowest diesel and super price in neighbourhood: <code>sensor.EVChargingStations_[fueltype]_[postalcode]_[*]km</code> for 5km and 10km </summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Price |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
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
    | **`distance`**  | **Distance to the supplier vs postal code** ( Not supported for IT )|
    | **`price diff`**  | **Price difference between the cheapest found in region versus the local price** |
    | `price diff %`  | Price difference in % between the cheapest found in region versus the local price |
    | `price diff 30l`  | Price difference for 30 liters between the cheapest found in region versus the local price |
    | `date`  | Date for the validity of the price |
    | `quantity`  | Quantity of fuel (only for fuel oil) |
    | `score`  | Score of the supplier |
    | `id`  | Unique id of the supplier |
    </details>

- <details><summary>Sensor with official diesel and super price <code>sensor.EVChargingStations_[fueltype]_officia_[fueltypecode]</code>, only supported for BE/FR/LU/NL</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | **Price** |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `price`   | Price |
    | `date`  | Date for the validity of the price |
    | `country`  | Country |
    | `price next`   | Next official price |
    | `date next`  | Date as of when the next price will be applicable |
    </details>
    
- <details><summary>Sensor diesel and super prediction: <code>sensor.EVChargingStations_[fueltype]_prediction</code> Only supported for BE/FR/LU</summary>
    
    | Attribute | Description |
    | --------- | ----------- |
    | State     | Percentage of increase or decrease predicted for coming days |
    | `last update` | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | **`trend`** | **Percentage of increase or decrease predicted for coming days** |
    | `date`  | Date for the validity of the price |
    </details>
    
- <details><summary>Sensor fuel oil prediction: <code>sensor.EVChargingStations_[oiltype]_[quantity]l_prediction</code> Only supported for BE/FR/LU</summary>

    | Attribute | Description |
    | --------- | ----------- |
    | State     | Percentage of increase or decrease predicted for coming days |
    | `last update `   | Timestamp info last retrieved from the carbu.com website. (There is a throttling of 1h active to limit requests. Restart HA to force update) |
    | `fueltype`   | Fuel type |
    | `fuelname` | Full name of the fuel type |
    | **`trend`** | **Percentage of increase or decrease predicted for coming days** |
    | `price` | Predicted maximum price for type and quantity |
    | `date`  | Date for the validity of the price |
    | `current official max price`  | Currently official max price |
    | `current official max price date`  | Date of the currently official max price |
    | `quantity`  | Quantity for which the price is expected. Main difference between below or above 2000l |
    </details>

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
