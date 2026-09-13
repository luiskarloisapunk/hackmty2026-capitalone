"""
Motor Predictivo de Flujo de Caja — Modelo AR(p) via Proyección Ortogonal (SVD).

Fundamento matemático
=====================
Dado el historial de flujos diarios y = [y₀, y₁, ..., y_{n-1}], construimos
el sistema sobredeterminado:

    A · β = b

donde A ∈ ℝ^{(n-p) × (p+1)} es la matriz de Hankel de ventanas deslizantes:

    A[i] = [1,  y[i],  y[i+1],  ...,  y[i+p-1]]
              ↑         ↑ lags en orden cronológico (más antiguo → más reciente)
           intercepto

y b[i] = y[i+p] es el valor objetivo (el día siguiente a la ventana).

La solución de mínimos cuadrados β* minimiza ‖Aβ − b‖²:

    β* = argmin ‖Aβ − b‖² = A† · b    (A† = pseudoinversa de Moore-Penrose)

numpy.linalg.lstsq la calcula internamente via SVD (A = UΣVᵀ):

    A† = V · Σ† · Uᵀ    donde Σ† invierte solo los valores singulares > rcond·σ_max

Esto garantiza estabilidad numérica frente a multicolinealidad entre lags
(ventanas temporales altamente correlacionadas comparten subespacios de la SVD).

Predicción (ventana deslizante)
================================
Una vez ajustado β*, para predecir el paso t+1:

    x_t = [1, y[t-p], y[t-p+1], ..., y[t-1]]    ← vector de características
    ŷ_{t+1} = x_t · β*

La ventana se desliza incorporando cada nueva predicción (feedback loop),
sin recalcular la SVD: complejidad O(p) por paso.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.lib.stride_tricks import as_strided


@dataclass
class CashFlowEngine:
    """
    Motor AR(p) de flujo de caja resuelto por proyección ortogonal vía SVD.

    Parámetros
    ----------
    lag   : orden p del modelo (número de días anteriores usados como features)
    rcond : umbral relativo para truncar valores singulares pequeños en lstsq
            (None → numpy usa machine epsilon × max(m,n) × σ_max)
    """

    lag: int = 14
    rcond: float | None = None

    # Atributos internos — inicializados en fit()
    _beta: np.ndarray = field(init=False, repr=False)
    _history: np.ndarray = field(init=False, repr=False)
    _fitted: bool = field(default=False, init=False)

    # ------------------------------------------------------------------
    # Construcción de la matriz de diseño (cero bucles Python)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_design_matrix(
        y: np.ndarray, p: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Construye A y b usando as_strided: vista zero-copy de y como
        bloques superpuestos de tamaño p, sin copias de datos intermedias.

        A[i, j] = y[i + j]   para i ∈ [0, n-p-1], j ∈ [0, p-1]
        b[i]    = y[i + p]

        La primera columna de A se rellena con unos (intercepto β₀).
        """
        n = len(y)
        rows = n - p
        stride = y.strides[0]  # bytes entre elementos consecutivos

        # Vista deslizante: A_raw[i] = y[i : i+p]  (sin copia)
        A_raw: np.ndarray = as_strided(
            y,
            shape=(rows, p),
            strides=(stride, stride),
        )

        # Añadir columna de intercepto a la izquierda
        ones = np.ones((rows, 1), dtype=np.float64)
        A: np.ndarray = np.hstack([ones, A_raw])   # shape: (n-p, p+1)
        b: np.ndarray = y[p:].copy()               # shape: (n-p,)

        return A, b

    # ------------------------------------------------------------------
    # Ajuste del modelo (Proyección Ortogonal)
    # ------------------------------------------------------------------

    def fit(self, flows: np.ndarray) -> "CashFlowEngine":
        """
        Calcula β* = argmin ‖Aβ − b‖² mediante lstsq (SVD interna).

        La proyección ortogonal de b sobre el espacio columna de A entrega
        el residual mínimo: e = b − Aβ* ⊥ col(A).

        Parámetros
        ----------
        flows : array float64 de flujos netos diarios (longitud ≥ lag + 1)

        Retorna self para encadenamiento (fluent interface).
        """
        if len(flows) < self.lag + 1:
            raise ValueError(
                f"Se necesitan al menos {self.lag + 1} observaciones; "
                f"recibidas: {len(flows)}."
            )

        A, b = self._build_design_matrix(flows, self.lag)

        # lstsq devuelve (solución, residuos, rango, valores singulares)
        result = np.linalg.lstsq(A, b, rcond=self.rcond)
        self._beta = result[0]            # shape: (lag+1,)

        # Preservar las últimas `lag` observaciones reales para el primer paso
        self._history = flows[-self.lag :].copy()
        self._fitted = True
        return self

    # ------------------------------------------------------------------
    # Predicción con ventana deslizante
    # ------------------------------------------------------------------

    def predict(self, horizon: int = 30) -> np.ndarray:
        """
        Proyecta los próximos `horizon` días de flujo de caja.

        Algoritmo de ventana deslizante:
            para t = 0, 1, ..., horizon-1:
                x_t = [1, window[0], ..., window[lag-1]]   (orden cronológico)
                ŷ_t = x_t · β*
                window ← shift_left(window) + [ŷ_t]

        Complejidad: O(horizon × lag) — sin recalcular SVD.

        Parámetros
        ----------
        horizon : número de días futuros a predecir

        Retorna
        -------
        np.ndarray float64 de longitud `horizon`
        """
        if not self._fitted:
            raise RuntimeError("Llama a fit() antes de predict().")

        window = self._history.copy()          # (lag,) orden cronológico
        predictions = np.empty(horizon, dtype=np.float64)

        for i in range(horizon):
            # [1, y_{t-lag}, ..., y_{t-1}] — misma estructura que las filas de A
            x = np.empty(self.lag + 1, dtype=np.float64)
            x[0] = 1.0
            x[1:] = window

            ŷ = float(x @ self._beta)
            predictions[i] = ŷ

            # Deslizar ventana: descartar lag más antiguo, agregar nueva predicción
            window = np.roll(window, -1)
            window[-1] = ŷ

        return predictions

    # ------------------------------------------------------------------
    # Simulación estocástica (bootstrap de residuos)
    # ------------------------------------------------------------------

    def simulate(
        self,
        flows: np.ndarray,
        horizon: int = 30,
        n_sims: int = 500,
        seed: int | None = None,
    ) -> np.ndarray:
        """
        Proyecta `horizon` días en `n_sims` trayectorias, remuestreando los
        residuos reales del ajuste en cada paso.

        Por qué esto y no `predict()`: el pronóstico puntual de un AR(p)
        iterado converge a la media (la incertidumbre se promedia a cero en
        cada paso), así que sale una línea casi plana y su acumulado sale
        casi recto -- el "escenario ideal" que no existe en la vida real.
        Al reinyectar ruido muestreado de los residuos (bootstrap), cada
        trayectoria conserva la volatilidad que el negocio realmente tiene,
        y los percentiles de esas trayectorias dan la banda de confianza.

        Retorna
        -------
        np.ndarray de forma (n_sims, horizon)
        """
        if not self._fitted:
            raise RuntimeError("Llama a fit() antes de simulate().")

        A, b = self._build_design_matrix(flows, self.lag)
        residuos = b - A @ self._beta

        rng = np.random.default_rng(seed)
        ventanas = np.tile(self._history, (n_sims, 1))  # (n_sims, lag)
        trayectorias = np.empty((n_sims, horizon), dtype=np.float64)

        intercepto = self._beta[0]
        pesos = self._beta[1:]

        for paso in range(horizon):
            choques = rng.choice(residuos, size=n_sims, replace=True)
            siguiente = intercepto + ventanas @ pesos + choques
            trayectorias[:, paso] = siguiente
            ventanas = np.roll(ventanas, -1, axis=1)
            ventanas[:, -1] = siguiente

        return trayectorias

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------

    def residual_std(self, flows: np.ndarray) -> float:
        """Desviación estándar de los residuos en muestra (error típico del modelo)."""
        if not self._fitted:
            raise RuntimeError("Llama a fit() primero.")
        A, b = self._build_design_matrix(flows, self.lag)
        return float(np.std(b - A @ self._beta))

    def in_sample_r2(self, flows: np.ndarray) -> float:
        """R² en muestra: fracción de varianza explicada por el modelo AR(p)."""
        if not self._fitted:
            raise RuntimeError("Llama a fit() primero.")
        A, b = self._build_design_matrix(flows, self.lag)
        ss_res = float(np.sum((b - A @ self._beta) ** 2))
        ss_tot = float(np.sum((b - b.mean()) ** 2))
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    @property
    def coefficients(self) -> np.ndarray:
        """β* = [β₀, β₁, …, β_p] — intercepto seguido de pesos de lags."""
        if not self._fitted:
            raise RuntimeError("Llama a fit() primero.")
        return self._beta.copy()
