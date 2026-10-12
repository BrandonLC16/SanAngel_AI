# F10.4 — Observabilidad y costos

## Señales disponibles

El proceso emite una línea JSON por solicitud HTTP y llamada saliente a OpenAI o GreenAPI en el
logger `backend.app.operations`. Sus campos son timestamp UTC, evento, componente, resultado,
duración en milisegundos y, cuando aplica, plantilla de ruta, clase de error y conteos de tokens.
Las alertas son líneas JSON con `event=alert` y un `code` cerrado. Configurar el supervisor o
colector para conservar estas líneas y generar avisos a partir de ese campo; no se envían datos
a un servicio externo desde el backend.

Un propietario autenticado puede consultar `GET /api/v1/admin/operations/metrics` por HTTPS. La
respuesta usa `Cache-Control: no-store` y contiene contadores HTTP por clase de estado, llamadas
OpenAI/GreenAPI por resultado, histogramas de latencia con límites 100/500/2000/10000 ms,
tokens de OpenAI, respuestas sin estimación, costo estimado y alertas emitidas. No contiene
mensajes, destinatarios, IDs externos ni credenciales. La ruta utiliza `AUDIT_READ`, permiso
exclusivo del rol `owner`. Su alcance es **un proceso**: al reiniciar se pierde y varios workers
necesitan agregación en el colector. Cada instalación corresponde a una sola sucursal.

La referencia de solicitud en logs es un HMAC truncado de `X-Request-ID` con clave efímera del
proceso. Sirve para correlacionar los logs HTTP y de fondo dentro de ese proceso sin imprimir un
ID enviado por el cliente que podría contener un número o token. No es estable tras reiniciar.
Las rutas se registran como plantillas de FastAPI, nunca como path/query de la solicitud.

## Uso y estimación de costo OpenAI

Cada `responses.create` registra duración y resultado; los errores se clasifican como timeout,
rate limit, conexión, estado HTTP u otro. Las respuestas con `usage` válido suman tokens de
entrada, entrada en caché, escritura de caché y salida. Los tokens en caché y de escritura están
incluidos en `input_tokens`; se descuentan para calcular la entrada ordinaria. El loop con tools
cuenta **cada** llamada a Responses. La [referencia de Responses](https://developers.openai.com/api/reference/resources/responses/methods/create)
documenta estos campos de `usage`.

Configurar para el modelo efectivo, a partir de la [tarifa oficial vigente](https://openai.com/api/pricing/),
las siguientes cantidades USD por millón de tokens:

```dotenv
OBSERVABILITY_INPUT_USD_PER_MILLION=
OBSERVABILITY_CACHED_INPUT_USD_PER_MILLION=
OBSERVABILITY_CACHE_WRITE_USD_PER_MILLION=
OBSERVABILITY_OUTPUT_USD_PER_MILLION=
OBSERVABILITY_DAILY_COST_ALERT_USD=
```

Las cuatro tarifas se configuran juntas; usar `0` para escritura de caché si la tarifa del modelo
no contempla ese cargo. Un umbral diario requiere las cuatro. Si se dejan
todas vacías, la estimación no se calcula para esa respuesta y aumenta
`openai_unpriced_responses`. Una respuesta sin `usage` también aumenta ese contador y produce una
alerta. El valor `openai_estimated_cost_usd` es una **estimación parcial**, nunca una factura:
no incorpora respuestas sin uso, llamadas fallidas posiblemente facturadas, cargos de otras
tools/servicios ni ajustes del proveedor. Comparar diariamente con el [uso y costos de la cuenta
OpenAI](https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs)
y corregir las tarifas cuando cambie modelo o precio. No colocar el nombre del modelo o tarifas
en labels de alta cardinalidad. Las tarifas no se fijan en código para evitar estimaciones
obsoletas.

## Alertas y respuesta

| Código JSON | Condición | Acción operativa |
|---|---|---|
| `http_slow`, `openai_slow`, `greenapi_slow` | Una solicitud HTTP tarda al menos 2000 ms; OpenAI, 15000 ms; GreenAPI, 5000 ms. | Revisar latencia por componente, upstream y cuota. |
| `openai_errors`, `greenapi_errors` | Al menos cinco fallos del proveedor en 60 segundos del proceso. | Revisar disponibilidad, rate limit y credenciales sin registrar respuestas crudas. |
| `openai_usage_missing` | Respuesta exitosa sin uso numérico verificable. | Conciliar con panel/API de uso antes de confiar en costos. |
| `openai_pricing_missing` | Hay uso válido, pero faltan tarifas configuradas. | Configurar las cuatro tarifas vigentes para obtener estimación. |
| `openai_daily_estimate` | El estimado del día UTC alcanza `OBSERVABILITY_DAILY_COST_ALERT_USD`. | Revisar gasto real y presupuesto; detener o limitar tráfico si procede. |

Cada código se emite como máximo una vez por minuto y proceso. La alerta de costo puede
repetirse en minutos posteriores mientras continúen las llamadas por encima del umbral.
Configurar reglas y destino en el colector/supervisor del despliegue, además de una prueba de
entrega al operador. Los contadores locales y alertas no sustituyen un presupuesto/hard limit
en OpenAI ni vigilancia del proveedor. En el runtime actual, `greenapi` mide el canal WhatsApp;
**Meta** es histórico desde F2.9 y no tiene adaptador activo ni errores que medir.

## Seguridad y límites

Solo se registran nombres de evento y categoría cerrados, plantilla de ruta, estado, duración y
conteos. No se registran payloads, prompt, respuestas, número de WhatsApp, URL con token de
GreenAPI, `Authorization`, cookies, texto de excepción del proveedor ni IDs externos. Los
diagnósticos de fondo rechazan categorías ajenas y códigos no numéricos. Restringir el colector
al personal operativo, definir retención y probar que no ingiere logs de acceso de proxies con
URLs o encabezados sensibles. El estado métrico vive en memoria por proceso y no persiste una
serie histórica; producción con varios procesos requiere agregar sus eventos externamente.

Las pruebas automatizadas usan solo dobles locales; no hubo llamadas reales a OpenAI/GreenAPI,
ni verificación de entrega de una alerta externa o comparación con una factura real.
