import { useState } from 'react'
import { Cuentas } from './components/Cuentas'
import { Resumen } from './components/Resumen'
import { Sidebar } from './components/Sidebar'
import './App.css'

const TITULO_SECCION = {
  resumen: 'Resumen',
  cuentas: 'Clientes y cuentas',
}

function App() {
  const [seccion, setSeccion] = useState('resumen')

  return (
    <div className="shell">
      <Sidebar seccionActiva={seccion} onCambiarSeccion={setSeccion} />

      <div className="contenido">
        <header className="topbar">
          <h1 className="topbar-titulo">{TITULO_SECCION[seccion]}</h1>
        </header>

        <main className="pagina">
          {seccion === 'resumen' ? <Resumen /> : <Cuentas />}
        </main>
      </div>
    </div>
  )
}

export default App
