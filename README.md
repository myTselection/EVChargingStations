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
   - Provide any 'origin': this can be a coordinate eg: "51.330436, 3.802043" or "street, city, country" or any sensor name which has latitude and longitutde coordinate attributes eg "person.fred" or "device_tracker.car_position"
- For 'Public single Shell charge station':
   - Provide the unique serial number of the charging station: the serial number can be found in the details of a charging station on [https://ui-map.shellrecharge.com](https://ui-map.shellrecharge.com)
- For 'Private Shell charge station':
   - Provide Shell credentials username and password
- TODO: After setting up the integration, the configuration can be updated using the 'Configure' button of the integration. The usage of a station filter can be enabled and set, the usage of a template to set the 'friendly name' of each sensor type can be enabled and set and the usage of icons with price indication can be enabled or disabled.
  - The checkboxes are required since else clearing the text of the configuration was not recorded (HA bug?) and filter or templates could no longer be removed once set.
  - When setting a sensor 'friendly name' template, any sensor attribute can be used as a placeholder which will be replaced with the actual value. Eg: `Price {fueltype} {fuelname} {supplier}` could be used as a template for the Price sensor. All available attributes can be fetched using the 'Developer Tools' > 'States' > 'Attributes' view in HA or using the tables listed below.



### Setup screenshot

![Carbu com setup config](https://github.com/myTselection/EVChargingStations/blob/629be913c9e8f06fdbcc55040880cb83ae2fe785/setup.png) 





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
    | `map_label` | Attribute that can be used to show on map, currently showning `<available connectors>/<total connectors (<max power>kWh)` |
    
    </details>
    

## Show map

### Nearest map

To show a map in Home Assistant with all nearest charging stations you can use a setup such as shown below. It will show the max kWh charging power on map.

   ```
   type: map
   entities:
     - entity: sensor.nearest_station_device_tracker_car_position
       label_mode: attribute
       attribute: map_label
       focus: false
     - entity: >-
         sensor.nearest_available_station_device_tracker_car_position
       label_mode: attribute
       attribute: map_label
       focus: true
     - entity: >-
         sensor.nearest_highspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: map_label
       focus: false
     - entity: >-
         sensor.nearest_available_highspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: map_label
       focus: true
     - entity: >-
         sensor.nearest_superhighspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: map_label
       focus: false
     - entity: >-
         sensor.nearest_available_superhighspeed_station_device_tracker_car_position
       label_mode: attribute
       attribute: map_label
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
     aspect_ratio: 185%
     url: ${states['sensor.car_eneco_charging_station_url'].state}

   ```

## Example info markdown card
Below markdown will only show unique charging stations, so if nearest and nearest available are the same, it will only be shown once.

A link towards Eneco chargemap is available on the name of the charging stations

A link to Google maps directions from car to charging station is available on the address of the charging station

To re-use, replace 
- `device_tracker_car_position` with origin used during setup of EVChargingStation
- `device_tracker.car_position` with entity id or sensor name of your car (or similar)

```

type: markdown
content: >-
  # Charging stations close to car



  ### Nearest available
  ({{state_attr('sensor.nearest_available_station_device_tracker_car_position','distance')}}km):

  [{{state_attr('sensor.nearest_available_station_device_tracker_car_position','name')}}]({{state_attr('sensor.nearest_available_station_device_tracker_car_position','url')}})

  >
  🗺️[{{state_attr('sensor.nearest_available_station_device_tracker_car_position','address')}},
  {{state_attr('sensor.nearest_available_station_device_tracker_car_position','postal_code')}}
  {{state_attr('sensor.nearest_available_station_device_tracker_car_position','city')}}](https://www.google.com/maps/dir/?api=1&origin={{state_attr('device_tracker.car_position','latitude')}},{{state_attr('device_tracker.car_position','longitude')}}&destination={{state_attr('sensor.nearest_available_station_device_tracker_car_position','latitude')}},{{state_attr('sensor.nearest_available_station_device_tracker_car_position','longitude')}}&travelmode=driving)

  {{state_attr('sensor.nearest_available_station_device_tracker_car_position','connector_max_power')}}kWh,
  {{state_attr('sensor.nearest_available_station_device_tracker_car_position','available_connectors')}}/{{state_attr('sensor.nearest_available_station_device_tracker_car_position','number_of_connectors')}}
  available

  {{state_attr('sensor.nearest_available_station_device_tracker_car_position','facilities')}}


  {% if
  state_attr('sensor.nearest_station_device_tracker_car_position','external_id')
  !=
  state_attr('sensor.nearest_available_station_device_tracker_car_position','external_id')
  %}

  ### Nearest 
  ({{state_attr('sensor.nearest_station_device_tracker_car_position','distance')}}km):

  [{{state_attr('sensor.nearest_station_device_tracker_car_position','name')}}]({{state_attr('sensor.nearest_station_device_tracker_car_position','url')}})

  >
  🗺️[{{state_attr('sensor.nearest_station_device_tracker_car_position','address')}},
  {{state_attr('sensor.nearest_station_device_tracker_car_position','postal_code')}}
  {{state_attr('sensor.nearest_station_device_tracker_car_position','city')}}](https://www.google.com/maps/dir/?api=1&origin={{state_attr('device_tracker.car_position','latitude')}},{{state_attr('device_tracker.car_position','longitude')}}&destination={{state_attr('sensor.nearest_station_device_tracker_car_position','latitude')}},{{state_attr('sensor.nearest_station_device_tracker_car_position','longitude')}}&travelmode=driving)

  {{state_attr('sensor.nearest_station_device_tracker_car_position','connector_max_power')}}kWh,
  {{state_attr('sensor.nearest_station_device_tracker_car_position','available_connectors')}}/{{state_attr('sensor.nearest_station_device_tracker_car_position','number_of_connectors')}}
  beschikbaar

  {{state_attr('sensor.nearest_station_device_tracker_car_position','facilities')}}

  {% endif %}



  {% if
  state_attr('sensor.nearest_available_station_device_tracker_car_position','external_id')
  !=
  state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','external_id')%}

  ### High speed available
  ({{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','distance')}}km):

  [{{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','name')}}]({{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','url')}})

  >
  🗺️[{{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','address')}},
  {{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','postal_code')}}
  {{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','city')}}](https://www.google.com/maps/dir/?api=1&origin={{state_attr('device_tracker.car_position','latitude')}},{{state_attr('device_tracker.car_position','longitude')}}&destination={{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','latitude')}},{{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','longitude')}}&travelmode=driving)

  {{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','connector_max_power')}}kWh,
  {{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','available_connectors')}}/{{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','number_of_connectors')}}
  available

  {{state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','facilities')}}

  {% endif %}

  {% if
  state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','external_id')
  !=
  state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','external_id')
  %}

  ### High speed
  ({{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','distance')}}km):

  [{{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','name')}}]({{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','url')}})

  >
  🗺️[{{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','address')}},
  {{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','postal_code')}}
  {{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','city')}}](https://www.google.com/maps/dir/?api=1&origin={{state_attr('device_tracker.car_position','latitude')}},{{state_attr('device_tracker.car_position','longitude')}}&destination={{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','latitude')}},{{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','longitude')}}&travelmode=driving)

  {{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','connector_max_power')}}kWh,
  {{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','available_connectors')}}/{{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','number_of_connectors')}}
  available

  {{state_attr('sensor.nearest_highspeed_station_device_tracker_car_position','facilities')}}

  {% endif %}



  {% if
  state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','external_id')
  !=
  state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','external_id')
  and
  state_attr('sensor.nearest_available_station_device_tracker_car_position','external_id')
  !=
  state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','external_id')%}

  ### Super highspeed available
  ({{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','distance')}}km):

  [{{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','name')}}]({{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','url')}})

  >
  🗺️[{{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','address')}},
  {{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','postal_code')}}
  {{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','city')}}](https://www.google.com/maps/dir/?api=1&origin={{state_attr('device_tracker.car_position','latitude')}},{{state_attr('device_tracker.car_position','longitude')}}&destination={{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','latitude')}},{{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','longitude')}}&travelmode=driving)

  {{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','connector_max_power')}}kWh,
  {{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','available_connectors')}}/{{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','number_of_connectors')}}
  available

  {{state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','facilities')}}

  {% endif %}

  {% if
  state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','external_id')
  !=
  state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','external_id')
  and
  state_attr('sensor.nearest_available_superhighspeed_station_device_tracker_car_position','external_id')!=
  state_attr('sensor.nearest_available_highspeed_station_device_tracker_car_position','external_id')
  %}

  ### Super highspeed
  ({{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','distance')}}km):

  [{{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','name')}}]({{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','url')}})

  >
  🗺️[{{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','address')}},
  {{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','postal_code')}}
  {{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','city')}}](https://www.google.com/maps/dir/?api=1&origin={{state_attr('device_tracker.car_position','latitude')}},{{state_attr('device_tracker.car_position','longitude')}}&destination={{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','latitude')}},{{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','longitude')}}&travelmode=driving)

  {{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','connector_max_power')}}kWh,
  {{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','available_connectors')}}/{{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','number_of_connectors')}}
  available

  {{state_attr('sensor.nearest_superhighspeed_station_device_tracker_car_position','facilities')}}

  {% endif %}
grid_options:
  columns: full



```

# TODO, UNDER CONSTRUCTION
### Services / Actions
    
    

## Status
Proof of concept status, still validating and extending functionalities. [Issues](https://github.com/myTselection/EVChargingStations/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code Carbu.com/custom_components/Carbu.com:
- [sensor.py](https://github.com/myTselection/EVChargingStations/blob/master/custom_components/EVChargingStations/sensor.py)
- [coordinator.py](https://github.com/myTselection/EVChargingStations/blob/master/custom_components/EVChargingStations/coordinator.py)
- [evrecharge.py EVApi](https://github.com/myTselection/EVChargingStations/blob/master/custom_components/EVChargingStations/evrecharge/__init__.py)

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

If you would encounter some issues with this custom component, you can enable extra debug logging by adding below into your `configuration.yaml`:
```
logger:
  default: info
  logs:
     custom_components.EVChargingStations: debug
```

## Example usage:
