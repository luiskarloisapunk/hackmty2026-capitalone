"""
Los tres productos de cuenta que ofrece la plataforma, y el rendimiento
esperado de cada uno, anclado a la tasa real de Cetes de Banxico.

La lógica del negocio: entre más líquido el dinero, menos rinde. La cuenta
de operación no rinde nada, la de acceso rápido rinde una fracción de Cetes
(se queda líquida), y la de inversión rinde Cetes completo o más, a cambio
de plazo y -- en el caso de acciones -- de riesgo real de pérdida.
"""

from app.services.banxico_client import obtener_tasa_cetes_28_dias

# Qué fracción de la tasa de referencia paga cada producto.
FACTOR_ACCESO_RAPIDO = 0.65  # líquido 24/7, por eso rinde menos
FACTOR_PLAZO_FIJO = 1.00  # replica Cetes a plazo
FACTOR_ACCIONES = 1.85  # rendimiento OBJETIVO, no garantizado

COMISION_SOBRE_ALPHA = 0.20  # nos quedamos con 20% de lo que exceda el benchmark


def _neto_de_comision(tasa_bruta: float, tasa_referencia: float) -> tuple[float, float]:
    """
    Aplica el modelo de comisión: solo cobramos sobre el alpha, es decir
    sobre lo que el producto gana POR ENCIMA del benchmark libre de riesgo.
    Si no le ganamos a Cetes, no cobramos nada.
    """
    alpha = max(tasa_bruta - tasa_referencia, 0.0)
    comision = alpha * COMISION_SOBRE_ALPHA
    return tasa_bruta - comision, comision


def describir_productos() -> list[dict]:
    """
    Los tres productos con su rendimiento esperado vigente.
    `advertencia` viene lleno solo donde hay riesgo real que comunicar.
    """
    referencia = obtener_tasa_cetes_28_dias()

    bruta_rapida = referencia * FACTOR_ACCESO_RAPIDO
    neta_rapida, comision_rapida = _neto_de_comision(bruta_rapida, referencia)

    bruta_plazo = referencia * FACTOR_PLAZO_FIJO
    neta_plazo, comision_plazo = _neto_de_comision(bruta_plazo, referencia)

    bruta_acciones = referencia * FACTOR_ACCIONES
    neta_acciones, comision_acciones = _neto_de_comision(bruta_acciones, referencia)

    return [
        {
            "id": "operacion",
            "tipo_nessie": "Checking",
            "nombre": "Cuenta de operación",
            "descripcion": "El dinero del día a día: cobras, pagas nómina y proveedores desde aquí.",
            "liquidez": "inmediata",
            "riesgo": "ninguno",
            "rendimiento_anual_esperado": 0.0,
            "comision_anual": 0.0,
            "garantizado": True,
            "advertencia": None,
        },
        {
            "id": "acceso_rapido",
            "tipo_nessie": "Savings",
            "nombre": "Fondo regulador",
            "descripcion": (
                "Tu colchón de temporada. Genera rendimiento todos los días y lo "
                "puedes retirar cuando quieras, sin penalización ni plazo."
            ),
            "liquidez": "inmediata",
            "riesgo": "muy bajo",
            "rendimiento_anual_esperado": round(neta_rapida, 4),
            "comision_anual": round(comision_rapida, 4),
            "garantizado": True,
            "advertencia": None,
        },
        {
            "id": "plazo_fijo",
            "tipo_nessie": "Investment",
            "nombre": "Inversión a plazo (Cetes)",
            "descripcion": (
                "El excedente de tu temporada alta invertido en Cetes a 28 días, "
                "programado para liberarse antes de tu próxima reinversión."
            ),
            "liquidez": "28 días",
            "riesgo": "bajo",
            "rendimiento_anual_esperado": round(neta_plazo, 4),
            "comision_anual": round(comision_plazo, 4),
            "garantizado": False,
            "advertencia": (
                "El rendimiento depende de la tasa vigente de Cetes y puede cambiar "
                "en cada subasta. No es un rendimiento garantizado."
            ),
        },
        {
            "id": "acciones",
            "tipo_nessie": "Investment",
            "nombre": "Paquete de acciones",
            "descripcion": (
                "Canasta diversificada de acciones. Mayor rendimiento potencial y "
                "también posibilidad real de perder parte del capital."
            ),
            "liquidez": "2 días hábiles",
            "riesgo": "alto",
            "rendimiento_anual_esperado": round(neta_acciones, 4),
            "comision_anual": round(comision_acciones, 4),
            "garantizado": False,
            "advertencia": (
                "Este producto NO está asegurado. El rendimiento mostrado es un "
                "objetivo histórico, no una promesa: puedes perder parte o la "
                "totalidad de lo que inviertas. Inviertes bajo tu propio riesgo."
            ),
        },
    ]


def tasa_referencia_vigente() -> dict:
    tasa = obtener_tasa_cetes_28_dias()
    return {
        "tasa_anual": round(tasa, 4),
        "fuente": "Cetes 28 días (Banxico, serie SF43936)",
        "comision_sobre_alpha": COMISION_SOBRE_ALPHA,
    }
