.PHONY: up down build migrate seed test lint format install dev

# Docker
up:
	docker compose up -d

up-build:
	docker compose up -d --build

down:
	docker compose down

down-v:
	docker compose down -v

logs:
	docker compose logs -f

# Database
migrate:
	docker compose exec backend alembic upgrade head

migrate-local:
	cd backend && alembic upgrade head

revision:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# Backend
install-backend:
	cd backend && uv sync

test:
	cd backend && uv run pytest tests/ -v

lint:
	cd backend && uv run ruff check app/ cli/ tests/
	cd backend && uv run mypy app/ cli/

format:
	cd backend && uv run ruff format app/ cli/ tests/
	cd backend && uv run ruff check --fix app/ cli/ tests/

# Frontend
install-frontend:
	cd frontend && npm install

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

# Full setup
install: install-backend install-frontend

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Ollama models
pull-models:
	docker compose exec ollama ollama pull qwen3-8b
	docker compose exec ollama ollama pull qwen3-1.7b
	docker compose exec ollama ollama pull nomic-embed-text

# Production
prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-up-build:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-migrate:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head

prod-logs:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# CLI
cli:
	cd backend && uv run cereborate
