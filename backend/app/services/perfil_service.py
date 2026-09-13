"""
Perfil del negocio: sus datos, su giro, y su vínculo con Nessie.

Nessie es la fuente bancaria del challenge, así que el perfil es donde el
negocio se da de alta ahí: se crea su customer y sus tres cuentas con los
saldos que el motor de regulación calculó, y a partir de ahí se pueden
leer sus movimientos reales desde la API.
"""

import httpx

from app.services.db import perfiles_collection
from app.services.nessie_client import nessie
from app.services.plantillas_negocio import PLANTILLAS

# Nessie solo acepta 'Checking', 'Savings' y 'Credit Card' -- no existe un
# tipo "Investment". La cuenta de inversión se abre como Savings y se
# distingue por el apodo; la diferencia de producto (plazo, rendimiento,
# riesgo) la lleva nuestro backend, no el tipo de cuenta de Nessie.
CUENTAS_A_CREAR = [
    ("operacion", "Checking", "Operación", "saldo_operacion"),
    ("acceso_rapido", "Savings", "Fondo regulador", "saldo_acceso_rapido"),
    ("plazo_fijo", "Savings", "Inversión a plazo", "saldo_plazo_fijo"),
]


def _direccion_demo() -> dict:
    return {
        "street_number": "455",
        "street_name": "Av Constitución",
        "city": "Monterrey",
        "state": "NL",
        "zip": "64000",
    }


def estado_nessie(perfil_negocio: dict) -> dict:
    """
    Qué sabe Nessie de este negocio. Si nunca se vinculó, se dice y ya; si
    está vinculado pero la API no responde, se distingue una cosa de la
    otra en vez de mostrar todo vacío como si no hubiera nada.
    """
    customer_id = perfil_negocio.get("nessie_customer_id")
    if not customer_id:
        return {"vinculado": False, "cuentas": [], "error": None}

    try:
        cuentas = nessie.get(f"/customers/{customer_id}/accounts")
    except httpx.HTTPError as e:
        return {
            "vinculado": True,
            "customer_id": customer_id,
            "cuentas": [],
            "error": f"Nessie no respondió: {type(e).__name__}",
        }

    return {
        "vinculado": True,
        "customer_id": customer_id,
        "cuentas": [
            {
                "id": cuenta.get("_id"),
                "tipo": cuenta.get("type"),
                "nombre": cuenta.get("nickname"),
                "balance": cuenta.get("balance"),
            }
            for cuenta in cuentas
        ],
        "error": None,
    }


async def vincular_con_nessie(perfil_negocio: dict, saldos: dict) -> dict:
    """
    Da de alta el negocio en Nessie: crea el customer y sus tres cuentas con
    el saldo que el motor calculó para cada una.
    """
    nombre = perfil_negocio.get("nombre", "Negocio")
    partes = nombre.split(" ", 1)
    primer_nombre = partes[0]
    apellido = partes[1] if len(partes) > 1 else "SA de CV"

    # Nessie no deja borrar clientes (responde 403), así que si un intento
    # anterior alcanzó a crear el cliente y falló después, hay que reusarlo.
    # Si no, cada reintento deja basura permanente en un sandbox que el
    # equipo comparte.
    customer_id = None
    try:
        for cliente in nessie.get("/customers"):
            if cliente.get("first_name") == primer_nombre and cliente.get("last_name") == apellido:
                customer_id = cliente["_id"]
                break
    except httpx.HTTPError:
        pass

    if customer_id is None:
        respuesta = nessie.post(
            "/customers",
            {
                "first_name": primer_nombre,
                "last_name": apellido,
                "address": _direccion_demo(),
            },
        )
        customer_id = respuesta["objectCreated"]["_id"]

    # Se guarda el cliente apenas existe: si algo falla al abrir las cuentas,
    # el vínculo no se pierde y se puede reintentar, en vez de dejar un
    # cliente huérfano en Nessie que nadie sabe que ya se creó.
    await perfiles_collection.update_one(
        {"usuario_id": perfil_negocio["usuario_id"]},
        {"$set": {"nessie_customer_id": customer_id}},
    )

    existentes = {c.get("nickname") for c in nessie.get(f"/customers/{customer_id}/accounts")}

    creadas = []
    for producto_id, tipo, apodo, clave_saldo in CUENTAS_A_CREAR:
        if apodo in existentes:
            continue
        cuenta = nessie.post(
            f"/customers/{customer_id}/accounts",
            {
                "type": tipo,
                "nickname": apodo,
                "rewards": 0,
                "balance": round(saldos.get(clave_saldo, 0.0), 2),
            },
        )
        creadas.append(
            {
                "producto_id": producto_id,
                "id": cuenta["objectCreated"]["_id"],
                "tipo": tipo,
                "nombre": apodo,
                "balance": round(saldos.get(clave_saldo, 0.0), 2),
            }
        )

    await perfiles_collection.update_one(
        {"usuario_id": perfil_negocio["usuario_id"]},
        {"$set": {"nessie_cuentas": creadas}},
    )

    return {"vinculado": True, "customer_id": customer_id, "cuentas": creadas, "error": None}


def construir_perfil(perfil_negocio: dict, usuario: dict, panorama: dict) -> dict:
    plantilla = PLANTILLAS.get(perfil_negocio.get("plantilla_id"))
    historial = perfil_negocio.get("historial", [])

    ingresos = [m["ingreso"] for m in historial]
    gastos = [m.get("gasto_inventario", 0.0) for m in historial]

    return {
        "usuario": usuario,
        "negocio": {
            "nombre": perfil_negocio.get("nombre"),
            "giro": perfil_negocio.get("giro"),
            "plantilla_id": perfil_negocio.get("plantilla_id"),
            "plantilla_nombre": plantilla.nombre if plantilla else None,
            "picos_por_anio": round(12 / plantilla.periodo_meses) if plantilla else None,
            "historial_es_sintetico": perfil_negocio.get("historial_es_sintetico", False),
            "tiene_historial_propio": perfil_negocio.get("tiene_historial_propio", False),
        },
        "historial": {
            "meses": len(historial),
            "desde": historial[0] if historial else None,
            "hasta": historial[-1] if historial else None,
            "ingreso_total": round(sum(ingresos), 2),
            "ingreso_promedio": round(sum(ingresos) / len(ingresos), 2) if ingresos else 0,
            "ingreso_maximo": round(max(ingresos), 2) if ingresos else 0,
            "ingreso_minimo": round(min(ingresos), 2) if ingresos else 0,
            "gasto_inventario_total": round(sum(gastos), 2),
        },
        "nessie": estado_nessie(perfil_negocio),
        "saldos_calculados": panorama.get("cuentas") if panorama.get("listo") else None,
    }
