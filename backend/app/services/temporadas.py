from dataclasses import dataclass
from statistics import mean, pstdev

TEMPORADA_ALTA = "alta"
TEMPORADA_REGULAR = "regular"
TEMPORADA_BAJA = "baja"


@dataclass
class IngresoMensual:
    anio: int
    mes: int
    monto: float


@dataclass
class ClasificacionMensual:
    anio: int
    mes: int
    monto: float
    temporada: str


@dataclass
class PerfilTemporadas:
    """
    Resultado de clasificar el historial de una PyME: la línea base
    ("corriente directa") contra la que se compara cada mes, y la
    clasificación de cada mes histórico. `clasificar()` se usa para
    catalogar un ingreso nuevo (ej. el mes en curso) con el mismo criterio.
    """
    ingreso_promedio_esperado: float
    promedio_general: float
    desviacion: float
    umbral_desviaciones: float
    historial_clasificado: list[ClasificacionMensual]

    def clasificar(self, monto: float) -> str:
        if self.desviacion == 0:
            return TEMPORADA_REGULAR
        if monto > self.promedio_general + self.umbral_desviaciones * self.desviacion:
            return TEMPORADA_ALTA
        if monto < self.promedio_general - self.umbral_desviaciones * self.desviacion:
            return TEMPORADA_BAJA
        return TEMPORADA_REGULAR


def construir_perfil_automatico(
    historial: list[IngresoMensual],
    umbral_desviaciones: float = 0.5,
) -> PerfilTemporadas:
    """
    Modo "automático": clasifica cada mes comparando su ingreso contra el
    promedio y la desviación estándar de TODO el historial, y calcula
    `ingreso_promedio_esperado` como el promedio de los meses que salieron
    "regular" (no el promedio general, que estaría distorsionado por los
    meses de temporada alta/baja).

    Requiere que la PyME ya tenga historial real de Nessie (idealmente
    12+ meses). Para PyMEs nuevas sin ese historial, se usa el modo
    predictivo por plantilla de sector (pendiente de implementar).
    """
    if len(historial) < 3:
        raise ValueError(
            "Se necesitan al menos 3 meses de historial para clasificar automáticamente"
        )

    montos = [h.monto for h in historial]
    promedio_general = mean(montos)
    desviacion = pstdev(montos)

    perfil_temporal = PerfilTemporadas(
        ingreso_promedio_esperado=promedio_general,  # placeholder, se corrige abajo
        promedio_general=promedio_general,
        desviacion=desviacion,
        umbral_desviaciones=umbral_desviaciones,
        historial_clasificado=[],
    )

    clasificados = [
        ClasificacionMensual(h.anio, h.mes, h.monto, perfil_temporal.clasificar(h.monto))
        for h in historial
    ]

    montos_regulares = [c.monto for c in clasificados if c.temporada == TEMPORADA_REGULAR]
    ingreso_promedio_esperado = mean(montos_regulares) if montos_regulares else promedio_general

    return PerfilTemporadas(
        ingreso_promedio_esperado=ingreso_promedio_esperado,
        promedio_general=promedio_general,
        desviacion=desviacion,
        umbral_desviaciones=umbral_desviaciones,
        historial_clasificado=clasificados,
    )
