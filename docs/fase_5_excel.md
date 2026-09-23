# Fase 5 — Plantilla e importación de precios (F5.1–F5.4)

La plantilla versionada es [`price_import.example.xlsx`](../examples/price_import.example.xlsx).
Contiene solo datos ficticios. Cada archivo de trabajo pertenece a **una instalación y una
sucursal**. Se copia con un nombre terminado en `.assistant-prices.xlsx`, que Git ignora, y se
reemplazan el código de sucursal y todas las filas de ejemplo antes de usarlo. F5.2 valida el
archivo en memoria, F5.3 prepara el preview y F5.4 incorpora confirmación y escritura
transaccional. Auditoría persistente y reporte corresponden a F5.5.

## Estructura exacta

- Formato: `.xlsx` normal, una sola hoja llamada `Precios`; no se aceptan macros ni `.xlsm`.
- `A3` contiene `schema_version` y `B3` el número entero `1`.
- `D3` contiene `branch_code` y `E3` el código de la sucursal. Debe coincidir exactamente con
  `ASSISTANT_BRANCH_CODE` del backend que procesa el archivo. No hay columna de sucursal por fila
  ni carga de varias sucursales en un archivo.
- La fila 6 contiene, en este orden exacto, los cinco encabezados siguientes. Los datos empiezan
  en la fila 7; cada fila posterior corresponde a un precio de producto y unidad.
- El título y la advertencia de ejemplo de las filas 2 y 4 son informativos. No cambian el
  contrato ni conceden privilegios.

| Columna | Encabezado | Valor requerido |
|---|---|---|
| A | `product_id` | Entero positivo del producto ya existente en la sucursal configurada. Identificador principal; nunca elige la sucursal. |
| B | `product_name` | Nombre actual del mismo producto, de 1 a 120 caracteres; se usa para verificar el ID y no para crear otro producto. |
| C | `unit` | Código interno en minúsculas, de 1 a 24 caracteres, con patrón `[a-z][a-z0-9]*(?:-[a-z0-9]+)*`; ejemplos: `kg`, `piece`, `package`. |
| D | `price_mxn` | Número de Excel en pesos mexicanos **por la unidad de C**, de `0.00` a `9999999999.99`, con máximo dos decimales. Sin símbolo, texto, separadores escritos a mano ni fórmulas. |
| E | `verified_on` | Fecha de Excel sin hora, mostrada como `yyyy-mm-dd`. Fecha en que el negocio confirmó ese precio; no programa su aplicación futura. |

La pareja `(product_id, unit)` debe aparecer una sola vez por archivo. Un precio importado es
el precio **actual** después de la confirmación y escritura transaccional de F5.4;
`verified_on` no cambia `created_at` ni `updated_at` de la base por sí solo. El backend debe
resolver `product_id` dentro de la sucursal configurada y comprobar que `product_name` coincide
antes de proponer cualquier actualización. La representación en Excel es numérica; el parser
convierte el importe a `Decimal` sin pasar un `float` a `PriceData`.

## Ejemplo y seguridad

La hoja contiene `sucursal-demo`, los IDs ficticios `900001` y `900002`, nombres con la palabra
“ejemplo”, dos unidades y precios inventados. Estos IDs no afirman existir en ninguna base. Los
datos de muestra deben sustituirse por datos aprobados de la sucursal correspondiente.

El archivo es input no confiable. `parse_price_import(content, filename=..., branch_scope=...)`
acepta bytes de un `.xlsx` sin abrir rutas ni escribir archivos. Usa `openpyxl` en modo de solo
lectura; el límite es 2 MiB para el archivo, 10 MiB descomprimidos, 128 entradas ZIP y 1000 filas
de datos. Rechaza nombres y entradas con path traversal, macros, fórmulas, vínculos externos,
hojas o cabeceras distintas, versiones no reconocidas y códigos de sucursal ajenos al alcance
inyectado por backend. Valida tipos, precios de `0.00` a `9999999999.99`, fecha real no futura,
unidad, nombres, IDs positivos de hasta 64 bits y duplicados `(product_id, unit)`. Los errores de
filas indican número, columna y código sin incluir valores del archivo. Si hay cualquier error,
el resultado contiene cero filas válidas. No existe escritura a DB en el parser.

## Preview de impacto (F5.3)

`PriceImportPreviewService(session, branch_scope=...).preview(content, filename=...)` recibe una
sesión limpia y el alcance construido desde la configuración backend. Primero usa el parser; un
archivo inválido o de otra sucursal produce errores sin consultar la DB. Después resuelve cada
producto dentro de la sucursal configurada, comprueba que está activo y que su nombre coincide
exactamente. Para cada precio válido informa `new` (alta), `changed` (cambio del importe) o
`unchanged` (sin cambio), con importe actual y propuesto, unidad, producto y fila de origen.
También resume los conteos y los errores. `is_valid` es falso si hay cualquier error; un preview
con errores no está listo para confirmación.

`to_review_data()` entrega un diccionario apto para JSON con solo esos campos comerciales. Los
precios se expresan como texto decimal exacto y los errores incluyen únicamente fila, campo y
código. No devuelve la hoja completa, valores inválidos, datos de otras sucursales, dirección,
teléfono ni credenciales. El servicio solo ejecuta consultas `SELECT`, no hace `flush`, `commit`
ni escritura y rechaza sesiones con cambios pendientes. La futura interfaz administrativa
deberá autenticar y autorizar a quien vea este resultado. F5.3 no agrega endpoint público ni
persiste un preview; F5.4 deberá volver a validar antes de cualquier escritura.

## Confirmación e importación (F5.4)

`PriceImportTransactionService(session_factory, branch_scope=...)` usa únicamente el alcance de
sucursal inyectado por el backend. `prepare(content, filename=...)` genera un
`PreparedPriceImport` con el preview, nombre lógico del archivo y SHA-256 de sus bytes, sin
persistirlo. El administrador debe revisar `prepared.preview.to_review_data()` mediante una
interfaz autenticada futura. Solo entonces el backend llama a
`confirm(content, filename=..., prepared=prepared, confirmed=True)`; un valor distinto del
booleano `True` o un archivo/nombre/sucursal diferente se rechaza antes de consultar la DB. El
objeto `PreparedPriceImport` es estado interno del backend y no debe construirse desde datos del
cliente o del modelo.

`confirm` abre una transacción SQLite con bloqueo de escritura, vuelve a parsear y revisar el
catálogo y compara el impacto actual con el preview aprobado. Si el archivo o los precios
cambiaron, o aparece cualquier error, rechaza la operación. Después crea solo precios ausentes,
actualiza solo importes diferentes y omite los iguales. Los repositorios derivan `branch_id` de
la sucursal configurada; jamás de una celda. Los importes pasan como `Decimal` por `PriceData`.
La transacción confirma todo al final o revierte todos los cambios ante un fallo, incluso si ya
se había escrito una fila. Un fallo de DB se expone mediante un error seguro sin SQL ni valores
del archivo.

El recibo exitoso incluye código de sucursal, huella SHA-256 y conteos de altas, cambios y filas
iguales. Sirve como base de trazabilidad, sin guardar el XLSX ni datos personales. F5.5 deberá
añadir el registro duradero de quién/cuándo/archivo lógico y los reportes. El servicio todavía
no se expone por HTTP; la futura ruta administrativa tendrá que exigir autenticación y
autorización, conservar el objeto preparado solo en backend y realizar la confirmación explícita.
Ningún texto de la hoja se convierte en instrucciones para OpenAI.
