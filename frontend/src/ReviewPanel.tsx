import { useEffect, useState, type FormEvent } from 'react'
import { AdminApiError, type AdminRole } from './api'
import { reviewApi, type ConversationDetail, type ConversationItem, type ConversationMode, type ResolveFAQInput, type UnresolvedItem } from './reviewApi'

type Props = { section: 'conversations' | 'unresolved'; role: AdminRole; csrfToken: string; onExpired: () => void }
const PAGE_SIZE = 25
const emptyFAQ: ResolveFAQInput = { category: 'general', question: '', answer: '' }

function errorText(error: unknown): string {
  const status = error instanceof AdminApiError ? error.status : null
  switch (status) {
    case 401: return 'Tu sesión expiró. Inicia sesión de nuevo.'
    case 403: return 'No tienes permiso o la verificación CSRF falló.'
    case 404: return 'El registro ya no está disponible en esta sucursal.'
    case 409: return 'El registro cambió o no puede modificarse ahora. Actualiza el detalle.'
    case 422: return 'Revisa los filtros y la FAQ. No incluyas datos personales.'
    default: return 'No se pudo completar la operación. Inténtalo de nuevo.'
  }
}

function formatDate(value: string): string {
  const parsed = new Date(/[zZ]$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`)
  return Number.isNaN(parsed.getTime()) ? 'Fecha no disponible' : parsed.toLocaleString('es-MX')
}

function Conversations({ role, csrfToken, onExpired }: Pick<Props, 'role' | 'csrfToken' | 'onExpired'>) {
  const [updatedFrom, setUpdatedFrom] = useState('')
  const [updatedTo, setUpdatedTo] = useState('')
  const [mode, setMode] = useState<ConversationMode | ''>('')
  const [mine, setMine] = useState(false)
  const [applied, setApplied] = useState({ updatedFrom: '', updatedTo: '', mode: '' as ConversationMode | '', mine: false })
  const [items, setItems] = useState<ConversationItem[]>([])
  const [detail, setDetail] = useState<ConversationDetail | null>(null)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const canWrite = role === 'editor' || role === 'owner'

  async function load(nextOffset: number, filters = applied) {
    setBusy(true); setError(null); setDetail(null)
    try {
      const page = await reviewApi.conversations({ updatedFrom: filters.updatedFrom || undefined, updatedTo: filters.updatedTo || undefined, mode: filters.mode || undefined, mine: filters.mine, offset: nextOffset })
      setItems(page.items); setHasMore(page.has_more); setOffset(nextOffset); setApplied(filters)
    } catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally { setBusy(false) }
  }

  useEffect(() => { void load(0) }, [])

  async function show(id: number) {
    setBusy(true); setError(null); setNotice(null)
    try { setDetail(await reviewApi.conversation(id)) }
    catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally { setBusy(false) }
  }

  async function changeMode(action: 'take' | 'release') {
    if (!canWrite || !detail || busy) return
    const id = detail.id
    setBusy(true); setError(null); setNotice(null)
    try {
      const result = action === 'take' ? await reviewApi.take(id, csrfToken) : await reviewApi.release(id, csrfToken)
      setDetail({ ...detail, mode: result.mode, assigned_to_me: result.assigned_to_me })
      setNotice(action === 'take' ? `Tomaste la conversación #${id}.` : `Liberaste la conversación #${id}.`)
      try {
        const [current, page] = await Promise.all([
          reviewApi.conversation(id),
          reviewApi.conversations({ updatedFrom: applied.updatedFrom || undefined, updatedTo: applied.updatedTo || undefined, mode: applied.mode || undefined, mine: applied.mine, offset }),
        ])
        setDetail(current); setItems(page.items); setHasMore(page.has_more)
      } catch (failure) {
        if (failure instanceof AdminApiError && failure.status === 401) onExpired()
        else setError('El cambio se guardó, pero no se pudo actualizar la bandeja. Usa Filtrar para recargarla.')
      }
    } catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally { setBusy(false) }
  }

  return <div className="commercial review-panel">
    {error && <div role="alert" className="notice notice-error">{error}</div>}
    {notice && <div role="status" className="notice notice-info">{notice}</div>}
    <section className="admin-card">
      <h2>Bandeja de conversaciones activas</h2>
      <p className="muted">Conversaciones conservadas en esta sucursal, ordenadas por actividad. Solo se muestran metadatos; no se guardan números ni contenido de mensajes. La respuesta humana aún no está disponible.</p>
      <form className="review-filters" onSubmit={(event: FormEvent) => { event.preventDefault(); void load(0, { updatedFrom, updatedTo, mode, mine }) }}>
        <label htmlFor="conversation-from">Actividad desde</label>
        <input id="conversation-from" type="date" value={updatedFrom} disabled={busy} onChange={(event) => setUpdatedFrom(event.target.value)} />
        <label htmlFor="conversation-to">Hasta</label>
        <input id="conversation-to" type="date" value={updatedTo} disabled={busy} onChange={(event) => setUpdatedTo(event.target.value)} />
        <label htmlFor="conversation-mode">Responsable</label>
        <select id="conversation-mode" value={mode} disabled={busy} onChange={(event) => setMode(event.target.value as ConversationMode | '')}><option value="">Todos</option><option value="AI">IA</option><option value="HUMAN">Personal</option></select>
        <label htmlFor="conversation-mine">Asignación</label>
        <select id="conversation-mine" value={mine ? 'mine' : 'all'} disabled={busy} onChange={(event) => setMine(event.target.value === 'mine')}><option value="all">Todas</option><option value="mine">Mis chats</option></select>
        <button type="submit" disabled={busy}>Filtrar</button>
      </form>
      <div className="admin-list">
        {items.length === 0 && !busy && <p>No hay conversaciones con estos filtros.</p>}
        {items.map((item) => <div className="admin-row" key={item.id}><div><strong>Conversación #{item.id}</strong><small>{item.mode === 'AI' ? 'IA' : item.assigned_to_me ? 'Personal · asignada a ti' : 'Personal · asignada'} · Última actividad: {formatDate(item.updated_at)}</small></div><button type="button" disabled={busy} onClick={() => void show(item.id)}>Ver detalle</button></div>)}
      </div>
      <div className="admin-actions"><button type="button" disabled={busy || offset === 0} onClick={() => void load(Math.max(0, offset - PAGE_SIZE))}>Anterior</button><button type="button" disabled={busy || !hasMore} onClick={() => void load(offset + PAGE_SIZE)}>Siguiente</button></div>
    </section>
    {detail && <section className="admin-card" aria-label="Detalle de conversación"><h2>Conversación #{detail.id}</h2><p>Canal: WhatsApp · Creada: {formatDate(detail.created_at)} · Última actividad: {formatDate(detail.updated_at)}</p><p>Responsable: {detail.mode === 'AI' ? 'IA' : detail.assigned_to_me ? 'Personal · asignada a ti' : 'Personal · asignada a otra persona'}</p><p>Metadatos de mensajes disponibles: {detail.message_count}</p>{detail.recent_messages.length === 0 ? <p>No hay metadatos de mensajes guardados.</p> : <ul className="review-messages">{detail.recent_messages.map((message, index) => <li key={index}>{message.direction === 'inbound' ? 'Entrante' : 'Saliente'} · {formatDate(message.occurred_at)}</li>)}</ul>}{canWrite && detail.mode === 'AI' && <button type="button" disabled={busy} onClick={() => void changeMode('take')}>Tomar chat</button>}{canWrite && detail.mode === 'HUMAN' && (detail.assigned_to_me || role === 'owner') && <button type="button" disabled={busy} onClick={() => void changeMode('release')}>Liberar chat</button>}</section>}
  </div>
}

function Unresolved({ role, csrfToken, onExpired }: Pick<Props, 'role' | 'csrfToken' | 'onExpired'>) {
  const [reason, setReason] = useState('')
  const [minOccurrences, setMinOccurrences] = useState(1)
  const [applied, setApplied] = useState({ reason: '', minOccurrences: 1 })
  const [items, setItems] = useState<UnresolvedItem[]>([])
  const [detail, setDetail] = useState<UnresolvedItem | null>(null)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [draft, setDraft] = useState<ResolveFAQInput>(emptyFAQ)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const canWrite = role === 'editor' || role === 'owner'

  async function load(nextOffset: number, filters = applied) {
    setBusy(true); setError(null); setDetail(null)
    try {
      const page = await reviewApi.unresolved({ reason: filters.reason || undefined, minOccurrences: filters.minOccurrences, offset: nextOffset })
      setItems(page.items); setHasMore(page.has_more); setOffset(nextOffset); setApplied(filters)
    } catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally { setBusy(false) }
  }

  useEffect(() => { void load(0) }, [])

  async function show(id: number) {
    setBusy(true); setError(null); setNotice(null)
    try { setDetail(await reviewApi.unresolvedDetail(id)); setDraft(emptyFAQ) }
    catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally { setBusy(false) }
  }

  async function resolve(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canWrite || !detail || busy) return
    setBusy(true); setError(null); setNotice(null)
    try {
      const result = await reviewApi.resolve(detail.id, draft, csrfToken)
      setDraft(emptyFAQ); setDetail(null)
      setNotice(`FAQ #${result.faq_id} guardada; agregado #${result.unresolved_id} resuelto.`)
      try {
        const page = await reviewApi.unresolved({ reason: applied.reason || undefined, minOccurrences: applied.minOccurrences, offset })
        setItems(page.items); setHasMore(page.has_more)
      } catch (failure) {
        if (failure instanceof AdminApiError && failure.status === 401) onExpired()
        else setError('La FAQ se guardó, pero no se pudo actualizar la lista. Usa Filtrar para recargarla.')
      }
    } catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally { setBusy(false) }
  }

  return <div className="commercial review-panel">
    {error && <div role="alert" className="notice notice-error">{error}</div>}
    {notice && <div role="status" className="notice notice-info">{notice}</div>}
    <section className="admin-card">
      <h2>Preguntas no resueltas</h2>
      <p className="muted">Se muestran motivo, frecuencia y fechas. La pregunta original no se almacena ni puede reconstruirse desde el panel.</p>
      <form className="review-filters" onSubmit={(event) => { event.preventDefault(); void load(0, { reason, minOccurrences }) }}>
        <label htmlFor="unresolved-reason">Motivo</label>
        <select id="unresolved-reason" value={reason} disabled={busy} onChange={(event) => setReason(event.target.value)}><option value="">Todos</option><option value="faq_unknown">Desconocida</option><option value="faq_ambiguous">Ambigua</option></select>
        <label htmlFor="unresolved-min">Frecuencia mínima</label>
        <input id="unresolved-min" type="number" min={1} max={1000000} value={minOccurrences} disabled={busy} onChange={(event) => setMinOccurrences(Number(event.target.value))} />
        <button type="submit" disabled={busy}>Filtrar</button>
      </form>
      <div className="admin-list">
        {items.length === 0 && !busy && <p>No hay agregados con estos filtros.</p>}
        {items.map((item) => <div className="admin-row" key={item.id}><div><strong>Registro #{item.id} · {item.reason === 'faq_unknown' ? 'Desconocida' : 'Ambigua'}</strong><small>{item.occurrences} ocurrencias · Última: {formatDate(item.last_seen_at)}</small></div><button type="button" disabled={busy} onClick={() => void show(item.id)}>Ver detalle</button></div>)}
      </div>
      <div className="admin-actions"><button type="button" disabled={busy || offset === 0} onClick={() => void load(Math.max(0, offset - PAGE_SIZE))}>Anterior</button><button type="button" disabled={busy || !hasMore} onClick={() => void load(offset + PAGE_SIZE)}>Siguiente</button></div>
    </section>
    {detail && <section className="admin-card" aria-label="Detalle de pregunta no resuelta">
      <h2>Registro #{detail.id}</h2><p>Motivo: {detail.reason === 'faq_unknown' ? 'Desconocida' : 'Ambigua'} · Frecuencia: {detail.occurrences}</p><p>Primera: {formatDate(detail.first_seen_at)} · Última: {formatDate(detail.last_seen_at)}</p>
      {canWrite && <><p className="muted">Para resolverlo, escribe la pregunta exacta obtenida por un canal autorizado y una respuesta aprobada. El servidor comprobará su correspondencia. No incluyas datos personales.</p><form className="admin-form" onSubmit={(event) => void resolve(event)}>
        <label htmlFor="resolve-category">Categoría</label><select id="resolve-category" value={draft.category} disabled={busy} onChange={(event) => setDraft({ ...draft, category: event.target.value as ResolveFAQInput['category'] })}>{(['general', 'servicios', 'pagos', 'entregas', 'politicas'] as const).map((category) => <option key={category}>{category}</option>)}</select>
        <label htmlFor="resolve-question">Pregunta aprobada</label><input id="resolve-question" value={draft.question} maxLength={240} required disabled={busy} onChange={(event) => setDraft({ ...draft, question: event.target.value })} />
        <label htmlFor="resolve-answer">Respuesta aprobada</label><textarea id="resolve-answer" value={draft.answer} maxLength={1200} required disabled={busy} onChange={(event) => setDraft({ ...draft, answer: event.target.value })} />
        <button className="primary-button" disabled={busy}>Guardar FAQ y resolver</button>
      </form></>}
    </section>}
  </div>
}

export function ReviewPanel({ section, role, csrfToken, onExpired }: Props) {
  return section === 'conversations' ? <Conversations role={role} csrfToken={csrfToken} onExpired={onExpired} /> : <Unresolved role={role} csrfToken={csrfToken} onExpired={onExpired} />
}
