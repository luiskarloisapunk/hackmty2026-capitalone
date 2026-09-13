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
    ratio = calcular_ratio_inventario(historial)
    ultima_temporada = sorted(historial, key=lambda t: t.anio)[-1]

    crecimiento = calcular_crecimiento_interanual(historial)
    if crecimiento is None:
        crecimiento = crecimiento_default_heuristico

    ingreso_proyectado = ultima_temporada.ingreso_temporada_alta * (1 + crecimiento)
    return ratio * ingreso_proyectado
