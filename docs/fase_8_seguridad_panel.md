# F8.8 — Pruebas de seguridad del panel

La suite `backend/tests/test_admin_panel_security.py` recorre las rutas HTTP registradas bajo
`/api/v1/admin` en el runtime FastAPI. `POST /auth/login` es la única entrada que debe aceptar
una petición sin sesión: verifica credenciales y no devuelve datos administrativos sin ellas.
Las demás rutas de negocio y de sesión responden 401 sin cookie válida. Los preflight `OPTIONS`
son parte de CORS y no ejecutan la operación administrativa.

Se comprueban estos límites:

- **Autorización:** `viewer`, `editor` y `owner` obtienen permisos de la cuenta activa en backend;
  cabeceras de rol o sucursal inventadas no elevan privilegios.
- **CSRF:** cada escritura admin registrada, incluido logout, rechaza tokens ausentes o erróneos.
  El login no usa CSRF porque aún no hay sesión; exige HTTPS y aplica límite de intentos.
- **XSS:** pruebas del panel insertan etiquetas HTML en nombre de usuario, producto y FAQ. React
  las muestra como texto o valor de formulario sin crear elementos ejecutables.
- **CORS:** un origen autorizado obtiene preflight para métodos y cabeceras configurados; otro
  origen no obtiene permiso. Un origen autorizado sigue necesitando autenticación y CSRF.
- **Fuerza bruta básica:** el límite de login persiste por cuenta y origen directo; la prueba
  verifica bloqueo tras intentos fallidos y recuperación al terminar la ventana de 15 minutos.
- **Expiración:** una cookie cuyo recibo de sesión venció en SQLite no puede consultar ni escribir;
  el shell retira la vista ante una fecha vencida o un 401 posterior.

Estas son pruebas locales sin red ni cuentas reales. CORS no sustituye la autorización: clientes
no navegador pueden enviar peticiones independientemente del preflight. Antes de publicar el
panel se debe configurar HTTPS y proxies confiables para que el esquema ASGI y el origen directo
usado por el límite de login sean correctos. La política operativa de cabeceras del servidor
estático, incluida CSP, corresponde al despliegue.
