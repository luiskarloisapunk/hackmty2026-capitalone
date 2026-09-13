"""
Asesor de Capital de Trabajo — Lógica de Inversión por Interés Compuesto.

Fórmula central:
    P · (1 + r/n)^(n·t) ≥ D

Despejando el principal mínimo P:
    P = D / (1 + r/n)^(n·t)

donde:
    D = déficit proyectado (valor absoluto)
    r = tasa de interés anual (decimal, e.g. 0.08)
    n = capitalizaciones por año (12 = mensual, 365 = diaria)
    t = tiempo en años hasta el déficit

Interpretación: P es el capital que, invertido hoy a tasa r con n
capitalizaciones, alcanza exactamente D al momento t. Cualquier
P + ε cubre el déficit con margen.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkingCapitalAdvisor:
    """
    Calcula el colchón de capital de trabajo para cubrir déficits proyectados.

    Parámetros
    ----------
    annual_rate : tasa de interés anual (decimal, e.g. 0.065 = 6.5%)
    compounds   : número de capitalizaciones por año (default 12 = mensual)
    """

    annual_rate: float = 0.065
    compounds: int = 12

    def required_principal(self, deficit: float, years: float) -> float:
        """
        Calcula el capital P exacto a invertir hoy para cubrir el déficit D.

            P = D / (1 + r/n)^(n·t)

        Parámetros
        ----------
        deficit : valor absoluto del déficit proyectado (D > 0, en $)
        years   : tiempo en años hasta que ocurre el déficit (t > 0)

        Retorna
        -------
        Principal P requerido en $.
        """
        if deficit <= 0.0:
            raise ValueError(f"El déficit debe ser positivo; recibido: {deficit}")
        if years <= 0.0:
            raise ValueError(f"El tiempo debe ser positivo; recibido: {years}")

        r, n, t = self.annual_rate, float(self.compounds), years
        factor = (1.0 + r / n) ** (n * t)
        return deficit / factor

    def surplus_coverage(
        self,
        surplus: float,
        deficit: float,
        years: float,
    ) -> dict[str, float]:
        """
        Analiza si el excedente actual S cubre el déficit proyectado D.

        Retorna un dict con:
        - required_principal : P mínimo a invertir hoy ($)
        - surplus            : excedente disponible S ($)
        - to_invest          : P si S ≥ P, de lo contrario la fracción alcanzable ($)
        - gap                : faltante si S < P (0 si S ≥ P) ($)
        - free_cushion       : excedente libre S − P (0 si S < P) ($)
        - coverage_ratio     : S / P (≥ 1 = cobertura completa)

        Parámetros
        ----------
        surplus : efectivo o activos líquidos disponibles hoy ($)
        deficit : valor absoluto del déficit proyectado ($)
        years   : tiempo en años hasta el déficit
        """
        P = self.required_principal(deficit, years)
        gap = max(0.0, P - surplus)
        cushion = max(0.0, surplus - P)
        to_invest = min(surplus, P)

        return {
            "required_principal": round(P, 2),
            "surplus": round(surplus, 2),
            "to_invest": round(to_invest, 2),
            "gap": round(gap, 2),
            "free_cushion": round(cushion, 2),
            "coverage_ratio": round(surplus / P, 4) if P > 0 else float("inf"),
        }

    def investment_growth(
        self,
        principal: float,
        years: float,
    ) -> float:
        """
        Calcula el valor futuro de `principal` invertido durante `years` años.

            FV = P · (1 + r/n)^(n·t)

        Útil para verificar que P crece exactamente hasta D.
        """
        r, n, t = self.annual_rate, float(self.compounds), years
        return principal * (1.0 + r / n) ** (n * t)
