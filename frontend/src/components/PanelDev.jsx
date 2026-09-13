import { useState } from 'react'
import { iniciarSesion } from '../api'

const CUENTAS = [
  { email: 'navidena@demo.com', etiqueta: 'Decoraciones del Norte', nota: 'pico Nov–Dic' },
  { email: 'heladeria@demo.com', etiqueta: 'Nieves del Valle', nota: 'pico Jun–Ago' },
  { email: 'papeleria@demo.com', etiqueta: 'Papelería Monterrey', nota: 'picos Feb y Ago' },
  { email: 'agro@demo.com', etiqueta: 'Agrícola Treviño', nota: 'cosecha Sep–Ene' },
]

/**
 * Atajo interno del equipo: cambiar de cuenta de demo sin pasar por el login.
 * No es parte del producto -- es para no perder tiempo en las pruebas.
 */
export function PanelDev({ onAutenticado, onSalir, emailActual }) {
  const [abierto, setAbierto] = useState(false)
  const [ocupado, setOcupado] = useState(null)

  const entrarComo = async (email) => {
    setOcupado(email)
    try {
      const sesion = await iniciarSesion(email, 'password')
      onAutenticado(sesion)
      setAbierto(false)
    } finally {
      setOcupado(null)
    }
  }

  return (
    <div className="dev">
      {abierto && (
        <div className="dev-panel">
          <span className="dev-titulo">Cambiar de cuenta</span>
          {CUENTAS.map((cuenta) => (
            <button
              key={cuenta.email}
              type="button"
              className={`dev-cuenta ${cuenta.email === emailActual ? 'activa' : ''}`}
              onClick={() => entrarComo(cuenta.email)}
              disabled={ocupado !== null}
            >
              <span className="dev-cuenta-nombre">{cuenta.etiqueta}</span>
              <span className="dev-cuenta-nota">{cuenta.nota}</span>
            </button>
          ))}
          <button type="button" className="dev-cuenta dev-salir" onClick={onSalir}>
            <span className="dev-cuenta-nombre">Volver al inicio</span>
            <span className="dev-cuenta-nota">cerrar sesión y ver el login</span>
          </button>
        </div>
      )}

      <button
        type="button"
        className={`dev-boton ${abierto ? 'abierto' : ''}`}
        onClick={() => setAbierto(!abierto)}
        title="Panel de desarrollo"
      >
        DEV
      </button>
    </div>
  )
}
