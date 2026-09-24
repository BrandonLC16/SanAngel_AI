import { useEffect, useState, type FormEvent } from 'react'
import { AdminApiError, type AdminRole } from './api'
import { commercialApi, type Branch, type FAQ, type FAQInput, type Price, type Product } from './commercialApi'

export type CommercialSection = 'branch' | 'products' | 'faqs'

type Props = {
  section: CommercialSection
  role: AdminRole
  csrfToken: string
  onExpired: () => void
}

const emptyFAQ: FAQInput = {
  category: 'general', question: '', answer: '', is_active: true,
}

function safeError(error: unknown): string {
  const status = error instanceof AdminApiError ? error.status : null
  switch (status) {
    case 401: return 'Tu sesión expiró. Inicia sesión de nuevo.'
    case 403: return 'No tienes permiso para esta operación.'
    case 404: return 'El registro ya no está disponible en esta sucursal.'
    case 409: return 'El registro ya existe o no puede modificarse.'
    case 422: return 'Revisa los datos e inténtalo de nuevo.'
    default: return 'No se pudo completar la operación. Inténtalo de nuevo.'
  }
}

export function CommercialPanel({ section, role, csrfToken, onExpired }: Props) {
  const [branch, setBranch] = useState<Branch | null>(null)
  const [branchDraft, setBranchDraft] = useState<Omit<Branch, 'code'> | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [selectedProduct, setSelectedProduct] = useState<number | null>(null)
  const [productName, setProductName] = useState('')
  const [productCategory, setProductCategory] = useState('')
  const [prices, setPrices] = useState<Price[]>([])
  const [priceUnit, setPriceUnit] = useState('kg')
  const [priceAmount, setPriceAmount] = useState('')
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [selectedFAQ, setSelectedFAQ] = useState<number | null>(null)
  const [faqDraft, setFaqDraft] = useState<FAQInput>(emptyFAQ)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const canWrite = role === 'editor' || role === 'owner'

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    setNotice(null)
    const load = async () => {
      try {
        if (section === 'branch') {
          const value = await commercialApi.branch()
          if (active) {
            setBranch(value)
            setBranchDraft({ name: value.name, address: value.address, phone: value.phone, business_hours: value.business_hours })
          }
        } else if (section === 'products') {
          const value = await commercialApi.products()
          if (active) setProducts(value)
        } else {
          const value = await commercialApi.faqs()
          if (active) setFaqs(value)
        }
      } catch (failure) {
        if (active) {
          setError(safeError(failure))
          if (failure instanceof AdminApiError && failure.status === 401) onExpired()
        }
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => { active = false }
  }, [section, onExpired])

  async function run(action: () => Promise<unknown>, refresh: () => Promise<void>, success: string): Promise<boolean> {
    if (busy) return false
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await action()
      await refresh()
      setNotice(success)
      return true
    } catch (failure) {
      setError(safeError(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
      return false
    } finally {
      setBusy(false)
    }
  }

  async function refreshProducts() { setProducts(await commercialApi.products()) }
  async function refreshPrices(productId: number) { setPrices(await commercialApi.prices(productId)) }
  async function refreshFAQs() { setFaqs(await commercialApi.faqs()) }

  function editProduct(product: Product) {
    setSelectedProduct(product.id)
    setProductName(product.name)
    setProductCategory(product.category)
    setPrices([])
    setError(null)
    void commercialApi.prices(product.id).then(setPrices).catch((failure: unknown) => {
      setError(safeError(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    })
  }

  function editFAQ(faq: FAQ) {
    setSelectedFAQ(faq.id)
    setFaqDraft({ category: faq.category, question: faq.question, answer: faq.answer, is_active: faq.is_active })
  }

  function submitBranch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!branchDraft || role !== 'owner') return
    void run(
      () => commercialApi.updateBranch(branchDraft, csrfToken),
      async () => {
        const value = await commercialApi.branch()
        setBranch(value)
        setBranchDraft({ name: value.name, address: value.address, phone: value.phone, business_hours: value.business_hours })
      },
      'Sucursal actualizada.',
    )
  }

  function submitProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canWrite) return
    const current = products.find((item) => item.id === selectedProduct)
    const action = current
      ? () => commercialApi.updateProduct(current.id, { name: productName, category: productCategory, is_active: current.is_active }, csrfToken)
      : () => commercialApi.createProduct({ name: productName, category: productCategory }, csrfToken)
    void run(action, refreshProducts, current ? 'Producto actualizado.' : 'Producto creado.').then((ok) => {
      if (ok && !current) { setProductName(''); setProductCategory('') }
    })
  }

  function submitPrice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canWrite || selectedProduct === null) return
    const productId = selectedProduct
    void run(
      () => commercialApi.putPrice(productId, priceUnit, priceAmount, csrfToken),
      () => refreshPrices(productId),
      'Precio guardado.',
    )
  }

  function submitFAQ(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canWrite) return
    const action = selectedFAQ === null
      ? () => commercialApi.createFAQ(faqDraft, csrfToken)
      : () => commercialApi.updateFAQ(selectedFAQ, faqDraft, csrfToken)
    void run(action, refreshFAQs, selectedFAQ === null ? 'FAQ creada.' : 'FAQ actualizada.').then((ok) => {
      if (ok && selectedFAQ === null) setFaqDraft(emptyFAQ)
    })
  }

  return (
    <div className="commercial">
      {loading && <p role="status">Cargando datos…</p>}
      {error && <div className="notice notice-error" role="alert">{error}</div>}
      {notice && <div className="notice notice-info" role="status">{notice}</div>}

      {section === 'branch' && branch && branchDraft && (
        <section className="admin-card">
          <h2>Datos de la sucursal</h2>
          <p className="muted">Código fijo de esta instalación: <strong>{branch.code}</strong></p>
          <form className="admin-form" onSubmit={submitBranch}>
            <label htmlFor="branch-name">Nombre</label>
            <input id="branch-name" value={branchDraft.name} maxLength={120} required disabled={role !== 'owner' || busy} onChange={(event) => setBranchDraft({ ...branchDraft, name: event.target.value })} />
            <label htmlFor="branch-address">Dirección</label>
            <input id="branch-address" value={branchDraft.address} maxLength={300} required disabled={role !== 'owner' || busy} onChange={(event) => setBranchDraft({ ...branchDraft, address: event.target.value })} />
            <label htmlFor="branch-phone">Teléfono E.164 (opcional)</label>
            <input id="branch-phone" value={branchDraft.phone ?? ''} maxLength={16} disabled={role !== 'owner' || busy} onChange={(event) => setBranchDraft({ ...branchDraft, phone: event.target.value || null })} />
            <label htmlFor="branch-hours">Horario</label>
            <textarea id="branch-hours" value={branchDraft.business_hours} maxLength={500} required disabled={role !== 'owner' || busy} onChange={(event) => setBranchDraft({ ...branchDraft, business_hours: event.target.value })} />
            {role === 'owner' && <button className="primary-button" disabled={busy}>Guardar sucursal</button>}
          </form>
        </section>
      )}

      {section === 'products' && (
        <div className="admin-grid">
          <section className="admin-card">
            <h2>Productos</h2>
            <div className="admin-list">
              {products.length === 0 && !loading && <p>No hay productos registrados.</p>}
              {products.map((product) => (
                <div className="admin-row" key={product.id}>
                  <div><strong>{product.name}</strong><small>{product.category} · {product.is_active ? 'Activo' : 'Inactivo'}</small></div>
                  <button type="button" onClick={() => editProduct(product)}>Ver</button>
                </div>
              ))}
            </div>
          </section>
          <div className="admin-stack">
            {canWrite && <section className="admin-card">
              <h2>{selectedProduct === null ? 'Nuevo producto' : 'Editar producto'}</h2>
              <form className="admin-form" onSubmit={submitProduct}>
                <label htmlFor="product-name">Nombre</label>
                <input id="product-name" value={productName} maxLength={120} required disabled={busy} onChange={(event) => setProductName(event.target.value)} />
                <label htmlFor="product-category">Categoría</label>
                <input id="product-category" value={productCategory} maxLength={80} required disabled={busy} onChange={(event) => setProductCategory(event.target.value)} />
                <button className="primary-button" disabled={busy}>{selectedProduct === null ? 'Crear producto' : 'Guardar producto'}</button>
              </form>
              {selectedProduct !== null && <div className="admin-actions">
                <button type="button" onClick={() => { setSelectedProduct(null); setProductName(''); setProductCategory(''); setPrices([]) }}>Nuevo</button>
                <button type="button" disabled={busy} onClick={() => {
                  const item = products.find((product) => product.id === selectedProduct)
                  if (!item) return
                  void run(
                    () => item.is_active
                      ? commercialApi.deactivateProduct(item.id, csrfToken)
                      : commercialApi.updateProduct(item.id, { name: item.name, category: item.category, is_active: true }, csrfToken),
                    refreshProducts,
                    item.is_active ? 'Producto desactivado.' : 'Producto reactivado.',
                  )
                }}>{products.find((item) => item.id === selectedProduct)?.is_active ? 'Desactivar' : 'Reactivar'}</button>
              </div>}
            </section>}
            {selectedProduct !== null && <section className="admin-card">
              <h2>Precios del producto</h2>
              <div className="admin-list">
                {prices.map((price) => <div className="admin-row" key={price.id}>
                  <div><strong>{price.amount} MXN</strong><small>por {price.unit}</small></div>
                  {canWrite && <div className="admin-actions">
                    <button type="button" onClick={() => { setPriceUnit(price.unit); setPriceAmount(price.amount) }}>Editar</button>
                    <button type="button" disabled={busy} onClick={() => void run(
                      () => commercialApi.deletePrice(selectedProduct, price.unit, csrfToken),
                      () => refreshPrices(selectedProduct),
                      'Precio eliminado.',
                    )}>Eliminar</button>
                  </div>}
                </div>)}
              </div>
              {canWrite && <form className="admin-form" onSubmit={submitPrice}>
                <label htmlFor="price-unit">Unidad</label>
                <input id="price-unit" value={priceUnit} maxLength={24} required disabled={busy} onChange={(event) => setPriceUnit(event.target.value)} />
                <label htmlFor="price-amount">Precio MXN</label>
                <input id="price-amount" type="text" inputMode="decimal" value={priceAmount} required disabled={busy} onChange={(event) => setPriceAmount(event.target.value)} />
                <button className="primary-button" disabled={busy}>Guardar precio</button>
              </form>}
            </section>}
          </div>
        </div>
      )}

      {section === 'faqs' && (
        <div className="admin-grid">
          <section className="admin-card">
            <h2>Preguntas frecuentes</h2>
            <div className="admin-list">
              {faqs.length === 0 && !loading && <p>No hay FAQ administradas.</p>}
              {faqs.map((faq) => <div className="admin-row" key={faq.id}>
                <div><strong>{faq.question}</strong><small>{faq.category} · {faq.is_active ? 'Activa' : 'Inactiva'}</small></div>
                <button type="button" onClick={() => editFAQ(faq)}>Ver</button>
              </div>)}
            </div>
          </section>
          <section className="admin-card">
            <h2>{selectedFAQ === null ? 'Nueva FAQ' : 'Detalle de FAQ'}</h2>
            <form className="admin-form" onSubmit={submitFAQ}>
              <label htmlFor="faq-category">Categoría</label>
              <select id="faq-category" value={faqDraft.category} disabled={!canWrite || busy} onChange={(event) => setFaqDraft({ ...faqDraft, category: event.target.value as FAQInput['category'] })}>
                {(['general', 'servicios', 'pagos', 'entregas', 'politicas'] as const).map((category) => <option key={category}>{category}</option>)}
              </select>
              <label htmlFor="faq-question">Pregunta</label>
              <input id="faq-question" value={faqDraft.question} maxLength={240} required disabled={!canWrite || busy} onChange={(event) => setFaqDraft({ ...faqDraft, question: event.target.value })} />
              <label htmlFor="faq-answer">Respuesta</label>
              <textarea id="faq-answer" value={faqDraft.answer} maxLength={1200} required disabled={!canWrite || busy} onChange={(event) => setFaqDraft({ ...faqDraft, answer: event.target.value })} />
              {canWrite && <button className="primary-button" disabled={busy}>{selectedFAQ === null ? 'Crear FAQ' : 'Guardar FAQ'}</button>}
            </form>
            {canWrite && selectedFAQ !== null && <div className="admin-actions">
              <button type="button" onClick={() => { setSelectedFAQ(null); setFaqDraft(emptyFAQ) }}>Nueva</button>
              <button type="button" disabled={busy} onClick={() => void run(
                () => faqDraft.is_active
                  ? commercialApi.deactivateFAQ(selectedFAQ, csrfToken)
                  : commercialApi.updateFAQ(selectedFAQ, { ...faqDraft, is_active: true }, csrfToken),
                async () => { await refreshFAQs(); setFaqDraft({ ...faqDraft, is_active: !faqDraft.is_active }) },
                faqDraft.is_active ? 'FAQ desactivada.' : 'FAQ reactivada.',
              )}>{faqDraft.is_active ? 'Desactivar' : 'Reactivar'}</button>
            </div>}
          </section>
        </div>
      )}
    </div>
  )
}
