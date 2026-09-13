import pandas as pd

from app.services.temporadas import IngresoMensual, PerfilTemporadas, construir_perfil_automatico


def cargar_ingresos_desde_csv(ruta_csv: str) -> list[IngresoMensual]:
    """
    Lee el CSV que produce generador_csv.py (columnas: fecha "YYYY-MM",
    valores) y lo convierte al formato que espera el clasificador de
    temporadas. Si el formato del generador cambia (ej. se agregan columnas
    de gasto/categoría), este es el único lugar que hay que ajustar --
    temporadas.py y regulacion.py no se tocan.
    """
    df = pd.read_csv(ruta_csv)
    fecha_partes = df["fecha"].str.split("-", expand=True)

    return [
        IngresoMensual(anio=int(anio), mes=int(mes), monto=float(monto))
        for anio, mes, monto in zip(fecha_partes[0], fecha_partes[1], df["valores"])
    ]


def construir_perfil_desde_csv(
    ruta_csv: str,
    umbral_desviaciones: float = 0.5,
) -> PerfilTemporadas:
    historial = cargar_ingresos_desde_csv(ruta_csv)
    return construir_perfil_automatico(historial, umbral_desviaciones=umbral_desviaciones)
