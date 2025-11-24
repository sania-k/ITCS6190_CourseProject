from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, lpad, try_to_timestamp, to_utc_timestamp, concat_ws, lit, window, count, min, max
from pyspark.sql.types import StringType, IntegerType, DoubleType, FloatType, ArrayType, StructType, StructField, MapType
import time, requests, re
from datetime import datetime, timedelta
from collections import defaultdict
from metar_taf_parser.parser.parser import MetarParser
import os

# Create Spark session
spark = SparkSession.builder.appName("AirportDelay").getOrCreate()

# -----------------------------------------------------------
# Resolve paths relative to project root (portable for Docker)
# -----------------------------------------------------------
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(project_root, "data", "sample", "flight_delay_aug2024_jul2025.csv")

# Output parquet path
parquet_output_path = os.path.join(
    project_root, "data", "sample", "parquet_delay_and_weather_25"
)

print("Loading CSV from:", csv_path)
print("Writing parquet to:", parquet_output_path)

# Load CSV
df = spark.read.csv(csv_path, header=True, inferSchema=True)

# Debug checks
df.printSchema()
df.select(
    "FlightDate", "OriginAirportID", "OriginCityName",
    "DestAirportID", "DestCityName", "CRSDepTime", "CRSArrTime"
).show(5, truncate=False)

# -----------------------------------------------------------
# Airport metadata table
# -----------------------------------------------------------
airport_df = spark.createDataFrame([
    (10397, "KATL", "America/New_York"),
    (11298, "KDFW", "America/Chicago"),
    (11292, "KDEN", "America/Denver"),
    (13930, "KORD", "America/Chicago"),
    (12892, "KLAX", "America/Los_Angeles"),
    (12478, "KJFK", "America/New_York"),
    (11057, "KCLT", "America/New_York"),
    (12889, "KLAS", "America/Los_Angeles"),
    (13204, "KMCO", "America/New_York"),
    (13303, "KMIA", "America/New_York")
], ["AirportID", "ICAO", "Timezone"])

# airport_df.show()

# -----------------------------------------------------------
# Join airport metadata
# -----------------------------------------------------------
df = df.join(
    airport_df.withColumnRenamed("AirportID", "OriginAirportID")
              .withColumnRenamed("Timezone", "OriginTimezone")
              .withColumnRenamed("ICAO", "OriginICAO"),
    on="OriginAirportID",
    how="inner"
)

df = df.join(
    airport_df.withColumnRenamed("AirportID", "DestAirportID")
              .withColumnRenamed("Timezone", "DestTimezone")
              .withColumnRenamed("ICAO", "DestICAO"),
    on="DestAirportID",
    how="inner"
)

# df.show(5)

# -----------------------------------------------------------
# Create timestamps
# -----------------------------------------------------------
df = df.withColumn(
    "CRSDepTimestamp",
    try_to_timestamp(
        concat_ws(" ", col("FlightDate"), lpad(col("CRSDepTime"), 4, "0")),
        lit("yyyy-MM-dd HHmm")
    )
)

df = df.withColumn(
    "CRSArrTimestamp",
    try_to_timestamp(
        concat_ws(" ", col("FlightDate"), lpad(col("CRSArrTime"), 4, "0")),
        lit("yyyy-MM-dd HHmm")
    )
)

df.select("FlightDate", "CRSDepTime", "CRSDepTimestamp").show(5, truncate=False)

# -----------------------------------------------------------
# Build METAR request windows (60-day chunks)
# -----------------------------------------------------------
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

origin_timeframes = origin_timeframes.withColumnRenamed("OriginICAO", "ICAO")
dest_timeframes = dest_timeframes.withColumnRenamed("DestICAO", "ICAO")

timeframes_df = origin_timeframes.union(dest_timeframes).orderBy("ICAO", "window.start")

# timeframes_df.show(truncate=False)

# -----------------------------------------------------------
# METAR API helpers
# -----------------------------------------------------------
def generate_request_url(start_timestamp, end_timestamp, icao_code):
    base = "https://flightsupport24.com/map/archive.php?"
    end = "&tz=Etc/UTC&format=onlytdf&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=2"

    if isinstance(start_timestamp, str):
        start_timestamp = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S")

    if isinstance(end_timestamp, str):
        end_timestamp = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

    interval_start = start_timestamp - timedelta(days=1)
    interval_end = end_timestamp + timedelta(days=1)

    return (
        f"{base}station={icao_code}&data=metar"
        f"&year1={interval_start.year}&month1={interval_start.month}&day1={interval_start.day}"
        f"&year2={interval_end.year}&month2={interval_end.month}&day2={interval_end.day}"
        f"{end}"
    )

def get_response_list(url):
    try:
        time.sleep(0.25)
        res = requests.get(url).text
        return res.strip().splitlines()[1:]
    except:
        return None

def get_metar_response(start_timestamp, end_timestamp, icao_code):
    url = generate_request_url(start_timestamp, end_timestamp, icao_code)
    return get_response_list(url)

# -----------------------------------------------------------
# Broadcast METAR lookups
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# Schema and parsing functions
# -----------------------------------------------------------
weather_schema = StructType([
    StructField("WindDirection", IntegerType(), True),
    StructField("WindSpeed", IntegerType(), True),
    StructField("WindGusts", IntegerType(), True),
    StructField("Visibility", DoubleType(), True),
    StructField("Precipitation", ArrayType(StringType()), True),
    StructField("Clouds", ArrayType(StringType()), True),
    StructField("Temperature", DoubleType(), True),
    StructField("DewPoint", DoubleType(), True),
])

def get_departure_metar(timestamp, icao):
    time_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})"
    data = broadcast_metar_lookup.value.get(icao, [])
    departure_metar = None

    for window in data:
        if window["start"] <= timestamp <= window["end"]:
            metar_list = window["response"]
            left, right = 0, len(metar_list) - 1

            while left <= right:
                mid = (left + right) // 2
                line = metar_list[mid]

                match = re.search(time_pattern, line)
                if match:
                    metar_timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")

                    if metar_timestamp <= timestamp:
                        departure_metar = " ".join(line.split()[3:])
                        left = mid + 1
                    else:
                        right = mid - 1
            break

    return departure_metar

def parse_metar_string(metar_line):
    if not metar_line:
        return None

    try:
        data = MetarParser().parse(metar_line)

        WindDirection = getattr(data._wind, "degrees", None)
        WindSpeed = getattr(data._wind, "speed", None)
        WindGusts = getattr(data._wind, "gust", None)

        Visibility = None
        vis_str = getattr(data, "_visibility", None)
        match = re.search(r'\d+', str(vis_str))
        if match:
            Visibility = float(match.group())

        Precipitation = []
        for cond in getattr(data, "_weather_conditions", None):
            desc = getattr(cond, "_descriptive", None)
            phenoms = getattr(cond, "_phenomenons", [])
            desc_str = desc.name.lower() if hasattr(desc, "name") else ""
            phenoms_str = " ".join(p.name.lower() for p in phenoms)
            Precipitation.append(" ".join(filter(None, [desc_str, phenoms_str])))

        Clouds = []
        for cloud in getattr(data, "_clouds", None):
            quantity = getattr(cloud, "_quantity", None)
            if quantity:
                Clouds.append(str(quantity))

        Temperature = getattr(data, "_temperature", None)
        DewPoint = getattr(data, "_dew_point", None)

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

    except Exception as e:
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

# -----------------------------------------------------------
# Apply UDFs
# -----------------------------------------------------------
origin_weather = get_and_parse_metar_udf(col("CRSDepTimestamp"), col("OriginICAO"))
df = df.withColumn("OriginWeather", origin_weather)

origin_cols = [
    col(f"OriginWeather.{c}").alias(f"Origin{c}")
    for c in weather_schema.fieldNames()
]
df = df.select("*", *origin_cols).drop("OriginWeather")

dest_weather = get_and_parse_metar_udf(col("CRSDepTimestamp"), col("DestICAO"))
df = df.withColumn("DestWeather", dest_weather)

dest_cols = [
    col(f"DestWeather.{c}").alias(f"Dest{c}")
    for c in weather_schema.fieldNames()
]
df = df.select("*", *dest_cols).drop("DestWeather")

df = df.drop("ICAO", "Timestamp", "TimestampUTC", "_c0")

df.printSchema()

# -----------------------------------------------------------
# Write Parquet to correct folder
# -----------------------------------------------------------
df.write.parquet(parquet_output_path, mode="overwrite")

spark.stop()