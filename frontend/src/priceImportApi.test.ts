import { afterEach, expect, it, vi } from 'vitest'
import { MAX_IMPORT_BYTES, priceImportApi } from './priceImportApi'

afterEach(() => vi.unstubAllGlobals())

it('envía solo XLSX acotado al mismo origen con CSRF', async () => {
  const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify({ branch_code: 'uno' }), {
    headers: { 'Content-Type': 'application/json' },
  })))
  vi.stubGlobal('fetch', fetchMock)
  const file = new File(['data'], 'precios.xlsx')
  await priceImportApi.preview(file, 'csrf')
  expect(fetchMock).toHaveBeenCalledWith('/api/v1/admin/price-import/preview', expect.objectContaining({
    method: 'POST', credentials: 'same-origin', cache: 'no-store', body: file,
    headers: { 'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'X-CSRF-Token': 'csrf', 'X-File-Name': 'precios.xlsx' },
  }))
  await priceImportApi.confirm('a'.repeat(32), 'csrf')
  expect(fetchMock.mock.calls[1]![1].body).toBe(JSON.stringify({ preview_id: 'a'.repeat(32), confirmed: true }))
  expect(fetchMock.mock.calls[1]![0]).not.toContain('csrf')
})

it('bloquea archivo y token inválidos antes de llamar al servidor', () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  expect(() => priceImportApi.preview(new File(['x'], 'precios.xlsm'), 'csrf')).toThrow()
  expect(() => priceImportApi.preview(new File(['x'], '../precios.xlsx'), 'csrf')).toThrow()
  expect(() => priceImportApi.preview(new File([new Uint8Array(MAX_IMPORT_BYTES + 1)], 'precios.xlsx'), 'csrf')).toThrow()
  expect(() => priceImportApi.confirm('../other', 'csrf')).toThrow()
  expect(fetchMock).not.toHaveBeenCalled()
})
