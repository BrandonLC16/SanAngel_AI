import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuditPanel } from './AuditPanel'
import { auditApi } from './auditApi'

vi.mock('./auditApi', () => ({ auditApi: { events: vi.fn() } }))
afterEach(() => { cleanup(); vi.resetAllMocks() })

it('muestra actor, entidad, fecha y antes/después de un precio; filtra por producto', async () => {
  vi.mocked(auditApi.events).mockResolvedValue({
    has_more: false,
    items: [{ id: 7, source: 'commercial', actor_user_id: 3, action: 'update', entity: 'price',
      entity_id: 18, occurred_at: '2026-09-25T12:00:00Z', product_id: 4, unit: 'kg',
      before: { amount: '123.45' }, after: { amount: '130.00' } }],
  })
  render(<AuditPanel onExpired={vi.fn()} />)
  expect(await screen.findByText(/Cambio · Precio #18/)).toBeTruthy()
  expect(screen.getByText(/Actor #3 · Producto #4/)).toBeTruthy()
  expect(screen.getByText(/Antes: \$123.45 MXN · Después: \$130.00 MXN/)).toBeTruthy()
  const user = userEvent.setup()
  await user.selectOptions(screen.getByLabelText('Entidad'), 'price')
  await user.type(screen.getByLabelText('ID de producto'), '4')
  await user.click(screen.getByRole('button', { name: 'Filtrar' }))
  expect(auditApi.events).toHaveBeenLastCalledWith({ entity: 'price', productId: 4, offset: 0 })
  expect(document.body.textContent).not.toContain('password')
})
