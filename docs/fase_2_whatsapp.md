# Diseño técnico — Fase 2
## WhatsApp mediante GreenAPI

## 1. Estado y alcance

F2.1-F2.8 permanecen registradas como completadas porque establecieron configuración, webhook,
normalización, cliente saliente, orquestación, idempotencia y separación del ACK. La migración
solicitada de Meta Cloud API a GreenAPI se registra dentro de F2.9 y reemplaza únicamente los
adaptadores de frontera.

Se mantienen sin cambios los contratos internos:

```text
InboundMessage
    -> MessageOrchestrator
        -> ChatService
        -> WhatsAppClient.send_text(recipient, text)
```

F2.9 está `✅ COMPLETADO` después de completar una prueba real:

```text
WhatsApp -> GreenAPI -> webhook -> OpenAI -> GreenAPI -> WhatsApp
```

## 2. Arquitectura

```text
Cliente de WhatsApp
        |
        v
     GreenAPI
        |
        | POST HTTPS + Authorization: Bearer <webhook token>
        v
/api/v1/whatsapp/webhook
        |
        v
WhatsAppWebhookService
        |
        | InboundMessage
        v
BackgroundTasks -> MessageOrchestrator
                       |              |
                       v              v
                 OpenAIService   WhatsAppClient
                                      |
                                      v
                            GreenAPI sendMessage
```

La ruta autentica y normaliza. El orquestador coordina. Los adaptadores externos están aislados
en servicios. La ruta no contiene llamadas directas a OpenAI ni construye endpoints de GreenAPI.

## 3. Configuración

```dotenv
GREEN_API_INSTANCE_ID=
GREEN_API_TOKEN_INSTANCE=
GREEN_API_API_URL=https://api.green-api.com
GREEN_API_WEBHOOK_TOKEN=
WHATSAPP_REQUEST_TIMEOUT_SECONDS=15
```

Reglas:

- `GREEN_API_INSTANCE_ID` contiene de 1 a 20 dígitos y no empieza con cero;
- `GREEN_API_TOKEN_INSTANCE` es `SecretStr` y acepta únicamente caracteres seguros para path;
- `GREEN_API_WEBHOOK_TOKEN` es `SecretStr`, se compara de forma exacta y nunca se registra;
- `GREEN_API_API_URL` exige HTTPS, sin credenciales, path, query o fragment;
- el host debe ser `green-api.com`, `greenapi.com` o uno de sus subdominios, incluido el host
  asignado a la instancia;
- el timeout es mayor que cero y no supera 120 segundos.

No hay fallback a variables de Meta. La ausencia de configuración requerida produce un fallo
cerrado y seguro. `.env` no se versiona y `.env.example` solo contiene valores vacíos o públicos.

## 4. Configuración de la instancia GreenAPI

En `SetSettings` o en la consola de GreenAPI se debe establecer:

```json
{
  "webhookUrl": "https://<host-publico>/api/v1/whatsapp/webhook",
  "webhookUrlToken": "<mismo valor que GREEN_API_WEBHOOK_TOKEN>",
  "incomingWebhook": "yes"
}
```

El token del webhook debe ser distinto del token de instancia. Si `webhookUrlToken` está
configurado, GreenAPI agrega el encabezado `Authorization` a las notificaciones. Este proyecto usa
el esquema documentado `Bearer AuthToken`.

GreenAPI no requiere el handshake GET de Meta. Por lo tanto, el endpoint expone únicamente POST;
un GET responde 405.

Referencias oficiales:

- [configuración SetSettings](https://green-api.com/en/docs/api/account/SetSettings/);
- [webhook endpoint](https://green-api.com/en/docs/api/receiving/technology-webhook-endpoint/);
- [formato de mensajes entrantes](https://green-api.com/en/docs/api/receiving/notifications-format/incoming-message/Webhook-IncomingMessageReceived/).

## 5. Autenticación del webhook

El endpoint es público y todo input es no confiable. El orden obligatorio es:

1. comprobar que `GREEN_API_WEBHOOK_TOKEN` y `GREEN_API_INSTANCE_ID` estén configurados;
2. exigir exactamente un valor de `Authorization` y limitar su tamaño;
3. comparar en tiempo constante `Bearer <GREEN_API_WEBHOOK_TOKEN>`;
4. rechazar con HTTP 403 antes de leer el body cuando la autenticación es inválida;
5. leer y parsear JSON solo después de autenticar;
6. validar el esquema e instancia;
7. programar trabajo únicamente para mensajes admitidos.

Si la configuración local falta, se responde HTTP 503 sin detalle. Los errores de autenticación
no reflejan tokens ni contenido.

## 6. Parsing y normalización

Solo se acepta:

- `typeWebhook=incomingMessageReceived`;
- `instanceData.typeInstance=whatsapp`;
- `instanceData.idInstance` igual a `GREEN_API_INSTANCE_ID`;
- un `idMessage` no vacío;
- un `senderData.chatId` válido con sufijo `@c.us` o `@g.us`;
- un timestamp entero no negativo.

Tipos admitidos:

| `typeMessage` | Campo de texto |
|---|---|
| `textMessage` | `textMessageData.textMessage` |
| `extendedTextMessage` | `extendedTextMessageData.text` |
| `quotedMessage` | `quotedMessage.extendedTextMessageData.text` |

El texto se recorta y debe respetar `CHAT_MAX_MESSAGE_CHARS`. Un texto vacío, excesivo o con
estructura inválida se ignora con ACK HTTP 200. También se ignoran estados, mensajes salientes,
media, ubicaciones, contactos y futuros tipos no soportados.

El resultado interno es:

```text
InboundMessage(
  provider="whatsapp",
  external_message_id=idMessage,
  sender_id=senderData.chatId,
  text=<texto normalizado>,
  timestamp=<timestamp UTC>
)
```

Mantener `provider="whatsapp"` evita acoplar idempotencia y orquestación al proveedor de
transporte.

## 7. ACK y procesamiento

Una notificación autenticada y parseada responde HTTP 200 sin esperar OpenAI o GreenAPI. El lote
se entrega a una única tarea `BackgroundTasks`, donde se construyen y cierran los adaptadores.

Cada mensaje se procesa de forma independiente. Un fallo no detiene los restantes. No existen
reintentos automáticos en esta capa, porque un resultado ambiguo del envío podría duplicar la
respuesta.

Limitación: `BackgroundTasks` vive en el proceso. Una caída después del ACK puede perder trabajo.
Antes de producción se debe evaluar una cola durable con backpressure, apagado ordenado,
recuperación y métricas.

## 8. Idempotencia

La clave es `provider:external_message_id`. El orquestador reclama antes de llamar a OpenAI,
marca como completado después del envío y libera la reserva si el procesamiento falla.

`InMemoryIdempotencyStore`:

- es atómico dentro de un proceso;
- almacena solo IDs, no texto ni remitentes;
- limita su capacidad a 10000 entradas;
- desaloja primero la entrada completada más antigua;
- nunca desaloja una entrada activa.

No es una solución de producción: no se comparte entre procesos, se pierde al reiniciar y deja
una ventana entre envío y marcado. Debe reemplazarse por persistencia coordinada.

## 9. Cliente saliente

GreenAPI define `SendMessage` como:

```text
POST {apiUrl}/waInstance{idInstance}/sendMessage/{apiTokenInstance}
```

Body:

```json
{
  "chatId": "5210000000000@c.us",
  "message": "Respuesta",
  "linkPreview": false
}
```

La respuesta válida es:

```json
{
  "idMessage": "..."
}
```

El texto saliente admite hasta 20000 caracteres conforme al endpoint actual. `chatId` se valida
antes de usarlo. La URL base se toma únicamente de configuración validada.

GreenAPI exige `apiTokenInstance` en el path. Este riesgo se controla así:

- el token solo se revela dentro del método que construye la solicitud;
- `httpx` y `httpcore` se configuran en nivel `WARNING` para impedir el log informativo de URL;
- no se sigue ninguna redirección;
- la URL final nunca se devuelve en excepciones;
- no se registran request/response bodies;
- los tests comprueban que el token no aparece en logs ni errores.

Timeouts, conexión, rate limit, estados HTTP y respuestas inválidas se traducen a excepciones
internas seguras. Solo se conserva un código numérico del proveedor cuando está disponible; no se
conservan mensajes ni cuerpos.

Referencias oficiales:

- [SendMessage](https://green-api.com/en/docs/api/sending/SendMessage/);
- [formato de solicitudes](https://green-api.com/en/docs/request-format/);
- [hosts de GreenAPI](https://green-api.com/en/docs/api/recommendations/using-green-api-hosts/);
- [errores comunes](https://green-api.com/en/docs/api/common-errors/).

## 10. Logging y privacidad

Se puede registrar:

- request ID;
- plantilla de endpoint;
- status HTTP;
- duración;
- categoría estable del fallo;
- conteos de mensajes.

No se registra:

- tokens;
- encabezado `Authorization`;
- URL final de `sendMessage`;
- body del webhook;
- `chatId` o número completo;
- texto de entrada o salida;
- respuesta completa de GreenAPI u OpenAI.

Los identificadores y números de WhatsApp son datos personales.

## 11. Pruebas

Las pruebas comunes no usan internet. Deben cubrir:

- configuración válida e inválida, secretos y allowlist del host;
- token Bearer correcto, ausente, duplicado e incorrecto;
- autenticación antes de leer el body;
- instancia correcta e incorrecta;
- texto simple, extendido, citado y grupo;
- tipos/eventos ignorados y JSON inválido;
- flujo completo con dobles;
- deduplicación y liberación tras fallo;
- ACK antes del procesamiento;
- endpoint/payload/respuesta de `SendMessage`;
- timeout, conexión, 401/403/429/5xx y respuesta inválida;
- ausencia de tokens, texto, destinatario y URL final en logs o errores.

Comandos de cierre:

```powershell
pytest
ruff check .
ruff format --check .
python -m pip check
git diff --check
```

## 12. Prueba real F2.9

La prueba real requiere que el usuario configure localmente la instancia y ambos tokens, sin
compartir sus valores. Luego:

1. reiniciar el backend para cargar la nueva configuración;
2. publicar el endpoint por HTTPS;
3. configurar `webhookUrl`, `webhookUrlToken` e `incomingWebhook=yes` en GreenAPI;
4. confirmar que el estado de la instancia permite enviar/recibir;
5. enviar un mensaje real al WhatsApp conectado;
6. comprobar POST autenticado y ACK 200;
7. comprobar procesamiento OpenAI;
8. comprobar `SendMessage` y recepción de la respuesta en WhatsApp;
9. ejecutar todos los validadores;
10. pasar F2.9 por `🧪 VALIDACION` y solo después a `✅ COMPLETADO`.

No se deben guardar payloads reales ni evidencias con números o tokens.

El 2026-09-21 se verificó el health público, la autenticación del webhook, el ACK HTTP 200, el
procesamiento de un mensaje sin fallos, la aceptación de `SendMessage` y la recepción final de la
respuesta confirmada por el usuario. La evidencia conservada contiene solo estados y conteos
seguros; no incluye texto, números, IDs externos, tokens o payloads.
