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
de sucursal y un repositorio de consulta determinista. F3.4 (precios) permanece sin iniciar.

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

## Configuración

`backend.app.core.config` es el único punto de lectura de variables de entorno. Las credenciales
se representan con `SecretStr` y no aparecen en `repr`, serializaciones ni errores de validación.

Variables relevantes:

- `ASSISTANT_BRANCH_CODE`: código inmutable de la única sucursal atendida por esta instalación;
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

La revisión base crea `alembic_version`, la revisión F3.2 crea `branches` y la revisión F3.3 crea
`products`. Cada producto pertenece obligatoriamente a una sucursal e incluye nombre, categoría,
estado activo, timestamps, unicidad de nombre dentro de su sucursal y restricciones de integridad.
Los precios se incorporarán en F3.4. Los cambios de schema deben realizarse mediante migraciones;
el código de aplicación no ejecuta `Base.metadata.create_all()`.

El engine y el `sessionmaker` se construyen de forma lazy. Las sesiones no hacen commit
implícito: cada servicio o repositorio futuro debe definir sus límites transaccionales. Los
archivos SQLite locales y sus sidecars están ignorados por Git. Cada conexión habilita las claves
foráneas de SQLite para que el alcance obligatorio de sucursal también se aplique en la base.

## Catálogo de productos

`ProductRepository` se construye con un objeto `Branch` persistido y no admite `branch_id` ni
`branch_code` en sus métodos. Las altas heredan ese alcance y todas las lecturas, actualizaciones,
bajas y cambios de estado vuelven a filtrarlo o comprobarlo. `list_active()` devuelve únicamente
productos activos de esa sucursal, ordenados de forma estable por categoría, nombre e id.

`ProductData` rechaza campos extra, nombres o categorías vacíos, texto compuesto solo por signos,
caracteres de control y longitudes fuera de los límites. El repositorio de F3.3 es infraestructura
interna; las tools y servicios de consulta para el chatbot se incorporarán en F3.5 sin exponer la
sucursal como argumento.

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
precios y FAQ conservarán el mismo contrato: el código del archivo debe coincidir con el alcance
de la instalación y nunca será un argumento controlado por el cliente o el modelo.

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
