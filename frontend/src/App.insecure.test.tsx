// @vitest-environment-options {"url":"http://127.0.0.1:5173/"}

import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { App } from './App'
import { getSession } from './api'

vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return { ...actual, getSession: vi.fn() }
})

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

it('bloquea credenciales cuando el shell se abre por HTTP', async () => {
  render(<App />)
  expect((await screen.findByRole('alert')).textContent).toContain('HTTPS')
  expect((screen.getByLabelText('Usuario') as HTMLInputElement).disabled).toBe(true)
  expect((screen.getByLabelText('Contraseña') as HTMLInputElement).disabled).toBe(true)
  expect((screen.getByRole('button', { name: /Entrar al panel/ }) as HTMLButtonElement).disabled).toBe(true)
  expect(getSession).not.toHaveBeenCalled()
})
