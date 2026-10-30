.PHONY: setup dev test lint migrate seed down build clean help

help:
	@echo "PatchPilot Developer Commands:"
	@echo "  make setup    - Install backend and frontend dependencies"
	@echo "  make dev      - Start development backend and frontend services"
	@echo "  make test     - Run automated test suite"
	@echo "  make lint     - Run Ruff and ESLint checks"
	@echo "  make migrate  - Run database migrations"
	@echo "  make seed     - Seed initial database data"
	@echo "  make down     - Stop docker compose services"

setup:
	@echo "Setting up Python virtual environment..."
	python -m venv .venv || py -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt || .venv/Scripts/pip.exe install -r backend/requirements.txt
	@echo "Setting up Frontend..."
	cd frontend && npm install

dev-backend:
	python -m uvicorn app.main:app --app-dir backend --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	docker compose up --build

test:
	pytest backend/tests -v

lint:
	ruff check backend
	cd frontend && npm run lint

migrate:
	cd backend && alembic upgrade head

seed:
	python sample_projects/create_broken_app_zip.py

down:
	docker compose down -v

