# F9.4 — Solicitud de ayuda humana

El flujo entrante de WhatsApp solicita revisión humana en dos casos cerrados:

- el cliente pide explícitamente hablar con una persona mediante las expresiones reconocidas por
  `human_handoff_policy.py`;
- el proveedor de IA falla o devuelve una respuesta vacía.

El backend ejecuta `request_human_help` con la conversación ya resuelta bajo
`ASSISTANT_BRANCH_CODE`. Guarda solo motivo (`customer_requested` o `ai_unavailable`) y hora en
`conversation_responder_states`. No guarda la pregunta, el teléfono ni una respuesta generada.
La reserva de respuesta de IA debe estar activa para crear el pendiente. Las entregas duplicadas
del webhook usan el recibo persistente existente y no crean otra solicitud. Mientras el pendiente
existe, los mensajes nuevos quedan recibidos sin llamar a la IA ni enviar una respuesta automática.

Después de guardar el pendiente, el cliente recibe un texto fijo que informa la solicitud y aclara
que aún no hay respuesta humana confirmada. Un fallo de persistencia impide enviar ese texto. Si
falla el envío o su resultado es ambiguo, se conserva la reserva existente para conciliación y no
se reintenta automáticamente. El pendiente no asigna un empleado, no cambia el modo a `HUMAN` y
no implica que alguien ya respondió. Un operador autorizado toma el chat mediante la ruta de F9.2;
esa transición limpia el aviso y bloquea a la IA. La respuesta real sigue el proceso confirmado
de F9.3.

La bandeja administrativa muestra primero las conversaciones con solicitud pendiente, su motivo
y hora. El total pendiente de la sucursal se muestra aunque un filtro o la página actual oculte
las conversaciones correspondientes. Se actualiza al abrirla, con el botón **Actualizar solicitudes** y cada 30 segundos
mientras permanece abierta. Solo usuarios con sesión y permiso de lectura de esa sucursal pueden
ver el aviso. El detalle evita texto y datos de contacto. El panel permanece interno hasta F10.

La tool `request_human_help` de F6 conserva su contrato de **propuesta sin ejecución** cuando se
invoca fuera de una conversación de WhatsApp. El orquestador ejecuta la solicitud persistente
desde las reglas anteriores porque posee el contexto de conversación y el alcance backend. Una
respuesta de IA que suena incierta pero contiene texto no se clasifica de forma automática como
fallo; tampoco se interpreta una consulta FAQ desconocida en el canal actual, que aún usa chat
simple. Esos casos requieren datos o señales determinísticas antes de ampliar la regla.
