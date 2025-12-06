# # # from pyspark.sql import SparkSession
# # # from pyspark.ml import PipelineModel
# # # from pyspark.sql.functions import col, when, size, concat_ws, floor, to_date, dayofweek, lit

# # # # 1. Initialize Spark (Using parentheses avoids indentation errors)
# # # spark = (SparkSession.builder
# # #     .appName("FlightPredictionDemo")
# # #     .master("local[*]")
# # #     .getOrCreate())

# # # spark.sparkContext.setLogLevel("ERROR")

# # # # 2. Load your saved model
# # # # (The git log showed this folder name, so this path should be correct)
# # # model_path = "spark_gbt_model"
# # # print(f"Loading model from {model_path}...")

# # # model = PipelineModel.load(model_path)

# # # # 3. Load some data to test
# # # # UPDATE THIS PATH to point to your actual CSV file
# # # data_path = "data/sample/parquet_delay_and_weather_24"
# # # print(f"Loading data from {data_path}...")

# # # # Load data (assuming headers exist)
# # # df = spark.read.parquet(data_path)

# # # print("Preprocessing data to match Model requirements...")

# # # # 1. FIX COLUMN NAMES (Remove trailing space)
# # # if "Operating_Airline " in df.columns:
# # #     df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# # # # 2. FEATURE ENGINEERING (Time & Weekend)
# # # # The model needs these columns, but they aren't in the raw parquet file.
# # # df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
# # # df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
# # # df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
# # # df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)

# # # # Create is_weekend (1 = Sun/Sat, 0 = Weekday)
# # # # Note: Spark dayofweek returns 1 for Sunday, 7 for Saturday
# # # df = df.withColumn("FlightDate", to_date(col("FlightDate")))
# # # df = df.withColumn("is_weekend", 
# # #     when((dayofweek(col("FlightDate")) == 1) | (dayofweek(col("FlightDate")) == 7), 1)
# # #     .otherwise(0)
# # # )

# # # # 3. PROCESS ARRAY COLUMNS (Your previous fix)
# # # weather_array_cols = [
# # #     "OriginPrecipitation", "OriginClouds",
# # #     "DestPrecipitation", "DestClouds"
# # # ]

# # # for c in weather_array_cols:
# # #     if c in df.columns:
# # #         df = df.withColumn(c, 
# # #             when(col(c).isNull(), "None")
# # #             .when(size(col(c)) == 0, "None")
# # #             .otherwise(concat_ws(",", col(c)))
# # #         )

# # # # 4. HANDLE MISSING NUMERIC COLUMNS (Safety Net)
# # # # If the ingestion data is missing any numeric columns the model needs, fill them with 0
# # # required_numerics = [
# # #     "Year", "Month", "DayofMonth", "DayOfWeek", 
# # #     "OriginWindDirection", "OriginWindSpeed", "DestWindDirection", "DestWindSpeed"
# # # ]
# # # for c in required_numerics:
# # #     if c not in df.columns:
# # #         df = df.withColumn(c, lit(0.0))

# # # # 4. Generate Predictions
# # # print("Generating predictions...")
# # # predictions = model.transform(df)

# # # # 5. Show "Likely On Time" (Prediction = 0.0)
# # # print("\n" + "="*40)
# # # print("PREDICTION: FLIGHTS LIKELY ON TIME")
# # # print("="*40)

# # # (predictions.filter(col("prediction") == 0.0)
# # #     .select("Dest", "DayOfWeek", col("Flight_Number_Operating_Airline").alias("FlightNum"), "probability")
# # #     .show(5, truncate=False))

# # # # 6. Show "Likely Delayed" (Prediction = 1.0)
# # # print("\n" + "="*40)
# # # print("PREDICTION: FLIGHTS LIKELY DELAYED")
# # # print("="*40)

# # # (predictions.filter(col("prediction") == 1.0)
# # #     .select("Dest", "DayOfWeek", col("Flight_Number_Operating_Airline").alias("FlightNum"), "probability")
# # #     .show(5, truncate=False))

# # # spark.stop()









# # from pyspark.sql import SparkSession
# # from pyspark.ml import PipelineModel
# # from pyspark.sql.functions import col, when, size, concat_ws, floor, to_date, dayofweek, lit

# # # 1. Initialize Spark
# # spark = (SparkSession.builder
# #     .appName("FlightPredictionDemo")
# #     .master("local[*]")
# #     .getOrCreate())

# # spark.sparkContext.setLogLevel("ERROR")

# # # 2. Load your saved model
# # model_path = "spark_gbt_model"
# # print(f"Loading model from {model_path}...")
# # model = PipelineModel.load(model_path)

# # # 3. Load data
# # data_path = "data/sample/parquet_delay_and_weather_24"
# # print(f"Loading data from {data_path}...")
# # df = spark.read.parquet(data_path)

# # print("Preprocessing data to match Model requirements...")

# # # --- PREPROCESSING STEPS (Must match backend.py) ---

# # # 1. FIX COLUMN NAMES
# # if "Operating_Airline " in df.columns:
# #     df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# # # 2. FEATURE ENGINEERING (Time & Weekend)
# # df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
# # df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
# # df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
# # df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)

# # df = df.withColumn("FlightDate", to_date(col("FlightDate")))
# # df = df.withColumn("is_weekend", 
# #     when((dayofweek(col("FlightDate")) == 1) | (dayofweek(col("FlightDate")) == 7), 1)
# #     .otherwise(0)
# # )

# # # 3. PROCESS ARRAY COLUMNS (Weather)
# # weather_array_cols = [
# #     "OriginPrecipitation", "OriginClouds",
# #     "DestPrecipitation", "DestClouds"
# # ]

# # for c in weather_array_cols:
# #     if c in df.columns:
# #         df = df.withColumn(c, 
# #             when(col(c).isNull(), "None")
# #             .when(size(col(c)) == 0, "None")
# #             .otherwise(concat_ws(",", col(c)))
# #         )

# # # 4. HANDLE MISSING NUMERIC COLUMNS
# # required_numerics = [
# #     "Year", "Month", "DayofMonth", "DayOfWeek", 
# #     "OriginWindDirection", "OriginWindSpeed", "DestWindDirection", "DestWindSpeed"
# # ]
# # for c in required_numerics:
# #     if c not in df.columns:
# #         df = df.withColumn(c, lit(0.0))

# # # --- GENERATE PREDICTIONS ---
# # print("Generating predictions...")
# # predictions = model.transform(df)

# # # --- DISPLAY RESULTS FOR DEMO ---

# # # Helper to select relevant columns
# # # We cast FlightNum to 'int' to remove the decimal (2446.0 -> 2446)
# # display_cols = [
# #     "FlightDate", 
# #     "Origin", 
# #     "Dest", 
# #     "CRSDepTime", 
# #     col("Flight_Number_Operating_Airline").cast("int").alias("FlightNum"), 
# #     "probability"
# # ]

# # print("\n" + "="*80)
# # print(" PREDICTION: FLIGHTS LIKELY ON TIME (Top 10)")
# # print("="*80)

# # (predictions.filter(col("prediction") == 0.0)
# #     .select(*display_cols)
# #     .orderBy("FlightDate", "CRSDepTime")
# #     .show(10, truncate=False))

# # print("\n" + "="*80)
# # print(" PREDICTION: FLIGHTS LIKELY DELAYED (Top 10)")
# # print("="*80)

# # (predictions.filter(col("prediction") == 1.0)
# #     .select(*display_cols)
# #     .orderBy("FlightDate", "CRSDepTime")
# #     .show(10, truncate=False))

# # spark.stop()























# from pyspark.sql import SparkSession
# from pyspark.ml import PipelineModel
# from pyspark.sql.functions import col, when, size, concat_ws, floor, to_date, dayofweek, lit

# # 1. Initialize Spark
# spark = (SparkSession.builder
#     .appName("FlightPredictionDemo")
#     .master("local[*]")
#     .getOrCreate())

# spark.sparkContext.setLogLevel("ERROR")

# # 2. Load model & data
# model_path = "spark_gbt_model"
# data_path = "data/sample/parquet_delay_and_weather_24"
# print(f"Loading model from {model_path}...")
# model = PipelineModel.load(model_path)
# df = spark.read.parquet(data_path)

# # --- PREPROCESSING (Must match backend.py Logic) ---

# # 1. FIX COLUMN NAMES
# if "Operating_Airline " in df.columns:
#     df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# # 2. FEATURE ENGINEERING (Time Calculations)
# # We calculate this exactly how backend.py does so the numbers match the UI
# df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
# df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
# df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
# df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)

# # *** THIS IS THE NUMBER YOU SEE IN THE FRONTEND ***
# df = df.withColumn("UI_Dep_Time", (col("DepHour") * 60) + col("DepMinute"))

# # 3. Weekend Flag
# df = df.withColumn("FlightDate", to_date(col("FlightDate")))
# df = df.withColumn("is_weekend", 
#     when((dayofweek(col("FlightDate")) == 1) | (dayofweek(col("FlightDate")) == 7), 1)
#     .otherwise(0)
# )

# # 4. Weather Array Fix
# weather_array_cols = ["OriginPrecipitation", "OriginClouds", "DestPrecipitation", "DestClouds"]
# for c in weather_array_cols:
#     if c in df.columns:
#         df = df.withColumn(c, 
#             when(col(c).isNull(), "None")
#             .when(size(col(c)) == 0, "None")
#             .otherwise(concat_ws(",", col(c)))
#         )

# # 5. Handle Missing Numerics
# required_numerics = ["Year", "Month", "DayofMonth", "DayOfWeek", "OriginWindDirection", "OriginWindSpeed", "DestWindDirection", "DestWindSpeed"]
# for c in required_numerics:
#     if c not in df.columns:
#         df = df.withColumn(c, lit(0.0))

# # --- GENERATE PREDICTIONS ---
# print("Generating predictions...")
# predictions = model.transform(df)

# # --- FILTER FOR DEMO ---
# # Update this date to match what you select in the UI
# TARGET_DATE = "2024-01-06" 

# print(f"\nSearching for flights on {TARGET_DATE}...")
# print(f"{'Origin':<10} {'Dest':<10} {'UI_Dep_Time':<15} {'Real_Flight_Num':<20} {'Prediction':<15} {'Probability'}")
# print("-" * 100)

# # Select columns to display
# # UI_Dep_Time: Matches the 'Dep' value in your dropdown
# # Flight_Number_Operating_Airline: The REAL flight number (so you know what plane it is)
# display_df = predictions.filter(col("FlightDate") == TARGET_DATE).select(
#     "Origin", 
#     "Dest", 
#     "UI_Dep_Time", 
#     col("Flight_Number_Operating_Airline").cast("int").alias("Real_Num"),
#     "prediction",
#     "probability"
# ).orderBy("UI_Dep_Time")

# # Collect and print row by row for cleaner formatting
# rows = display_df.collect()

# for row in rows:
#     # Format probability nicely
#     prob = row['probability']
#     prob_str = f"[{prob[0]:.2f}, {prob[1]:.2f}]"
    
#     # Translate prediction to text
#     pred_text = "DELAYED" if row['prediction'] == 1.0 else "On Time"
    
#     print(f"{row['Origin']:<10} {row['Dest']:<10} {str(row['UI_Dep_Time']):<15} {str(row['Real_Num']):<20} {pred_text:<15} {prob_str}")

# spark.stop()














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
