import { useEffect, useState, type FormEvent } from 'react'
import { AdminApiError } from './api'
import { auditApi, type AuditEvent } from './auditApi'

type Props = { onExpired: () => void }
const PAGE_SIZE = 25
const entities = { branch: 'Sucursal', product: 'Producto', price: 'Precio', faq: 'FAQ', admin_user: 'Usuario' }
const actions = { create: 'Alta', update: 'Cambio', deactivate: 'Desactivación', delete: 'Baja' }

function formatDate(value: string): string {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? 'Fecha no disponible' : parsed.toLocaleString('es-MX')
}

function stateText(event: AuditEvent, state: 'before' | 'after'): string {
  const value = event[state]
  if (!value) return '—'
  if (event.entity === 'price' && value.amount) return `$${value.amount} MXN`
  if (event.entity === 'admin_user' && value.role) return value.role
  return '—'
}

export function AuditPanel({ onExpired }: Props) {
  const [entity, setEntity] = useState('')
  const [productId, setProductId] = useState('')
  const [applied, setApplied] = useState({ entity: '', productId: '' })
  const [items, setItems] = useState<AuditEvent[]>([])
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load(nextOffset: number, filters = applied) {
    setBusy(true); setError(null)
    try {
      const page = await auditApi.events({
        entity: filters.entity || undefined,
        productId: filters.productId ? Number(filters.productId) : undefined,
        offset: nextOffset,
      })
      setItems(page.items); setHasMore(page.has_more); setOffset(nextOffset); setApplied(filters)
    } catch (failure) {
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
      else setError('No se pudo consultar la auditoría. Revisa los filtros e inténtalo de nuevo.')
    } finally { setBusy(false) }
  }

  useEffect(() => { void load(0) }, [])

  function apply(event: FormEvent) {
    event.preventDefault()
    void load(0, { entity, productId })
  }

  return <div className="commercial review-panel">
    <section className="admin-card">
      <h2>Auditoría administrativa</h2>
      <p className="muted">Cambios de esta sucursal. Los importes y roles muestran su valor anterior y posterior; otros recursos conservan solo el recibo del cambio.</p>
      {error && <div role="alert" className="notice notice-error">{error}</div>}
      <form className="review-filters" onSubmit={apply}>
        <label htmlFor="audit-entity">Entidad</label>
        <select id="audit-entity" value={entity} onChange={(event) => { setEntity(event.target.value); if (event.target.value !== 'price') setProductId('') }} disabled={busy}>
          <option value="">Todas</option>{Object.entries(entities).map(([key, label]) => <option value={key} key={key}>{label}</option>)}
        </select>
        <label htmlFor="audit-product">ID de producto</label>
        <input id="audit-product" type="number" min="1" step="1" value={productId} onChange={(event) => setProductId(event.target.value)} disabled={busy || entity !== 'price'} />
        <button type="submit" disabled={busy}>Filtrar</button>
      </form>
      <div className="admin-list">
        {items.length === 0 && !busy && <p>No hay cambios con estos filtros.</p>}
        {items.map((item) => <div className="admin-row" key={`${item.source}-${item.id}`}><div>
          <strong>{actions[item.action]} · {entities[item.entity]} #{item.entity_id}{item.unit ? ` · ${item.unit}` : ''}</strong>
          <small>{formatDate(item.occurred_at)} · Actor #{item.actor_user_id}{item.product_id ? ` · Producto #${item.product_id}` : ''}</small>
          <small>Antes: {stateText(item, 'before')} · Después: {stateText(item, 'after')}</small>
        </div></div>)}
      </div>
      <div className="admin-actions"><button type="button" disabled={busy || offset === 0} onClick={() => void load(Math.max(0, offset - PAGE_SIZE))}>Anterior</button><button type="button" disabled={busy || !hasMore} onClick={() => void load(offset + PAGE_SIZE)}>Siguiente</button></div>
    </section>
  </div>
}
