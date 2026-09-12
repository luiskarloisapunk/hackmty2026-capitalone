from app.services.nessie_client import nessie

def crear_cliente(first_name: str, last_name: str, address: dict):
    body = {
        "first_name": first_name,
        "last_name": last_name,
        "address": address
    }
    return nessie.post("/customers", body)

def crear_cuenta_ahorro(customer_id: str, nickname: str, balance: float):
    body = {
        "type": "Savings",
        "nickname": nickname,
        "rewards": 0,
        "balance": balance
    }
    return nessie.post(f"/customers/{customer_id}/accounts", body)
