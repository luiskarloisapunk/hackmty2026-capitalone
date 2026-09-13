"""
Router de Temporadas — expone el clasificador de temporadas estacionales
(alta/regular/baja) y la proyección de reserva de reinversión para la
siguiente temporada alta.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.nessie_client import nessie
from app.services.regulacion import (
    TemporadaHistorica,
    calcular_crecimiento_interanual,
    calcular_ratio_inventario,
    proyectar_reserva_reinversion,
)
from app.services.temporadas import IngresoMensual, construir_perfil_automatico

router = APIRouter(prefix="/api/temporadas", tags=["temporadas"])


# ---------------------------------------------------------------------------
# Esquemas de request / response (Pydantic v2)
# ---------------------------------------------------------------------------


class IngresoMensualIn(BaseModel):
    anio: int
    mes: int = Field(ge=1, le=12)
    monto: float


class ClasificacionMensualOut(BaseModel):
    anio: int
    mes: int
    monto: float
    temporada: str


class AnalizarTemporadasRequest(BaseModel):
    historial: list[IngresoMensualIn] | None = Field(
        default=None,
        description="Historial mensual manual. Si es null, se agrega desde los depósitos de la cuenta Nessie indicada en `nessie_account_id`.",
    )
    nessie_account_id: str | None = Field(
        default=None,
        description="Cuenta Nessie (checking) de la que se agregan los depósitos por mes si no se manda `historial`.",
    )
    umbral_desviaciones: float = Field(default=0.5, gt=0)


class PerfilTemporadasOut(BaseModel):
    ingreso_promedio_esperado: float
    promedio_general: float
    desviacion: float
    umbral_desviaciones: float
    historial_clasificado: list[ClasificacionMensualOut]
    temporada_mes_mas_reciente: str


class TemporadaHistoricaIn(BaseModel):
    anio: int
    ingreso_temporada_alta: float
    gasto_inventario_temporada_alta: float


class ReservaReinversionRequest(BaseModel):
    historial_temporadas_altas: list[TemporadaHistoricaIn]
    crecimiento_default_heuristico: float = Field(default=0.08, ge=0)


class ReservaReinversionResponse(BaseModel):
    reserva_proyectada: float
    ratio_historico_gasto_ingreso: float
    crecimiento_aplicado: float
    crecimiento_fue_estimado: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agregar_depositos_nessie(account_id: str) -> list[IngresoMensual]:
    depositos = nessie.get(f"/accounts/{account_id}/deposits")
    acumulado: dict[tuple[int, int], float] = {}
    for deposito in depositos:
        fecha = deposito["transaction_date"]  # "YYYY-MM-DD"
        anio, mes = int(fecha[:4]), int(fecha[5:7])
        acumulado[(anio, mes)] = acumulado.get((anio, mes), 0.0) + float(deposito["amount"])

    return [
        IngresoMensual(anio=anio, mes=mes, monto=monto)
        for (anio, mes), monto in sorted(acumulado.items())
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/analizar", response_model=PerfilTemporadasOut)
def analizar_temporadas(body: AnalizarTemporadasRequest) -> PerfilTemporadasOut:
    """
    Clasifica el historial mensual de una PyME en alta/regular/baja y calcula
    su ingreso base esperado ("corriente directa"). Usa `historial` si se
    manda, si no agrega los depósitos de `nessie_account_id` por mes.
    """
    if body.historial:
        historial = [
            IngresoMensual(anio=h.anio, mes=h.mes, monto=h.monto) for h in body.historial
        ]
    elif body.nessie_account_id:
        historial = _agregar_depositos_nessie(body.nessie_account_id)
    else:
        raise HTTPException(
            status_code=400, detail="Se requiere `historial` o `nessie_account_id`"
        )

    try:
        perfil = construir_perfil_automatico(
            historial, umbral_desviaciones=body.umbral_desviaciones
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ultimo_mes = perfil.historial_clasificado[-1]

    return PerfilTemporadasOut(
        ingreso_promedio_esperado=round(perfil.ingreso_promedio_esperado, 2),
        promedio_general=round(perfil.promedio_general, 2),
        desviacion=round(perfil.desviacion, 2),
        umbral_desviaciones=perfil.umbral_desviaciones,
        historial_clasificado=[
            ClasificacionMensualOut(
                anio=c.anio, mes=c.mes, monto=c.monto, temporada=c.temporada
            )
            for c in perfil.historial_clasificado
        ],
        temporada_mes_mas_reciente=ultimo_mes.temporada,
    )


@router.post("/reserva-reinversion", response_model=ReservaReinversionResponse)
def calcular_reserva_reinversion(body: ReservaReinversionRequest) -> ReservaReinversionResponse:
    """
    Proyecta cuánto debe apartarse (en la cuenta Savings) para la
    reinversión en inventario/insumos de cara a la siguiente temporada alta,
    escalando con el crecimiento histórico real de la PyME.
    """
    historial = [
        TemporadaHistorica(
            anio=h.anio,
            ingreso_temporada_alta=h.ingreso_temporada_alta,
            gasto_inventario_temporada_alta=h.gasto_inventario_temporada_alta,
        )
        for h in body.historial_temporadas_altas
    ]

    try:
        ratio = calcular_ratio_inventario(historial)
        reserva = proyectar_reserva_reinversion(
            historial, crecimiento_default_heuristico=body.crecimiento_default_heuristico
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    crecimiento_real = calcular_crecimiento_interanual(historial)
    crecimiento_aplicado = (
        crecimiento_real if crecimiento_real is not None else body.crecimiento_default_heuristico
    )

    return ReservaReinversionResponse(
        reserva_proyectada=round(reserva, 2),
        ratio_historico_gasto_ingreso=round(ratio, 4),
        crecimiento_aplicado=round(crecimiento_aplicado, 4),
        crecimiento_fue_estimado=crecimiento_real is None,
    )
