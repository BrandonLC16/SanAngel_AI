# F8.7 — Auditoría administrativa

`GET /api/v1/admin/audit/events` expone recibos de cambios administrativos de la instalación
configurada. Requiere sesión HTTPS vigente y rol `owner`; el frontend solo muestra la sección a
ese rol, pero el backend vuelve a comprobar el rol activo y la sucursal en la base. La respuesta
usa `Cache-Control: no-store`.

La lista está ordenada por fecha descendente e ID de recibo, con `limit` entre 1 y 100 y `offset`
entre 0 y 5000. `entity` puede ser `branch`, `product`, `price`, `faq` o `admin_user`. Para
investigar un precio se puede indicar `entity=price&product_id=<id>`. El ID de producto se
interpreta solo dentro de `ASSISTANT_BRANCH_CODE`; no existe un parámetro de sucursal.

Cada fila contiene ID de recibo y fuente, ID local del actor, acción, entidad e ID de entidad,
timestamp UTC y valores `before`/`after` permitidos explícitamente:

- precio: importe decimal en MXN; además ID de producto y unidad;
- cambio de rol: rol anterior y nuevo;
- sucursal, producto y FAQ: `before`/`after` nulos. El recibo registra que hubo cambio, pero no
  duplica dirección, teléfono, texto de FAQ ni otros campos comerciales libres.

Los cambios manuales de precio y rol ya dejaban recibos transaccionales. Desde F8.7, cada precio
creado o actualizado mediante la confirmación Excel del panel también deja un recibo de precio
en la misma transacción que la escritura y el resumen de importación. Si falla cualquier recibo,
se revierten los precios y se registra el intento fallido de importación. La confirmación vuelve
a validar que el actor sea una cuenta activa con permiso de escritura de la sucursal.

La proyección de la API se construye campo por campo. No lee ni serializa hashes de contraseña,
tokens de sesión, CSRF, cuerpos HTTP, hojas Excel ni texto de conversaciones. Los cambios
anteriores a F8.7 provenientes de importaciones conservan solo el resumen de F5.5: no se pueden
reconstruir valores por fila retroactivamente. Los recibos no distinguen en la lista si un precio
se cambió manualmente o por Excel; el reporte de importación conserva su resumen por separado.
Definir acceso y retención operativos de esta auditoría antes de producción.
