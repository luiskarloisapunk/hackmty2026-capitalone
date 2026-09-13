import { useEffect, useState } from 'react'
import { analizarTemporadas, calcularReservaReinversion } from '../api'
import { HISTORIAL_EJEMPLO, HISTORIAL_TEMPORADAS_ALTAS_EJEMPLO } from '../data/ejemploTemporadas'
import { SeasonBadge } from './SeasonBadge'
import { TemporadasChart } from './TemporadasChart'

function formatoMoneda(valor) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    maximumFractionDigits: 0,
  }).format(valor)
}

export function Resumen() {
  const [perfil, setPerfil] = useState(null)
  const [reserva, setReserva] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      analizarTemporadas({ historial: HISTORIAL_EJEMPLO }),
      calcularReservaReinversion({ historial_temporadas_altas: HISTORIAL_TEMPORADAS_ALTAS_EJEMPLO }),
    ])
      .then(([perfilRes, reservaRes]) => {
        setPerfil(perfilRes)
        setReserva(reservaRes)
      })
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
  }, [])

  if (cargando) return <p className="texto">Analizando temporadas...</p>
  if (error) return <p className="texto error">{error}</p>
  if (!perfil) return null

  const ultimoMes = perfil.historial_clasificado[perfil.historial_clasificado.length - 1]

  return (
    <div className="resumen">
      <p className="dato-ejemplo">
        Mostrando datos de ejemplo (Decoraciones del Norte, la PyME que siembra{' '}
        <code>seed_nessie.py</code>) mientras no hay una PyME real seleccionada.
      </p>

      <div className="pyme-card">
        <div>
          <div className="pyme-nombre">Decoraciones del Norte</div>
          <div className="pyme-sub">Último mes: {ultimoMes.anio}-{String(ultimoMes.mes).padStart(2, '0')}</div>
        </div>
        <SeasonBadge temporada={perfil.temporada_mes_mas_reciente} />
      </div>

      <div className="stat-row">
        <div className="stat">
          <span className="stat-label">Ingreso del último mes</span>
          <span className="stat-value">{formatoMoneda(ultimoMes.monto)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Ingreso regularizado</span>
          <span className="stat-value">{formatoMoneda(perfil.ingreso_promedio_esperado)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Reserva para próxima temporada alta</span>
          <span className="stat-value">{formatoMoneda(reserva.reserva_proyectada)}</span>
        </div>
      </div>

      <TemporadasChart
        historial={perfil.historial_clasificado}
        ingresoPromedioEsperado={perfil.ingreso_promedio_esperado}
      />
    </div>
  )
}
