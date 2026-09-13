import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

# Sin timeout explícito, pymongo espera 30 segundos antes de rendirse. Eso
# hacía que el arranque se colgara medio minuto cuando Mongo no era
# alcanzable, y que nginx cortara los requests con 504 en vez de dar un
# error entendible. 8s alcanza de sobra para Atlas y falla rápido cuando
# de verdad no hay nadie del otro lado.
client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
db = client["hackmty_db"]

negocios_collection = db["negocios"]
usuarios_collection = db["usuarios"]
perfiles_collection = db["perfiles_negocio"]
