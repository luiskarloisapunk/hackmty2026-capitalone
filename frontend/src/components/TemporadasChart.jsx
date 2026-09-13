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

const COLOR_TEMPORADA = {
  alta: '#D22E1E',
  regular: '#E29D12',
  baja: '#097167',
}

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

const NOMBRE_SERIE = {
  monto: 'Ingreso del mes',
  ingresoPromedioEsperado: 'Ingreso regularizado',
}

function formatoMoneda(valor) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    maximumFractionDigits: 0,
  }).format(valor)
}

export function TemporadasChart({ historial, ingresoPromedioEsperado }) {
  const datos = historial.map((mes) => ({
    ...mes,
    etiqueta: `${MESES[mes.mes - 1]} ${String(mes.anio).slice(2)}`,
    ingresoPromedioEsperado,
  }))

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Ingresos por temporada vs. ingreso regularizado</h3>
        <div className="chart-legend">
          <span className="legend-item">
            <i style={{ background: COLOR_TEMPORADA.alta }} /> Alta
          </span>
          <span className="legend-item">
            <i style={{ background: COLOR_TEMPORADA.regular }} /> Regular
          </span>
          <span className="legend-item">
            <i style={{ background: COLOR_TEMPORADA.baja }} /> Baja
          </span>
          <span className="legend-item">
            <i className="legend-linea" /> Ingreso regularizado
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={datos} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="etiqueta"
            tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatoMoneda}
            tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
            axisLine={false}
            tickLine={false}
            width={84}
          />
          <Tooltip
            formatter={(valor, nombre) => [formatoMoneda(valor), NOMBRE_SERIE[nombre] ?? nombre]}
          />
          <Bar dataKey="monto" radius={[4, 4, 0, 0]} maxBarSize={36}>
            {datos.map((mes) => (
              <Cell
                key={`${mes.anio}-${mes.mes}`}
                fill={COLOR_TEMPORADA[mes.temporada] ?? 'var(--color-neutral-300)'}
              />
            ))}
          </Bar>
          <Line
            type="monotone"
            dataKey="ingresoPromedioEsperado"
            stroke="var(--color-primary)"
            strokeWidth={2.5}
            strokeDasharray="6 4"
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
