# Methodology

This document describes the end-to-end methodology used in the flight delay prediction system, including batch pipelines, streaming components, and the machine learning workflow. The implementation is organized into modular components under `src/`.

---

## 1. Data Ingestion (`src/ingestion.py`)

### 1.1 Flight delay data

Flight statistics data (schedule and realized delay outcomes) is ingested using Spark.

• Load raw CSV files containing flight schedules, realized departure and arrival times, and delay indicators (for example `DepDel15`).
• Apply an explicit schema when possible; otherwise fall back to Spark schema inference.
• Normalize time-related fields (scheduled times, actual times) and key identifiers (airline codes, airport codes).

### 1.2 METAR weather data

Weather data is sourced from METAR reports via a REST API.

• Query METAR endpoints for origin and destination airports, keyed by ICAO/IATA code and timestamp.
• Parse raw METAR strings into structured fields such as wind direction, wind speed, visibility, precipitation, clouds, temperature, and dew point.
• Handle API rate limiting and retries, and persist raw responses for traceability.

### 1.3 Dataset join and Parquet output

Flight and METAR data are joined to create a unified training dataset.

• Join keys are based on airport (origin/destination) and time proximity between scheduled departure time and nearest METAR observation.
• Multiple station reports within the time window are resolved using deterministic rules (for example nearest in time or most recent before departure).
• The resulting dataset is written to disk as partitioned Parquet files to support efficient downstream batch processing and re-use.

---

## 2. Data Transformations (`src/transformations.py`)

The transformation stage converts the raw joined dataset into clean, model-ready features.

### 2.1 Feature engineering from raw data

Using the joined Parquet data, we derive structured features, including:

• Temporal features: year, month, day of month, day of week, weekend indicator, scheduled departure and arrival hour/minute (derived from `CRSDepTime` and `CRSArrTime`).
• Weather features: wind direction and speed, visibility, precipitation, and cloud categories for both origin and destination.
• Flight descriptors: marketing airline, operating airline, origin airport, and destination airport.

Where time is encoded as `HHMM` integers, helper functions convert them into hours and minutes, which are later used as numeric features.

### 2.2 Data cleaning and imputation

Cleaning is applied before modeling to ensure consistency.

• Drop or transform columns that introduce label leakage (for example realized departure time, realized delays, taxi times, and post-fact delay cause codes).
• Remove redundant identifiers and duplicate text fields that do not add modeling value.
• Handle missing values in the retained features. For the current workflow, rows with missing values in any selected feature or label are dropped, resulting in a fully non-null training set.
• Normalize array-like weather fields (for example precipitation and clouds) into deterministic string representations (for example comma-separated categories) to simplify downstream encoding.

### 2.3 Categorical encoding and scaling

Transformations prepare features for Spark ML models.

• Convert string fields (airlines, airports, weather category strings) into indexed categorical representations suitable for ML (for example StringIndexer + OneHotEncoder).
• Apply scaling or normalization to continuous variables (for example wind speed, visibility, time-of-day) when required by the chosen model.
• Persist the fitted encoders and scalers as part of the ML pipeline so that the same transformations can be applied consistently in training, validation, and streaming inference.

### 2.4 Train/test dataset creation

A deterministic split strategy is applied.

• Partition the cleaned dataset into training, validation, and test sets, typically using time-based or random splits depending on the experimental design.
• Store splits as separate Parquet datasets or partition tags to support reproducible experiments and consistent model comparison.

---

## 3. Streaming Pipeline (`src/streaming.py`)

The streaming component enables real-time delay prediction using Spark Structured Streaming.

### 3.1 Real-time flight data stream

• Ingest live or near-real-time flight events (for example from a message queue, Kafka topic, or REST poller) that contain upcoming flight schedules and identifiers.
• Optionally enrich the streaming data with a live METAR feed, applying similar join logic as in the batch pipeline but in a streaming context.

### 3.2 Spark Structured Streaming implementation

• Define a streaming DataFrame source for flight events and weather updates.
• Apply the same transformation and feature-engineering logic as the batch pipeline by reusing shared utilities and ML transformers.
• Use watermarking, windowing, and proper checkpointing to handle late data and guarantee exactly-once or at-least-once semantics as configured.

### 3.3 Real-time delay predictions

• Load the trained ML model and its associated feature pipeline in the streaming job.
• For each incoming flight record, build the feature vector and apply the model to produce real-time predictions of whether the flight will be delayed by at least 15 minutes.
• Attach prediction outputs and confidence scores to the event and write them to downstream sinks (for example dashboards, alerting systems, or storage).

### 3.4 Streaming aggregations and window functions

• Use window functions and aggregations to compute statistics over time, such as average predicted delay probability per airport, airline, or route.
• Maintain rolling metrics (for example 15-minute, 1-hour, or daily windows) to support operational monitoring and analytics.

---

## 4. ML Pipeline (`src/SparkFlightPredictionModel.ipynb`)

The ML pipeline encapsulates feature preparation, model training, evaluation, and analysis.

### 4.1 Predictive model definition

• Define models suitable for binary classification of `DepDel15` (0 = on-time, 1 = delayed 15+ minutes), such as gradient boosted trees, random forests, or logistic regression in Spark ML.
• Optionally combine multiple models or experiment with different algorithms while keeping the feature transformation pipeline fixed.

### 4.2 Feature selection and engineering

• Assemble all numeric and encoded categorical features into a single feature vector using a VectorAssembler.
• Perform feature selection or dimensionality reduction as needed, based on feature importance, correlation analysis, or domain knowledge.
• Iterate on feature engineering (for example additional temporal patterns, route-level aggregates, or historical delay rates) to improve predictive performance.

### 4.3 Model training and evaluation

• Train models on the training split and tune hyperparameters using cross-validation or train/validation splits.
• Evaluate models using metrics appropriate for imbalanced classification, such as precision, recall, F1, ROC-AUC, and PR-AUC, in addition to plain accuracy.
• Log results, configuration, and model artifacts for reproducibility.

### 4.4 Performance analysis and feature importance

• Use built-in feature importance (for example from tree-based models) and additional analysis to understand which features drive predictions.
• Aggregate performance by segment (for example by airline, airport, time-of-day, or weather regime) to identify strengths and weaknesses of the model.
• Summarize findings to guide further feature engineering and future model upgrades.

---

## 5. Utilities (`src/utils.py`)

The utilities module contains shared helpers used throughout ingestion, transformation, ML, and streaming.

### 5.1 Spark session management

• Provide a single entry point to create and configure a SparkSession with appropriate application name, logging, and resource settings.
• Encapsulate cluster-specific configuration (for example master URL, memory, shuffle settings) so that pipeline code remains environment-agnostic.

### 5.2 Data validation and schema checking

• Implement schema definitions and validation routines to ensure that ingested data matches expected types and constraints.
• Run checks for common issues (for example missing key columns, unexpected null rates, invalid categorical values) before continuing pipeline execution.

### 5.3 Date and time utilities

• Helper functions for converting between formats (for example `YYYYMMDD`, `HHMM`, timestamps), time zones, and calendar features.
• Functions for computing weekend flags, local vs UTC time, and aligning times between flight schedules and METAR observations.

---

## 6. Cross-Cutting Methodology

### 6.1 Data processing

The pipeline leverages Spark for distributed batch and streaming processing.

• Distributed batch computation for ingestion, joins, and feature engineering.
• Schema inference and explicit schema definitions where appropriate to ensure type correctness.
• Systematic handling of missing data through cleaning, filtering, and controlled imputation strategies.
• Use of Parquet as the primary storage format for efficient compression, predicate pushdown, and interoperability across batch and streaming components.

### 6.2 Feature engineering

Feature engineering is central to capturing the dynamics of flight delays.

• Temporal features: calendar variables and time-of-day representations capturing patterns such as peak hours and weekend effects.
• Weather-based features: wind, visibility, precipitation, and cloud conditions at both origin and destination.
• Historical and operational patterns: delay indicators and aggregated statistics can be incorporated in future iterations to capture route and airline behavior.
• Consistent categorical encoding across batch, ML, and streaming paths to maintain coherent feature spaces.

### 6.3 Analysis

Spark SQL and DataFrame APIs support exploratory analysis and monitoring.

• SQL queries on Parquet tables for quick inspection and slice-and-dice analysis across airports, airlines, and time periods.
• Window functions and aggregations to analyze trends, rolling averages, and distributions of delays.
• Statistical analysis and visualization (where integrated) to compare model predictions against observed outcomes and to validate assumptions.
• Feature importance analysis to guide data and modeling decisions.

### 6.4 ML and streaming integration

ML models are designed to be compatible with both batch scoring and real-time streaming.

• Train predictive models on historical batch data, then serialize them along with their feature pipelines.
• Load and apply the same models in the streaming pipeline for real-time inference.
• Track model performance over time using evaluation metrics; use this feedback to trigger retraining and hyperparameter tuning.
• Maintain a clear separation between data processing, feature engineering, and model logic to keep the system modular and extensible.

---

This methodology provides a consistent blueprint for how flight and weather data are ingested, transformed, modeled, and served, both in batch and in real time, using Spark as the core processing engine.

