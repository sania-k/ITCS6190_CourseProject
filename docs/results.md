Below is a clean, well-structured **results README.md** that you can drop directly into `docs/results.md` or a top-level `RESULTS.md`. It summarizes model performance, major findings, issues, limitations, and front-end behavior.

---

#  Flight Delay Prediction – Results Summary

This document presents the results of the **ITCS6190 Course Project: Flight Delay Prediction with Apache Spark**. The goal of the project was to build an end-to-end big data pipeline for predicting flight delays using historical flight records and weather observations (METAR).

---

##  Model Performance

We trained multiple machine learning models using Spark MLlib.
The **Gradient Boosted Trees (GBT) classifier** achieved the best performance.

### **Final Model: Gradient Boosted Trees (GBT)**

| Metric         | Result                                                        |
| -------------- | ------------------------------------------------------------- |
| **Accuracy**   | **~76%**                                                       |
| F1      | ~72%              |


**Interpretation:**
The model is reasonably good at predicting **on-time flights**, but less accurate for the minority class (**delayed flights**). This reflects the strong class imbalance in real-world delay data.

---

##  Experiment Summary

### Features Used

* **Flight attributes**
  Departure time, day of week, airline, destination, month, distance, historical delay fields.
* **Weather features**
  Temperature, visibility, cloud ceiling, wind speed/gust, altimeter reading, weather phenomena, etc.

### Key Observations

* Weather features were valuable but **had high missingness** → reduced their overall predictive contribution.
* Departure time and airline were among the **strongest predictors**.
* The model improved when categorical features were properly encoded and numerical features standardized.

---

##  Known Issues & Challenges

### **1. Missing and Null Weather Columns**

A significant portion of METAR data could not be matched to flight timestamps or airports.
This created:

* High null rates in weather-related fields
* Reduced model reliability on weather-heavy predictions
* Need for additional imputation logic or richer weather-data sources

### **2. Class Imbalance**

Most flights are not delayed → creates skewed learning.

* Majority class: **on time / <15 min delay**
* Minority class: **true delays (>15 min)**

As a result:

* The model tends to predict “on time” more confidently.
* Recall for delayed flights is limited.
* Performance ceiling is largely dictated by dataset imbalance.

Future improvement: Apply SMOTE, class weighting, or anomaly-style modeling.

### **3. METAR–Flight Alignment Challenges**

* METAR reports are published irregularly (often hourly).
* Flight times are not evenly distributed.
* Weather may change rapidly → timestamp mismatch introduces noise.

---

## Key Findings

* **Flight delays correlate strongly with airline and departure hour.**
* **Weather contributes meaningful signal but is incomplete**, lowering potential model accuracy.
* **GBT outperformed logistic regression, random forest, and baseline models** due to its ability to handle nonlinear relationships.
* Even with limitations, a **76% accuracy** is strong given the noisy and incomplete data.

---

##  Front-End Application Results

A simple web front-end allows end users to input:

* **Destination airport**
* **Airline**
* **Day of week**

The app then queries the trained model and returns:

### ** Prediction: Will your flight be delayed (yes/no)?**

This provides an interactive demonstration of how Spark MLlib outputs can be operationalized into a user-facing tool.

Future extensions could include:

* Showing predicted probability (confidence score)
* Visualizing feature contribution (SHAP values)
* Incorporating live weather streams for real-time predictions

---

##  Conclusions

* The project successfully demonstrates a **full big-data + ML pipeline** using Spark.
* The model achieves **solid performance** given real-world dataset imperfections.
* There is substantial room for improvement by:

  * Enriching weather data
  * Reducing null rates
  * Addressing class imbalance
  * More advanced hyperparameter tuning

Overall, the system provides a functional and extendable starting point for operational flight delay prediction.

---

##  Future Work

* Add **SMOTE or cost-sensitive learning** for improved minority-class detection.
* Enhance **weather ingestion** (e.g., nearest-neighbor METAR matching, NOAA bulk datasets).
* Incorporate **historical delay baselines per route/airline/time block**.
* Deploy model using **real-time streaming** and a more robust front-end interface.

---


