# Carnicería AI Chatbot

Backend en Python para siete asistentes de atención por WhatsApp, uno por sucursal y número. Los
siete usan el mismo código y las mismas instrucciones; cada instalación queda fijada a una
sucursal y solo puede consultar sus datos comerciales determinísticos, para que el modelo no
invente ni mezcle precios, existencias, direcciones, horarios, promociones o pedidos.
El despliegue inicial se limitará a **una sucursal piloto**; las otras seis se evaluarán después
de desplegarla y observar su operación.

## Estado actual

La Fase 1 (F1.1-F1.9) está completada. Incluye FastAPI, configuración validada, health check,
errores HTTP seguros, request ID, logging mínimo, CORS explícito y una integración desacoplada con
OpenAI Responses API.

La Fase 2 conserva sus subfases y contratos internos, pero el proveedor de WhatsApp cambió de
Meta Cloud API a GreenAPI dentro de F2.9. Ya están implementados y probados sin red:

- autenticación del webhook de GreenAPI mediante un token Bearer;
- normalización de mensajes de texto, texto extendido y texto citado;
- cliente saliente de GreenAPI;
- flujo WhatsApp -> chatbot -> WhatsApp;
- idempotencia persistente por sucursal en F7.3;
- ACK después de persistir trabajo cifrado en SQLite y procesamiento por un worker de sucursal.

F2.9 está `✅ COMPLETADO`: la instancia real quedó autorizada, el webhook registrado y el
recorrido WhatsApp -> GreenAPI -> backend -> OpenAI -> GreenAPI -> WhatsApp fue confirmado con un
mensaje real. F2.10 y la Fase 2 están `✅ COMPLETADO`. F3.1 está `✅ COMPLETADO`:
SQLAlchemy, SQLite y Alembic tienen una base reproducible. F3.2 está `✅ COMPLETADO`: implementa
la entidad de sucursal, el alcance fijo por instalación y la carga idempotente de un perfil JSON.
F3.3 está `✅ COMPLETADO`: implementa productos con categoría, estado activo, alcance obligatorio
de sucursal y un repositorio de consulta determinista. F3.4 está `✅ COMPLETADO`: implementa
precios exactos por sucursal, producto y unidad. F3.5 está `✅ COMPLETADO`: implementa servicios
de consulta comercial de solo lectura con alcance de sucursal inyectado. F3.6 y la Fase 3 están
`✅ COMPLETADO`: quedaron verificadas la integridad y reversibilidad de las migraciones y el
procedimiento de respaldo previo a cambios productivos. La Fase 4 está `✅ COMPLETADO` en su
alcance de servicio FAQ local.

F4.1 está `✅ COMPLETADO`: define una tabla FAQ TSV por instalación, con categorías cerradas,
versión y sucursal obligatoria en cada fila. El formato, el ejemplo ficticio y sus reglas de
validación están en
[`docs/fase_4_faq.md`](docs/fase_4_faq.md). F4.2 está `✅ COMPLETADO`: añade carga acotada del TSV
y búsqueda local de solo lectura, sin OpenAI y con el alcance de sucursal inyectado desde backend.
F4.3 está `✅ COMPLETADO`: define una política determinista. Solo una FAQ exacta y única puede
aportar contenido; una pregunta desconocida o ambigua recibe texto fijo y una propuesta de ayuda
humana sin ejecutar el traspaso.
F4.4 está `✅ COMPLETADO`: prueba instrucciones adversariales del cliente y del documento, pedidos
de credenciales y FAQ equivalentes con respuestas en conflicto. La búsqueda y la política usan la
misma clave de pregunta para que esos conflictos produzcan una respuesta ambigua.
F4.5 cierra la fase con una prueba del ejemplo completo a través de la política de respuesta y
la revisión de documentación, seguridad y validaciones. La FAQ todavía no está conectada al
orquestador ni al canal WhatsApp; esa integración corresponde a fases posteriores. No se añadió
RAG: el TSV acotado y la búsqueda determinista cubren el alcance actual.

F5.1 está `✅ COMPLETADO`: define la [plantilla Excel de precios](docs/fase_5_excel.md) por
instalación. El ejemplo versionado contiene solo datos ficticios, un `branch_code` de archivo, ID
y nombre de producto, unidad, precio en MXN y fecha de verificación. F5.2 incorporó un parser
de solo lectura que valida `.xlsx`, tamaño, paquete,
sucursal configurada, cabeceras, tipos, duplicados y rangos, y devuelve errores por fila sin
escribir en la base. F5.3 añade un preview de solo lectura: coteja ID y nombre del producto
dentro de la sucursal configurada y presenta altas, cambios, precios iguales y errores mediante
datos mínimos aptos para revisión administrativa. F8.5 expone este flujo en el panel
autenticado.

F5.4 incorpora un servicio interno de importación transaccional. Exige un preview revisado y
confirmación explícita, vuelve a validar archivo y catálogo bajo una transacción, y crea o
actualiza únicamente precios de la sucursal configurada. Ante un error revierte toda la carga.
F5.5 añade auditoría persistente a cada intento de confirmación: actor opaco, fecha UTC, huella
SHA-256 del archivo como identificador lógico, sucursal, resultado, conteos y errores seguros.
El recibo enlaza al reporte, que se consulta con alcance de sucursal. El Excel no se guarda en la
base ni en disco. F8.5 lo conecta a rutas administrativas; no está conectado al chatbot.
F5.6 cierra la Fase 5 con pruebas de cargas maliciosas y revisión de seguridad del flujo interno.
F8.5 conecta la importación al panel autenticado y limita el upload antes de leerlo completo.

F6.1 define los [contratos estrictos de cuatro tools](docs/fase_6_tools.md) para Responses API:
precio, datos de sucursal, FAQ y propuesta de ayuda humana. La allowlist y los argumentos se
validan en backend antes de asociar la sucursal configurada. F6.2 implementa handlers locales
de solo lectura con resultados tipados y alcance de sucursal; se pueden probar sin modelo.
F6.3 añade un dispatcher con mapa cerrado, validación backend y timeout de espera acotado.
Rechaza `execute_sql` y otros nombres no autorizados antes de abrir la base. F6.4 agrega un
método interno de Responses API que ejecuta tool calls validadas, devuelve sus resultados al
modelo y obtiene una respuesta final, con límites de rondas y pruebas mockeadas. El endpoint
interno de chat y WhatsApp aún no componen ese método con el dispatcher. F6.5 añade
desambiguación determinista de productos con sucursal fija; F6.6 prueba entradas adversariales y
auditoría mínima de tools. F6.7 cierra la fase con una revisión del límite agregado de llamadas,
tokens, timeouts y reintentos. Los topes de aplicación no sustituyen métricas ni presupuesto de
gasto para una futura integración operativa; los detalles están en
[`docs/fase_6_tools.md`](docs/fase_6_tools.md).

Para preparar un archivo local de la sucursal, copia
[`price_import.example.xlsx`](examples/price_import.example.xlsx) con un nombre terminado en
`.assistant-prices.xlsx`, sustituye `branch_code` y elimina o reemplaza las dos filas ficticias.
Ese nombre de archivo está ignorado por Git; la plantilla de ejemplo permanece versionada.

## Modelo de los siete asistentes

Cada número se instala como una instancia independiente del mismo proyecto:

```text
instalación/número 1 -> ASSISTANT_BRANCH_CODE=sucursal-1 -> DB/perfil sucursal 1
instalación/número 2 -> ASSISTANT_BRANCH_CODE=sucursal-2 -> DB/perfil sucursal 2
...
instalación/número 7 -> ASSISTANT_BRANCH_CODE=sucursal-7 -> DB/perfil sucursal 7
```

Este esquema describe la capacidad prevista. El checklist F10.9 y el primer despliegue F10.10
abarcan únicamente la instalación piloto.

El prompt base es único y no contiene datos de una tienda. La identidad de la sucursal proviene
solo de configuración backend. Ni el cliente ni el modelo pueden enviar o cambiar un
`branch_id`/`branch_code`; los servicios de negocio inyectan ese alcance automáticamente.

Para el MVP con SQLite se recomienda un archivo de base de datos distinto por instalación. Esto
añade aislamiento físico al aislamiento lógico del servicio. Si en el futuro se comparte una
base PostgreSQL, todas las consultas deberán continuar filtradas por la sucursal configurada.

## Requisitos y preparación local

- Python 3.12, 3.13 o 3.14.
- `pip` disponible mediante `python -m pip`.

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Para desarrollo local, completa las credenciales solamente en `.env`, ignorado por Git. En
producción, usa el [montaje de un secret manager y el procedimiento de rotación](docs/fase_10_secrets.md):
`SECRETS_DIR` apunta a cinco archivos externos al repositorio y a la imagen. Nunca guardes
tokens reales en archivos versionados, comandos compartidos, logs o documentación.

En cada instalación que se active configura valores propios para:

- `ASSISTANT_BRANCH_CODE`;
- `CONVERSATION_IDENTITY_KEY` para la identidad de conversaciones de F7.2;
- `DATABASE_URL`;
- `GREEN_API_INSTANCE_ID`, `GREEN_API_TOKEN_INSTANCE` y `GREEN_API_WEBHOOK_TOKEN`.

`ASSISTANT_BRANCH_CODE` debe tener de 2 a 48 caracteres en minúsculas, comenzar con letra y usar
solo letras, números o guiones simples. Aunque no es un secreto, fija la frontera de datos y no
debe cambiarse durante una conversación.

Genera un token independiente y URL-safe para el webhook; el siguiente comando produce un valor
de 43 caracteres:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copia el resultado a `GREEN_API_WEBHOOK_TOKEN` en `.env` local o al archivo homónimo del gestor
en producción, y al `webhookUrlToken` de GreenAPI. No lo guardes en el historial del shell.
No lo reutilices como token de instancia ni lo compartas. Un valor anterior de menos de 32
caracteres debe rotarse antes del próximo arranque.

Genera otro valor independiente con el mismo comando para `CONVERSATION_IDENTITY_KEY`. Consérvalo
estable por instalación para que el mismo remitente conserve su conversación y para descifrar el
destinatario de las respuestas humanas. Una rotación cambia el HMAC y hace inaccesibles las
conversaciones anteriores sin una migración; un mensaje entrante posterior inicia otra conversación.

## Configuración

`backend.app.core.config` centraliza la configuración y los secretos montados. Las credenciales
se representan con `SecretStr` y no aparecen en `repr`, serializaciones ni errores de validación.

Variables relevantes:

- `SECRETS_DIR`: ruta absoluta al montaje del gestor en producción;
- `ASSISTANT_BRANCH_CODE`: código inmutable de la única sucursal atendida por esta instalación;
- `CONVERSATION_IDENTITY_KEY`: secreto backend-only para derivar la identidad externa opaca y
  cifrar el destinatario de respuestas humanas;
- `ADMIN_AUTH_KEY`: secreto backend-only independiente para CSRF y límite de login del personal;
- `OPENAI_API_KEY`: clave backend-only para la prueba real del chatbot;
- `OPENAI_MODEL`: modelo configurable, `gpt-5.6` por defecto;
- `OPENAI_STORE_RESPONSES`: `false` por defecto;
- `OPENAI_TIMEOUT_SECONDS`: mayor que 0 y hasta 120 segundos;
- `OPENAI_MAX_RETRIES`: de 0 a 5, con 2 por defecto;
- `DATABASE_URL`: URL SQLite configurable, oculta en representaciones y con
  `sqlite+pysqlite:///./carniceria.db` como valor por defecto;
- `GREEN_API_INSTANCE_ID`: identificador numérico de la instancia GreenAPI;
- `GREEN_API_TOKEN_INSTANCE`: token secreto usado para enviar mensajes;
- `GREEN_API_API_URL`: host HTTPS asignado a la instancia o
  `https://api.green-api.com`; solo se aceptan `green-api.com`, `greenapi.com` y sus
  subdominios;
- `GREEN_API_WEBHOOK_TOKEN`: secreto independiente, aleatorio y URL-safe de 32 a 256 caracteres
  para autenticar el webhook;
- `WHATSAPP_REQUEST_TIMEOUT_SECONDS`: mayor que 0 y hasta 120 segundos, con 15 por defecto;
- `ADMIN_REQUESTS_PER_MINUTE`, `INTERNAL_REQUESTS_PER_MINUTE` y
  `WEBHOOK_REQUESTS_PER_SECOND`: cuotas HTTP por instalación;
- `HTTP_BODY_READ_TIMEOUT_SECONDS`: plazo máximo para leer un cuerpo HTTP;
- `TRUSTED_PROXY_IPS`: lista de IP exactas del proxy conectado directamente; vacía por defecto;
- `CHAT_MAX_MESSAGE_CHARS`: entre 1 y 10000, con 2000 por defecto;
- `CORS_ALLOWED_ORIGINS`: lista separada por comas de orígenes HTTP/HTTPS exactos.

Si falta una credencial requerida por un adaptador, este falla de forma cerrada sin mostrar su
valor. El health check continúa disponible sin credenciales:

```http
GET /health
```

```json
{
  "status": "ok",
  "service": "carniceria-ai-chatbot"
}
```

## Persistencia SQLite y migraciones

F3.1 incorpora SQLAlchemy 2.0 y Alembic. `DatabaseSettings` carga exclusivamente `DATABASE_URL`,
por lo que las migraciones no requieren claves de OpenAI o GreenAPI. La aplicación acepta en esta
fase solo `sqlite` o `sqlite+pysqlite`, sin host, usuario o password en la URL.

Desde la raíz del repositorio:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

La revisión base crea `alembic_version`, la revisión F3.2 crea `branches`, la revisión F3.3 crea
`products` y la revisión F3.4 crea `prices`. Cada producto pertenece obligatoriamente a una
sucursal. Cada precio actual pertenece a la misma sucursal que su producto, usa `NUMERIC(12,2)`,
incluye unidad y timestamps, y es único por sucursal, producto y unidad. Los cambios de schema
deben realizarse mediante migraciones; la revisión F5.5 agrega `price_import_audits` con
metadatos mínimos del intento, sin conservar el Excel. Fase 7 agrega el esquema mínimo de
WhatsApp y los agregados FAQ sin texto. El código de aplicación no ejecuta
`Base.metadata.create_all()`.

El engine y el `sessionmaker` se construyen de forma lazy. Las sesiones no hacen commit
implícito: cada servicio o repositorio futuro debe definir sus límites transaccionales. Los
archivos SQLite locales y sus sidecars están ignorados por Git. Cada conexión habilita las claves
foráneas de SQLite para que el alcance obligatorio de sucursal también se aplique en la base.

Las pruebas de migración crean una base vacía, recorren las quince revisiones y verifican que el
esquema coincide con los modelos. Comprueban las restricciones de sucursal, producto y precio,
la reversión de migraciones en una base temporal y el rollback completo de una transacción que
viola una restricción. Un `downgrade` que elimina tablas también elimina sus datos; se usa solo
en pruebas o tras un procedimiento de recuperación aprobado. F7.6 también prueba un backup y
restore aislado con datos de las cuatro tablas de Fase 7.

### Respaldo previo a una migración productiva

Antes de cualquier futura migración sobre una instalación con datos, detener webhooks, tareas y
otras escrituras, confirmar el archivo SQLite de **esa** instalación y crear un respaldo nuevo en
un directorio protegido fuera del repositorio. Por ejemplo, adaptando ambas rutas a la sucursal:

```powershell
$sourceDb = "C:\datos\sucursal-1.db"
$backupDb = "D:\respaldos-protegidos\sucursal-1-$(Get-Date -Format yyyyMMdd-HHmmss).db"
$branchCode = "sucursal-1"
python -m scripts.backup_sqlite --source $sourceDb --destination $backupDb --branch-code $branchCode
```

El comando usa la API de respaldo de SQLite para incluir datos confirmados aun si existe un WAL,
rechaza un origen inexistente y nunca reemplaza un respaldo previo. Exige integridad, claves
foráneas, sucursal y revisión esperada antes de informar éxito. Si falla, no ejecutar la migración.
Verificar además que la recuperación funciona en una copia aislada; conservarlo con acceso
restringido y según la política de retención antes de
ejecutar `python -m alembic upgrade head`. Después comprobar `current`, `check` y lecturas de
datos representativas antes de reanudar escrituras. Ante un fallo productivo, detener escrituras
y recuperar el respaldo verificado mediante el procedimiento operativo; no usar `downgrade` como
sustituto del respaldo. La [guía de continuidad F10.7](docs/fase_10_continuidad.md) define el
RPO/RTO inicial, la protección de copias, el ensayo y la conciliación antes de reanudar webhooks.

## Catálogo de productos

`ProductRepository` se construye con un objeto `Branch` persistido y no admite `branch_id` ni
`branch_code` en sus métodos. Las altas heredan ese alcance y todas las lecturas, actualizaciones,
bajas y cambios de estado vuelven a filtrarlo o comprobarlo. `list_active()` devuelve únicamente
productos activos de esa sucursal, ordenados de forma estable por categoría, nombre e id.

`ProductData` rechaza campos extra, nombres o categorías vacíos, texto compuesto solo por signos,
caracteres de control y longitudes fuera de los límites. El repositorio de F3.3 es infraestructura
interna; los servicios de consulta de F3.5 usan el mismo alcance sin exponer la sucursal como
argumento.

## Precios exactos por sucursal

`PriceData` representa el importe con `Decimal`, rechaza explícitamente valores `float`, importes
negativos, más de dos decimales, valores fuera de `NUMERIC(12,2)` y campos extra. La unidad es un
código interno de hasta 24 caracteres, normalizado a minúsculas; por ejemplo, `kg`, `piece` o
`package`.

`PriceRepository` se construye con un `Branch` persistido y recibe un objeto `Product` ya resuelto
por backend. No acepta `branch_id` ni `product_id` desde los datos del precio. Todas sus consultas
filtran la sucursal configurada, y la clave foránea compuesta impide guardar un precio con un
producto de otra sucursal incluso si se evita el repositorio. Cada combinación
sucursal–producto–unidad mantiene un único precio actual; `updated_at` registra su última
modificación.

## Consultas comerciales de solo lectura

`BranchScope` se crea desde `AssistantSettings`, cuyo `ASSISTANT_BRANCH_CODE` proviene únicamente
de configuración backend. `CommercialQueryService` recibe ese scope al construirse y expone solo:

- `get_branch_info()`;
- `search_product(query)`;
- `get_product_price(product_id, unit=...)`.

Ningún método acepta `branch_id` ni `branch_code`. `search_product` consulta únicamente productos
activos, normaliza mayúsculas y acentos, y ordena coincidencias exactas, prefijos y coincidencias
parciales de forma determinista. Una búsqueda sin coincidencias devuelve una tupla vacía; un
producto inexistente/inactivo o un precio no disponible producen errores de dominio específicos.

Los resultados son DTOs Pydantic inmutables y separados de las entidades ORM. El servicio no
expone operaciones de escritura, no depende de OpenAI y no registra consultas ni datos completos.
Las tools que conectarán estos servicios con el modelo pertenecen a Fase 6, no a F3.5.

`ProductDisambiguationService.resolve(product_query)` ofrece un resultado de solo lectura para
un término de producto explícito. Informa la sucursal propia, pide precisar entre varias
coincidencias, solicita confirmación ante una sola coincidencia parcial y aclara cuando no hay
producto. Solo una coincidencia exacta única proporciona el ID del producto para una consulta
posterior de precio, que vuelve a filtrar por la misma sucursal. No acepta sucursal elegida por
el cliente ni devuelve precios durante la desambiguación. Todavía no está conectado al flujo de
WhatsApp.

## Carga del perfil personalizado

Cada instalación recibe un archivo JSON propio. Copia el ejemplo y usa un nombre terminado en
`.assistant-profile.json`, que Git ignora:

```powershell
Copy-Item examples\assistant_profile.example.json sucursal-1.assistant-profile.json
```

Edita únicamente datos de la sucursal y asegúrate de que `branch.code` coincida exactamente con
`ASSISTANT_BRANCH_CODE`. Después aplica migraciones, valida el perfil sin escribir y confírmalo:

```powershell
python -m alembic upgrade head
python -m backend.app.cli.provision_assistant --profile .\sucursal-1.assistant-profile.json
python -m backend.app.cli.provision_assistant --profile .\sucursal-1.assistant-profile.json --apply
```

La carga es idempotente: crea la sucursal la primera vez, actualiza sus datos cuando cambian y no
hace nada si el contenido ya coincide. Un perfil de otra sucursal se rechaza antes de escribir.
El comando no muestra dirección, teléfono, horarios, URL de base de datos ni credenciales.

En F3.2 el perfil contiene datos básicos de la sucursal. Las futuras cargas de productos,
precios y FAQ conservarán el mismo contrato: el código de cada registro FAQ debe coincidir con
el alcance de la instalación y nunca será un argumento controlado por el cliente o el modelo.

## Webhook de GreenAPI

GreenAPI debe apuntar `webhookUrl` a:

```text
https://<host-publico>/api/v1/whatsapp/webhook
```

En la configuración de la instancia se debe establecer:

- `incomingWebhook=yes`;
- `webhookUrlToken` con el mismo valor local de `GREEN_API_WEBHOOK_TOKEN`;
- una URL HTTPS pública que reenvíe al backend.

GreenAPI enviará `Authorization: Bearer <token>` en cada notificación. El backend exige una única
cabecera válida, la compara en tiempo constante y lo hace antes de leer el body. `GET` no realiza
un handshake y responde HTTP 405.

Después de autenticarse, el payload se valida con modelos Pydantic tolerantes a campos futuros.
Solo se procesan `incomingMessageReceived` de la instancia configurada y con estos tipos:

- `textMessage`;
- `extendedTextMessage`;
- `quotedMessage` cuando contiene texto extendido.

El mensaje se normaliza al contrato interno `InboundMessage`. Los demás eventos y tipos no
soportados se ignoran con ACK HTTP 200. JSON malformado o una estructura inesperada tampoco
provocan un HTTP 500.

## Cliente saliente de GreenAPI

`WhatsAppClient.send_text` conserva la interfaz usada por el orquestador y envía:

```text
POST {GREEN_API_API_URL}/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN_INSTANCE}
```

Payload:

```json
{
  "chatId": "5210000000000@c.us",
  "message": "Texto de respuesta",
  "linkPreview": false
}
```

También se admiten identificadores de grupo con sufijo `@g.us`. El texto debe tener entre 1 y
20000 caracteres. Una respuesta válida contiene `idMessage`.

GreenAPI exige el token de instancia en el path. Por ello la URL se construye exclusivamente
dentro del backend, los logs de URL de `httpx` y `httpcore` se elevan a nivel `WARNING`, y ninguna
excepción incluye la URL, el token, el destinatario, el texto ni el body del proveedor. El cliente
no sigue redirecciones ni reintenta automáticamente, lo que evita duplicar mensajes tras un
resultado ambiguo.

## Flujo e idempotencia

Cada mensaje aceptado pasa a `MessageOrchestrator`, que consulta el servicio de chat y envía la
respuesta con `WhatsAppClient`. La ruta no conoce OpenAI ni detalles del envío de GreenAPI.

F7.3 usa `PersistentIdempotencyStore` en el flujo real. Reserva el `idMessage` entrante en
`whatsapp_event_receipts` con una inserción atómica y una restricción única por sucursal. Otra
entrega del mismo ID recibe ACK sin generar otra respuesta, incluso con varios procesos o después
de reiniciar. Cada reserva, liberación previa al envío y finalización se confirma en una
transacción SQLite independiente. El servicio de identidad de F7.2 queda conectado después de la
reserva y antes de consultar al chatbot; una carrera del mismo remitente crea una sola
conversación.

Si falla el chatbot antes de enviar, se libera la reserva para permitir un intento posterior. Si
se inició un envío o falló la confirmación del recibo después de enviarlo, la reserva se conserva:
un reintento automático podría duplicar la respuesta. El estado `claimed` requiere conciliación
operativa antes de cualquier reenvío. La base y GreenAPI no comparten una transacción, por lo que
este control evita duplicados automáticos, pero no garantiza entrega exactamente una vez.

F7.1 agrega las tablas `conversations`, `messages` y `whatsapp_event_receipts` mediante Alembic.
La conversación queda ligada a una sucursal y al canal `whatsapp`; su identidad externa es una
clave opaca de 64 caracteres, sin guardar el número de WhatsApp. El mensaje guarda solo dirección
y hora, sin texto. El recibo guarda el identificador del evento y su estado, sin payload del
webhook. Las claves foráneas y restricciones impiden asociar un mensaje a una conversación de
otra sucursal o duplicar un recibo dentro de la misma sucursal.

F7.2 agrega `ConversationIdentityService`: a partir del `sender_id` normalizado del webhook,
calcula una clave HMAC-SHA256 con `CONVERSATION_IDENTITY_KEY` y resuelve la conversación bajo
`ASSISTANT_BRANCH_CODE`. El texto del cliente y el modelo no pueden elegir sucursal. El contexto
devuelto contiene únicamente IDs internos y el código de sucursal; los logs registran sucursal y
estado, sin número, clave opaca ni texto. Configure una clave independiente, aleatoria, URL-safe de
32 a 256 caracteres por instalación y manténgala estable: rotarla sin migrar claves existentes
inicia una identidad de conversación nueva para cada remitente.

F7.4 define una política técnica de [retención, borrado y redacción](docs/fase_7_privacidad.md):
30 días para conversaciones inactivas, metadatos de mensajes y recibos completados. El comando
`python -m backend.app.cli.purge_whatsapp_metadata` muestra candidatos; `--apply` ejecuta la
purga limitada a la sucursal configurada. Las reservas `claimed` no se borran automáticamente y
se informan para revisión. La purga diaria debe programarse por instalación antes de producción.

F7.5 agrega agregados de preguntas FAQ no resueltas por sucursal: normaliza la consulta y guarda
solo un HMAC, motivo, contador y fechas. `UnresolvedQuestionService.list_most_frequent()` permite
consultarlos desde un futuro panel autorizado. La purga de 30 días también los incluye. El
registro se conecta al fallback determinístico de `search_faq` cuando el dispatcher recibe
`unresolved_settings`; el canal WhatsApp actual aún usa el chat simple y no produce estos
agregados automáticamente. Véase la [política de privacidad](docs/fase_7_privacidad.md).

F8.1 agrega autenticación backend para el personal. La contraseña se almacena solo como hash
Argon2id; el login establece una sesión opaca y revocable en una cookie HTTPS segura, y el logout
exige CSRF. Los intentos de login tienen límites persistentes por cuenta y origen directo. El
usuario se crea solo desde una CLI local, sin ruta de registro público. Consulta la
[guía de autenticación](docs/fase_8_auth.md) para configuración, endpoints y límites.

F8.2 agrega roles `viewer`, `editor` y `owner` persistidos por sucursal. Las rutas
`/api/v1/admin/me`, `/users` y `/users/{id}/role` comprueban sesión, rol y sucursal en backend;
el cambio de rol exige CSRF. Los usuarios anteriores reciben `viewer` al migrar y un propietario
inicial debe aprovisionarse localmente con `--role owner`. Cada cambio efectivo de rol deja un
recibo mínimo y transaccional en la base. La
[guía de RBAC](docs/fase_8_rbac.md) detalla permisos y respuestas 401/403/404.

F8.3 añade el [shell React del panel](frontend/README.md): login, sesión, layout de escritorio,
cliente API del mismo origen y mensajes de error.

F8.4 agrega [administración comercial](docs/fase_8_commercial.md) de la sucursal configurada,
productos, precios exactos y FAQ mediante rutas con sesión, RBAC y CSRF. El panel ofrece los
formularios y listas correspondientes. Cada cambio efectivo deja auditoría transaccional;
las FAQ administradas sustituyen por pregunta a las del TSV cuando se usa la tool FAQ.

F8.5 incorpora [la importación Excel del panel](docs/fase_8_import_excel.md). F8.6 agrega
[listados y detalle mínimo](docs/fase_8_revision.md) de conversaciones y preguntas FAQ no
resueltas, con resolución de una FAQ aprobada sin exponer el texto original del agregado.
F8.7 agrega [auditoría administrativa](docs/fase_8_auditoria.md) de cambios comerciales y de
rol, visible solo para propietarios de la instalación. Los precios modificados mediante el panel
o su importación Excel conservan actor, fecha, producto, unidad e importes anterior y nuevo.
F8.8 agrega [pruebas de seguridad del panel](docs/fase_8_seguridad_panel.md) para rutas anónimas,
roles, CSRF, XSS, CORS, límite de login y expiración de sesión.
El [cierre de Fase 8](docs/fase_8_cierre.md) resume las entregas y sus límites. El panel y los
endpoints administrativos deben permanecer locales y restringidos: **no exponerlos a internet
antes de completar F10**, que incluye TLS/proxy, cabeceras de seguridad y controles operativos.

F9.1 incorpora el [modo AI/HUMAN](docs/fase_9_modo.md) por conversación. La transición interna
exige personal autorizado de la misma sucursal; cada modo `HUMAN` tiene un solo usuario asignado.
Una respuesta de IA en curso impide tomar el chat y el modo `HUMAN` impide nuevas respuestas
automáticas. F9.2 agrega la [bandeja de conversaciones](docs/fase_9_bandeja.md) con filtros,
detalle mínimo y toma/liberación bajo sesión, RBAC y CSRF. F9.3 incorpora la
[respuesta humana por WhatsApp](docs/fase_9_respuesta_humana.md) con revisión explícita, envío
desde la instancia configurada y un recibo de aceptación en cola. Los resultados inciertos
bloquean nuevos envíos hasta conciliación; no se afirma entrega al teléfono.
F9.4 agrega [solicitudes de ayuda humana](docs/fase_9_handoff.md): una petición explícita del
cliente o una respuesta de IA fallida/vacía deja un aviso persistente por conversación en la
bandeja de la sucursal. La IA se detiene para ese chat hasta que personal autorizado lo tome.
El acuse al cliente no afirma que alguien haya respondido.

F2.8 usaba `BackgroundTasks` para separar el procesamiento externo del ACK. F10.8 lo sustituyó
por un [inbox SQLite cifrado y un worker por sucursal](docs/fase_10_cola.md): el webhook confirma
solo después del commit, y OpenAI y GreenAPI se ejecutan en el worker. Un envío ambiguo queda
para conciliación, sin reintento automático.

F9.5 cierra la [auditoría de atención humana](docs/fase_9_cierre.md): registra actor y eventos
de solicitud, toma, liberación y envío manual en la misma transacción que sus cambios. El panel
solo muestra metadatos de la sucursal y distingue aceptación en cola de entrega. La
[política de privacidad](docs/fase_7_privacidad.md) borra estos eventos a los 30 días o junto
con su conversación; la purga informa su conteo.

F10.1 añade [límites de solicitudes y cuerpos](docs/fase_10_limites.md) para webhook autenticado,
panel y chat interno. La lectura HTTP tiene timeout; GreenAPI conserva reentrega cuando recibe
429 o 503 y el envío saliente no se reintenta automáticamente. Las cuotas son locales a cada
proceso y no usan encabezados de proxy no confiables.

F10.2 añade [TLS y proxy inverso](docs/fase_10_https.md). En producción, FastAPI rechaza HTTP
antes de leer cuerpos o ejecutar rutas; solo acepta el esquema HTTPS de TLS directo o una única
declaración `X-Forwarded-Proto: https` desde una IP de proxy configurada. Caddy termina TLS y
sirve el panel con CSP bajo el mismo origen. El arranque productivo desactiva la interpretación
automática de cabeceras de proxy de Uvicorn y mantiene el backend en loopback.

F10.3 carga en producción cinco credenciales desde un [secret manager montado fuera del
repositorio y de la imagen](docs/fase_10_secrets.md). El arranque falla si falta alguna; la
rotación exige reiniciar los procesos y revocar la versión anterior. El procedimiento incluye
OpenAI, GreenAPI y sesiones administrativas, además de la revocación de tokens Meta históricos.

F10.4 agrega [métricas operativas y alertas JSON](docs/fase_10_observabilidad.md) de solicitudes,
latencia, fallos OpenAI/GreenAPI y uso de tokens. El costo se estima solo con tarifas explícitas
del modelo configurado; un propietario puede consultar los agregados del proceso por una ruta
administrativa protegida. Los logs usan una referencia opaca en lugar del ID bruto de solicitud.

F10.5 incorpora [escaneo de dependencias y secretos en CI](docs/fase_10_scanning.md) para Python,
el lockfile del panel y la historia Git. Dependabot propone actualizaciones semanales sin merge
automático. El escaneo de secretos solo publica un resultado genérico y no conserva hallazgos.

F10.6 añade [imágenes Docker comunes y despliegue por sucursal](docs/fase_10_docker.md): backend y
panel/Caddy corren sin root, con healthchecks, bases fijadas por digest, dependencias bloqueadas y
contexto de build restringido. Cada una de las siete instalaciones aporta su propia configuración,
secretos montados y volúmenes fuera de las imágenes.

F10.7 añade [respaldo y restauración verificados por sucursal](docs/fase_10_continuidad.md),
con objetivos iniciales RPO de 24 horas y RTO de 4 horas. La guía describe el trabajo diario,
almacenamiento protegido, ensayo mensual y cambio a una base nueva tras verificarla.

F10.8 mide el webhook y adopta una [cola SQLite con worker](docs/fase_10_cola.md) por instalación.
Un error al guardar trabajo devuelve 503 para conservar la reentrega; la cola cifra contenido,
deduplica IDs y acota la capacidad sin añadir Redis.

F10.9 mantiene el [checklist de autorización de producción](docs/fase_10_checklist_produccion.md)
para privacidad, políticas de WhatsApp, controles de OpenAI, DNS/HTTPS, presupuestos, incidentes,
rollback y la matriz de la única instalación piloto. Las otras seis sucursales se evaluarán
después de desplegar y observar el piloto; no requieren aprovisionamiento ni firma en F10.9.
El solicitante aprobó por excepción los campos sin evidencia para cerrar F10.9. Esa aprobación
permite continuar a un despliegue controlado del piloto en F10.10; la apertura a clientes requiere
sus comprobaciones productivas y resolver cualquier hallazgo crítico.

## Servicio OpenAI y chat interno

`OpenAIService` encapsula el cliente asíncrono oficial de Responses API. El modelo, timeout,
reintentos acotados y la opción `store` proceden de configuración. No registra prompts, mensajes
ni respuestas completos.

`POST /api/v1/chat` sirve solo para desarrollo, pruebas e integración interna; no es el canal
público del cliente. Para una prueba local segura:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
python scripts/manual_chat_probe.py --expect success
```

## Validaciones

```powershell
pytest
ruff check .
ruff format --check .
python -m pip check
```

Las pruebas automatizadas bloquean red externa y sustituyen OpenAI y GreenAPI por dobles locales.
Los placeholders de prueba no son credenciales reales.

## Seguridad y límites conocidos

- `.env` y sus variantes locales están ignorados; `.env.example` no contiene secretos.
- Cada runtime exige `ASSISTANT_BRANCH_CODE`; un perfil con otro código se rechaza antes de
  escribir. El repositorio de productos exige una sucursal ya resuelta por backend, no acepta el
  alcance desde los datos del producto y tiene pruebas negativas entre dos sucursales.
- Los importes se conservan como `Decimal`/`NUMERIC(12,2)`, nunca como `float`; la aplicación y la
  base rechazan precios negativos, duplicados inválidos y asociaciones producto-sucursal
  inconsistentes.
- Las consultas comerciales reciben un `BranchScope` creado desde configuración backend. Sus
  firmas no aceptan sucursal, sus resultados son inmutables y las pruebas intentan leer productos
  y precios de otra sucursal para confirmar el rechazo.
- Los archivos `*.assistant-profile.json` reales están ignorados; solo se versiona el ejemplo
  ficticio.
- No se registran bodies, query strings, `Authorization`, textos completos ni identificadores de
  WhatsApp sin redactar.
- La URL configurable de GreenAPI tiene allowlist HTTPS para reducir riesgo SSRF.
- El token del webhook es independiente del token de instancia.
- Un token local que no cumpla la longitud y formato requeridos produce un fallo cerrado. La
  rotación productiva sincroniza el archivo montado y `webhookUrlToken` de GreenAPI según F10.3.
- CORS usa orígenes explícitos y nunca `*`.
- La Fase 2 validó el MVP del canal; F10.8 ya persiste trabajos antes del ACK. Antes de producción
  siguen pendientes la conciliación operativa de reservas ambiguas, pruebas de carga reales,
  rate limiting perimetral, despliegue efectivo del secret manager y entrega de alertas.
- El backend y el túnel temporal están detenidos; la URL `trycloudflare.com` usada en F2.9 ya no
  es válida.

Consulta `docs/fase_2_whatsapp.md` para el diseño vigente y `plan_de_trabajo.md` para el registro
oficial, incluyendo el historial preservado de Meta y la migración a GreenAPI.
