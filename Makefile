.PHONY: help install dev backend frontend seed seed-nessie check \
        docker-build docker-up docker-down docker-logs docker-check

# Usa uv si está instalado; si no, cae a python/pip normal para que nadie
# se quede trabado por no tener uv.
UV := $(shell command -v uv 2>/dev/null)
ifdef UV
  PY := uv run
  PIP_INSTALL := uv sync
else
  PY :=
  PIP_INSTALL := pip install -e .
endif

help:
	@echo "AC/DC Cash Flow"
	@echo ""
	@echo "  Nativo (desarrollo, con recarga automática):"
	@echo "    make install    instala dependencias de backend y frontend"
	@echo "    make seed       crea las 3 cuentas de prueba (contraseña: password)"
	@echo "    make dev        levanta backend y frontend juntos"
	@echo ""
	@echo "  Docker (todo en un comando, incluye su propia base de datos):"
	@echo "    make docker-up  construye y levanta el stack completo"
	@echo "    make docker-down  lo apaga"
	@echo ""
	@echo "  Si algo no carga:"
	@echo "    make check      revisa tu entorno y dice qué falta"

install:
	cd backend && $(PIP_INSTALL)
	cd frontend && npm install

# Las 3 cuentas de negocio de prueba. Es idempotente: correrlo de nuevo
# regenera los datos de demo sin tocar cuentas que hayan creado ustedes.
seed:
	cd backend && $(PY) python seed_demo.py

# Datos de ejemplo directo en Nessie (el otro seed, para probar la API).
seed-nessie:
	cd backend && $(PY) python ../seed_nessie.py

check:
	cd backend && $(PY) python diagnostico.py

backend:
	cd backend && $(PY) uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Backend en http://localhost:8000  ·  Frontend en http://localhost:5173"
	@echo "Cuentas de prueba: navidena@demo.com / heladeria@demo.com / papeleria@demo.com  (contraseña: password)"
	@echo "Ctrl+C detiene ambos."
	@trap 'kill 0' EXIT; \
	(cd backend && $(PY) uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

docker-build:
	docker compose build

# Siempre reconstruye: la imagen congela el código, así que sin esto se
# levanta la versión anterior después de un git pull.
docker-up:
	docker compose up -d --build
	@echo ""
	@echo "App en          http://localhost"
	@echo "API directa en  http://localhost:8000"
	@echo "Docs de la API  http://localhost:8000/docs"
	@echo "Cuentas de prueba: navidena@demo.com / heladeria@demo.com / papeleria@demo.com  (contraseña: password)"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-check:
	docker compose exec backend python diagnostico.py
