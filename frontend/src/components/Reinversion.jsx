import { useEffect, useState } from 'react'
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { obtenerReinversion } from '../api'
import { COLOR_TEMPORADA, MESES, etiquetaMes, moneda, porcentaje } from '../formato'

const VENTANAS = [
  { id: 12, etiqueta: 'Último año' },
  { id: 24, etiqueta: 'Últimos 2 años' },
  { id: 0, etiqueta: 'Todo' },
]

export function Reinversion() {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [ventana, setVentana] = useState(12)

  useEffect(() => {
    obtenerReinversion()
      .then(setDatos)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="mensaje-error">{error}</p>
  if (!datos) return <p className="texto">Calculando plan de reinversión...</p>
  if (!datos.listo) return <p className="texto">{datos.motivo}</p>

  const serieCompleta = datos.serie_mensual
  const serie = (ventana === 0 ? serieCompleta : serieCompleta.slice(-ventana)).map((mes) => ({
    ...mes,
    etiqueta: etiquetaMes(mes.anio, mes.mes),
  }))

  const siguiente = datos.siguiente_mes
  const temporada = datos.siguiente_temporada_alta

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div>
          <h2 className="seccion-titulo">Reinversión en inventario e insumos</h2>
          <p className="seccion-bajada">
            Cuánto has invertido en inventario o insumos, cuánto toca el mes que entra y
            cuánto vas a necesitar para tu próxima temporada alta.
          </p>
        </div>
        <div className="selector-segmentado">
          {VENTANAS.map((opcion) => (
            <button
              key={opcion.id}
              type="button"
              className={`segmento ${ventana === opcion.id ? 'activo' : ''}`}
              onClick={() => setVentana(opcion.id)}
            >
              {opcion.etiqueta}
            </button>
          ))}
        </div>
      </header>

      <div className="pronostico-doble">
        <div className="pronostico">
          <span className="pronostico-periodo">
            Siguiente mes · {MESES[siguiente.mes - 1]} {siguiente.anio}
          </span>
          <span className="pronostico-etiqueta">Gasto en inventario o insumos estimado</span>
          <span className="pronostico-cifra">{moneda(siguiente.gasto_inventario_estimado)}</span>
          <span className="pronostico-detalle">
            Base histórica {moneda(siguiente.base_historica)} ajustada por crecimiento
            ×{siguiente.factor_crecimiento_aplicado.toFixed(2)}
          </span>
          <span className="pronostico-fuente">Calculado con el {siguiente.fuente}</span>
        </div>

        {temporada && (
          <div className="pronostico pronostico-destacado">
            <span className="pronostico-periodo">Próxima temporada alta</span>

            <div className="proyeccion">
              <div className="proyeccion-fila">
                <span>Ingreso que esperas recibir</span>
                <strong>{moneda(temporada.ingreso_proyectado)}</strong>
              </div>
              <div className="proyeccion-fila proyeccion-gasto">
                <span>Lo que te costará prepararla</span>
                <strong>− {moneda(temporada.gasto_inventario_proyectado)}</strong>
              </div>
              <div className="proyeccion-fila proyeccion-total">
                <span>Te queda</span>
                <strong>{moneda(temporada.margen_esperado)}</strong>
              </div>
            </div>

            <span className="pronostico-detalle">
              Inventario e insumos se llevan {porcentaje(temporada.ratio_historico_gasto_ingreso, 1)} de tu
              ingreso de temporada alta. Eso es lo que hay que tener apartado antes de que empiece.
            </span>
            <span className="pronostico-fuente">
              Proyectado desde {moneda(temporada.ingreso_temporada_anterior)} de la temporada
              anterior, sobre {temporada.ciclos_considerados}{' '}
              {temporada.ciclos_considerados === 1 ? 'ciclo completo' : 'ciclos completos'}
              {temporada.crecimiento_interanual !== null &&
                ` · crecimiento ${porcentaje(temporada.crecimiento_interanual, 1)}${
                  temporada.crecimiento_fue_estimado ? ' (estimado)' : ''
                }`}
            </span>
          </div>
        )}
      </div>

      <div className="panel-grafica">
        <div className="grafica-encabezado">
          <h3>Gasto en inventario o insumos contra ingreso del mes</h3>
          <div className="leyenda">
            <span className="leyenda-item"><i className="muestra-punto" style={{ background: COLOR_TEMPORADA.alta }} /> Alta</span>
            <span className="leyenda-item"><i className="muestra-punto" style={{ background: COLOR_TEMPORADA.regular }} /> Regular</span>
            <span className="leyenda-item"><i className="muestra-punto" style={{ background: COLOR_TEMPORADA.baja }} /> Baja</span>
            <span className="leyenda-item"><i className="muestra-linea" /> Ingreso</span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={serie} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="etiqueta"
              tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              interval={serie.length > 18 ? 2 : 0}
            />
            <YAxis
              tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
              tickFormatter={moneda}
              tickLine={false}
              axisLine={false}
              width={90}
            />
            <Tooltip
              formatter={(valor, nombre) => [
                moneda(valor),
                nombre === 'gasto_inventario' ? 'Inventario o insumos' : 'Ingreso',
              ]}
            />
            <Bar dataKey="gasto_inventario" maxBarSize={30} radius={0} isAnimationActive={false}>
              {serie.map((mes) => (
                <Cell key={`${mes.anio}-${mes.mes}`} fill={COLOR_TEMPORADA[mes.temporada]} />
              ))}
            </Bar>
            <Line
              dataKey="ingreso"
              stroke="var(--color-primary)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
