import { useEffect, useState, type FormEvent } from 'react'
import { AdminApiError, getSession, login, logout, type AdminSession } from './api'

type Notice = { kind: 'error' | 'info'; text: string } | null

const roleNames: Record<AdminSession['role'], string> = {
  viewer: 'Consulta',
  editor: 'Edición',
  owner: 'Propietario',
}

function errorStatus(error: unknown): number | null {
  return error instanceof AdminApiError ? error.status : null
}

function loginError(error: unknown): string {
  switch (errorStatus(error)) {
    case 401:
      return 'Usuario o contraseña incorrectos.'
    case 429:
      return 'Demasiados intentos. Espera unos minutos antes de volver a intentar.'
    case 403:
      return 'El inicio de sesión requiere una conexión HTTPS segura.'
    case 503:
      return 'El servicio no está disponible por ahora. Inténtalo más tarde.'
    default:
      return 'No se pudo conectar con el servidor. Revisa la conexión e inténtalo de nuevo.'
  }
}

export function App() {
  const secureConnection = window.location.protocol === 'https:'
  const [session, setSession] = useState<AdminSession | null>(null)
  const [checking, setChecking] = useState(true)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<Notice>(null)

  async function refreshSession() {
    setChecking(true)
    try {
      const current = await getSession()
      setSession(current)
      setNotice(null)
    } catch (error) {
      setSession(null)
      if (errorStatus(error) !== 401) {
        setNotice({
          kind: 'error',
          text: 'No se pudo verificar la sesión. Puedes volver a intentar o iniciar sesión.',
        })
      }
    } finally {
      setChecking(false)
    }
  }

  useEffect(() => {
    if (!secureConnection) {
      setNotice({
        kind: 'info',
        text: 'Para iniciar sesión, abre el panel mediante una conexión HTTPS segura.',
      })
      setChecking(false)
      return
    }
    void refreshSession()
  }, [secureConnection])

  useEffect(() => {
    if (!session) return
    const remaining = Date.parse(session.expires_at) - Date.now()
    if (!Number.isFinite(remaining) || remaining <= 0) {
      setSession(null)
      setNotice({ kind: 'info', text: 'Tu sesión expiró. Inicia sesión de nuevo.' })
      return
    }
    const timer = window.setTimeout(() => {
      setSession(null)
      setNotice({ kind: 'info', text: 'Tu sesión expiró. Inicia sesión de nuevo.' })
    }, Math.min(remaining, 2_147_483_647))
    return () => window.clearTimeout(timer)
  }, [session])

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy || !secureConnection) return
    const form = event.currentTarget
    const values = new FormData(form)
    const username = String(values.get('username') ?? '').trim()
    const password = String(values.get('password') ?? '')
    const passwordInput = form.elements.namedItem('password')
    if (passwordInput instanceof HTMLInputElement) passwordInput.value = ''
    setNotice(null)
    setBusy(true)
    try {
      setSession(await login(username, password))
    } catch (error) {
      setNotice({ kind: 'error', text: loginError(error) })
    } finally {
      setBusy(false)
    }
  }

  async function submitLogout() {
    if (!session || busy) return
    setNotice(null)
    setBusy(true)
    try {
      await logout(session.csrf_token)
      setSession(null)
    } catch (error) {
      if (errorStatus(error) === 401) {
        setSession(null)
        setNotice({ kind: 'info', text: 'Tu sesión expiró. Inicia sesión de nuevo.' })
      } else {
        setNotice({
          kind: 'error',
          text: 'No se pudo cerrar la sesión. Inténtalo de nuevo.',
        })
      }
    } finally {
      setBusy(false)
    }
  }

  if (checking) {
    return (
      <main className="loading-screen" aria-live="polite">
        <span className="brand-mark" aria-hidden="true">SA</span>
        <p>Verificando sesión…</p>
      </main>
    )
  }

  if (!session) {
    return (
      <main className="login-page">
        <section className="login-story" aria-label="San Ángel">
          <div className="story-top"><span className="brand-mark" aria-hidden="true">SA</span><span>SAN ÁNGEL</span></div>
          <div className="story-copy">
            <span className="eyebrow">PANEL DE OPERACIÓN</span>
            <h1>Tu operación,<br /><em>en un solo lugar.</em></h1>
            <p>Accede a las herramientas internas de tu instalación con tu cuenta de personal.</p>
          </div>
          <div className="story-footer">Acceso exclusivo para personal autorizado</div>
        </section>
        <section className="login-side">
          <div className="login-content">
            <p className="section-label">BIENVENIDO</p>
            <h2>Inicia sesión</h2>
            <p className="muted">Ingresa con las credenciales de tu instalación.</p>
            {notice && (
              <div className={`notice notice-${notice.kind}`} role="alert">
                <span>{notice.text}</span>
                {notice.text.startsWith('No se pudo verificar') && (
                  <button type="button" className="text-button" onClick={() => void refreshSession()}>
                    Reintentar
                  </button>
                )}
              </div>
            )}
            <form onSubmit={(event) => void submitLogin(event)}>
              <label htmlFor="username">Usuario</label>
              <input id="username" name="username" type="text" autoComplete="username" maxLength={64} required disabled={!secureConnection} />
              <label htmlFor="password">Contraseña</label>
              <input id="password" name="password" type="password" autoComplete="current-password" maxLength={1024} required disabled={!secureConnection} />
              <button className="primary-button" type="submit" disabled={busy || !secureConnection}>
                {busy ? 'Ingresando…' : 'Entrar al panel'}<span aria-hidden="true">→</span>
              </button>
            </form>
            <div className="login-help">Si necesitas acceso, contacta al responsable de esta instalación.</div>
          </div>
          <div className="login-legal">© San Ángel · Uso interno</div>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand"><span className="brand-mark" aria-hidden="true">SA</span><span>SAN ÁNGEL<small>ADMINISTRACIÓN</small></span></div>
        <nav aria-label="Navegación principal">
          <p className="nav-caption">ESPACIO DE TRABAJO</p>
          <span className="nav-item nav-active" aria-current="page"><span aria-hidden="true">◧</span>Resumen</span>
          <p className="nav-caption nav-second">PRÓXIMAMENTE</p>
          <span className="nav-item nav-disabled"><span aria-hidden="true">▦</span>Catálogo</span>
          <span className="nav-item nav-disabled"><span aria-hidden="true">◇</span>Conversaciones</span>
          <span className="nav-item nav-disabled"><span aria-hidden="true">▤</span>Preguntas</span>
        </nav>
        <div className="sidebar-footer">Panel de operación<br /><strong>Acceso interno</strong></div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-path">Panel <span>/</span> Resumen</div>
          <div className="topbar-actions">
            <div className="account"><span className="avatar" aria-hidden="true">{session.username.slice(0, 1).toUpperCase()}</span><span><strong>{session.username}</strong><small>{roleNames[session.role]}</small></span></div>
            <button className="logout-button" onClick={() => void submitLogout()} disabled={busy}>Cerrar sesión</button>
          </div>
        </header>
        <main className="dashboard">
          <div className="page-intro"><span className="section-label">VISTA GENERAL</span><h1>Bienvenido al panel</h1><p>Tu espacio de trabajo para administrar esta instalación.</p></div>
          {notice && <div className={`notice notice-${notice.kind}`} role="alert">{notice.text}</div>}
          <div className="summary-grid">
            <section className="summary-card accent-card"><span className="card-kicker">ESTADO DE ACCESO</span><div className="status-indicator"><span className="status-dot" />Sesión activa</div><p>Estás conectado como <strong>{session.username}</strong>.</p></section>
            <section className="summary-card"><span className="card-kicker">TU PERFIL</span><h2>{roleNames[session.role]}</h2><p>Los permisos de tu cuenta se verifican en el servidor.</p></section>
          </div>
          <section className="coming-panel"><div className="coming-icon" aria-hidden="true">↗</div><div><span className="card-kicker">SIGUIENTE PASO</span><h2>Más herramientas en camino</h2><p>Las secciones comerciales y de atención se habilitarán conforme se incorporen al panel.</p></div></section>
        </main>
      </div>
    </div>
  )
}
