# ITCS6190 Course Project: Flight Delay Prediction with Apache Spark
## Video Demo Link
1. https://drive.google.com/drive/folders/1VAKRo_Ntb1KMg5Vl06BTGdT37S7UKSh-?usp=sharing# ITCS6190 Course Project: Flight Delay Prediction with Apache Spark

## Overview

This is a comprehensive big data analysis project for **ITCS6190 (Cloud Computing for Data Analysis)** that designs and implements an end-to-end data pipeline using **Apache Spark**, SQL, Streaming, and MLlib. The project analyzes domestic flight data from Charlotte-Douglas International Airport (CLT) with weather data to predict flight delays.

### Project Goal

Determine the likelihood of flight delays by analyzing the relationship between:
- Flight characteristics (departure time, destination, airline, etc.)
- Weather conditions at origin and destination airports
- Historical delay patterns

### Team Members

1. Anshuk Gottipati
2. Frank Garcia
3. Nicholas Cassarino
4. Purva Rajaram Jagtap
5. Sania Khan

---

## Project Structure

```
ITCS6190_CourseProject/
├── data/
│   └── sample/
│       ├── flight_delay_[year].csv     # Flight delay data for that year/date range
│       └── parquet/                    # Processed parquet files
├── docs/
│   └── slides/                         # Presentation slides on the project
│   ├── methodology.md                  # Detailed methodology
│   ├── dataset_overview.md             # Dataset documentation
│   ├── results.md                      # Project results
│   ├── limitations.md                  # Project limitations
│   └── reproduction_guide.md           # How to reproduce results
├── frontend/                         
├── notebooks/
│   ├── eda.ipynb                       # Exploratory Data Analysis
│   ├── exploratory_analysis_viz.ipynb  # Exploratory Visualizations
│   ├── ingestion.ipynb                 # Data ingestion examples
│   ├── complex_q.ipynb                 # Complex analysis on flight delays
│   ├── complex_q_par.ipynb             # Parallel complex on flight delays+weather
│   └── SparkFlightPrediction.ipynb     # Training ML model
├── src/
│   ├── Makefile                        # Automates build process
│   ├── run_bash.sh                     # Executes pipeline
│   ├── show_predictions.py             # Batch delay predictions
│   ├── backend.py                      # Serves ML predictions 
│   ├── ingestion.py                    # Data ingestion pipeline
│   ├── streaming.py                    # Streamings flight+weather data
│   ├── streaming_example.py            # Picks up streamed data
│   ├── ml_pipeline.py                  # Runs model inference 
│   ├── train_model                     # Training ML model
├── spark_gbt_model/                    # Delay Prediction Model
├── .dockerignore                       # Files Docker should ignore
├── .gitignore                          # Files git should ignore
├── requirements.txt                    # Python dependencies
├── Makefile                            # Automates project workflow
├── Dockerfile                          # Builds service images
├── docker-compose.yml                   # Defines service containers 
├── run.sh                               # Main execution script
└── README.md                            # This file
```

---

## Data Overview

### Flight Delay Data

The project uses flight delay datasets from the Bureau of Transportation Statistics, covering domestic flights with details about:
- **Time Information**: Scheduled/actual departure and arrival times
- **Route Information**: Origin and destination airports, cities
- **Delay Information**: Delay types (carrier, weather, NAS, security, late aircraft)
- **Flight Details**: Airline, flight number, aircraft movement times
- **Aggregate Data**: Distance, elapsed time, taxi times

**Sample Data Location**: `data/sample/flight_delay_*.csv`

**Key Flight Data Columns**:
- `FlightDate`, `DayOfWeek`, `Month`, `Year` - Temporal information
- `Origin`, `Dest` - Airport codes
- `CRSDepTime`, `DepTime` - Scheduled vs. actual departure
- `DepDelay`, `DepDelayMinutes` - Departure delay metrics
- `DepDel15` - Binary flag: delay > 15 minutes
- `WeatherDelay`, `CarrierDelay`, `NASDelay` - Delay categories
- `Distance`, `CRSElapsedTime` - Flight characteristics
- `TaxiOut`, `TaxiIn`, `AirTime` - Operational times

### Weather Data (METAR)

The pipeline enriches flight data with METAR (Meteorological Aerodrome Report) weather observations fetched via API:

**Weather Features**:

| Feature | Description |
|---------|-------------|
| `Wind_Direction` | Wind direction in degrees |
| `Wind_Speed` | Wind speed in knots |
| `Wind_Gust` | Wind gust speed (knots) |
| `Visibility` | Horizontal visibility (statute miles) |
| `Temperature` | Temperature (°C) |
| `Dewpoint` | Dewpoint temperature (°C) |
| `Altimeter` | Altimeter pressure (inches Hg) |
| `Cloud_Coverage` | Cloud information (coverage and altitude) |
| `Precipitation` | Precipitation, fog, thunderstorms, etc. |

**Airports Included** (Top 10 US airports):
- ATL (Atlanta)
- DFW (Dallas/Fort Worth)
- DEN (Denver)
- ORD (Chicago)
- LAX (Los Angeles)
- JFK (New York)
- - CLT (Charlotte)
  - LAS (Las Vegas)
  - MCO (Orlando)
  - MIA (Miami)

---

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

## Getting Started

### Prerequisites

1. **Python 3.8 or higher**
   ```bash
   python --version
   ```

2. **Java 8 or higher** (required for Apache Spark)
   ```bash
   java -version
   ```

3. **Apache Spark 3.0+**
   - [Download from Apache Spark](https://spark.apache.org/downloads.html)
   - Verify installation:
     ```bash
     spark-submit --version
     ```

### Installation

1. Clone the project repository and enter the project directory:

   ```bash
   git clone git@github.com:sania-k/ITCS6190_CourseProject.git
   cd ITCS6190_CourseProject
   ```

2. (Optional) Create and activate a virtual environment for Python to keep dependencies isolated.

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify the installation**
   ```bash
   python -c "import pyspark; print('PySpark version:', pyspark.__version__)"
   ```

### Running the Project

#### In order to run the full project, including frontend, use Docker
```bash
make all
```
Then visit `localhost:3000`


#### Run the complete pipeline (without frontend):
##### Option 1:
```bash
bash run.sh
```

##### Option 2: Using Make
```bash
make run
```


---

## Project Components

| File | Purpose |
|------|----------|
| **Makefile** | Automates project pipeline tasks like building, running, and testing. |
| **src/backend.py** | Contains backend logic, including API endpoints or server-side functions.|
| **src/ingestion.py** | Handles data ingestion from multiple sources into the pipeline.|
| **src/ml_pipeline.py** | Manages data input into the machine learning model. |
| **src/run_bash.sh** | Shell script for executing pipeline tasks in sequence. |
| **src/show_predictions.py** | Displays or visualizes predictions from the ML model. |
| **src/streaming.py** | Implements streaming for real-time data processing.  |
| **src/streaming_example.py** | Example or test script for streaming functionality. |
| **src/train_model.py** | Trains the machine learning model on input data.  |
| **udfs.py** | Contains user-defined functions to support custom backend logic. |

---

## Analysis & Notebooks

The project includes Jupyter notebooks for exploratory analysis in `notebooks/`:

| File | Purpose |
|------|---------|
| **notebooks/eda.ipynb** | Exploratory Data Analysis |
| **notebooks/exploratory_analysis_viz.ipynb** | Exploratory Visualizations |
| **notebooks/ingestion.ipynb** | Data ingestion examples |
| **notebooks/complex_q.ipynb** | Complex analysis on flight delays |
| **notebooks/complex_q_par.ipynb** | Parallel complex analysis on flight delays + weather |
| **notebooks/SparkFlightPrediction.ipynb** | Training ML model |

---

## Key Features

### Data Processing
- Distributed batch processing with Spark  
- Schema inference and type detection  
- Missing data handling  
- Efficient Parquet storage  

### Feature Engineering
- Temporal features  
- Weather-based features  
- Historical delay patterns  
- Categorical encoding  

### Analysis
- SQL-based queries  
- Window functions and aggregations  
- Statistical analysis  
- Feature importance  

### ML & Streaming
- Predictive models  
- Model evaluation metrics  
- Hyperparameter tuning  

---

## Documentation

Comprehensive documentation in `docs/`:
- **methodology.md** - Project methodology
- **dataset_overview.md** - Data information
- **results.md** - Project findings
- **limitations.md** - Project constraints
- **reproduction_guide.md** - Reproduction steps

---

## Performance & Optimization

- **Partitioning**: Data partitioned by date and airport
- **Caching**: Frequently used data cached
- **Broadcasting**: Small lookup tables broadcasted
- **Columnar Format**: Parquet for efficient I/O
- **Scalability**: Supports datasets > 1TB

---

## Troubleshooting

**Next.js shows errors on localhost:3000**:
```bash
# Refresh localhost:3000 repeatedly
# Errors stop showing once the backend is fully warmed up
```

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

---

## Contributing

1. Create a feature branch
2. Make changes and test
3. Write/update tests
4. Submit pull request

---

## References

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [PySpark API](https://spark.apache.org/docs/latest/api/python/)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [Bureau of Transportation Statistics Flight Delay Data](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGK&QO_fu146_anzr=b0-gvzr)
- [METAR Data](https://flightsupport24.com/map/#/metar-archive)
     - NOTE: this website has recently been taken down
- [METAR Format](https://en.wikipedia.org/wiki/METAR)
- [Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
