# F8.3 — Shell administrativo

Shell React + TypeScript con Vite para escritorio. Incluye login, recuperación de sesión,
layout, cierre de sesión y estados de error. F8.4 incorpora listas y formularios de la
sucursal configurada, productos, precios y FAQ. El backend aplica RBAC, CSRF y alcance de
sucursal; los permisos visuales del panel solo facilitan el uso.

F8.5 incorpora [importación de precios Excel](../docs/fase_8_import_excel.md): carga, vista
previa, confirmación y recibo para editores y propietarios. La sucursal destino la fija el backend.

## Preparación y validación

Desde la raíz del repositorio:

```powershell
cd frontend
npm ci
npm run test
npm run build
npm run dev
```

`npm run dev` abre el shell en `http://127.0.0.1:5173/` solo en la máquina local. La página
puede verse aunque el backend esté apagado; en HTTP el formulario queda inactivo y explica que
se requiere HTTPS.
El proxy de desarrollo reenvía `/api` a `https://127.0.0.1:8000` con validación de certificado.
Para probar login en desarrollo, configurar `ADMIN_DEV_TLS_CERT_FILE` y
`ADMIN_DEV_TLS_KEY_FILE` con rutas a un certificado local confiable para `127.0.0.1` y su clave,
fuera del repositorio. Vite servirá el panel por HTTPS. El backend también debe usar HTTPS con un
certificado confiable para `127.0.0.1`; el certificado puede cubrir ambos puertos. El valor de
`ADMIN_DEV_TLS_*` solo lo lee la configuración de Vite en Node y no entra al bundle. El shell
HTTP sin esas variables sirve para comprobar el layout; el formulario impide introducir
contraseñas. No se
debe desactivar la validación TLS ni simular `X-Forwarded-Proto` desde un cliente arbitrario.
Para un despliegue, servir `frontend/dist/` y `/api` bajo el mismo origen
HTTPS mediante el proxy inverso. El backend mantiene su allowlist CORS sin `*`; el shell usa
rutas relativas y no necesita CORS entre orígenes.

La sesión está en una cookie `Secure`/`HttpOnly` emitida por el backend. El cliente usa
`credentials: 'same-origin'`; solo conserva el token CSRF en memoria mientras la sesión está
abierta y lo envía en `X-CSRF-Token` al cerrar sesión. No usa `localStorage`, URLs con tokens,
API keys, secretos de GreenAPI ni variables `VITE_` de credenciales. Los errores muestran mensajes
fijos; no imprimen el body del servidor. React inserta nombres como texto y no usa HTML dinámico.

El bundle de producción requiere un servidor HTTPS con cabeceras de seguridad apropiadas,
incluida CSP; el servidor estático de Vite es solo de desarrollo. `npm run build` verifica tipos
y genera los archivos estáticos en `frontend/dist/`, que Git ignora.
