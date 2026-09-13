"""
Plan de reinversión en inventario: cuánto se ha gastado, cuánto toca el mes
que viene y cuánto hay que tener listo para la próxima temporada alta.

Es el puente entre el historial crudo (ingreso + gasto de inventario por mes)
y regulacion.py, que razona en ciclos de temporada alta y no en meses.
"""

from app.services.regulacion import (
    TemporadaHistorica,
    calcular_crecimiento_interanual,
    proyectar_temporada_alta,
)
from app.services.temporadas import TEMPORADA_ALTA, PerfilTemporadas


def construir_temporadas_altas(
    perfil: PerfilTemporadas,
    gastos_por_periodo: dict[tuple[int, int], float],
) -> list[TemporadaHistorica]:
    """
    Agrupa los meses clasificados como temporada alta por año y suma su
    ingreso y su gasto de inventario, que es la forma en que regulacion.py
    espera el historial.
    """
    acumulado: dict[int, dict[str, float]] = {}

    for mes in perfil.historial_clasificado:
        if mes.temporada != TEMPORADA_ALTA:
            continue
        registro = acumulado.setdefault(mes.anio, {"ingreso": 0.0, "gasto": 0.0, "meses": 0})
        registro["ingreso"] += mes.monto
        registro["gasto"] += gastos_por_periodo.get((mes.anio, mes.mes), 0.0)
        registro["meses"] += 1

    if not acumulado:
        return []

    # El primer y el último año del historial suelen traer la temporada
    # cortada a la mitad. Compararlos contra un año completo inventa
    # crecimientos negativos enormes, así que solo se consideran los ciclos
    # con tantos meses altos como el más completo que se haya observado.
    meses_ciclo_completo = max(v["meses"] for v in acumulado.values())

    return [
        TemporadaHistorica(
            anio=anio,
            ingreso_temporada_alta=valores["ingreso"],
            gasto_inventario_temporada_alta=valores["gasto"],
        )
        for anio, valores in sorted(acumulado.items())
        if valores["gasto"] > 0 and valores["meses"] == meses_ciclo_completo
    ]


def proyectar_siguiente_mes(
    perfil: PerfilTemporadas,
    gastos_por_periodo: dict[tuple[int, int], float],
) -> dict:
    """
    Cuánto inventario toca comprar el mes que entra.

    Se apoya en la estacionalidad, no en el promedio general: si el mes que
    viene cayó en temporada alta el año pasado, el gasto se parecerá al de
    ese mes, no al de un mes cualquiera.
    """
    ultimo = perfil.historial_clasificado[-1]
    siguiente_mes = ultimo.mes % 12 + 1
    siguiente_anio = ultimo.anio + (1 if siguiente_mes == 1 else 0)

    # Mismo mes en años anteriores: la mejor referencia estacional que hay.
    analogos = [
        gastos_por_periodo[(anio, mes)]
        for (anio, mes) in gastos_por_periodo
        if mes == siguiente_mes
    ]

    if analogos:
        base = sum(analogos) / len(analogos)
        fuente = "mismo mes de años anteriores"
    else:
        valores = list(gastos_por_periodo.values())
        base = sum(valores) / len(valores) if valores else 0.0
        fuente = "promedio general (sin mes análogo en el historial)"

    crecimiento = calcular_crecimiento_interanual(
        construir_temporadas_altas(perfil, gastos_por_periodo)
    )
    factor = 1 + (crecimiento if crecimiento is not None else 0.0)

    return {
        "anio": siguiente_anio,
        "mes": siguiente_mes,
        "gasto_inventario_estimado": round(base * factor, 2),
        "base_historica": round(base, 2),
        "factor_crecimiento_aplicado": round(factor, 4),
        "fuente": fuente,
    }


def construir_plan(
    perfil: PerfilTemporadas,
    gastos_por_periodo: dict[tuple[int, int], float],
) -> dict:
    """Todo lo que la vista de reinversión necesita, en una sola llamada."""
    serie = [
        {
            "anio": mes.anio,
            "mes": mes.mes,
            "ingreso": round(mes.monto, 2),
            "gasto_inventario": round(gastos_por_periodo.get((mes.anio, mes.mes), 0.0), 2),
            "temporada": mes.temporada,
        }
        for mes in perfil.historial_clasificado
    ]

    temporadas_altas = construir_temporadas_altas(perfil, gastos_por_periodo)

    siguiente_temporada = None
    if temporadas_altas:
        proyeccion = proyectar_temporada_alta(temporadas_altas)
        siguiente_temporada = {
            "ingreso_proyectado": round(proyeccion["ingreso_proyectado"], 2),
            "gasto_inventario_proyectado": round(proyeccion["gasto_inventario"], 2),
            "margen_esperado": round(proyeccion["margen_esperado"], 2),
            "ingreso_temporada_anterior": round(proyeccion["ingreso_temporada_anterior"], 2),
            # Se conserva el nombre viejo: es lo que hay que apartar, y el
            # motor de cuentas lo consume con esa clave.
            "reserva_objetivo": round(proyeccion["gasto_inventario"], 2),
            "ratio_historico_gasto_ingreso": round(proyeccion["ratio_gasto_ingreso"], 4),
            "ciclos_considerados": len(temporadas_altas),
            "crecimiento_interanual": proyeccion["crecimiento_aplicado"],
            "crecimiento_fue_estimado": proyeccion["crecimiento_fue_estimado"],
        }

    return {
        "serie_mensual": serie,
        "siguiente_mes": proyectar_siguiente_mes(perfil, gastos_por_periodo),
        "siguiente_temporada_alta": siguiente_temporada,
    }
