import sys
from pyspark.sql import SparkSession
from pyspark.ml.pipeline import PipelineModel # Assuming you saved a Pipeline
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import functions as F
import pandas as pd

pipeline_path = "../notebooks/spark_gbt_model"

spark = SparkSession.builder.appName("PredictFlightDelay").getOrCreate()

# Load the pipeline model
loaded_pipeline_model = PipelineModel.load(pipeline_path)

input_schema = StructType([
    StructField("FlightDate", StringType(), True),
    StructField("OriginAirportID", IntegerType(), True),
    StructField("OriginCityName", StringType(), True),
    StructField("OriginTemperature", DoubleType(), True),
    StructField("OriginWindSpeed", DoubleType(), True),
    StructField("OriginVisibility", DoubleType(), True),
    StructField("OriginPrecipitation", StringType(), True),
    StructField("DestAirportID", IntegerType(), True),
    StructField("DestCityName", StringType(), True),
    StructField("DestTemperature", DoubleType(), True),
    StructField("DestWindSpeed", DoubleType(), True),
    StructField("DestVisibility", DoubleType(), True),
    StructField("DestPrecipitation", StringType(), True),
    StructField("CRSDepTimestamp", StringType(), True),
    StructField("WeatherDelay", DoubleType(), True),
    StructField("Marketing_Airline_Network", StringType(), True), 
    StructField("Operating_Airline", StringType(), True),
    StructField("Origin", StringType(), True),
    StructField("Dest", StringType(), True),  
    StructField("OriginClouds", StringType(), True),
    StructField("DestClouds", StringType(), True),
    StructField("OriginWindDirection", DoubleType(), True), 
    StructField("DestWindDirection", DoubleType(), True),
    StructField("CRSArrTime", IntegerType(), True)
])

print("--- Using provided input data row for prediction ---")

# The specific input data you provided in your prompt, structured as a list of tuples:
user_input_data = [
    ('2024-08-01', 11057, 'Charlotte, NC', None, None, 10.0, '[]', 
     13303, 'Miami, FL', None, None, 10.0, '[]', '2024-08-01 09:30:00', None, 
     'AA', 'AA_Operating', 'CLT', 'MIA', 'FEW', 'FEW', None, None, 1130)
]

# 4. Create a Spark DataFrame from the single user input row
input_df = spark.createDataFrame(user_input_data, schema=input_schema)

input_df = input_df.withColumn(
    "CRSDepTimestamp_ts", F.to_timestamp(F.col("CRSDepTimestamp"), "yyyy-MM-dd HH:mm:ss")
).withColumn("Year", F.year(F.col("CRSDepTimestamp_ts"))
).withColumn("Month", F.month(F.col("CRSDepTimestamp_ts"))
).withColumn("DayofMonth", F.dayofmonth(F.col("CRSDepTimestamp_ts"))
).withColumn("DayOfWeek", F.dayofweek(F.col("CRSDepTimestamp_ts"))
).withColumn("CRSDepTime_Str", F.concat(F.lpad(F.hour(F.col("CRSDepTimestamp_ts")), 2, '0'), F.lpad(F.minute(F.col("CRSDepTimestamp_ts")), 2, '0'))
).withColumn("CRSDepTime", F.col("CRSDepTime_Str").cast(IntegerType())
).drop("CRSDepTime_Str").withColumn("DepHour", F.hour(F.col("CRSDepTimestamp_ts"))
).withColumn(
    "ArrHour",
    F.floor(F.col("CRSArrTime") / 100).cast(IntegerType())
).withColumn( 
    "DepMinute",
    F.minute(F.col("CRSDepTimestamp_ts"))
).withColumn( 
    "ArrMinute",
    F.col("CRSArrTime") % 100
).withColumn( 
    "is_weekend",
    F.col("DayOfWeek").isin([1, 7]) # Sunday is 1, Saturday is 7 in Spark's dayofweek
)

cols_to_fill_numeric = ["OriginTemperature", "OriginWindSpeed", "DestTemperature", "DestWindSpeed", "OriginWindDirection", "DestWindDirection"]
input_df = input_df.fillna(0.0, subset=cols_to_fill_numeric)

cols_to_fill_string = ["Marketing_Airline_Network", "Operating_Airline", "Origin", "Dest", "OriginClouds", "DestClouds", "OriginPrecipitation", "DestPrecipitation"]
input_df = input_df.fillna('UNKNOWN', subset=cols_to_fill_string)

print("\nInput DataFrame:")
input_df.show()

predictions = loaded_pipeline_model.transform(input_df)

print("Prediction Results:")
predictions.select("OriginCityName", "DestCityName", "prediction", "probability").show(truncate=False)

spark.stop()