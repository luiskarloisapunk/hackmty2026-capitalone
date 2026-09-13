import { useEffect, useState } from 'react'
import { obtenerClientes, obtenerCuentas } from '../api'

export function Cuentas() {
  const [clientes, setClientes] = useState([])
  const [clienteSeleccionado, setClienteSeleccionado] = useState(null)
  const [cuentas, setCuentas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    obtenerClientes()
      .then(setClientes)
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
  }, [])

  const verCuentas = async (cliente) => {
    setClienteSeleccionado(cliente)
    setCuentas([])
    try {
      const data = await obtenerCuentas(cliente._id)
      setCuentas(data)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <h2 className="subtitulo">Clientes</h2>

      {cargando && <p className="texto">Cargando...</p>}
      {error && <p className="texto error">{error}</p>}

      {!cargando && !error && (
        <ul className="lista">
          {clientes.map((cliente) => (
            <li key={cliente._id}>
              <button type="button" className="boton" onClick={() => verCuentas(cliente)}>
                {cliente.first_name} {cliente.last_name}
              </button>
            </li>
          ))}
        </ul>
      )}

      {clienteSeleccionado && (
        <div className="detalle">
          <h2 className="subtitulo">Cuentas de {clienteSeleccionado.first_name}</h2>
          {cuentas.length === 0 ? (
            <p className="texto">Sin cuentas registradas.</p>
          ) : (
            <ul className="lista">
              {cuentas.map((cuenta) => (
                <li key={cuenta._id} className="texto">
                  {cuenta.nickname || cuenta.type} — ${cuenta.balance}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
