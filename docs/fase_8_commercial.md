# F8.4 — Datos comerciales del panel

El panel administra únicamente la sucursal fijada por `ASSISTANT_BRANCH_CODE`. El backend
resuelve esa sucursal de la base en cada operación; ningún cuerpo ni ruta pública admite
`branch_id` o `branch_code` para elegir otra. La sucursal debe aprovisionarse primero con el
perfil local. Su código no se cambia ni se borra desde HTTP, porque identifica la instalación y
está referenciado por usuarios, productos y conversaciones.

## Permisos y rutas

Todas las rutas tienen prefijo `/api/v1/admin/commercial`, requieren cookie de sesión HTTPS y
devuelven datos de una sola sucursal. Las escrituras exigen `X-CSRF-Token`.

| Recurso | Lectura (`viewer` o superior) | Escritura |
|---|---|---|
| Sucursal | `GET /branch` | `PUT /branch`: solo `owner` |
| Productos | `GET /products` | `POST /products`, `PUT /products/{id}`, `DELETE /products/{id}`: `editor` o `owner` |
| Precios | `GET /products/{id}/prices` | `PUT /products/{id}/prices/{unit}`, `DELETE /products/{id}/prices/{unit}`: `editor` o `owner` |
| FAQ | `GET /faqs` | `POST /faqs`, `PUT /faqs/{id}`, `DELETE /faqs/{id}`: `editor` o `owner` |

`PUT` de precio recibe `{"amount":"120.00"}` y crea o cambia el precio actual de esa unidad.
Los importes se envían como cadenas decimales, no floats. `DELETE` de producto o FAQ desactiva el
registro; `PUT` puede reactivarlo. `DELETE` de precio elimina la fila actual y deja su importe
anterior en auditoría. Una ruta con ID ajeno devuelve 404; sin sesión 401; sin permiso o CSRF
válido 403; duplicados 409; entradas inválidas 422. Las respuestas de éxito usan `no-store`.

La revisión Alembic `20260924_0010` agrega `managed_faqs` con clave de pregunta normalizada
única por sucursal y `admin_commercial_audits`. Las FAQ administradas sustituyen por pregunta a
las filas del TSV de la instalación al ejecutar la tool `search_faq`. Una FAQ administrada
desactivada también suprime la fila equivalente del TSV. El TSV sigue aportando las demás
preguntas, se valida antes de cada consulta de la tool y nunca acepta otra sucursal. Si no está
disponible o es inválido, la tool falla cerrada aunque haya FAQ administradas. El flujo WhatsApp
actual todavía no invoca esa tool; su integración permanece fuera de F8.4.

Cada cambio efectivo crea en la misma transacción un recibo con sucursal, actor local, recurso,
ID, acción y hora. Para precios incluye producto, unidad e importe anterior y nuevo. No guarda cuerpos HTTP,
preguntas/respuestas FAQ, dirección, teléfono, contraseñas ni tokens. Si falla el recibo, la
escritura se revierte. Las lecturas y las escrituras sin cambio no crean recibo. La base limita
el actor a la misma sucursal mediante clave foránea compuesta; el servicio vuelve a comprobar
el rol vigente dentro de la transacción.

Antes de migrar una instalación con datos, detener escrituras y seguir el procedimiento de
[respaldo y recuperación](../README.md#respaldo-previo-a-una-migración-productiva). El panel
se sirve con `/api` bajo el mismo origen HTTPS. La UI oculta acciones según rol por claridad;
la decisión de autorización siempre ocurre en backend.
