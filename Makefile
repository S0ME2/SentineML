.SILENT:

.PHONY: help start lint format up build down clean ps shapp

APP=app.main:app
HOST=127.0.0.1
PORT=8888
COMPOSE=docker compose

help:
	echo "Makefile commands:"
	echo "  make start    Start the FastAPI application"
	echo "  make lint     Run Ruff checks"
	echo "  make format   Format with Ruff"
	echo "  make up       Start containers"
	echo "  make build    Build and start containers"
	echo "  make down     Stop containers"
	echo "  make clean    Stop containers and delete volumes"
	echo "  make ps       Show containers"
	echo "  make shapp    Open a shell in the app container"

start:
	uv run uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

lint:
	uv run ruff check app

format:
	uv run ruff format app
	uv run ruff check --fix app

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
