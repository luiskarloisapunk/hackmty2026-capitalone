FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias antes de copiar el código para aprovechar la caché.
# Instala directo desde pyproject.toml (única fuente de verdad) en vez de
# duplicar la lista a mano -- eso se desincroniza en cuanto alguien agrega
# una dependencia nueva y no se acuerda de tocar este archivo también.
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/
COPY seed_demo.py .
# Para poder diagnosticar el contenedor:
#   docker compose exec backend python diagnostico.py
COPY diagnostico.py .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
