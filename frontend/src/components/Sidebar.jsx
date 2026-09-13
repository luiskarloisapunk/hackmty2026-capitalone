import capitalOneLogo from '../assets/Capital_One_logo.svg'
import { Logo } from './Logo'

const SECCIONES = [
  { id: 'resumen', label: 'Resumen' },
  { id: 'cuentas', label: 'Clientes y cuentas' },
]

export function Sidebar({ seccionActiva, onCambiarSeccion }) {
  return (
    <aside className="sidebar">
      <div className="marca">
        <Logo size={32} />
        <span className="marca-nombre">AC/DC Cash Flow</span>
      </div>

      <nav className="nav">
        {SECCIONES.map((seccion) => (
          <button
            key={seccion.id}
            type="button"
            className={`nav-item ${seccion.id === seccionActiva ? 'activo' : ''}`}
            onClick={() => onCambiarSeccion(seccion.id)}
          >
            {seccion.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-badge">
          <span className="sidebar-footer-label">Built for the</span>
          <img src={capitalOneLogo} alt="Capital One" className="sidebar-footer-logo" />
        </div>
        <span>HackMTY 2026</span>
      </div>
    </aside>
  )
}
