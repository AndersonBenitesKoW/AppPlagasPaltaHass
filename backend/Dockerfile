FROM python:3.12-slim-trixie

WORKDIR /app

# libglib2.0-0t64 (libgthread) y libgl1: ultralytics instala opencv-python completo,
# que los necesita aunque también esté opencv-python-headless.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0t64 \
        libgl1 \
        libxcb1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Dependencias primero (capa cacheable), luego el código.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN uv sync --locked --no-dev

# --no-sync: no reinstalar dependencias (ni las de dev) en cada arranque.
CMD sh -c 'uv run --no-sync uvicorn plagas.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}'
