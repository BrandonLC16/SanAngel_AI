import { AdminApiError } from './api'

export type ConversationItem = { id: number; channel: 'whatsapp'; created_at: string; updated_at: string }
export type MessageMetadata = { direction: 'inbound' | 'outbound'; occurred_at: string }
export type ConversationDetail = ConversationItem & { message_count: number; recent_messages: MessageMetadata[] }
export type UnresolvedItem = {
  id: number; reason: 'faq_unknown' | 'faq_ambiguous'; occurrences: number
  first_seen_at: string; last_seen_at: string
}
export type Page<T> = { items: T[]; has_more: boolean }
export type ResolveFAQInput = {
  category: 'general' | 'servicios' | 'pagos' | 'entregas' | 'politicas'
  question: string; answer: string
}
export type ResolveFAQResult = { faq_id: number; unresolved_id: number }

const BASE = '/api/v1/admin/review'

function positiveId(id: number): number {
  if (!Number.isSafeInteger(id) || id < 1) throw new AdminApiError(422)
  return id
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init, credentials: 'same-origin', cache: 'no-store',
    })
  } catch {
    throw new AdminApiError(null)
  }
  if (!response.ok) throw new AdminApiError(response.status)
  if (!response.headers.get('content-type')?.includes('application/json')) throw new AdminApiError(null)
  try {
    return await response.json() as T
  } catch {
    throw new AdminApiError(null)
  }
}

function pageQuery(offset: number): URLSearchParams {
  if (!Number.isSafeInteger(offset) || offset < 0 || offset > 5000) throw new AdminApiError(422)
  return new URLSearchParams({ limit: '25', offset: String(offset) })
}

function validDate(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new AdminApiError(422)
  return value
}

export const reviewApi = {
  conversations(filters: { updatedFrom?: string; updatedTo?: string; offset: number }): Promise<Page<ConversationItem>> {
    const query = pageQuery(filters.offset)
    if (filters.updatedFrom) query.set('updated_from', validDate(filters.updatedFrom))
    if (filters.updatedTo) query.set('updated_to', validDate(filters.updatedTo))
    return request(`/conversations?${query}`)
  },
  conversation(id: number): Promise<ConversationDetail> {
    return request(`/conversations/${positiveId(id)}`)
  },
  unresolved(filters: { reason?: string; minOccurrences: number; offset: number }): Promise<Page<UnresolvedItem>> {
    const query = pageQuery(filters.offset)
    if (filters.reason) {
      if (filters.reason !== 'faq_unknown' && filters.reason !== 'faq_ambiguous') throw new AdminApiError(422)
      query.set('reason', filters.reason)
    }
    if (!Number.isSafeInteger(filters.minOccurrences) || filters.minOccurrences < 1 || filters.minOccurrences > 1000000) throw new AdminApiError(422)
    query.set('min_occurrences', String(filters.minOccurrences))
    return request(`/unresolved?${query}`)
  },
  unresolvedDetail(id: number): Promise<UnresolvedItem> {
    return request(`/unresolved/${positiveId(id)}`)
  },
  resolve(id: number, value: ResolveFAQInput, csrf: string): Promise<ResolveFAQResult> {
    return request(`/unresolved/${positiveId(id)}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify({ ...value, is_active: true }),
    })
  },
}
