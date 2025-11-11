# Makefile

PARQUET_DIR := ../data/sample/parquet
CSV_FILE := ../data/sample/flight_delay_aug2024_jul2025.csv

.PHONY: run

run:
	@if [ ! -f "$(CSV_FILE)" ]; then \
		echo "❌ Missing required file: $(CSV_FILE)"; \
		echo "Please add the flight_delay_aug2024_jul2025.csv file before continuing."; \
		exit 1; \
	fi; \
	if [ ! -d "$(PARQUET_DIR)" ]; then \
		echo "Directory $(PARQUET_DIR) not found. Running ingestion.py..."; \
		python3 ingestion.py; \
	else \
		echo "Directory $(PARQUET_DIR) exists. Skipping ingestion."; \
	fi; \
	echo "Running nick_bash.sh..."; \
	bash nick_bash.sh

