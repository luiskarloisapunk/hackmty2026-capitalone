const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function obtenerClientes() {
  const res = await fetch(`${API_URL}/api/customers/`)
  if (!res.ok) throw new Error('No se pudieron obtener los clientes')
  return res.json()
}

export async function obtenerCuentas(clienteId) {
  const res = await fetch(`${API_URL}/api/accounts/${clienteId}`)
  if (!res.ok) throw new Error('No se pudieron obtener las cuentas')
  return res.json()
}

async function postJSON(ruta, payload) {
  const res = await fetch(`${API_URL}${ruta}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null)
    throw new Error(cuerpo?.detail || `Error al llamar ${ruta}`)
  }
  return res.json()
}

export function analizarTemporadas(payload) {
  return postJSON('/api/temporadas/analizar', payload)
}

export function calcularReservaReinversion(payload) {
  return postJSON('/api/temporadas/reserva-reinversion', payload)
}