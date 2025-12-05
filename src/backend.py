# # # # src/backend.py
# # # import pandas as pd
# # # from fastapi import FastAPI, Query
# # # from fastapi.middleware.cors import CORSMiddleware
# # # import uvicorn
# # # import os

# # # # -------------------------------------------
# # # # CONFIG
# # # # -------------------------------------------
# # # DEPARTURE_AIRPORT = "CLT"  # always Charlotte
# # # TEST_PARQUET_PATH = "data/sample/test/flights.parquet"  # change to your real path

# # # # -------------------------------------------
# # # # APP INIT
# # # # -------------------------------------------
# # # app = FastAPI(title="Flight Delay Prediction API")

# # # # Allow frontend → backend CORS in Docker
# # # app.add_middleware(
# # #     CORSMiddleware,
# # #     allow_origins=["*"],  # (change to specific domain in production)
# # #     allow_credentials=True,
# # #     allow_methods=["*"],
# # #     allow_headers=["*"],
# # # )

# # # # -------------------------------------------
# # # # LOAD DATA ONCE (FAST & EFFICIENT)
# # # # -------------------------------------------
# # # print("Loading test parquet dataset...")

# # # df = pd.read_parquet(TEST_PARQUET_PATH)

# # # # Force correct dtypes
# # # df["FlightDate"] = pd.to_datetime(df["FlightDate"])
# # # df["OriginAirportID"] = df["OriginAirportID"].astype(str)
# # # df["DestAirportID"] = df["DestAirportID"].astype(str)
# # # df["FlightNumber"] = df["FlightNumber"].astype(str)

# # # print(f"Loaded {len(df)} rows into memory.")

# # # # -------------------------------------------
# # # # DESTINATIONS ENDPOINT
# # # # -------------------------------------------
# # # @app.get("/destinations")
# # # def get_destinations():
# # #     dests = (
# # #         df[["DestAirportID", "DestCityName"]]
# # #         .drop_duplicates()
# # #         .sort_values("DestAirportID")
# # #     )
# # #     return dests.to_dict(orient="records")

# # # # -------------------------------------------
# # # # VALID DATES ENDPOINT
# # # # -------------------------------------------
# # # @app.get("/dates")
# # # def get_dates(arrival: str = Query(...)):
# # #     filtered = df[df["DestAirportID"] == arrival]
# # #     dates = sorted(filtered["FlightDate"].dt.strftime("%Y-%m-%d").unique().tolist())
# # #     return dates

# # # # -------------------------------------------
# # # # VALID FLIGHTS FOR DATE + DEST ENDPOINT
# # # # -------------------------------------------
# # # @app.get("/flights")
# # # def get_flights(
# # #     arrival: str = Query(...),
# # #     date: str = Query(...)
# # # ):
# # #     filtered = df[
# # #         (df["DestAirportID"] == arrival) &
# # #         (df["FlightDate"].dt.strftime("%Y-%m-%d") == date)
# # #     ]

# # #     flights = []
# # #     for _, row in filtered.iterrows():
# # #         flights.append({
# # #             "flight_id": row["FlightNumber"],
# # #             "departure_time": row["CRSDepTime"],
# # #             "arrival_time": row["CRSArrTime"]
# # #         })

# # #     return flights

# # # # -------------------------------------------
# # # # PREDICTION ENDPOINT
# # # # -------------------------------------------
# # # @app.get("/predict")
# # # def predict(flight_id: str = Query(...)):
# # #     # extract row
# # #     row = df[df["FlightNumber"] == flight_id].iloc[0]

# # #     # TODO: replace fake model with your Spark model
# # #     # pred = model.predict(features)
# # #     fake_pred = 55  # placeholder

# # #     return {
# # #         "delay": float(fake_pred),
# # #         "weather": {
# # #             "temp": float(row["Temperature"]),
# # #             "wind": float(row["WindSpeed"]),
# # #             "rain": float(row["Precipitation"])
# # #         }
# # #     }

# # # # -------------------------------------------
# # # # RUN SERVER
# # # # -------------------------------------------
# # # if __name__ == "__main__":
# # #     uvicorn.run(
# # #         "backend:app",
# # #         host="0.0.0.0",
# # #         port=9998,
# # #         reload=False
# # #     )
















# # from pyspark.sql.functions import udf
# # from pyspark.sql.types import StringType

# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # import os

# # from pyspark.sql import SparkSession
# # from pyspark.ml.pipeline import PipelineModel
# # from pyspark.sql.functions import col, floor, monotonically_increasing_id

# # # ----------------------------------------
# # # Spark session
# # # ----------------------------------------
# # spark = SparkSession.builder.appName("FastAPIInference").getOrCreate()

# # # ----------------------------------------
# # # Paths
# # # ----------------------------------------
# # PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # PARQUET_PATH = os.path.join(PROJECT_ROOT, "data", "sample", "parquet_delay_and_weather_24")
# # MODEL_PATH = os.path.join(PROJECT_ROOT, "spark_gbt_model")


# # # ----------------------------------------
# # # Load data once
# # # ----------------------------------------
# # df = spark.read.parquet(PARQUET_PATH)

# # # 1. Create minute-based time fields (matches your training logic)
# # df = df.withColumn(
# #     "CRSDepTimeMinute",
# #     floor(col("CRSDepTime") / 100) * 60 + (col("CRSDepTime") % 100)
# # )

# # df = df.withColumn(
# #     "CRSArrTimeMinute",
# #     floor(col("CRSArrTime") / 100) * 60 + (col("CRSArrTime") % 100)
# # )

# # # 2. Create a stable numeric ID for frontend selections
# # df = df.withColumn("FlightID", monotonically_increasing_id())

# # # ----------------------------------------
# # # Load model once
# # # ----------------------------------------
# # model = PipelineModel.load(MODEL_PATH)

# # # ----------------------------------------
# # # Precompute destination list
# # # ----------------------------------------
# # destinations = (
# #     df.select("DestCityName")
# #       .distinct()
# #       .orderBy("DestCityName")
# #       .rdd.flatMap(lambda x: x)
# #       .collect()
# # )

# # # ----------------------------------------
# # # Precompute date options per destination
# # # ----------------------------------------
# # dates_by_dest = {}
# # for dest in destinations:
# #     dates = (
# #         df.filter(col("DestCityName") == dest)
# #           .select("FlightDate")
# #           .distinct()
# #           .rdd.flatMap(lambda x: x)
# #           .collect()
# #     )
# #     dates_by_dest[dest] = [d.strftime("%Y-%m-%d") for d in dates]

# # # ----------------------------------------
# # # Precompute flights per (destination, date)
# # # ----------------------------------------
# # flights_by_dest_date = {}

# # rows = df.select("DestCityName", "FlightDate", "FlightID",
# #                  "CRSDepTimeMinute", "CRSArrTimeMinute").collect()

# # for row in rows:
# #     key = (row["DestCityName"], row["FlightDate"].strftime("%Y-%m-%d"))
# #     if key not in flights_by_dest_date:
# #         flights_by_dest_date[key] = []
# #     flights_by_dest_date[key].append({
# #         "flight_id": int(row["FlightID"]),
# #         "departure_time": row["CRSDepTimeMinute"],
# #         "arrival_time": row["CRSArrTimeMinute"]
# #     })

# # # ----------------------------------------
# # # APP
# # # ----------------------------------------
# # app = FastAPI()

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # ----------------------------------------
# # # Routes
# # # ----------------------------------------

# # @app.get("/destinations")
# # def get_destinations():
# #     return destinations

# # @app.get("/dates")
# # def get_dates(arrival: str):
# #     return dates_by_dest.get(arrival, [])

# # @app.get("/flights")
# # def get_flights(arrival: str, date: str):
# #     key = (arrival, date)
# #     return flights_by_dest_date.get(key, [])

# # @app.get("/predict")
# # def predict(flight_id: int):
# #     # Spark lookup
# #     sdf = df.filter(col("FlightID") == flight_id)
# #     if sdf.count() == 0:
# #         raise HTTPException(404, "Invalid flight ID")

# #     pred = model.transform(sdf).select("prediction").collect()[0][0]
# #     return {"delay": float(pred)}


















# # from pyspark.sql.functions import udf
# # from pyspark.sql.types import StringType

# from src.udfs import arr_to_str

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import os

# from pyspark.sql import SparkSession
# from pyspark.ml.pipeline import PipelineModel
# from pyspark.sql.functions import col, floor, monotonically_increasing_id
# from pyspark.sql.functions import to_date, dayofweek, when

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

# # ---------------------------------------------------
# # PREPROCESSING FIX — MATCH TRAINING TRANSFORMATIONS
# # ---------------------------------------------------
# # from pyspark.sql.functions import udf
# # from pyspark.sql.types import StringType

# # def arr_to_str_py(val):
# #     if val is None:
# #         return "None"
# #     if isinstance(val, list):
# #         if len(val) == 0:
# #             return "None"
# #         return ",".join(str(x) for x in val)
# #     return str(val)

# # arr_to_str = udf(arr_to_str_py, StringType())

# weather_cols = [
#     "OriginPrecipitation", "OriginClouds",
#     "DestPrecipitation", "DestClouds"
# ]

# for c in weather_cols:
#     if c in df.columns:
#         df = df.withColumn(c, arr_to_str(col(c)))

# if "Operating_Airline " in df.columns:  # trailing space
#     df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# # ---------------------------------------------------
# # NOW continue your existing backend preprocessing
# # ---------------------------------------------------

# # -------------------------------------------------------
# # FILL CATEGORICAL NULLS (MUST BE BEFORE MODEL TRANSFORM)
# # -------------------------------------------------------
# from pyspark.sql.functions import lit

# categorical_columns = [
#     "Marketing_Airline_Network",
#     "Operating_Airline",
#     "Origin",
#     "Dest",
#     "OriginPrecipitation",
#     "OriginClouds",
#     "DestPrecipitation",
#     "DestClouds"
# ]

# for c in categorical_columns:
#     if c in df.columns:
#         df = df.fillna({c: "None"})

# # 1. Create minute-based time fields (matches your training logic)
# df = df.withColumn(
#     "CRSDepTimeMinute",
#     floor(col("CRSDepTime") / 100) * 60 + (col("CRSDepTime") % 100)
# )


# df = df.withColumn(
#     "CRSArrTimeMinute",
#     floor(col("CRSArrTime") / 100) * 60 + (col("CRSArrTime") % 100)
# )

# # -------------------------------------------------------
# # MATCH TRAINING: Create DepHour, ArrHour, DepMinute, ArrMinute
# # -------------------------------------------------------
# # These replicate your pandas training logic:
# # DepHour = CRSDepTime // 100
# # ArrHour = CRSArrTime // 100
# # DepMinute = CRSDepTime % 100
# # ArrMinute = CRSArrTime % 100

# df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
# df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
# df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
# df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)


# # -------------------------------------------------------
# # MATCH TRAINING: compute is_weekend exactly like training
# # -------------------------------------------------------
# from pyspark.sql.functions import to_date, dayofweek, when

# # Convert FlightDate from string → Spark date
# df = df.withColumn("FlightDate", to_date(col("FlightDate")))

# # In Spark: Monday=2 ... Sunday=1
# # Weekend: Saturday (7) or Sunday (1)
# df = df.withColumn(
#     "is_weekend",
#     when((dayofweek(col("FlightDate")) == 7) | (dayofweek(col("FlightDate")) == 1), 1)
#     .otherwise(0)
# )

# # -------------------------------------------------------
# # DROP TRAINING-DROPPED COLUMNS
# # -------------------------------------------------------
# drop_cols = ["CRSDepTime", "CRSArrTime"]
# for c in drop_cols:
#     if c in df.columns:
#         df = df.drop(c)

# # Ensure backend has ALL numeric columns used in training
# numeric_columns_expected = [
#     "Year", "Month", "DayofMonth", "DayOfWeek",
#     "OriginWindDirection", "OriginWindSpeed", "OriginVisibility",
#     "DestWindDirection", "DestWindSpeed", "DestVisibility",
#     "DepHour", "ArrHour", "DepMinute", "ArrMinute", "is_weekend"
# ]

# for c in numeric_columns_expected:
#     if c not in df.columns:
#         df = df.withColumn(c, lit(None).cast("double"))

# ####################################################################################################

# import json

# median_file = os.path.join(PROJECT_ROOT, "data", "median_fill_values.json")
# with open(median_file, "r") as f:
#     median_fill_values = json.load(f)

# numeric_cols_to_fill = list(median_fill_values.keys())

# # Apply the same fills the training pipeline uses
# for colname in numeric_cols_to_fill:
#     if colname in df.columns:
#         df = df.fillna({colname: float(median_fill_values[colname])})

# ###################################################################################################

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






# src/backend.py
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pyspark.sql import SparkSession
from pyspark.ml.pipeline import PipelineModel
# IMPORT NATIVE FUNCTIONS TO REPLACE UDF
from pyspark.sql.functions import (
    col, floor, monotonically_increasing_id, 
    to_date, dayofweek, when, lit, 
    concat_ws, size
)

# ----------------------------------------
# 1. Spark Session & Configuration
# ----------------------------------------
spark = SparkSession.builder.appName("FastAPIInference").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# ----------------------------------------
# 2. Paths
# ----------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(PROJECT_ROOT, "data", "sample", "parquet_delay_and_weather_24")
MODEL_PATH = os.path.join(PROJECT_ROOT, "spark_gbt_model")
MEDIAN_FILE = os.path.join(PROJECT_ROOT, "data", "median_fill_values.json")

# ----------------------------------------
# 3. Load Data
# ----------------------------------------
print(f"Loading data from {PARQUET_PATH}...")
df = spark.read.parquet(PARQUET_PATH)

# ----------------------------------------
# 4. Data Processing (Matching train_model.py)
# ----------------------------------------

# --- A. Drop Columns ---
cols_to_drop = [
    # Actual departure/arrival values -> leakage
    "DepTime", "DepDelay", "DepDelayMinutes",
    "DepartureDelayGroups", "TaxiOut", "WheelsOff", "WheelsOn",
    "TaxiIn", "ArrTime", "ArrDelay", "ArrDelayMinutes",
    "ArrDel15", "ArrivalDelayGroups",

    # After-fact outcomes
    "Cancelled", "Diverted",

    # Redundant ID fields
    "DestAirportID", "OriginAirportID", "DOT_ID_Marketing_Airline",
    "DOT_ID_Operating_Airline", "OriginAirportSeqID",
    "DestAirportSeqID", "OriginCityMarketID", "DestCityMarketID",
    "Flight_Number_Operating_Airline", "OriginICAO", "DestICAO",

    # Duplicated / unnecessary text fields 
    # REMOVED 'DestCityName' from this list so the UI works. Model ignores it.
    "DepTimeBlk", "ArrTimeBlk",
    "OriginTimezone", "DestTimezone",

    # Redundant timestamps
    "CRSDepTimestamp", "CRSArrTimestamp",

    # Columns with lots of NaN
    'CancellationCode',
    'CarrierDelay','WeatherDelay','NASDelay',"SecurityDelay","LateAircraftDelay",
    "OriginWindGusts", "OriginTemperature", "OriginDewPoint",
    "DestWindGusts",'DestTemperature','DestDewPoint'
]

# Drop columns if they exist
existing_drop = [c for c in cols_to_drop if c in df.columns]
df = df.drop(*existing_drop)

# --- B. Label Column ---
if "DepDel15" in df.columns:
    df = df.drop("DepDel15")

# --- C. Array to String (NATIVE SPARK - NO UDF) ---
# This block replaces the 'arr_to_str' UDF.
# It does the exact same logic: Null/Empty -> "None", otherwise join with comma.
weather_array_cols = [
    "OriginPrecipitation", "OriginClouds",
    "DestPrecipitation", "DestClouds"
]

for c in weather_array_cols:
    if c in df.columns:
        df = df.withColumn(c, 
            when(col(c).isNull(), "None")         # If Null -> "None"
            .when(size(col(c)) == 0, "None")      # If Empty List -> "None"
            .otherwise(concat_ws(",", col(c)))    # Else -> "val1,val2"
        )

# --- D. Renaming ---
if "Operating_Airline " in df.columns:
    df = df.withColumnRenamed("Operating_Airline ", "Operating_Airline")

# --- E. Feature Engineering: Time ---
# Logic: t // 100 = hour, t % 100 = minute
df = df.withColumn("DepHour", floor(col("CRSDepTime") / 100))
df = df.withColumn("ArrHour", floor(col("CRSArrTime") / 100))
df = df.withColumn("DepMinute", col("CRSDepTime") % 100)
df = df.withColumn("ArrMinute", col("CRSArrTime") % 100)

# Calculate total minutes for the Frontend Display BEFORE dropping original cols
df = df.withColumn("CRSDepTimeMinute", (col("DepHour") * 60) + col("DepMinute"))
df = df.withColumn("CRSArrTimeMinute", (col("ArrHour") * 60) + col("ArrMinute"))

# --- F. Feature Engineering: Weekend ---
# Spark: dayofweek (1=Sun, 2=Mon...7=Sat). 
df = df.withColumn("FlightDate", to_date(col("FlightDate")))
df = df.withColumn(
    "is_weekend",
    when((dayofweek(col("FlightDate")) == 1) | (dayofweek(col("FlightDate")) == 7), 1)
    .otherwise(0)
)

# --- G. Drop Original Time Columns ---
df = df.drop("CRSDepTime", "CRSArrTime")

# --- H. Categorical Handling ---
cat_cols = [
    "Marketing_Airline_Network",
    "Operating_Airline",
    "Origin",
    "Dest",
    "OriginPrecipitation",
    "OriginClouds",
    "DestPrecipitation",
    "DestClouds"
]

cat_fill_dict = {c: "None" for c in cat_cols if c in df.columns}
if cat_fill_dict:
    df = df.fillna(cat_fill_dict)

# --- I. Numeric Handling (Median Fill) ---
if os.path.exists(MEDIAN_FILE):
    with open(MEDIAN_FILE, "r") as f:
        median_fill_values = json.load(f)
    
    # Ensure keys match expected numerics
    num_cols = [
        "Year", "Month", "DayofMonth", "DayOfWeek",
        "OriginWindDirection", "OriginWindSpeed", "OriginVisibility",
        "DestWindDirection", "DestWindSpeed", "DestVisibility",
        "DepHour", "ArrHour", "DepMinute", "ArrMinute", "is_weekend"
    ]
    
    # Fill based on JSON
    for colname, median_val in median_fill_values.items():
        if colname in df.columns:
            df = df.fillna({colname: float(median_val)})
            
    # Safety check: If a num_col is missing entirely, create it with 0.0
    for c in num_cols:
        if c not in df.columns:
            df = df.withColumn(c, lit(0.0))
else:
    print("WARNING: median_fill_values.json not found. Model may fail on nulls.")


# ----------------------------------------
# 5. Final Preparation
# ----------------------------------------
# Create Unique ID for API Lookup
df = df.withColumn("FlightID", monotonically_increasing_id())

# Cache the DataFrame for faster API performance
df.cache()

# Trigger action to force execution immediately (checks for errors now, not later)
print(f"Backend processed. Cached {df.count()} rows.")

# Load the trained Spark Model
print(f"Loading model from {MODEL_PATH}...")
model = PipelineModel.load(MODEL_PATH)

# ----------------------------------------
# 6. Pre-computation (Frontend Helpers)
# ----------------------------------------

# Get list of Destinations (using DestCityName for readability in UI)
destinations = (
    df.select("DestCityName")
      .distinct()
      .orderBy("DestCityName")
      .rdd.flatMap(lambda x: x)
      .collect()
)

# Map: Destination -> List of Dates
dates_by_dest = {}
rows_dates = df.select("DestCityName", "FlightDate").distinct().collect()
for r in rows_dates:
    dest_name = r["DestCityName"]
    date_str = r["FlightDate"].strftime("%Y-%m-%d")
    
    if dest_name not in dates_by_dest:
        dates_by_dest[dest_name] = []
    dates_by_dest[dest_name].append(date_str)

# Map: (Dest, Date) -> List of Flight Details
flights_by_dest_date = {}
# We use DestCityName here to match the frontend selection
flight_rows = df.select("DestCityName", "FlightDate", "FlightID", "CRSDepTimeMinute", "CRSArrTimeMinute").collect()

for row in flight_rows:
    dest_name = row["DestCityName"]
    date_str = row["FlightDate"].strftime("%Y-%m-%d")
    key = (dest_name, date_str)
    
    if key not in flights_by_dest_date:
        flights_by_dest_date[key] = []
        
    flights_by_dest_date[key].append({
        "flight_id": int(row["FlightID"]),
        "departure_time": row["CRSDepTimeMinute"],
        "arrival_time": row["CRSArrTimeMinute"]
    })

# ----------------------------------------
# 7. FastAPI App
# ----------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# @app.get("/predict")
# def predict(flight_id: int):
#     # Filter for the specific flight
#     sdf = df.filter(col("FlightID") == flight_id)
    
#     if sdf.isEmpty():
#         raise HTTPException(status_code=404, detail="Flight not found")

#     # Run Inference
#     preds = model.transform(sdf)
    
#     # Extract results
#     row = preds.select("prediction", "probability").collect()[0]
    
#     pred_label = float(row["prediction"])
#     prob_delay = float(row["probability"][1]) 

#     return {
#         "prediction": int(pred_label),
#         "probability_delay": prob_delay,
#         "is_delayed": pred_label == 1.0
#     }


@app.get("/predict")
def predict(flight_id: int):
    sdf = df.filter(col("FlightID") == flight_id)
    if sdf.isEmpty():
        raise HTTPException(status_code=404, detail="Flight not found")

    preds = model.transform(sdf)
    row = preds.select("prediction", "probability").collect()[0]
    pred_label = int(row["prediction"])

    # exact contract match: only `delay`
    return {"delay": pred_label}



