# F8.2 — Autorización administrativa

Todos los administradores pertenecen a la sucursal fija de `ASSISTANT_BRANCH_CODE`; no existe
rol global. La revisión `20260924_0009` agrega `admin_users.role` con una restricción de base
de datos. Las cuentas de F8.1 pasan a `viewer` al migrar. Para iniciar la administración de una
instalación, una persona con acceso local autorizado ejecuta:

```powershell
python -m alembic upgrade head
python -m backend.app.cli.create_admin_user --username propietario --role owner
```

La CLI mantiene la contraseña interactiva; `--role` solo acepta `viewer`, `editor` u `owner`.
No hay creación pública de usuarios ni selección de sucursal en las rutas admin.

| Rol | `GET /me` | `GET /users` | `PATCH /users/{id}/role` |
|---|---|---|---|
| `viewer` | Sí | No | No |
| `editor` | Sí | Sí | No |
| `owner` | Sí | Sí | Sí, para otra cuenta de su sucursal |

Las rutas tienen prefijo `/api/v1/admin`. `GET /me` devuelve nombre y rol de la sesión.
`GET /users` devuelve solo ID, nombre, rol y estado de cuentas de la instalación. `PATCH`
acepta únicamente `{"role": "viewer|editor|owner"}` y exige `X-CSRF-Token` de la sesión.
No admite `branch_id` ni `branch_code`; un ID de otra sucursal responde 404 sin modificarlo.
No se permite cambiar el propio rol mediante HTTP. Los cambios de rol se leen de la base en
cada petición; una sesión anterior no conserva permisos retirados.

Sin cookie válida se responde 401. Un rol sin permiso, una petición sin CSRF o un intento de
cambiar el propio rol responde 403. Un usuario inexistente o fuera de la sucursal responde 404.
Los JSON de éxito llevan `Cache-Control: no-store` y no incluyen hashes ni tokens de sesión.
El backend comprueba los permisos incluso si el frontend envía un rol, botón o cabecera falsos.
La actualización de rol revalida al propietario dentro de la escritura SQL y limita la fila
destino a la sucursal de la sesión. Un cambio efectivo inserta en la misma transacción un recibo
`admin_role_audits` con sucursal, IDs de actor y destino, roles anterior y nuevo y hora. No guarda
contraseñas, tokens, IP, cuerpos HTTP ni nombres. Una petición rechazada o sin cambio no crea
recibo; si la auditoría no puede persistirse, el cambio de rol revierte.

F8.2 no crea CRUD de productos, precios, FAQ ni sucursales. Cada ruta futura deberá declarar
permiso explícito, exigir CSRF para escritura y filtrar por la sucursal del backend. La matriz
actual solo cubre las rutas que existen; al incorporar nuevas operaciones se deben ampliar
permisos y pruebas negativas. Esta regla sigue la guía de [autorización de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).
