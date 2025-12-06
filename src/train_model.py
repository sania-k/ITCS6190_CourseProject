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
