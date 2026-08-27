# Diseño técnico — Fase 2
## WhatsApp como interfaz principal del cliente

**Fecha:** 2026-08-25  
**Actualizado:** 2026-08-27
**Estado:** F2.1-F2.6 completadas; subfases posteriores pendientes.

---

# 1. Objetivo

Conectar el núcleo construido en Fase 1 con WhatsApp Business Platform / Cloud API para que:

1. un cliente envíe un mensaje por WhatsApp;
2. Meta notifique al backend mediante webhook;
3. el backend valide y normalice el evento;
4. el chatbot genere una respuesta;
5. el backend envíe la respuesta mediante Graph API;
6. el cliente la reciba en WhatsApp.

---

# 2. Arquitectura

```text
Cliente
   |
   v
WhatsApp
   |
   v
Meta
   |
   | HTTPS webhook
   v
FastAPI
   |
   v
WhatsAppWebhookService
   |
   v
MessageOrchestrator
   |
   +--------------------------+
   |                          |
   v                          v
Chatbot/OpenAI            Business services
   |                          |
   +------------+-------------+
                |
                v
        WhatsAppClient
                |
                v
        Meta Graph API
                |
                v
             Cliente
```

---

# 3. Fronteras y responsabilidades

## WhatsApp route

Responsable de:

- handshake GET;
- recibir POST;
- obtener raw body;
- validar autenticidad;
- responder HTTP apropiadamente.

NO responsable de:

- prompts;
- lógica comercial;
- consultar precios;
- construir conversaciones directamente.

## WhatsAppWebhookService

- validar evento;
- parsear únicamente estructuras soportadas;
- normalizar evento.

Ejemplo interno:

```text
InboundMessage
- provider = whatsapp
- external_message_id
- sender_id
- message_type
- text
- timestamp
```

## MessageOrchestrator

- determinar si el evento requiere respuesta;
- invocar chatbot;
- invocar servicios comerciales cuando se incorporen;
- pedir envío.

## WhatsAppClient

- enviar mensajes;
- timeout;
- errores de Graph API;
- tokens en headers;
- nunca exponerlos al dominio.

---

# 4. Variables previstas

Agregar únicamente cuando empiece F2.1:

```env
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
META_APP_SECRET=
META_GRAPH_API_VERSION=v26.0
WHATSAPP_REQUEST_TIMEOUT_SECONDS=15
```

No inventar valores sensibles. Los secretos permanecen opcionales en `Settings` hasta que se
habilite el adaptador que los consume; cuando se configuran se validan y se protegen con
`SecretStr`. `WHATSAPP_PHONE_NUMBER_ID` acepta un identificador numérico y el timeout está
acotado a un máximo de 120 segundos.

`META_GRAPH_API_VERSION` se centraliza en `Settings`. El default `v26.0` corresponde a la versión
más reciente declarada por el
[changelog oficial de Graph API](https://developers.facebook.com/docs/graph-api/changelog/) al
implementar F2.1 (introducida el 2026-07-29). Debe confirmarse nuevamente antes de una prueba real
o despliegue porque el ciclo de versiones de Meta es externo al repositorio.

---

# 5. Seguridad del webhook

## Handshake GET

Validar los parámetros requeridos por Meta y comparar el verify token configurado.

No loguearlo.

F2.2 expone `GET /api/v1/whatsapp/webhook`. Exige una sola instancia de `hub.mode`,
`hub.verify_token` y `hub.challenge`; el modo debe ser `subscribe` y el challenge un entero
decimal acotado. El token se compara en tiempo constante contra `WHATSAPP_VERIFY_TOKEN`.

Una solicitud válida devuelve únicamente el challenge como texto plano. Mode, token o challenge
inválidos reciben HTTP 403 sin cuerpo; la ausencia de configuración del verify token recibe HTTP
503 sin cuerpo. La ruta y el middleware no registran el query string ni el token. Esta subfase no
implementa el método POST.

## POST

Tratar el webhook como endpoint público hostil.

Antes de procesar:

1. obtener raw body;
2. validar firma oficial vigente;
3. cuando corresponda `X-Hub-Signature-256`, comprobar HMAC-SHA256 con `META_APP_SECRET`;
4. comparación segura;
5. parsear JSON;
6. validar schema;
7. ignorar eventos no soportados.

No confiar en que un payload tiene forma correcta solo porque es JSON.

F2.3 implementa `POST /api/v1/whatsapp/webhook`. La ruta obtiene el body crudo mediante
`Request.body()` y no accede a JSON antes de autenticarlo. Exige exactamente un header
`X-Hub-Signature-256` con formato `sha256=<64 hex minúsculas>`, calcula HMAC-SHA256 sobre esos
bytes con `META_APP_SECRET` y compara los digests mediante `hmac.compare_digest`.

Una firma válida permite continuar hasta un ACK HTTP 200 sin cuerpo. Firma ausente, duplicada,
malformada, calculada con otro secreto o correspondiente a otros bytes recibe HTTP 403 sin
cuerpo. Si `META_APP_SECRET` no está configurado, la ruta falla cerrada con HTTP 503 sin cuerpo.
Ni body, firma ni secreto se registran o reflejan.

F2.4 agrega modelos Pydantic mínimos y tolerantes a campos extra para `object`, `entry`,
`changes`, `value`, `messages` y `text`. `WhatsAppWebhookService` procesa únicamente
`object=whatsapp_business_account`, cambios `field=messages`, `messaging_product=whatsapp` y
mensajes `type=text`.

Cada texto válido produce un `InboundMessage` interno con provider, message id, sender, texto y
timestamp. Se eliminan espacios exteriores y se aplica `CHAT_MAX_MESSAGE_CHARS`, con un máximo
estructural absoluto de 10000 caracteres. Texto vacío o excesivo se ignora.

Eventos con `statuses`, objetos/cambios no relevantes y tipos no soportados se ignoran. JSON
malformado, roots inesperados, campos con tipos incorrectos o estructuras futuras no producen
HTTP 500: el parser devuelve cero mensajes y la ruta autenticada conserva ACK HTTP 200. El raw
body, sender y texto no se registran.

Esta subfase solo normaliza; no deduplica, orquesta ni envía respuestas.

---

# 6. Idempotencia

Los webhooks pueden repetirse.

Usar el ID externo del mensaje/evento.

Durante desarrollo puede existir una interfaz:

```text
IdempotencyStore
```

con implementación temporal en memoria.

Antes de producción debe usar almacenamiento persistente.

---

# 7. ACK rápido

El endpoint webhook no debe realizar trabajo arbitrariamente largo antes de responder.

Diseñar separación entre:

```text
recepción/verificación
```

y:

```text
procesamiento
```

Para MVP local puede utilizarse un mecanismo simple y probado.

Antes de producción evaluar una cola/worker si el volumen, latencia o garantías de entrega lo requieren.

---

# 8. Privacidad

El número/identificador de WhatsApp se trata como dato personal.

Logs:

```text
permitido: ******1234
evitar:    +5218112345678
```

No persistir conversaciones completas hasta que exista política de retención definida en la fase correspondiente.

---

# 9. Tipos de mensajes

Primero soportar únicamente texto.

Para otros tipos:

- imagen;
- audio;
- ubicación;
- documento;
- contacto;

responder de forma controlada o ignorarlos según regla explícita.

No intentar procesarlos como texto accidentalmente.

---

# 10. Envío

`WhatsAppClient` debe:

- construir endpoint con base/version/phone-number-id de configuración;
- enviar token en header;
- validar destinatario;
- enviar payload estructurado;
- aplicar timeout;
- mapear errores;
- ser mockeable;
- evitar logs con token o cuerpo sensible.

F2.5 implementa `WhatsAppClient.send_text` con `httpx` asíncrono y cliente HTTP inyectable. El
endpoint se construye únicamente como
`https://graph.facebook.com/{META_GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages`; la base
no es configurable por input externo. El access token permanece backend-only y se envía solo en
`Authorization: Bearer`.

El payload usa `messaging_product=whatsapp`, `recipient_type=individual`, `type=text`, destinatario
validado y objeto `text` con `preview_url` explícito. El texto se normaliza, no admite blancos y se
limita a 4096 caracteres. Una respuesta exitosa se valida y devuelve el message ID de Meta.

El timeout procede de `WHATSAPP_REQUEST_TIMEOUT_SECONDS`. El cliente no sigue redirecciones ni
reintenta automáticamente; timeout, conexión, HTTP 429, otros estados no exitosos y respuestas
inválidas se mapean a excepciones internas seguras. Token, destinatario, texto y respuesta del
proveedor no se registran ni se incorporan a errores. El cliente propio puede cerrarse mediante
`aclose()` o context manager; uno inyectado permanece bajo control del caller.

F2.5 no conecta todavía el cliente con el webhook o el chatbot.

F2.6 agrega `MessageOrchestrator` como frontera de aplicación entre el mensaje normalizado,
`ChatService` y `WhatsAppClient`. El orquestador recibe un `InboundMessage`, obtiene la respuesta
mediante la interfaz de chat y solicita el envío al mismo `sender_id` mediante una interfaz de
salida mockeable. La ruta no importa ni invoca OpenAI o Graph API directamente.

La composición de adaptadores es perezosa: solo ocurre después de validar la firma y cuando el
parser produjo al menos un mensaje soportado. Los fallos conocidos de aplicación se convierten en
`MessageProcessingError`, con HTTP 503 y representación pública fija; mensaje, respuesta,
destinatario y detalle del proveedor no se reflejan ni registran.

El procesamiento de F2.6 permanece dentro de la solicitud y es secuencial para lotes. No incorpora
deduplicación, tareas de background, colas ni reintentos: F2.7 y F2.8 permanecen pendientes.

---

# 11. Mensajes fuera de conversación de servicio / plantillas

Antes de implementar mensajes iniciados por el negocio, promociones o seguimientos:

- revisar reglas y ventanas vigentes de WhatsApp;
- utilizar plantillas aprobadas cuando corresponda;
- no asumir que una respuesta libre es válida indefinidamente;
- documentar categoría/consentimiento cuando aplique.

Fase 2 se concentra inicialmente en responder mensajes iniciados por el cliente.

---

# 12. Pruebas obligatorias

- handshake válido;
- handshake inválido;
- firma POST válida;
- firma POST inválida;
- JSON inválido;
- evento sin mensaje;
- mensaje de texto;
- mensaje duplicado;
- tipo no soportado;
- envío correcto mockeado;
- error Graph API;
- timeout;
- ningún token en logs/excepciones.

Las pruebas automáticas no llaman a Meta.

---

# 13. Definition of Done

Fase 2 solo termina cuando:

- webhook está verificado;
- POST valida autenticidad;
- texto entrante se normaliza;
- mensaje de respuesta puede enviarse;
- flujo WhatsApp -> chatbot -> WhatsApp funciona en entorno de prueba;
- idempotencia mínima existe;
- errores son seguros;
- tokens no aparecen en Git/logs;
- tests pasan;
- README/plan actualizados.
