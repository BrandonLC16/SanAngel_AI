# F10.1 — Rate limiting y límites de recursos

## Límites HTTP por instalación

| Entrada | Cuota inicial | Cuerpo máximo | Exceso |
|---|---:|---:|---|
| Webhook GreenAPI autenticado | 100 solicitudes/s, ráfaga de 200 | 1 MiB | HTTP 429 con `Retry-After: 1`; GreenAPI puede reentregar |
| Administración | 120 solicitudes/min por conexión directa | 64 KiB para JSON | HTTP 429 o 413 |
| Preview de Excel del panel | Cuota administrativa | 2 MiB, tras sesión y CSRF | HTTP 413 |
| Chat interno de desarrollo | 30 solicitudes/min por conexión directa | 16 KiB | HTTP 429 o 413 |

El webhook comprueba configuración y Bearer **antes** de consumir cuota o leer el cuerpo. La
cuota se comparte por proceso de la instalación, nunca por IP: GreenAPI puede enviar muchos
eventos desde una misma dirección. Una notificación demasiado grande o con longitud inválida recibe
HTTP 200 sin procesarse; evita que una notificación imposible de aceptar bloquee la cola con
reintentos continuos. El límite de 1 MiB excede ampliamente el texto admitido por el chatbot.
Si la lectura del cuerpo se agota, el webhook devuelve 503 para pedir reentrega. Un 429 tampoco
confirma recepción. Los eventos aceptados mantienen los recibos persistentes de idempotencia.

[GreenAPI documenta](https://green-api.com/en/docs/api/recommendations/working-with-incomming-webhooks/)
que un webhook sin HTTP 200 se reintenta aproximadamente un minuto después, y su
[guía del endpoint](https://green-api.com/en/docs/api/receiving/technology-webhook-endpoint/)
describe un ritmo cercano a 50 notificaciones/s. La cuota inicial permite el doble de ese
ritmo sostenido y una ráfaga adicional; debe revisarse con métricas reales antes de elevar el
tráfico. `Retry-After` es una indicación HTTP; no se asume que GreenAPI la siga.

Los límites administrativos e internos usan la dirección de conexión directa; no confían en
`X-Forwarded-For`. El login conserva además su bloqueo persistente por cuenta y origen. Las
cuotas nuevas son **por proceso**, con máximo de 4096 claves en memoria por grupo; una
instalación con varios workers necesita un límite compartido en el perímetro. El health check
queda fuera de estas cuotas. No se registran IP, cuerpos, tokens ni contenido de mensajes en
los nuevos controles; el log HTTP conserva su request ID, ruta, duración, estado y categoría.

## Timeouts y reintentos

La lectura de cuerpos HTTP y del Excel tiene un plazo configurable de 10 segundos por defecto.
Un timeout de administración o chat interno devuelve 408; uno de webhook devuelve 503 para
permitir reentrega. `OPENAI_TIMEOUT_SECONDS=30` y `OPENAI_MAX_RETRIES=2` siguen siendo los
valores iniciales del SDK para una operación sin escritura comercial. El envío GreenAPI usa
`WHATSAPP_REQUEST_TIMEOUT_SECONDS=15` y **cero reintentos automáticos**: un timeout o error
ambiguo puede haber enviado el mensaje, y repetirlo lo duplicaría. Tampoco se cancela por un
timeout HTTP general una transacción o envío manual en curso.

`ADMIN_REQUESTS_PER_MINUTE`, `INTERNAL_REQUESTS_PER_MINUTE`,
`WEBHOOK_REQUESTS_PER_SECOND` y `HTTP_BODY_READ_TIMEOUT_SECONDS` permiten ajustar el despliegue
sin cambiar código. Todos se validan al iniciar. Una cuota demasiado baja puede retrasar
tráfico real; antes de cambiarla se deben observar 429 y tiempos de reentrega. El límite de
memoria por proceso no sustituye un control perimetral. F10.8 confirma el webhook solo después
del commit de una [cola durable](fase_10_cola.md); cuando esta se satura responde 503 para
permitir la reentrega.
