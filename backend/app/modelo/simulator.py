"""
Simulador de transacciones sintéticas que imitan el esquema JSON de la API Nessie.

Modelo de flujo neto diario:
    income(t) = base_income + A·cos(2π·t/365) + ε_i,   ε_i ~ N(0, σ²)
    expense(t) = base_expense + 0.4A·cos(2π·t/365) + ε_e

El coseno garantiza pico en t=0 (enero) y valle en t=182 (julio = temporada baja).
El diferencial de amplitud (1.0 vs 0.4) asegura que el flujo NETO replique
el mismo ciclo estacional: positivo en temporada alta, estrecho en baja.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import numpy as np
from typing_extensions import TypedDict  # requerido por Pydantic v2 en Python < 3.12


class NessieTransaction(TypedDict):
    """Subconjunto del esquema de transacción de la API Nessie."""

    transaction_id: str
    date: str        # ISO-8601: "YYYY-MM-DD"
    amount: float    # positivo = ingreso (credit), negativo = gasto (debit)
    type: str        # "credit" | "debit"
    description: str


def simulate_nessie_transactions(
    n_days: int = 365,
    base_income: float = 5_000.0,
    base_expense: float = 3_500.0,
    amplitude: float = 2_000.0,
    noise_std: float = 500.0,
    seed: int = 42,
    start_date: date | None = None,
) -> list[NessieTransaction]:
    """
    Genera `n_days` pares de transacciones (crédito + débito) para una PyME estacional.

    Parámetros
    ----------
    n_days       : número de días a simular
    base_income  : ingreso diario promedio ($)
    base_expense : gasto diario promedio ($)
    amplitude    : amplitud del ciclo estacional ($)
    noise_std    : desviación estándar del ruido gaussiano ($)
    seed         : semilla del generador para reproducibilidad
    start_date   : primer día de la simulación (default: 1 enero del año actual)

    Retorna
    -------
    Lista de dicts con esquema NessieTransaction, dos entradas por día.
    """
    rng = np.random.default_rng(seed)

    if start_date is None:
        start_date = date.today().replace(month=1, day=1)

    # Eje temporal normalizado para el ciclo anual
    t = np.arange(n_days, dtype=np.float64)
    seasonal_cycle = np.cos(2.0 * np.pi * t / 365.0)  # pico en t=0, valle en t=182

    # Señal de ingresos + ruido gaussiano; clip para evitar valores negativos
    incomes: np.ndarray = np.clip(
        base_income + amplitude * seasonal_cycle + rng.normal(0.0, noise_std, n_days),
        a_min=200.0,
        a_max=None,
    )

    # Gastos con amplitud reducida (0.4x) → el flujo neto hereda el mismo ciclo
    expenses: np.ndarray = np.clip(
        base_expense + (amplitude * 0.4) * seasonal_cycle + rng.normal(0.0, noise_std * 0.7, n_days),
        a_min=100.0,
        a_max=None,
    )

    transactions: list[NessieTransaction] = []
    for i in range(n_days):
        tx_date = (start_date + timedelta(days=i)).isoformat()
        base_id = f"TX{i:05d}"

        transactions.append(
            NessieTransaction(
                transaction_id=f"{base_id}C",
                date=tx_date,
                amount=round(float(incomes[i]), 2),
                type="credit",
                description="Ventas diarias",
            )
        )
        transactions.append(
            NessieTransaction(
                transaction_id=f"{base_id}D",
                date=tx_date,
                amount=-round(float(expenses[i]), 2),
                type="debit",
                description="Gastos operativos",
            )
        )

    return transactions


def aggregate_daily_cashflow(
    transactions: list[NessieTransaction],
) -> tuple[np.ndarray, list[str]]:
    """
    Agrega transacciones por fecha → flujo neto diario.

    Retorna
    -------
    flows : np.ndarray (float64) con el flujo neto de cada día
    dates : list[str] con las fechas en orden cronológico
    """
    daily: dict[str, float] = defaultdict(float)
    for tx in transactions:
        daily[tx["date"]] += tx["amount"]

    sorted_dates = sorted(daily.keys())
    flows = np.array([daily[d] for d in sorted_dates], dtype=np.float64)
    return flows, sorted_dates
