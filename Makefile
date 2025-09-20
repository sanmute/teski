.PHONY: setup dev dev-backend dev-frontend build lint

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	cd frontend && npm install

dev-backend:
	uvicorn backend.main:app --reload --env-file .env.backend --port 8000

dev-frontend:
	cd frontend && npm run dev -- --host localhost --port 5173

dev:
	@bash -c 'set -euo pipefail; trap "kill 0" INT TERM EXIT; \
	uvicorn backend.main:app --reload --env-file .env.backend --port 8000 & \
	cd frontend && npm run dev -- --host localhost --port 5173'

build:
	cd frontend && npm run build
	$(PYTHON) -m compileall backend

lint:
	eslint frontend/src --ext .ts,.tsx
