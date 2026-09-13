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


def seed_pyme_estacional():
    """
    Crea una PyME de ejemplo con estacionalidad marcada (tienda de decoración
    navideña: pico en Oct-Dic, temporada baja Ene-Mar, regular el resto),
    con sus 3 cuentas Nessie y un año de depósitos históricos en Checking
    para poder probar el clasificador de temporadas y el motor de regulación.
    """
    customer_resp = nessie.post(
        "/customers",
        {
            "first_name": "Decoraciones",
            "last_name": "Del Norte SA de CV",
            "address": {
                "street_number": "455",
                "street_name": "Av Constitución",
                "city": "Monterrey",
                "state": "NL",
                "zip": "64000",
            },
        },
    )
    customer_id = customer_resp.get("objectCreated", {}).get("_id")
    print(f"✅ PyME creada: {customer_id}")

    checking_id = nessie.post(
        f"/customers/{customer_id}/accounts",
        {"type": "Checking", "nickname": "Operación", "rewards": 0, "balance": 15000},
    ).get("objectCreated", {}).get("_id")
    print(f"✅ Cuenta Checking (operación): {checking_id}")

    savings_id = nessie.post(
        f"/customers/{customer_id}/accounts",
        {"type": "Savings", "nickname": "Fondo Regulador", "rewards": 0, "balance": 20000},
    ).get("objectCreated", {}).get("_id")
    print(f"✅ Cuenta Savings (fondo regulador, liquidez inmediata): {savings_id}")

    investment_id = nessie.post(
        f"/customers/{customer_id}/accounts",
        {"type": "Investment", "nickname": "Fondo de Inversión", "rewards": 0, "balance": 0},
    ).get("objectCreated", {}).get("_id")
    print(f"✅ Cuenta Investment (CETES / plazo fijo): {investment_id}")

    # (año, mes, monto de ventas del mes, temporada) -- Sep 2025 a Ago 2026.
    ventas_mensuales = [
        (2025, 9, 42000, "regular"),
        (2025, 10, 95000, "alta"),
        (2025, 11, 130000, "alta"),
        (2025, 12, 155000, "alta"),
        (2026, 1, 21000, "baja"),
        (2026, 2, 19500, "baja"),
        (2026, 3, 24000, "baja"),
        (2026, 4, 41000, "regular"),
        (2026, 5, 43500, "regular"),
        (2026, 6, 40000, "regular"),
        (2026, 7, 44000, "regular"),
        (2026, 8, 46000, "regular"),
    ]

    for year, month, monto, temporada in ventas_mensuales:
        nessie.post(
            f"/accounts/{checking_id}/deposits",
            {
                "medium": "balance",
                "transaction_date": f"{year}-{month:02d}-15",
                "amount": monto,
                "description": f"Ventas del mes - temporada {temporada}",
            },
        )
        print(f"  💰 Depósito {year}-{month:02d}: ${monto} ({temporada})")

    print("\nGuarda estos IDs para las pruebas del motor de temporadas:")
    print(f"PYME_CUSTOMER_ID={customer_id}")
    print(f"PYME_CHECKING_ID={checking_id}")
    print(f"PYME_SAVINGS_ID={savings_id}")
    print(f"PYME_INVESTMENT_ID={investment_id}")


if __name__ == "__main__":
    seed()
    seed_pyme_estacional()
