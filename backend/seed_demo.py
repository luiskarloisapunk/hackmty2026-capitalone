"""
Siembra los negocios de demo: usuario + perfil + historial generado.

Cada negocio usa una plantilla de giro distinta (fase y periodo distintos),
así que sus gráficas NO se parecen entre sí -- ese era justamente el punto.

Uso:  cd backend && python seed_demo.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth import hashear_password  # noqa: E402
from app.services.db import perfiles_collection, usuarios_collection  # noqa: E402
from app.services.generador_datos import generar_historial  # noqa: E402
from app.services.plantillas_negocio import PLANTILLAS  # noqa: E402

PASSWORD_DEMO = "password"

NEGOCIOS_DEMO = [
    {
        "email": "navidena@demo.com",
        "nombre": "Alejandra Ruiz",
        "nombre_negocio": "Decoraciones del Norte",
        "plantilla_id": "retail_navideno",
        "saldo_operacion": 38000.0,
        "seed": 101,
    },
    {
        "email": "heladeria@demo.com",
        "nombre": "Bruno Salas",
        "nombre_negocio": "Nieves del Valle",
        "plantilla_id": "heladeria",
        "saldo_operacion": 26500.0,
        "seed": 202,
    },
    {
        "email": "papeleria@demo.com",
        "nombre": "Carmen Ortiz",
        "nombre_negocio": "Papelería Monterrey",
        "plantilla_id": "papeleria_escolar",
        "saldo_operacion": 19800.0,
        "seed": 303,
    },
]


async def sembrar() -> None:
    password_hash = hashear_password(PASSWORD_DEMO)

    for negocio in NEGOCIOS_DEMO:
        plantilla = PLANTILLAS[negocio["plantilla_id"]]
        # 32 meses desde enero 2024 -> termina en agosto 2026.
        generado = generar_historial(
            plantilla, meses=32, anio_inicio=2024, mes_inicio=1, seed=negocio["seed"]
        )

        await usuarios_collection.delete_many({"email": negocio["email"]})
        resultado = await usuarios_collection.insert_one(
            {
                "email": negocio["email"],
                "nombre": negocio["nombre"],
                "password_hash": password_hash,
                "es_demo": True,
            }
        )
        usuario_id = str(resultado.inserted_id)

        await perfiles_collection.delete_many({"nombre": negocio["nombre_negocio"]})
        await perfiles_collection.insert_one(
            {
                "usuario_id": usuario_id,
                "nombre": negocio["nombre_negocio"],
                "giro": plantilla.giro,
                "plantilla_id": negocio["plantilla_id"],
                "tiene_historial_propio": True,
                "historial_es_sintetico": True,
                "historial": generado.meses,
                "saldo_operacion": negocio["saldo_operacion"],
                "es_demo": True,
            }
        )

        picos = sorted(generado.meses[-12:], key=lambda m: -m["ingreso"])[:2]
        meses_pico = ", ".join(f"{m['anio']}-{m['mes']:02d}" for m in picos)
        print(f"✅ {negocio['nombre_negocio']:<26} {negocio['email']:<22} pico en {meses_pico}")

    print(f"\nTodas las cuentas de demo usan la contraseña: {PASSWORD_DEMO}")


if __name__ == "__main__":
    asyncio.run(sembrar())
