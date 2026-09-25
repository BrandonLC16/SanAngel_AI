import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReviewPanel } from './ReviewPanel'
import { reviewApi } from './reviewApi'

vi.mock('./reviewApi', async (original) => {
  const actual = await original<typeof import('./reviewApi')>()
  return { ...actual, reviewApi: Object.fromEntries(Object.keys(actual.reviewApi).map((key) => [key, vi.fn()])) }
})

beforeEach(() => {
  vi.mocked(reviewApi.conversations).mockResolvedValue({ items: [], has_more: false })
  vi.mocked(reviewApi.unresolved).mockResolvedValue({ items: [], has_more: false })
})
afterEach(() => { cleanup(); vi.resetAllMocks() })

it('filtra conversaciones y muestra solo el detalle mínimo', async () => {
  vi.mocked(reviewApi.conversations).mockResolvedValue({
    items: [{ id: 7, channel: 'whatsapp', created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-25T10:00:00Z' }], has_more: false,
  })
  vi.mocked(reviewApi.conversation).mockResolvedValue({
    id: 7, channel: 'whatsapp', created_at: '2026-09-20T10:00:00Z', updated_at: '2026-09-25T10:00:00Z',
    message_count: 1, recent_messages: [{ direction: 'inbound', occurred_at: '2026-09-25T10:00:00Z' }],
  })
  const user = userEvent.setup()
  render(<ReviewPanel section="conversations" role="viewer" csrfToken="csrf" onExpired={vi.fn()} />)
  expect(await screen.findByText('Conversación #7')).toBeTruthy()
  expect(document.body.textContent).not.toContain('chatId')
  await user.type(screen.getByLabelText('Actividad desde'), '2026-09-01')
  await user.click(screen.getByRole('button', { name: 'Filtrar' }))
  await waitFor(() => expect(reviewApi.conversations).toHaveBeenLastCalledWith({ updatedFrom: '2026-09-01', updatedTo: undefined, offset: 0 }))
  await user.click(screen.getByRole('button', { name: 'Ver detalle' }))
  expect(await screen.findByText('Metadatos de mensajes disponibles: 1')).toBeTruthy()
  expect(document.body.textContent).toContain('Entrante')
})

it('permite resolver una FAQ solo al editor y limpia la pregunta del formulario', async () => {
  vi.mocked(reviewApi.unresolved).mockResolvedValue({
    items: [{ id: 4, reason: 'faq_unknown', occurrences: 3, first_seen_at: '2026-09-20T10:00:00Z', last_seen_at: '2026-09-25T10:00:00Z' }], has_more: false,
  })
  vi.mocked(reviewApi.unresolvedDetail).mockResolvedValue({
    id: 4, reason: 'faq_unknown', occurrences: 3, first_seen_at: '2026-09-20T10:00:00Z', last_seen_at: '2026-09-25T10:00:00Z',
  })
  vi.mocked(reviewApi.resolve).mockResolvedValue({ faq_id: 12, unresolved_id: 4 })
  const user = userEvent.setup()
  render(<ReviewPanel section="unresolved" role="editor" csrfToken="csrf" onExpired={vi.fn()} />)
  await screen.findByText(/Registro #4 · Desconocida/)
  await user.click(screen.getByRole('button', { name: 'Ver detalle' }))
  await screen.findByRole('button', { name: 'Guardar FAQ y resolver' })
  await user.type(screen.getByLabelText('Pregunta aprobada'), '¿Aceptan vales?')
  await user.type(screen.getByLabelText('Respuesta aprobada'), 'Sí, aceptamos vales.')
  await user.click(screen.getByRole('button', { name: 'Guardar FAQ y resolver' }))
  await waitFor(() => expect(reviewApi.resolve).toHaveBeenCalledWith(
    4, { category: 'general', question: '¿Aceptan vales?', answer: 'Sí, aceptamos vales.' }, 'csrf',
  ))
  expect(await screen.findByText('FAQ #12 guardada; agregado #4 resuelto.')).toBeTruthy()
  expect(screen.queryByLabelText('Pregunta aprobada')).toBeNull()
})

it('oculta la resolución al perfil de consulta', async () => {
  vi.mocked(reviewApi.unresolved).mockResolvedValue({
    items: [{ id: 4, reason: 'faq_unknown', occurrences: 3, first_seen_at: '2026-09-20T10:00:00Z', last_seen_at: '2026-09-25T10:00:00Z' }], has_more: false,
  })
  vi.mocked(reviewApi.unresolvedDetail).mockResolvedValue({
    id: 4, reason: 'faq_unknown', occurrences: 3, first_seen_at: '2026-09-20T10:00:00Z', last_seen_at: '2026-09-25T10:00:00Z',
  })
  const user = userEvent.setup()
  render(<ReviewPanel section="unresolved" role="viewer" csrfToken="csrf" onExpired={vi.fn()} />)
  await screen.findByText(/Registro #4 · Desconocida/)
  await user.click(screen.getByRole('button', { name: 'Ver detalle' }))
  await screen.findByLabelText('Detalle de pregunta no resuelta')
  expect(screen.queryByRole('button', { name: 'Guardar FAQ y resolver' })).toBeNull()
})
