# Fase 4 — Fuente, consulta y política FAQ (F4.1–F4.3)

## Fuente elegida

Cada instalación tendrá una **tabla TSV de texto UTF-8** propia, por ejemplo
`sucursal-1.assistant-faq.tsv`. Es una fuente de contenido aprobada por el negocio, no una base
consultada directamente por el asistente en F4.1. Los archivos reales con ese sufijo están
ignorados por Git; solo se versiona [un ejemplo ficticio](../examples/faq_table.example.tsv).

La primera línea debe tener, en este orden exacto, cinco columnas separadas por tabuladores:

```text
schema_version<TAB>branch_code<TAB>category<TAB>question<TAB>answer
```

Cada línea posterior representa un registro. Se usa la convención TSV del módulo `csv` de Python
para entrecomillar campos cuando sea necesario. Los campos `question` y `answer` son texto plano,
sin tabuladores, saltos de línea ni otros caracteres de control. No se admiten columnas extra,
campos faltantes ni espacios al inicio o al final de las preguntas y respuestas.

| Columna | Contrato |
|---|---|
| `schema_version` | Obligatoria, valor literal `1` en cada fila. |
| `branch_code` | Obligatoria en cada fila; código válido de 2 a 48 caracteres y exactamente igual a `ASSISTANT_BRANCH_CODE` de la instalación. |
| `category` | Uno de los cinco códigos de la tabla siguiente. |
| `question` | Pregunta de texto plano, entre 1 y 240 caracteres. |
| `answer` | Respuesta aprobada de texto plano, entre 1 y 1200 caracteres. |

Categorías permitidas:

| Código | Uso previsto |
|---|---|
| `general` | Orientación general que no pertenece a otra categoría. |
| `servicios` | Servicios ofrecidos, previa validación por personal. |
| `pagos` | Información validada sobre formas de pago. |
| `entregas` | Información validada sobre opciones de entrega. |
| `politicas` | Políticas comerciales aprobadas. |

El ejemplo usa `sucursal-demo` y respuestas marcadas `EJEMPLO FICTICIO`; no describe condiciones
reales. Para crear la fuente de una instalación, copiarlo a un archivo local con el sufijo
`.assistant-faq.tsv`, sustituir el código de **todas** las filas por el código configurado y
reemplazar las respuestas con texto aprobado por el negocio. Nunca incluir claves, tokens, datos
de pago, datos personales innecesarios ni instrucciones para el modelo.

## Validación y alcance

`backend.app.schemas.faq` define la cabecera, categorías y campos admitidos. La función
`validate_scoped_faq_row` de `backend.app.services.faq_scope` valida una fila y exige un
`BranchScope` creado desde `AssistantSettings`; compara el código de la tabla con el código del
backend y devuelve un registro inmutable cuyo alcance se toma del backend. Rechaza filas de otra
sucursal, aunque su texto sea válido. Ni el cliente ni el modelo pueden elegir el alcance. La
cabecera se comprueba con `validate_faq_columns`.

La tabla es **dato no confiable**, no instrucciones privilegiadas. Su contenido no puede modificar
el system prompt, activar herramientas, cambiar precios ni conceder permisos. Preguntas y
respuestas deben presentarse como contenido recuperado, con la sucursal ya autorizada por código;
no se deben promover a mensajes de sistema. Los precios, existencias, horarios, ubicaciones y
pedidos siguen dependiendo de sus fuentes y lógica determinísticas correspondientes.

## Carga y búsqueda local (F4.2)

`FAQService` recibe una ruta local elegida por el backend y un `BranchScope` construido desde
configuración. Lee el TSV completo **una sola vez**, valida cabecera y todas las filas, y conserva
un snapshot inmutable en memoria. Si una fila apunta a otra sucursal, tiene un campo inválido o
el archivo falla, no queda disponible ninguna respuesta parcial. Un archivo con solo cabecera es
válido y devuelve cero resultados. Para aplicar cambios del archivo se debe construir un servicio
nuevo; no hay recarga por mensaje.

La lectura está limitada a **256 KiB** y **500 filas**, con decodificación UTF-8 estricta y parser
TSV estricto. Extensión distinta de `.tsv`, archivo ausente, permisos insuficientes, contenido
demasiado grande, texto mal codificado o formato inválido producen `FAQSourceError`. El error
público no contiene ruta, fila ni contenido del archivo.

`search_faq(query)` acepta una cadena de hasta **240 caracteres**. Rechaza entradas vacías, no
imprimibles o sin caracteres alfanuméricos con `FAQQueryInputError`. Normaliza Unicode, mayúsculas,
acentos y espacios para comparar **solo la pregunta**. Ordena coincidencias exactas, de prefijo y
parciales de manera determinista, devuelve como máximo cinco registros inmutables y devuelve una
tupla vacía si no hay coincidencias. La firma no acepta sucursal desde el cliente o el modelo.

La ruta de la fuente debe seleccionarse en código o configuración backend de la instalación,
nunca desde el mensaje de WhatsApp ni desde argumentos de OpenAI. El servicio no llama a OpenAI,
no escribe a la base de datos y no está conectado a rutas HTTP o al orquestador. La política para
preguntas desconocidas y respuestas conversacionales corresponde a F4.3 y fases posteriores.

Ejemplo de uso **interno** después de preparar el archivo de esa instalación:

```python
from pathlib import Path

from backend.app.core.config import AssistantSettings
from backend.app.services.branch_scope import BranchScope
from backend.app.services.faq_service import FAQService

scope = BranchScope.from_settings(AssistantSettings())
faq = FAQService(Path("sucursal-1.assistant-faq.tsv"), branch_scope=scope)
coincidencias = faq.search_faq("¿Qué formas de pago aceptan?")
```

## Respuesta confirmada y desconocidos (F4.3)

`FAQResponsePolicy` usa el servicio local y decide sin OpenAI ni herramientas. Solo entrega un
`FAQAnswer` si hay **una coincidencia exacta y única** de pregunta, normalizada por mayúsculas,
acentos, espacios y signos de interrogación externos. El resultado identifica su fuente como
`faq` y su nivel de confianza como `untrusted_source`: el texto sigue siendo dato recuperado,
nunca instrucciones para el sistema o para herramientas.

Una pregunta sin coincidencias devuelve `FAQFallback` con texto fijo que reconoce que no hay
respuesta confirmada. Una coincidencia parcial o varias coincidencias exactas también devuelve
texto fijo y pide reformular o consultar al personal. Ningún fallback copia la consulta ni inventa
precios, existencias, horarios, ubicaciones, políticas o confirmaciones comerciales. Una consulta
inválida mantiene el error de validación de F4.2.

Cada fallback lleva una propuesta `request_human_help` con razón cerrada (`faq_unknown` o
`faq_ambiguous`) y `executed=False`. Es una intención conceptual: no contacta a nadie, no guarda
teléfono ni conversación y no afirma que una persona haya respondido. La ejecución, autorización,
idempotencia y auditoría del traspaso humano pertenecen a fases posteriores.

El texto del usuario y el de la tabla pueden contener intentos de prompt injection. La política
no los ejecuta, no cambia de sucursal y no concede privilegios. Una instrucción añadida a una
pregunta conocida deja de ser una coincidencia exacta y recibe fallback. El contenido FAQ que se
use más adelante con un modelo debe conservar su condición de dato no confiable. Para hechos
comerciales críticos, la fuente sigue siendo el servicio determinista correspondiente, no esta
política FAQ.
