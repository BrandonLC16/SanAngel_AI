# Fase 7 — Política técnica de privacidad de WhatsApp

## Alcance y datos guardados

Esta política cubre las tablas `conversations`, `messages`, `whatsapp_event_receipts` y
`unresolved_questions` del backend. No establece una conclusión de cumplimiento legal ni una
política para las copias externas de GreenAPI, OpenAI o los respaldos operativos.

| Tabla | Campos operativos | No se guarda |
|---|---|---|
| `conversations` | Sucursal, canal, HMAC-SHA256 del `chatId`, creación y última actividad | Número/chat ID en claro, nombre, texto |
| `messages` | Sucursal, conversación, dirección y hora | Texto, archivos, datos de pago; el flujo actual aún no crea filas aquí |
| `whatsapp_event_receipts` | Sucursal, `idMessage` entrante, estado y horas | Remitente, texto, body completo del webhook, ID del envío saliente |
| `unresolved_questions` | Sucursal, motivo FAQ, HMAC-SHA256 de la pregunta normalizada, contador y fechas | Pregunta en claro, remitente, número, conversación, respuesta, argumentos completos |

`CONVERSATION_IDENTITY_KEY` es secreto backend y se mantiene estable por instalación. El `chatId`
solo pasa por memoria para correlacionar la conversación y enviar la respuesta. La configuración
de OpenAI conserva `store=false` por defecto. Los logs de WhatsApp y de la purga registran
categorías, sucursal y conteos; omiten identificadores completos, HMAC, mensajes y secretos.
Omitir el identificador es la redacción preferida. Las pruebas comprueban esa omisión.

La normalización de preguntas no resueltas unifica mayúsculas, acentos, espacios y puntuación
exterior antes de calcular el HMAC con `CONVERSATION_IDENTITY_KEY` y un dominio distinto del de
identidad de remitentes. El índice único por sucursal, motivo y HMAC permite incrementar el
contador sin guardar texto, incluso si la pregunta contiene datos personales. La consulta interna
`UnresolvedQuestionService.list_most_frequent(limit=50)` entrega como máximo 100 agregados de
la sucursal configurada para un panel autorizado futuro. El panel podrá ver frecuencia y motivo,
pero no reconstruir el texto original; la clave HMAC no se registra en logs. La fuente actual es
solo el fallback determinístico de `search_faq` cuando el dispatcher recibe la configuración de
identidad. El flujo WhatsApp vigente usa el chat simple y todavía no invoca ese dispatcher; no se
clasifican respuestas libres del modelo como preguntas no resueltas.
Estos agregados no se vinculan a remitentes, por lo que el borrado individual no puede descontar
una contribución concreta; la purga de 30 días limita su vida útil.

## Plazos

Los plazos siguientes son valores técnicos iniciales y deben revisarse antes de producción con
el responsable de privacidad y las necesidades reales de reentrega de GreenAPI:

| Dato | Retención y acción |
|---|---|
| Conversación | Borrar 30 días después de `updated_at` si no quedan mensajes recientes. Cada mensaje entrante que resuelve la conversación actualiza esa fecha. |
| Metadatos de mensaje | Borrar 30 días después de `occurred_at`, aun si la conversación sigue activa. |
| Recibo `completed` | Borrar 30 días después de `completed_at`. Un evento repetido después de ese plazo podría procesarse otra vez. |
| Recibo `claimed` | No borrar automáticamente. Si lleva más de un día, contarlo para conciliación. Borrarlo sin resolver un envío ambiguo podría causar una segunda respuesta. |
| Pregunta no resuelta agregada | Borrar 30 días después de `last_seen_at`; un registro posterior crea un contador nuevo. |

La purga usa solo la sucursal de `ASSISTANT_BRANCH_CODE`; también se permite purgarla cuando su
perfil está inactivo. Las operaciones se ejecutan en una transacción SQLite. El comando local
primero permite previsualizar conteos y requiere `--apply` para borrar:

```powershell
python -m backend.app.cli.purge_whatsapp_metadata
python -m backend.app.cli.purge_whatsapp_metadata --apply
```

Ejecutar `--apply` diariamente mediante el programador operacional de cada instalación, después
de aplicar las migraciones y configurar `ASSISTANT_BRANCH_CODE` y `DATABASE_URL`. La purga puede
seguir funcionando si falta la clave de identidad; el borrado individual sí la requiere. El
comando informa solo conteos; `reservas_para_revision` nunca se borra de forma automática.
Revisar esas reservas antes de cualquier intervención o reenvío.

## Borrado individual

`WhatsAppPrivacyService.erase_sender(external_user_id)` valida el identificador normalizado,
deriva la misma clave HMAC y elimina la conversación y sus metadatos `messages` de la sucursal
configurada. No hay endpoint público ni argumento CLI que ponga el número en una URL, logs o
historial de comandos. El servicio no puede asociar un recibo con un remitente porque la tabla
deliberadamente no guarda esa relación; los recibos `completed` siguen su plazo de 30 días y
los `claimed` requieren conciliación. El borrado individual puede ejecutarse desde una interfaz
interna autorizada cuando exista, sin ampliar el alcance de esta fase.

SQLite puede conservar bytes antiguos en páginas libres, WAL o respaldos después de un `DELETE`.
La purga es borrado lógico de filas; la sanitización física, la retención de backups y el borrado
de copias externas necesitan un procedimiento operacional separado antes de producción.
