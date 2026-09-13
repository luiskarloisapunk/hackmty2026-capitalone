from app.services.nessie_client import nessie
from app.services.db import negocios_collection

async def crear_cliente(first_name: str, last_name: str, address: dict):
    body = {
        "first_name": first_name,
        "last_name": last_name,
        "address": address
    }
    resultado_nessie = nessie.post("/customers", body)
    nessie_id = resultado_nessie["objectCreated"]["_id"]

    documento = {
        "nessie_customer_id": nessie_id,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
    }
    await negocios_collection.insert_one(documento)

    return resultado_nessie

async def crear_cuenta_ahorro(customer_id: str, nickname: str, balance: float):
    body = {
        "type": "Savings",
        "nickname": nickname,
        "rewards": 0,
        "balance": balance
    }
    resultado_nessie = nessie.post(f"/customers/{customer_id}/accounts", body)
    account_id = resultado_nessie["objectCreated"]["_id"]

    await negocios_collection.update_one(
        {"nessie_customer_id": customer_id},
        {"$push": {"cuentas": {
            "nessie_account_id": account_id,
            "nickname": nickname,
            "balance": balance,
        }}}
    )

    return resultado_nessie

async def crear_cuenta_inversion(customer_id: str, nickname: str, balance: float):
    body = {
        "type": "Investment",
        "nickname": nickname,
        "rewards": 0,
        "balance": balance
    }
    resultado_nessie = nessie.post(f"/customers/{customer_id}/accounts", body)
    account_id = resultado_nessie["objectCreated"]["_id"]

    await negocios_collection.update_one(
        {"nessie_customer_id": customer_id},
        {"$push": {"cuentas": {
            "nessie_account_id": account_id,
            "nickname": nickname,
            "balance": balance,
        }}}
    )

    return resultado_nessie
