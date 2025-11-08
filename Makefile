.PHONY: setup dev dev-api dev-legacy dev-frontend build lint

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
API_APP ?= app.main:app
LEGACY_APP ?= backend.main:app
API_ENV ?= .env

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	cd frontend && npm install

dev-api:
	uvicorn $(API_APP) --reload --env-file $(API_ENV) --port 8000

dev-legacy:
	uvicorn $(LEGACY_APP) --reload --env-file .env.backend --port 8100

dev-frontend:
	cd frontend && npm run dev -- --host localhost --port 5173

dev:
	@bash -c 'set -euo pipefail; trap "kill 0" INT TERM EXIT; \
	uvicorn $(API_APP) --reload --env-file $(API_ENV) --port 8000 & \
	cd frontend && npm run dev -- --host localhost --port 5173'

build:
	cd frontend && npm run build
	$(PYTHON) -m compileall backend

lint:
	eslint frontend/src --ext .ts,.tsx
