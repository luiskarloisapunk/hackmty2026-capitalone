import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import customers, accounts
from app.routers import treasury
from app.routers import temporadas
from app.routers import negocios
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Con SEED_DEMO=true (lo que hace docker-compose), el stack levanta ya con
    las cuentas de demo cargadas. Es idempotente: si ya existen, no toca
    nada, así que reiniciar el contenedor no borra lo que hayan capturado.
    """
    if os.getenv("SEED_DEMO", "").lower() in {"1", "true", "yes"}:
        try:
            from seed_demo import sembrar, ya_sembrado

            if not await ya_sembrado():
                await sembrar()
        except Exception as e:  # nunca impedir que la API arranque
            print(f"[seed] No se pudieron sembrar las cuentas de demo: {e}")
    yield


app = FastAPI(title="HackMTY Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(accounts.router)
app.include_router(treasury.router)
app.include_router(temporadas.router)
app.include_router(negocios.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Backend HackMTY corriendo 🚀"}
