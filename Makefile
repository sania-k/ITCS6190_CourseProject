# # IMAGE_NAME=flight-delay-pipeline

# # # Run full pipeline
# # run:
# # 	docker build --target full -t $(IMAGE_NAME) .
# # 	docker run --rm -p 9998:9998 $(IMAGE_NAME)

# # # Build full image only
# # build:
# # 	docker build --target full -t $(IMAGE_NAME) .

# # # Run ONLY the streaming server
# # stream:
# # 	docker build --target stream_only -t flight-delay-stream .
# # 	docker run --rm -p 9998:9998 flight-delay-stream

# # # Debug shell inside full container
# # shell:
# # 	docker build --target full -t $(IMAGE_NAME) .
# # 	docker run --rm -it $(IMAGE_NAME) bash























# # ------------------------------
# # Images
# # ------------------------------
# INGESTION_IMAGE=ingestion
# STREAM_IMAGE=stream
# TRAINER_IMAGE=trainer
# BACKEND_IMAGE=flight-backend
# FRONTEND_IMAGE=flight-frontend

# # ------------------------------
# # 1. Full first-time setup (NO STREAMING)
# # ------------------------------
# first-time:
# 	@echo "🔧 Ingestion (CSV → Parquet)..."
# 	docker build --target ingestion -t $(INGESTION_IMAGE) .
# 	docker run --rm -it $(INGESTION_IMAGE)

# 	@echo "Training ML Model..."
# 	docker build --target trainer -t $(TRAINER_IMAGE) .
# 	docker run --rm -it \
# 		-v $(PWD)/data:/app/data \
# 		-v $(PWD)/spark_gbt_model:/app/spark_gbt_model \
# 		$(TRAINER_IMAGE)

# 	@echo "First-time setup complete!"
# 	@echo "Run: make up"

# # ------------------------------
# # 2. Scenario 1 — TA Demo: Streaming After Ingestion
# # ------------------------------
# stream-demo:
# 	@echo "Running ingestion..."
# 	docker build --target ingestion -t $(INGESTION_IMAGE) .
# 	docker run --rm -it $(INGESTION_IMAGE)

# 	@echo "Starting streaming (demo mode)..."
# 	docker build --target stream -t $(STREAM_IMAGE) .
# 	docker run --rm -it $(STREAM_IMAGE)

# # ------------------------------
# # 3. Scenario 3 — Start App Normally
# # ------------------------------
# up:
# 	docker compose up --build

# up-d:
# 	docker compose up -d --build

# down:
# 	docker compose down

# # ------------------------------
# # 4. Re-run ingestion only
# # ------------------------------
# ingest:
# 	docker build --target ingestion -t $(INGESTION_IMAGE) .
# 	docker run --rm -it $(INGESTION_IMAGE)
		
# # ------------------------------
# # 5. Retrain the model only
# # ------------------------------
# train:
# 	docker build --target trainer -t $(TRAINER_IMAGE) .
# 	docker run --rm -it \
# 	    -v $(PWD)/data:/app/data \
# 	    -v $(PWD)/spark_gbt_model:/app/spark_gbt_model \
# 	    $(TRAINER_IMAGE)
# # ------------------------------
# # 6. Debug shells
# # ------------------------------
# shell-backend:
# 	docker exec -it flight-backend bash

# shell-frontend:
# 	docker exec -it flight-frontend sh

# build-backend:
# 	docker compose build --no-cache backend

















# ---------------------------------------
# Image names
# ---------------------------------------
INGESTION_IMAGE=ingestion
TRAINER_IMAGE=trainer
BACKEND_IMAGE=flight-backend
FRONTEND_IMAGE=flight-frontend

# ---------------------------------------
# 1. Full pipeline (run EVERYTHING)
# ---------------------------------------
all: ingest train build-backend build-frontend up

# ---------------------------------------
# 2. Ingestion (CSV → Parquet)
# ---------------------------------------
ingest:
	@echo "Ingestion..."
	docker build --target ingestion -t $(INGESTION_IMAGE) .
	docker run --rm -it $(INGESTION_IMAGE)

# ---------------------------------------
# 3. Train ML model
# ---------------------------------------
train:
	@echo "Training ML model..."
	docker build --target trainer -t $(TRAINER_IMAGE) .
	docker run --rm -it \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/spark_gbt_model:/app/spark_gbt_model \
		$(TRAINER_IMAGE)

# ---------------------------------------
# 4. Build backend image
# ---------------------------------------
build-backend:
	@echo "Building backend..."
	docker compose build --no-cache backend

# ---------------------------------------
# 5. Build frontend image
# ---------------------------------------
build-frontend:
	@echo "Building frontend..."
	docker compose build --no-cache frontend

# ---------------------------------------
# 6. Bring system up / down
# ---------------------------------------
up:
	docker compose up --build

up-d:
	docker compose up -d --build

down:
	docker compose down

# ---------------------------------------
# 7. Shell access
# ---------------------------------------
shell-backend:
	docker exec -it flight-backend bash

shell-frontend:
	docker exec -it flight-frontend sh

# Add this to the variables section at the top
PREDICTOR_IMAGE=predictor

# Add this command to the list of targets
# ---------------------------------------
# 8. Run Prediction Demo
# ---------------------------------------
predict:
	@echo "Running prediction demo..."
	docker build --target predictor -t $(PREDICTOR_IMAGE) .
	docker run --rm -it \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/spark_gbt_model:/app/spark_gbt_model \
		$(PREDICTOR_IMAGE)