# Dataset Overview

## 1. Purpose

This dataset powers a Spark-based classification model that predicts whether a flight will depart with a delay of 15 minutes or more, using only **scheduled information** and **pre-departure weather conditions** (METAR features) at origin and destination airports.

The data is constructed by joining:

* Flight statistics data (scheduled and realized times, delays, cancellations, etc.)
* METAR weather data for origin and destination stations

Only features that would be known **before scheduled departure time** are kept for modeling to avoid label leakage.

* Flight Statistics Source:
* Metar Statistics Source: 
---

## 2. Record counts and structure

**Raw joined parquet input**

* Path: `parquet_delay_and_weather_24/`
* Rows: `35194`
* Columns: `68`

**Post-cleaning feature DataFrame (`df`)**

After column selection and dropping rows with missing values in the retained columns:

* Rows: `31316`
* Columns: `25` (including label)

**Spark DataFrame (`sdf`)**

Created via `spark.createDataFrame(df)` with the following schema:

```text
root
 |-- Year: long (nullable = true)
 |-- Month: long (nullable = true)
 |-- DayofMonth: long (nullable = true)
 |-- DayOfWeek: long (nullable = true)
 |-- FlightDate: timestamp (nullable = true)
 |-- Marketing_Airline_Network: string (nullable = true)
 |-- Operating_Airline: string (nullable = true)
 |-- Origin: string (nullable = true)
 |-- Dest: string (nullable = true)
 |-- OriginWindDirection: double (nullable = true)
 |-- OriginWindSpeed: double (nullable = true)
 |-- OriginVisibility: double (nullable = true)
 |-- OriginPrecipitation: string (nullable = true)
 |-- OriginClouds: string (nullable = true)
 |-- DestWindDirection: double (nullable = true)
 |-- DestWindSpeed: double (nullable = true)
 |-- DestVisibility: double (nullable = true)
 |-- DestPrecipitation: string (nullable = true)
 |-- DestClouds: string (nullable = true)
 |-- label: long (nullable = true)
 |-- DepHour: long (nullable = true)
 |-- ArrHour: long (nullable = true)
 |-- DepMinute: long (nullable = true)
 |-- ArrMinute: long (nullable = true)
 |-- is_weekend: long (nullable = true)
```

---

## 3. Target variable (label)

The target for modeling is the **departure delay indicator**.

* Original source column: `DepDel15`

  * Type in raw parquet: `float64`
  * Semantics:

    * `1.0` = flight departed **15 minutes or more** late
    * `0.0` = flight departed less than 15 minutes late (or on time)

* Processing:

  * Rows with missing `DepDel15` are removed during `df.dropna()`.
  * `DepDel15` is cast to integer and stored as `label`:

    ```python
    label_col = "DepDel15"
    y = df[label_col].astype(int)
    df["label"] = y
    df = df.drop(columns=[label_col])
    ```

Final label:

* Column name: `label`
* Type: `int64` in pandas, `long` in Spark
* Values: `0` or `1`

---

## 4. Feature columns (post-processing)

Below is the final feature set in `df` before converting to Spark, grouped by category.

### 4.1 Temporal and calendar features

| Column       | Type                   | Description                                                           |
| ------------ | ---------------------- | --------------------------------------------------------------------- |
| `Year`       | int32 / long           | Calendar year of the flight date                                      |
| `Month`      | int32 / long           | Month of year, 1 to 12                                                |
| `DayofMonth` | int32 / long           | Day of month, 1 to 31                                                 |
| `DayOfWeek`  | int32 / long           | Day of week, 1 to 7 (as in original flight data)                      |
| `FlightDate` | datetime64 / timestamp | Flight date with time (converted to pandas datetime, Spark timestamp) |
| `DepHour`    | int64 / long           | Scheduled departure hour extracted from `CRSDepTime`                  |
| `DepMinute`  | int64 / long           | Scheduled departure minute extracted from `CRSDepTime`                |
| `ArrHour`    | int64 / long           | Scheduled arrival hour extracted from `CRSArrTime`                    |
| `ArrMinute`  | int64 / long           | Scheduled arrival minute extracted from `CRSArrTime`                  |
| `is_weekend` | int64 / long           | Indicator 1 if flight date is Saturday or Sunday, else 0              |

Time derivation functions:

```python
def hhmm_to_hour(t):
    t = int(t)
    return t // 100

def hhmm_to_minute(t):
    t = int(t)
    return t % 100
```

The original columns `CRSDepTime` and `CRSArrTime` are dropped after `DepHour`, `DepMinute`, `ArrHour`, and `ArrMinute` are created.

`is_weekend` is computed as:

```python
df["FlightDate"] = pandas.to_datetime(df["FlightDate"])
df["is_weekend"] = df["FlightDate"].dt.dayofweek.isin([5, 6]).astype(int)
```

### 4.2 Flight identification features

| Column                      | Type          | Description                                    |
| --------------------------- | ------------- | ---------------------------------------------- |
| `Marketing_Airline_Network` | object/string | Marketing or branded carrier code/network name |
| `Operating_Airline`         | object/string | Operating carrier code                         |
| `Origin`                    | object/string | Origin airport code (IATA)                     |
| `Dest`                      | object/string | Destination airport code (IATA)                |

High-cardinality categorical features likely to be string-indexed in Spark.

### 4.3 Weather features – origin airport

| Column                | Type           | Description                                                        |
| --------------------- | -------------- | ------------------------------------------------------------------ |
| `OriginWindDirection` | float64/double | Wind direction in degrees at origin                                |
| `OriginWindSpeed`     | float64/double | Wind speed at origin                                               |
| `OriginVisibility`    | float64/double | Horizontal visibility at origin                                    |
| `OriginPrecipitation` | object/string  | Precipitation categories at origin encoded as comma-separated text |
| `OriginClouds`        | object/string  | Cloud layers at origin encoded as comma-separated text             |

`OriginPrecipitation` and `OriginClouds` originally may contain array-like structures. They are normalized via `arr_to_str`:

```python
def arr_to_str(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "None"
    if isinstance(val, (list, np.ndarray)):
        if len(val) == 0:
            return "None"
        return ",".join(map(str, val))
    return str(val)

weather_array_cols = [
    "OriginPrecipitation", "OriginClouds",
    "DestPrecipitation", "DestClouds"
]

for col in weather_array_cols:
    df[col] = df[col].apply(arr_to_str)
```

Thus, downstream Spark processing will always see these as non-null strings such as:
`"None"`, `"RA"`, `"RA,SN"`, etc.

### 4.4 Weather features – destination airport

| Column              | Type           | Description                                                             |
| ------------------- | -------------- | ----------------------------------------------------------------------- |
| `DestWindDirection` | float64/double | Wind direction in degrees at destination                                |
| `DestWindSpeed`     | float64/double | Wind speed at destination                                               |
| `DestVisibility`    | float64/double | Horizontal visibility at destination                                    |
| `DestPrecipitation` | object/string  | Precipitation categories at destination encoded as comma-separated text |
| `DestClouds`        | object/string  | Cloud layers at destination encoded as comma-separated text             |

Same `arr_to_str` normalization as for the origin weather features.

---

## 5. Columns removed and rationale

The original joined dataset contained 68 columns. A large subset is dropped to:

* Avoid **label leakage** from realized outcomes and post-departure information
* Remove duplicate or redundant IDs and text fields
* Drop columns with extensive missing values that are not essential for the model

### 5.1 Leakage-prone realized outcome columns

Removed because they encode actual realized delays or post-flight outcomes that are not known at prediction time.

* `DepTime`, `DepDelay`, `DepDelayMinutes`
* `DepartureDelayGroups`
* `TaxiOut`, `WheelsOff`, `WheelsOn`, `TaxiIn`
* `ArrTime`, `ArrDelay`, `ArrDelayMinutes`
* `ArrDel15`, `ArrivalDelayGroups`
* `Cancelled`, `Diverted`
* Delay cause breakdowns: `CarrierDelay`, `WeatherDelay`, `NASDelay`, `SecurityDelay`, `LateAircraftDelay`

These are kept only in the auxiliary `label_df` for analysis and possible alternative label definitions, but not as features in `df`.

### 5.2 Redundant identifiers and text

Removed to simplify the feature space and avoid multicollinearity among identifiers and their human-readable forms.

* Airport and sequence IDs:
  `DestAirportID`, `OriginAirportID`,
  `OriginAirportSeqID`, `DestAirportSeqID`,
  `OriginCityMarketID`, `DestCityMarketID`
* Airline ID fields:
  `DOT_ID_Marketing_Airline`, `DOT_ID_Operating_Airline`
* Other identifiers:
  `Flight_Number_Operating_Airline`, `OriginICAO`, `DestICAO`
* Redundant text fields:
  `OriginCityName`, `DestCityName`
* Time-block categorical summaries:
  `DepTimeBlk`, `ArrTimeBlk`
* Timezone fields:
  `OriginTimezone`, `DestTimezone`
* Timestamp duplicates of CRS times:
  `CRSDepTimestamp`, `CRSArrTimestamp`

### 5.3 High-missing weather and delay columns

Some fields have extremely high proportions of missing values in this sample and are excluded from modeling:

* `CancellationCode`
* `OriginWindGusts`, `OriginTemperature`, `OriginDewPoint`
* `DestWindGusts`, `DestTemperature`, `DestDewPoint`

Note: in this dataset, `OriginTemperature`, `OriginDewPoint`, `DestTemperature`, and `DestDewPoint` are entirely missing, which is why they are dropped.

---

## 6. Missing data handling

At the feature-engineering stage, after column selection, the dataset still has missing values in some weather and label fields. The applied strategy is:

```python
df = df.dropna()
```

Effect:

* Only rows with **no missing values in the retained 22 columns** (before time feature engineering and `is_weekend`) are kept.
* Resulting row count: from `35194` down to `31316`.

Because `DepDel15` is included in this set, all retained rows have a valid label. After this, all final feature and label columns are fully non-null.

---
## 8. Summary for Spark pipeline consumers

For downstream Spark stages, you can assume:

* Each row in `sdf` corresponds to a single scheduled flight leg with:

  * Calendar fields: year, month, day, weekday, weekend flag
  * Scheduled time fields: departure and arrival hour/minute
  * Carrier and airport identifiers as strings
  * Pre-departure METAR features from origin and destination stations
* Target:

  * `label` = 1 indicates departure delay of at least 15 minutes
  * `label` = 0 indicates departure delay under 15 minutes
* No columns contain nulls in the Spark DataFrame `sdf`.
* All realized outcome fields and obvious post-fact variables have been removed to avoid information leakage.


