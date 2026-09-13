import { useEffect, useState } from 'react'
import { iniciarSesion, obtenerPlantillas, registrar } from '../api'
import { Logo } from './Logo'

const CUENTAS_DEMO = [
  { email: 'navidena@demo.com', negocio: 'Decoraciones del Norte', giro: 'Retail navideño' },
  { email: 'heladeria@demo.com', negocio: 'Nieves del Valle', giro: 'Heladería' },
  { email: 'papeleria@demo.com', negocio: 'Papelería Monterrey', giro: 'Papelería escolar' },
]

export function Acceso({ onAutenticado }) {
  const [modo, setModo] = useState('login')

  return (
    <div className="acceso">
      <section className="acceso-marca">
        <div className="acceso-marca-contenido">
          <div className="marca marca-grande">
            <Logo size={52} />
            <span className="marca-nombre">AC/DC Cash Flow</span>
          </div>
          <h1 className="acceso-titulo">
            Tu negocio es estacional.<br />Tu ingreso no tiene por qué serlo.
          </h1>
          <p className="acceso-bajada">
            Regularizamos el ingreso de tu temporada alta para que la baja no te
            agarre sin caja, e invertimos el excedente mientras esperas tu
            próxima reinversión de inventario.
          </p>
          <ul className="acceso-puntos">
            <li><span className="punto" /> Predicción de liquidez a 90 días</li>
            <li><span className="punto" /> Rendimiento anclado a Cetes de Banxico</li>
            <li><span className="punto" /> Reserva de inventario que crece contigo</li>
          </ul>
        </div>
      </section>

      <section className="acceso-formulario">
        <div className="acceso-caja">
          <div className="acceso-tabs">
            <button
              type="button"
              className={`acceso-tab ${modo === 'login' ? 'activo' : ''}`}
              onClick={() => setModo('login')}
            >
              Iniciar sesión
            </button>
            <button
              type="button"
              className={`acceso-tab ${modo === 'registro' ? 'activo' : ''}`}
              onClick={() => setModo('registro')}
            >
              Registrar mi negocio
            </button>
          </div>

          {modo === 'login' ? (
            <FormularioLogin onAutenticado={onAutenticado} />
          ) : (
            <FormularioRegistro onAutenticado={onAutenticado} />
          )}
        </div>
      </section>
    </div>
  )
}

function FormularioLogin({ onAutenticado }) {
  const [email, setEmail] = useState('navidena@demo.com')
  const [password, setPassword] = useState('password')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const enviar = async (evento) => {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      const sesion = await iniciarSesion(email, password)
      onAutenticado(sesion)
    } catch (e) {
      setError(e.message)
      setEnviando(false)
    }
  }

  return (
    <form className="formulario" onSubmit={enviar}>
      <label className="campo">
        <span>Correo</span>
        <input
          id="login-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>

      <label className="campo">
        <span>Contraseña</span>
        <input
          id="login-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>

      {error && <p className="mensaje-error">{error}</p>}

      <button className="boton boton-primario" type="submit" disabled={enviando}>
        {enviando ? 'Entrando...' : 'Entrar'}
      </button>

      <div className="demo-lista">
        <span className="demo-titulo">Cuentas de prueba · contraseña <code>password</code></span>
        {CUENTAS_DEMO.map((cuenta) => (
          <button
            key={cuenta.email}
            type="button"
            className="demo-fila"
            onClick={() => {
              setEmail(cuenta.email)
              setPassword('password')
            }}
          >
            <span className="demo-negocio">{cuenta.negocio}</span>
            <span className="demo-giro">{cuenta.giro}</span>
          </button>
        ))}
      </div>
    </form>
  )
}

function FormularioRegistro({ onAutenticado }) {
  const [datos, setDatos] = useState({
    nombre: '',
    nombre_negocio: '',
    email: '',
    password: '',
  })
  const [tieneHistorial, setTieneHistorial] = useState(null)
  const [plantillaId, setPlantillaId] = useState('')
  const [plantillas, setPlantillas] = useState([])
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    obtenerPlantillas().then(setPlantillas).catch(() => setPlantillas([]))
  }, [])

  const actualizar = (campo) => (evento) =>
    setDatos((previo) => ({ ...previo, [campo]: evento.target.value }))

  const enviar = async (evento) => {
    evento.preventDefault()
    setError(null)

    if (tieneHistorial === null) {
      setError('Dinos si ya llevas registro de tus finanzas.')
      return
    }
    if (tieneHistorial === false && !plantillaId) {
      setError('Elige el giro que más se parezca a tu negocio.')
      return
    }

    setEnviando(true)
    try {
      const sesion = await registrar({
        ...datos,
        tiene_historial: tieneHistorial,
        plantilla_id: tieneHistorial ? null : plantillaId,
      })
      onAutenticado(sesion, { pedirCsv: tieneHistorial })
    } catch (e) {
      setError(e.message)
      setEnviando(false)
    }
  }

  return (
    <form className="formulario" onSubmit={enviar}>
      <label className="campo">
        <span>Tu nombre</span>
        <input id="reg-nombre" value={datos.nombre} onChange={actualizar('nombre')} required />
      </label>

      <label className="campo">
        <span>Nombre del negocio</span>
        <input
          id="reg-negocio"
          value={datos.nombre_negocio}
          onChange={actualizar('nombre_negocio')}
          required
        />
      </label>

      <label className="campo">
        <span>Correo</span>
        <input id="reg-email" type="email" value={datos.email} onChange={actualizar('email')} required />
      </label>

      <label className="campo">
        <span>Contraseña <small>(mínimo 8 caracteres)</small></span>
        <input
          id="reg-password"
          type="password"
          minLength={8}
          value={datos.password}
          onChange={actualizar('password')}
          required
        />
      </label>

      <fieldset className="grupo">
        <legend>¿Ya llevas registro de tus finanzas?</legend>
        <div className="opciones">
          <button
            type="button"
            className={`opcion ${tieneHistorial === true ? 'activo' : ''}`}
            onClick={() => setTieneHistorial(true)}
          >
            Sí, tengo mi historial
          </button>
          <button
            type="button"
            className={`opcion ${tieneHistorial === false ? 'activo' : ''}`}
            onClick={() => setTieneHistorial(false)}
          >
            Todavía no
          </button>
        </div>
      </fieldset>

      {tieneHistorial === true && (
        <p className="nota-inline">
          Al entrar te damos la plantilla de CSV para que la llenes y la subas.
        </p>
      )}

      {tieneHistorial === false && (
        <label className="campo">
          <span>¿Qué giro se parece más a tu negocio?</span>
          <select
            id="reg-plantilla"
            value={plantillaId}
            onChange={(e) => setPlantillaId(e.target.value)}
          >
            <option value="">Elige un giro...</option>
            {plantillas.map((plantilla) => (
              <option key={plantilla.id} value={plantilla.id}>
                {plantilla.nombre}
              </option>
            ))}
          </select>
          <small className="ayuda">
            Arrancamos con el patrón típico de ese giro y lo vamos ajustando
            conforme acumules datos reales.
          </small>
        </label>
      )}

      {error && <p className="mensaje-error">{error}</p>}

      <button className="boton boton-primario" type="submit" disabled={enviando}>
        {enviando ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>
    </form>
  )
}
