# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Python sanity
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (DuckDB wheels usually don't need build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user (important for mounted volumes)
RUN useradd -m appuser \
 && mkdir -p /data /app/logs \
 && chown -R appuser:appuser /app /data

USER appuser

# DuckDB location (DO NOT keep it in /app)
ENV DUCKDB_PATH=/data/app.db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
