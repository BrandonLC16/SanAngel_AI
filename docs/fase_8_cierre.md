# Fase 8 — Cierre del panel administrativo

La Fase 8 entrega el panel para operación local de una instalación y su sucursal configurada.
El backend mantiene la autorización, la sesión, el alcance de sucursal y las escrituras; el
frontend solo presenta los permisos al personal.

| Subfase | Entrega comprobada |
|---|---|
| F8.1 | Credenciales Argon2id, sesión opaca revocable, cookie segura, CSRF y límite de login. |
| F8.2 | Roles `viewer`, `editor` y `owner` comprobados en backend y limitados a la sucursal. |
| F8.3 | Shell React de escritorio, login, cliente API del mismo origen y estados de error. |
| F8.4 | Gestión de sucursal, productos, precios y FAQ con RBAC, CSRF y auditoría. |
| F8.5 | Importación Excel con validación, vista previa por sesión, confirmación y recibo. |
| F8.6 | Revisión acotada de conversaciones y preguntas no resueltas; resolución de FAQ aprobada. |
| F8.7 | Consulta de auditoría para `owner`, con actor, acción, fecha, entidad y before/after permitido; cambios de precio del panel y de Excel trazables. |
| F8.8 | Pruebas de rutas anónimas, autorización, CSRF, XSS, CORS, límite de login y expiración. |

Las guías de [autenticación](fase_8_auth.md), [roles](fase_8_rbac.md),
[datos comerciales](fase_8_commercial.md), [importación](fase_8_import_excel.md),
[revisión](fase_8_revision.md), [auditoría](fase_8_auditoria.md) y
[seguridad del panel](fase_8_seguridad_panel.md) describen el comportamiento y sus límites.

## Validación de cierre — 2026-09-25

- `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`: 603 pruebas aprobadas.
- `.venv\Scripts\ruff.exe check .`: aprobado.
- `.venv\Scripts\ruff.exe format --check .`: 171 archivos correctos.
- `.venv\Scripts\python.exe -m pip check`: sin dependencias rotas.
- `npm --prefix frontend run test`: 29 pruebas aprobadas en 10 archivos.
- `npm --prefix frontend run build`: tipos y bundle generados correctamente.
- `git diff --check`: sin errores de espacios; Git avisó sobre conversión LF/CRLF.

El cierre ejecuta las pruebas existentes de backend y frontend. No modifica código de aplicación
ni añade pruebas que dupliquen controles ya cubiertos en F8.8.

## Límite de despliegue

**No exponer el panel ni los endpoints administrativos a internet antes de completar F10.**
El backend y el servidor de desarrollo Vite escuchan en `127.0.0.1` de forma predeterminada.
Una suite local y un build correcto no verifican el proxy, TLS, cabeceras de seguridad/CSP,
gestión de secretos, respaldo ni controles operativos previstos en F10. Mantener el acceso
local y restringido; no usar el servidor de desarrollo como servidor público.

El flujo WhatsApp actual todavía no alimenta automáticamente las vistas de mensajes ni los
agregados FAQ del panel. Las importaciones anteriores a F8.7 no tienen auditoría de precios
por fila. La retención operativa del historial y la revisión de producción siguen pendientes.
