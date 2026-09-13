import capitalOneLogo from '../assets/Capital_One_logo.svg'
import { Logo } from './Logo'

const SECCIONES = [
  { id: 'inicio', label: 'Inicio' },
  { id: 'cuentas', label: 'Cuentas' },
  { id: 'liquidez', label: 'Liquidez' },
  { id: 'reinversion', label: 'Reinversión' },
  { id: 'historial', label: 'Mi historial' },
]

export function Sidebar({ seccionActiva, onCambiarSeccion, negocio, onSalir }) {
  return (
    <aside className="sidebar">
      <div className="marca">
        <Logo size={32} />
        <span className="marca-nombre">AC/DC Cash Flow</span>
      </div>

      {negocio && (
        <button
          type="button"
          className={`sidebar-negocio ${seccionActiva === 'perfil' ? 'activo' : ''}`}
          onClick={() => onCambiarSeccion('perfil')}
          title="Ver el perfil del negocio"
        >
          <span className="sidebar-negocio-inicial">{negocio.nombre?.charAt(0)}</span>
          <span className="sidebar-negocio-datos">
            <span className="sidebar-negocio-nombre">{negocio.nombre}</span>
            <span className="sidebar-negocio-giro">{negocio.giro}</span>
          </span>
        </button>
      )}

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
        <button type="button" className="nav-item nav-salir" onClick={onSalir}>
          Cerrar sesión
        </button>
        <div className="sidebar-footer-badge">
          <span className="sidebar-footer-label">Built for the</span>
          <img src={capitalOneLogo} alt="Capital One" className="sidebar-footer-logo" />
        </div>
      </div>
    </aside>
  )
}
