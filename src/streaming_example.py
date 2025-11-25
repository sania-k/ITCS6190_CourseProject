import socket
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, lpad, from_json, try_to_timestamp, concat_ws, lit, window, count, min, max, explode, expr
from pyspark.sql.types import StringType, IntegerType, DoubleType, DateType, ArrayType, StructType, StructField, TimestampType, MapType

from pyspark.ml.pipeline import PipelineModel
import pyspark.sql.functions as F


HOST = "localhost"
PORT = 9995

# -------------------------
# Create Spark Session
# -------------------------
spark = SparkSession.builder.appName("AirportDelayPredictions").getOrCreate()

# -------------------------
# Load your trained pipeline
# -------------------------
pipeline_path = "../notebooks/spark_gbt_model"
loaded_pipeline_model = PipelineModel.load(pipeline_path)


# -------------------------
# Existing Schema
# -------------------------
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


# -------------------------
# Streaming Socket Input
# -------------------------
raw_stream = spark.readStream.format("socket") \
    .option("host", HOST) \
    .option("port", PORT) \
    .load()

parsed_stream = raw_stream.select(from_json(col("value"), outer_schema).alias("json"))

flights_df = parsed_stream.select(explode(col("json.records")).alias("data")).select("data.*")


# ---------------------------------------------------------------
# Minimal preprocessing so your pipeline accepts the streaming rows
# ---------------------------------------------------------------
model_ready_df = flights_df \
    .withColumn("CRSDepTimestamp_ts", F.col("CRSDepTimestamp")) \
    .withColumn("Year", F.year("CRSDepTimestamp_ts")) \
    .withColumn("Month", F.month("CRSDepTimestamp_ts")) \
    .withColumn("DayofMonth", F.dayofmonth("CRSDepTimestamp_ts")) \
    .withColumn("DayOfWeek", F.dayofweek("CRSDepTimestamp_ts")) \
    .withColumn("CRSDepTime_Str",
        F.concat(F.lpad(F.hour("CRSDepTimestamp_ts"), 2, '0'),
                 F.lpad(F.minute("CRSDepTimestamp_ts"), 2, '0'))
    ) \
    .withColumn("CRSDepTime", F.col("CRSDepTime_Str").cast(IntegerType())) \
    .drop("CRSDepTime_Str") \
    .withColumn("DepHour", F.hour("CRSDepTimestamp_ts")) \
    .withColumn("ArrHour", F.floor(F.col("CRSArrTime")/100)) \
    .withColumn("DepMinute", F.minute("CRSDepTimestamp_ts")) \
    .withColumn("ArrMinute", F.col("CRSArrTime") % 100) \
    .withColumn("is_weekend", F.col("DayOfWeek").isin([1,7]))


# -------------------------
# FILL missing values
# -------------------------
num_fill = ["OriginTemperature","OriginWindSpeed","DestTemperature",
            "DestWindSpeed","OriginWindDirection","DestWindDirection"]

str_fill = ["Marketing_Airline_Network","Operating_Airline","Origin","Dest",
            "OriginClouds","DestClouds","OriginPrecipitation","DestPrecipitation"]

model_ready_df = model_ready_df.fillna(0.0, subset=num_fill).fillna("UNKNOWN", subset=str_fill)


# -------------------------
# Apply model to each microbatch
# -------------------------
def predict_batch(batch_df, batch_id):
    if batch_df.count() == 0:
        return
    batch_df = (
    batch_df
    .withColumn("OriginPrecipitation",  expr("get(OriginPrecipitation, 0)"))
    .withColumn("OriginClouds",         expr("get(OriginClouds, 0)"))
    .withColumn("DestPrecipitation",    expr("get(DestPrecipitation, 0)"))
    .withColumn("DestClouds",           expr("get(DestClouds, 0)"))
)
    preds = loaded_pipeline_model.transform(batch_df)
    preds.select(
        "OriginCityName",
        "DestCityName",
        "CRSDepTimestamp",
        "prediction",
        "probability"
    ).show(truncate=False)


query = model_ready_df.writeStream \
    .foreachBatch(predict_batch) \
    .outputMode("append") \
    .start()

query.awaitTermination()
