# F10.3 — Secretos y rotación

## Fuente productiva de secretos

Cada instalación recibe credenciales distintas mediante un **secret manager** que monta cinco
archivos de solo lectura en un directorio absoluto, externo al repositorio y al contenido de la
imagen. `SECRETS_DIR` apunta a ese directorio. Docker Swarm Secrets puede montar los archivos en
`/run/secrets`; Kubernetes Secret volumes o un gestor equivalente también sirven si el montaje
mantiene los mismos nombres. El proceso debe tener permiso de lectura; el resto de usuarios y
servicios no deben tenerlo. Dar acceso únicamente al servicio de la sucursal correspondiente.

| Archivo montado | Uso |
|---|---|
| `OPENAI_API_KEY` | Responses API de esa instalación. |
| `GREEN_API_TOKEN_INSTANCE` | API saliente de la instancia GreenAPI. |
| `GREEN_API_WEBHOOK_TOKEN` | Bearer del webhook GreenAPI. |
| `ADMIN_AUTH_KEY` | CSRF y buckets de login administrativo. |
| `CONVERSATION_IDENTITY_KEY` | Identidad y cifrado del destinatario de conversaciones. |

El nombre del archivo es exactamente el de la tabla. Cada archivo debe contener solo el valor,
sin espacios ni salto de línea; tamaño de 1 a 4096 bytes. El directorio y los destinos de sus
enlaces simbólicos deben quedar fuera del repositorio; cada archivo debe permanecer dentro del
montaje. No incluir el montaje en el build context, la imagen, un volumen compartido entre
sucursales, backups generales ni evidencias. `.dockerignore` excluye `.env`, variantes y
directorios `secrets/`; no hay Dockerfile en esta subfase y no se ha construido una imagen.

En producción, `scripts.run_backend` verifica los cinco archivos antes de escuchar, desactiva
dotenv al cargar secretos y rechaza valores secretos en variables de entorno. `APP_ENV=production`,
`ASSISTANT_BRANCH_CODE`, `DATABASE_URL`, `GREEN_API_INSTANCE_ID` y los demás parámetros no
secretos se entregan como variables de entorno del servicio. `SECRETS_DIR` también se entrega
como variable de entorno. No arrancar producción con Uvicorn directo: usar
`python -m scripts.run_backend`. En desarrollo, `.env` local ignorado por Git sigue disponible;
no se deben copiar credenciales de desarrollo a producción. Las instancias cachean la
configuración: una rotación requiere reiniciar **todos** los procesos de esa sucursal y verificar
que no quede ningún proceso con el secreto anterior.

Referencia del mecanismo de montaje: [Docker Swarm secrets](https://docs.docker.com/engine/swarm/secrets/).

## Rotación programada

1. Identificar la sucursal, el secreto, su versión actual y quién tiene acceso. Preparar una
   versión nueva en el gestor; nunca pegarla en comandos, tickets, Git, `.env`, logs ni frontend.
2. **OpenAI:** crear una clave de proyecto nueva con permisos mínimos, actualizar el archivo
   montado, reiniciar la instalación y comprobar una respuesta de prueba sin registrar el texto
   ni la clave. Después eliminar la clave anterior desde la consola de OpenAI. Revisar uso y
   gasto inesperados.
3. **GreenAPI instancia:** cambiar `apiTokenInstance` en la consola de la instancia, actualizar
   `GREEN_API_TOKEN_INSTANCE` en el gestor y reiniciar. Comprobar un envío controlado; el token
   anterior debe dejar de funcionar. Evitar el método beta `updateApiToken` automatizado mientras
   no se valide su estabilidad.
4. **GreenAPI webhook:** generar un Bearer independiente, aleatorio y URL-safe de 32 a 256
   caracteres. Actualizar `GREEN_API_WEBHOOK_TOKEN` y `webhookUrlToken` de la misma instancia en
   la consola/SetSettings, reiniciar y comprobar recepción autenticada. El cambio de SetSettings
   puede tardar hasta cinco minutos; durante el desajuste se devuelven 403 y **no** se confirma
   recepción. Vigilar reintentos y conciliación de mensajes pendientes. No aceptar a la vez el
   token viejo por conveniencia.
5. **Admin:** generar `ADMIN_AUTH_KEY` nuevo e independiente. Ejecutar
   `python -m backend.app.cli.revoke_admin_sessions --apply` con el alcance de la instalación
   configurado; el comando revoca solo sesiones activas de esa sucursal y no imprime tokens.
   Actualizar el archivo montado, reiniciar y verificar que las sesiones previas fallen y que
   un login nuevo funcione. Rotar la clave sola cambia CSRF, pero **no** revoca cookies de sesión.
6. Registrar hora, sucursal, identificadores de versión (nunca valores), comprobaciones y
   revocación de la versión anterior. Retirar permisos del gestor a procesos/operadores antiguos.

[OpenAI documenta la creación y eliminación de claves](https://help.openai.com/en/articles/8304786-keeping-your-openai-account-secure),
[GreenAPI permite cambiar el token de instancia](https://green-api.com/en/docs/before-start/) y
[SetSettings define `webhookUrlToken` y su propagación](https://green-api.com/en/docs/api/account/SetSettings/).

## Credencial comprometida

Revocar **primero** la credencial expuesta en el proveedor o invalidar sesiones admin de inmediato,
aunque cause una interrupción. Para OpenAI, eliminar la clave afectada en el proyecto y revisar
uso/gasto; para GreenAPI, cambiar el token de instancia desde la consola o soporte, y reemplazar
`webhookUrlToken` si se expuso. Para `ADMIN_AUTH_KEY` o una cookie administrativa expuesta,
ejecutar la revocación de sesiones de la sucursal antes del reinicio y cambiar la clave. Revisar
accesos al gestor, Git, logs y despliegues afectados; retirar la versión expuesta en cada lugar
y documentar el incidente sin copiar el secreto. Si hay indicios de abuso del número WhatsApp,
seguir además la [guía de GreenAPI para la cuenta](https://green-api.com/en/docs/faq/how-to-protect-personal-data/).

La mención **Meta** en el plan es histórica: F2.9 cambió el runtime a GreenAPI. Si aún existe
algún token Meta/WhatsApp Cloud API de la integración antigua, identificar su aplicación y
revocarlo en la cuenta administradora de Meta; verificar que ningún proceso lo utilice. No se
introduce una segunda integración Meta ni una variable `META_*` en el runtime actual.

`CONVERSATION_IDENTITY_KEY` no entra en la rotación rutinaria: cambiarla sin migración vuelve
ilegibles los destinatarios cifrados y altera la identidad de conversaciones. Si se compromete,
aislar la instalación y preparar una migración/recuperación específica antes de sustituirla.

## Comprobación de despliegue

Confirmar para cada sucursal: montaje externo de solo lectura, permisos mínimos, nombre exacto
de archivos, arranque por `scripts.run_backend`, ausencia de secretos en entorno y build context,
proceso reiniciado, prueba de webhook y salida, login admin nuevo y sesiones anteriores
revocadas. Las pruebas automáticas de F10.3 usan solo valores ficticios y no verifican un gestor
real ni la revocación remota en las cuentas de proveedor; esas comprobaciones quedan en el
procedimiento operacional de cada despliegue.
