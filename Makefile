# Image, Data Directories, and Database Path
IMAGE_NAME = project_image
LOCAL_HOST_DIR = $(shell pwd)
CONTAINER_SRC_DIR = /app/src
DATA_DIR = /app/src/esg_app/api/data
DB_PATH=$(DATA_DIR)/esg_scores.db
DB_MANAGE_PATH=/app/src/esg_app/utils/data_utils/db_manage.py

# Environment Variables
ENV_VARS = \
	-e FLASK_APP=/app/src/app.py \
	-e FLASK_DEBUG='1' \
	-e FLASK_ENV='development' \
	-e PYTHONPATH='/app/src' \
	-e PYTHONDONTWRITEBYTECODE=1 \
	-e DB_PATH=$(DB_PATH) \
	-e DATA_DIR=$(DATA_DIR) \
	-e DB_MANAGE_PATH=$(DB_MANAGE_PATH)

# Docker Flags
ALL_FLAGS = \
	-v "$(LOCAL_HOST_DIR):$(CONTAINER_SRC_DIR)" \
	$(ENV_VARS)

# Phony Targets
.PHONY = build interactive flask

# Build our Docker image
build:
	docker build . -t $(IMAGE_NAME)

# Run container interactively. All files will be mounted except requirements
interactive: build
	docker run -it -p 5001:5001 \
	$(ALL_FLAGS) \
	--shm-size=2g $(IMAGE_NAME) /bin/sh

# Run Flask server on port 5001
flask: build
	docker run -p 5001:5001 \
	$(ALL_FLAGS) \
	$(IMAGE_NAME)

# Create a sqlite database file and associated tables
db_create: build
	docker run $(ALL_FLAGS) $(IMAGE_NAME) \
		python $(DB_MANAGE_PATH) db_create

# Load data into the sqlite database
db_load: build
	docker run $(ALL_FLAGS) $(IMAGE_NAME) \
		python $(DB_MANAGE_PATH) db_load

# Delete the database file
db_rm: build
	docker run $(ALL_FLAGS) $(IMAGE_NAME) \
		python $(DB_MANAGE_PATH) db_rm

# Delete the database file and reload data
db_clean: build
	docker run $(ALL_FLAGS) $(IMAGE_NAME) \
		python $(DB_MANAGE_PATH) db_clean

# Create interactive sqlite session with database
db_interactive: build
	docker run -it $(ALL_FLAGS) $(IMAGE_NAME) \
	sqlite3 -column -header $(DB_PATH)