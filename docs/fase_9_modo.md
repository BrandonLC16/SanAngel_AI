# F9.1 — Responsable de conversación AI/HUMAN

Cada conversación de WhatsApp tiene un estado persistente por sucursal en
`conversation_responder_states`. `AI` es el modo inicial; `HUMAN` exige exactamente un
`assigned_admin_user_id` de la misma sucursal. La revisión Alembic `20260925_0011` crea la tabla
y asigna `AI` a las conversaciones existentes sin reconstruir `conversations` ni `messages`.

El servicio interno `ConversationModeService` permite estas transiciones:

| Estado | Operación | Resultado |
|---|---|---|
| `AI`, sin respuesta en curso | `take` por `editor` u `owner` activo | `HUMAN`, asignado a ese usuario |
| `AI`, con respuesta en curso | `take` | conflicto; no cambia el responsable |
| `HUMAN` | `take` por otro usuario | conflicto; conserva al asignado |
| `HUMAN` | `release` por el asignado o un `owner` activo | `AI`, sin asignado |
| `HUMAN` | intento de respuesta automática | omitido; no llama al modelo ni envía WhatsApp |

El servicio recibe el alcance desde configuración backend, comprueba la sucursal de la
conversación, el rol y el estado actual del usuario, y usa actualizaciones condicionales en una
transacción. Un principal vencido, `viewer`, inactivo o de otra sucursal no puede cambiar el modo.
Las rutas y botones administrativos de F9.2 obtienen el principal mediante la sesión HTTPS
vigente y exigen CSRF; F9.1 solo incorporó el servicio interno.

El orquestador de WhatsApp reserva una respuesta de IA antes de consultar al modelo. Mientras la
reserva está activa, `take` falla. Después de confirmar el envío y finalizar el recibo del evento,
libera la reserva. Si falla antes de intentar el envío, libera tanto la reserva como el recibo.
Tras un envío ambiguo conserva la reserva y el recibo para conciliación manual: evita transferir
la conversación a un humano mientras pudiera llegar esa respuesta. Una caída en ese punto puede
dejar la conversación bloqueada; no se despeja automáticamente ni se reenvía a ciegas.

La purga y el borrado individual de metadatos eliminan el estado junto con la conversación. La
tabla no almacena texto de mensajes, número de WhatsApp, contraseña ni token. F9.2 incorporó la
[bandeja y los controles de toma/liberación](fase_9_bandeja.md); F9.3 incorporó el
[envío humano](fase_9_respuesta_humana.md) y bloquea la liberación mientras el envío esté
pendiente o incierto. El panel sigue sin
estar preparado para exposición pública hasta F10.
