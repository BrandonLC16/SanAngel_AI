# Fase 5 — Plantilla y parser de precios (F5.1–F5.2)

La plantilla versionada es [`price_import.example.xlsx`](../examples/price_import.example.xlsx).
Contiene solo datos ficticios. Cada archivo de trabajo pertenece a **una instalación y una
sucursal**. Se copia con un nombre terminado en `.assistant-prices.xlsx`, que Git ignora, y se
reemplazan el código de sucursal y todas las filas de ejemplo antes de usarlo. F5.2 valida el
archivo en memoria; preview, confirmación y transacción pertenecen a las subfases siguientes.

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

La pareja `(product_id, unit)` debe aparecer una sola vez por archivo. Un precio importado será
el precio **actual** después de la confirmación y escritura transaccional de fases posteriores;
`verified_on` no cambia `created_at` ni `updated_at` de la base por sí solo. El backend debe
resolver `product_id` dentro de la sucursal configurada y comprobar que `product_name` coincide
antes de proponer cualquier actualización. La representación en Excel es numérica; el parser
deberá convertir el importe a `Decimal` sin pasar un `float` a `PriceData`.

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

La existencia de `product_id` y la coincidencia de `product_name` con la base de la sucursal
configurada requieren consulta de solo lectura durante el preview de F5.3. La importación futura
seguirá validar → preview → confirmar → transacción → auditoría. Ningún texto de la hoja se
convierte en instrucciones para OpenAI.
