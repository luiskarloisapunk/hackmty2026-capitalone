import { useState } from 'react'
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
import {
  COLOR_TEMPORADA,
  ETIQUETA_TEMPORADA,
  etiquetaMes,
  moneda,
  porcentaje,
} from '../formato'

const VENTANAS = [
  { id: 12, etiqueta: '12 meses' },
  { id: 24, etiqueta: '24 meses' },
  { id: 0, etiqueta: 'Todo' },
]

export function Inicio({ panorama }) {
  const [ventana, setVentana] = useState(12)

  const { temporadas, cuentas, regulacion, negocio } = panorama
  const base = temporadas.ingreso_promedio_esperado

  const regulacionPorMes = new Map(regulacion.map((m) => [`${m.anio}-${m.mes}`, m]))
  const completa = temporadas.historial_clasificado.map((mes) => ({
    ...mes,
    etiqueta: etiquetaMes(mes.anio, mes.mes),
    base,
    regularizado: regulacionPorMes.get(`${mes.anio}-${mes.mes}`)?.ingreso_regularizado ?? base,
  }))

  const serie = ventana === 0 ? completa : completa.slice(-ventana)
  const ultimo = temporadas.ultimo_mes
  const temporadaActual = temporadas.temporada_actual

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div className="negocio-identidad">
          <h2 className="seccion-titulo">{negocio.nombre}</h2>
          <p className="seccion-bajada">
            {negocio.giro} · último mes registrado {etiquetaMes(ultimo.anio, ultimo.mes)}
          </p>
        </div>
        <span className={`pastilla pastilla-${temporadaActual}`}>
          {ETIQUETA_TEMPORADA[temporadaActual]}
        </span>
      </header>

      <div className="tira-metricas">
        <Metrica etiqueta="Ingreso del último mes" valor={moneda(ultimo.monto)} />
        <Metrica etiqueta="Ingreso regularizado" valor={moneda(base)} destacada />
        <Metrica etiqueta="Fondo regulador" valor={moneda(cuentas.saldo_acceso_rapido)} />
        <Metrica etiqueta="Inversión a plazo" valor={moneda(cuentas.saldo_plazo_fijo)} />
      </div>

      <div className="panel-grafica">
        <div className="grafica-encabezado">
          <h3>De corriente alterna a corriente directa</h3>
          <div className="grafica-controles">
            <div className="leyenda">
              <span className="leyenda-item"><i className="muestra-punto" style={{ background: COLOR_TEMPORADA.alta }} /> Alta</span>
              <span className="leyenda-item"><i className="muestra-punto" style={{ background: COLOR_TEMPORADA.regular }} /> Regular</span>
              <span className="leyenda-item"><i className="muestra-punto" style={{ background: COLOR_TEMPORADA.baja }} /> Baja</span>
              <span className="leyenda-item"><i className="muestra-linea" /> Ingreso regularizado</span>
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
          </div>
        </div>

        <ResponsiveContainer width="100%" height={340}>
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
                nombre === 'monto' ? 'Ingreso real' : 'Ingreso regularizado',
              ]}
            />
            <Bar dataKey="monto" maxBarSize={32} radius={0} isAnimationActive={false}>
              {serie.map((mes) => (
                <Cell key={`${mes.anio}-${mes.mes}`} fill={COLOR_TEMPORADA[mes.temporada]} />
              ))}
            </Bar>
            <Line
              dataKey="regularizado"
              stroke="var(--color-primary)"
              strokeWidth={2.5}
              strokeDasharray="6 4"
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="panel-plano">
        <h3 className="panel-titulo">Qué hizo el motor con tu dinero</h3>
        <div className="dato-linea">
          <span>Rendimiento generado desde que empezaste</span>
          <strong className="cifra-positiva">{moneda(cuentas.rendimiento_acumulado)}</strong>
        </div>
        <div className="dato-linea">
          <span>Meses de temporada baja que tu reserva alcanzó a cubrir</span>
          <strong>{cuentas.meses_cubiertos}</strong>
        </div>
        <div className="dato-linea">
          <span>Tasa de referencia vigente</span>
          <strong>{porcentaje(panorama.tasa_referencia.tasa_anual)}</strong>
        </div>
      </div>
    </div>
  )
}

function Metrica({ etiqueta, valor, destacada }) {
  return (
    <div className={`metrica ${destacada ? 'metrica-destacada' : ''}`}>
      <span className="metrica-etiqueta">{etiqueta}</span>
      <span className="metrica-valor">{valor}</span>
    </div>
  )
}
