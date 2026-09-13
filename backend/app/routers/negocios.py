"""
Router del negocio: su perfil, su panorama (home + cuentas), su plan de
reinversión, su proyección de liquidez, y la carga/descarga del historial
en CSV.
"""

from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.routers.auth import UsuarioOut, obtener_usuario_actual
from app.services import negocio_service
from app.services.liquidez import proyectar_liquidez
from app.services.plantillas_negocio import listar_plantillas
from app.services.productos import describir_productos, tasa_referencia_vigente

router = APIRouter(prefix="/api/negocios", tags=["negocios"])

COLUMNAS_CSV = ["fecha", "ingreso", "gasto_inventario"]


class LiquidezRequest(BaseModel):
    horizonte_dias: int = Field(default=90, ge=15, le=180)


async def _perfil_requerido(usuario: UsuarioOut) -> dict:
    perfil = await negocio_service.obtener_perfil(usuario.id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="Este usuario todavía no tiene un negocio dado de alta")
    return perfil


@router.get("/plantillas")
def obtener_plantillas() -> list[dict]:
    """Catálogo de giros para una PyME que aún no tiene historial propio."""
    return listar_plantillas()


@router.get("/productos")
def obtener_productos() -> dict:
    return {"productos": describir_productos(), "tasa_referencia": tasa_referencia_vigente()}


@router.get("/plantilla-csv")
def descargar_plantilla_csv() -> StreamingResponse:
    """
    CSV vacío con las columnas que espera el sistema, más un par de filas de
    ejemplo para que quede claro el formato de cada una.
    """
    ejemplo = pd.DataFrame(
        [
            {"fecha": "2025-01", "ingreso": 48000, "gasto_inventario": 15200},
            {"fecha": "2025-02", "ingreso": 51500, "gasto_inventario": 16800},
        ],
        columns=COLUMNAS_CSV,
    )
    buffer = io.StringIO()
    ejemplo.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="plantilla_historial.csv"'},
    )


@router.post("/mio/historial-csv")
async def subir_historial_csv(
    archivo: UploadFile = File(...),
    usuario: UsuarioOut = Depends(obtener_usuario_actual),
) -> dict:
    """Reemplaza el historial del negocio con el CSV que sube el usuario."""
    await _perfil_requerido(usuario)

    contenido = await archivo.read()
    try:
        df = pd.read_csv(io.BytesIO(contenido))
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo leer el archivo como CSV")

    faltantes = [c for c in COLUMNAS_CSV if c not in df.columns]
    if faltantes:
        raise HTTPException(
            status_code=400,
            detail=f"Al CSV le faltan estas columnas: {', '.join(faltantes)}. Descarga la plantilla para ver el formato.",
        )

    df = df.dropna(subset=COLUMNAS_CSV)
    if len(df) < 3:
        raise HTTPException(status_code=400, detail="El CSV necesita al menos 3 meses con datos completos")

    partes = df["fecha"].astype(str).str.strip().str.split("-", expand=True)
    if partes.shape[1] < 2:
        raise HTTPException(status_code=400, detail="La columna `fecha` debe venir como AAAA-MM (ej. 2025-01)")

    try:
        historial = [
            {
                "anio": int(anio),
                "mes": int(mes),
                "ingreso": float(ingreso),
                "gasto_inventario": float(gasto),
            }
            for anio, mes, ingreso, gasto in zip(
                partes[0], partes[1], df["ingreso"], df["gasto_inventario"]
            )
        ]
    except ValueError:
        raise HTTPException(status_code=400, detail="Hay valores no numéricos en `ingreso` o `gasto_inventario`")

    historial.sort(key=lambda m: (m["anio"], m["mes"]))
    await negocio_service.reemplazar_historial(usuario.id, historial)

    return {"meses_cargados": len(historial), "desde": historial[0], "hasta": historial[-1]}


@router.get("/mio")
async def mi_negocio(usuario: UsuarioOut = Depends(obtener_usuario_actual)) -> dict:
    perfil = await _perfil_requerido(usuario)
    return {
        "nombre": perfil.get("nombre"),
        "giro": perfil.get("giro"),
        "plantilla_id": perfil.get("plantilla_id"),
        "tiene_historial_propio": perfil.get("tiene_historial_propio", False),
        "historial_es_sintetico": perfil.get("historial_es_sintetico", False),
        "meses_de_historial": len(perfil.get("historial", [])),
    }


@router.get("/mio/panorama")
async def panorama(usuario: UsuarioOut = Depends(obtener_usuario_actual)) -> dict:
    perfil = await _perfil_requerido(usuario)
    return negocio_service.construir_panorama(perfil)


@router.get("/mio/reinversion")
async def reinversion(usuario: UsuarioOut = Depends(obtener_usuario_actual)) -> dict:
    perfil = await _perfil_requerido(usuario)
    return negocio_service.construir_reinversion(perfil)


@router.post("/mio/liquidez")
async def liquidez(
    body: LiquidezRequest,
    usuario: UsuarioOut = Depends(obtener_usuario_actual),
) -> dict:
    perfil = await _perfil_requerido(usuario)
    panorama_actual = negocio_service.construir_panorama(perfil)
    if not panorama_actual.get("listo"):
        return {"listo": False, "motivo": panorama_actual.get("motivo")}

    return proyectar_liquidez(
        historial=perfil.get("historial", []),
        saldo_actual=panorama_actual["cuentas"]["saldo_operacion"],
        tasa_anual=panorama_actual["tasa_referencia"]["tasa_anual"],
        horizonte_dias=body.horizonte_dias,
    )
