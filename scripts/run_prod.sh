#!/usr/bin/env bash
set -e

echo "=== Starting Chakravyuh Production Build & Run ==="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. Build Frontend
echo "--> Building frontend..."
cd "$ROOT_DIR/frontend"
npm run build

# 2. Start Backend
echo "--> Starting backend on :8000..."
cd "$ROOT_DIR/backend"
if [ -d "$ROOT_DIR/.venv" ]; then
    source "$ROOT_DIR/.venv/bin/activate"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000

