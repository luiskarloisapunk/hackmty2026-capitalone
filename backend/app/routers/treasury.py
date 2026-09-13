"""
Router de Tesorería — expone el motor predictivo AR(p) como API REST.

Endpoints
---------
POST /api/treasury/analyze
    Acepta transacciones Nessie (o las simula si no se proporcionan)
    y devuelve la proyección de liquidez a 30 días + recomendación de
    capital de trabajo.

GET /api/treasury/simulate
    Genera y retorna 365 días de transacciones sintéticas (útil para demo).
"""

from __future__ import annotations

from typing import Annotated

import numpy as np
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.modelo import (
    CashFlowEngine,
    NessieTransaction,
    WorkingCapitalAdvisor,
    aggregate_daily_cashflow,
    simulate_nessie_transactions,
)

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


# ---------------------------------------------------------------------------
# Esquemas de request / response (Pydantic v2)
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    transactions: list[NessieTransaction] | None = Field(
        default=None,
        description="Transacciones Nessie. Si es null se generan datos sintéticos.",
    )
    lag: int = Field(default=14, ge=2, le=60, description="Orden p del modelo AR")
    horizon: int = Field(default=30, ge=1, le=90, description="Días a proyectar")
    annual_rate: float = Field(
        default=0.065, gt=0.0, lt=1.0, description="Tasa de interés anual (decimal)"
    )
    current_balance: float | None = Field(
        default=None,
        description="Saldo líquido actual en $. Si es null se estima del historial.",
    )


class WorkingCapitalRec(BaseModel):
    required_principal: float
    surplus: float
    to_invest: float
    gap: float
    free_cushion: float
    coverage_ratio: float


class AnalyzeResponse(BaseModel):
    model_lag: int
    observations_used: int
    residual_std: float
    in_sample_r2: float
    forecast_30d: list[float]
    cumulative_cashflow: list[float]
    worst_day: int
    projected_deficit: float
    current_balance: float
    working_capital: WorkingCapitalRec | None
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/simulate", response_model=list[NessieTransaction])
def get_simulated_transactions(
    n_days: Annotated[int, Query(ge=30, le=730)] = 365,
    seed: Annotated[int, Query()] = 42,
) -> list[NessieTransaction]:
    """Genera transacciones sintéticas para demo o testing."""
    return simulate_nessie_transactions(n_days=n_days, seed=seed)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_treasury(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Pipeline completo de tesorería predictiva:

    1. Agrega transacciones → flujo neto diario
    2. Ajusta AR(p) via lstsq/SVD
    3. Proyecta `horizon` días con ventana deslizante
    4. Detecta el déficit máximo proyectado
    5. Calcula el principal de inversión necesario (interés compuesto)
    """
    # Paso 1 — Datos
    txs: list[NessieTransaction] = (
        body.transactions
        if body.transactions
        else simulate_nessie_transactions()
    )
    flows, _ = aggregate_daily_cashflow(txs)

    # Paso 2 — Ajuste del modelo
    engine = CashFlowEngine(lag=body.lag)
    engine.fit(flows)

    # Paso 3 — Proyección
    forecast: np.ndarray = engine.predict(horizon=body.horizon)
    cumulative: np.ndarray = np.cumsum(forecast)

    # Paso 4 — Análisis de liquidez
    worst_idx = int(np.argmin(cumulative))
    projected_deficit = float(cumulative[worst_idx])  # negativo = déficit

    # Saldo actual: explícito o estimado como suma de los últimos 30 días
    balance = (
        body.current_balance
        if body.current_balance is not None
        else float(flows[-30:].sum())
    )

    # Paso 5 — Recomendación de inversión
    wc_rec: WorkingCapitalRec | None = None
    message = "Sin déficit proyectado en el horizonte analizado."

    if projected_deficit < 0:
        years_to_deficit = (worst_idx + 1) / 365.0
        advisor = WorkingCapitalAdvisor(annual_rate=body.annual_rate)
        coverage = advisor.surplus_coverage(
            surplus=max(balance, 0.0),
            deficit=abs(projected_deficit),
            years=years_to_deficit,
        )
        wc_rec = WorkingCapitalRec(**coverage)
        action = "suficiente" if coverage["gap"] == 0 else "insuficiente"
        message = (
            f"Déficit de ${abs(projected_deficit):,.2f} proyectado en el día "
            f"{worst_idx + 1}. Saldo actual {action} "
            f"(ratio de cobertura: {coverage['coverage_ratio']:.2f}x)."
        )

    return AnalyzeResponse(
        model_lag=body.lag,
        observations_used=len(flows),
        residual_std=round(engine.residual_std(flows), 2),
        in_sample_r2=round(engine.in_sample_r2(flows), 4),
        forecast_30d=[round(f, 2) for f in forecast.tolist()],
        cumulative_cashflow=[round(c, 2) for c in cumulative.tolist()],
        worst_day=worst_idx + 1,
        projected_deficit=round(projected_deficit, 2),
        current_balance=round(balance, 2),
        working_capital=wc_rec,
        message=message,
    )
