from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, lpad, try_to_timestamp, to_utc_timestamp, concat_ws, lit, window, count, min, max
from pyspark.sql.types import StringType, IntegerType, DoubleType, FloatType, ArrayType, StructType, StructField, MapType
import time, requests, re
from datetime import datetime, timedelta
from collections import defaultdict
from metar_taf_parser.parser.parser import MetarParser

# Creating Spark Session
spark = SparkSession.builder.appName("AirportDelay").getOrCreate()


# Loading Delay Sample Data 
df = spark.read.csv("data/sample/flight_delay_2024.csv", header=True, inferSchema=True)

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



# Adding Timestamps

# Airport dataframe to join with delay data for airport data needed for API lookups:
# Contains top 10 airports in the US, the only airports in the database at the moment
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
    (11057, "KCLT", "America/New_York"), # Charlotte, NC: Charlotte Douglas International
    (12889, "KLAS", "America/Los_Angeles"), # Las Vegas, NV
    (13204, "KMCO", "America/New_York"), # Orlando, FL
    (13303, "KMIA", "America/New_York") # Miami, FL
], ["AirportID", "ICAO", "Timezone"])

airport_df.select("AirportID", "ICAO", "Timezone").show()

# Joining airport data with delay data
# For origin airport
df = df.join(  
    airport_df.withColumnRenamed("AirportID", "OriginAirportID")
              .withColumnRenamed("Timezone", "OriginTimezone")
              .withColumnRenamed("ICAO", "OriginICAO"),
    on="OriginAirportID",
    how="inner"
)

# For destination airport
df = df.join(airport_df.withColumnRenamed("AirportID", "DestAirportID")
              .withColumnRenamed("Timezone", "DestTimezone")
              .withColumnRenamed("ICAO", "DestICAO"),
    on="DestAirportID",
    how="inner"
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

# Confirming Columns
df.select(
    "FlightDate",
    "CRSDepTime",
    "CRSDepTimeStamp",
).show(5, truncate=False)



#  Adding METAR Data

# Making 60 day windows for airports, grouped by location to minimize the amount of API called
# 60 days is the maximum date range for the api

origin_timeframes = (
    df.withColumn("window", window("CRSDepTimestamp", "60 days"))
    .groupBy("OriginICAO", "window")
    .agg(
        min("CRSDepTimestamp").alias("start_date"),
        max("CRSDepTimestamp").alias("end_date"),
        count("*").alias("records")
    )
    .withColumn("Type", lit("Origin"))
)

dest_timeframes = (
    df.withColumn("window", window("CRSDepTimestamp", "60 days"))
    .groupBy("DestICAO", "window")
    .agg(
        min("CRSDepTimestamp").alias("start_date"),
        max("CRSDepTimestamp").alias("end_date"),
        count("*").alias("records")
    )
    .withColumn("Type", lit("Destination"))  
)

# Merging dest and origin into one df for consolidation

origin_timeframes = origin_timeframes.withColumnRenamed("OriginICAO", "ICAO")
dest_timeframes = dest_timeframes.withColumnRenamed("DestICAO", "ICAO")

timeframes_df = origin_timeframes.union(dest_timeframes).orderBy("ICAO", "window.start")

# Show final combined result
timeframes_df.show(truncate=False)


# Calling METAR weather data api 

# Helper functions for api calls
def generate_request_url(start_timestamp, end_timestamp, icao_code):
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
    interval_start = start_timestamp - timedelta(days=1)
    day1, month1, year1 = interval_start.day, interval_start.month, interval_start.year

    # End of date range
    # Date range doesn't include current day, have to go forward one
    interval_end = end_timestamp + timedelta(days=1)
    day2, month2, year2 = interval_end.day, interval_end.month, interval_end.year

    # Build URL
    request_URL = (
        f"{base}station={icao_code}&data=metar"
        f"&year1={year1}&month1={month1}&day1={day1}"
        f"&year2={year2}&month2={month2}&day2={day2}"
        f"{end}"
    )

    return request_URL

def get_response_list(url):
    """Returns a list of metar data

    url(string): the request url for the api call
    """

    try:
        time.sleep(0.25) #TODO: proper api rate limitings
        res = requests.get(url).text        

        metar_list = res.strip().splitlines()[1:] # Ignore first line, irrelevant data
        return metar_list

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def get_metar_response(start_timestamp, end_timestamp,icao_code):
    """ Makes url and api call, returns list of metar data

    timestamp(datetime) -> scheduled flight departure time (UTC)
    icao_code(string) -> ICAO code of the airport 
    """
    url = generate_request_url(start_timestamp, end_timestamp, icao_code)
    return get_response_list(url)


# Broadcasting results for faster lookup for the greater dataframe
metar_lookup = defaultdict(list)

for row in timeframes_df.collect():
    start, end, icao = row['start_date'], row['end_date'], row['ICAO']
    response = get_metar_response(start, end, icao)
    metar_lookup[icao].append({
        "start": start,
        "end": end,
        "response": response
    })

broadcast_metar_lookup = spark.sparkContext.broadcast(metar_lookup)

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

# Helper functions for search and parsing of metar data
def get_departure_metar(timestamp, icao):
    """" Returns metar observation from right before the planned departure of a flight
    
    timestamp(datetime): the planned departure time
    icao(string): the origin or destination of the flight
    """

    time_pattern =  r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})"
    data = broadcast_metar_lookup.value.get(icao, [])
    departure_metar = None

    # Finding the correct window (time + location) where the metar data for a specific row/flight
    # will be stored
    for window in data:
        if window["start"] <= timestamp <= window["end"]: 
            # On the correct list of metar responses, doing a binary search to more quickly
            # find the correct row of metar data before the flight
            # TODO: look into a better search method          
            metar_list = window["response"]
            left, right = 0, len(metar_list) - 1
            
            while left <= right:
                mid = (left+right) // 2
                line = metar_list[mid]
                
                match = re.search(time_pattern, line)
                
                if match:
                    metar_timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")

                    if metar_timestamp <= timestamp:
                        departure_metar = " ".join(line.split()[3:])
                        left = mid + 1 
                    else:
                        right = mid - 1
                else:
                    continue

            break

    return departure_metar

def parse_metar_string(metar_line):
    '''Parsing string through use of python-metar-taf-parser library
    
    metar_line(str): metar observation string
    '''
    if not metar_line:
        return None
    
    try:
        data = MetarParser().parse(metar_line)

        WindDirection = getattr(data._wind,"degrees", None)
        WindSpeed = getattr(data._wind,"speed", None)
        WindGusts = getattr(data._wind,"gust", None)

        # Visibility comes as a string like "5km" or "> 10km", must extract the number and cast
        Visibility = None

        vis_str = getattr(data,"_visibility", None)

        match = re.search(r'\d+', str(vis_str))
        if match:
            Visibility = float(match.group())

        # Weather conditions/precip is in a list of weather_condition objects
        # Must extract the category needed
        Precipitation = []

        # Combining the description and phenomenon for category
        for cond in getattr(data,"_weather_conditions",None): 
            desc = getattr(cond, "_descriptive", None)
            phenoms = getattr(cond, "_phenomenons", [])

            desc_str = desc.name.lower() if hasattr(desc, "name") else str(desc).lower() if desc else ""
            phenoms_str = " ".join(
                p.name.lower() if hasattr(p, "name") else str(p).lower() for p in phenoms
                )

            combo = " ".join(filter(None, [desc_str, phenoms_str]))
            Precipitation.append(combo)

        # Cloud list is in a list of cloud objects
        # Must extract the cloud type from the object
        Clouds = []

        cloud_map = {
            "CLR": "clear",
            "FEW": "few",
            "SCT": "scattered",
            "BKN": "broken",
            "OVC": "overcast"
        }

        for cloud in getattr(data, "_clouds", None) or []:
            quantity_obj = getattr(cloud, "_quantity", None)

            if quantity_obj:
                qty = getattr(quantity_obj, "name", str(quantity_obj))
                qty = qty.upper()

                friendly = cloud_map.get(qty, qty.lower())
                Clouds.append(friendly)
        
        # Temperature
        Temperature = getattr(data, "_temperature", None)
        Temperature = float(Temperature) if Temperature else None
        
        # Dew point
        
        DewPoint = getattr(data, "_dew_point", None)
        DewPoint = float(DewPoint) if DewPoint else None

        # Returning object as a list
        row = Row(
            WindDirection,
            WindSpeed,
            WindGusts,
            Visibility,
            Precipitation,
            Clouds,
            Temperature,
            DewPoint    
        )
        
        return row
    
    except Exception as e:
        # Skip unparsable lines
        if "invalid literal for int() with base 10" in str(e):
            print(f"Skipping malformed METAR: {metar_line}")
        else:
            print(f"Error parsing METAR: {metar_line}\n{e}")
        return None

    

def get_and_parse_metar(timestamp, icao):
    """Returns row of weather data parsed from metar observation based on the time/location of the flight
    
    timestamp(datetime): the planned departure time
    icao(string): the origin or destination of the flight
    """
    metar_line = get_departure_metar(timestamp, icao)
    return parse_metar_string(metar_line)

get_and_parse_metar_udf = udf(get_and_parse_metar, weather_schema)

# Getting Origin(CLT) weather
origin_weather = get_and_parse_metar_udf(col("CRSDepTimeStamp"), col("OriginICAO")).alias("OriginWeather")
df = df.withColumn("OriginWeather", origin_weather)

# Expanding into separate columns
origin_cols = [
    col(f"OriginWeather.{c}").alias(f"Origin{c}") 
    for c in weather_schema.fieldNames()
]
df = df.select("*", *origin_cols).drop("OriginWeather")


# Getting Destination weather
dest_weather = get_and_parse_metar_udf(col("CRSDepTimeStamp"), col("DestICAO")).alias("DestWeather")
df = df.withColumn("DestWeather", dest_weather)

# Expanding into separate columns
dest_cols = [
    col(f"DestWeather.{c}").alias(f"Dest{c}") 
    for c in weather_schema.fieldNames()
]
df = df.select("*", *dest_cols).drop("DestWeather")

# Dropping repeated/unneeded columns
df = df.drop("ICAO", "Timestamp", "TimestampUTC", "_c0")

df.printSchema()
df.write.parquet('../data/sample/parquet_delay_and_weather_24',mode="overwrite")

spark.stop()