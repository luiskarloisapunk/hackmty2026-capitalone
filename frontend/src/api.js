// En el build de producción el frontend lo sirve nginx, que proxea /api al
// backend en el mismo origen: por eso la base va vacía y las rutas quedan
// relativas. En desarrollo Vite corre aparte del backend, así que apunta a
// su puerto. VITE_API_URL permite forzar otra cosa si hiciera falta.
//
// Ojo con el `??`: la base vacía es un valor válido, y con `||` se caía al
// default y las peticiones salían a /api/api/... (404).
const API_URL =
  import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:8000')

const CLAVE_TOKEN = 'acdc_token'

export function guardarToken(token) {
  localStorage.setItem(CLAVE_TOKEN, token)
}

export function leerToken() {
  return localStorage.getItem(CLAVE_TOKEN)
}

export function borrarToken() {
  localStorage.removeItem(CLAVE_TOKEN)
}

async function pedir(ruta, { metodo = 'GET', cuerpo, conToken = true } = {}) {
  const headers = {}
  if (cuerpo !== undefined) headers['Content-Type'] = 'application/json'
  if (conToken) {
    const token = leerToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}${ruta}`, {
    method: metodo,
    headers,
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  })

  if (!res.ok) {
    const detalle = await res.json().catch(() => null)
    const mensaje = detalle?.detail
    throw new Error(typeof mensaje === 'string' ? mensaje : `Error ${res.status} en ${ruta}`)
  }

  return res.json()
}

// --- Sesión ---

export function iniciarSesion(email, password) {
  return pedir('/api/auth/login', { metodo: 'POST', cuerpo: { email, password }, conToken: false })
}

export function registrar(datos) {
  return pedir('/api/auth/registro', { metodo: 'POST', cuerpo: datos, conToken: false })
}

export function usuarioActual() {
  return pedir('/api/auth/me')
}

// --- Negocio ---

export function obtenerPlantillas() {
  return pedir('/api/negocios/plantillas', { conToken: false })
}

export function obtenerPanorama() {
  return pedir('/api/negocios/mio/panorama')
}

export function obtenerPerfil() {
  return pedir('/api/negocios/mio/perfil')
}

export function vincularNessie() {
  return pedir('/api/negocios/mio/nessie/vincular', { metodo: 'POST', cuerpo: {} })
}

export function obtenerReinversion() {
  return pedir('/api/negocios/mio/reinversion')
}

export function obtenerLiquidez(horizonteDias = 90) {
  return pedir('/api/negocios/mio/liquidez', {
    metodo: 'POST',
    cuerpo: { horizonte_dias: horizonteDias },
  })
}

export function urlPlantillaCsv() {
  return `${API_URL}/api/negocios/plantilla-csv`
}

export async function subirHistorialCsv(archivo) {
  const datos = new FormData()
  datos.append('archivo', archivo)

  const res = await fetch(`${API_URL}/api/negocios/mio/historial-csv`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${leerToken()}` },
    body: datos,
  })

  if (!res.ok) {
    const detalle = await res.json().catch(() => null)
    throw new Error(detalle?.detail || 'No se pudo procesar el CSV')
  }
  return res.json()
}
