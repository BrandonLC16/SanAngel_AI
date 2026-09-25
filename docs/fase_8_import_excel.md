# F8.5 — Importación de precios desde el panel

El menú **Importación Excel** muestra la sucursal obtenida del backend. Un usuario `editor` u
`owner` elige un `.xlsx` de hasta 2 MiB, solicita una vista previa y revisa altas, cambios,
filas iguales, importes y errores. Solo una vista previa válida habilita **Confirmar importación**.
El resultado muestra los conteos y el ID del recibo de auditoría. Un `viewer` ve la sucursal y
la explicación, pero no puede cargar archivos.

El panel envía el XLSX como cuerpo binario a `POST /api/v1/admin/price-import/preview` y la
confirmación explícita a `POST /api/v1/admin/price-import/confirm`. El nombre original viaja en
`X-File-Name` codificado en UTF-8 para validar la extensión; no se persiste ni se registra.
Ambas rutas exigen HTTPS,
sesión vigente, permiso de escritura comercial y `X-CSRF-Token`. La solicitud no admite código de
sucursal ni ID de sucursal. El backend usa `ASSISTANT_BRANCH_CODE`, lee el
cuerpo por partes y rechaza más de 2 MiB antes de acumularlo. El parser de F5 exige la plantilla
versionada y limita filas, tamaño descomprimido y estructura ZIP. Ningún dato del archivo se
interpreta como instrucciones.

Una vista previa válida recibe un identificador aleatorio. El backend conserva los bytes y el
objeto preparado en memoria durante un máximo de 10 minutos, con capacidad de 16 vistas previas
por proceso. La entrada está ligada a la sesión y se consume una sola vez. Al confirmar, el
servicio de F5 vuelve a validar archivo y catálogo dentro de una transacción y registra el
resultado; si los precios cambiaron, exige una nueva vista previa. Los bytes del XLSX no se
guardan en la base ni en el registro de auditoría.

**Límite operativo:** este almacenamiento temporal es local a un solo proceso. Para usar varios
workers o instancias se necesitará un almacén compartido para las vistas previas antes de
habilitar este flujo en ese despliegue. Un reinicio invalida los identificadores pendientes;
el operador puede volver a cargar el archivo. La retención y borrado de reportes de auditoría
siguen pendientes antes de producción, según la Fase 5.
