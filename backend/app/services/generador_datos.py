"""
Generador de historiales financieros sintéticos.

Es la versión importable de la lógica que vive en generador_csv.py (que es
el script interactivo). Aquí los parámetros se pasan como argumentos, para
poder generar perfiles DISTINTOS por negocio en vez de la misma serie.

Modelo: valor(t) = (base + crecimiento·t + amplitud·sin(2π(t - fase)/periodo)) · ruido
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class PerfilNegocio:
    """Los parámetros que hacen que un giro se vea distinto a otro."""

    nombre: str
    giro: str
    base_mensual: float
    amplitud: float
    periodo_meses: int = 12
    fase_meses: float = 0.0  # corre el pico del ciclo (0 = pico en enero)
    crecimiento_mensual: float = 0.0
    ruido_relativo: float = 0.05
    gasto_inventario_min: float = 0.25
    gasto_inventario_max: float = 0.45


@dataclass
class HistorialGenerado:
    meses: list[dict] = field(default_factory=list)

    def ingresos(self) -> list[dict]:
        return [{"anio": m["anio"], "mes": m["mes"], "monto": m["ingreso"]} for m in self.meses]


def generar_historial(
    perfil: PerfilNegocio,
    meses: int = 24,
    anio_inicio: int = 2024,
    mes_inicio: int = 1,
    seed: int | None = None,
) -> HistorialGenerado:
    """
    Genera `meses` de ingreso y gasto de inventario para un perfil de negocio.

    El gasto de inventario es un % variable del ingreso (no fijo) y además
    se adelanta al ciclo: un negocio compra inventario ANTES de su
    temporada alta, no durante -- por eso el gasto usa el ingreso del mes
    siguiente como referencia cuando existe.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(meses, dtype=np.float64)

    ciclo = perfil.amplitud * np.sin(2 * np.pi * (t - perfil.fase_meses) / perfil.periodo_meses)
    tendencia = perfil.base_mensual + perfil.crecimiento_mensual * t
    ingresos = tendencia + ciclo
    ingresos = ingresos * rng.normal(1.0, perfil.ruido_relativo, meses)
    ingresos = np.clip(ingresos, perfil.base_mensual * 0.15, None).round(2)

    porcentajes = rng.uniform(perfil.gasto_inventario_min, perfil.gasto_inventario_max, meses)
    # El inventario se compra un mes antes de venderlo.
    referencia = np.concatenate([ingresos[1:], ingresos[-1:]])
    gastos = (referencia * porcentajes).round(2)

    registros = []
    for i in range(meses):
        total_meses = (mes_inicio - 1) + i
        registros.append(
            {
                "anio": anio_inicio + total_meses // 12,
                "mes": total_meses % 12 + 1,
                "ingreso": float(ingresos[i]),
                "gasto_inventario": float(gastos[i]),
            }
        )

    return HistorialGenerado(meses=registros)


def generar_flujo_diario(
    historial: HistorialGenerado,
    gastos_fijos_mensuales: float,
    ruido_relativo: float = 0.22,
    seed: int | None = None,
) -> np.ndarray:
    """
    Convierte el historial mensual en flujo neto DIARIO, que es lo que come
    el motor AR(p) de liquidez.

    Clave: los gastos fijos NO bajan en temporada baja aunque el ingreso sí.
    Por eso el flujo neto se vuelve negativo en los valles -- que es
    justamente el problema de caja que el producto resuelve, y sin eso el
    pronóstico nunca detecta un déficit.
    """
    rng = np.random.default_rng(seed)
    dias_por_mes = 30
    flujos = []

    for mes in historial.meses:
        neto_mensual = mes["ingreso"] - mes["gasto_inventario"] - gastos_fijos_mensuales
        diario = neto_mensual / dias_por_mes
        escala = max(abs(diario), gastos_fijos_mensuales / dias_por_mes)
        ruido = rng.normal(0.0, escala * ruido_relativo, dias_por_mes)
        flujos.append(diario + ruido)

    return np.concatenate(flujos).round(2)
