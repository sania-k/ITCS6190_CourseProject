############################################################
# BASE SPARK + PYTHON IMAGE
############################################################
FROM python:3.10-slim-bookworm AS base
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    curl bash procps netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install Spark
ENV SPARK_VERSION=3.5.0
ENV HADOOP_VERSION=3
RUN curl -L "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
    | tar zx -C /opt/
RUN ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark

ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${PATH}"
ENV PYSPARK_PYTHON=python
ENV PYSPARK_DRIVER_PYTHON=python

# Python deps
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy whole project
COPY . .

############################################################
# TARGET 1 — INGESTION (CSV → Parquet)
############################################################
FROM base AS ingestion
WORKDIR /app
CMD ["python", "src/ingestion.py"]

############################################################
# TARGET 2 — STREAMING ONLY (TA DEMO MODE)
############################################################
FROM base AS stream
WORKDIR /app
CMD ["python", "src/streaming.py"]

############################################################
# TARGET 3 — MODEL TRAINER (Parquet → Model)
############################################################
FROM base AS trainer
WORKDIR /app
CMD ["spark-submit", "src/train_model.py"]

############################################################
# TARGET 4 — FASTAPI BACKEND
############################################################
FROM base AS backend
WORKDIR /app
EXPOSE 9998
CMD ["uvicorn", "src.backend:app", "--host", "0.0.0.0", "--port", "9998"]

############################################################
# TARGET 5 — PREDICTION DEMO
############################################################
FROM base AS predictor
WORKDIR /app
# We use spark-submit to ensure all PySpark context is loaded correctly
CMD ["spark-submit", "src/show_predictions.py"]