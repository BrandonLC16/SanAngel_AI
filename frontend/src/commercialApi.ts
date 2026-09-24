import { AdminApiError } from './api'

export type Branch = {
  code: string
  name: string
  address: string
  phone: string | null
  business_hours: string
}

export type Product = { id: number; name: string; category: string; is_active: boolean }
export type Price = { id: number; product_id: number; unit: string; amount: string }
export type FAQ = {
  id: number
  category: 'general' | 'servicios' | 'pagos' | 'entregas' | 'politicas'
  question: string
  answer: string
  is_active: boolean
}
export type FAQInput = Omit<FAQ, 'id'>

const BASE = '/api/v1/admin/commercial'

async function request<T>(path: string, method = 'GET', csrf?: string, body?: object): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      credentials: 'same-origin',
      cache: 'no-store',
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
  } catch {
    throw new AdminApiError(null)
  }
  if (!response.ok) throw new AdminApiError(response.status)
  if (response.status === 204) return undefined as T
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new AdminApiError(null)
  }
  try {
    return await response.json() as T
  } catch {
    throw new AdminApiError(null)
  }
}

function positiveId(id: number): number {
  if (!Number.isSafeInteger(id) || id < 1) throw new AdminApiError(null)
  return id
}

function validUnit(unit: string): string {
  const normalized = unit.trim().toLowerCase()
  if (normalized.length > 24 || !/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(normalized)) {
    throw new AdminApiError(422)
  }
  return normalized
}

export const commercialApi = {
  branch: () => request<Branch>('/branch'),
  updateBranch: (value: Omit<Branch, 'code'>, csrf: string) =>
    request<Branch>('/branch', 'PUT', csrf, value),
  products: () => request<Product[]>('/products'),
  createProduct: (value: Pick<Product, 'name' | 'category'>, csrf: string) =>
    request<Product>('/products', 'POST', csrf, value),
  updateProduct: (id: number, value: Omit<Product, 'id'>, csrf: string) =>
    request<Product>(`/products/${positiveId(id)}`, 'PUT', csrf, value),
  deactivateProduct: (id: number, csrf: string) =>
    request<void>(`/products/${positiveId(id)}`, 'DELETE', csrf),
  prices: (productId: number) =>
    request<Price[]>(`/products/${positiveId(productId)}/prices`),
  putPrice: (productId: number, unit: string, amount: string, csrf: string) =>
    request<Price>(`/products/${positiveId(productId)}/prices/${validUnit(unit)}`, 'PUT', csrf, { amount }),
  deletePrice: (productId: number, unit: string, csrf: string) =>
    request<void>(`/products/${positiveId(productId)}/prices/${validUnit(unit)}`, 'DELETE', csrf),
  faqs: () => request<FAQ[]>('/faqs'),
  createFAQ: (value: FAQInput, csrf: string) => request<FAQ>('/faqs', 'POST', csrf, value),
  updateFAQ: (id: number, value: FAQInput, csrf: string) =>
    request<FAQ>(`/faqs/${positiveId(id)}`, 'PUT', csrf, value),
  deactivateFAQ: (id: number, csrf: string) =>
    request<void>(`/faqs/${positiveId(id)}`, 'DELETE', csrf),
}
