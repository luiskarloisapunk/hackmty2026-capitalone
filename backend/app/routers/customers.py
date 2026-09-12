from fastapi import APIRouter, HTTPException
from app.services.nessie_client import nessie
from app.services.cliente import crear_cliente, crear_cuenta_ahorro

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("/")
def list_customers():
    try:
        return nessie.get("/customers")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_customer(customer: dict):
    try:
        return await crear_cliente(**customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{customer_id}/accounts/savings")
async def create_savings_account(customer_id: str, nickname: str, balance: float):
    try:
        return await crear_cuenta_ahorro(customer_id, nickname, balance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
