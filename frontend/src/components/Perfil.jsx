import { useEffect, useState } from 'react'
import { obtenerPerfil, vincularNessie } from '../api'
import { etiquetaMes, moneda } from '../formato'

export function Perfil() {
  const [perfil, setPerfil] = useState(null)
  const [error, setError] = useState(null)
  const [abierta, setAbierta] = useState('negocio')
  const [vinculando, setVinculando] = useState(false)

  const cargar = () => {
    obtenerPerfil()
      .then(setPerfil)
      .catch((e) => setError(e.message))
  }

  useEffect(cargar, [])

  const alternar = (id) => setAbierta(abierta === id ? null : id)

  const darDeAlta = async () => {
    setError(null)
    setVinculando(true)
    try {
      await vincularNessie()
      cargar()
    } catch (e) {
      setError(e.message)
    } finally {
      setVinculando(false)
    }
  }

  if (error && !perfil) return <p className="mensaje-error">{error}</p>
  if (!perfil) return <p className="texto">Cargando perfil...</p>

  const { negocio, usuario, historial, nessie, saldos_calculados: saldos } = perfil

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div className="perfil-identidad">
          <span className="perfil-inicial">{negocio.nombre?.charAt(0)}</span>
          <div>
            <h2 className="seccion-titulo">{negocio.nombre}</h2>
            <p className="seccion-bajada">
              {negocio.giro} · {usuario.nombre} · {usuario.email}
            </p>
          </div>
        </div>
      </header>

      {error && <p className="mensaje-error">{error}</p>}

      <div className="acordeon">
        <Desplegable
          id="negocio"
          titulo="Giro y estacionalidad"
          resumen={negocio.plantilla_nombre ?? 'Sin plantilla'}
          abierta={abierta === 'negocio'}
          onAlternar={alternar}
        >
          <Fila etiqueta="Giro" valor={negocio.giro ?? 'No especificado'} />
          <Fila etiqueta="Plantilla de estacionalidad" valor={negocio.plantilla_nombre ?? '—'} />
          <Fila
            etiqueta="Picos de temporada al año"
            valor={negocio.picos_por_anio ? `${negocio.picos_por_anio}` : '—'}
          />
          <Fila
            etiqueta="Origen de los datos"
            valor={
              negocio.historial_es_sintetico
                ? 'Patrón típico del giro (aún sin historial propio)'
                : 'Historial propio del negocio'
            }
          />
        </Desplegable>

        <Desplegable
          id="historial"
          titulo="Historial financiero"
          resumen={`${historial.meses} meses`}
          abierta={abierta === 'historial'}
          onAlternar={alternar}
        >
          {historial.desde && (
            <Fila
              etiqueta="Periodo cubierto"
              valor={`${etiquetaMes(historial.desde.anio, historial.desde.mes)} – ${etiquetaMes(
                historial.hasta.anio,
                historial.hasta.mes
              )}`}
            />
          )}
          <Fila etiqueta="Ingreso acumulado" valor={moneda(historial.ingreso_total)} />
          <Fila etiqueta="Ingreso promedio mensual" valor={moneda(historial.ingreso_promedio)} />
          <Fila etiqueta="Mejor mes" valor={moneda(historial.ingreso_maximo)} />
          <Fila etiqueta="Peor mes" valor={moneda(historial.ingreso_minimo)} />
          <Fila
            etiqueta="Gastado en inventario"
            valor={moneda(historial.gasto_inventario_total)}
          />
        </Desplegable>

        <Desplegable
          id="nessie"
          titulo="Cuentas en Capital One Nessie"
          resumen={nessie.vinculado ? `${nessie.cuentas.length} cuentas` : 'Sin dar de alta'}
          abierta={abierta === 'nessie'}
          onAlternar={alternar}
        >
          {!nessie.vinculado && (
            <>
              <p className="tarjeta-descripcion">
                Tu negocio todavía no está dado de alta en Nessie. Al darlo de alta
                creamos tu cliente y tus tres cuentas allá, con los saldos que el
                motor ya calculó para ti.
              </p>
              <button
                type="button"
                className="boton boton-primario"
                onClick={darDeAlta}
                disabled={vinculando}
              >
                {vinculando ? 'Dando de alta...' : 'Dar de alta en Nessie'}
              </button>
            </>
          )}

          {nessie.vinculado && (
            <>
              <Fila etiqueta="ID de cliente en Nessie" valor={nessie.customer_id} mono />
              {nessie.error ? (
                <div className="aviso">
                  <span className="aviso-titulo">No se pudieron leer las cuentas</span>
                  <p>
                    {nessie.error}. Tu negocio sí está dado de alta; es la API la que
                    no está respondiendo ahorita.
                  </p>
                </div>
              ) : (
                nessie.cuentas.map((cuenta) => (
                  <Fila
                    key={cuenta.id}
                    etiqueta={`${cuenta.nombre} (${cuenta.tipo})`}
                    valor={moneda(cuenta.balance)}
                  />
                ))
              )}
            </>
          )}
        </Desplegable>

        {saldos && (
          <Desplegable
            id="saldos"
            titulo="Saldos que calculó el motor"
            resumen={moneda(
              saldos.saldo_operacion + saldos.saldo_acceso_rapido + saldos.saldo_plazo_fijo
            )}
            abierta={abierta === 'saldos'}
            onAlternar={alternar}
          >
            <Fila etiqueta="Operación" valor={moneda(saldos.saldo_operacion)} />
            <Fila etiqueta="Fondo regulador" valor={moneda(saldos.saldo_acceso_rapido)} />
            <Fila etiqueta="Inversión a plazo" valor={moneda(saldos.saldo_plazo_fijo)} />
            <Fila
              etiqueta="Rendimiento acumulado"
              valor={moneda(saldos.rendimiento_acumulado)}
            />
            <Fila
              etiqueta="Meses de temporada baja cubiertos"
              valor={`${saldos.meses_cubiertos}`}
            />
          </Desplegable>
        )}
      </div>
    </div>
  )
}

function Desplegable({ id, titulo, resumen, abierta, onAlternar, children }) {
  return (
    <article className={`tarjeta-cuenta ${abierta ? 'abierta' : ''}`}>
      <button
        type="button"
        className="tarjeta-cabecera"
        onClick={() => onAlternar(id)}
        aria-expanded={abierta}
      >
        <span className="tarjeta-identidad">
          <span className="tarjeta-nombre">{titulo}</span>
        </span>
        <span className="tarjeta-cifras">
          <span className="tarjeta-rendimiento">{resumen}</span>
        </span>
        <span className={`chevron ${abierta ? 'abierto' : ''}`} aria-hidden="true" />
      </button>

      {abierta && <div className="tarjeta-cuerpo tarjeta-cuerpo-perfil">{children}</div>}
    </article>
  )
}

function Fila({ etiqueta, valor, mono }) {
  return (
    <div className="dato-linea">
      <span>{etiqueta}</span>
      <strong className={mono ? 'valor-mono' : undefined}>{valor}</strong>
    </div>
  )
}
