#!/bin/bash
set -e

echo "=============================================="
echo "=== Running Flight Delay Spark Pipeline ==="
echo "=============================================="

echo "[1/3] Starting INGESTION..."
python src/ingestion.py
echo "[1/3] Ingestion COMPLETE"
echo "----------------------------------------------"

echo "[2/3] Starting STREAMING..."
python src/streaming.py
echo "[2/3] Streaming COMPLETE (server exited)"
echo "----------------------------------------------"

echo "[3/3] Starting ML PIPELINE..."
python src/ml_pipeline.py
echo "[3/3] ML Pipeline COMPLETE"
echo "----------------------------------------------"

echo "=== FULL PIPELINE COMPLETE ==="