import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client["hackmty_db"]

negocios_collection = db["negocios"]
usuarios_collection = db["usuarios"]
perfiles_collection = db["perfiles_negocio"]
