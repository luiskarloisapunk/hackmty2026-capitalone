#!/usr/bin/env bash
set -e

PROJECT_NAME="hackmty2026-capitalone"
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

echo "📁 Creando backend (Python + FastAPI)..."
mkdir -p backend/app/routers backend/app/services

cat > backend/pyproject.toml << 'EOF'
[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "httpx",
    "python-dotenv",
]
EOF

cat > backend/.env.example << 'EOF'
NESSIE_API_KEY=tu_api_key_aqui
NESSIE_BASE_URL=http://api.nessieisreal.com
EOF

touch backend/app/__init__.py backend/app/routers/__init__.py backend/app/services/__init__.py

cat > backend/app/services/nessie_client.py << 'EOF'
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NESSIE_BASE_URL", "http://api.nessieisreal.com")
API_KEY = os.getenv("NESSIE_API_KEY")


class NessieClient:
    def __init__(self):
        self.client = httpx.Client(timeout=10.0)

    def _url(self, path: str) -> str:
        separator = "&" if "?" in path else "?"
        return f"{BASE_URL}{path}{separator}key={API_KEY}"

    def get(self, path: str):
        r = self.client.get(self._url(path))
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict):
        r = self.client.post(self._url(path), json=body)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, body: dict):
        r = self.client.put(self._url(path), json=body)
        r.raise_for_status()
        return r.json()

    def delete(self, path: str):
        r = self.client.delete(self._url(path))
        r.raise_for_status()
        return r.json()


nessie = NessieClient()
EOF

cat > backend/app/routers/customers.py << 'EOF'
from fastapi import APIRouter, HTTPException
from app.services.nessie_client import nessie

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/")
def list_customers():
    try:
        return nessie.get("/customers")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_customer(customer: dict):
    try:
        return nessie.post("/customers", customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
EOF

cat > backend/app/routers/accounts.py << 'EOF'
from fastapi import APIRouter, HTTPException
from app.services.nessie_client import nessie

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/{customer_id}")
def list_accounts(customer_id: str):
    try:
        return nessie.get(f"/customers/{customer_id}/accounts")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{customer_id}")
def create_account(customer_id: str, account: dict):
    try:
        return nessie.post(f"/customers/{customer_id}/accounts", account)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
EOF

cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import customers, accounts

app = FastAPI(title="HackMTY Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(accounts.router)


@app.get("/")
def root():
    return {"message": "Backend HackMTY corriendo 🚀"}
EOF

echo "✅ Backend listo."

echo "📁 Creando frontend con Vite..."
npm create vite@latest frontend -- --template react

mkdir -p frontend/src/api
cat > frontend/src/api/client.js << 'EOF'
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function getCustomers() {
  const res = await fetch(`${API_URL}/customers`);
  return res.json();
}

export async function createCustomer(data) {
  const res = await fetch(`${API_URL}/customers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}
EOF

cat > frontend/.env.example << 'EOF'
VITE_API_URL=http://localhost:8000/api
EOF

mkdir -p docs
cat > docs/pitch.md << 'EOF'
# Pitch - [Nombre del proyecto]

## Problema

## Solución

## Demo

## Impacto / negocio

## Stack técnico
EOF

cat > README.md << 'EOF'
# HackMTY 2026 - Reto Capital One

## Backend (Python/FastAPI con uv)
cd backend
cp .env.example .env       # agrega tu NESSIE_API_KEY
uv sync                    # crea el venv e instala dependencias automáticamente
uv run uvicorn app.main:app --reload

# Docs automáticas en http://localhost:8000/docs

## Frontend
cd frontend
cp .env.example .env
npm install
npm run dev
EOF

cat > .gitignore << 'EOF'
node_modules/
.venv/
__pycache__/
*.pyc
.env
dist/
.DS_Store
EOF

echo "🎉 Proyecto listo en ./$PROJECT_NAME"
