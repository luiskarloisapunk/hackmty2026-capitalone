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
