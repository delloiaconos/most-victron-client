# ===== Variables =====
IMAGE_NAME ?= most-victron-client
TAG ?= devel
FULL_IMAGE = $(IMAGE_NAME):$(TAG)

CONTAINER_NAME ?= most-giroe-development

# ===== Targets =====

.PHONY: all build push run deploy clean test inspect ansible-deply

all: build

## Build the Docker image
build:
	docker build --platform linux/amd64 -t $(FULL_IMAGE) -f Dockerfile .

## Push the image to the registry
push:
	docker push $(FULL_IMAGE)

## Run the container locally
run:
	mkdir -p logs
	docker run --rm -d \
		--name $(CONTAINER_NAME) \
		-v "${PWD}/logs:/app/logs" \
    	-v "${PWD}/development.ini:/config/config.ini:ro" \
		$(FULL_IMAGE)

## Deploy (build + push + run)
deploy: build push run

## Test
test: build run

inspect:
	docker inspect --format='{{json .State.Health}}' $(CONTAINER_NAME) | jq

## Stop and remove running container
clean:
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)

ansible-deploy:
	ansible-playbook create_containers.yml --ask-become-pass