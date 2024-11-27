IMAGE_NAME = project_image
LOCAL_HOST_DIR = $(shell pwd)
CONTAINER_SRC_DIR = /app/src

.PHONY = build interactive snpglobal flask

build:
	docker build . -t $(IMAGE_NAME)

interactive: build
	docker run -it -p 5001:5001 \
	-e PYTHONPATH='/app/src' \
	-v $(LOCAL_HOST_DIR):$(CONTAINER_SRC_DIR) \
	--shm-size=2g $(IMAGE_NAME) /bin/sh

# snpglobal: build
# 	docker run -it --rm \
# 	-e PYTHONPATH='/app/src' \
# 	-v $(LOCAL_HOST_DIR):$(CONTAINER_SRC_DIR) \
# 	$(IMAGE_NAME) /bin/sh -c \
# 	"xvfb-run -a python esg_app/utils/parallel_scraper.py"

flask: build
	docker run -p 5001:5001 \
	-e FLASK_APP=/app/src/app.py \
	-e FLASK_DEBUG='1' \
	-e FLASK_ENV='development' \
	-e KM_API_KEY=$(KM_API_KEY) \
	-v "$(LOCAL_HOST_DIR):$(CONTAINER_SRC_DIR)" \
	--shm-size=2g $(IMAGE_NAME)
