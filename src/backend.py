# # # src/backend.py
# # import pandas as pd
# # from fastapi import FastAPI, Query
# # from fastapi.middleware.cors import CORSMiddleware
# # import uvicorn
# # import os

# # # -------------------------------------------
# # # CONFIG
# # # -------------------------------------------
# # DEPARTURE_AIRPORT = "CLT"  # always Charlotte
# # TEST_PARQUET_PATH = "data/sample/test/flights.parquet"  # change to your real path

# # # -------------------------------------------
# # # APP INIT
# # # -------------------------------------------
# # app = FastAPI(title="Flight Delay Prediction API")

# # # Allow frontend → backend CORS in Docker
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],  # (change to specific domain in production)
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # -------------------------------------------
# # # LOAD DATA ONCE (FAST & EFFICIENT)
# # # -------------------------------------------
# # print("Loading test parquet dataset...")

# # df = pd.read_parquet(TEST_PARQUET_PATH)

# # # Force correct dtypes
# # df["FlightDate"] = pd.to_datetime(df["FlightDate"])
# # df["OriginAirportID"] = df["OriginAirportID"].astype(str)
# # df["DestAirportID"] = df["DestAirportID"].astype(str)
# # df["FlightNumber"] = df["FlightNumber"].astype(str)

# # print(f"Loaded {len(df)} rows into memory.")

# # # -------------------------------------------
# # # DESTINATIONS ENDPOINT
# # # -------------------------------------------
# # @app.get("/destinations")
# # def get_destinations():
# #     dests = (
# #         df[["DestAirportID", "DestCityName"]]
# #         .drop_duplicates()
# #         .sort_values("DestAirportID")
# #     )
# #     return dests.to_dict(orient="records")

# # # -------------------------------------------
# # # VALID DATES ENDPOINT
# # # -------------------------------------------
# # @app.get("/dates")
# # def get_dates(arrival: str = Query(...)):
# #     filtered = df[df["DestAirportID"] == arrival]
# #     dates = sorted(filtered["FlightDate"].dt.strftime("%Y-%m-%d").unique().tolist())
# #     return dates

# # # -------------------------------------------
# # # VALID FLIGHTS FOR DATE + DEST ENDPOINT
# # # -------------------------------------------
# # @app.get("/flights")
# # def get_flights(
# #     arrival: str = Query(...),
# #     date: str = Query(...)
# # ):
# #     filtered = df[
# #         (df["DestAirportID"] == arrival) &
# #         (df["FlightDate"].dt.strftime("%Y-%m-%d") == date)
# #     ]

# #     flights = []
# #     for _, row in filtered.iterrows():
# #         flights.append({
# #             "flight_id": row["FlightNumber"],
# #             "departure_time": row["CRSDepTime"],
# #             "arrival_time": row["CRSArrTime"]
# #         })

# #     return flights

# # # -------------------------------------------
# # # PREDICTION ENDPOINT
# # # -------------------------------------------
# # @app.get("/predict")
# # def predict(flight_id: str = Query(...)):
# #     # extract row
# #     row = df[df["FlightNumber"] == flight_id].iloc[0]

# #     # TODO: replace fake model with your Spark model
# #     # pred = model.predict(features)
# #     fake_pred = 55  # placeholder

# #     return {
# #         "delay": float(fake_pred),
# #         "weather": {
# #             "temp": float(row["Temperature"]),
# #             "wind": float(row["WindSpeed"]),
# #             "rain": float(row["Precipitation"])
# #         }
# #     }

# # # -------------------------------------------
# # # RUN SERVER
# # # -------------------------------------------
# # if __name__ == "__main__":
# #     uvicorn.run(
# #         "backend:app",
# #         host="0.0.0.0",
# #         port=9998,
# #         reload=False
# #     )
















# from pyspark.sql.functions import udf
# from pyspark.sql.types import StringType

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import os

# from pyspark.sql import SparkSession
# from pyspark.ml.pipeline import PipelineModel
# from pyspark.sql.functions import col, floor, monotonically_increasing_id

# # ----------------------------------------
# # Spark session
# # ----------------------------------------
# spark = SparkSession.builder.appName("FastAPIInference").getOrCreate()

# # ----------------------------------------
# # Paths
# # ----------------------------------------
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# PARQUET_PATH = os.path.join(PROJECT_ROOT, "data", "sample", "parquet_delay_and_weather_24")
# MODEL_PATH = os.path.join(PROJECT_ROOT, "spark_gbt_model")


# # ----------------------------------------
# # Load data once
# # ----------------------------------------
# df = spark.read.parquet(PARQUET_PATH)

# # 1. Create minute-based time fields (matches your training logic)
# df = df.withColumn(
#     "CRSDepTimeMinute",
#     floor(col("CRSDepTime") / 100) * 60 + (col("CRSDepTime") % 100)
# )

# df = df.withColumn(
#     "CRSArrTimeMinute",
#     floor(col("CRSArrTime") / 100) * 60 + (col("CRSArrTime") % 100)
# )

# # 2. Create a stable numeric ID for frontend selections
# df = df.withColumn("FlightID", monotonically_increasing_id())

# # ----------------------------------------
# # Load model once
# # ----------------------------------------
# model = PipelineModel.load(MODEL_PATH)

# # ----------------------------------------
# # Precompute destination list
# # ----------------------------------------
# destinations = (
#     df.select("DestCityName")
#       .distinct()
#       .orderBy("DestCityName")
#       .rdd.flatMap(lambda x: x)
#       .collect()
# )

# # ----------------------------------------
# # Precompute date options per destination
# # ----------------------------------------
# dates_by_dest = {}
# for dest in destinations:
#     dates = (
#         df.filter(col("DestCityName") == dest)
#           .select("FlightDate")
#           .distinct()
#           .rdd.flatMap(lambda x: x)
#           .collect()
#     )
#     dates_by_dest[dest] = [d.strftime("%Y-%m-%d") for d in dates]

# # ----------------------------------------
# # Precompute flights per (destination, date)
# # ----------------------------------------
# flights_by_dest_date = {}

# rows = df.select("DestCityName", "FlightDate", "FlightID",
#                  "CRSDepTimeMinute", "CRSArrTimeMinute").collect()

# for row in rows:
#     key = (row["DestCityName"], row["FlightDate"].strftime("%Y-%m-%d"))
#     if key not in flights_by_dest_date:
#         flights_by_dest_date[key] = []
#     flights_by_dest_date[key].append({
#         "flight_id": int(row["FlightID"]),
#         "departure_time": row["CRSDepTimeMinute"],
#         "arrival_time": row["CRSArrTimeMinute"]
#     })

# # ----------------------------------------
# # APP
# # ----------------------------------------
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ----------------------------------------
# # Routes
# # ----------------------------------------

# @app.get("/destinations")
# def get_destinations():
#     return destinations

# @app.get("/dates")
# def get_dates(arrival: str):
#     return dates_by_dest.get(arrival, [])

# @app.get("/flights")
# def get_flights(arrival: str, date: str):
#     key = (arrival, date)
#     return flights_by_dest_date.get(key, [])

# @app.get("/predict")
# def predict(flight_id: int):
#     # Spark lookup
#     sdf = df.filter(col("FlightID") == flight_id)
#     if sdf.count() == 0:
#         raise HTTPException(404, "Invalid flight ID")

#     pred = model.transform(sdf).select("prediction").collect()[0][0]
#     return {"delay": float(pred)}


















# from pyspark.sql.functions import udf
# from pyspark.sql.types import StringType

from src.udfs import arr_to_str

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from pyspark.sql import SparkSession
from pyspark.ml.pipeline import PipelineModel
from pyspark.sql.functions import col, floor, monotonically_increasing_id
from pyspark.sql.functions import to_date, dayofweek, when

# ----------------------------------------
# Spark session
# ----------------------------------------
spark = SparkSession.builder.appName("FastAPIInference").getOrCreate()

# ----------------------------------------
# Paths
# ----------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(PROJECT_ROOT, "data", "sample", "parquet_delay_and_weather_24")
MODEL_PATH = os.path.join(PROJECT_ROOT, "spark_gbt_model")


# ----------------------------------------
# Load data once
# ----------------------------------------
df = spark.read.parquet(PARQUET_PATH)

# ---------------------------------------------------
# PREPROCESSING FIX — MATCH TRAINING TRANSFORMATIONS
# ---------------------------------------------------
# from pyspark.sql.functions import udf
# from pyspark.sql.types import StringType

# def arr_to_str_py(val):
#     if val is None:
#         return "None"
#     if isinstance(val, list):
#         if len(val) == 0:
#             return "None"
#         return ",".join(str(x) for x in val)
#     return str(val)

# arr_to_str = udf(arr_to_str_py, StringType())

weather_cols = [
    "OriginPrecipitation", "OriginClouds",
    "DestPrecipitation", "DestClouds"
]

for c in weather_cols:
    if c in df.columns:
        df = df.withColumn(c, arr_to_str(col(c)))

if "Operating_Airline " in df.columns:  # trailing space
    df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# ---------------------------------------------------
# NOW continue your existing backend preprocessing
# ---------------------------------------------------

# -------------------------------------------------------
# FILL CATEGORICAL NULLS (MUST BE BEFORE MODEL TRANSFORM)
# -------------------------------------------------------
from pyspark.sql.functions import lit

categorical_columns = [
    "Marketing_Airline_Network",
    "Operating_Airline",
    "Origin",
    "Dest",
    "OriginPrecipitation",
    "OriginClouds",
    "DestPrecipitation",
    "DestClouds"
]

for c in categorical_columns:
    if c in df.columns:
        df = df.fillna({c: "None"})

# 1. Create minute-based time fields (matches your training logic)
df = df.withColumn(
    "CRSDepTimeMinute",
    floor(col("CRSDepTime") / 100) * 60 + (col("CRSDepTime") % 100)
)


df = df.withColumn(
    "CRSArrTimeMinute",
    floor(col("CRSArrTime") / 100) * 60 + (col("CRSArrTime") % 100)
)

# -------------------------------------------------------
# MATCH TRAINING: Create DepHour, ArrHour, DepMinute, ArrMinute
# -------------------------------------------------------
# These replicate your pandas training logic:
# DepHour = CRSDepTime // 100
# ArrHour = CRSArrTime // 100
# DepMinute = CRSDepTime % 100
# ArrMinute = CRSArrTime % 100

df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)


# -------------------------------------------------------
# MATCH TRAINING: compute is_weekend exactly like training
# -------------------------------------------------------
from pyspark.sql.functions import to_date, dayofweek, when

# Convert FlightDate from string → Spark date
df = df.withColumn("FlightDate", to_date(col("FlightDate")))

# In Spark: Monday=2 ... Sunday=1
# Weekend: Saturday (7) or Sunday (1)
df = df.withColumn(
    "is_weekend",
    when((dayofweek(col("FlightDate")) == 7) | (dayofweek(col("FlightDate")) == 1), 1)
    .otherwise(0)
)

# -------------------------------------------------------
# DROP TRAINING-DROPPED COLUMNS
# -------------------------------------------------------
drop_cols = ["CRSDepTime", "CRSArrTime"]
for c in drop_cols:
    if c in df.columns:
        df = df.drop(c)

# Ensure backend has ALL numeric columns used in training
numeric_columns_expected = [
    "Year", "Month", "DayofMonth", "DayOfWeek",
    "OriginWindDirection", "OriginWindSpeed", "OriginVisibility",
    "DestWindDirection", "DestWindSpeed", "DestVisibility",
    "DepHour", "ArrHour", "DepMinute", "ArrMinute", "is_weekend"
]

for c in numeric_columns_expected:
    if c not in df.columns:
        df = df.withColumn(c, lit(None).cast("double"))

####################################################################################################

import json

median_file = os.path.join(PROJECT_ROOT, "data", "median_fill_values.json")
with open(median_file, "r") as f:
    median_fill_values = json.load(f)

numeric_cols_to_fill = list(median_fill_values.keys())

# Apply the same fills the training pipeline uses
for colname in numeric_cols_to_fill:
    if colname in df.columns:
        df = df.fillna({colname: float(median_fill_values[colname])})

###################################################################################################

# 2. Create a stable numeric ID for frontend selections
df = df.withColumn("FlightID", monotonically_increasing_id())

# ----------------------------------------
# Load model once
# ----------------------------------------
model = PipelineModel.load(MODEL_PATH)

# ----------------------------------------
# Precompute destination list
# ----------------------------------------
destinations = (
    df.select("DestCityName")
      .distinct()
      .orderBy("DestCityName")
      .rdd.flatMap(lambda x: x)
      .collect()
)

# ----------------------------------------
# Precompute date options per destination
# ----------------------------------------



dates_by_dest = {}
for dest in destinations:
    dates = (
        df.filter(col("DestCityName") == dest)
          .select("FlightDate")
          .distinct()
          .rdd.flatMap(lambda x: x)
          .collect()
    )
    dates_by_dest[dest] = [d.strftime("%Y-%m-%d") for d in dates]

# ----------------------------------------
# Precompute flights per (destination, date)
# ----------------------------------------
flights_by_dest_date = {}

rows = df.select("DestCityName", "FlightDate", "FlightID",
                 "CRSDepTimeMinute", "CRSArrTimeMinute").collect()

for row in rows:
    key = (row["DestCityName"], row["FlightDate"].strftime("%Y-%m-%d"))
    if key not in flights_by_dest_date:
        flights_by_dest_date[key] = []
    flights_by_dest_date[key].append({
        "flight_id": int(row["FlightID"]),
        "departure_time": row["CRSDepTimeMinute"],
        "arrival_time": row["CRSArrTimeMinute"]
    })

# ----------------------------------------
# APP
# ----------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------
# Routes
# ----------------------------------------

@app.get("/destinations")
def get_destinations():
    return destinations

@app.get("/dates")
def get_dates(arrival: str):
    return dates_by_dest.get(arrival, [])

@app.get("/flights")
def get_flights(arrival: str, date: str):
    key = (arrival, date)
    return flights_by_dest_date.get(key, [])

@app.get("/predict")
def predict(flight_id: int):
    # Spark lookup
    sdf = df.filter(col("FlightID") == flight_id)
    if sdf.count() == 0:
        raise HTTPException(404, "Invalid flight ID")

    

    pred = model.transform(sdf).select("prediction").collect()[0][0]
    return {"delay": float(pred)}
