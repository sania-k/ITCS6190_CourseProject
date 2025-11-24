#################################################
# BASE IMAGE 
#################################################
FROM python:3.10-slim-bookworm AS base
WORKDIR /app

# System wide dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    curl \
    bash \
    procps \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Java
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Spark
ENV SPARK_VERSION=3.5.0
ENV HADOOP_VERSION=3

RUN curl -L "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
    | tar zx -C /opt/

RUN ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark

ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${PATH}"
ENV PYSPARK_PYTHON=python
ENV PYSPARK_DRIVER_PYTHON=python

# Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy project
COPY . .

#################################################
# BUILD TARGET: full pipeline
#################################################
FROM base AS full
WORKDIR /app
RUN chmod +x run.sh

CMD ["bash", "run.sh"]

#################################################
# BUILD TARGET: STREAM ONLY
#################################################
FROM base AS stream_only
WORKDIR /app
CMD ["python", "-u", "src/streaming.py"]
