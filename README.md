# Carnicería AI Chatbot

Backend en Python para siete asistentes de atención por WhatsApp, uno por sucursal y número. Los
siete usan el mismo código y las mismas instrucciones; cada instalación queda fijada a una
sucursal y solo puede consultar sus datos comerciales determinísticos, para que el modelo no
invente ni mezcle precios, existencias, direcciones, horarios, promociones o pedidos.

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
- idempotencia temporal en memoria;
- ACK separado del procesamiento externo mediante `BackgroundTasks`.

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
datos mínimos aptos para revisión administrativa. Todavía no hay endpoint de administración.

F5.4 incorpora un servicio interno de importación transaccional. Exige un preview revisado y
confirmación explícita, vuelve a validar archivo y catálogo bajo una transacción, y crea o
actualiza únicamente precios de la sucursal configurada. Ante un error revierte toda la carga.
F5.5 añade auditoría persistente a cada intento de confirmación: actor opaco, fecha UTC, huella
SHA-256 del archivo como identificador lógico, sucursal, resultado, conteos y errores seguros.
El recibo enlaza al reporte, que se consulta con alcance de sucursal. El Excel no se guarda en la
base ni en disco. El servicio no está conectado a un endpoint ni al chatbot.
F5.6 cierra la Fase 5 con pruebas de cargas maliciosas y revisión de seguridad del flujo interno.
La futura interfaz administrativa aún debe autenticar al personal y limitar el upload antes de
leerlo completo.

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

Completa las credenciales solamente en `.env`. Ese archivo está ignorado por Git; nunca guardes
tokens reales en archivos versionados, comandos compartidos, logs o documentación.

En cada una de las siete instalaciones configura valores propios para:

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

Copia el resultado directamente a `GREEN_API_WEBHOOK_TOKEN` y al `webhookUrlToken` de GreenAPI.
No lo reutilices como token de instancia ni lo compartas. Un valor anterior de menos de 32
caracteres debe rotarse antes del próximo arranque.

Genera otro valor independiente con el mismo comando para `CONVERSATION_IDENTITY_KEY`. Consérvalo
estable por instalación para que el mismo remitente conserve su conversación.

## Configuración

`backend.app.core.config` es el único punto de lectura de variables de entorno. Las credenciales
se representan con `SecretStr` y no aparecen en `repr`, serializaciones ni errores de validación.

Variables relevantes:

- `ASSISTANT_BRANCH_CODE`: código inmutable de la única sucursal atendida por esta instalación;
- `CONVERSATION_IDENTITY_KEY`: secreto backend-only para derivar la identidad externa opaca;
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
metadatos mínimos del intento, sin conservar el Excel. El código de aplicación no ejecuta
`Base.metadata.create_all()`.

El engine y el `sessionmaker` se construyen de forma lazy. Las sesiones no hacen commit
implícito: cada servicio o repositorio futuro debe definir sus límites transaccionales. Los
archivos SQLite locales y sus sidecars están ignorados por Git. Cada conexión habilita las claves
foráneas de SQLite para que el alcance obligatorio de sucursal también se aplique en la base.

Las pruebas de migración crean una base vacía, recorren las cinco revisiones y verifican que el
esquema coincide con los modelos. Comprueban las restricciones de sucursal, producto y precio,
la reversión de migraciones en una base temporal y el rollback completo de una transacción que
viola una restricción. Un `downgrade` que elimina tablas también elimina sus datos; se usa solo
en pruebas o tras un procedimiento de recuperación aprobado.

### Respaldo previo a una migración productiva

Antes de cualquier futura migración sobre una instalación con datos, detener webhooks, tareas y
otras escrituras, confirmar el archivo SQLite de **esa** instalación y crear un respaldo nuevo en
un directorio protegido fuera del repositorio. Por ejemplo, adaptando ambas rutas a la sucursal:

```powershell
$sourceDb = "C:\datos\sucursal-1.db"
$backupDb = "D:\respaldos-protegidos\sucursal-1-$(Get-Date -Format yyyyMMdd-HHmmss).db"
python -m scripts.backup_sqlite --source $sourceDb --destination $backupDb
```

El comando usa la API de respaldo de SQLite para incluir datos confirmados aun si existe un WAL,
rechaza un origen inexistente y nunca reemplaza un respaldo previo. Exige que
`PRAGMA integrity_check` devuelva `ok` antes de informar éxito. Si falla, no ejecutar la migración. Verificar
además que el respaldo se puede abrir, que corresponde a la sucursal y que la recuperación funciona
en una copia aislada; conservarlo con acceso restringido y según la política de retención antes de
ejecutar `python -m alembic upgrade head`. Después comprobar `current`, `check` y lecturas de
datos representativas antes de reanudar escrituras. Ante un fallo productivo, detener escrituras
y recuperar el respaldo verificado mediante el procedimiento operativo; no usar `downgrade` como
sustituto del respaldo. La automatización de respaldos y restauraciones periódicas pertenece a la
preparación para producción.

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

F2.7 reclama temporal y atómicamente `provider:external_message_id` antes de invocar el chatbot.
Un ID ya reclamado o completado recibe ACK sin otra respuesta. La implementación
`InMemoryIdempotencyStore` guarda como máximo 10000 IDs por proceso y no almacena texto ni
remitentes.

Esta idempotencia no es apta para producción: se pierde al reiniciar, no se comparte entre
procesos y puede volver a aceptar IDs desalojados. Debe sustituirse por almacenamiento persistente
y coordinado antes del despliegue.

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

El servicio de F7.2 aún no está conectado al procesamiento del webhook: esa integración y los
recibos persistentes quedan para F7.3. Antes de guardar contenido conversacional o habilitar
producción se necesita la política de retención y borrado de F7.4.

F2.8 programa una única tarea `BackgroundTasks` por notificación aceptada. OpenAI y GreenAPI se
ejecutan después del ACK HTTP 200, cada mensaje se maneja de forma independiente y no existen
reintentos automáticos. Este mecanismo tampoco es una cola durable: una caída después del ACK
puede perder trabajo.

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
- Un token local que no cumpla la longitud y formato requeridos produce un fallo cerrado; se debe
  rotar el mismo valor en `.env` y en `webhookUrlToken` de GreenAPI antes de reiniciar.
- CORS usa orígenes explícitos y nunca `*`.
- La Fase 2 valida el MVP y no declara el sistema production-ready. Antes de producción faltan,
  entre otros controles, idempotencia persistente, cola durable, HTTPS estable, rate limiting,
  secret manager, rotación operativa de secretos y observabilidad.
- El backend y el túnel temporal están detenidos; la URL `trycloudflare.com` usada en F2.9 ya no
  es válida.

Consulta `docs/fase_2_whatsapp.md` para el diseño vigente y `plan_de_trabajo.md` para el registro
oficial, incluyendo el historial preservado de Meta y la migración a GreenAPI.
