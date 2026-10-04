.SILENT:

.PHONY: help start lint format test demo up build down backup clean ps shapp

APP=app.main:app
HOST=127.0.0.1
PORT=8888
COMPOSE=docker compose
BACKUP_FILE ?= backups/sentinelml-$(shell date +%Y%m%d-%H%M%S).dump

help:
	echo "Makefile commands:"
	echo "  make start    Start the FastAPI application"
	echo "  make lint     Run Ruff checks"
	echo "  make format   Format with Ruff"
	echo "  make test     Run unit tests (no database required)"
	echo "  make demo     Record synthetic example runs against the local API"
	echo "  make up       Start containers"
	echo "  make build    Build and start containers"
	echo "  make down     Stop containers"
	echo "  make backup   Write a non-overwriting PostgreSQL backup"
	echo "  make clean    Delete volumes (requires CONFIRM=YES)"
	echo "  make ps       Show containers"
	echo "  make shapp    Open a shell in the app container"

start:
	uv run uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

lint:
	uv run ruff check app tests sentinelml_client.py examples
	uv run ruff format --check app tests sentinelml_client.py examples

format:
	uv run ruff format app tests sentinelml_client.py examples
	uv run ruff check --fix app tests sentinelml_client.py examples

test:
	uv run python -m unittest discover -s tests -v

demo:
	uv run python -m examples.track_experiment --url "$${SENTINELML_URL:-http://127.0.0.1:$${APP_PORT:-8888}}"

up:
	$(COMPOSE) up -d --wait

build:
	$(COMPOSE) up -d --build --wait

down:
	$(COMPOSE) down

backup:
	@set -eu; \
	backup_dir="$(dir $(BACKUP_FILE))"; \
	mkdir -p "$$backup_dir"; \
	if [ -e "$(BACKUP_FILE)" ]; then \
		echo "Refusing to overwrite existing backup: $(BACKUP_FILE)"; \
		exit 1; \
	fi; \
	temp_file="$$(mktemp "$$backup_dir/.sentinelml-backup.XXXXXX")"; \
	trap 'rm -f "$$temp_file"' EXIT; \
	$(COMPOSE) exec -T db sh -c 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" --format=custom --no-owner' > "$$temp_file"; \
	ln "$$temp_file" "$(BACKUP_FILE)"; \
	rm "$$temp_file"; \
	trap - EXIT; \
	echo "Wrote $(BACKUP_FILE)"

clean:
	@if [ "$${CONFIRM:-}" != "YES" ]; then \
		echo "Refusing to delete Compose volumes. Use: make clean CONFIRM=YES"; \
		exit 1; \
	fi
	$(COMPOSE) down -v

ps:
	$(COMPOSE) ps -a

shapp:
	$(COMPOSE) exec app sh
