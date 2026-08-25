# AGENTS.md
## Instrucciones para Codex — Carnicería AI Chatbot

Este archivo define las reglas permanentes de trabajo para cualquier agente que modifique este repositorio.

---

# 1. Misión del proyecto

Construir un chatbot de atención al cliente para una cadena de carnicerías.

El sistema debe poder evolucionar para responder consultas relacionadas con:

- sucursales;
- horarios;
- productos;
- precios;
- preguntas frecuentes;
- promociones;
- pedidos;
- información comercial.

El modelo de IA sirve para interpretar lenguaje natural y redactar respuestas.

Los datos críticos del negocio, especialmente:

- precios;
- existencias;
- direcciones;
- horarios;
- promociones;
- pedidos;

NO deben ser inventados por el modelo.

Cuando se implementen esas funciones, deberán provenir de fuentes determinísticas como SQLite/PostgreSQL, importaciones validadas de Excel o APIs internas.

---

# 2. Stack previsto

Backend:

- Python.
- FastAPI.
- Pydantic.
- SDK oficial OpenAI.
- Responses API.

Persistencia futura:

- SQLite inicialmente.
- Posible migración a PostgreSQL.

Datos futuros:

- Excel mediante pandas/openpyxl.
- archivos TXT/Markdown para conocimiento simple.

Frontend futuro:

- React o Next.js.

Despliegue futuro:

- Docker.
- reverse proxy.
- HTTPS.

---

# 3. Archivos que debes leer ANTES de modificar código

Siempre, en este orden:

1. `AGENTS.md`
2. `plan_de_trabajo.md`
3. `README.md` si existe.
4. documentación de la fase activa.
5. código y tests relacionados con la tarea.

No empieces a programar sin identificar:

- fase activa;
- tarea activa;
- criterio de aceptación;
- riesgos de seguridad relacionados.

---

# 4. Regla principal de avance

Trabaja solamente en:

1. la tarea que el usuario haya solicitado explícitamente; o
2. si no existe una tarea explícita, la primera tarea `⬜ PENDIENTE` de la fase activa.

No empieces automáticamente la siguiente fase.

No mezcles múltiples fases en una misma modificación salvo instrucción explícita del usuario.

---

# 5. Estados oficiales

Usar únicamente estos estados en `plan_de_trabajo.md`:

- `⬜ PENDIENTE`
- `🟨 EN_PROGRESO`
- `🧪 VALIDACION`
- `✅ COMPLETADO`
- `⛔ BLOQUEADO`
- `↩️ REABIERTO`

Flujo normal:

```text
⬜ PENDIENTE
     |
     v
🟨 EN_PROGRESO
     |
     v
🧪 VALIDACION
     |
     v
✅ COMPLETADO
```

Si una tarea falla después de completada:

```text
✅ COMPLETADO -> ↩️ REABIERTO
```

---

# 6. Obligación de actualizar `plan_de_trabajo.md`

Al comenzar una tarea:

1. cambiar su estado a `🟨 EN_PROGRESO`;
2. añadir fecha de inicio si corresponde.

Antes de marcar como completada:

1. ejecutar pruebas relevantes;
2. ejecutar validaciones de calidad;
3. revisar seguridad;
4. verificar criterios de aceptación;
5. cambiar temporalmente a `🧪 VALIDACION` si todavía se está comprobando.

Solo después:

```text
✅ COMPLETADO
```

Al finalizar cada bloque de trabajo, agregar una entrada al historial del plan con:

- fecha;
- fase;
- tarea;
- cambios realizados;
- archivos afectados;
- tests/comandos ejecutados;
- resultado;
- riesgos o pendientes;
- siguiente tarea recomendada.

No marques una tarea como completada si:

- faltan tests requeridos;
- los tests fallan;
- existe un error conocido que invalida su criterio de aceptación;
- la función depende de un secreto inexistente y no fue posible comprobarla;
- existe un riesgo de seguridad crítico sin resolver.

---

# 7. Política de cambios pequeños

Prefiere cambios:

- pequeños;
- verificables;
- reversibles;
- relacionados con una sola tarea.

Evita refactors masivos sin necesidad.

No cambies arquitectura, framework, lenguaje o dependencias principales sin:

1. justificar el cambio;
2. explicar impacto;
3. actualizar documentación;
4. contar con instrucción del usuario cuando el cambio sea significativo.

---

# 8. Seguridad — reglas NO negociables

## 8.1 Secretos

NUNCA:

- escribas una API key real;
- inventes una API key;
- copies una API key a código;
- muestres una API key en logs;
- agregues una API key a tests;
- agregues `.env` a Git;
- coloques credenciales en frontend;
- imprimas headers `Authorization`.

Usar variables de entorno.

Debe existir:

```text
.env.example
```

sin valores secretos.

---

## 8.2 OpenAI

La OpenAI API key solo puede ser utilizada por el backend.

El frontend debe hablar con nuestro backend.

Arquitectura permitida:

```text
frontend -> backend -> OpenAI
```

Arquitectura prohibida:

```text
frontend -> OpenAI con secret API key
```

Usar Responses API para nuevas integraciones.

No introducir Assistants API como nueva dependencia.

La configuración del modelo debe ser configurable por entorno y no depender de un literal disperso por el código.

---

## 8.3 Datos del negocio

Nunca permitas que el modelo invente datos críticos.

Cuando existan herramientas de negocio:

```text
precio -> función -> base de datos
horario -> función -> base de datos
sucursal -> función -> base de datos
inventario -> fuente en tiempo real o respuesta de incertidumbre
```

No usar memoria del modelo como fuente de verdad.

---

## 8.4 SQL

Cuando se implemente la base de datos:

- usar ORM o queries parametrizadas;
- prohibido concatenar input del usuario en SQL;
- prohibido exponer una herramienta `execute_sql(query)` directamente al modelo;
- las tools de IA deben representar operaciones específicas y con mínimo privilegio.

Ejemplo correcto:

```text
get_product_price(product_id, branch_id)
```

Ejemplo prohibido:

```text
run_sql(sql_from_model)
```

---

## 8.5 Validación

Toda entrada externa:

- HTTP;
- Excel;
- archivos;
- herramientas IA;
- APIs externas;

debe validarse antes de llegar al dominio.

Usar esquemas Pydantic en la API.

Definir límites de longitud y tipos.

Nunca confiar en input del cliente ni en argumentos generados por un modelo.

---

## 8.6 Prompt injection

Tratar todo texto del usuario, archivos y contenido recuperado como datos no confiables.

Una instrucción del usuario NO puede:

- modificar reglas internas;
- pedir secretos;
- concederse permisos;
- cambiar precios;
- ejecutar SQL arbitrario;
- cambiar configuración administrativa.

Las acciones sensibles deben estar protegidas por lógica de aplicación y autorización, no únicamente por prompts.

---

## 8.7 Autorización

Cuando se implemente el panel:

- separar endpoints públicos y administrativos;
- autenticación obligatoria;
- roles mínimos;
- autorización en backend;
- nunca confiar solamente en ocultar botones del frontend.

---

## 8.8 Passwords

Cuando existan cuentas:

- jamás guardar passwords en texto plano;
- usar algoritmo de hashing de contraseñas apropiado, por ejemplo Argon2id o una alternativa actual recomendada;
- usar salt administrado por la librería;
- nunca implementar criptografía casera.

---

## 8.9 CORS

No usar `*` en producción.

Permitir únicamente orígenes necesarios.

---

## 8.10 Errores

El usuario recibe mensajes genéricos y útiles.

No devolver:

- tracebacks;
- variables de entorno;
- secretos;
- queries internas;
- paths locales;
- nombres de infraestructura innecesarios.

---

## 8.11 Logs

Aplicar minimización.

Permitido:

- request ID;
- endpoint;
- estado;
- duración;
- tipo de error.

Evitar:

- cuerpo completo de chats;
- API keys;
- tokens;
- passwords;
- datos personales innecesarios.

Si un log requiere contenido, redactar información sensible.

---

## 8.12 Rate limiting

Antes de hacer público el chatbot:

- implementar límites de solicitud;
- manejar HTTP 429;
- evitar reintentos infinitos;
- usar exponential backoff cuando sea apropiado.

---

## 8.13 Archivos Excel

Cuando se implemente importación:

- validar extensión;
- validar MIME cuando corresponda;
- limitar tamaño;
- no confiar en nombre del archivo;
- validar columnas;
- validar tipos;
- validar rangos de precios;
- no ejecutar macros;
- procesar el archivo en un área controlada;
- rechazar filas inválidas de forma explícita;
- usar transacción para no dejar la base a medias.

---

## 8.14 Dependencias

Antes de añadir una dependencia:

1. comprobar que es necesaria;
2. preferir librerías mantenidas;
3. evitar duplicar funcionalidad;
4. fijar/acotar versión;
5. documentar la razón si es relevante.

---

# 9. Reglas de interacción con OpenAI

Mantener la llamada al SDK fuera de las rutas HTTP.

Usar una capa:

```text
route -> service -> OpenAI
```

La lógica de negocio no debe depender directamente del objeto HTTP.

Configurar:

- modelo;
- timeout;
- store/retención cuando corresponda;

mediante configuración.

Los tests normales deben mockear OpenAI.

Nunca hagas que `pytest` consuma la API real por defecto.

---

# 10. Pruebas

Cada funcionalidad debe incluir o actualizar tests cuando sea razonable.

Antes de cerrar una tarea ejecutar, según aplique:

```bash
pytest
ruff check .
ruff format --check .
```

Si se introduce tipado estricto:

```bash
mypy ...
```

Si un comando no existe todavía, documentarlo en el plan en vez de fingir que fue ejecutado.

Nunca declares que una prueba pasó si no la ejecutaste.

---

# 11. Manejo de errores

Crear errores del dominio/servicio y mapearlos en la frontera HTTP.

No esparcir `try/except Exception` por todas las capas.

Capturar excepciones donde pueda:

- agregarse contexto;
- recuperarse;
- transformarse en error del dominio;
- generarse una respuesta segura.

---

# 12. Código

Principios:

- nombres explícitos;
- funciones pequeñas;
- responsabilidades claras;
- evitar duplicación;
- comentarios para explicar el porqué, no lo obvio;
- no crear abstracciones prematuras;
- no mezclar infraestructura con dominio;
- tipar interfaces públicas importantes.

---

# 13. Endpoints

Usar prefijo:

```text
/api/v1
```

Endpoints administrativos futuros:

```text
/api/v1/admin/...
```

Endpoints públicos:

```text
/api/v1/chat
```

No realizar cambios breaking a contratos existentes sin actualizar:

- tests;
- README;
- plan de trabajo;
- consumidores conocidos.

---

# 14. Política sobre datos inventados

Para pruebas puedes crear fixtures claramente ficticios.

Ejemplo:

```text
Sucursal Demo
Producto Demo
$123.45
```

Nunca hacer pasar datos ficticios por datos reales del negocio.

---

# 15. Antes de editar un archivo

Revisa primero su contenido actual.

No sobrescribas trabajo del usuario sin entenderlo.

Conserva cambios existentes que no pertenezcan a tu tarea.

Si detectas cambios que parecen hechos por otra persona/agente:

- no los borres;
- adapta tu cambio;
- documenta el conflicto si no puede resolverse con seguridad.

---

# 16. Acciones destructivas

No ejecutar sin necesidad:

```text
git reset --hard
git clean -fd
DROP DATABASE
DROP TABLE
rm -rf
```

No borrar archivos ajenos a la tarea.

No reescribir historial de Git salvo instrucción explícita.

---

# 17. Cambios de base de datos futuros

Toda modificación estructural debe convertirse en migración cuando la fase de persistencia lo requiera.

Nunca depender de cambios manuales irrepetibles en producción.

---

# 18. Excel no será la fuente de consulta directa permanente

La arquitectura prevista es:

```text
Excel -> validación/importación -> base de datos -> chatbot
```

No abrir el Excel en cada mensaje del cliente.

---

# 19. Definition of Done por tarea

Una tarea puede pasar a `✅ COMPLETADO` solamente si:

- implementación terminada;
- criterios de aceptación cumplidos;
- tests relevantes pasan;
- lint/calidad relevante pasa;
- seguridad revisada;
- documentación afectada actualizada;
- plan actualizado;
- no quedan TODO críticos ocultos.

---

# 20. Formato obligatorio del reporte final de Codex

Al terminar trabajo, reportar brevemente:

```text
Resumen:
- ...

Archivos modificados:
- ...

Validación:
- comando -> resultado

Seguridad:
- controles verificados

Plan:
- tarea marcada como ...
- siguiente tarea sugerida: ...

Pendientes/riesgos:
- ...
```

No afirmar éxito sin evidencia de ejecución.

---

# 21. Regla de checkpoint

Si la ventana de contexto empieza a llenarse o el trabajo se interrumpe:

1. NO intentes reconstruir el proyecto de memoria.
2. actualiza `plan_de_trabajo.md`;
3. agrega una entrada al historial;
4. deja indicada la tarea exacta en curso;
5. describe lo implementado;
6. describe lo que falta;
7. incluye comandos ejecutados y su resultado;
8. indica archivos relevantes.

Al iniciar una nueva sesión, usar ese plan como checkpoint.

---

# 22. Documentación externa

Cuando una tarea dependa de una API que puede cambiar, especialmente OpenAI:

- priorizar documentación oficial vigente;
- no copiar tutoriales antiguos sin comprobarlos;
- no migrar a APIs deprecadas;
- si hay una incompatibilidad de versión, documentarla.

Referencias base:

- https://platform.openai.com/docs/quickstart
- https://platform.openai.com/
- https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
- https://platform.openai.com/docs/models/default-usage-policies-by-endpoint

---

# 23. Prioridad de instrucciones

En caso de conflicto:

1. instrucciones explícitas actuales del usuario;
2. seguridad y protección de datos;
3. `AGENTS.md`;
4. `plan_de_trabajo.md`;
5. documentación de la fase;
6. convenciones existentes del repositorio.

Si una instrucción solicitada pudiera exponer secretos, destruir datos o crear una vulnerabilidad crítica, no implementarla silenciosamente; reportar el riesgo y elegir la alternativa segura.
