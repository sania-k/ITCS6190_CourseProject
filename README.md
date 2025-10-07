# Team 1 ITCS6190 Course Project Repository
## Overview
In this cloud computing for data analysis project, our team will design and implement a big data analysis pipeline through the use of Apache Spark's structured API's, SQL, Streaming, and MLib on our dataset. Our goal is to compare a daily list of outgoing domestic flights from the Charlotte-Douglas Airport, using the timings and locations to the weather during near departure to determine the likelihood of a fight delay.

Team Members:
1. Anshuk Gottipati
2. Frank Garcia
3. Nicholas Cassarino
4. Purva Rajaram Jagtap
5. Sania Khan

## Data
The sample data is stored in `Data/Sample/flight_delay_jan2025.csv`, which contains just one month of data for testing
The data is in both the sample and the greater dataset is stored in the following columns:
| Variable Name             | Type          | Description                                                                                                                                                                                                    |
| ------------------------- | ------------- | ------------------------------------|
| `Year`     | long          | Year                                |
| `Quarter`      | long          | Quarter                             |
| `Month`       | long          | Month                               |
| `DayofMonth`        | long          | Day of Month                        |
| `DayOfWeek`         | long          | Day of Week                         |
| `FlightDate`          | timestamp_ntz | Flight Date                         |
| `Marketing_Airline_Network` | string        | Unique Marketing Carrier Code. When the same code has been used by multiple carriers, a numeric suffix is used for earlier users, e.g., PA, PA(1), PA(2). Use this field for analysis across a range of years. |
| `OriginCityName `           | string        | Origin Airport, City Name          |
| `DestCityName`            | string        | Destination Airport, City Name       |
| `CRSDepTime`             | double        | CRS (scheduled) Departure Time (local time: hhmm) |
| `DepTime`              | double        | Actual Departure Time (local time: hhmm) |
| `DepDelay`      | double        | Difference in minutes between scheduled and actual departure time. Early departures show negative numbers.|
| `DepDelayMinutes`       | double        | Difference in minutes between scheduled and actual departure time. Early departures set to 0. |
| `TaxiOut`        | double        | Taxi Out Time: duration an aircraft spends taxiing from gate to runway before takeoff, in minutes |
| `WheelsOff`         | double        | Exact moment aircraft wheels leave the ground during takeoff (local time: hhmm) |
| `WheelsOn`          | double        | Exact moment aircraft wheels contact the runway during landing (local time: hhmm) |
| `TaxiIn`  | double        | Taxi In Time: duration aircraft spends taxiing from runway to gate after landing, in minutes |
| `CRSArrTime`   | double        | CRS (scheduled) Arrival Time (local time: hhmm) |
| `ArrTime`    | double        | Actual Arrival Time (local time: hhmm) |
| `ArrDelay`     | double        | Difference in minutes between scheduled and actual arrival time. Early arrivals show negative numbers |
| `ArrDelayMinutes`      | double        | Difference in minutes between scheduled and actual arrival time. Early arrivals set to 0. |
| `CRSElapsedTime`       | double        | CRS (scheduled) Elapsed Time of Flight, in minutes |
| `ActualElapsedTime`        | double        | Elapsed Time of Flight, in minutes  |
| `AirTime`         | double        | Flight Time, in minutes             |
| `Distance`  | double        | Distance between airports (miles)   |
| `DistanceGroup`   | long          | Distance intervals, every 250 miles, for flight segment |
| `CarrierDelay`    | double        | Carrier Delay, in minutes           |
| `WeatherDelay`     | double        | Weather Delay, in minutes            |
| `NASDelay`      | double        | National Air System Delay, in minutes |
| `SecurityDelay`       | double        | Security Delay, in minutes           |
| `LateAircraftDelay `        | double        | Late Aircraft Delay, in minutes      |
| `Holidays`                  | boolean       | Indicates whether the flight occurs on a holiday |
| `CRSDepTimeMinute`          | integer       | Minute portion of scheduled departure time |
| `CRSDepTimeHour`            | integer       | Hour portion of scheduled departure time |
| `WheelsOffMinute`           | integer       | Minute portion of wheels-off time   |
| `WheelsOffHour`             | integer       | Hour portion of wheels-off time     |
| `CRSArrTimeMinute`          | integer       | Minute portion of scheduled arrival time |
| `CRSArrTimeHour`            | integer       | Hour portion of scheduled arrival time |
| `WheelsOnMinute`            | integer       | Minute portion of wheels-on time     |
| `WheelsOnHour`              | integer       | Hour portion of wheels-on time       |
| `CRSDepTimeHourDis`         | string        | Discretized scheduled departure hour (for analysis) |
| `WheelsOffHourDis`          | string        | Discretized wheels-off hour (for analysis) |
| `CRSArrTimeHourDis`         | string        | Discretized scheduled arrival hour (for analysis) |
| `WheelsOnHourDis`           | string        | Discretized wheels-on hour (for analysis) |
| `CRSElapsedTimeGorup`       | long          | Grouped CRS elapsed time (for analysis) |

From here we can filter to look at NC data specifically, specific months, and specific airports


This data will be joined with METAR data at ingestioon. This can include the following weather data for both the origin and destination of flights:
| Data Name             | Description                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| `Time`                | The time of the observation from the METAR (third token).                                                |
| `Wind_Direction`      | Wind direction in degrees (first three digits of the wind token, e.g., `010` for 10°).                   |
| `Wind_Speed`          | Wind speed in knots (next two digits of the wind token, e.g., `08` for 8 knots).                         |
| `Wind_Gust`           | Wind gust speed in knots if present (after `G` in the wind token).                                       |
| `Visibility`          | Horizontal visibility in statute miles (if present, from the token containing `SM`).                     |
| `Runway_Visual_Range` | Runway visual range from tokens starting with `R` (distance plus optional `M`/`P` for min/max).          |
| `Temperature`         | Temperature in Celsius from token like `21/16` (first number).                                           |
| `Dewpoint`            | Dewpoint in Celsius from token like `21/16` (second number).                                             |
| `Altimeter`           | Altimeter pressure in inches of mercury from token like `A3000`.                                         |
| `Cloud_Coverage`      | Cloud information from tokens like `OVC100`, `SCT050` (overcast, scattered, height in hundreds of feet). |
| `Weather_Phenomena`   | A list of weather events. Each item has:                                                                 |
| └─ `Type`             | The kind of weather (e.g., rain, fog, hail, thunderstorm, freezing rain, volcanic ash, etc.).            |
| └─ `Intensity`        | The intensity of the weather: light (`-`), moderate (no sign), or heavy (`+`).                           |
| `Remarks`             | Any remaining remarks from the METAR (`RMK` section), often including station sensors or codes.          |


## Ingestion
### Prereqs:
1. *Python 3.x*:
   - [Download and Install Python](https://www.python.org/downloads/)
   - Verify installation:
     ```bash
     python3 --version
     ```

2. *PySpark, Selenium, Beautiful Soup, and Requests*:
   - Install using pip:
     ```bash
     pip install pyspark selenium beautifulsoup4 request
     ```

3. *Apache Spark*:
   - Ensure Spark is installed. You can download it from the [Apache Spark Downloads](https://spark.apache.org/downloads.html) page.
   - Verify installation by running:
     ```bash
     spark-submit --version
     ```
