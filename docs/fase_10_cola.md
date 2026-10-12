# F10.8 — Decisión de cola y worker de WhatsApp

## Medición y decisión

La [documentación de GreenAPI](https://green-api.com/en/docs/api/receiving/technology-webhook-endpoint/)
indica aproximadamente 50 notificaciones por segundo, reintentos a intervalos de un minuto y
entrega durante hasta 24 horas. En este repositorio no hay medidas de tráfico de las siete
instalaciones reales. Se probaron 50 notificaciones sintéticas autenticadas, con proveedores
simulados, en una máquina de desarrollo Windows:

| Flujo | p50 | p95 | Capacidad observada |
|---|---:|---:|---:|
| `BackgroundTasks` anterior, sin E/S real de proveedor | 3,39 ms | 4,26 ms | 264,3 req/s |
| Commit en la nueva cola SQLite, sin ejecutar proveedor | 9,12 ms | 11,85 ms | 97,4 req/s |

Repetir la segunda medición con `.venv\Scripts\python.exe -m scripts.measure_webhook`. Es un
ensayo local secuencial de 50 solicitudes; no demuestra capacidad sostenida, latencia de red,
entrega a clientes ni rendimiento de producción. Medir p95, profundidad de cola, edad del trabajo
más antiguo y tasa de 503 por sucursal en el despliegue real antes de aumentar tráfico.
Una ejecución anterior, antes de agregar la clave HMAC de borrado, midió 8,23 ms de p50,
11,44 ms de p95 y 111,8 req/s; estos valores muestran variación de la máquina de desarrollo.

`BackgroundTasks` no basta para el ACK: vive en el proceso y una caída tras HTTP 200 pierde el
mensaje, que GreenAPI ya considera entregado. Se adopta una **cola transaccional en la SQLite
existente y un worker separado por sucursal**. El ensayo supera el ritmo publicado para la
frontera HTTP y cada instalación ya posee su propio volumen SQLite; no hay evidencia para
introducir Redis ni una base compartida. Si un ensayo sostenido o tráfico real muestra que el
backlog crece, se medirá de nuevo y se decidirá entonces una infraestructura distinta.

## Contrato de ACK e idempotencia

```text
autenticar -> limitar body -> validar instancia y mensaje
           -> cifrar y COMMIT de job único por sucursal + idMessage
           -> ACK 200
worker     -> reclamar job pending de forma atómica
           -> recibo idempotente en whatsapp_event_receipts
           -> OpenAI / GreenAPI
           -> borrar job al completar
```

Eventos no soportados siguen recibiendo ACK sin crear trabajo. Si falta la base, la cola
está saturada, o el commit falla, el webhook devuelve **503 sin ACK** para que GreenAPI lo
reintente. El límite es 5000 trabajos por instalación; no se vacía ni pierde trabajo para abrir
espacio. Un segundo webhook con el mismo ID se ignora cuando existe un job o un recibo, incluso
después de reiniciar. La restricción única de SQLite y el reclamo atómico impiden que dos workers
procesen el mismo job simultáneamente. La sucursal siempre viene de `ASSISTANT_BRANCH_CODE`.

Una caída antes del reclamo deja `pending`, recuperable al reiniciar. Después del reclamo el
estado es `processing`; una excepción pasa a `uncertain`. Si el proceso muere durante el envío,
`processing` permanece para conciliación. **Ninguno de esos dos estados se reenvía
automáticamente**, porque un `sendMessage` ambiguo podría haber sido aceptado. El recibo
persistente `claimed`/`completed` del orquestador sigue siendo la segunda barrera contra
duplicados. No se promete entrega exactamente una vez.

## Operación por instalación

1. Detener la instalación y obtener el respaldo F10.7 **con la versión aún desplegada**, antes
   de sustituir su imagen: la herramienta de respaldo con `--branch-code` exige la revisión
   Alembic de esa imagen. Después ejecutar `alembic upgrade head` de la nueva imagen sobre su
   volumen y comprobar `alembic check`. Aprovisionar el perfil de la misma sucursal antes de
   aceptar webhooks. Desplegar la misma imagen backend para `backend` y `worker`; iniciar un
   worker por proyecto Compose. El worker no publica puertos. No usar `downgrade` para recuperar
   una cola con trabajos pendientes.
2. Inspeccionar localmente con `python -m backend.app.cli.run_whatsapp_worker --status`: solo
   imprime conteos `pending`, `processing` y `uncertain`. `--once` procesa un único job y sirve
   para ensayos controlados. El modo normal consulta la cola cada 250 ms.
3. Vigilar profundidad y edad de `pending`, `processing` antiguo, cualquier `uncertain`, 503 del
   webhook y salud del proceso. Investigar una cola que crece o trabajo `processing` que supera
   los plazos de OpenAI/GreenAPI. El healthcheck de Compose comprueba acceso a la DB; **no**
   demuestra que la cola se esté vaciando. Configurar alertas externas con esos conteos.
4. Ante `processing`/`uncertain`, detener el worker de esa sucursal, cotejar recibos SQLite y
   aceptación/historial de GreenAPI con acceso autorizado. No cambiar el job a `pending` ni
   reenviar sin demostrar que no hubo aceptación. Resolver la atención al cliente mediante el
   flujo humano si el envío no puede acreditarse. Registrar la decisión y retirar el job solo
   tras conciliación, bajo la política de retención y borrado. Reanudar luego el worker.

Los cuerpos de webhook, números y texto no se registran. El job guarda solo ID externo,
sucursal, timestamps, estado y un payload cifrado con una subclave separada de
`CONVERSATION_IDENTITY_KEY`. El mismo secreto de la instalación debe mantenerse disponible para
abrir los jobs pendientes tras reiniciar o restaurar. El job se borra inmediatamente después de
procesarse; los jobs inciertos requieren revisión y borrado dentro del plazo de privacidad de
30 días. El borrado individual del remitente elimina sus jobs `pending` de la sucursal mediante
una clave HMAC opaca; si hay un job ya reclamado o incierto, bloquea el borrado hasta que el
operador detenga el worker y concilie el envío. No rotar la clave de identidad con jobs
pendientes: una clave nueva no puede descifrarlos. La base, su WAL y sus backups se protegen
según [F10.7](fase_10_continuidad.md).
