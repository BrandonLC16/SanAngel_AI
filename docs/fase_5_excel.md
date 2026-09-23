# Fase 5 — Contrato de la plantilla de precios (F5.1)

La plantilla versionada es [`price_import.example.xlsx`](../examples/price_import.example.xlsx).
Contiene solo datos ficticios. Cada archivo de trabajo pertenece a **una instalación y una
sucursal**. Se copia con un nombre terminado en `.assistant-prices.xlsx`, que Git ignora, y se
reemplazan el código de sucursal y todas las filas de ejemplo antes de usarlo. La carga todavía
no está implementada: F5.1 define únicamente el contrato; F5.2 incorporará el parser y las
validaciones, seguidas por preview, confirmación y transacción en las subfases previstas.

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

El archivo es input no confiable. El parser futuro debe comprobar extensión, tamaño, estructura
del paquete, hoja, cabecera, versión, tipos, límites, duplicados y que el código de `E3` coincide
con el alcance backend **antes** de cualquier escritura. Debe rechazar macros, fórmulas, vínculos
externos y contenido de otras sucursales; la validación visual de Excel no sustituye estas
comprobaciones. La importación seguirá el flujo validar → preview → confirmar → transacción →
auditoría. Ningún texto de la hoja se convierte en instrucciones para OpenAI.
