import { useCallback, useEffect, useState } from 'react'
import { borrarToken, guardarToken, leerToken, obtenerPanorama } from './api'
import { Acceso } from './components/Acceso'
import { Cuentas } from './components/Cuentas'
import { Historial } from './components/Historial'
import { Inicio } from './components/Inicio'
import { Liquidez } from './components/Liquidez'
import { PanelDev } from './components/PanelDev'
import { Reinversion } from './components/Reinversion'
import { Sidebar } from './components/Sidebar'
import './App.css'

const TITULO_SECCION = {
  inicio: 'Inicio',
  cuentas: 'Cuentas',
  liquidez: 'Liquidez',
  reinversion: 'Reinversión',
  historial: 'Mi historial',
}

function App() {
  // Si quedó un token de una visita anterior, la sesión arranca viva.
  const [sesion, setSesion] = useState(() => (leerToken() ? { usuario: null } : null))
  const [seccion, setSeccion] = useState('inicio')
  const [panorama, setPanorama] = useState(null)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)

  const cargarPanorama = useCallback(() => {
    setCargando(true)
    setError(null)
    obtenerPanorama()
      .then(setPanorama)
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
  }, [])

  useEffect(() => {
    if (sesion && !panorama) cargarPanorama()
    // Solo al montar: los cambios de sesión posteriores ya recargan solos.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const autenticar = (datosSesion, opciones = {}) => {
    guardarToken(datosSesion.access_token)
    setSesion(datosSesion)
    setPanorama(null)
    setSeccion(opciones.pedirCsv ? 'historial' : 'inicio')
    cargarPanorama()
  }

  const salir = () => {
    borrarToken()
    setSesion(null)
    setPanorama(null)
    setError(null)
  }

  if (!sesion) {
    return (
      <>
        <Acceso onAutenticado={autenticar} />
        <PanelDev onAutenticado={autenticar} onSalir={salir} emailActual={null} />
      </>
    )
  }

  return (
    <div className="shell">
      <Sidebar
        seccionActiva={seccion}
        onCambiarSeccion={setSeccion}
        negocio={panorama?.negocio}
        onSalir={salir}
      />

      <div className="contenido">
        <header className="topbar">
          <h1 className="topbar-titulo">{TITULO_SECCION[seccion]}</h1>
        </header>

        <main className="pagina">
          {error && <p className="mensaje-error">{error}</p>}
          {cargando && !panorama && <p className="texto">Cargando tu negocio...</p>}

          {panorama?.listo === false && (
            <div className="aviso">
              <span className="aviso-titulo">Falta historial</span>
              <p>{panorama.motivo}</p>
            </div>
          )}

          {panorama?.listo && (
            <>
              {seccion === 'inicio' && <Inicio panorama={panorama} />}
              {seccion === 'cuentas' && <Cuentas panorama={panorama} />}
              {seccion === 'liquidez' && <Liquidez />}
              {seccion === 'reinversion' && <Reinversion />}
            </>
          )}

          {seccion === 'historial' && (
            <Historial panorama={panorama} onHistorialActualizado={cargarPanorama} />
          )}
        </main>
      </div>

      <PanelDev
        onAutenticado={autenticar}
        onSalir={salir}
        emailActual={sesion?.usuario?.email ?? null}
      />
    </div>
  )
}

export default App
