from dataclasses import dataclass


@dataclass
class TemporadaHistorica:
    """
    Un ciclo de temporada alta ya cerrado. Este es el contrato de datos que
    necesita este módulo -- de dónde salgan estos números (CSV, Nessie,
    captura manual) es responsabilidad de quien arme esa integración.
    """
    anio: int
    ingreso_temporada_alta: float
    gasto_inventario_temporada_alta: float


def calcular_ratio_inventario(historial: list[TemporadaHistorica]) -> float:
    """
    Relación histórica entre lo gastado en inventario/insumos y el ingreso
    de temporada alta. Promedia varios ciclos para suavizar un año atípico.
    """
    if not historial:
        raise ValueError("Se necesita al menos una temporada alta histórica")
    ratios = [
        t.gasto_inventario_temporada_alta / t.ingreso_temporada_alta
        for t in historial
        if t.ingreso_temporada_alta > 0
    ]
    if not ratios:
        raise ValueError("Ningún registro histórico tiene ingreso mayor a cero")
    return sum(ratios) / len(ratios)


def calcular_crecimiento_interanual(historial: list[TemporadaHistorica]) -> float | None:
    """
    Crecimiento entre las dos temporadas altas más recientes (año vs año),
    para no confundir crecimiento real con el efecto normal de la
    estacionalidad. None si no hay al menos dos ciclos con qué comparar.
    """
    if len(historial) < 2:
        return None
    anterior, actual = sorted(historial, key=lambda t: t.anio)[-2:]
    if anterior.ingreso_temporada_alta == 0:
        return None
    return (
        actual.ingreso_temporada_alta - anterior.ingreso_temporada_alta
    ) / anterior.ingreso_temporada_alta


def proyectar_reserva_reinversion(
    historial: list[TemporadaHistorica],
    crecimiento_default_heuristico: float = 0.08,
) -> float:
    """
    Cuánto debe apartarse como reserva líquida (en la cuenta Savings) para
    la reinversión en inventario/insumos de cara a la SIGUIENTE temporada
    alta. Escala con el crecimiento real del negocio en vez de ser un monto
    fijo: usa la relación histórica gasto/ingreso aplicada al ingreso
    proyectado del siguiente ciclo.

    Si la PyME solo tiene un ciclo histórico (o ninguno con el que comparar
    crecimiento), se usa `crecimiento_default_heuristico` como placeholder
    -- reemplazar por una plantilla de crecimiento por sector cuando exista.
    """
    return proyectar_temporada_alta(historial, crecimiento_default_heuristico)["gasto_inventario"]


def proyectar_temporada_alta(
    historial: list[TemporadaHistorica],
    crecimiento_default_heuristico: float = 0.08,
) -> dict:
    """
    El panorama completo de la siguiente temporada alta: cuánto se espera
    vender, cuánto costará surtirse, y qué queda en medio.

    La reserva por sí sola no dice nada: saber que hay que apartar $200k
    solo es útil junto al ingreso que se espera recibir.
    """
    ratio = calcular_ratio_inventario(historial)
    ultima_temporada = sorted(historial, key=lambda t: t.anio)[-1]

    crecimiento = calcular_crecimiento_interanual(historial)
    crecimiento_estimado = crecimiento is None
    if crecimiento_estimado:
        crecimiento = crecimiento_default_heuristico

    ingreso_proyectado = ultima_temporada.ingreso_temporada_alta * (1 + crecimiento)
    gasto_inventario = ratio * ingreso_proyectado

    return {
        "ingreso_proyectado": ingreso_proyectado,
        "gasto_inventario": gasto_inventario,
        "margen_esperado": ingreso_proyectado - gasto_inventario,
        "ratio_gasto_ingreso": ratio,
        "crecimiento_aplicado": crecimiento,
        "crecimiento_fue_estimado": crecimiento_estimado,
        "ingreso_temporada_anterior": ultima_temporada.ingreso_temporada_alta,
    }
