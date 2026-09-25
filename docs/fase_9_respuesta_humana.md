# F9.3 — Respuesta humana por WhatsApp

El panel permite que el empleado asignado a un chat en modo `HUMAN` redacte, revise y confirme
una respuesta. `POST /api/v1/admin/review/conversations/{id}/messages` exige sesión administrativa
vigente, permiso `conversation:send`, token CSRF, `request_id` UUID v4, texto de 1 a 2000
caracteres y `confirmed=true`. El servicio vuelve a comprobar usuario activo, sucursal configurada,
modo `HUMAN` y asignación exacta. Un propietario de la sucursal debe tomar el chat para enviarlo;
su rol no le permite responder por otro empleado. El panel nunca elige sucursal, número ni instancia.

El destinatario se cifra al recibir cada mensaje nuevo con una subclave derivada de
`CONVERSATION_IDENTITY_KEY`. Se valida contra el HMAC de la conversación y el código de la
instalación antes de enviar. Las conversaciones anteriores a esta migración carecen de destinatario
recuperable: podrán responderse después de un nuevo mensaje entrante. No se guarda destinatario en
claro ni texto saliente en la base; los metadatos de envío guardan actor, sucursal, conversación,
solicitud, estado, hora e ID del proveedor. El `WhatsAppClient` usa la instancia GreenAPI ya
configurada para esta instalación. Un código de sucursal distinto en la configuración bloquea el
envío.

La reserva de `request_id` se confirma en base de datos antes de llamar al proveedor. Una respuesta
con `idMessage` queda `accepted` y crea un metadato de mensaje saliente; significa aceptación en
la cola de GreenAPI, **no entrega al teléfono**. Un timeout u otro fallo ambiguo queda `uncertain`.
En ese caso el chat permanece bloqueado para nuevos envíos y para liberarlo a la IA; requiere
conciliación operativa. Repetir el mismo `request_id` devuelve el estado guardado sin volver a
enviar. No hay reintento automático. El panel avisa de este límite y no conserva el borrador después
del intento.

`GET /api/v1/admin/review/conversations/{id}` muestra `manual_send_blocked` y el último recibo
sin número, texto ni ID del proveedor. La purga de 30 días conserva conversaciones con envíos
`pending` o `uncertain`; el borrado explícito de un remitente elimina también sus recibos. Los
recibos `accepted` se eliminan con la conversación al vencer su retención. Antes de producción hay
que definir un procedimiento de conciliación de resultados inciertos y la operación de la clave de
cifrado. El panel continúa restringido a uso local; F10 debe completarse antes de exponerlo a
internet.
