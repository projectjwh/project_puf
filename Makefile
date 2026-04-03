.PHONY: help install dev up down migrate test lint format clean deploy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev: ## Install with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

up: ## Start all Docker services
	docker compose -f config/docker-compose.yml up -d

down: ## Stop all Docker services
	docker compose -f config/docker-compose.yml down

logs: ## Tail Docker service logs
	docker compose -f config/docker-compose.yml logs -f

migrate: ## Run Alembic migrations to head + seed catalog
	alembic -c pipelines/alembic/alembic.ini upgrade head
	python scripts/seed_catalog_sources.py

migrate-down: ## Rollback last Alembic migration
	alembic -c pipelines/alembic/alembic.ini downgrade -1

migrate-status: ## Show current migration status
	alembic -c pipelines/alembic/alembic.ini current

test: ## Run tests (excluding integration)
	pytest -m "not integration" -v

test-all: ## Run all tests including integration
	pytest -v

test-cov: ## Run tests with coverage report
	pytest -m "not integration" --cov=pipelines --cov=flows --cov=api --cov-report=term-missing

lint: ## Run linter
	ruff check .

format: ## Format code
	ruff format .
	ruff check --fix .

typecheck: ## Run type checker
	mypy pipelines/ flows/ api/

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/

seed-catalog: ## Seed catalog.sources from sources.yaml
	python scripts/seed_catalog_sources.py

db-shell: ## Open psql shell to PostgreSQL
	docker compose -f config/docker-compose.yml exec postgres psql -U puf_admin -d puf

prefect-ui: ## Open Prefect UI URL
	@echo "Prefect UI: http://localhost:4200"

deploy: ## Serve all Prefect deployments with cron schedules
	python -m flows.deploy

dbt-run: ## Run all dbt models
	cd models && dbt run

dbt-test: ## Run all dbt tests
	cd models && dbt test
