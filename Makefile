.PHONY: test dev lint test-backend test-frontend

test-backend:
	PYTHONPATH=backend .venv/bin/pytest backend/tests

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend

lint:
	.venv/bin/ruff check backend/app
	.venv/bin/mypy backend/app

dev:
	@echo "Starting backend and frontend in dev mode..."
	bash scripts/dev.sh
