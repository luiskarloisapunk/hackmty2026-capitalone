"""
Predicción de liquidez a 30/90 días para un negocio, sobre el motor AR(p).

Usa simulación estocástica en vez del pronóstico puntual: un AR(p) iterado
converge a su media y produce una proyección plana cuyo acumulado sale
prácticamente recto -- el escenario ideal que nunca ocurre. Con bootstrap de
residuos cada trayectoria conserva la volatilidad real del negocio, y los
percentiles dan el rango honesto: optimista, esperado y pesimista.
"""

import numpy as np

from app.modelo import CashFlowEngine, WorkingCapitalAdvisor
from app.services.generador_datos import HistorialGenerado, generar_flujo_diario

LAG_POR_DEFECTO = 14
SIMULACIONES = 600


def proyectar_liquidez(
    historial: list[dict],
    saldo_actual: float,
    tasa_anual: float,
    horizonte_dias: int = 90,
    gastos_fijos_mensuales: float | None = None,
    seed: int | None = 7,
) -> dict:
    if len(historial) < 6:
        return {"listo": False, "motivo": "Se necesitan al menos 6 meses de historial."}

    if gastos_fijos_mensuales is None:
        ingreso_promedio = sum(m["ingreso"] for m in historial) / len(historial)
        gastos_fijos_mensuales = ingreso_promedio * 0.42

    flujos = generar_flujo_diario(
        HistorialGenerado(meses=historial),
        gastos_fijos_mensuales=gastos_fijos_mensuales,
        seed=seed,
    )

    motor = CashFlowEngine(lag=LAG_POR_DEFECTO).fit(flujos)
    trayectorias = motor.simulate(
        flujos, horizon=horizonte_dias, n_sims=SIMULACIONES, seed=seed
    )

    acumulado = saldo_actual + np.cumsum(trayectorias, axis=1)
    p10 = np.percentile(acumulado, 10, axis=0)
    p50 = np.percentile(acumulado, 50, axis=0)
    p90 = np.percentile(acumulado, 90, axis=0)

    dia_peor = int(np.argmin(p10)) + 1
    saldo_minimo_pesimista = float(p10.min())
    saldo_minimo_esperado = float(p50.min())

    # Probabilidad de quedarse sin caja en algún punto del horizonte.
    prob_deficit = float((acumulado.min(axis=1) < 0).mean())

    recomendacion = None
    if saldo_minimo_pesimista < 0:
        asesor = WorkingCapitalAdvisor(annual_rate=tasa_anual)
        anios_al_deficit = dia_peor / 365.0
        recomendacion = asesor.surplus_coverage(
            surplus=max(saldo_actual, 0.0),
            deficit=abs(saldo_minimo_pesimista),
            years=max(anios_al_deficit, 1 / 365),
        )

    return {
        "listo": True,
        "horizonte_dias": horizonte_dias,
        "saldo_inicial": round(saldo_actual, 2),
        "r2_en_muestra": round(motor.in_sample_r2(flujos), 4),
        "volatilidad_diaria": round(motor.residual_std(flujos), 2),
        "proyeccion": [
            {
                "dia": i + 1,
                "pesimista": round(float(p10[i]), 2),
                "esperado": round(float(p50[i]), 2),
                "optimista": round(float(p90[i]), 2),
            }
            for i in range(horizonte_dias)
        ],
        "dia_mas_critico": dia_peor,
        "saldo_minimo_esperado": round(saldo_minimo_esperado, 2),
        "saldo_minimo_pesimista": round(saldo_minimo_pesimista, 2),
        "probabilidad_deficit": round(prob_deficit, 4),
        "recomendacion_capital": recomendacion,
        "tasa_anual_usada": round(tasa_anual, 4),
    }
