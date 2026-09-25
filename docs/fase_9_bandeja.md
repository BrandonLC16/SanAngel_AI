# F9.2 — Bandeja de conversaciones

La vista **Conversaciones** del panel muestra las conversaciones de WhatsApp conservadas en la
instalación, ordenadas por última actividad y paginadas. Como todavía no existe un estado de
cierre, «activas» significa que la conversación sigue en la base de datos de la sucursal; la
purga de privacidad puede eliminar las inactivas después de 30 días. Se pueden filtrar por
fechas de actividad, responsable `AI`/`HUMAN` y asignación al usuario actual. El detalle muestra
modo, asignación propia, fechas y metadatos de hasta 50 mensajes. No incluye número, `chatId`,
clave HMAC, texto ni identidad de otro empleado.

`GET /api/v1/admin/review/conversations` añade `mode=AI|HUMAN` y `mine=true|false` a los filtros
de F8.6. `GET /conversations/{id}` incluye los mismos campos de estado. Ambas rutas exigen sesión
HTTPS y permiso de lectura; el servicio vuelve a comprobar usuario activo y sucursal configurada.
Las conversaciones anteriores sin fila de estado se muestran como `AI`; la toma crea esa fila de
manera atómica si falta.

Un `editor` u `owner` puede usar `POST /api/v1/admin/review/conversations/{id}/take` para tomar
un chat en modo `AI` sin respuesta en curso. El asignado, o cualquier `owner` de la misma
sucursal, puede usar `POST /conversations/{id}/release` para devolverlo a `AI`. Las dos rutas
exigen sesión, permiso `conversation:mode:write` y `X-CSRF-Token`; el servicio de F9.1 repite la
autorización y aplica la transición condicional en la base. Una ID de otra sucursal da 404;
una toma concurrente o un cambio incompatible da 409. El panel actualiza la bandeja después
de cada transición y muestra errores si el estado cambió mientras el operador lo veía.

La [respuesta humana por WhatsApp](fase_9_respuesta_humana.md) de F9.3 agrega el envío tras
confirmación y mantiene el chat bloqueado cuando el resultado es incierto. La clave HMAC por sí
sola no permite reconstruir el `chatId`; los mensajes entrantes nuevos guardan el destinatario
cifrado para ese fin. El panel sigue siendo interno y no debe exponerse a internet antes de F10.
