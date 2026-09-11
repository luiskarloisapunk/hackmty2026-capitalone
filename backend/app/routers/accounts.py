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
