.PHONY: help install dev backend frontend seed seed-nessie check \
        docker-build docker-up docker-down docker-logs docker-check \
        docker up down docker-host puertos-libres

# Usa uv si está instalado; si no, cae a python/pip normal para que nadie
# se quede trabado por no tener uv.
# En Linux se usa la red del host por defecto: el bridge de Docker está
# filtrado en Codespaces y en varios Docker-in-Docker, y ahí los
# contenedores arrancan pero no se alcanzan entre sí (login con 504).
# Docker Desktop (Mac/Windows) no soporta network_mode: host igual, así
# que ahí se queda el compose normal.
ifeq ($(shell uname -s),Linux)
  COMPOSE := docker compose -f docker-compose.yml -f docker-compose.host.yml
else
  COMPOSE := docker compose
endif

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

dev: puertos-libres
	@echo "Backend en http://localhost:8000  ·  Frontend en http://localhost:5173"
	@echo "Cuentas de prueba: navidena@demo.com / heladeria@demo.com / papeleria@demo.com  (contraseña: password)"
	@echo "Ctrl+C detiene ambos."
	@trap 'kill 0' EXIT; \
	(cd backend && $(PY) uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

docker-build:
	$(COMPOSE) build

# Siempre reconstruye: la imagen congela el código, así que sin esto se
# levanta la versión anterior después de un git pull.
docker-up: puertos-libres
	$(COMPOSE) up -d --build
	@echo ""
	@echo "App en          http://localhost"
	@echo "API directa en  http://localhost:8000"
	@echo "Docs de la API  http://localhost:8000/docs"
	@echo "Cuentas de prueba: navidena@demo.com / heladeria@demo.com / papeleria@demo.com  (contraseña: password)"

docker-down:
	-docker compose down
	-docker compose -f docker-compose.yml -f docker-compose.host.yml down

# Plan B: si `make docker-up` levanta los contenedores pero el login se
# queda colgado, la red bridge de Docker está filtrada en tu máquina y los
# contenedores no se alcanzan entre sí. Esto los pone en la red del host.
docker-host:
	docker compose -f docker-compose.yml -f docker-compose.host.yml up -d --build
	@echo ""
	@echo "App en          http://localhost"
	@echo "API directa en  http://localhost:8000"
	@echo "Cuentas de prueba: navidena@demo.com / heladeria@demo.com / papeleria@demo.com  (contraseña: password)"

# Alias, porque `make docker up` (con espacio) es el error fácil de cometer
# y el mensaje de make no ayuda nada a entender qué pasó.
docker: docker-up
up: docker-up
down: docker-down

docker-logs:
	$(COMPOSE) logs -f

docker-check:
	$(COMPOSE) exec backend python diagnostico.py

# Si quedaron contenedores arriba, ocupan 8000 y 80 y luego `make dev`
# falla con "address already in use" sin decir por qué.
puertos-libres:
	@if docker compose ps -q 2>/dev/null | grep -q . || \
	    docker compose -f docker-compose.yml -f docker-compose.host.yml ps -q 2>/dev/null | grep -q .; then \
	  echo "Hay contenedores del proyecto corriendo; los bajo primero..."; \
	  $(MAKE) -s docker-down; \
	fi
