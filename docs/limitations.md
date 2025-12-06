# Limitations
---

This document describes the key limitations of the current delay-prediction pipeline that uses joined Flight Statistics and METAR data and trains models in Spark.

## 1. Limited Data Availability (≈ 6 Months)

**Description**
The data source currently only provides roughly six months of flight and weather history at a time. As a result, the training and evaluation dataset is restricted to this time window.

**Impact**

* The model cannot fully learn **long-term seasonality** (e.g., year-over-year holiday effects, summer vs. winter patterns across multiple years).
* Performance metrics may be **biased toward recent conditions** (specific schedules, airline behaviors, airport operations, and weather patterns in that half-year window).
* It is harder to assess **model robustness** under rare or extreme conditions that may not occur in every six-month slice (e.g., major storms, large-scale disruptions).

**Potential Mitigations (Future Work)**

* Incorporate **archived historical data** if/when storage and access constraints are resolved.
* Periodically retrain and **compare models across windows** (e.g., rolling six-month windows) to monitor stability.
* Use **domain knowledge features** (e.g., holiday flags, seasonal indicators) to partially compensate for missing multi-year history.

---

## 2. Imbalanced Dataset

**Description**
The label `DepDel15` (departure delay ≥ 15 minutes) is not evenly distributed: on-time / low-delay flights are more frequent than significantly delayed flights. This creates an **imbalanced classification problem**.

**Impact**

* A naive model can achieve **high accuracy** by mostly predicting “no delay,” while still performing poorly on the **minority class** (delayed flights).
* Metrics like plain accuracy or macro-averaged loss can **hide poor recall** on delayed flights, which are often the most operationally important cases.
* Threshold selection and calibration become more sensitive; the default decision boundary may not align with business priorities (e.g., catching as many true delays as possible).

**Potential Mitigations (Future Work)**

* Use **class-aware metrics** during evaluation (e.g., precision/recall, F1, ROC-AUC, PR-AUC, confusion matrix by class).
* Apply **rebalancing strategies**:

  * Class weighting in the loss function
  * Oversampling the delayed class or undersampling the majority class
* Explore **cost-sensitive modeling**, where misclassifying a delayed flight is penalized more heavily than misclassifying an on-time flight.

---

## 3. Modeling Framework Constraints (Spark vs. PyTorch)

**Description**
The current pipeline is built around **Apache Spark** (pandas → Spark DataFrame → Spark ML pipeline). While Spark is strong at distributed data processing and classical ML workflows, it is less convenient for experimenting with **advanced deep learning architectures** compared to frameworks like PyTorch.

**Impact**

* Model selection is effectively limited to what is easily supported in Spark ML (e.g., tree-based models, linear models, gradient boosting), which may be sufficient but less flexible than modern DL frameworks.
* Implementing architectures like **RNNs, LSTMs, temporal CNNs, or Transformers** for sequence-based modeling (e.g., sequences of METAR reports over time) is **more complex** and requires additional integration layers (Spark → PyTorch).
* Rapid prototyping and hyperparameter tuning for deep models is **more cumbersome** than in a pure PyTorch or Pythonic ML environment.

**Potential Mitigations (Future Work)**

* Introduce a **hybrid architecture**:

  * Use Spark for data ingestion, joins, and feature engineering
  * Export clean feature sets to a **PyTorch training pipeline** for more advanced models.
* Evaluate frameworks and integrations such as:

  * Spark + PyTorch (e.g., using Petastorm, TorchDistributor, or similar patterns)
  * Model serving that’s agnostic to the training framework (Spark only as a data/feature layer).
* Start with Spark ML baselines, then **incrementally layer in** PyTorch models where they provide clear performance or modeling advantages (e.g., temporal modeling of evolving weather features).

---

## 4. Summary

In its current form, the pipeline is:

* **Data-limited** to ≈ six months of history,
* Operating on an **imbalanced classification problem**, and
* Constrained by a **Spark-centric modeling stack** that is less flexible for deep learning architectures than PyTorch.

These limitations don’t prevent the system from being useful, but they are important context for interpreting results and planning future improvements.


