# Fase 6 — Contratos, handlers, dispatcher y loop (F6.1–F6.4)

F6.1 define cuatro funciones para Responses API. Sigue sin conectar OpenAI a los servicios de
negocio ni ejecutar tool calls. Los schemas usan `type: "function"`, `strict: true`, un objeto
`parameters` con todas sus propiedades en `required` y `additionalProperties: false`, según la
[documentación oficial de function calling](https://developers.openai.com/api/docs/guides/function-calling#strict-mode).
Los límites de número y el patrón de unidad usan el subconjunto admitido de
[JSON Schema para Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas).
La documentación indica que ciertas restricciones de patrón y rango no están disponibles para
modelos ajustados; la integración futura deberá comprobar la compatibilidad del modelo configurado.

| Tool | Argumentos del modelo | Contrato |
|---|---|---|
| `get_product_price` | `product_id`: entero positivo de hasta 64 bits; `unit`: código minúsculo de hasta 24 caracteres | Precio exacto por producto y unidad. |
| `get_branch_info` | Objeto vacío `{}` | Datos de la sucursal ya configurada. |
| `search_faq` | `query`: pregunta de hasta 240 caracteres | Búsqueda en la FAQ validada de la sucursal. |
| `request_human_help` | `reason`: `customer_requested`, `faq_unknown` o `faq_ambiguous` | Solo propuesta conceptual; no contacta al personal. |

`get_tool_schemas()` devuelve una copia independiente de la allowlist. Ningún schema contiene
`branch_id` o `branch_code`, SQL libre, precio escrito, credenciales ni datos personales. La
descripción de una tool no concede privilegios: el backend solo aceptará los cuatro nombres.

`validate_tool_call(name, arguments_json, assistant_settings=...)` rechaza un nombre desconocido
antes de parsear argumentos. Exige JSON de hasta 4096 bytes, sin claves duplicadas ni constantes
no estándar. Los modelos Pydantic son estrictos, inmutables y prohíben propiedades extra. Se
validan rangos, unidad y texto de FAQ otra vez en backend; un schema remoto no sustituye esta
validación. Los errores no incluyen los argumentos recibidos.

Después de validar nombre y argumentos, el backend crea `BranchScope` desde
`AssistantSettings`. La sucursal nunca se deriva del JSON generado por el modelo. El resultado
`ValidatedToolCall` contiene esa identidad backend. La implementación F6.2 exige que cada handler
reciba también el mismo `BranchScope` configurado en backend y rechaza llamadas de otra sucursal,
de otra tool o con argumentos de otro tipo antes de acceder a datos.

`ToolHandlers` ofrece cuatro métodos explícitos, sin dispatcher ni dependencia del modelo:

- `get_product_price` consulta el servicio comercial con producto, unidad y sucursal configurada.
  Devuelve `ProductPriceInfo` con `Decimal` o `ProductPriceNotFoundResult(status="not_found")`.
  Producto inexistente, inactivo, ajeno o sin precio para la unidad tienen el mismo resultado;
  una sucursal no configurada sigue siendo error de servicio.
- `get_branch_info` devuelve `BranchInfo` de la sucursal configurada.
- `search_faq` usa `FAQService` y `FAQResponsePolicy`. Solo una coincidencia exacta y única
  devuelve `FAQAnswer`, marcado `trust_level="untrusted_source"`; sin coincidencia o con
  ambigüedad devuelve `FAQFallback` con texto fijo y propuesta de ayuda. Un archivo con filas de
  otra sucursal se rechaza entero.
- `request_human_help` devuelve `HumanHelpProposal(executed=False)` para uno de los tres motivos
  permitidos. No contacta al personal, guarda datos personales ni confirma una transferencia.

Las rutas y el archivo FAQ son configuración interna. Ningún método acepta sucursal, SQL, cambios
de precio ni una acción comercial de escritura desde argumentos del modelo. Las pruebas de F6.2
invocan estos métodos localmente sin OpenAI. La selección y ejecución centralizada de tool calls
se implementa en F6.3.

`ToolDispatcher.dispatch(name, arguments_json)` usa un mapa inmutable de los cuatro nombres a
métodos explícitos de `ToolHandlers`. Rechaza un nombre desconocido (incluido `execute_sql`) antes
de parsear argumentos o abrir una sesión. Después llama a `validate_tool_call`, que vuelve a
validar el JSON y liga la sucursal desde `AssistantSettings`. El dispatcher construye el handler
con ese mismo alcance y con una sesión nueva creada dentro del worker; no usa `getattr`, `eval`,
SQL generado por el modelo ni una función proporcionada en los argumentos.

El timeout predeterminado es de 3 segundos y se puede configurar en backend entre más de cero y
30 segundos. Incluye la espera por uno de los cuatro workers y la ejecución del handler. Al
vencer, el solicitante recibe `ToolExecutionTimeoutError` sin contenido del argumento. La tarea
de lectura que ya comenzó puede continuar hasta terminar: el timeout limita la espera del
solicitante, no interrumpe de forma forzosa SQLite o la lectura del archivo. La concurrencia
global está acotada a cuatro tareas, incluso cuando vencen los timeouts; una sesión de base no
se comparte entre threads. Los servicios subyacentes mantienen límites de tamaño para FAQ y
consultas de solo lectura.

F6.4 añade `OpenAIService.generate_reply_with_tools(message, dispatcher)`. Hace una solicitud a
Responses API con los cuatro schemas, detecta cada elemento `function_call`, ejecuta el nombre y
argumentos mediante el dispatcher, agrega un `function_call_output` con el mismo `call_id` y
solicita la respuesta final. Se preservan todos los elementos de `response.output`, incluidos
los de razonamiento, al construir cada entrada siguiente con `store` configurado; esta secuencia
sigue la [guía oficial de function calling](https://developers.openai.com/api/docs/guides/function-calling#handling-function-calls)
y la [gestión manual de estado](https://developers.openai.com/api/docs/guides/conversation-state#manually-manage-conversation-state).
Las llamadas se ejecutan en orden y se devuelve texto solo si la respuesta está completa y
contiene un mensaje final no vacío.

El loop permite hasta tres rondas de ejecución de tools y cuatro llamadas por respuesta. La
cuarta respuesta de API debe ser final: si vuelve a solicitar una tool, se rechaza sin ejecutarla.
Cada respuesta está limitada a 16 elementos y solicita como máximo 1024 tokens de salida.
Los resultados tipados se serializan a JSON de hasta 8192 bytes; el `Decimal` se mantiene como
cadena y la respuesta FAQ conserva `trust_level="untrusted_source"`. El prompt indica que el
texto recuperado es dato, no instrucción, y que una propuesta de ayuda no es un traspaso
ejecutado. Llamadas desconocidas, argumentos inválidos y respuestas incompletas fallan de forma
cerrada sin devolver argumentos al modelo. El loop comprueba que el dispatcher y el servicio
OpenAI comparten la sucursal configurada antes de llamar al proveedor.

Este método tiene pruebas mockeadas, sin red. El endpoint de chat y WhatsApp conservan su flujo
actual de texto; la composición operativa con el dispatcher aún requiere configuración backend
del archivo FAQ y se abordará en una subfase posterior. Un fallo o timeout de tool nunca debe
convertirse en un dato comercial supuesto.
