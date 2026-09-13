import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

BANXICO_TOKEN = os.getenv("BANXICO_TOKEN")
BANXICO_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1"

# Serie SF43936: Cetes a 28 días, tasa de rendimiento (resultado de subasta
# semanal). Se usa como tasa de referencia libre de riesgo para el asesor de
# capital de trabajo y para el motor de inversión.
SERIE_CETES_28_DIAS = "SF43936"

TASA_RESPALDO = 0.065  # si Banxico no responde y no hay nada en caché

_CACHE_TTL_SEGUNDOS = 6 * 60 * 60  # las subastas de Cetes son semanales
_cache: dict[str, tuple[float, float]] = {}  # serie -> (tasa_decimal, timestamp)


def _consultar_dato_mas_reciente(serie: str) -> float:
    url = f"{BANXICO_BASE_URL}/series/{serie}/datos/oportuno"
    r = httpx.get(url, params={"token": BANXICO_TOKEN}, timeout=10.0)
    r.raise_for_status()
    datos = r.json()["bmx"]["series"][0]["datos"]
    return float(datos[-1]["dato"])


def obtener_tasa_cetes_28_dias() -> float:
    """
    Tasa de rendimiento de Cetes a 28 días, como decimal (6.25% -> 0.0625).
    Cachea en memoria por unas horas para no golpear la API de Banxico en
    cada request -- las subastas de Cetes son semanales, no hace falta
    consultar más seguido que eso.
    """
    ahora = time.monotonic()
    if SERIE_CETES_28_DIAS in _cache:
        tasa, guardado_en = _cache[SERIE_CETES_28_DIAS]
        if ahora - guardado_en < _CACHE_TTL_SEGUNDOS:
            return tasa

    try:
        tasa_porcentaje = _consultar_dato_mas_reciente(SERIE_CETES_28_DIAS)
        tasa = tasa_porcentaje / 100
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        if SERIE_CETES_28_DIAS in _cache:
            return _cache[SERIE_CETES_28_DIAS][0]
        return TASA_RESPALDO

    _cache[SERIE_CETES_28_DIAS] = (tasa, ahora)
    return tasa
