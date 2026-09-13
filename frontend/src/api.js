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