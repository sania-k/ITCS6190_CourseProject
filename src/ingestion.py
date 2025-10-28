from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, lpad, try_to_timestamp, to_utc_timestamp, concat_ws, lit, window, count, min, max
from pyspark.sql.types import StringType, IntegerType, DoubleType, FloatType, ArrayType, StructType, StructField, MapType
import time, requests, re, bisect
import pandas as pd
from datetime import datetime, timedelta
from metar_taf_parser.parser.parser import MetarParser

# Creating Spark Session
spark = SparkSession.builder.appName("AirportDelay").getOrCreate()


# --- Loading Delay Sample Data ---

# Loading delay dataset from sample data
df = spark.read.csv("flight_delay_jan_2025_clt_origin_major_dest.csv", header=True, inferSchema=True)

# df = df.limit(5)

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


# # what ur gonna do:
# use the from metar_taf_parser.parser.parser import MetarParser libary for parsing
# put the data into windows for less api calls
# seperate the response function from the getting nearest data function to make that work

# Create 60-day windows for airports
origin_timeframes = (
    df.withColumn("window", window("CRSDepTimestamp", "45 days"))
    .groupBy("OriginICAO", "window")
    .agg(
        min("CRSDepTimestamp").alias("start_date"),
        max("CRSDepTimestamp").alias("end_date"),
        count("*").alias("records")
    )
    .withColumn("Type", lit("Origin"))  # Label this set as Origin
)

# Create 60-day windows for Destination airports
dest_timeframes = (
    df.withColumn("window", window("CRSDepTimestamp", "45 days"))
    .groupBy("DestICAO", "window")
    .agg(
        min("CRSDepTimestamp").alias("start_date"),
        max("CRSDepTimestamp").alias("end_date"),
        count("*").alias("records")
    )
    .withColumn("Type", lit("Destination"))  # Label this set as Destination
)

# Standardize column names so both dataframes match
origin_timeframes = origin_timeframes.withColumnRenamed("OriginICAO", "ICAO")
dest_timeframes = dest_timeframes.withColumnRenamed("DestICAO", "ICAO")

# Combine both into one dataframe using union
timeframes_combined = origin_timeframes.union(dest_timeframes).orderBy("ICAO", "window.start")

# Show final combined result
timeframes_combined.show(truncate=False)


# --- Getting METAR weather data ---

# Functions
def generate_request_url(start_timestamp, end_timestamp,icao_code):
    """Returns a string: the API call URL for previous and current day
    to ensure weather data from before departure.

    timestamp(datetime) -> scheduled flight departure time (UTC)
    icao_code(string) -> ICAO code of the airport 
    """
    base = "https://flightsupport24.com/map/archive.php?"
    end = "&tz=Etc/UTC&format=onlytdf&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=2"
    
    if isinstance(start_timestamp, str):
        start_timestamp = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S")
    
    if isinstance(end_timestamp, str):
        end_timestamp = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

    # Start of date range
    # Going a day in case weather data before midnight flights is needed
    start = start_timestamp - timedelta(days=1)
    day1, month1, year1 = start.day, start.month, start.year

    # Current day
    # Date range doesn't include current day, have to go forward one
    end = end_timestamp + timedelta(days=1)
    day2, month2, year2 = end.day, end.month, end.year

    # Build URL
    request_URL = (
        f"{base}station={icao_code}&data=metar"
        f"&year1={year1}&month1={month1}&day1={day1}"
        f"&year2={year2}&month2={month2}&day2={day2}"
        f"{end}"
    )

    return request_URL

def get_metar_response_list(url):
    """Returns a list of metar data

    url(string): the request url for the api call    """

    try:
        time.sleep(0.25) #TODO: proper api rate limitings
        res = requests.get(url).text        

        metar_list = res.strip().splitlines()[1:] # Ignore first line, irrelevant data

        return metar_list

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
def get_departure_metar(metar_list,timestamp):
    """" Returns metar observation from right before the planned departure of a flight
    
    metar_list(list(string)): the list of metar strings
    timestamp(datetime): the planned departure time
    """

    time_pattern =  r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})"

    departure_metar = None
    left, right = 0, len(metar_list) - 1
    
    while left <= right:
        mid = (left+right) // 2
        line = metar_list[mid]
        
        match = re.search(time_pattern, line)
        
        if match:
            metar_timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")

            if metar_timestamp <= timestamp:
                departure_metar = line
                left = mid + 1 
            else:
                right = mid - 1
        else:
            return None

    departure_metar = " ".join(departure_metar.split()[3:])
    return departure_metar

def parse_metar_string(metar_line):
    '''Parsing string through use of python-metar-taf-parser library
    
    metar_line(str): metar observation string
    '''
    if not metar_line:
        return None
    
    data = MetarParser().parse(metar_line) # Creates metar object with observations

    # Result fields--only keeping what is relevant
    WindDirection= None     # in degrees from N
    WindSpeed= None         # in kts
    WindGusts= None         # in kts
    Visibility= None        # statute miles
    Precipitation= []       # type (category)
    Clouds= []              # type (category)
    Temperature= None       # deg C
    DewPoint= None          # deg C

    WindDirection = data._wind.degrees
    WindSpeed = data._wind.speed
    WindGusts = data._wind.gust

    # Visibility comes as a string like "5km" or "> 10km", must extract the number and cast
    vis_str = data._visibility.distance

    match = re.search(r'\d+', vis_str)
    if match:
        Visibility = int(match.group())

    # Weather conditions/precip is in a list of weather_condition objects
    # Must extract the category needed

    weather_cond_list = data._weather_conditions

    for cond in weather_cond_list: # Combining the description and phenomenon for category
        desc = getattr(cond, "_descriptive", None)
        phenoms = getattr(cond, "_phenomenons", [])

        desc_str = desc.name.lower() if hasattr(desc, "name") else str(desc).lower() if desc else ""
        phenoms_str = " ".join(p.name.lower() if hasattr(p, "name") else str(p).lower() for p in phenoms)

        combo = " ".join(filter(None, [desc_str, phenoms_str]))
        Precipitation.append(combo)
        

    # Cloud list is in a list of cloud objects
    # Must extract the cloud type from the list
    clouds_list = data._clouds

    for cloud in clouds_list:
        quantity = getattr(cloud, "_quantity", None)
        
        if quantity:
            Clouds.append(quantity)

    Temperature = data._temperature

    DewPoint = data._dew_point

    # Returning object as a list
    return Row(
        WindDirection,
        WindSpeed,
        WindGusts,
        Visibility,
        Precipitation,
        Clouds,
        Temperature,
        DewPoint    
    )

# INCOMPLETE

# todo: create logic of:
# making api calls on window -> getting metar data for each line in df -> parsing




# departure_metar = 'CLT	2025-10-01 17:52	KTTN 051853Z 04011KT 9999 VCTS SN FZFG BKN003 OVC010 M02/M02 A3006'


# departure_metar = " ".join(departure_metar.split()[3:])

# print(departure_metar)

# wayugh = parse_metar_string(departure_metar)

# print(wayugh)


spark.stop()