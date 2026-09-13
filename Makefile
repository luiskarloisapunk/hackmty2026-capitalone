.PHONY: install dev backend frontend seed

install:
	cd backend && uv sync
	cd frontend && npm install

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Iniciando backend y frontend juntos (Ctrl+C detiene ambos)..."
	@trap 'kill 0' EXIT; \
	(cd backend && uv run uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

seed:
	cd backend && uv run python ../seed_nessie.py
