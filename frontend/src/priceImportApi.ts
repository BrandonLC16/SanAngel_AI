import { AdminApiError } from './api'

export const MAX_IMPORT_BYTES = 2 * 1024 * 1024
const BASE = '/api/v1/admin/price-import'
const XLSX_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

export type ImportIssue = { row: number | null; field: string | null; code: string }
export type ImportPreview = {
  branch_code: string
  preview_id: string | null
  is_valid: boolean
  summary: { new: number; changed: number; unchanged: number; errors: number }
  items: {
    source_row: number; product_id: number; product_name: string; unit: string
    current_price_mxn: string | null; proposed_price_mxn: string
    verified_on: string; action: 'new' | 'changed' | 'unchanged'
  }[]
  issues: ImportIssue[]
}
export type ImportReceipt = {
  audit_id: number; attempt_id: string; branch_code: string
  created: number; updated: number; unchanged: number
}

async function post<T>(path: string, csrf: string, body: BodyInit, contentType: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}/${path}`, {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': contentType, 'X-CSRF-Token': csrf,
        ...(body instanceof File ? { 'X-File-Name': encodeURIComponent(body.name) } : {}),
      }, body,
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

export const priceImportApi = {
  preview(file: File, csrf: string): Promise<ImportPreview> {
    if (!/\.xlsx$/i.test(file.name) || file.name.startsWith('.') || file.name.includes('..') || file.name.includes('/') || file.name.includes('\\') || file.name.includes(':') || file.name.length > 255 || encodeURIComponent(file.name).length > 512) {
      throw new AdminApiError(422)
    }
    if (file.size < 1 || file.size > MAX_IMPORT_BYTES) throw new AdminApiError(413)
    return post('preview', csrf, file, XLSX_TYPE)
  },
  confirm(previewId: string, csrf: string): Promise<ImportReceipt> {
    if (!/^[0-9a-f]{32}$/.test(previewId)) throw new AdminApiError(422)
    return post('confirm', csrf, JSON.stringify({ preview_id: previewId, confirmed: true }), 'application/json')
  },
}
