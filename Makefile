IMAGE_NAME=flight-delay-pipeline

# Run full pipeline
run:
	docker build --target full -t $(IMAGE_NAME) .
	docker run --rm -p 9998:9998 $(IMAGE_NAME)

# Build full image only
build:
	docker build --target full -t $(IMAGE_NAME) .

# Run ONLY the streaming server
stream:
	docker build --target stream_only -t flight-delay-stream .
	docker run --rm -p 9998:9998 flight-delay-stream

# Debug shell inside full container
shell:
	docker build --target full -t $(IMAGE_NAME) .
	docker run --rm -it $(IMAGE_NAME) bash