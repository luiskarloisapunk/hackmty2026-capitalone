"""
Motor de regulación: corre la lógica "corriente alterna → corriente directa"
mes a mes sobre el historial del negocio y deja los saldos de las 3 cuentas.

La regla, en una línea: en temporada alta el excedente sobre la línea base
se aparta (primero a la reserva líquida, el resto a inversión); en temporada
baja se retira de la reserva para completar hasta la línea base.
"""

from dataclasses import dataclass

from app.services.temporadas import PerfilTemporadas


@dataclass
class MovimientoMensual:
    anio: int
    mes: int
    ingreso: float
    temporada: str
    ingreso_regularizado: float
    a_reserva: float
    a_inversion: float
    desde_reserva: float
    rendimiento_generado: float
    saldo_reserva: float
    saldo_inversion: float


def simular_regulacion(
    perfil: PerfilTemporadas,
    reserva_objetivo: float,
    tasa_acceso_rapido: float,
    tasa_inversion: float,
) -> list[MovimientoMensual]:
    """
    Recorre el historial aplicando la regulación y devuelve el detalle mes
    a mes (incluye el rendimiento devengado, prorrateado a mensual).

    `reserva_objetivo` es cuánto debe quedarse líquido antes de mandar nada
    a inversión: es el dinero que la PyME va a necesitar para reabastecer
    inventario, y por eso no se puede amarrar a plazo.
    """
    base = perfil.ingreso_promedio_esperado
    mensual_rapida = tasa_acceso_rapido / 12
    mensual_inversion = tasa_inversion / 12

    saldo_reserva = 0.0
    saldo_inversion = 0.0
    movimientos: list[MovimientoMensual] = []

    for mes in perfil.historial_clasificado:
        rendimiento = saldo_reserva * mensual_rapida + saldo_inversion * mensual_inversion
        saldo_reserva += saldo_reserva * mensual_rapida
        saldo_inversion += saldo_inversion * mensual_inversion

        a_reserva = 0.0
        a_inversion = 0.0
        desde_reserva = 0.0

        if mes.monto > base:
            excedente = mes.monto - base
            falta_para_objetivo = max(reserva_objetivo - saldo_reserva, 0.0)
            a_reserva = min(excedente, falta_para_objetivo)
            a_inversion = excedente - a_reserva
            saldo_reserva += a_reserva
            saldo_inversion += a_inversion
            regularizado = base
        else:
            faltante = base - mes.monto
            desde_reserva = min(faltante, saldo_reserva)
            saldo_reserva -= desde_reserva

            # Si la reserva líquida no alcanza, se liquida inversión: es
            # preferible romper el plazo a que el negocio se quede sin caja.
            faltante_restante = faltante - desde_reserva
            desde_inversion = min(faltante_restante, saldo_inversion)
            saldo_inversion -= desde_inversion
            desde_reserva += desde_inversion

            regularizado = mes.monto + desde_reserva

        # Rebalanceo: el colchón líquido se mantiene en su objetivo trayendo
        # dinero de vuelta desde el plazo fijo. Sin esto la reserva se queda
        # en cero después de cada temporada baja y el negocio entra a la
        # siguiente sin liquidez, que es exactamente lo que queremos evitar.
        if saldo_reserva < reserva_objetivo and saldo_inversion > 0:
            rebalance = min(reserva_objetivo - saldo_reserva, saldo_inversion)
            saldo_inversion -= rebalance
            saldo_reserva += rebalance

        movimientos.append(
            MovimientoMensual(
                anio=mes.anio,
                mes=mes.mes,
                ingreso=round(mes.monto, 2),
                temporada=mes.temporada,
                ingreso_regularizado=round(regularizado, 2),
                a_reserva=round(a_reserva, 2),
                a_inversion=round(a_inversion, 2),
                desde_reserva=round(desde_reserva, 2),
                rendimiento_generado=round(rendimiento, 2),
                saldo_reserva=round(saldo_reserva, 2),
                saldo_inversion=round(saldo_inversion, 2),
            )
        )

    return movimientos


def resumen_cuentas(
    movimientos: list[MovimientoMensual],
    saldo_operacion: float,
) -> dict:
    """Saldos finales y cuánto rendimiento acumuló el negocio en total."""
    if not movimientos:
        return {
            "saldo_operacion": round(saldo_operacion, 2),
            "saldo_acceso_rapido": 0.0,
            "saldo_plazo_fijo": 0.0,
            "rendimiento_acumulado": 0.0,
            "meses_cubiertos": 0,
        }

    ultimo = movimientos[-1]
    return {
        "saldo_operacion": round(saldo_operacion, 2),
        "saldo_acceso_rapido": ultimo.saldo_reserva,
        "saldo_plazo_fijo": ultimo.saldo_inversion,
        "rendimiento_acumulado": round(sum(m.rendimiento_generado for m in movimientos), 2),
        "meses_cubiertos": sum(1 for m in movimientos if m.desde_reserva > 0),
    }
