"""
Perfil de negocio de cada usuario: su historial financiero y todo lo que se
deriva de él (temporadas, cuentas, reinversión).

El historial vive aquí en un solo lugar y todas las vistas del producto lo
consumen: la gráfica del home, las cuentas, la predicción de liquidez y el
plan de reinversión salen del mismo origen.
"""

from app.services.db import perfiles_collection
from app.services.generador_datos import generar_historial
from app.services.motor_cuentas import resumen_cuentas, simular_regulacion
from app.services.plantillas_negocio import PLANTILLAS
from app.services.productos import describir_productos, tasa_referencia_vigente
from app.services.reinversion import construir_plan
from app.services.temporadas import IngresoMensual, construir_perfil_automatico

GASTOS_FIJOS_POR_DEFECTO = 0.42  # fracción del ingreso base que se va en fijos


def _gastos_por_periodo(historial: list[dict]) -> dict[tuple[int, int], float]:
    return {(m["anio"], m["mes"]): m.get("gasto_inventario", 0.0) for m in historial}


def _perfil_temporadas(historial: list[dict]):
    ingresos = [IngresoMensual(anio=m["anio"], mes=m["mes"], monto=m["ingreso"]) for m in historial]
    return construir_perfil_automatico(ingresos)


async def obtener_perfil(usuario_id: str) -> dict | None:
    return await perfiles_collection.find_one({"usuario_id": usuario_id})


async def crear_perfil(
    usuario_id: str,
    nombre_negocio: str,
    plantilla_id: str | None,
    tiene_historial: bool,
) -> dict:
    """
    Crea el perfil al registrarse.

    Si el negocio NO tiene historial propio, se siembra con la plantilla de
    su giro para que pueda usar el producto desde el día uno; en cuanto suba
    su CSV real, ese historial sintético se reemplaza.
    """
    historial: list[dict] = []
    giro = None

    if not tiene_historial and plantilla_id in PLANTILLAS:
        perfil_sintetico = PLANTILLAS[plantilla_id]
        giro = perfil_sintetico.giro
        generado = generar_historial(perfil_sintetico, meses=24, anio_inicio=2024, seed=None)
        historial = generado.meses

    documento = {
        "usuario_id": usuario_id,
        "nombre": nombre_negocio,
        "giro": giro,
        "plantilla_id": plantilla_id,
        "tiene_historial_propio": tiene_historial,
        "historial_es_sintetico": bool(historial) and not tiene_historial,
        "historial": historial,
        "saldo_operacion": 25000.0,
    }

    await perfiles_collection.insert_one(documento)
    documento.pop("_id", None)
    return documento


async def reemplazar_historial(usuario_id: str, historial: list[dict]) -> None:
    await perfiles_collection.update_one(
        {"usuario_id": usuario_id},
        {
            "$set": {
                "historial": historial,
                "historial_es_sintetico": False,
                "tiene_historial_propio": True,
            }
        },
    )


def construir_panorama(perfil_negocio: dict) -> dict:
    """
    Lo que alimenta el home y la vista de cuentas: temporadas clasificadas,
    saldos de las 3 cuentas tras correr la regulación, y los productos con
    su rendimiento vigente.
    """
    historial = perfil_negocio.get("historial", [])
    if len(historial) < 3:
        return {
            "listo": False,
            "motivo": "Se necesitan al menos 3 meses de historial para analizar temporadas.",
        }

    perfil = _perfil_temporadas(historial)
    gastos = _gastos_por_periodo(historial)
    plan = construir_plan(perfil, gastos)

    # Cuánto se queda líquido y cuánto se pone a trabajar.
    #
    # Líquido: 3 meses de colchón (el criterio clásico de tesorería) más el
    # inventario del mes que entra. Todo lo demás se va a plazo fijo: el
    # dinero del inventario de la próxima temporada alta SÍ debe estar
    # invertido -- se sabe con meses de anticipación cuándo se va a ocupar,
    # así que puede rendir mientras espera, que es justo la idea del
    # producto. Si aun así hace falta caja, el motor liquida inversión.
    base = perfil.ingreso_promedio_esperado
    deficits = [base - m.monto for m in perfil.historial_clasificado[-12:] if m.monto < base]
    deficit_mensual_promedio = sum(deficits) / len(deficits) if deficits else 0.0
    colchon_temporada_baja = deficit_mensual_promedio * 3

    inventario_proximo_mes = plan["siguiente_mes"]["gasto_inventario_estimado"]
    reserva_inventario = 0.0
    if plan["siguiente_temporada_alta"]:
        reserva_inventario = plan["siguiente_temporada_alta"]["reserva_objetivo"]

    reserva_objetivo = colchon_temporada_baja + inventario_proximo_mes

    productos = describir_productos()
    por_id = {p["id"]: p for p in productos}

    movimientos = simular_regulacion(
        perfil,
        reserva_objetivo=reserva_objetivo,
        tasa_acceso_rapido=por_id["acceso_rapido"]["rendimiento_anual_esperado"],
        tasa_inversion=por_id["plazo_fijo"]["rendimiento_anual_esperado"],
    )
    cuentas = resumen_cuentas(movimientos, perfil_negocio.get("saldo_operacion", 0.0))

    ultimo = perfil.historial_clasificado[-1]

    return {
        "listo": True,
        "negocio": {
            "nombre": perfil_negocio.get("nombre"),
            "giro": perfil_negocio.get("giro"),
            "historial_es_sintetico": perfil_negocio.get("historial_es_sintetico", False),
        },
        "temporadas": {
            "ingreso_promedio_esperado": round(perfil.ingreso_promedio_esperado, 2),
            "temporada_actual": ultimo.temporada,
            "ultimo_mes": {"anio": ultimo.anio, "mes": ultimo.mes, "monto": round(ultimo.monto, 2)},
            "historial_clasificado": [
                {
                    "anio": m.anio,
                    "mes": m.mes,
                    "monto": round(m.monto, 2),
                    "temporada": m.temporada,
                }
                for m in perfil.historial_clasificado
            ],
        },
        "regulacion": [
            {
                "anio": m.anio,
                "mes": m.mes,
                "ingreso": m.ingreso,
                "ingreso_regularizado": m.ingreso_regularizado,
                "a_reserva": m.a_reserva,
                "a_inversion": m.a_inversion,
                "desde_reserva": m.desde_reserva,
                "saldo_reserva": m.saldo_reserva,
                "saldo_inversion": m.saldo_inversion,
            }
            for m in movimientos
        ],
        "cuentas": cuentas,
        "productos": productos,
        "reserva_objetivo": round(reserva_objetivo, 2),
        "reserva_desglose": {
            "colchon_temporada_baja": round(colchon_temporada_baja, 2),
            "inventario_proximo_mes": round(inventario_proximo_mes, 2),
            "inventario_proxima_temporada_en_plazo": round(reserva_inventario, 2),
        },
        "tasa_referencia": tasa_referencia_vigente(),
    }


def construir_reinversion(perfil_negocio: dict) -> dict:
    historial = perfil_negocio.get("historial", [])
    if len(historial) < 3:
        return {"listo": False, "motivo": "Historial insuficiente."}

    perfil = _perfil_temporadas(historial)
    plan = construir_plan(perfil, _gastos_por_periodo(historial))
    plan["listo"] = True
    return plan
