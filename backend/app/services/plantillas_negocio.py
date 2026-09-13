"""
Plantillas de estacionalidad por giro.

Sirven para dos cosas:
1. Una PyME nueva SIN historial elige la plantilla que más se parece a su
   giro, y arrancamos con ese patrón hasta que acumule datos reales.
2. Sembrar los negocios de demo con perfiles distintos entre sí.

La fase corre el pico del ciclo: con t=0 en enero, el pico cae en
`fase + periodo/4` meses.
"""

from app.services.generador_datos import PerfilNegocio

PLANTILLAS: dict[str, PerfilNegocio] = {
    "retail_navideno": PerfilNegocio(
        nombre="Retail de temporada navideña",
        giro="Decoración, regalos y artículos de fin de año",
        base_mensual=48000,
        amplitud=62000,
        periodo_meses=12,
        fase_meses=8,  # pico en diciembre
        crecimiento_mensual=900,
        ruido_relativo=0.07,
        gasto_inventario_min=0.30,
        gasto_inventario_max=0.48,
    ),
    "heladeria": PerfilNegocio(
        nombre="Heladería / bebidas frías",
        giro="Alimentos y bebidas de consumo estacional",
        base_mensual=62000,
        amplitud=38000,
        periodo_meses=12,
        fase_meses=3,  # pico en junio-julio
        crecimiento_mensual=450,
        ruido_relativo=0.06,
        gasto_inventario_min=0.22,
        gasto_inventario_max=0.34,
    ),
    "papeleria_escolar": PerfilNegocio(
        nombre="Papelería y útiles escolares",
        giro="Papelería con ciclo de regreso a clases",
        base_mensual=38000,
        amplitud=30000,
        periodo_meses=6,  # dos picos al año: agosto y enero
        fase_meses=5.5,
        crecimiento_mensual=300,
        ruido_relativo=0.08,
        gasto_inventario_min=0.28,
        gasto_inventario_max=0.42,
    ),
    "turismo_playa": PerfilNegocio(
        nombre="Turismo y hospedaje",
        giro="Servicios turísticos con temporada vacacional",
        base_mensual=85000,
        amplitud=55000,
        periodo_meses=12,
        fase_meses=4,  # pico en julio-agosto
        crecimiento_mensual=700,
        ruido_relativo=0.09,
        gasto_inventario_min=0.15,
        gasto_inventario_max=0.28,
    ),
    "agricola": PerfilNegocio(
        nombre="Agrícola / cosecha",
        giro="Producción agrícola con ciclo de cosecha",
        base_mensual=55000,
        amplitud=70000,
        periodo_meses=12,
        fase_meses=7,  # pico en noviembre (cosecha del ciclo primavera-verano)
        crecimiento_mensual=400,
        ruido_relativo=0.11,
        gasto_inventario_min=0.40,
        gasto_inventario_max=0.60,
        desfase_insumos_meses=5,  # semilla y fertilizante se compran al sembrar, en junio
    ),
    "constante": PerfilNegocio(
        nombre="Negocio sin estacionalidad marcada",
        giro="Ingresos relativamente parejos todo el año",
        base_mensual=52000,
        amplitud=6000,
        periodo_meses=12,
        fase_meses=0,
        crecimiento_mensual=350,
        ruido_relativo=0.05,
    ),
}


def listar_plantillas() -> list[dict]:
    """Catálogo para que una PyME nueva elija con qué patrón arrancar."""
    return [
        {
            "id": clave,
            "nombre": perfil.nombre,
            "giro": perfil.giro,
            "ingreso_base_mensual": perfil.base_mensual,
            "intensidad_estacional": round(perfil.amplitud / perfil.base_mensual, 2),
            "picos_por_anio": round(12 / perfil.periodo_meses),
        }
        for clave, perfil in PLANTILLAS.items()
    ]
