# Carniceria AI Chatbot

Backend en Python para un chatbot de atencion al cliente de una cadena de carnicerias.
El proyecto se construye por fases para mantener los datos comerciales en fuentes
deterministicas y evitar que el modelo invente precios, existencias, direcciones, horarios,
promociones o pedidos.

## Estado actual

La Fase 1 (F1.1-F1.9) esta completada. El repositorio cuenta con una aplicacion FastAPI,
configuracion central validada, health check, errores HTTP seguros, request ID, logging minimo,
CORS configurable y una integracion desacoplada con OpenAI Responses API. El endpoint interno
de chat fue validado con pruebas sin red y con una llamada manual real.

Fase 2 cuenta con la configuracion central de Meta/WhatsApp, el handshake GET, la autenticacion
HMAC-SHA256 del webhook POST y el parser de mensajes de texto. WhatsApp sera el canal principal
del cliente, pero la orquestacion y el cliente de Graph API todavia no estan implementados.

## Health check

`GET /health` responde sin requerir credenciales de proveedor ni llamar a servicios externos:

```json
{
  "status": "ok",
  "service": "carniceria-ai-chatbot"
}
```

## Requisitos

- Python 3.12, 3.13 o 3.14.
- `pip` disponible mediante `python -m pip`.

## Preparacion local

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Completa `OPENAI_API_KEY` solamente en el archivo local `.env` cuando una tarea posterior
requiera una prueba manual. Nunca guardes una clave real en archivos versionados.

## Configuracion

`backend.app.core.config` es el unico punto de lectura de variables de entorno. `HttpSettings`
carga al iniciar solo configuracion HTTP no sensible; `Settings` agrega la credencial y opciones
de OpenAI cuando `OpenAIService` las solicita. Ninguno imprime secretos.

Valores y limites iniciales:

- `OPENAI_API_KEY` es obligatoria y se mantiene como valor secreto;
- `OPENAI_MODEL` es configurable y usa `gpt-5.6` por defecto;
- `OPENAI_STORE_RESPONSES` usa `false` por defecto;
- `OPENAI_TIMEOUT_SECONDS` acepta valores mayores a 0 y hasta 120 segundos;
- `OPENAI_MAX_RETRIES` acepta de 0 a 5 y usa 2 por defecto;
- `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN` y `META_APP_SECRET` son secretos opcionales
  hasta habilitar los adaptadores que los consumen y se mantienen protegidos por `SecretStr`;
- `WHATSAPP_PHONE_NUMBER_ID` es opcional y, cuando se configura, acepta solamente digitos;
- `META_GRAPH_API_VERSION` es configurable y usa `v26.0` como version oficial vigente al
  implementar F2.1;
- `WHATSAPP_REQUEST_TIMEOUT_SECONDS` acepta valores mayores a 0 y hasta 120 segundos, con 15
  segundos por defecto;
- `CORS_ALLOWED_ORIGINS` acepta una lista separada por comas de origenes HTTP/HTTPS exactos;
- `CHAT_MAX_MESSAGE_CHARS` acepta valores entre 1 y 10000, con 2000 por defecto.

Si falta configuración obligatoria, la aplicación genera un error de validación sin incluir el
valor de ninguna credencial.

Sin `CORS_ALLOWED_ORIGINS`, el acceso desde navegador queda deshabilitado. Cada origen debe
contener solo esquema, host y puerto opcional; no se permiten comodines, paths, credenciales,
query strings ni duplicados. `.env.example` incluye exclusivamente los origenes locales de
desarrollo.

La version de Graph API vive en `Settings`; futuros clientes deben construir sus endpoints desde
esa configuracion y no repetir una version hardcodeada. Antes de una prueba real o despliegue se
debe confirmar que la version configurada continue soportada por Meta.

## Handshake del webhook de WhatsApp

`GET /api/v1/whatsapp/webhook` implementa la verificacion inicial solicitada por Meta. Requiere
una unica instancia de `hub.mode=subscribe`, `hub.verify_token` y un `hub.challenge` decimal. Si
el token coincide con `WHATSAPP_VERIFY_TOKEN`, responde como texto plano con solamente el
challenge; solicitudes incorrectas reciben HTTP 403 sin cuerpo. Si el verify token no esta
configurado, el endpoint falla de forma cerrada con HTTP 503 sin cuerpo.

El token se compara de forma segura, no se refleja en respuestas y la aplicacion no registra el
query string.

El mismo path acepta POST y, antes de acceder a JSON, conserva los bytes exactos del body y valida
`X-Hub-Signature-256` mediante HMAC-SHA256 con `META_APP_SECRET`. La firma debe usar el formato
`sha256=<64 caracteres hexadecimales>` y se compara en tiempo constante. Una firma valida recibe
HTTP 200 sin cuerpo; firmas ausentes, duplicadas, malformadas o incorrectas reciben HTTP 403 sin
cuerpo. Si falta el App Secret, responde HTTP 503 sin cuerpo.

Tras autenticarlo, el backend valida la estructura relevante mediante modelos Pydantic tolerantes
a campos futuros. Los mensajes `type=text` se normalizan como `InboundMessage` interno con
provider, message id, sender, texto y timestamp. El texto se recorta y se limita mediante
`CHAT_MAX_MESSAGE_CHARS`; texto vacio o excesivo se ignora.

Webhooks de estado, objetos/cambios ajenos, productos distintos de WhatsApp y tipos no soportados
como imagen, audio, documento, ubicacion, contactos e interactivos se ignoran con ACK HTTP 200.
JSON malformado o estructuras inesperadas tampoco generan HTTP 500. Todavia no se responde al
cliente ni se deduplican mensajes; esas responsabilidades pertenecen a subfases posteriores.

## Servicio OpenAI

`backend.app.services.openai_service.OpenAIService` encapsula el cliente asincrono oficial y
expone una interfaz simple que puede recibir un cliente simulado. Cada solicitud usa Responses
API con el modelo, timeout, reintentos acotados y opcion `store` provenientes de configuracion.
El prompt provisional se versiona en `backend/app/prompts/base_system_prompt.txt`.

Los errores de timeout, limite de solicitudes, conexion, estado HTTP y respuesta vacia se
convierten a excepciones internas seguras. El servicio no registra el prompt, el mensaje ni la
respuesta completos. La conexion desde una ruta HTTP se realiza mediante el servicio de
aplicacion desacoplado.

## Chat interno de desarrollo

`POST /api/v1/chat` sirve exclusivamente para desarrollo, pruebas e integracion interna; no es
el canal final del cliente y no debe exponerse como API publica en produccion.

Request:

```json
{
  "message": "Hola"
}
```

Response:

```json
{
  "answer": "..."
}
```

El mensaje no puede estar vacio ni superar `CHAT_MAX_MESSAGE_CHARS`. Las solicitudes invalidas
responden HTTP 422 sin devolver el contenido rechazado y los fallos del proveedor responden
HTTP 503 con un mensaje publico estable.

## Prueba manual local

Guarda `OPENAI_API_KEY` solamente en `.env` o en el entorno del proceso local. No escribas la
clave en comandos compartidos, logs, documentación ni evidencias. Inicia el backend:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal ejecuta el probe seguro:

```powershell
python scripts/manual_chat_probe.py --expect success
```

El probe solo acepta el endpoint loopback, no imprime la respuesta del modelo y reporta
únicamente estado HTTP, presencia de request ID y longitud de la respuesta.

La prueba exitosa requiere que `OPENAI_API_KEY` tenga un valor válido en un `.env` local. Si el
archivo no existe, créalo a partir de `.env.example`; `.env` está ignorado y Codex no crea,
solicita ni copia credenciales reales.
Si el proveedor responde HTTP 429, revisa la cuota, facturación y límites del proyecto antes de
repetir la prueba; el backend devolverá únicamente su error público HTTP 503.

## Frontera HTTP

- `X-Request-ID` se conserva si es valido o se genera de forma segura y se devuelve en la
  respuesta;
- las excepciones internas se convierten a un JSON estable con codigo publico y request ID;
- los errores inesperados responden HTTP 500 sin traceback ni detalle interno;
- los logs incluyen request ID, metodo, plantilla de endpoint, estado, duracion y categoria;
- no se registran body, query string, headers ni `Authorization`.

## Validaciones disponibles

```powershell
pytest
ruff check .
ruff format --check .
python -m pip check
```

`pytest` activa una barrera global que rechaza resolución DNS y conexiones a direcciones no
loopback. Las pruebas HTTP en proceso siguen funcionando y OpenAI se sustituye por dobles de
prueba. Los valores que ocupan el lugar de credenciales son placeholders explícitos, nunca
claves reales.

## Estructura base

```text
backend/
  app/
    api/routes/
    core/
    prompts/
    schemas/
    services/
  tests/
docs/
```

Consulta `docs/fase_1_diseno.md` para el diseño de la fase activa y
`plan_de_trabajo.md` para el estado oficial de cada tarea.

## Seguridad

- La API key de OpenAI es utilizada solo por el backend y se carga desde el entorno.
- `.env` y sus variantes locales están ignorados; `.env.example` no contiene secretos.
- Las pruebas automatizadas normales no deben invocar servicios externos ni consumir créditos.
- CORS utiliza origenes explicitos y no permite `*`, incluso fuera de produccion.
