import { useRef, useState } from 'react'
import { subirHistorialCsv, urlPlantillaCsv } from '../api'
import { etiquetaMes, moneda } from '../formato'

export function Historial({ panorama, onHistorialActualizado }) {
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState(null)
  const [subiendo, setSubiendo] = useState(false)
  const inputArchivo = useRef(null)

  const sintetico = panorama?.negocio?.historial_es_sintetico

  const alSeleccionar = async (evento) => {
    const archivo = evento.target.files?.[0]
    if (!archivo) return

    setError(null)
    setSubiendo(true)
    try {
      const respuesta = await subirHistorialCsv(archivo)
      setResultado(respuesta)
      onHistorialActualizado()
    } catch (e) {
      setError(e.message)
    } finally {
      setSubiendo(false)
      if (inputArchivo.current) inputArchivo.current.value = ''
    }
  }

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div>
          <h2 className="seccion-titulo">Mi historial financiero</h2>
          <p className="seccion-bajada">
            Todo lo que ves en la app sale de aquí: las temporadas, las cuentas,
            la liquidez y el plan de inventario.
          </p>
        </div>
      </header>

      {sintetico && (
        <div className="aviso">
          <span className="aviso-titulo">Estás viendo datos del patrón de tu giro</span>
          <p>
            Todavía no subes tu historial real, así que arrancamos con el
            comportamiento típico de negocios como el tuyo. En cuanto subas tu
            CSV, todos los cálculos se rehacen con tus números.
          </p>
        </div>
      )}

      <div className="pasos">
        <article className="paso">
          <span className="paso-numero">1</span>
          <div className="paso-contenido">
            <h3>Descarga la plantilla</h3>
            <p>
              Un CSV con las columnas que necesitamos: <code>fecha</code> (AAAA-MM),{' '}
              <code>ingreso</code> y <code>gasto_inventario</code>. Trae dos filas de
              ejemplo para que veas el formato.
            </p>
            <a className="boton boton-secundario" href={urlPlantillaCsv()} download>
              Descargar plantilla CSV
            </a>
          </div>
        </article>

        <article className="paso">
          <span className="paso-numero">2</span>
          <div className="paso-contenido">
            <h3>Llénala con tus meses</h3>
            <p>
              Una fila por mes, mínimo 3 meses. Entre más historial tengas, mejor
              detectamos tus temporadas: con 24 meses o más ya podemos comparar
              año contra año.
            </p>
          </div>
        </article>

        <article className="paso">
          <span className="paso-numero">3</span>
          <div className="paso-contenido">
            <h3>Súbela</h3>
            <p>Reemplaza el historial actual y recalcula todo al instante.</p>
            <input
              id="csv-historial"
              ref={inputArchivo}
              type="file"
              accept=".csv,text/csv"
              onChange={alSeleccionar}
              className="input-archivo"
            />
            <label htmlFor="csv-historial" className="boton boton-primario">
              {subiendo ? 'Procesando...' : 'Elegir archivo CSV'}
            </label>
          </div>
        </article>
      </div>

      {error && (
        <div className="aviso aviso-fuerte">
          <span className="aviso-titulo">No se pudo cargar el archivo</span>
          <p>{error}</p>
        </div>
      )}

      {resultado && (
        <div className="panel-plano">
          <h3 className="panel-titulo">Historial actualizado</h3>
          <div className="dato-linea">
            <span>Meses cargados</span>
            <strong>{resultado.meses_cargados}</strong>
          </div>
          <div className="dato-linea">
            <span>Periodo</span>
            <strong>
              {etiquetaMes(resultado.desde.anio, resultado.desde.mes)} –{' '}
              {etiquetaMes(resultado.hasta.anio, resultado.hasta.mes)}
            </strong>
          </div>
          <div className="dato-linea">
            <span>Primer ingreso registrado</span>
            <strong>{moneda(resultado.desde.ingreso)}</strong>
          </div>
        </div>
      )}
    </div>
  )
}
