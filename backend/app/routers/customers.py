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
