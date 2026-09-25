import { AdminApiError } from './api'

export type AuditEvent = {
  id: number; source: 'commercial' | 'role'; actor_user_id: number
  action: 'create' | 'update' | 'deactivate' | 'delete'
  entity: 'branch' | 'product' | 'price' | 'faq' | 'admin_user'
  entity_id: number; occurred_at: string; product_id: number | null; unit: string | null
  before: Record<string, string> | null; after: Record<string, string> | null
}
export type AuditPage = { items: AuditEvent[]; has_more: boolean }

export const auditApi = {
  async events(filters: { entity?: string; productId?: number; offset: number }): Promise<AuditPage> {
    if (!Number.isSafeInteger(filters.offset) || filters.offset < 0 || filters.offset > 5000) throw new AdminApiError(422)
    if (filters.productId !== undefined && (!Number.isSafeInteger(filters.productId) || filters.productId < 1)) throw new AdminApiError(422)
    const query = new URLSearchParams({ limit: '25', offset: String(filters.offset) })
    if (filters.entity) query.set('entity', filters.entity)
    if (filters.productId !== undefined) query.set('product_id', String(filters.productId))
    let response: Response
    try {
      response = await fetch(`/api/v1/admin/audit/events?${query}`, { credentials: 'same-origin', cache: 'no-store' })
    } catch {
      throw new AdminApiError(null)
    }
    if (!response.ok) throw new AdminApiError(response.status)
    if (!response.headers.get('content-type')?.includes('application/json')) throw new AdminApiError(null)
    try { return await response.json() as AuditPage } catch { throw new AdminApiError(null) }
  },
}
