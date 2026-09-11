"""
Crea un cliente y una cuenta de prueba en Nessie, para no tener que
armar datos a mano cada vez que reinicias tu entorno de desarrollo.

Uso: make seed   (o: cd backend && uv run python ../scripts/seed_nessie.py)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.services.nessie_client import nessie  # noqa: E402


def seed():
    customer_resp = nessie.post(
        "/customers",
        {
            "first_name": "Ana",
            "last_name": "Pérez",
            "address": {
                "street_number": "123",
                "street_name": "Av Siempre Viva",
                "city": "Monterrey",
                "state": "NL",
                "zip": "64000",
            },
        },
    )
    # Nota: revisa en /docs de Nessie si tu respuesta trae el id bajo
    # "objectCreated" -- a veces el shape cambia entre endpoints.
    customer_id = customer_resp.get("objectCreated", {}).get("_id")
    print(f"✅ Cliente creado: {customer_id}")
    print(customer_resp)

    account_resp = nessie.post(
        f"/customers/{customer_id}/accounts",
        {
            "type": "Checking",
            "nickname": "Cuenta Demo",
            "rewards": 0,
            "balance": 1000,
        },
    )
    account_id = account_resp.get("objectCreated", {}).get("_id")
    print(f"✅ Cuenta creada: {account_id}")
    print(account_resp)

    print("\nGuarda estos IDs para tus pruebas y tu demo:")
    print(f"CUSTOMER_ID={customer_id}")
    print(f"ACCOUNT_ID={account_id}")


if __name__ == "__main__":
    seed()
