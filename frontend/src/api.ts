export type AdminRole = 'viewer' | 'editor' | 'owner'

export type AdminSession = {
  username: string
  role: AdminRole
  expires_at: string
  csrf_token: string
}

export class AdminApiError extends Error {
  constructor(readonly status: number | null) {
    super('admin_api_error')
    this.name = 'AdminApiError'
  }
}

function isSession(value: unknown): value is AdminSession {
  if (typeof value !== 'object' || value === null) return false
  const session = value as Record<string, unknown>
  return (
    typeof session.username === 'string' &&
    (session.role === 'viewer' || session.role === 'editor' || session.role === 'owner') &&
    typeof session.expires_at === 'string' &&
    typeof session.csrf_token === 'string'
  )
}

async function requestSession(path: string, init: RequestInit): Promise<AdminSession> {
  let response: Response
  try {
    response = await fetch(`/api/v1/admin/auth/${path}`, {
      ...init,
      credentials: 'same-origin',
      cache: 'no-store',
    })
  } catch {
    throw new AdminApiError(null)
  }
  if (!response.ok) throw new AdminApiError(response.status)
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new AdminApiError(null)
  }
  let body: unknown
  try {
    body = await response.json()
  } catch {
    throw new AdminApiError(null)
  }
  if (!isSession(body)) throw new AdminApiError(null)
  return body
}

export function getSession(): Promise<AdminSession> {
  return requestSession('session', { method: 'GET' })
}

export function login(username: string, password: string): Promise<AdminSession> {
  return requestSession('login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
}

export async function logout(csrfToken: string): Promise<void> {
  let response: Response
  try {
    response = await fetch('/api/v1/admin/auth/logout', {
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      credentials: 'same-origin',
      cache: 'no-store',
    })
  } catch {
    throw new AdminApiError(null)
  }
  if (!response.ok) throw new AdminApiError(response.status)
}
