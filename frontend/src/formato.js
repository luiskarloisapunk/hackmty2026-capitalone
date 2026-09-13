const MONEDA = new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: 'MXN',
  maximumFractionDigits: 0,
})

export const MESES = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
]

export function moneda(valor) {
  return MONEDA.format(valor ?? 0)
}

export function porcentaje(valor, decimales = 2) {
  return `${((valor ?? 0) * 100).toFixed(decimales)}%`
}

export function etiquetaMes(anio, mes) {
  return `${MESES[mes - 1]} ${String(anio).slice(2)}`
}

export const ETIQUETA_TEMPORADA = {
  alta: 'Temporada alta',
  regular: 'Temporada regular',
  baja: 'Temporada baja',
}

export const COLOR_TEMPORADA = {
  alta: '#D22E1E',
  regular: '#E29D12',
  baja: '#097167',
}
