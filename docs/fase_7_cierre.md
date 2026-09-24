# Fase 7 — Cierre y recuperación SQLite

## Alcance comprobado

| Subfase | Resultado |
|---|---|
| F7.1 | Esquema mínimo `conversations`, `messages` y `whatsapp_event_receipts` para WhatsApp. |
| F7.2 | Identidad externa HMAC y sucursal derivada de `ASSISTANT_BRANCH_CODE`. |
| F7.3 | Reserva persistente y única de eventos entrantes, con pruebas de concurrencia. |
| F7.4 | Retención, purga y borrado individual documentados y probados. |
| F7.5 | Agregados FAQ sin texto, contador atómico y consulta interna por sucursal. |

Al cerrar Fase 7, siete revisiones Alembic llegaban a `20260924_0007`. F8.1 añadió la revisión
`20260924_0008` y F8.2 añadió `20260924_0009`; la prueba de recuperación usa la cabecera actual. Las pruebas crean una base vacía,
ejecutan `upgrade head` y `check`, preservan datos existentes al pasar de `20260924_0006` a la
revisión final, prueban el recorrido de migraciones y restauran en otra ruta
un respaldo con datos representativos de las cuatro tablas de Fase 7. La prueba de recuperación
comprueba `integrity_check`, `foreign_key_check`, revisión y filas restauradas; no toca bases reales.

Esta fase entrega la base persistente. El flujo WhatsApp actual aún usa chat simple: no escribe
filas `messages` ni llama al dispatcher de FAQ para generar agregados automáticamente. El panel
administrativo y la cola durable pertenecen a fases posteriores. Estos límites no deben
interpretarse como preparación para producción.

## Plan de backup y restore por instalación

Cada instalación tiene su propio archivo SQLite, `ASSISTANT_BRANCH_CODE` y
`CONVERSATION_IDENTITY_KEY`. Conservar la clave de identidad en un secret manager o respaldo de
secretos separado: sin la misma clave, los HMAC restaurados no conservarán su correlación. El
respaldo de la base contiene identificadores de eventos y claves seudónimas; restringir acceso,
cifrarlo en reposo y mantenerlo fuera del repositorio. Definir propietario, plazo de retención y
eliminación de respaldos antes de producción.

Antes de una migración o recuperación:

Preparar rutas únicas en directorios existentes y con acceso restringido, por ejemplo:

```powershell
$sourceDb = "C:\datos\sucursal-1.db"
$backupDb = "D:\respaldos-protegidos\sucursal-1-$(Get-Date -Format yyyyMMdd-HHmmss).db"
$restoreDb = "D:\ensayo-aislado\sucursal-1-$(Get-Date -Format yyyyMMdd-HHmmss).db"
```

1. Detener webhooks, tareas de fondo y demás escrituras de **esa** instalación; registrar versión
   de aplicación, sucursal y revisión Alembic sin registrar secretos ni mensajes.
2. Revisar recibos `claimed` y envíos ambiguos. La base y GreenAPI no comparten transacción.
3. Crear un respaldo nuevo en una ruta protegida, sin sobrescribir otro archivo:

   ```powershell
   python -m scripts.backup_sqlite --source $sourceDb --destination $backupDb
   ```

4. Ensayar la recuperación en una ruta **nueva y aislada** con la misma API de SQLite, que vuelve
   a verificar integridad y rechaza un destino existente:

   ```powershell
   python -m scripts.backup_sqlite --source $backupDb --destination $restoreDb
   $env:DATABASE_URL = "sqlite+pysqlite:///" + ($restoreDb -replace '\\', '/')
   python -m alembic current
   python -m alembic check
   ```

5. Confirmar `PRAGMA integrity_check = ok`, `PRAGMA foreign_key_check` vacío, revisión esperada,
   código de sucursal configurado y conteos representativos de conversaciones, recibos y preguntas
   no resueltas. Ejecutar una prueba funcional sin GreenAPI ni OpenAI externos. Si falta cualquier
   comprobación, mantener escrituras detenidas y conservar el original.
6. Para una recuperación real, usar un archivo restaurado nuevo y verificado, cambiar
   `DATABASE_URL` de esa instalación, mantener el anterior sin sobrescribir y repetir las
   comprobaciones antes de reanudar. Conciliar eventos posteriores al punto de respaldo y todos
   los `claimed` antes de permitir reentregas: restaurar puede perder recibos recientes y una
   reentrega sin conciliación podría duplicar una respuesta. Nunca usar `downgrade` como restore.

Programar un respaldo diario más uno previo a cada migración y un ensayo de restauración
periódico en un entorno aislado. Medir el tiempo real de recuperación y acordar RPO/RTO con la
operación antes de producción. La automatización, el almacenamiento protegido y la conciliación
de eventos externos siguen siendo tareas operativas pendientes.
