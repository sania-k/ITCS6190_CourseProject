import sys
import os
import json
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.functions import (
    col, when, size, concat_ws, floor, to_date, dayofweek, lit, monotonically_increasing_id
)

# ---------------------------------------------------------
# Spark init
# ---------------------------------------------------------
spark = (
    SparkSession.builder
    .appName("FlightPredictionDemo")
    .master("local[*]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
median_file_path = "data/median_fill_values.json"
model_path = "spark_gbt_model"
data_path = "data/sample/parquet_delay_and_weather_24"

print("\n--- LOADING ---")
print(model_path, data_path, median_file_path)

# ---------------------------------------------------------
# Load medians EXACTLY like backend
# ---------------------------------------------------------
if not os.path.exists(median_file_path):
    print(f"Missing {median_file_path}")
    sys.exit(1)

with open(median_file_path, "r") as f:
    median_fill_values = json.load(f)

model = PipelineModel.load(model_path)
df = spark.read.parquet(data_path)

# ---------------------------------------------------------
# PREPROCESSING (IDENTICAL TO BACKEND)
# ---------------------------------------------------------

# Fix incorrect name
if "Operating_Airline " in df.columns:
    df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# Time features
df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)

df = df.withColumn("UI_Dep_Time", (col("DepHour") * 60) + col("DepMinute"))

# Weekend feature (same dayofweek logic as backend)
df = df.withColumn("FlightDate", to_date(col("FlightDate")))
df = df.withColumn(
    "is_weekend",
    when((dayofweek(col("FlightDate")) == 1) | (dayofweek(col("FlightDate")) == 7), 1)
    .otherwise(0)
)

# Convert arrays to strings exactly like backend
weather_cols = [
    "OriginPrecipitation", "OriginClouds",
    "DestPrecipitation", "DestClouds"
]

for c in weather_cols:
    if c in df.columns:
        df = df.withColumn(
            c,
            when(col(c).isNull(), "None")
            .when(size(col(c)) == 0, "None")
            .otherwise(concat_ws(",", col(c)))
        )

# Fill numeric values using EXACT median JSON
for col_name, median_val in median_fill_values.items():
    if col_name in df.columns:
        df = df.fillna({col_name: float(median_val)})

# Ensure numeric columns exist
required = [
    "Year", "Month", "DayofMonth", "DayOfWeek",
    "OriginWindDirection", "OriginWindSpeed", "OriginVisibility",
    "DestWindDirection", "DestWindSpeed", "DestVisibility",
    "DepHour", "ArrHour", "DepMinute", "ArrMinute", "is_weekend"
]

for c in required:
    if c not in df.columns:
        df = df.withColumn(c, lit(0.0))

# ---------------------------------------------------------
# Predict
# ---------------------------------------------------------
print("\n--- PREDICTING ---")
preds = model.transform(df)

TARGET_DATE = "2024-01-06"

subset = preds.filter(col("FlightDate") == TARGET_DATE)

print(f"\nPredictions for {TARGET_DATE}")
print("-" * 120)
print(
    f"{'Origin':<6} {'Dest':<6} {'UI_Dep':<8} {'Prediction':<10} {'Prob':<15} {'CRSDepTime'}"
)
print("-" * 120)

rows = subset.select(
    "Origin", "Dest", "UI_Dep_Time",
    "prediction", "probability", "CRSDepTime"
).orderBy("UI_Dep_Time").collect()

for r in rows:
    prob = f"{r['probability'][1]:.3f}"
    status = "DELAYED" if r['prediction'] == 1 else "On Time"
    print(
        f"{r['Origin']:<6} {r['Dest']:<6} {str(r['UI_Dep_Time']):<8} {status:<10} {prob:<15} {r['CRSDepTime']}"
    )

print("-" * 120)
spark.stop()
