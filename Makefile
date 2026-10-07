.PHONY: help up down logs build-backend build-frontend lint test test-int test-modelo typecheck format gen-api migrate seed clean install-backend install-frontend verify

.DEFAULT_GOAL := help

# =====================================================
# Detección de herramientas
# =====================================================
UV         ?= uv
NPM        ?= npm
DOCKER     ?= docker
COMPOSE    ?= docker compose

# =====================================================
# Ayuda
# =====================================================
help: ## mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# =====================================================
# Install
# =====================================================
install-backend: ## instalar deps del backend (uv sync)
	cd backend && $(UV) sync --extra torch-cpu

install-frontend: ## instalar deps del frontend
	cd frontend && $(NPM) install

install: install-backend install-frontend ## instalar todo

# =====================================================
# Lint, tipos, formato
# =====================================================
lint: ## ejecutar linters
	cd backend && $(UV) run ruff check . && $(UV) run ruff format --check .
	cd backend && $(UV) run mypy src
	cd backend && $(UV) run lint-imports
	cd frontend && $(NPM) run lint

lint-fix: ## arreglar lo que se pueda automáticamente
	cd backend && $(UV) run ruff check . --fix && $(UV) run ruff format .
	cd frontend && $(NPM) run lint:fix

typecheck: ## chequear tipos (backend mypy, frontend tsc)
	cd backend && $(UV) run mypy src
	cd frontend && $(NPM) run typecheck

format: ## formatear todo
	cd backend && $(UV) run ruff format .
	cd frontend && $(NPM) run format

# =====================================================
# Tests
# =====================================================
test: ## tests rápidos (unit + contract + api)
	cd backend && $(UV) run pytest
	cd frontend && $(NPM) run test:run

test-int: ## tests de integración (requiere Docker para Postgres)
	cd backend && $(UV) run pytest -m integration --no-cov

test-modelo: ## regresión del modelo (requiere models/*.pt)
	cd backend && $(UV) run pytest -m modelo --no-cov

cobertura: ## coverage en HTML
	cd backend && $(UV) run pytest --cov-report=html
	cd frontend && $(NPM) run test:cov

# =====================================================
# Contrato API
# =====================================================
gen-api: ## exportar OpenAPI y regenerar tipos del frontend
	cd backend && $(UV) run python -m plagas.scripts.exportar_openapi > ../openapi.json
	cd frontend && $(NPM) run gen:api

check-api: ## falla si el contrato API cambió
	cd backend && $(UV) run python -m plagas.scripts.exportar_openapi > /tmp/openapi.new.json
	diff -u ../openapi.json /tmp/openapi.new.json
	cd frontend && $(NPM) run check:api

# =====================================================
# Migraciones
# =====================================================
migrate: ## aplicar migraciones
	cd backend && $(UV) run alembic upgrade head

migrate-new: ## crear nueva migración (uso: make migrate-new MSG="...")
	cd backend && $(UV) run alembic revision --autogenerate -m "$(MSG)"

seed: ## cargar datos iniciales (catálogo, usuarios dev)
	cd backend && $(UV) run python -m plagas.scripts.seed

# =====================================================
# Docker
# =====================================================
up: ## levantar el stack (db + backend + frontend + keycloak)
	$(COMPOSE) up -d --build

down: ## bajar el stack
	$(COMPOSE) down

down-v: ## bajar el stack y borrar volúmenes
	$(COMPOSE) down -v

logs: ## tail de logs
	$(COMPOSE) logs -f --tail=100

build-backend: ## construir imagen del backend
	$(DOCKER) build -t plagas-backend ./backend

build-frontend: ## construir imagen del frontend
	$(DOCKER) build -t plagas-frontend ./frontend

# =====================================================
# Verificación rápida
# =====================================================
verify: lint test ## lint + test (lo que corre en CI por defecto)

# =====================================================
# Limpieza
# =====================================================
clean: ## limpiar caches y artefactos
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name coverage -exec rm -rf {} + 2>/dev/null || true
	rm -f backend/.coverage backend/coverage.xml
	rm -rf backend/htmlcov
