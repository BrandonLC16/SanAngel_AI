# Fase 6 — Contratos e implementaciones de tools (F6.1–F6.2)

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
| `get_product_price` | `product_id`: entero positivo de hasta 64 bits; `unit`: código minúsculo de hasta 24 caracteres | Consulta futura de precio exacto por producto y unidad. |
| `get_branch_info` | Objeto vacío `{}` | Consulta futura de la sucursal ya configurada. |
| `search_faq` | `query`: pregunta de hasta 240 caracteres | Búsqueda futura en la FAQ validada de la sucursal. |
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
queda para F6.3.
