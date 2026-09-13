FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias antes de copiar el código para aprovechar la caché
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "fastapi>=0.111" \
    "uvicorn[standard]>=0.29" \
    "httpx>=0.27" \
    "python-dotenv>=1.0" \
    "numpy>=1.26" \
    "motor>=3.4"

COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
