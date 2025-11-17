#!/bin/bash
set -e

## Ingestion to set up parquet dir
## TODO


# Start Streaming
unset SPARK_HOME

echo "Starting data streamer..."
python3 streaming.py &
STREAM_PID=$!
sleep 5

# Recieve streaming
echo "Starting Spark Structured Streaming job..."
python3 streaming_test.py

echo "Stopping streamer..."
kill $STREAM_PID

