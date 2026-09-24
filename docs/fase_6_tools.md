# Fase 6 — Tools y desambiguación de producto (F6.1–F6.7)

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

F6.5 añade `ProductDisambiguationService.resolve(product_query)` para un término de producto
explícito. Recibe `BranchScope` del backend y reutiliza `CommercialQueryService`: la respuesta
indica el nombre verificado de la propia sucursal, sin aceptar un selector de sucursal. Una
coincidencia exacta única devuelve el producto de esa sucursal; una única coincidencia parcial
solo sugiere el nombre y pide confirmación, sin entregar un ID seleccionable. Varias coincidencias
devuelven hasta cinco opciones de la sucursal propia y piden precisar cuál; ninguna coincidencia
pide confirmar el nombre. La respuesta de desambiguación no incluye precios. Una mención de otra
tienda dentro del término no cambia el alcance y puede resultar en `not_found` hasta que el
cliente aclare el producto. Solo después de identificarlo se puede consultar el precio mediante
`get_product_price`, que vuelve a aplicar el mismo alcance backend.

Este servicio es determinista y se prueba sin modelo ni red. No agrega una quinta tool a la
allowlist de F6.1–F6.4. La extracción del término de producto y su composición con el flujo de
WhatsApp siguen pendientes; el código actual no afirma resolver automáticamente un mensaje libre.

## F6.6 — Pruebas de seguridad y auditoría mínima

Las pruebas offline cubren instrucciones hostiles en el mensaje del cliente y en una respuesta
FAQ, llamadas a tools inexistentes, argumentos extra o malformados, texto SQL en argumentos y
destinos de exfiltración. Una solicitud del modelo no puede agregar una tool, cambiar la sucursal
configurada, ejecutar SQL libre ni convertir `request_human_help` en una acción ejecutada.
La FAQ conserva `trust_level="untrusted_source"` al volver al modelo.

`ToolDispatcher` registra una línea por intento con únicamente `tool=<nombre permitido|unsupported>`
y `status=<ok|not_found|fallback|proposed|rejected|timeout|error>`. Un nombre desconocido se
registra como `unsupported` para evitar inyección en logs. No registra argumentos, resultados,
identificadores de cliente, texto FAQ, direcciones, importes, secretos ni detalles de excepciones.
El registro describe el resultado del handler; un fallo posterior al serializar la respuesta no
se registra como resultado del handler.

Estas pruebas demuestran el límite de privilegios del backend con un proveedor simulado. No
demuestran que un modelo real nunca redacte una afirmación comercial no respaldada en su texto
final. Antes de conectar este loop al canal del cliente, la integración debe tratar ese riesgo
por separado y comprobar el comportamiento con casos representativos.

## F6.7 — Cierre y revisión de costos

Las pruebas de cierre comprueban el presupuesto agregado del loop: hasta cuatro solicitudes
`responses.create`, doce ejecuciones de tools (cuatro por cada una de tres rondas) y ninguna
ejecución en la cuarta respuesta si vuelve a pedir una tool. Cada solicitud fija
`max_output_tokens=1024` y `parallel_tool_calls=False`; cada resultado de tool se limita a 8192
bytes. Una respuesta con más de 16 elementos o más de cuatro llamadas a función se rechaza antes
de ejecutar sus tools. El dispatcher usa cuatro workers como máximo y timeout de espera de 3 segundos
por defecto, configurable hasta 30. El mensaje inicial tiene límite configurable de caracteres.

Estos límites acotan el trabajo de aplicación, pero no establecen un presupuesto monetario. La
[documentación oficial de OpenAI sobre function calling](https://developers.openai.com/api/docs/guides/function-calling#token-usage)
indica que los schemas de tools consumen tokens de entrada; el loop también reenvía el contexto
anterior en cada solicitud. El [conteo de tokens](https://developers.openai.com/api/docs/guides/token-counting)
incluye estructura y contenido que una estimación por caracteres no refleja. Además, el SDK puede
reintentar solicitudes según `OPENAI_MAX_RETRIES` (2 por defecto, hasta 5) y el timeout de OpenAI
se configura aparte (30 segundos por defecto, hasta 120). Se requieren métricas, alertas y un
presupuesto operativo antes de habilitar este flujo para clientes.

F6.1–F6.7 cierran el núcleo interno de tools de solo lectura y sus pruebas offline. El endpoint
interno y WhatsApp siguen usando el flujo de texto previo; la composición operativa con el
dispatcher, la fuente FAQ por instalación y la validación de respuestas finales quedan pendientes
para trabajo posterior explícito. Esta fase no declara una integración de tools en producción.
