# Diseño técnico — Fase 2
## WhatsApp como interfaz principal del cliente

**Fecha:** 2026-08-25  
**Estado:** PENDIENTE hasta cerrar Fase 1.

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
META_GRAPH_API_VERSION=
WHATSAPP_REQUEST_TIMEOUT_SECONDS=15
```

No inventar valores.

`META_GRAPH_API_VERSION` debe fijarse/configurarse según una versión oficial soportada en el momento de implementación.

---

# 5. Seguridad del webhook

## Handshake GET

Validar los parámetros requeridos por Meta y comparar el verify token configurado.

No loguearlo.

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
