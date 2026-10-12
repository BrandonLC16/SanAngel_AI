# F10.2 — HTTPS, proxy y cabeceras

## Despliegue por instalación

Cada sucursal necesita un dominio o subdominio propio, DNS hacia el servidor, puertos 80/443
disponibles y persistencia protegida para los certificados de Caddy. El ejemplo
[`deploy/Caddyfile`](../deploy/Caddyfile) usa HTTPS automático de Caddy, redirección HTTP a
HTTPS, un backend FastAPI en `127.0.0.1:8000` y `frontend/dist/` bajo el mismo origen.
El ejemplo se validó con Caddy 2.11.7; fijar esa versión al desplegar y actualizarla mediante
un cambio verificado.
En `PUBLIC_DOMAIN` se configura solo el nombre DNS; `PANEL_DIST` es la ruta absoluta del build.
No se guardan certificados ni claves TLS en el repositorio. Caddy y FastAPI deben correr en el
mismo host; si se separan, hace falta un canal privado autenticado y revisar de nuevo la lista de
proxies confiables. Si varias instalaciones comparten host, se combinan sus bloques de sitio en
un solo Caddy y se asigna un puerto loopback distinto a cada backend.

Ejemplo de preparación, repetido con variables y datos propios para cada instalación:

```powershell
npm --prefix frontend run build
$env:APP_ENV = 'production'
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '8000'
$env:TRUSTED_PROXY_IPS = '127.0.0.1'
$env:PUBLIC_DOMAIN = 'panel.ejemplo.invalid'  # reemplazar por DNS real
$env:PANEL_DIST = 'C:/ruta/instalacion/frontend/dist'
caddy validate --config deploy/Caddyfile --adapter caddyfile
python -m scripts.run_backend
# En otro proceso o servicio: caddy run --config deploy/Caddyfile --adapter caddyfile
```

La configuración productiva de la aplicación se guarda en el `.env` local ignorado por Git;
`PUBLIC_DOMAIN` y `PANEL_DIST` se entregan al proceso de Caddy. La URL de GreenAPI debe ser
`https://<dominio>/api/v1/whatsapp/webhook`; el proxy conserva `Authorization` y la ruta.
Mantener las dos aplicaciones como servicios supervisados. No usar el servidor de Vite para
publicar el panel. No abrir el puerto 8000 hacia la red pública. Para el panel del mismo origen,
dejar `CORS_ALLOWED_ORIGINS` vacío en producción; si se usa otro origen autorizado, debe ser
HTTPS y exacto.

## Confianza y rechazo

`scripts.run_backend` arranca Uvicorn con `proxy_headers=False`, sin access log y, en
producción, solo en una IP loopback. No arrancar producción con `uvicorn` directo ni permitir
`FORWARDED_ALLOW_IPS=*`: Uvicorn transformaría el cliente y el esquema antes de que la
aplicación pudiera validar el peer real. `TRUSTED_PROXY_IPS` admite hasta 16 direcciones IP
exactas; no admite rangos, comodines, DNS ni direcciones de escucha. Su valor por defecto es
vacío. El ejemplo usa solo `127.0.0.1`.

FastAPI acepta `X-Forwarded-Proto` únicamente cuando la conexión directa proviene de esa lista
y tiene exactamente un valor `https`. Ignora `X-Forwarded-For`, `X-Forwarded-Host` y
`Forwarded`; por ello los límites de F10.1 y el límite de login ven la IP directa del proxy.
Caddy sobrescribe `X-Forwarded-Proto` y elimina los otros tres encabezados hacia el backend.
El `Host` público coincide con el sitio configurado en Caddy. Un HTTP que llega directamente al
backend productivo recibe 403 sin redirección ni procesamiento del body; esto evita depender de
redirecciones para el webhook. HTTP al dominio público se redirige a HTTPS por Caddy.

No situar otra capa (CDN, túnel o balanceador) delante de Caddy sin definir antes su confianza
y su comportamiento de TLS; el Caddyfile actual supone que recibe directamente al cliente.

## Cabeceras

El backend aplica `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
`X-Frame-Options: DENY` y `Permissions-Policy` restrictiva, también a errores HTTP.
En respuestas HTTPS productivas aplica HSTS de un año, sin `includeSubDomains` ni preload.
Las rutas administrativas aplican `Cache-Control: no-store`. Caddy aplica las mismas cabeceras
generales al contenido estático y una CSP al panel: scripts, estilos, imágenes, fuentes y
conexiones solo del mismo origen; sin objetos, bases externas ni framing. No usa
`unsafe-inline` ni `unsafe-eval`. El build actual usa recursos locales.

## Validación y límites

Las pruebas automatizadas cubren HTTP rechazado, TLS directo, proxy permitido, IP ajena,
valores duplicados o ambiguos de `X-Forwarded-Proto`, otras cabeceras falsas, configuración
del servidor y CSP. `caddy validate` comprueba el archivo con variables de ejemplo. Con Caddy
instalado, `python -m scripts.f102_tls_smoke --caddy <ruta-a-caddy>` ensaya TLS con una CA
temporal validada localmente, redirección, rechazo del HTTP directo, `/health` y CSP del panel;
usa solo loopback y los puertos 8000, 18080 y 18443, sin llamadas a proveedores ni instalar
la CA en el sistema. Esta sonda debe pasar antes de apuntar GreenAPI a un dominio real.

F10.2 no activa por sí sola DNS, certificados públicos, firewall ni GreenAPI. Las cuotas HTTP
por IP de F10.1 se agregan bajo la IP del proxy; antes de aumentar tráfico administrativo hay
que definir un límite compartido en el perímetro o una extracción de IP cliente con cadena de
confianza verificada. El webhook conserva cuota global y no depende de la IP del remitente.
