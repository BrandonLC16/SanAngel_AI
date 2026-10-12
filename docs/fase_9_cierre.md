# Fase 9 — Auditoría y cierre

## Eventos y consulta

Cada solicitud nueva de ayuda humana guarda un evento `help_requested` con actor de sistema y
motivo fijo (`customer_requested` o `ai_unavailable`). Tomar y liberar una conversación guarda
`take` y `release` con el usuario administrativo que ejecutó la transición. Una respuesta manual
guarda `send_pending` al reservar el envío y `send_accepted` o `send_uncertain` al registrar el
resultado. El recibo de envío conserva la relación local entre esos dos eventos. Cada evento se
escribe en la misma transacción que el cambio correspondiente. Una solicitud repetida o un
`request_id` manual repetido no genera otro evento.

El panel de auditoría existente permite filtrar por `conversation` y solo lo consulta un
propietario autenticado de la sucursal configurada. Presenta actor, acción, conversación, fecha,
modo, motivo fijo o estado del envío con ID local de recibo. No devuelve texto, teléfono, destinatario cifrado, HMAC,
ID del proveedor ni credenciales. `send_accepted` confirma únicamente que GreenAPI aceptó el
mensaje en su cola; no confirma entrega, lectura ni respuesta del personal al cliente.

## Retención y borrado

Los eventos de `conversation_audits` vencen 30 días después de `occurred_at`, aun si la
conversación sigue activa. La purga de metadatos también los elimina antes de borrar una
conversación vencida. El borrado individual del remitente elimina los eventos vinculados a su
conversación en la sucursal configurada. La previsualización y el comando `--apply` informan
`auditorias_conversacion` como conteo, sin identificadores personales. Ejecutar la purga de
forma diaria según la [política de privacidad](fase_7_privacidad.md). Los recibos manuales
`pending` y `uncertain` siguen retenidos para conciliación y bloquean el borrado automático de
su conversación; sus eventos de auditoría vencen igualmente a los 30 días.

## Comprobación y límites

Las pruebas locales cubren actor, acciones de solicitud, toma, liberación y envío, lectura con
RBAC y sucursal, ausencia de contenido sensible, restricciones de base de datos, migración,
retención y borrado. No se requiere enviar mensajes reales para validar F9.5.

Antes de aplicar la migración `20261012_0014` a una instalación con datos, detener escrituras y
crear un respaldo SQLite verificado según la [guía de recuperación](fase_7_cierre.md). La
migración añade una tabla nueva y no reconstruye conversaciones anteriores; por ello el historial
comienza con eventos posteriores a su aplicación. La retención de respaldos y copias externas
sigue siendo una responsabilidad operacional separada. El ACK del webhook antes de la tarea de
fondo sigue sin cola durable y requiere atención en una fase posterior.
