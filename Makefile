# SED Energy AI Marketing System — Makefile
.PHONY: help up down build logs migrate seed shell backend-shell frontend-shell

help:
	@echo "SED Energy AI Marketing System"
	@echo ""
	@echo "  make up           Start all services"
	@echo "  make down         Stop all services"
	@echo "  make build        Rebuild Docker images"
	@echo "  make logs         Tail all service logs"
	@echo "  make migrate      Run database migrations"
	@echo "  make seed         Seed initial data"
	@echo "  make shell        Open backend Python shell"
	@echo "  make test         Run backend tests"
	@echo "  make lint         Run linters"
	@echo ""

up:
	docker-compose up -d
	@echo "✅ SED AI Marketing System running at http://localhost:3000"

down:
	docker-compose down

build:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f celery_worker

migrate:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python scripts/seed.py

shell:
	docker-compose exec backend python

backend-shell:
	docker-compose exec backend bash

frontend-shell:
	docker-compose exec frontend sh

restart-backend:
	docker-compose restart backend celery_worker celery_beat

test:
	docker-compose exec backend pytest tests/ -v

lint:
	docker-compose exec backend ruff check app/
	cd frontend && npm run lint

db-reset:
	docker-compose exec backend alembic downgrade base
	docker-compose exec backend alembic upgrade head
	@echo "⚠️  Database reset complete"

flower:
	@echo "Celery Flower monitoring at http://localhost:5555"
	@open http://localhost:5555

env-check:
	@python3 scripts/check_env.py
