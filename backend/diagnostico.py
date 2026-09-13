"""
Revisa que tu entorno local esté bien configurado.

Es para cuando algo "no carga" en tu máquina pero sí en la de alguien más:
en vez de adivinar, dice exactamente qué falta.

Uso:  cd backend && python diagnostico.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import httpx  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

OK = "\033[92m✓\033[0m"
MAL = "\033[91m✗\033[0m"
AVISO = "\033[93m!\033[0m"

URL_NESSIE_BUENA = "https://api.nessieisreal.com"


def revisar_variables() -> list[str]:
    problemas = []
    print("\n— Variables de entorno (backend/.env) —")

    for nombre in ["NESSIE_API_KEY", "MONGODB_URI", "JWT_SECRET_KEY", "BANXICO_TOKEN"]:
        valor = os.getenv(nombre)
        if valor:
            print(f"  {OK} {nombre} definida")
        else:
            print(f"  {MAL} {nombre} NO está definida")
            problemas.append(f"Falta {nombre} en backend/.env")

    url = os.getenv("NESSIE_BASE_URL", "")
    if url == URL_NESSIE_BUENA:
        print(f"  {OK} NESSIE_BASE_URL correcta")
    elif not url:
        print(f"  {AVISO} NESSIE_BASE_URL vacía (se usará el default, que sí es correcto)")
    else:
        print(f"  {MAL} NESSIE_BASE_URL = {url}")
        if "reimaginebanking" in url:
            problemas.append(
                "Tu NESSIE_BASE_URL apunta a api.reimaginebanking.com, un dominio que "
                f"ya NO resuelve. Cámbiala a {URL_NESSIE_BUENA}"
            )
        elif url.startswith("http://"):
            problemas.append(
                "Tu NESSIE_BASE_URL usa http://. Nessie solo responde por HTTPS: "
                f"cámbiala a {URL_NESSIE_BUENA}"
            )
        else:
            problemas.append(f"NESSIE_BASE_URL inesperada; debería ser {URL_NESSIE_BUENA}")

    return problemas


def revisar_nessie() -> list[str]:
    problemas = []
    print("\n— Conexión con Nessie —")

    url = os.getenv("NESSIE_BASE_URL") or URL_NESSIE_BUENA
    key = os.getenv("NESSIE_API_KEY")
    if not key:
        print(f"  {MAL} sin API key, no se puede probar")
        return ["Falta NESSIE_API_KEY"]

    try:
        r = httpx.get(f"{url}/customers", params={"key": key}, timeout=15.0)
        r.raise_for_status()
        clientes = r.json()
        print(f"  {OK} Nessie responde · {len(clientes)} clientes con tu key")
        if not clientes:
            print(f"  {AVISO} No hay clientes todavía: la lista saldrá vacía en la app.")
            print("      Da de alta un negocio desde la pestaña Perfil para crearlos.")
    except httpx.HTTPError as e:
        print(f"  {MAL} No se pudo conectar: {type(e).__name__}")
        problemas.append(f"Nessie no responde desde tu red ({type(e).__name__})")

    return problemas


def revisar_mongo() -> list[str]:
    problemas = []
    print("\n— Conexión con MongoDB —")

    uri = os.getenv("MONGODB_URI")
    if not uri:
        print(f"  {MAL} sin MONGODB_URI, no se puede probar")
        return ["Falta MONGODB_URI"]

    if "<password>" in uri or "<PASSWORD>" in uri:
        print(f"  {MAL} la URI trae '<password>' literal, sin reemplazar")
        return ["Reemplaza <password> en MONGODB_URI por la contraseña real"]

    try:
        import pymongo

        cliente = pymongo.MongoClient(uri, serverSelectionTimeoutMS=8000)
        cliente.admin.command("ping")
        db = cliente["hackmty_db"]
        usuarios = db["usuarios"].count_documents({})
        perfiles = db["perfiles_negocio"].count_documents({})
        print(f"  {OK} Mongo responde · {usuarios} usuarios, {perfiles} perfiles de negocio")
        if perfiles == 0:
            print(f"  {AVISO} No hay negocios. Corre: python seed_demo.py")
    except Exception as e:
        print(f"  {MAL} No se pudo conectar: {type(e).__name__}")
        problemas.append(f"Mongo no responde ({type(e).__name__})")

    return problemas


def revisar_banxico() -> list[str]:
    print("\n— Tasa de referencia (Banxico) —")
    try:
        from app.services.banxico_client import TASA_RESPALDO, obtener_tasa_cetes_28_dias

        tasa = obtener_tasa_cetes_28_dias()
        if tasa == TASA_RESPALDO:
            print(f"  {AVISO} Se está usando la tasa de respaldo ({tasa:.2%}).")
            print("      Revisa tu BANXICO_TOKEN; la app funciona igual, con ese valor fijo.")
        else:
            print(f"  {OK} Cetes 28 días: {tasa:.2%}")
    except Exception as e:
        print(f"  {AVISO} No se pudo consultar: {type(e).__name__} (la app usa tasa de respaldo)")
    return []


def main() -> None:
    print("=" * 62)
    print("  Diagnóstico de entorno · AC/DC Cash Flow")
    print("=" * 62)

    problemas = revisar_variables() + revisar_nessie() + revisar_mongo() + revisar_banxico()

    print("\n" + "=" * 62)
    if problemas:
        print(f"  {MAL} {len(problemas)} cosa(s) que arreglar:\n")
        for i, problema in enumerate(problemas, 1):
            print(f"   {i}. {problema}")
        print("\n  Guíate con backend/.env.example para el formato.")
        sys.exit(1)

    print(f"  {OK} Todo en orden. Levanta con: make dev")


if __name__ == "__main__":
    main()
