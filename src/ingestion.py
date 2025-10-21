from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, lpad, try_to_timestamp, to_utc_timestamp, concat_ws, lit
from pyspark.sql.types import StringType, IntegerType, DoubleType, FloatType, ArrayType, StructType, StructField, MapType
import time
import requests
import re
import pandas as pd


from datetime import datetime, timedelta

# Creating Spark Session
spark = SparkSession.builder.appName("AirportDelay").getOrCreate()


# --- Loading Delay Sample Data ---

# Loading delay dataset from sample data
df = spark.read.csv("../data/sample/flight_delay_jan_2025_clt_origin_major_dest.csv", header=True, inferSchema=True)


# Checking Columns
df.printSchema()
df.select(
    "FlightDate",
    "OriginAirportID",
    "OriginCityName",
    "DestAirportID",
    "DestCityName",
    "CRSDepTime",
    "CRSArrTime",
).show(5, truncate=False)



# --- Adding Timestamps ---

# Airport dataframe to join with delay data for airport data needed for API lookups:
# Contains top 7 airports in the US, the only airports in the database at the moment
#   AirportID - the ID as per delay data
#   ICAO - Airport ICAO code for METAR API lookup
#   Timezone - Airport location for timezone conversions to UTC
airport_df = spark.createDataFrame([
    (10397, "KATL", "America/New_York"), # Atlanta, GA: Hartsfield-Jackson Atlanta International
    (11298, "KDFW", "America/Chicago"), # Dallas/Fort Worth, TX: Dallas/Fort Worth International
    (11292, "KDEN", "America/Denver"), # Denver, CO: Denver International
    (13930, "KORD", "America/Chicago"), # Chicago, IL: Chicago O"Hare International
    (12892, "KLAX", "America/Los_Angeles"), # Los Angeles, CA: Los Angeles International
    (12478, "KJFK", "America/New_York"), # New York, NY: John F. Kennedy International
    (11057, "KCLT", "America/New_York") # Charlotte, NC: Charlotte Douglas International
], ["AirportID", "ICAO", "Timezone"])

airport_df.select("AirportID", "ICAO", "Timezone").show()

# Joining airport data with delay data
# For origin airport
df = df.join(  
    airport_df.withColumnRenamed("AirportID", "OriginAirportID")
              .withColumnRenamed("Timezone", "OriginTimezone")
              .withColumnRenamed("ICAO", "OriginICAO"),
    on="OriginAirportID",
    how="left"
)

# For destination airport
df = df.join(airport_df.withColumnRenamed("AirportID", "DestAirportID")
              .withColumnRenamed("Timezone", "DestTimezone")
              .withColumnRenamed("ICAO", "DestICAO"),
    on="DestAirportID",
    how="left"
)

# Confirming columns
df.select(
    "FlightDate",
    "OriginAirportID",
    "OriginCityName",
    "OriginTimezone",
    "OriginICAO",
    "DestAirportID",
    "DestCityName",
    "DestTimezone",
    "DestICAO",
    "CRSDepTime",
    "CRSArrTime",
).show(5, truncate=False)

# Creating timestamp columns for delay data
# Departure timestamp
df = df.withColumn(
    "CRSDepTimestamp",
    try_to_timestamp(
        concat_ws(" ", col("FlightDate"), lpad(col("CRSDepTime"), 4, "0")),
        lit("yyyy-MM-dd HHmm")
    )
)

# Arrival timestamp
df = df.withColumn(
    "CRSArrTimestamp",
    try_to_timestamp(
        concat_ws(" ", col("FlightDate"), lpad(col("CRSArrTime"), 4, "0")),
        lit("yyyy-MM-dd HHmm")
    )
)

# Creating timestamp columns in UTC for delay data (needed for API calls)
# Departure timestamp
df = df.withColumn(
    "CRSDepTimestamp_UTC",
    to_utc_timestamp("CRSDepTimestamp", col("OriginTimezone"))
)

# Arrival timestamp
df = df.withColumn(
    "CRSArrTimestamp_UTC",
    to_utc_timestamp("CRSArrTimestamp", col("DestTimezone"))
)

# Confirming Columns
df.select(
    "FlightDate",
    "CRSDepTime",
    "CRSDepTimeStamp",
    "CRSDepTimeStamp_UTC"
).show(5, truncate=False)



# --- Adding METAR Data to Dataframe---

# Creating schemas to describe columns being added
weather_schema = StructType([
    StructField("WindDirection",IntegerType(),True),           # in degrees from N
    StructField("WindSpeed",IntegerType(),True),               # in kts
    StructField("WindGusts",IntegerType(),True),               # in kts
    StructField("Visibility",DoubleType(),True),              # statute miles
    StructField("Precipitation",ArrayType(StringType()),True), # type
    StructField("Clouds",ArrayType(StringType()),True),        # type
    StructField("Temperature",DoubleType(),True),             # deg C
    StructField("DewPoint",DoubleType(),True),                # deg C
])

# Helper functions for metar data retrieval

def generate_request_url(timestamp,icao_code):
    """Returns a string: the API call URL for previous and current day
    to ensure weather data from before departure.

    timestamp(datetime) -> scheduled flight departure time (UTC)
    icao_code(string) -> ICAO code of the airport 
    """
    base = "https://flightsupport24.com/map/archive.php?"
    end = "&tz=Etc/UTC&format=onlytdf&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=2"
    
    if isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

    # Previous day
    prev = timestamp - timedelta(days=1)
    day1, month1, year1 = prev.day, prev.month, prev.year

    # Current day
    post = timestamp + timedelta(days=1)
    day2, month2, year2 = post.day, post.month, post.year

    # Build URL
    request_URL = (
        f"{base}station={icao_code}&data=metar"
        f"&year1={year1}&month1={month1}&day1={day1}"
        f"&year2={year2}&month2={month2}&day2={day2}"
        f"{end}"
    )

    return request_URL

def get_metar_string(url,timestamp):
    """Returns a string of metar data from directly before the scheduled flight departure

    url(string): the request url for the api call
    timestamp(datetime): scheduled flight departure time (local)
    """

    try:
        time.sleep(0.25) #TODO: proper api rate limitings
        res = requests.get(url).text        

        metar_list = res.strip().splitlines()[1:] # Ignore first line, irrelevant data
        
        # Finding the observation immediately before planned departure

        # How the timestamp is formatted in the metar strings
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})"

        metar_line = None

        for line in metar_list:
            match = re.search(pattern,line)

            if not match:
                continue

            metar_timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")

            # Since the list is sorted, can check till the observation data is after
            # the target time and return the line before
            if metar_timestamp >= timestamp:
                break

            metar_line = line

        return metar_line

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def fetch_metar_for_row(row):
    '''Returns string of metar data using pandas df for faster retrieval
    
    row - row of pandas dataframe containing time and location requested
    '''
    # Optional: total rows for percentage calculation
    total = len(airport_times_pd)
    
    # Calculate current progress
    current_index = row.name + 1  # row.name is zero-based index
    if current_index % 10 == 0 or current_index == total:  # print every 10 rows or last row
        print(f"Processing row {current_index}/{total} ({current_index/total:.1%})")


    url = generate_request_url(row["TimestampUTC"], row["ICAO"])
    return get_metar_string(url, row["Timestamp"])

def parse_metar_string(metar_line):
    """ Returns a row of all the metar data characteristics

    metar_line -> line of metar data to be parsed
    """

    if not metar_line:
        return None

    tokens = metar_line.split()

    # Result fields
    WindDirection= None     # in degrees from N
    WindSpeed= None         # in kts
    WindGusts= None         # in kts
    Visibility= None        # statute miles
    Precipitation= []       # type, intensity
    Clouds= []              # time, height (ft)
    Temperature= None       # deg C
    DewPoint= None          # deg C
    
    i = 5 # counter, skipping first several irrelevant fields
    # print(tokens[i])

    # --- wind data ---
    # format: dddSSktgg
    if i < len(tokens) and "KT" in tokens[i]:
        # print(tokens[i])
        wind_match = re.match(r"(\d{3})(\d{2})(G(\d+))?KT", tokens[i])
        if wind_match:
            WindDirection = int(wind_match.group(1))
            WindSpeed = int(wind_match.group(2))
            
            # Wind gusts are optional
            if wind_match.group(4):
                WindGusts = int(wind_match.group(4))
        i += 1

    # --- visibility ---
    # format: vvSM
    if i < len(tokens) and tokens[i].endswith("SM"):
        # print(tokens[i])
        vis_match = re.match(r"(\d+)", tokens[i])
        if vis_match:
            Visibility = int(vis_match.group(1))
        i += 1

    # --- precip ---
    # format: +/-PP
    precip_dict = {
        "RA": "rain", "SN": "snow", "UP": "unknown_precip",
        "FG": "fog", "BR": "mist", "HZ": "haze", "TS": "thunderstorm",
        "GR": "hail", "GS": "small_hail", "FZRA": "freezing_rain"
    }

    while i < len(tokens) and any(code in tokens[i] for code in precip_dict):
        code = tokens[i]

        if code in precip_dict:
            Precipitation.append({
                "type": precip_dict[code],
            })
        i += 1

    # --- cloud cover ---
    # format: CCChhhh
    cloud_dict = {
        "CLR": "clear",
        "FEW": "few clouds",
        "SCT": "scattered clouds",
        "BKN": "broken clouds",
        "OVC": "overcast"
    }

    while i < len(tokens) and re.match(r"^(CLR|FEW|SCT|BKN|OVC)\d{0,3}$", tokens[i]):
        # print(tokens[i])
        match = re.match(r"^(CLR|FEW|SCT|BKN|OVC)(\d{3})?", tokens[i])
        if match:
            type_code = match.group(1)
            Clouds.append({
                "type": cloud_dict.get(type_code, "unknown"),
            })
        i += 1

    # --- temp/dp ---
    # format tt/dd
    if i < len(tokens) and "/" in tokens[i]:
        # print(tokens[i])
        temp_match = re.match(r"^(M?\d{1,2})/(M?\d{1,2})$", tokens[i])
        if temp_match:
            t, d = temp_match.groups()
            Temperature = -int(t[1:]) if t.startswith("M") else int(t)
            DewPoint = -int(d[1:]) if d.startswith("M") else int(d)

    # Returning as row for ease of adding to dataframe
    return Row(
        WindDirection=WindDirection,
        WindSpeed=WindSpeed,
        WindGusts=WindGusts,
        Visibility=Visibility,
        Precipitation=[f"{p['type']}" for p in Precipitation],
        Clouds=[f"{c['type']}" for c in Clouds],
        Temperature=Temperature,
        DewPoint=DewPoint    
    )

# Creating UDF to parse data from metar into the columns in the dataframe
parse_metar_string_udf = udf(parse_metar_string, weather_schema)

# Getting data from df needed for API calls and putting it in a pandas dataframe
# This is to hopefully speed it up

# Data from departure locations (will all be CLT)
origin_times_pd = df.select(
    col("OriginICAO").alias("ICAO"),
    col("CRSDepTimestamp").alias("Timestamp"),
    col("CRSDepTimestamp_UTC").alias("TimestampUTC")
).distinct().toPandas()

# Data from arrival locations
dest_times_pd = df.select(
    col("DestICAO").alias("ICAO"),
    col("CRSDepTimestamp").alias("Timestamp"),
    col("CRSDepTimestamp_UTC").alias("TimestampUTC")
).distinct().toPandas()

# Combining dataframes
airport_times_pd = pd.concat([origin_times_pd, dest_times_pd]).drop_duplicates()
print(airport_times_pd.head())

# Getting METAR data for each needed location/time
airport_times_pd["metar"] = airport_times_pd.apply(fetch_metar_for_row, axis=1)
print(airport_times_pd.head())

# Converting back to spark dataframe
weather_df = spark.createDataFrame(airport_times_pd)
weather_df.select("*").show(5, truncate=False)

# Joining METAR data to corresponding row with correct naming convention
origin_weather_df = weather_df.withColumnRenamed("metar", "OriginMetar")
df = df.join(
    origin_weather_df,
    (df.OriginICAO == origin_weather_df.ICAO) & 
    (df.CRSDepTimestamp_UTC == origin_weather_df.TimestampUTC),
    "left"
)

dest_weather_df = weather_df.withColumnRenamed("metar", "DestMetar")
df = df.join(
    dest_weather_df,
    (df.DestICAO == dest_weather_df.ICAO) & 
    (df.CRSDepTimestamp_UTC == dest_weather_df.TimestampUTC),
    "left"
)

df.select(
    "FlightDate",
    "OriginCityName",
    "OriginMetar",
    "DestCityName",
    "CRSDepTime",
    "DestMetar"
).show(5, truncate=False)

# Parsing Origin(CLT) weather
origin_weather = parse_metar_string_udf(col("OriginMetar")).alias("OriginWeather")
df = df.withColumn("OriginWeather", origin_weather)

# Expanding into seperate columns
origin_cols = [
    col(f"OriginWeather.{c}").alias(f"Origin{c}") 
    for c in weather_schema.fieldNames()
]
df = df.select("*", *origin_cols).drop("OriginWeather")


# Parsing Destination weather
dest_weather = parse_metar_string_udf(col("DestMetar")).alias("DestWeather")
df = df.withColumn("DestWeather", dest_weather)

# Expanding into seperate columns
dest_cols = [
    col(f"DestWeather.{c}").alias(f"Dest{c}") 
    for c in weather_schema.fieldNames()
]
df = df.select("*", *dest_cols).drop("DestWeather")

# Dropping repeated/unneeded columns
df = df.drop("ICAO", "Timestamp", "TimestampUTC", "_c0")

df.printSchema()
print('parquet write:')
df.write.parquet('data/sample/parquet',mode="overwrite")


spark.stop()