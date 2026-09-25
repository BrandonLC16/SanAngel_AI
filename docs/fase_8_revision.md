# F8.6 — Conversaciones y preguntas no resueltas

El panel ofrece dos vistas de la sucursal configurada por `ASSISTANT_BRANCH_CODE`:

- **Conversaciones:** lista por última actividad, con filtros de fecha y páginas de 25 en la UI.
  El detalle muestra creación, última actividad, conteo de metadatos de mensajes y hasta 50
  marcas de dirección/hora. No muestra teléfono, `chatId`, HMAC ni contenido de mensajes.
- **Preguntas no resueltas:** lista y detalle por motivo, frecuencia y fechas, con filtros de
  motivo y frecuencia mínima. No muestra la pregunta original ni su HMAC. Un `editor` o `owner`
  puede resolver un agregado mediante una FAQ aprobada.

Todas las rutas están bajo `/api/v1/admin/review`, requieren sesión HTTPS y vuelven a comprobar
rol y sucursal dentro del servicio. `GET /conversations` admite `updated_from`, `updated_to`,
`limit` (1–100) y `offset` (0–5000); `GET /conversations/{id}` devuelve detalle mínimo.
`GET /unresolved` admite `reason`, `min_occurrences`, `limit` y `offset`;
`GET /unresolved/{id}` devuelve el mismo agregado mínimo. Una ID de otra sucursal devuelve 404.
Las respuestas de éxito usan `Cache-Control: no-store`.

`POST /unresolved/{id}/resolve` exige permiso comercial de escritura y `X-CSRF-Token`.
El operador debe conocer la pregunta exacta por un canal autorizado; el panel no puede
reconstruirla desde el agregado. El backend normaliza la pregunta y comprueba su HMAC en tiempo
constante contra el registro de esa sucursal. Rechaza formatos evidentes de correo o teléfono
en pregunta y respuesta; esta detección no sustituye la revisión humana de privacidad. Si
coincide, crea o actualiza una FAQ activa y retira el agregado en una sola transacción. El
recibo comercial registra actor, sucursal, FAQ y acción sin texto de pregunta o respuesta; si
falla la auditoría, no se publica la FAQ ni se retira el agregado. Una pregunta que contenga
datos personales no debe copiarse a una FAQ pública; puede elaborarse una FAQ genérica desde la
administración comercial, sin declarar resuelto ese agregado concreto.

El canal WhatsApp actual actualiza la última actividad de las conversaciones, pero todavía no
guarda filas de `messages`. Los agregados FAQ provienen del fallback determinístico de la tool
FAQ cuando se usa el dispatcher; el flujo WhatsApp simple actual aún no la invoca. Por ello el
detalle de una conversación puede mostrar cero metadatos de mensajes y el listado de preguntas
puede estar vacío aun con tráfico. Integrar esa tool en WhatsApp queda fuera de F8.6.
