import { useState } from 'react'
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ReferenceLine,
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

// Cada métrica sabe qué parte de la gráfica explica: al seleccionarla, eso
// se queda encendido y el resto se apaga.
const FOCOS = {
  ultimo: { pista: 'La barra del mes más reciente' },
  regularizado: { pista: 'La línea que aplana tus temporadas' },
  reserva: { pista: 'Los meses que tu reserva alcanzó a cubrir' },
  inversion: { pista: 'Los meses cuyo excedente se fue a inversión' },
}

const OPACIDAD_APAGADA = 0.15

export function Inicio({ panorama }) {
  const [ventana, setVentana] = useState(12)
  const [foco, setFoco] = useState(null)

  const { temporadas, cuentas, regulacion, negocio } = panorama
  const base = temporadas.ingreso_promedio_esperado

  const regulacionPorMes = new Map(regulacion.map((m) => [`${m.anio}-${m.mes}`, m]))
  const completa = temporadas.historial_clasificado.map((mes) => {
    const movimiento = regulacionPorMes.get(`${mes.anio}-${mes.mes}`)
    return {
      ...mes,
      etiqueta: etiquetaMes(mes.anio, mes.mes),
      regularizado: movimiento?.ingreso_regularizado ?? base,
      aInversion: movimiento?.a_inversion ?? 0,
      desdeReserva: movimiento?.desde_reserva ?? 0,
    }
  })

  const serie = ventana === 0 ? completa : completa.slice(-ventana)
  const ultimo = temporadas.ultimo_mes
  const etiquetaUltimo = etiquetaMes(ultimo.anio, ultimo.mes)

  const alternarFoco = (id) => setFoco(foco === id ? null : id)

  const opacidadBarra = (mes) => {
    if (!foco) return 1
    if (foco === 'ultimo') return mes.etiqueta === etiquetaUltimo ? 1 : OPACIDAD_APAGADA
    if (foco === 'regularizado') return OPACIDAD_APAGADA
    if (foco === 'reserva') return mes.desdeReserva > 0 ? 1 : OPACIDAD_APAGADA
    if (foco === 'inversion') return mes.aInversion > 0 ? 1 : OPACIDAD_APAGADA
    return 1
  }

  const opacidadLinea = !foco || foco === 'regularizado' ? 1 : 0.2

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div className="negocio-identidad">
          <h2 className="seccion-titulo">{negocio.nombre}</h2>
          <p className="seccion-bajada">
            {negocio.giro} · último mes registrado {etiquetaUltimo}
          </p>
        </div>
        <span className={`pastilla pastilla-${temporadas.temporada_actual}`}>
          {ETIQUETA_TEMPORADA[temporadas.temporada_actual]}
        </span>
      </header>

      <div className="tira-metricas">
        <Metrica
          id="ultimo"
          etiqueta="Ingreso del último mes"
          valor={moneda(ultimo.monto)}
          activa={foco === 'ultimo'}
          onClick={alternarFoco}
        />
        <Metrica
          id="regularizado"
          etiqueta="Ingreso regularizado"
          valor={moneda(base)}
          activa={foco === 'regularizado'}
          onClick={alternarFoco}
        />
        <Metrica
          id="reserva"
          etiqueta="Fondo regulador"
          valor={moneda(cuentas.saldo_acceso_rapido)}
          activa={foco === 'reserva'}
          onClick={alternarFoco}
        />
        <Metrica
          id="inversion"
          etiqueta="Inversión a plazo"
          valor={moneda(cuentas.saldo_plazo_fijo)}
          activa={foco === 'inversion'}
          onClick={alternarFoco}
        />
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

        {foco && (
          <div className="barra-foco">
            <span className="barra-foco-texto">{FOCOS[foco].pista}</span>
            <button type="button" className="barra-foco-limpiar" onClick={() => setFoco(null)}>
              Ver todo
            </button>
          </div>
        )}

        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={serie} margin={{ top: 22, right: 16, left: 0, bottom: 0 }}>
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
              cursor={{ fill: 'var(--color-neutral-100)', fillOpacity: 0.55 }}
              formatter={(valor, nombre) => [
                moneda(valor),
                nombre === 'monto' ? 'Ingreso real' : 'Ingreso regularizado',
              ]}
            />

            {/* Marca dónde termina el historial: el mes en el que estás parado. */}
            <ReferenceLine
              x={etiquetaUltimo}
              stroke="var(--color-neutral-700)"
              strokeWidth={1}
              label={{
                value: 'Mes actual',
                position: 'top',
                fill: 'var(--color-neutral-700)',
                fontSize: 11,
                fontWeight: 600,
              }}
            />

            <Bar dataKey="monto" maxBarSize={32} radius={0} isAnimationActive={false}>
              {serie.map((mes) => {
                const esUltimo = mes.etiqueta === etiquetaUltimo
                return (
                  <Cell
                    key={`${mes.anio}-${mes.mes}`}
                    fill={COLOR_TEMPORADA[mes.temporada]}
                    fillOpacity={opacidadBarra(mes)}
                    stroke={esUltimo ? 'var(--color-neutral-900)' : undefined}
                    strokeWidth={esUltimo ? 1.5 : 0}
                  />
                )
              })}
            </Bar>

            <Line
              dataKey="regularizado"
              type="linear"
              stroke="var(--color-primary)"
              strokeWidth={foco === 'regularizado' ? 3.5 : 2.5}
              strokeOpacity={opacidadLinea}
              strokeLinecap="round"
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

function Metrica({ id, etiqueta, valor, activa, onClick }) {
  return (
    <button
      type="button"
      className={`metrica metrica-activable ${activa ? 'activa' : ''}`}
      onClick={() => onClick(id)}
      aria-pressed={activa}
    >
      <span className="metrica-etiqueta">{etiqueta}</span>
      <span className="metrica-valor">{valor}</span>
    </button>
  )
}
