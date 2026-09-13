import { useState } from 'react'
import { moneda, porcentaje } from '../formato'

const SALDO_POR_PRODUCTO = {
  operacion: 'saldo_operacion',
  acceso_rapido: 'saldo_acceso_rapido',
  plazo_fijo: 'saldo_plazo_fijo',
  acciones: null,
}

export function Cuentas({ panorama }) {
  // Acordeón: abrir una cierra la anterior, como las notas colapsadas de Obsidian.
  const [abierta, setAbierta] = useState('acceso_rapido')

  const { productos, cuentas, tasa_referencia: tasa, reserva_desglose: desglose } = panorama

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div>
          <h2 className="seccion-titulo">Tus cuentas</h2>
          <p className="seccion-bajada">
            Entre más líquido el dinero, menos rinde. Abre cada cuenta para ver
            a qué plazo está y cuánto genera.
          </p>
        </div>
        <div className="tasa-referencia">
          <span className="tasa-valor">{porcentaje(tasa.tasa_anual)}</span>
          <span className="tasa-etiqueta">{tasa.fuente}</span>
        </div>
      </header>

      <div className="acordeon">
        {productos.map((producto) => (
          <TarjetaCuenta
            key={producto.id}
            producto={producto}
            saldo={
              SALDO_POR_PRODUCTO[producto.id]
                ? cuentas[SALDO_POR_PRODUCTO[producto.id]]
                : null
            }
            abierta={abierta === producto.id}
            onAlternar={() => setAbierta(abierta === producto.id ? null : producto.id)}
            desglose={producto.id === 'acceso_rapido' ? desglose : null}
          />
        ))}
      </div>

      <div className="panel-plano">
        <div className="dato-linea">
          <span>Rendimiento que ya generaron tus cuentas</span>
          <strong className="cifra-positiva">{moneda(cuentas.rendimiento_acumulado)}</strong>
        </div>
        <div className="dato-linea">
          <span>Meses de temporada baja cubiertos con tu reserva</span>
          <strong>{cuentas.meses_cubiertos}</strong>
        </div>
      </div>
    </div>
  )
}

function TarjetaCuenta({ producto, saldo, abierta, onAlternar, desglose }) {
  const [monto, setMonto] = useState('')
  const [confirmado, setConfirmado] = useState(false)

  const invertible = producto.id === 'plazo_fijo' || producto.id === 'acciones'
  const riesgoAlto = producto.riesgo === 'alto'

  return (
    <article className={`tarjeta-cuenta ${abierta ? 'abierta' : ''} riesgo-${producto.riesgo.replace(' ', '-')}`}>
      <button type="button" className="tarjeta-cabecera" onClick={onAlternar} aria-expanded={abierta}>
        <span className={`indicador indicador-${producto.riesgo.replace(' ', '-')}`} />

        <span className="tarjeta-identidad">
          <span className="tarjeta-nombre">{producto.nombre}</span>
          <span className="tarjeta-meta">
            Liquidez {producto.liquidez} · riesgo {producto.riesgo}
          </span>
        </span>

        <span className="tarjeta-cifras">
          {saldo !== null && <span className="tarjeta-saldo">{moneda(saldo)}</span>}
          <span className="tarjeta-rendimiento">
            {producto.rendimiento_anual_esperado > 0
              ? `${porcentaje(producto.rendimiento_anual_esperado)} anual`
              : 'Sin rendimiento'}
          </span>
        </span>

        <span className={`chevron ${abierta ? 'abierto' : ''}`} aria-hidden="true" />
      </button>

      {abierta && (
        <div className="tarjeta-cuerpo">
          <p className="tarjeta-descripcion">{producto.descripcion}</p>

          {desglose && (
            <div className="desglose">
              <div className="desglose-fila">
                <span>Colchón de temporada baja (3 meses)</span>
                <strong>{moneda(desglose.colchon_temporada_baja)}</strong>
              </div>
              <div className="desglose-fila">
                <span>Inventario del próximo mes</span>
                <strong>{moneda(desglose.inventario_proximo_mes)}</strong>
              </div>
            </div>
          )}

          {producto.comision_anual > 0 && (
            <p className="tarjeta-comision">
              Comisión: {porcentaje(producto.comision_anual)} anual, cobrada solo
              sobre lo que este producto gane por encima de Cetes. Si no le
              ganamos al benchmark, no cobramos.
            </p>
          )}

          {producto.advertencia && (
            <div className={`aviso ${riesgoAlto ? 'aviso-fuerte' : ''}`}>
              <span className="aviso-titulo">
                {riesgoAlto ? 'Inviertes bajo tu propio riesgo' : 'Rendimiento no garantizado'}
              </span>
              <p>{producto.advertencia}</p>
            </div>
          )}

          {invertible && (
            <div className="accion-invertir">
              <label className="campo campo-inline">
                <span>Aumentar lo invertido</span>
                <input
                  id={`monto-${producto.id}`}
                  type="number"
                  min="0"
                  step="1000"
                  placeholder="0"
                  value={monto}
                  onChange={(e) => {
                    setMonto(e.target.value)
                    setConfirmado(false)
                  }}
                />
              </label>
              <button
                type="button"
                className={`boton ${riesgoAlto ? 'boton-riesgo' : 'boton-primario'}`}
                disabled={!monto || Number(monto) <= 0}
                onClick={() => setConfirmado(true)}
              >
                {riesgoAlto ? 'Acepto el riesgo e invertir' : 'Invertir'}
              </button>

              {confirmado && (
                <p className="confirmacion">
                  Simulación: {moneda(Number(monto))} a {porcentaje(producto.rendimiento_anual_esperado)} anual
                  generarían {moneda((Number(monto) * producto.rendimiento_anual_esperado) / 12)} al mes.
                  {riesgoAlto && ' Recuerda que este producto puede perder valor.'}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  )
}
