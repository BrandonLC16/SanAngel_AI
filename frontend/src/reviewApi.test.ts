import { afterEach, expect, it, vi } from 'vitest'
import { reviewApi } from './reviewApi'

afterEach(() => vi.unstubAllGlobals())

it('usa rutas del mismo origen y solo envía CSRF en escrituras', async () => {
  const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify({ items: [], has_more: false }), {
    headers: { 'Content-Type': 'application/json' },
  })))
  vi.stubGlobal('fetch', fetchMock)
  await reviewApi.conversations({ updatedFrom: '2026-09-01', offset: 0 })
  expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/admin/review/conversations?limit=25&offset=0&updated_from=2026-09-01')
  expect(fetchMock.mock.calls[0]![1]).toMatchObject({ credentials: 'same-origin', cache: 'no-store' })
  await reviewApi.resolve(4, { category: 'general', question: '¿Tienen entrega?', answer: 'Sí.' }, 'csrf')
  expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/admin/review/unresolved/4/resolve')
  expect(fetchMock.mock.calls[1]![1]).toMatchObject({
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': 'csrf' },
    body: JSON.stringify({ category: 'general', question: '¿Tienen entrega?', answer: 'Sí.', is_active: true }),
  })
  expect(fetchMock.mock.calls[1]![0]).not.toContain('csrf')
  await reviewApi.conversations({ mode: 'HUMAN', mine: true, offset: 25 })
  expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/admin/review/conversations?limit=25&offset=25&mode=HUMAN&mine=true')
  await reviewApi.take(7, 'csrf')
  await reviewApi.release(7, 'csrf')
  expect(fetchMock.mock.calls[3]![0]).toBe('/api/v1/admin/review/conversations/7/take')
  expect(fetchMock.mock.calls[4]![0]).toBe('/api/v1/admin/review/conversations/7/release')
  for (const index of [3, 4]) {
    expect(fetchMock.mock.calls[index]![1]).toMatchObject({ method: 'POST', credentials: 'same-origin', headers: { 'X-CSRF-Token': 'csrf' } })
    expect(fetchMock.mock.calls[index]![0]).not.toContain('csrf')
  }
})

it('rechaza IDs, filtros y paginación inválidos antes de llamar al servidor', () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  expect(() => reviewApi.conversation(0)).toThrow()
  expect(() => reviewApi.unresolvedDetail(-1)).toThrow()
  expect(() => reviewApi.unresolved({ reason: 'other', minOccurrences: 1, offset: 0 })).toThrow()
  expect(() => reviewApi.conversations({ updatedFrom: '../x', offset: 0 })).toThrow()
  expect(() => reviewApi.conversations({ offset: 5001 })).toThrow()
  expect(() => reviewApi.conversations({ mode: 'OTHER' as 'AI', offset: 0 })).toThrow()
  expect(() => reviewApi.take(0, 'csrf')).toThrow()
  expect(fetchMock).not.toHaveBeenCalled()
})
