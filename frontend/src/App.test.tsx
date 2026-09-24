import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from './App'
import { AdminApiError, getSession, login, logout } from './api'
import { commercialApi } from './commercialApi'

vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return { ...actual, getSession: vi.fn(), login: vi.fn(), logout: vi.fn() }
})

vi.mock('./commercialApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./commercialApi')>()
  return { ...actual, commercialApi: { ...actual.commercialApi, branch: vi.fn() } }
})

const validSession = {
  username: 'operador',
  role: 'owner' as const,
  expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
  csrf_token: 'test-only-csrf',
}

beforeEach(() => {
  vi.mocked(getSession).mockRejectedValue(new AdminApiError(401))
})

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

async function fillLogin() {
  const user = userEvent.setup()
  await screen.findByRole('heading', { name: 'Inicia sesión' })
  await user.type(screen.getByLabelText('Usuario'), 'operador')
  await user.type(screen.getByLabelText('Contraseña'), 'test-only-password')
  await user.click(screen.getByRole('button', { name: /Entrar al panel/ }))
  return user
}

describe('shell del panel', () => {
  it('muestra login sin sesión y errores seguros para credenciales inválidas', async () => {
    vi.mocked(login).mockRejectedValue(new AdminApiError(401))
    render(<App />)
    await fillLogin()
    expect(await screen.findByRole('alert')).toHaveProperty(
      'textContent',
      'Usuario o contraseña incorrectos.',
    )
    expect(document.body.textContent).not.toContain('test-only-password')
  })

  it('explica el límite de intentos y la falta de conexión', async () => {
    vi.mocked(login).mockRejectedValueOnce(new AdminApiError(429))
    render(<App />)
    const user = await fillLogin()
    expect((await screen.findByRole('alert')).textContent).toContain('Demasiados intentos')
    expect((screen.getByLabelText('Usuario') as HTMLInputElement).value).toBe('operador')
    vi.mocked(login).mockRejectedValueOnce(new AdminApiError(null))
    await user.type(screen.getByLabelText('Contraseña'), 'test-only-password')
    await user.click(screen.getByRole('button', { name: /Entrar al panel/ }))
    expect((await screen.findByRole('alert')).textContent).toContain('No se pudo conectar')
  })

  it('abre el layout con sesión vigente y cierra usando CSRF en memoria', async () => {
    vi.mocked(login).mockResolvedValue(validSession)
    vi.mocked(logout).mockResolvedValue()
    render(<App />)
    const user = await fillLogin()
    expect(await screen.findByRole('heading', { name: 'Bienvenido al panel' })).toBeTruthy()
    expect(screen.getByRole('navigation', { name: 'Navegación principal' })).toBeTruthy()
    expect(document.body.textContent).toContain('Propietario')
    await user.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    await screen.findByRole('heading', { name: 'Inicia sesión' })
    expect(logout).toHaveBeenCalledWith('test-only-csrf')
  })

  it('abre la sección de sucursal desde la navegación del panel', async () => {
    vi.mocked(getSession).mockResolvedValue(validSession)
    vi.mocked(commercialApi.branch).mockResolvedValue({
      code: 'sucursal-uno', name: 'Uno', address: 'Dirección',
      phone: null, business_hours: 'Lunes',
    })
    render(<App />)
    const user = userEvent.setup()
    await screen.findByRole('heading', { name: 'Bienvenido al panel' })
    await user.click(screen.getByRole('button', { name: 'Sucursal' }))
    expect(await screen.findByText('sucursal-uno')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Guardar sucursal' })).toBeTruthy()
  })

  it('muestra texto de usuario sin interpretarlo como HTML', async () => {
    vi.mocked(getSession).mockResolvedValue({
      ...validSession,
      username: '<img src=x onerror=alert(1)>',
    })
    render(<App />)
    await screen.findByRole('heading', { name: 'Bienvenido al panel' })
    expect(document.body.textContent).toContain('<img src=x onerror=alert(1)>')
    expect(document.querySelector('img')).toBeNull()
  })

  it('permite reintentar la comprobación si el API no responde', async () => {
    vi.mocked(getSession)
      .mockRejectedValueOnce(new AdminApiError(null))
      .mockResolvedValueOnce(validSession)
    render(<App />)
    const user = userEvent.setup()
    expect((await screen.findByRole('alert')).textContent).toContain('No se pudo verificar')
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Bienvenido al panel' })).toBeTruthy()
    })
  })
})
