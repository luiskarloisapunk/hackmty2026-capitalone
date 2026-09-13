import { useEffect, useState } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { obtenerLiquidez } from '../api'
import { moneda, porcentaje } from '../formato'

const HORIZONTES = [30, 60, 90]

export function Liquidez() {
  const [horizonte, setHorizonte] = useState(90)
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    setCargando(true)
    obtenerLiquidez(horizonte)
      .then(setDatos)
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
  }, [horizonte])

  if (cargando) return <p className="texto">Simulando escenarios de caja...</p>
  if (error) return <p className="mensaje-error">{error}</p>
  if (!datos?.listo) return <p className="texto">{datos?.motivo}</p>

  const serie = datos.proyeccion.map((punto) => ({
    ...punto,
    rango: [punto.pesimista, punto.optimista],
  }))

  const hayRiesgo = datos.saldo_minimo_pesimista < 0

  return (
    <div className="seccion">
      <header className="seccion-encabezado">
        <div>
          <h2 className="seccion-titulo">Predicción de liquidez</h2>
          <p className="seccion-bajada">
            600 escenarios simulados sobre tu historial real. La banda muestra
            el rango entre el peor y el mejor 10%, no una promesa.
          </p>
        </div>
        <div className="selector-segmentado">
          {HORIZONTES.map((dias) => (
            <button
              key={dias}
              type="button"
              className={`segmento ${horizonte === dias ? 'activo' : ''}`}
              onClick={() => setHorizonte(dias)}
            >
              {dias} días
            </button>
          ))}
        </div>
      </header>

      {hayRiesgo && (
        <div className="aviso aviso-fuerte">
          <span className="aviso-titulo">Riesgo de quedarte sin caja</span>
          <p>
            En el escenario pesimista tu saldo baja hasta{' '}
            <strong>{moneda(datos.saldo_minimo_pesimista)}</strong> alrededor del día{' '}
            {datos.dia_mas_critico}. Probabilidad de que ocurra:{' '}
            <strong>{porcentaje(datos.probabilidad_deficit, 1)}</strong>.
          </p>
        </div>
      )}

      <div className="tira-metricas">
        <Metrica etiqueta="Saldo inicial" valor={moneda(datos.saldo_inicial)} />
        <Metrica etiqueta="Escenario esperado (mínimo)" valor={moneda(datos.saldo_minimo_esperado)} />
        <Metrica
          etiqueta="Escenario pesimista (mínimo)"
          valor={moneda(datos.saldo_minimo_pesimista)}
          alerta={hayRiesgo}
        />
        <Metrica etiqueta="Probabilidad de déficit" valor={porcentaje(datos.probabilidad_deficit, 1)} />
      </div>

      <div className="panel-grafica">
        <div className="grafica-encabezado">
          <h3>Saldo proyectado de la cuenta de operación</h3>
          <div className="leyenda">
            <span className="leyenda-item"><i className="muestra-banda" /> Rango pesimista–optimista</span>
            <span className="leyenda-item"><i className="muestra-linea" /> Escenario esperado</span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={serie} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="dia"
              tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              tickFormatter={(dia) => `d${dia}`}
              interval={Math.floor(serie.length / 8)}
            />
            <YAxis
              tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
              tickFormatter={moneda}
              tickLine={false}
              axisLine={false}
              width={90}
            />
            <Tooltip
              formatter={(valor, nombre) => {
                if (nombre === 'rango') return null
                return [moneda(valor), 'Escenario esperado']
              }}
              labelFormatter={(dia) => `Día ${dia}`}
            />
            <ReferenceLine y={0} stroke="var(--color-accent)" strokeWidth={1.5} />
            <Area
              dataKey="rango"
              stroke="none"
              fill="var(--color-primary)"
              fillOpacity={0.14}
              isAnimationActive={false}
            />
            <Line
              dataKey="esperado"
              stroke="var(--color-primary)"
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {datos.recomendacion_capital && (
        <div className="panel-plano">
          <h3 className="panel-titulo">Colchón de capital recomendado</h3>
          <p className="panel-nota">
            Cuánto necesitas apartar hoy, a {porcentaje(datos.tasa_anual_usada)} anual, para
            cubrir ese hueco cuando llegue.
          </p>
          <div className="dato-linea">
            <span>Capital a apartar hoy</span>
            <strong>{moneda(datos.recomendacion_capital.required_principal)}</strong>
          </div>
          <div className="dato-linea">
            <span>Tu saldo disponible</span>
            <strong>{moneda(datos.recomendacion_capital.surplus)}</strong>
          </div>
          <div className="dato-linea">
            <span>{datos.recomendacion_capital.gap > 0 ? 'Te falta' : 'Te sobra'}</span>
            <strong className={datos.recomendacion_capital.gap > 0 ? 'cifra-alerta' : 'cifra-positiva'}>
              {moneda(
                datos.recomendacion_capital.gap > 0
                  ? datos.recomendacion_capital.gap
                  : datos.recomendacion_capital.free_cushion
              )}
            </strong>
          </div>
        </div>
      )}

      <p className="pie-tecnico">
        Modelo autorregresivo AR(14) ajustado por mínimos cuadrados (SVD) ·
        R² en muestra {datos.r2_en_muestra} · volatilidad diaria{' '}
        {moneda(datos.volatilidad_diaria)} · 600 trayectorias con bootstrap de residuos
      </p>
    </div>
  )
}

function Metrica({ etiqueta, valor, alerta }) {
  return (
    <div className={`metrica ${alerta ? 'metrica-alerta' : ''}`}>
      <span className="metrica-etiqueta">{etiqueta}</span>
      <span className="metrica-valor">{valor}</span>
    </div>
  )
}
