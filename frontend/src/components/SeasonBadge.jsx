const ETIQUETA = {
  alta: 'Temporada alta',
  regular: 'Temporada regular',
  baja: 'Temporada baja',
}

export function SeasonBadge({ temporada }) {
  return <span className={`pill ${temporada}`}>{ETIQUETA[temporada] ?? temporada}</span>
}
