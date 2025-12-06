import socket
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, lpad, from_json, try_to_timestamp, concat_ws, lit, window, count, min, max, explode
from pyspark.sql.types import StringType, IntegerType, DoubleType, DateType, ArrayType, StructType, StructField, TimestampType, MapType

HOST = "localhost"
PORT = 9998

# Creating Spark Session
spark = SparkSession.builder.appName("AirportDelay").getOrCreate()

# Defining schema for json stream
record_schema = StructType([
    StructField("DestAirportID", IntegerType(), True),
    StructField("OriginAirportID", IntegerType(), True),
    StructField("Year", IntegerType(), True),
    StructField("Month", IntegerType(), True),
    StructField("DayofMonth", IntegerType(), True),
    StructField("DayOfWeek", IntegerType(), True),
    StructField("FlightDate", DateType(), True),
    StructField("Marketing_Airline_Network", StringType(), True),
    StructField("DOT_ID_Marketing_Airline", IntegerType(), True),
    StructField("Operating_Airline", StringType(), True),
    StructField("DOT_ID_Operating_Airline", IntegerType(), True),
    StructField("Flight_Number_Operating_Airline", IntegerType(), True),
    StructField("OriginAirportSeqID", IntegerType(), True),
    StructField("OriginCityMarketID", IntegerType(), True),
    StructField("Origin", StringType(), True),
    StructField("OriginCityName", StringType(), True),
    StructField("DestAirportSeqID", IntegerType(), True),
    StructField("DestCityMarketID", IntegerType(), True),
    StructField("Dest", StringType(), True),
    StructField("DestCityName", StringType(), True),
    StructField("CRSDepTime", IntegerType(), True),
    StructField("DepTime", DoubleType(), True),
    StructField("DepDelay", DoubleType(), True),
    StructField("DepDelayMinutes", DoubleType(), True),
    StructField("DepDel15", DoubleType(), True),
    StructField("DepartureDelayGroups", DoubleType(), True),
    StructField("DepTimeBlk", StringType(), True),
    StructField("TaxiOut", DoubleType(), True),
    StructField("WheelsOff", DoubleType(), True),
    StructField("WheelsOn", DoubleType(), True),
    StructField("TaxiIn", DoubleType(), True),
    StructField("CRSArrTime", IntegerType(), True),
    StructField("ArrTime", DoubleType(), True),
    StructField("ArrDelay", DoubleType(), True),
    StructField("ArrDelayMinutes", DoubleType(), True),
    StructField("ArrDel15", DoubleType(), True),
    StructField("ArrivalDelayGroups", DoubleType(), True),
    StructField("ArrTimeBlk", StringType(), True),
    StructField("Cancelled", DoubleType(), True),
    StructField("CancellationCode", StringType(), True),
    StructField("Diverted", DoubleType(), True),
    StructField("CarrierDelay", DoubleType(), True),
    StructField("WeatherDelay", DoubleType(), True),
    StructField("NASDelay", DoubleType(), True),
    StructField("SecurityDelay", DoubleType(), True),
    StructField("LateAircraftDelay", DoubleType(), True),
    StructField("OriginICAO", StringType(), True),
    StructField("OriginTimezone", StringType(), True),
    StructField("DestICAO", StringType(), True),
    StructField("DestTimezone", StringType(), True),
    StructField("CRSDepTimestamp", TimestampType(), True),
    StructField("CRSArrTimestamp", TimestampType(), True),
    StructField("CRSDepTimestamp_UTC", TimestampType(), True),
    StructField("CRSArrTimestamp_UTC", TimestampType(), True),
    StructField("OriginMetar", StringType(), True),
    StructField("DestMetar", StringType(), True),
    StructField("OriginWindDirection", IntegerType(), True),
    StructField("OriginWindSpeed", IntegerType(), True),
    StructField("OriginWindGusts", IntegerType(), True),
    StructField("OriginVisibility", DoubleType(), True),
    StructField("OriginPrecipitation", ArrayType(StringType(), True), True),
    StructField("OriginClouds", ArrayType(StringType(), True), True),
    StructField("OriginTemperature", DoubleType(), True),
    StructField("OriginDewPoint", DoubleType(), True),
    StructField("DestWindDirection", IntegerType(), True),
    StructField("DestWindSpeed", IntegerType(), True),
    StructField("DestWindGusts", IntegerType(), True),
    StructField("DestVisibility", DoubleType(), True),
    StructField("DestPrecipitation", ArrayType(StringType(), True), True),
    StructField("DestClouds", ArrayType(StringType(), True), True),
    StructField("DestTemperature", DoubleType(), True),
    StructField("DestDewPoint", DoubleType(), True)
])


outer_schema = StructType([
    StructField("window_start", StringType(), True),
    StructField("num_records", IntegerType(), True),
    StructField("records", ArrayType(record_schema), True)
])

# Read streaming data from the socket
raw_stream = spark.readStream.format("socket") \
    .option("host", HOST) \
    .option("port", PORT) \
    .load()

# Parse JSON into structured format
parsed_stream = raw_stream.select(from_json(col("value"), outer_schema).alias("json"))

# Flatten the 'records' array into individual rows
flights_df = parsed_stream.select(explode(col("json.records")).alias("data")) \
    .select("data.*")

# Show some columns in console
output_df = flights_df.select(
    "FlightDate",
    "OriginAirportID",
    "OriginCityName",
    "OriginTemperature",
    "OriginWindSpeed",
    "OriginVisibility",
    "OriginPrecipitation",
    "DestAirportID",
    "DestCityName",
    "DestTemperature",
    "DestWindSpeed",
    "DestVisibility",
    "DestPrecipitation",
    "CRSDepTimestamp",
    "WeatherDelay"
)

query = output_df.writeStream \
    .format("console") \
    .outputMode("append") \
    .option("truncate", False) \
    .start()

query.awaitTermination()