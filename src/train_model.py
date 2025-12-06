# # train_model.py
# import os
# from pyspark.sql import SparkSession
# from pyspark.sql.functions import col, when
# from pyspark.ml import Pipeline
# from pyspark.ml.feature import (
#     StringIndexer,
#     OneHotEncoder,
#     VectorAssembler
# )
# from pyspark.ml.classification import GBTClassifier
# from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
# from pyspark.ml.tuning import ParamGridBuilder, CrossValidator


# # -----------------------------------------------------
# # Spark session
# # -----------------------------------------------------
# spark = SparkSession.builder \
#     .appName("TrainFlightDelayModel") \
#     .getOrCreate()

# print("Spark session started.")


# # -----------------------------------------------------
# # Load parquet
# # -----------------------------------------------------
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_PATH = os.path.join(PROJECT_ROOT, "data", "sample", "parquet_delay_and_weather_25")

# print(f"Loading parquet from: {DATA_PATH}")
# df = spark.read.parquet(DATA_PATH)

# print(f"Loaded {df.count()} rows")


# # -----------------------------------------------------
# # Create label column
# # DepDel15 = 1 means delayed > 15 minutes
# # -----------------------------------------------------
# df = df.withColumn(
#     "label",
#     when(col("DepDel15") == 1, 1).otherwise(0)
# )

# # Remove rows with null labels
# df = df.filter(col("label").isNotNull())


# # -----------------------------------------------------
# # Feature columns (from your notebook)
# # NOTE: you may adjust this list if needed.
# # -----------------------------------------------------
# categorical_cols = [
#     "Marketing_Airline_Network",
#     "OriginCityName",
#     "DestCityName",
#     "CRSDepTimeHourDis",
#     "CRSArrTimeHourDis",
# ]

# numeric_cols = [
#     "Distance",
#     "CRSDepTimeMinute",
#     "CRSArrTimeMinute",
#     "WheelsOffMinute",
#     "WheelsOnMinute",
#     "CRSElapsedTime",
#     "ActualElapsedTime",
#     "AirTime",
#     "DayofWeek",
#     "Month",
#     "DayofMonth"
# ]

# # -----------------------------------------------------
# # Build pipeline stages
# # -----------------------------------------------------
# indexers = [
#     StringIndexer(inputCol=c, outputCol=f"{c}_indexed", handleInvalid="keep")
#     for c in categorical_cols
# ]

# encoders = [
#     OneHotEncoder(
#         inputCols=[f"{c}_indexed"],
#         outputCols=[f"{c}_encoded"]
#     )
#     for c in categorical_cols
# ]

# assembler_inputs = [
#     f"{c}_encoded" for c in categorical_cols
# ] + numeric_cols

# assembler = VectorAssembler(
#     inputCols=assembler_inputs,
#     outputCol="features"
# )

# gbt = GBTClassifier(
#     labelCol="label",
#     featuresCol="features",
#     maxIter=50,
#     maxDepth=5
# )

# pipeline = Pipeline(stages=indexers + encoders + [assembler, gbt])


# # -----------------------------------------------------
# # Train/test split
# # -----------------------------------------------------
# train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
# print(f"Train: {train_df.count()} rows")
# print(f"Test: {test_df.count()} rows")


# # -----------------------------------------------------
# # Cross validation (from your notebook)
# # -----------------------------------------------------
# paramGrid = (
#     ParamGridBuilder()
#     .addGrid(gbt.maxDepth, [3, 5, 7])
#     .addGrid(gbt.maxIter, [30, 50, 100])
#     .addGrid(gbt.stepSize, [0.05, 0.1, 0.2])
#     .addGrid(gbt.maxBins, [32, 64])
#     .build()
# )

# evaluator = BinaryClassificationEvaluator(
#     labelCol="label",
#     metricName="areaUnderROC"
# )

# cv = CrossValidator(
#     estimator=pipeline,
#     estimatorParamMaps=paramGrid,
#     evaluator=evaluator,
#     numFolds=3,
#     parallelism=4,
# )

# print("Starting model cross-validation training...")
# cv_model = cv.fit(train_df)
# best_model = cv_model.bestModel

# print("Cross-validation complete.")


# # -----------------------------------------------------
# # Evaluate
# # -----------------------------------------------------
# preds = best_model.transform(test_df)

# acc_eval = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
# f1_eval = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="f1")

# accuracy = acc_eval.evaluate(preds)
# f1 = f1_eval.evaluate(preds)

# print("========================================")
# print("Final Model Performance:")
# print(f"Accuracy: {accuracy}")
# print(f"F1 Score: {f1}")
# print("========================================")


# # -----------------------------------------------------
# # Save model (exactly like your notebook)
# # -----------------------------------------------------
# MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "model", "spark_gbt_model")

# print(f"Saving model to: {MODEL_SAVE_PATH}")
# best_model.write().overwrite().save(MODEL_SAVE_PATH)

# print("Model saved successfully.")

# spark.stop()




import pandas
import numpy as np
from numpy import column_stack
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import GBTClassifier, RandomForestClassifier
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator

# df = pandas.read_parquet("../data/sample/parquet_delay_and_weather_24/")
# label_df = pandas.read_parquet("../data/sample/parquet_delay_and_weather_24/")

df = pandas.read_parquet("data/sample/parquet_delay_and_weather_24/")
label_df = pandas.read_parquet("data/sample/parquet_delay_and_weather_24/")


cols_to_drop = [
    # Actual departure/arrival values → leakage
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
    "OriginCityName", "DestCityName",
    "DepTimeBlk", "ArrTimeBlk",
    "OriginTimezone", "DestTimezone",

    # Redundant timestamps
    "CRSDepTimestamp", "CRSArrTimestamp",

    # Columsn that have a lot of nan that seem useful
    'CancellationCode',
    'CarrierDelay','WeatherDelay','NASDelay',"SecurityDelay","LateAircraftDelay",
    "OriginWindGusts", "OriginTemperature", "OriginDewPoint",
    "DestWindGusts",'DestTemperature','DestDewPoint'
]

label_cols_to_drop = [
    # Actual departure/arrival values → leakage
    "DepTime",
    "DepartureDelayGroups", "TaxiOut", "WheelsOff", "WheelsOn",
    "TaxiIn", "ArrTime", "ArrivalDelayGroups",

    # After-fact outcomes
    "Cancelled", "Diverted",

    # Redundant ID fields
    "DestAirportID", "OriginAirportID", "DOT_ID_Marketing_Airline",
    "DOT_ID_Operating_Airline", "OriginAirportSeqID",
    "DestAirportSeqID", "OriginCityMarketID", "DestCityMarketID",
    "Flight_Number_Operating_Airline", "OriginICAO", "DestICAO",

    # Duplicated / unnecessary text fields
    "OriginCityName", "DestCityName",
    "DepTimeBlk", "ArrTimeBlk",
    "OriginTimezone", "DestTimezone",

    # Redundant timestamps
    "CRSDepTimestamp", "CRSArrTimestamp",

    # Columsn that have a lot of nan that seem useful
    'CancellationCode',
    'CarrierDelay','WeatherDelay','NASDelay',"SecurityDelay","LateAircraftDelay",
    "OriginWindGusts", "OriginTemperature", "OriginDewPoint",
    "DestWindGusts",'DestTemperature','DestDewPoint'
]


df.drop(columns=cols_to_drop, inplace=True)

label_df.drop(columns=label_cols_to_drop, inplace=True)
###df = df.dropna()#### Pretty bad, removes an entire row if something is null
#defining y

label_col = "DepDel15"

# 1. Drop rows where the label is missing
df = df.dropna(subset=[label_col])

# 2. Now it is safe to cast to int
y = df[label_col].astype(int)
df["label"] = y
df = df.drop(columns=[label_col])


def hhmm_to_hour(t):
    t = int(t)
    return t // 100

df["DepHour"] = df["CRSDepTime"].apply(hhmm_to_hour)
df["ArrHour"] = df["CRSArrTime"].apply(hhmm_to_hour)

def hhmm_to_minute(t):
    t = int(t)
    return t % 100

df["DepMinute"] = df["CRSDepTime"].apply(hhmm_to_minute)
df["ArrMinute"] = df["CRSArrTime"].apply(hhmm_to_minute)

df = df.drop(columns=["CRSDepTime", "CRSArrTime"])

df["FlightDate"] = pandas.to_datetime(df["FlightDate"])
df["is_weekend"] = df["FlightDate"].dt.dayofweek.isin([5, 6]).astype(int)

def arr_to_str(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "None"
    if isinstance(val, (list, np.ndarray)):
        if len(val) == 0:
            return "None"
        return ",".join(map(str, val))
    return str(val)
weather_array_cols = [
    "OriginPrecipitation", "OriginClouds",
    "DestPrecipitation", "DestClouds"
]

for col in weather_array_cols:
    df[col] = df[col].apply(arr_to_str)

df.rename(columns={'Operating_Airline ': 'Operating_Airline'}, inplace=True) # ?


# from pyspark import SparkConf
# conf = SparkConf().set("spark.driver.extraJavaOptions", "-Dlog4j.configuration=file:log4j.properties")
spark = SparkSession.builder.appName("Pandas to Spark").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
# spark = SparkSession.builder \
#     .appName("Pandas to Spark") \
#     .config(conf=conf) \
#     .getOrCreate()

####################################################################################################
# Compute medians from training data
numeric_cols_to_fill = [
    "Year", "Month", "DayofMonth", "DayOfWeek",
    "OriginWindDirection", "OriginWindSpeed", "OriginVisibility",
    "DestWindDirection", "DestWindSpeed", "DestVisibility",
    "DepHour", "ArrHour", "DepMinute", "ArrMinute", "is_weekend"
]

median_fill_values = {}
for col in numeric_cols_to_fill:
    median_value = df[col].median()
    if np.isnan(median_value):
        median_value = 0  # safe fallback
    median_fill_values[col] = median_value

# Fill numerics
df[numeric_cols_to_fill] = df[numeric_cols_to_fill].fillna(median_fill_values)


import json

with open("data/median_fill_values.json", "w") as f:
    json.dump(median_fill_values, f)



####################################################################################################

sdf = spark.createDataFrame(df)

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

num_cols = [
    "Year",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "OriginWindDirection",
    "OriginWindSpeed",
    "OriginVisibility",
    "DestWindDirection",
    "DestWindSpeed",
    "DestVisibility",
    "DepHour",
    "ArrHour",
    "DepMinute",
    "ArrMinute",
    "is_weekend"
]

# StringIndexers for all categorical features
indexers = [
    StringIndexer(
        inputCol=c,
        outputCol=c + "_idx",
        handleInvalid="keep"
    )
    for c in cat_cols
]

# OneHotEncoders for all indexed categorical features
encoders = [
    OneHotEncoder(
        inputCol=c + "_idx",
        outputCol=c + "_ohe"
    )
    for c in cat_cols
]

# VectorAssembler that combines encoded categoricals and numeric features
assembler = VectorAssembler(
    inputCols=[c + "_ohe" for c in cat_cols] + num_cols,
    outputCol="features",
    handleInvalid="keep"
)

# Classifier THIS GIVE A MODEL WITH AROUND 75% accuracy really quickly
gbt = GBTClassifier(
    labelCol="label",
    featuresCol="features",
    maxDepth=5,
    maxIter=50
)




# Pipeline
pipeline = Pipeline(stages=indexers + encoders + [assembler, gbt])

# Train test split
train_df, test_df = sdf.randomSplit([0.8, 0.2], seed=42)

# Fit model
gbt_model = pipeline.fit(train_df)

# Predictions
predictions = gbt_model.transform(test_df)

predictions.select("label", "prediction", "probability").show(50, truncate=False)



# Accuracy
acc_eval = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy"
)
accuracy = acc_eval.evaluate(predictions)

# F1 (overall)
f1_eval = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="f1"
)
f1 = f1_eval.evaluate(predictions)

print("Accuracy:", accuracy)
print("F1:", f1)

save_path = "./spark_gbt_model"
gbt_model.write().overwrite().save(save_path)
print(f"Model successfully saved to: {save_path}")
