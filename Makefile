.SILENT:

.PHONY: help start up upb down clean ps

APP=app.main:app
HOST=127.0.0.1
PORT=8888

COMPOSE=docker compose

help:
	echo "Makefile commands:"
	echo "	make start  - Start the FastAPI application using uvicorn"
	echo "	make up     - Start the Docker containers in detached mode"
	echo "	make build    - Build and start the Docker containers in detached mode"
	echo "	make down   - Stop the Docker containers"
	echo "	make clean  - Stop and remove the Docker containers and volumes"
	echo "	make ps     - Display all Docker containers, including stopped ones"
	echo "	make shapp  - Open a shell in the 'app' Docker container"

start:
	uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

up:
	$(COMPOSE) up -d

build:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

ps:
	$(COMPOSE) ps -a

shapp:
	$(COMPOSE) exec app sh