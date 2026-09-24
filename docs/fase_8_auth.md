# F8.1 — Autenticación backend del personal

## Alcance

`AdminUser` pertenece a la sucursal configurada por `ASSISTANT_BRANCH_CODE`. La base guarda
únicamente `password_hash` Argon2id, nunca una contraseña en claro. `AdminSession` guarda SHA-256
de un token aleatorio de 256 bits, vencimiento y revocación; `AdminLoginThrottle` guarda HMAC de
identificador de cuenta y origen directo, contador y ventana. Ninguna tabla guarda el origen IP o
el token de sesión en claro. No existe registro público de administradores.

La biblioteca `argon2-cffi` usa Argon2id y permite detectar parámetros desactualizados para
rehash tras un login correcto ([documentación oficial](https://argon2-cffi.readthedocs.io/en/stable/howto.html)).
Se fija `argon2-cffi>=25.1,<26.0` en `pyproject.toml`; no existe lockfile en este repositorio.

## Aprovisionamiento local

En cada instalación, crear primero el perfil de sucursal y aplicar migraciones. Generar
`ADMIN_AUTH_KEY` independiente y URL-safe de 32 a 256 caracteres, guardarlo solo en el backend y
fuera del repositorio. Después ejecutar en una terminal local protegida:

```powershell
python -m alembic upgrade head
python -m backend.app.cli.create_admin_user --username operador
```

El comando solicita la contraseña dos veces sin argumento de línea de comandos; exige de 12 a
1024 caracteres y devuelve solo un estado genérico. Los errores no muestran contraseña, hash,
usuario ni ruta de la base. La cuenta se crea solo en la sucursal configurada.

## Contrato HTTP

Las rutas `/api/v1/admin/auth/login`, `/session` y `/logout` exigen HTTPS en el esquema ASGI.
Detrás de un proxy TLS, configurar correctamente el esquema mediante un proxy de confianza;
no confiar en `X-Forwarded-Proto` de clientes arbitrarios.

| Ruta | Entrada | Resultado |
|---|---|---|
| `POST /login` | JSON `username`, `password` | Cookie de sesión y JSON con `username`, rol, vencimiento y token CSRF. Error 401 genérico o 429. |
| `GET /session` | Cookie | Sesión activa, rol y token CSRF; 401 si expiró o fue revocada. |
| `POST /logout` | Cookie y cabecera `X-CSRF-Token` | Revoca la sesión en SQLite y elimina la cookie; 403 si falta CSRF. |

La cookie `__Host-admin_session` tiene `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`, sin
`Domain` y duración máxima de ocho horas. El token no se devuelve en JSON, URL ni logs. La cookie
se configura con la API de [Starlette](https://www.starlette.io/responses/). El token CSRF se
deriva con HMAC del token de sesión y `ADMIN_AUTH_KEY`, se entrega en JSON y debe permanecer en
memoria del panel; `/session` permite recuperarlo tras recargar. Toda futura operación de escritura
autenticada deberá exigirlo en backend. `SameSite` y CORS por sí solos no reemplazan la defensa
CSRF ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)).

Los cuerpos de login se validan y sus errores no repiten el contenido. Las respuestas de sesión
correctas usan `Cache-Control: no-store`. El middleware HTTP registra solo endpoint, estado,
duración y categoría, no credenciales, cookies ni cabeceras completas.

## Límite de intentos y sesiones

Cada intento con formato válido incrementa de forma atómica dos contadores SQLite: máximo cinco
por nombre de cuenta y veinte por origen directo en una ventana de quince minutos. El sexto o
vigésimo primer intento recibe 429 antes de verificar Argon2. El servicio ignora
`X-Forwarded-For`, por lo que un proxy inverso puede agrupar a todos los clientes en un mismo
origen; resolver la identidad del cliente únicamente mediante configuración explícita de proxies
confiables antes de un despliegue público. Cuatro verificaciones Argon2 simultáneas como máximo
limitan memoria. Los contadores de más de un día y las sesiones vencidas hace más de un día se
purgan en el siguiente login de la sucursal. Estas medidas siguen la recomendación de
[login throttling de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

Las sesiones son revocables y no deslizantes: expiran ocho horas después del login. Desactivar
un `AdminUser` impide usar sus sesiones existentes. Rotar `ADMIN_AUTH_KEY` cambia los tokens CSRF
y las claves de throttling; la sesión opaca sigue válida hasta su vencimiento o revocación.

## Límites

F8.1 no agregó roles, RBAC, CRUD administrativo ni frontend. F8.2 incorpora roles y endpoints
de autorización descritos en [su guía](fase_8_rbac.md). Antes de producción faltan configuración TLS/proxy estable, protección operacional
de la base y secreto, evaluación de capacidad Argon2, MFA/alertas según riesgo y monitoreo de
intentos de login. Las pruebas usan SQLite temporal y clientes HTTPS locales, sin red externa.
