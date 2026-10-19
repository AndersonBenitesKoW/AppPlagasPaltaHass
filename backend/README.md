# Backend — plagas

API de diagnóstico de plagas y enfermedades en palta Hass con modelos YOLO11.

## Stack

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic
- Ultralytics YOLO11 (CPU-only en prod; en dev se inyecta un detector falso)
- Estructura: Clean Architecture / Hexagonal (ports & adapters)

## Setup local

```bash
# 1. Python 3.12 (pyenv-win)
pyenv install 3.12
pyenv local 3.12

# 2. uv
uv sync --extra torch-cpu

# 3. Variables de entorno
cp .env.example .env

# 4. Pesos
# modelos/*.pt NO están en git. Para dev: cp ../../backend/models/hojas.pt models/
# o ajustar APP_MODELOS_DIR en .env.

# 5. Levantar (sin Docker): uvicorn con factory
uv run uvicorn plagas.main:create_app --factory --reload --port 8000
```

## Tests

```bash
# Rápidos (unit + contract fake + api + inspector)
uv run pytest

# Integración (requiere Docker para testcontainers Postgres)
uv run pytest -m integration

# Regresión del modelo (requiere los .pt)
uv run pytest -m modelo

# Cobertura
uv run pytest --cov-report=html
```

## Lint y tipos

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src
uv run lint-imports
```

## Estructura

```
src/plagas/
├── main.py              # create_app() factory
├── config.py            # Settings
├── container.py         # Composition root
├── shared/              # kernel
│   ├── domain/          # errores, identidad, ports
│   ├── infrastructure/  # db, logging, oidc, reloj, integridad
│   └── api/             # errors, middlewares, auth, seguridad, health
└── modules/
    ├── diagnostico/     # bounded context principal
    └── catalogo/        # enfermedades y recomendaciones
```

Ver [ARQUITECTURA.md](../ARQUITECTURA.md) para el detalle completo.

cd backend
uv run uvicorn plagas.main:create_app --factory --reload --port 8000
