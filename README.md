# ITCS6190 Course Project: Flight Delay Prediction with Apache Spark
## Video Link
1. https://drive.google.com/drive/folders/1VAKRo_Ntb1KMg5Vl06BTGdT37S7UKSh-?usp=sharing
## Overview

This is a comprehensive big data analysis project for **ITCS6190 (Cloud Computing for Data Analysis)** that designs and implements an end-to-end data pipeline using **Apache Spark**, SQL, Streaming, and MLlib. The project analyzes domestic flight data from Charlotte-Douglas International Airport (CLT) and correlates it with weather data to predict flight delays.

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
│       ├── flight_delay_*.csv          # Flight delay data
│       └── parquet/                    # Processed parquet files
├── docs/
│   ├── methodology.md                  # Detailed methodology
│   ├── dataset_overview.md             # Dataset schema documentation
│   ├── results.md                      # Analysis results
│   ├── limitations.md                  # Project limitations
│   └── reproduction_guide.md           # How to reproduce results
├── notebooks/
│   ├── eda.ipynb                       # Exploratory Data Analysis
│   ├── exploratory_analysis_viz.ipynb  # Visualization notebook
│   ├── ingestion.ipynb                 # Data ingestion examples
│   ├── transformations.ipynb           # Data transformation examples
│   ├── ml_pipeline.ipynb               # ML model pipeline
│   ├── sql_queries.ipynb               # SQL query examples
│   ├── complex_q.ipynb                 # Complex analysis queries
│   ├── complex_q_par.ipynb             # Parallel complex queries
│   └── streaming_demo.ipynb            # Streaming example
├── src/
│   ├── ingestion.py                    # Data ingestion pipeline
│   ├── transformations.py              # Data transformations
│   ├── streaming.py                    # Streaming job
│   ├── streaming_example.py            # Streaming example
│   ├── ml_pipeline.py                  # ML model training
│   └── utils.py                        # Utility functions
├── tests/
│   ├── test_ingestion.py               # Ingestion tests
│   ├── test_ml.py                      # ML pipeline tests
│   ├── test_sql.py                     # SQL tests
│   └── test_streaming.py               # Streaming tests
├── requirements.txt                     # Python dependencies
├── Makefile                             # Build targets
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
| `Weather_Phenomena` | Precipitation, fog, thunderstorms, etc. |

**Airports Included** (Top 10 US airports):
- ATL (Atlanta), DFW (Dallas/Fort Worth), DEN (Denver)
- ORD (Chicago), LAX (Los Angeles), JFK (New York)
- CLT (Charlotte), LAS (Las Vegas), MCO (Orlando), MIA (Miami)

---

## Technology Stack

### Core Technologies
- **Apache Spark 3.x** - Distributed data processing and SQL
- **PySpark** - Python API for Spark
- **Python 3.8+** - Programming language
- **SQL** - Data querying and analysis
- **Jupyter Notebooks** - Interactive analysis and visualization

### Libraries & Tools
- **pandas** - Data manipulation and analysis
- **matplotlib** - Data visualization
- **pytest** - Unit testing framework
- **metar_taf_parser** - METAR weather data parsing
- **requests** - HTTP library for API calls

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

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ITCS6190_CourseProject
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify the installation**
   ```bash
   python -c "import pyspark; print('PySpark version:', pyspark.__version__)"
   ```

### Running the Project

#### Option 1: Run the complete pipeline
```bash
bash run.sh
```

#### Option 2: Using Make
```bash
make run
```

#### Option 3: Run individual components
```bash
python src/ingestion.py
python src/transformations.py
python src/streaming.py
python src/ml_pipeline.py
```

---

## Project Components

### 1. Data Ingestion (`src/ingestion.py`)
- Load flight delay CSV data using Spark
- Fetch METAR weather data via REST API
- Join flight and weather datasets
- Save processed data as Parquet files

### 2. Data Transformations (`src/transformations.py`)
- Feature engineering from raw data
- Data cleaning and imputation
- Categorical encoding and scaling
- Creating training/test datasets

### 3. Streaming Pipeline (`src/streaming.py`)
- Real-time flight data stream processing
- Spark Structured Streaming implementation
- Real-time delay predictions
- Stream aggregations and window functions

### 4. ML Pipeline (`src/ml_pipeline.py`)
- Predictive models for flight delays
- Feature selection and engineering
- Model training and evaluation
- Performance metrics and feature importance

### 5. Utilities (`src/utils.py`)
- Spark session management
- Data validation and schema checking
- Date/time manipulation and timezone conversion

---

## Analysis & Notebooks

The project includes Jupyter notebooks for exploratory analysis:

| Notebook | Purpose |
|----------|---------|
| `eda.ipynb` | Exploratory Data Analysis |
| `exploratory_analysis_viz.ipynb` | Visualizations and statistics |
| `ml_pipeline.ipynb` | Model training and evaluation |
| `sql_queries.ipynb` | SQL-based analysis |
| `streaming_demo.ipynb` | Streaming pipeline demo |

---

## Testing

Run tests with pytest:
```bash
pytest
pytest tests/test_ingestion.py -v
pytest --cov=src tests/
```

---

## Key Features

### Data Processing
- ✓ Distributed batch processing with Spark  
- ✓ Schema inference and type detection  
- ✓ Missing data handling  
- ✓ Efficient Parquet storage  

### Feature Engineering
- ✓ Temporal features  
- ✓ Weather-based features  
- ✓ Historical delay patterns  
- ✓ Categorical encoding  

### Analysis
- ✓ SQL-based queries  
- ✓ Window functions and aggregations  
- ✓ Statistical analysis  
- ✓ Feature importance  

### ML & Streaming
- ✓ Predictive models  
- ✓ Real-time streaming  
- ✓ Model evaluation metrics  
- ✓ Hyperparameter tuning  

---

## Documentation

Comprehensive documentation in `docs/`:
- **methodology.md** - Project methodology
- **dataset_overview.md** - Data schema and dictionary
- **results.md** - Analysis findings
- **limitations.md** - Project constraints
- **reproduction_guide.md** - Reproduction steps

---

## Performance & Optimization

- **Partitioning**: Data partitioned by date and airport
- **Caching**: Frequently used DataFrames cached
- **Broadcasting**: Small lookup tables broadcasted
- **Columnar Format**: Parquet for efficient I/O
- **Scalability**: Supports datasets > 1TB

---

## Troubleshooting

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
- [Bureau of Transportation Statistics](https://www.bts.gov/)
- [METAR Format](https://en.wikipedia.org/wiki/METAR)
- [Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)

---

## License

See `LICENSE` file for details.

---

## Contact

For questions or issues:
- Open an issue in the repository
- Contact the project team members

---

**Last Updated**: November 16, 2025  
**Project Status**: Active Development  
**Course**: ITCS6190 - Cloud Computing for Data Analysis
