import { afterEach, describe, expect, it, vi } from 'vitest'
import { commercialApi } from './commercialApi'

afterEach(() => vi.unstubAllGlobals())

describe('cliente comercial', () => {
  it('limita rutas al mismo origen y envía CSRF en escrituras', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 7, product_id: 3, unit: 'kg', amount: '120.00' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    await commercialApi.putPrice(3, 'KG', '120.00', 'test-only-csrf')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/admin/commercial/products/3/prices/kg',
      expect.objectContaining({
        method: 'PUT',
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': 'test-only-csrf' },
        body: JSON.stringify({ amount: '120.00' }),
      }),
    )
    expect(fetchMock.mock.calls[0]![0]).not.toContain('test-only-csrf')
  })

  it('rechaza IDs y unidades que puedan alterar la ruta', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    expect(() => commercialApi.deletePrice(0, 'kg', 'csrf')).toThrow()
    expect(() => commercialApi.deletePrice(1, '../branch', 'csrf')).toThrow()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('no propaga respuestas de error del servidor', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('detalle privado', { status: 503 }),
    ))
    await expect(commercialApi.products()).rejects.toMatchObject({ status: 503, message: 'admin_api_error' })
  })
})
