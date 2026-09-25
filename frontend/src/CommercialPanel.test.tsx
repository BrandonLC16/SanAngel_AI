import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CommercialPanel } from './CommercialPanel'
import { commercialApi } from './commercialApi'

vi.mock('./commercialApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./commercialApi')>()
  return {
    ...actual,
    commercialApi: Object.fromEntries(
      Object.keys(actual.commercialApi).map((key) => [key, vi.fn()]),
    ),
  }
})

beforeEach(() => {
  vi.mocked(commercialApi.branch).mockResolvedValue({
    code: 'sucursal-uno', name: 'Uno', address: 'Dirección', phone: null, business_hours: 'Lunes',
  })
  vi.mocked(commercialApi.products).mockResolvedValue([])
  vi.mocked(commercialApi.faqs).mockResolvedValue([])
  vi.mocked(commercialApi.prices).mockResolvedValue([])
})

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

it('muestra la sucursal fija y solo permite guardarla al propietario', async () => {
  const onExpired = vi.fn()
  render(<CommercialPanel section="branch" role="editor" csrfToken="csrf" onExpired={onExpired} />)
  expect(await screen.findByText('sucursal-uno')).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Guardar sucursal' })).toBeNull()
  expect((screen.getByLabelText('Nombre') as HTMLInputElement).disabled).toBe(true)
})

it('crea producto con CSRF y muestra texto de catálogo como texto', async () => {
  vi.mocked(commercialApi.products)
    .mockResolvedValueOnce([{ id: 1, name: '<img src=x onerror=alert(1)>', category: 'Res', is_active: true }])
    .mockResolvedValueOnce([{ id: 1, name: '<img src=x onerror=alert(1)>', category: 'Res', is_active: true }])
  vi.mocked(commercialApi.createProduct).mockResolvedValue({ id: 2, name: 'Aguja', category: 'Res', is_active: true })
  const user = userEvent.setup()
  render(<CommercialPanel section="products" role="editor" csrfToken="test-only-csrf" onExpired={vi.fn()} />)
  expect(await screen.findByText('<img src=x onerror=alert(1)>')).toBeTruthy()
  expect(document.querySelector('img')).toBeNull()
  await user.type(screen.getByLabelText('Nombre'), 'Aguja')
  await user.type(screen.getByLabelText('Categoría'), 'Res')
  await user.click(screen.getByRole('button', { name: 'Crear producto' }))
  await waitFor(() => expect(commercialApi.createProduct).toHaveBeenCalledWith(
    { name: 'Aguja', category: 'Res' }, 'test-only-csrf',
  ))
})

it('muestra pregunta y respuesta FAQ no confiables como texto', async () => {
  const question = '<img src=x onerror=alert(1)>'
  const answer = '<script>alert(1)</script>'
  vi.mocked(commercialApi.faqs).mockResolvedValue([{
    id: 8, category: 'general', question, answer, is_active: true,
  }])
  render(<CommercialPanel section="faqs" role="viewer" csrfToken="csrf" onExpired={vi.fn()} />)
  expect(await screen.findByText(question)).toBeTruthy()
  await userEvent.setup().click(screen.getByRole('button', { name: 'Ver' }))
  expect((screen.getByLabelText('Respuesta') as HTMLTextAreaElement).value).toBe(answer)
  expect(document.querySelector('img')).toBeNull()
  expect(document.querySelector('script')).toBeNull()
})
