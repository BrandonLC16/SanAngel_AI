import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PriceImportPanel } from './PriceImportPanel'
import { commercialApi } from './commercialApi'
import { priceImportApi } from './priceImportApi'

vi.mock('./commercialApi', async (original) => {
  const actual = await original<typeof import('./commercialApi')>()
  return { ...actual, commercialApi: { ...actual.commercialApi, branch: vi.fn() } }
})
vi.mock('./priceImportApi', async (original) => {
  const actual = await original<typeof import('./priceImportApi')>()
  return { ...actual, priceImportApi: { preview: vi.fn(), confirm: vi.fn() } }
})

beforeEach(() => {
  vi.mocked(commercialApi.branch).mockResolvedValue({
    code: 'sucursal-uno', name: 'Uno', address: 'Dirección', phone: null, business_hours: 'Lunes',
  })
})
afterEach(() => { cleanup(); vi.resetAllMocks() })

it('muestra destino fijo, preview y recibo tras confirmación explícita', async () => {
  vi.mocked(priceImportApi.preview).mockResolvedValue({
    branch_code: 'sucursal-uno', preview_id: 'a'.repeat(32), is_valid: true,
    summary: { new: 1, changed: 0, unchanged: 0, errors: 0 }, issues: [],
    items: [{ source_row: 7, product_id: 5, product_name: '<script>dato</script>', unit: 'kg', current_price_mxn: null, proposed_price_mxn: '123.45', verified_on: '2026-01-15', action: 'new' }],
  })
  vi.mocked(priceImportApi.confirm).mockResolvedValue({
    audit_id: 9, attempt_id: 'test-attempt', branch_code: 'sucursal-uno',
    created: 1, updated: 0, unchanged: 0,
  })
  const user = userEvent.setup({ applyAccept: false })
  render(<PriceImportPanel role="editor" csrfToken="test-csrf" onExpired={vi.fn()} />)
  expect(await screen.findByText(/Uno \(sucursal-uno\)/)).toBeTruthy()
  await user.upload(screen.getByLabelText('Archivo de precios'), new File(['xlsx'], 'precios.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))
  expect((screen.getByLabelText('Archivo de precios') as HTMLInputElement).files?.length).toBe(1)
  await user.click(screen.getByRole('button', { name: 'Ver vista previa' }))
  expect(priceImportApi.preview).toHaveBeenCalled()
  await screen.findByRole('button', { name: 'Confirmar importación' })
  expect(priceImportApi.confirm).not.toHaveBeenCalled()
  expect(document.querySelector('script')).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Confirmar importación' }))
  await waitFor(() => expect(priceImportApi.confirm).toHaveBeenCalledWith('a'.repeat(32), 'test-csrf'))
  expect(await screen.findByText('Recibo de auditoría: #9')).toBeTruthy()
})

it('no ofrece importación al perfil de consulta', async () => {
  render(<PriceImportPanel role="viewer" csrfToken="test-csrf" onExpired={vi.fn()} />)
  expect(await screen.findByText(/Uno \(sucursal-uno\)/)).toBeTruthy()
  expect(screen.queryByLabelText('Archivo de precios')).toBeNull()
})
