from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import customers, accounts
from app.routers import treasury
from app.routers import temporadas
from app.routers import auth

app = FastAPI(title="HackMTY Backend")

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
app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Backend HackMTY corriendo 🚀"}
