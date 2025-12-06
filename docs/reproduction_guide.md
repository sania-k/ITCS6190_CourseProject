# Reproduction Guide

This guide explains how to set up the environment and rerun the full flight delay prediction pipeline, including data ingestion, transformations, streaming, and the ML pipeline.

The instructions assume you are working with the `ITCS6190_CourseProject` repository.

## Technology Stack

### Core Technologies
- **Apache Spark 3.x** - Distributed data processing and SQL
- **PySpark** - Python API for Spark
- **Python 3.8+** - Programming language
- **SQL** - Data querying and analysis
- **Jupyter Notebooks** - Interactive analysis and visualization
- **Docker** - Building and running containers

### Libraries & Tools
- **pyspark==3.5.0** – Distributed data processing framework for big data analytics.  
- **pandas** – Data manipulation and analysis library for structured data.  
- **matplotlib** – Plotting library for creating visualizations in Python.  
- **pytest** – Framework for writing and running Python tests.  
- **requests** – Simplifies making HTTP requests in Python.  
- **metar-taf-parser-mivek** – Parses METAR and TAF aviation weather data.  
- **numpy** – Provides support for  arrays and functions.  
- **pyarrow** – Enables data processing.  
- **uvicorn[standard]** – ASGI server for running Python web applications.  
- **fastapi** – Web framework for building APIs with Python.

### Data Formats
- **CSV** - Input flight delay data
- **Parquet** - Optimized columnar storage for processed data
- **Spark DataFrame** - In-memory distributed data structures

---

## 1. Getting Started

### 1.1 Prerequisites

You need the following installed on your machine.

1. Python 3.8 or higher

   Check your version:

   ```bash
   python --version
   ```

2. Java 8 or higher (required for Apache Spark)

   ```bash
   java -version
   ```

3. Apache Spark 3.0 or newer

   You can download Spark from the Apache Spark website.
   After installation, verify:

   ```bash
   spark-submit --version
   ```

### 1.2 Clone the repository

1. Clone the project repository and enter the project directory:

   ```bash
   git clone git@github.com:sania-k/ITCS6190_CourseProject.git
   cd ITCS6190_CourseProject
   ```

2. (Optional) Create and activate a virtual environment for Python to keep dependencies isolated.

---

## 2. Installation

### 2.1 Install Python dependencies

From inside the project root:

```bash
pip install -r requirements.txt
```

### 2.2 Verify the PySpark installation

Confirm that PySpark is installed and can be imported:

```bash
python -c "import pyspark; print('PySpark version:', pyspark.__version__)"
```

If this command prints a version string without errors, the Python side of Spark is correctly installed.

---

## 3. Data Preparation

This project expects flight delay and METAR weather data that has been or will be stored in Parquet format by the ingestion step.

1. Ensure that any required configuration for data locations or API keys is set as expected by `src/ingestion.py`
   For example, this may involve:
   • File paths for raw flight CSV data
   • Credentials or endpoints for the METAR REST API

2. If necessary, edit configuration variables, environment variables, or a config file (if used) so that `ingestion.py` can:
   • Read flight CSV files
   • Fetch METAR data
   • Write the joined dataset to the intended Parquet output directory

Consult the main project README or comments in `src/ingestion.py` if you are unsure about paths or configuration.

---

## 4. Running the Project

You can reproduce the full pipeline in several ways.

### 4.1: Run the complete pipeline

If you want to execute the complete end to end workflow with frontend (ingestion, transformations, ML, and streaming demo if included):
#### In order to run the full project, including frontend, use Docker
```bash
make all
```
Then visit `localhost:3000`


### 4.2: Optional Ways:

#### Option 1: Run:

   ```bash
   bash run.sh
   ```
   
   This script should orchestrate each major step in the correct order.

### Option 2: Use Make

If the project includes a Makefile, you can run:
   
   ```bash
   make run
   ```

This provides a single command that wraps the same steps defined in `run.sh`.

### Option 3: Run individual components

You can also run each stage separately for debugging or experimentation.

## 5. Reproducing Results

To reproduce the main experimental results reported for this project:

1. Run `src/ingestion.py` to generate the joined flight and METAR Parquet dataset if it does not already exist.
2. Run `notebooks/SparkFlightPrediction.ipnyb` to produce cleaned features, train the model, and compute evaluation metrics.
3. Optionally run `src/streaming.py` to demonstrate real time predictions using the trained model.
   - Run `src/streaming_example.py` to view the results in terminal.

If the project stores metrics or model outputs in a particular directory (for example `outputs/` or `models/`), those locations will contain the artifacts you can compare against previously reported results.

---

## 6. Troubleshooting

If something does not work as expected:

1. Verify that your Java and Spark versions match those required.
2. Confirm that environment variables or config files for data paths and API keys are set correctly.
3. Check the logs printed by Spark and the Python scripts, especially for:
   • Missing data files
   • Incorrect schemas
   • Network issues when calling the METAR API


**Spark fails to initialize**:
```bash
java -version
export SPARK_HOME=/path/to/spark
```

**Out of memory**:
```bash
spark-submit --executor-memory 4g src/ingestion.py
spark-submit --driver-memory 2g src/ingestion.py
```

**Module not found**:
```bash
pip install -r requirements.txt --force-reinstall
```

After fixing configuration or data issues, rerun the relevant step or use `bash run.sh` to rerun the full pipeline.

---

This reproduction guide should allow another user to install the dependencies, prepare the data, and rerun the full flight delay pipeline using the same methodology you used.

