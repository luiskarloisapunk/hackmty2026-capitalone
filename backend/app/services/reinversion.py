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
    Arma cada ciclo de temporada alta con su ingreso y con TODO lo que se
    gastó para llegar a él: la preparación previa más lo gastado durante la
    temporada. Contar solo el gasto de los meses altos subestima el costo
    cuando la compra ocurre antes de vender -- en el campo, la semilla y el
    fertilizante se pagan meses antes de cosechar.

    Los ciclos se agrupan por el año en que empiezan, así una temporada que
    cruza de año (nov–feb) no se parte en dos, y un negocio con dos picos al
    año se compara contra su mismo año anterior.
    """
    ciclos: list[dict] = []
    pendiente = 0.0
    actual: dict | None = None
    meses_fuera = 0
    gasto_en_pausa = 0.0

    for mes in perfil.historial_clasificado:
        gasto = gastos_por_periodo.get((mes.anio, mes.mes), 0.0)

        if mes.temporada == TEMPORADA_ALTA:
            if actual is None:
                actual = {"anio": mes.anio, "ingreso": 0.0, "gasto": pendiente}
                pendiente = 0.0
            # Un solo mes flojo dentro de la temporada no la parte en dos.
            actual["gasto"] += gasto_en_pausa
            gasto_en_pausa = 0.0
            meses_fuera = 0
            actual["ingreso"] += mes.monto
            actual["gasto"] += gasto
        elif actual is None:
            pendiente += gasto
        else:
            meses_fuera += 1
            gasto_en_pausa += gasto
            if meses_fuera >= 2:
                ciclos.append(actual)
                actual = None
                pendiente = gasto_en_pausa
                gasto_en_pausa = 0.0
                meses_fuera = 0

    # El primer ciclo no trae completa su preparación (el historial empieza a
    # la mitad) y el que sigue abierto al final no ha terminado: ninguno es
    # comparable, así que quedan fuera.
    completos = ciclos[1:]
    if not completos:
        return []

    por_anio: dict[int, dict[str, float]] = {}
    for ciclo in completos:
        grupo = por_anio.setdefault(ciclo["anio"], {"ingreso": 0.0, "gasto": 0.0, "ciclos": 0})
        grupo["ingreso"] += ciclo["ingreso"]
        grupo["gasto"] += ciclo["gasto"]
        grupo["ciclos"] += 1

    ciclos_por_anio = max(g["ciclos"] for g in por_anio.values())

    return [
        TemporadaHistorica(
            anio=anio,
            ingreso_temporada_alta=valores["ingreso"],
            gasto_inventario_temporada_alta=valores["gasto"],
        )
        for anio, valores in sorted(por_anio.items())
        if valores["gasto"] > 0 and valores["ciclos"] == ciclos_por_anio
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
