# Multi-stage Docker build for SatRoute / Chakravyuh Constellation Simulator

# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime environment with Python backend
FROM python:3.11-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/pyproject.toml ./backend/
RUN pip install --no-cache-dir fastapi uvicorn orjson numpy networkx sgp4 pydantic

# Copy application source
COPY backend/ ./backend/
COPY data/ ./data/
COPY docs/ ./docs/

# Copy built frontend assets to static directory for FastAPI
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

