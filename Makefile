.PHONY: setup dev dev-api dev-legacy dev-frontend build lint docker-up docker-down docker-build docker-logs docker-clean

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
API_APP ?= main:app
LEGACY_APP ?= backend.main:app
API_ENV ?= .env

setup: ## Install Python dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	cd frontend && npm install

dev-api: ## Run the API server
	uvicorn $(API_APP) --reload --env-file $(API_ENV) --port 8000

dev-legacy: ## Run the legacy backend server
	uvicorn $(LEGACY_APP) --reload --env-file .env.backend --port 8100

dev-frontend: ## Run the frontend server
	cd frontend && npm run dev -- --host localhost --port 5173

dev: ## Run the API and frontend servers
	@bash -c 'set -euo pipefail; trap "kill 0" INT TERM EXIT; \
	uvicorn $(API_APP) --reload --env-file $(API_ENV) --port 8000 & \
	cd frontend && npm run dev -- --host localhost --port 5173'

build: ## Build the frontend
	cd frontend && npm run build
	$(PYTHON) -m compileall backend

lint: ## Run ESLint on the frontend
	eslint frontend/src --ext .ts,.tsx

# Docker development commands
docker-build: ## Build the Docker images
	docker-compose build

docker-up: docker-ensure-db ## Start the Docker containers
	docker-compose up

# Ensure database files exist (prevents Docker from creating directories)
docker-ensure-db: ## Ensure database files exist
	@touch teski.db teski_v2.db 2>/dev/null || true

docker-up-d: docker-ensure-db ## Start the Docker containers in detached mode
	docker-compose up -d

docker-down: ## Stop the Docker containers
	docker-compose down

docker-logs: ## Follow the logs of the Docker containers
	docker-compose logs -f

docker-logs-api: ## Follow the logs of the API container
	docker-compose logs -f api

docker-logs-legacy: ## Follow the logs of the legacy backend container
	docker-compose logs -f legacy

docker-logs-frontend: ## Follow the logs of the frontend container
	docker-compose logs -f frontend

docker-clean: ## Clean up the Docker containers and volumes
	docker-compose down -v --rmi local
	docker volume rm teski_frontend_node_modules 2>/dev/null || true

docker-restart: ## Restart the Docker containers
	docker-compose restart

docker-shell-api: ## Open a shell in the API container
	docker-compose exec api bash

docker-shell-legacy: ## Open a shell in the legacy backend container
	docker-compose exec legacy bash

docker-shell-frontend: ## Open a shell in the frontend container
	docker-compose exec frontend sh

help: ## Displays the available commands (this help)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
