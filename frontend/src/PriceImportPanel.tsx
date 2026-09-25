import { useEffect, useRef, useState, type FormEvent } from 'react'
import { AdminApiError, type AdminRole } from './api'
import { commercialApi, type Branch } from './commercialApi'
import { priceImportApi, type ImportIssue, type ImportPreview, type ImportReceipt } from './priceImportApi'

type Props = { role: AdminRole; csrfToken: string; onExpired: () => void }

const issueText: Record<string, string> = {
  branch_mismatch: 'El archivo corresponde a otra sucursal.',
  branch_unavailable: 'La sucursal de esta instalación no está disponible.',
  invalid_workbook: 'El archivo no es un XLSX válido o contiene elementos no permitidos.',
  invalid_size: 'El archivo está vacío o supera el límite.',
  invalid_sheets: 'Debe contener solo la hoja Precios.',
  invalid_metadata: 'Revisa la versión y el código de sucursal de la plantilla.',
  invalid_headers: 'Los encabezados no coinciden con la plantilla.',
  invalid_positive_integer: 'El ID del producto debe ser un entero positivo.',
  invalid_text: 'El nombre del producto no es válido.',
  invalid_code: 'La unidad no tiene un formato válido.',
  invalid_number: 'El precio debe ser un número de Excel, sin fórmula.',
  out_of_range: 'El precio está fuera del rango permitido.',
  invalid_date: 'La fecha de verificación no es válida.',
  duplicate: 'El producto y la unidad están duplicados.',
  product_unavailable: 'El producto no está activo en esta sucursal.',
  product_name_mismatch: 'El nombre no coincide con el catálogo actual.',
  empty_data: 'La hoja no contiene precios.',
  extra_column: 'Hay una columna adicional no permitida.',
  unexpected_value: 'Hay un valor fuera de las columnas previstas.',
}

function describeIssue(issue: ImportIssue): string {
  const where = issue.row === null ? 'Archivo' : `Fila ${issue.row}${issue.field ? `, ${issue.field}` : ''}`
  return `${where}: ${issueText[issue.code] ?? 'Revisa esta fila de la plantilla.'}`
}

function errorText(error: unknown): string {
  const status = error instanceof AdminApiError ? error.status : null
  switch (status) {
    case 401: return 'Tu sesión expiró. Inicia sesión de nuevo.'
    case 403: return 'No tienes permiso o la verificación CSRF falló.'
    case 409: return 'La vista previa venció o cambió el catálogo. Carga el archivo de nuevo.'
    case 413: return 'El archivo debe medir entre 1 byte y 2 MiB.'
    case 422: return 'Selecciona un archivo .xlsx válido y revisa los datos.'
    default: return 'No se pudo completar la operación. Inténtalo de nuevo.'
  }
}

export function PriceImportPanel({ role, csrfToken, onExpired }: Props) {
  const [branch, setBranch] = useState<Branch | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [receipt, setReceipt] = useState<ImportReceipt | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const canWrite = role === 'editor' || role === 'owner'

  useEffect(() => {
    let active = true
    void commercialApi.branch().then((value) => { if (active) setBranch(value) }).catch((failure: unknown) => {
      if (!active) return
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    })
    return () => { active = false }
  }, [onExpired])

  async function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canWrite || !file || !branch || busy) return
    setBusy(true); setError(null); setPreview(null); setReceipt(null)
    try {
      const result = await priceImportApi.preview(file, csrfToken)
      if (result.branch_code !== branch.code) throw new AdminApiError(null)
      setPreview(result)
    } catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally {
      setBusy(false)
    }
  }

  async function confirm() {
    if (!canWrite || !preview?.is_valid || !preview.preview_id || busy) return
    setBusy(true); setError(null)
    const previewId = preview.preview_id
    setPreview(null)
    try {
      const result = await priceImportApi.confirm(previewId, csrfToken)
      if (result.branch_code !== branch?.code) throw new AdminApiError(null)
      setReceipt(result)
      setFile(null)
      if (fileInput.current) fileInput.current.value = ''
    } catch (failure) {
      setError(errorText(failure))
      if (failure instanceof AdminApiError && failure.status === 401) onExpired()
    } finally {
      setBusy(false)
    }
  }

  return <div className="commercial import-panel">
    {error && <div className="notice notice-error" role="alert">{error}</div>}
    <section className="admin-card">
      <h2>Importar precios desde Excel</h2>
      <p className="muted">Destino fijo: <strong>{branch ? `${branch.name} (${branch.code})` : 'Cargando sucursal…'}</strong>. La plantilla debe usar este código y productos existentes.</p>
      <p>Usa una hoja <strong>Precios</strong> en formato .xlsx, máximo 2 MiB y 1000 filas. La vista previa no modifica precios.</p>
      {canWrite ? <form className="admin-form" onSubmit={(event) => void submitPreview(event)}>
        <label htmlFor="price-import-file">Archivo de precios</label>
        <input ref={fileInput} id="price-import-file" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" disabled={busy || !branch} onChange={(event) => {
          setFile(event.target.files?.[0] ?? null); setPreview(null); setReceipt(null); setError(null)
        }} />
        <button className="primary-button" disabled={busy || !branch || !file}>{busy ? 'Procesando…' : 'Ver vista previa'}</button>
      </form> : <p>Tu perfil solo puede consultar datos; la importación requiere permiso de edición.</p>}
    </section>
    {preview && <section className="admin-card" aria-label="Vista previa de importación">
      <h2>Vista previa</h2>
      <p>Sucursal destino: <strong>{preview.branch_code}</strong></p>
      <p>Altas: {preview.summary.new} · Cambios: {preview.summary.changed} · Sin cambio: {preview.summary.unchanged} · Errores: {preview.summary.errors}</p>
      {preview.issues.length > 0 && <ul className="import-issues">{preview.issues.map((issue, index) => <li key={index}>{describeIssue(issue)}</li>)}</ul>}
      {preview.is_valid && <>
        <div className="import-table-wrap"><table className="import-table"><thead><tr><th>Fila</th><th>Producto</th><th>Unidad</th><th>Actual</th><th>Propuesto</th><th>Verificado</th><th>Acción</th></tr></thead><tbody>{preview.items.map((item) => <tr key={item.source_row}><td>{item.source_row}</td><td>{item.product_name} (#{item.product_id})</td><td>{item.unit}</td><td>{item.current_price_mxn ?? '—'}</td><td>{item.proposed_price_mxn}</td><td>{item.verified_on}</td><td>{item.action === 'new' ? 'Alta' : item.action === 'changed' ? 'Cambio' : 'Igual'}</td></tr>)}</tbody></table></div>
        <p className="muted">Revisa cada importe. La confirmación aplica los cambios de forma transaccional y vence en 10 minutos.</p>
        <button type="button" className="primary-button" disabled={busy} onClick={() => void confirm()}>Confirmar importación</button>
      </>}
    </section>}
    {receipt && <section className="admin-card" role="status">
      <h2>Importación completada</h2>
      <p>Sucursal: <strong>{receipt.branch_code}</strong></p>
      <p>Altas: {receipt.created} · Cambios: {receipt.updated} · Sin cambio: {receipt.unchanged}</p>
      <p>Recibo de auditoría: #{receipt.audit_id}</p>
    </section>}
  </div>
}
