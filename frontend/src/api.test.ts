import { afterEach, describe, expect, it, vi } from 'vitest'
import { AdminApiError, getSession, login, logout } from './api'

const session = {
  username: 'operador',
  role: 'viewer',
  expires_at: '2099-01-01T00:00:00Z',
  csrf_token: 'test-only-csrf',
}

afterEach(() => vi.unstubAllGlobals())

describe('cliente API admin', () => {
  it('usa rutas relativas, cookie del navegador y no guarda tokens', async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify(session), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    expect(await login('operador', 'test-only-password')).toEqual(session)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/admin/auth/login',
      expect.objectContaining({
        method: 'POST',
        credentials: 'same-origin',
        cache: 'no-store',
      }),
    )
    const body = JSON.parse(fetchMock.mock.calls[0]![1].body as string)
    expect(body).toEqual({ username: 'operador', password: 'test-only-password' })
    expect(await getSession()).toEqual(session)
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/admin/auth/session')
  })

  it('envía CSRF solo al cerrar sesión y no expone el token en la URL', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    await logout('test-only-csrf')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/admin/auth/logout',
      expect.objectContaining({
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRF-Token': 'test-only-csrf' },
      }),
    )
  })

  it('rechaza respuestas no JSON y conserva solo el estado del error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<script>malicioso</script>')))
    await expect(getSession()).rejects.toMatchObject({ status: null })

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('secreto interno', { status: 503 })))
    await expect(getSession()).rejects.toEqual(new AdminApiError(503))
  })
})
