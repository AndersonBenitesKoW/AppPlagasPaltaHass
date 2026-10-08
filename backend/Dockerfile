FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libxcb1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --locked --no-dev

COPY . .

CMD ["sh", "-c", "uv run uvicorn plagas.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]