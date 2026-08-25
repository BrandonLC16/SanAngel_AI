# plan_de_trabajo.md
## Chatbot IA para Carnicerías

**Última actualización:** 2026-08-25  
**Fase activa:** Fase 1  
**Estado global:** 🟨 EN DESARROLLO  
**Propósito:** este archivo es el checkpoint oficial del proyecto y debe actualizarse después de cada avance relevante.

---

# 1. Estados oficiales

| Estado | Significado |
|---|---|
| ⬜ PENDIENTE | Todavía no iniciado |
| 🟨 EN_PROGRESO | Trabajo activo |
| 🧪 VALIDACION | Implementado, pendiente de comprobar |
| ✅ COMPLETADO | Criterios cumplidos y verificados |
| ⛔ BLOQUEADO | No puede continuar por una dependencia |
| ↩️ REABIERTO | Se había cerrado pero requiere corrección |

---

# 2. Reglas de actualización

Codex debe actualizar este archivo cada vez que avance el proyecto.

## Al comenzar

Cambiar:

```text
⬜ PENDIENTE -> 🟨 EN_PROGRESO
```

## Antes de cerrar

Cambiar:

```text
🟨 EN_PROGRESO -> 🧪 VALIDACION
```

Ejecutar:

- tests;
- lint;
- controles de seguridad;
- criterios de aceptación.

Solo si todo lo requerido pasa:

```text
🧪 VALIDACION -> ✅ COMPLETADO
```

## Si existe impedimento

```text
🟨 EN_PROGRESO -> ⛔ BLOQUEADO
```

y registrar exactamente:

- qué falta;
- por qué bloquea;
- cómo resolverlo.

---

# 3. Principios del proyecto

1. OpenAI interpreta lenguaje; la base de datos será la fuente de verdad comercial.
2. La IA nunca debe inventar precios, existencia, horarios o sucursales.
3. La API key solo existe en backend.
4. La seguridad se implementa durante todas las fases, no al final.
5. Los tests normales no consumen OpenAI.
6. Los cambios deben ser pequeños y verificables.
7. Una fase no comienza automáticamente al terminar otra.
8. Todo avance significativo debe quedar documentado aquí.

---

# 4. FASE 1 — Backend mínimo + OpenAI

**Objetivo:** FastAPI operativo y primera respuesta real mediante OpenAI Responses API.

**Estado:** 🟨 EN_PROGRESO

## F1.1 — Inicialización del repositorio

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-08-25

Tareas:

- [x] crear estructura de carpetas;
- [x] crear `pyproject.toml`;
- [x] configurar Python;
- [x] crear `.gitignore`;
- [x] crear `.env.example`;
- [x] crear README inicial;
- [x] verificar que `.env` no sea rastreado.

Criterios:

- [x] proyecto instalable;
- [x] estructura coincide con diseño;
- [x] ningún secreto versionado.

Seguridad:

- [x] `.env` ignorado;
- [x] secrets no aparecen en README;
- [x] API key solo se referencia por nombre de variable.

---

## F1.2 — Configuración central

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] implementar `Settings`;
- [ ] cargar variables de entorno;
- [ ] validar configuración requerida;
- [ ] hacer modelo configurable;
- [ ] hacer timeout configurable;
- [ ] definir máximo de caracteres.

Seguridad:

- [ ] configuración no imprime secretos;
- [ ] error por secret faltante no revela valores;
- [ ] defaults seguros.

---

## F1.3 — Aplicación FastAPI y health check

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] crear aplicación;
- [ ] registrar router;
- [ ] crear `GET /health`;
- [ ] añadir tests.

Criterios:

- [ ] HTTP 200;
- [ ] respuesta mínima;
- [ ] tests pasan.

Seguridad:

- [ ] health no expone configuración interna.

---

## F1.4 — CORS y manejo base de errores

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] configurar allowlist de orígenes;
- [ ] crear errores internos;
- [ ] respuestas HTTP seguras;
- [ ] correlation/request ID básico.

Seguridad:

- [ ] no `*` en producción;
- [ ] no tracebacks hacia el consumidor;
- [ ] no headers sensibles en logs.

---

## F1.5 — OpenAIService

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] instalar SDK oficial;
- [ ] encapsular cliente;
- [ ] implementar Responses API;
- [ ] cargar prompt base;
- [ ] configurar `store=False` cuando corresponda;
- [ ] configurar timeout;
- [ ] manejar errores relevantes.

Criterios:

- [ ] servicio mockeable;
- [ ] rutas no importan lógica concreta innecesaria del SDK;
- [ ] no usar Assistants API.

Seguridad:

- [ ] API key backend-only;
- [ ] nunca loguear key;
- [ ] no loguear prompt/mensaje completo por defecto.

---

## F1.6 — Endpoint `/api/v1/chat`

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] crear `ChatRequest`;
- [ ] crear `ChatResponse`;
- [ ] validar mensaje;
- [ ] conectar con `OpenAIService`;
- [ ] crear tests de éxito/error.

Seguridad:

- [ ] máximo de caracteres;
- [ ] input vacío rechazado;
- [ ] errores externos redactados;
- [ ] sin exposición de stack traces.

---

## F1.7 — Pruebas y calidad

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] tests sin API real;
- [ ] mock de OpenAI;
- [ ] probar input inválido;
- [ ] probar fallo proveedor;
- [ ] ejecutar Ruff;
- [ ] documentar comandos.

Criterios:

- [ ] `pytest` pasa;
- [ ] lint pasa;
- [ ] no consumo accidental de créditos.

---

## F1.8 — Prueba de integración manual

**Estado:** ⬜ PENDIENTE

Tareas:

- [ ] cargar API key localmente;
- [ ] iniciar servidor;
- [ ] realizar una petición real;
- [ ] verificar respuesta;
- [ ] no almacenar la key ni pegarla en evidencias.

Criterios:

- [ ] Responses API comprobada;
- [ ] error handling comprobado;
- [ ] plan actualizado.

---

## F1.9 — Cierre de Fase 1

**Estado:** ⬜ PENDIENTE

- [ ] todos los criterios de `fase_1_diseno.md` cumplen;
- [ ] README actualizado;
- [ ] tests pasan;
- [ ] seguridad revisada;
- [ ] no secretos en Git;
- [ ] historial actualizado;
- [ ] marcar Fase 1 `✅ COMPLETADO`.

---

# 5. FASE 2 — Cliente web mínimo

**Estado:** ⬜ PENDIENTE

Objetivo:

Crear una interfaz web inicial para conversar con el backend.

Tareas principales:

- [ ] crear frontend;
- [ ] chat UI básico;
- [ ] consumir `/api/v1/chat`;
- [ ] loading/error states;
- [ ] no incluir secretos en frontend;
- [ ] sanitizar/renderizar respuestas de forma segura;
- [ ] restringir CORS al origen real.

Seguridad:

- [ ] cero API keys del proveedor en frontend;
- [ ] prevenir XSS al renderizar contenido;
- [ ] política de dependencias frontend;
- [ ] CSP antes de producción.

---

# 6. FASE 3 — Reglas de negocio y FAQ

**Estado:** ⬜ PENDIENTE

Objetivo:

Hacer que el asistente conozca las reglas generales del negocio sin inventar información.

Tareas:

- [ ] prompt de negocio;
- [ ] políticas de respuesta;
- [ ] FAQ inicial;
- [ ] cargar TXT/Markdown;
- [ ] fallback a humano;
- [ ] pruebas contra preguntas desconocidas.

Seguridad:

- [ ] tratar documentos como contenido no confiable;
- [ ] defensa contra prompt injection;
- [ ] impedir que documentos cambien privilegios;
- [ ] no incluir secretos en archivos de conocimiento.

---

# 7. FASE 4 — SQLite + sucursales + productos + precios

**Estado:** ⬜ PENDIENTE

Objetivo:

Crear la primera fuente de verdad comercial.

Tablas iniciales:

- `branches`;
- `products`;
- `prices`;
- `faqs` cuando corresponda.

Tareas:

- [ ] modelo relacional;
- [ ] SQLAlchemy;
- [ ] migraciones;
- [ ] repositorios;
- [ ] seeds ficticios para desarrollo;
- [ ] tests.

Seguridad:

- [ ] queries parametrizadas/ORM;
- [ ] restricciones de integridad;
- [ ] no SQL generado libremente por IA;
- [ ] permisos de DB mínimos en producción;
- [ ] backups antes de cambios sensibles.

---

# 8. FASE 5 — Importación segura de Excel

**Estado:** ⬜ PENDIENTE

Objetivo:

Permitir actualizar precios desde un archivo administrado por personal autorizado.

Flujo:

```text
Excel
  |
  v
validación
  |
  v
preview
  |
  v
confirmación
  |
  v
transacción
  |
  v
base de datos
```

Tareas:

- [ ] plantilla Excel definida;
- [ ] pandas/openpyxl;
- [ ] validar columnas;
- [ ] validar IDs/sucursales;
- [ ] validar tipos y precios;
- [ ] preview de cambios;
- [ ] importación transaccional;
- [ ] reporte de errores.

Seguridad:

- [ ] límite de tamaño;
- [ ] allowlist de extensiones;
- [ ] MIME/estructura verificados;
- [ ] rechazar macros cuando aplique;
- [ ] nombres de archivo no controlan paths;
- [ ] prevenir path traversal;
- [ ] transacción rollback;
- [ ] solo administradores pueden importar.

---

# 9. FASE 6 — Function calling para datos exactos

**Estado:** ⬜ PENDIENTE

Objetivo:

Permitir al modelo solicitar datos verificables sin darle acceso libre a la base.

Tools iniciales:

- `get_product_price`;
- `get_branch_info`;
- `search_faq`;
- `request_human_help`.

Tareas:

- [ ] schemas estrictos;
- [ ] dispatcher de tools;
- [ ] autorización por tool;
- [ ] validar argumentos generados por IA;
- [ ] pruebas;
- [ ] respuestas de incertidumbre.

Seguridad:

- [ ] `strict`/schema cuando sea compatible;
- [ ] nunca `execute_sql`;
- [ ] read-only para consultas;
- [ ] límites de resultados;
- [ ] timeouts;
- [ ] auditoría de llamadas de herramientas;
- [ ] prompt injection no puede otorgar nuevos permisos.

---

# 10. FASE 7 — Conversaciones y preguntas no resueltas

**Estado:** ⬜ PENDIENTE

Objetivo:

Mantener contexto mínimo y aprender qué información le falta al negocio.

Tareas:

- [ ] conversations;
- [ ] messages;
- [ ] unanswered_questions;
- [ ] contexto de sucursal;
- [ ] política de retención;
- [ ] resumen/conservación limitada.

Seguridad y privacidad:

- [ ] minimización de datos;
- [ ] no guardar más de lo necesario;
- [ ] definir tiempo de retención;
- [ ] borrado;
- [ ] redactar información sensible;
- [ ] acceso administrativo protegido;
- [ ] revisar `store` y controles de datos del proveedor.

---

# 11. FASE 8 — Panel administrativo

**Estado:** ⬜ PENDIENTE

Objetivo:

Administrar desde PC:

- productos;
- precios;
- sucursales;
- FAQ;
- conversaciones;
- preguntas sin resolver.

Tareas:

- [ ] login;
- [ ] dashboard;
- [ ] CRUD autorizado;
- [ ] importador Excel;
- [ ] auditoría de cambios;
- [ ] roles.

Seguridad:

- [ ] auth backend;
- [ ] hash seguro de passwords;
- [ ] cookies seguras o estrategia JWT correctamente diseñada;
- [ ] protección CSRF cuando aplique;
- [ ] RBAC;
- [ ] expiración de sesión;
- [ ] rate limiting de login;
- [ ] bloqueo/mitigación de fuerza bruta;
- [ ] audit log de cambios de precio;
- [ ] nunca confiar en permisos del frontend.

---

# 12. FASE 9 — Hardening para exposición pública

**Estado:** ⬜ PENDIENTE

Objetivo:

Preparar API/chat para internet.

- [ ] HTTPS obligatorio;
- [ ] reverse proxy;
- [ ] rate limiting;
- [ ] headers de seguridad;
- [ ] CSP;
- [ ] límites de body;
- [ ] timeouts;
- [ ] reintentos controlados;
- [ ] health/readiness;
- [ ] secret manager en producción;
- [ ] rotación de secretos;
- [ ] budget/alerts de OpenAI;
- [ ] dependency scanning;
- [ ] secret scanning;
- [ ] logs centralizados;
- [ ] backup y restore probado;
- [ ] política de incidentes;
- [ ] política de privacidad revisada.

---

# 13. FASE 10 — Docker y despliegue

**Estado:** ⬜ PENDIENTE

- [ ] Dockerfile backend;
- [ ] Dockerfile frontend;
- [ ] compose para desarrollo si conviene;
- [ ] usuario no-root;
- [ ] imágenes mínimas;
- [ ] secrets no horneados en imagen;
- [ ] HTTPS;
- [ ] configuración por entorno;
- [ ] backup DB;
- [ ] rollback.

---

# 14. FASE 11 — Canal externo / WhatsApp

**Estado:** ⬜ PENDIENTE

Objetivo:

Conectar el backend ya estable a un canal oficial de mensajería.

- [ ] webhook;
- [ ] validación de firma;
- [ ] idempotencia;
- [ ] correlación usuario/conversación;
- [ ] plantillas cuando correspondan;
- [ ] reintentos;
- [ ] observabilidad.

Seguridad:

- [ ] verificar autenticidad del webhook;
- [ ] no confiar en payload sin validar;
- [ ] protección contra replay cuando aplique;
- [ ] secretos del proveedor en backend.

---

# 15. FASE 12 — Pedidos e integraciones comerciales

**Estado:** ⬜ PENDIENTE

Posibles funciones:

- pedidos;
- disponibilidad;
- POS;
- ERP;
- inventario;
- recomendaciones para carne asada.

Seguridad:

- [ ] acciones de escritura requieren confirmación explícita;
- [ ] idempotencia;
- [ ] autorización;
- [ ] precios revalidados antes de confirmar;
- [ ] inventario proveniente de fuente real;
- [ ] audit trail;
- [ ] nunca confirmar un pedido solo por texto generado por IA.

---

# 16. Matriz global de seguridad

| Control | Fase inicial | Antes de producción | Estado |
|---|---:|---:|---|
| API key backend-only | 1 | Sí | ⬜ |
| `.env` ignorado | 1 | Sí | ⬜ |
| validación Pydantic | 1 | Sí | ⬜ |
| CORS allowlist | 1 | Sí | ⬜ |
| errores seguros | 1 | Sí | ⬜ |
| logs sin secretos | 1 | Sí | ⬜ |
| input size limit | 1 | Sí | ⬜ |
| timeout OpenAI | 1 | Sí | ⬜ |
| tests sin consumo real | 1 | Sí | ⬜ |
| rate limiting | diseño 1 | Sí | ⬜ |
| SQL parametrizado/ORM | 4 | Sí | ⬜ |
| migraciones | 4 | Sí | ⬜ |
| validación Excel | 5 | Sí | ⬜ |
| function tools con mínimo privilegio | 6 | Sí | ⬜ |
| defensa prompt injection | 3/6 | Sí | ⬜ |
| retención/minimización de chats | 7 | Sí | ⬜ |
| autenticación admin | 8 | Sí | ⬜ |
| RBAC | 8 | Sí | ⬜ |
| hash de passwords | 8 | Sí | ⬜ |
| protección fuerza bruta | 8 | Sí | ⬜ |
| audit log precios | 8 | Sí | ⬜ |
| HTTPS | 9 | Sí | ⬜ |
| CSP/security headers | 9 | Sí | ⬜ |
| secret manager | 9/10 | Sí | ⬜ |
| rotación de secretos | 9 | Sí | ⬜ |
| dependency scanning | 9 | Sí | ⬜ |
| secret scanning | 9 | Sí | ⬜ |
| backup/restore | 9/10 | Sí | ⬜ |
| webhook signature validation | 11 | Si se usa | ⬜ |
| confirmación para pedidos | 12 | Si se usa | ⬜ |

---

# 17. Riesgos conocidos

## R-01 — Alucinación de precios

**Severidad:** crítica  
**Mitigación:** precios solo desde DB/tool.

## R-02 — Exposición de OpenAI API key

**Severidad:** crítica  
**Mitigación:** backend-only, env/secrets, scanning, rotación.

## R-03 — Prompt injection

**Severidad:** alta  
**Mitigación:** mínimo privilegio, validación de tools, no confiar únicamente en prompt.

## R-04 — Excel incorrecto modifica precios

**Severidad:** alta  
**Mitigación:** preview + validación + transacción + auditoría.

## R-05 — Acceso no autorizado al panel

**Severidad:** crítica  
**Mitigación:** auth + RBAC + HTTPS + rate limits + sesiones seguras.

## R-06 — Costos no controlados de IA

**Severidad:** alta  
**Mitigación:** rate limiting, longitud máxima, modelo configurable, usage alerts y budget.

## R-07 — Dependencia externa no disponible

**Severidad:** media/alta  
**Mitigación:** timeout, retries limitados, circuit/fallback cuando el volumen lo justifique.

## R-08 — Almacenamiento excesivo de chats

**Severidad:** alta  
**Mitigación:** minimización, retención definida, controles de acceso y borrado.

---

# 18. Backlog futuro opcional

- [ ] recomendaciones de paquetes para carne asada;
- [ ] cálculo de cantidades por número de personas;
- [ ] detección de intención;
- [ ] dashboard de productos más preguntados;
- [ ] analytics de preguntas no resueltas;
- [ ] derivación a empleado;
- [ ] promociones;
- [ ] pedidos;
- [ ] integración POS;
- [ ] inventario en tiempo real;
- [ ] múltiples canales;
- [ ] evaluación automática de calidad de respuestas;
- [ ] tests de prompts/evals.

---

# 19. Checkpoint actual

**Fase activa:** Fase 1  
**Tarea activa:** ninguna; F1.1 finalizada sin iniciar tareas posteriores.
**Última tarea completada:** F1.1 — Inicialización del repositorio.
**Siguiente tarea sugerida:** F1.2 — Configuración central, solo con instrucción del usuario.

---

# 20. Historial de avances

## 2026-08-25 — Diseño inicial

**Fase:** preparación / Fase 1  
**Estado:** ✅ COMPLETADO

Cambios:

- creado diseño de Fase 1;
- definido `AGENTS.md`;
- definido plan por fases;
- agregada matriz transversal de seguridad;
- definidos criterios para que Codex actualice estados.

Archivos:

- `docs/fase_1_diseno.md`
- `AGENTS.md`
- `plan_de_trabajo.md`

Validación:

- revisión documental inicial.

Pendientes:

- todavía no se ha implementado código.
- todavía no existe prueba real con OpenAI.
- comenzar F1.1.

---

## 2026-08-25 — Inicialización del repositorio

**Fase:** Fase 1
**Tarea:** F1.1 — Inicialización del repositorio
**Estado:** ✅ COMPLETADO

Cambios:

- creada la estructura base de paquetes para `backend/app`, rutas, núcleo, prompts,
  esquemas, servicios y tests, sin implementar tareas F1.2 o posteriores;
- agregado empaquetado instalable con Python 3.12–3.14 y herramientas de desarrollo acotadas;
- agregados `.gitignore`, `.env.example` sin secretos y README inicial;
- agregada prueba mínima de importación del paquete.

Archivos:

- `.gitignore`
- `.env.example`
- `pyproject.toml`
- `README.md`
- `backend/__init__.py`
- `backend/app/**/__init__.py`
- `backend/tests/__init__.py`
- `backend/tests/test_package.py`
- `plan_de_trabajo.md`

Validación:

- `python -m venv .venv` -> entorno creado con Python 3.14.7;
- `.venv\\Scripts\\python.exe -m pip install -e ".[dev]"` -> instalación editable correcta;
- `.venv\\Scripts\\python.exe -m pytest` -> 1 prueba aprobada;
- `.venv\\Scripts\\ruff.exe check .` -> sin hallazgos;
- `.venv\\Scripts\\ruff.exe format --check .` -> 13 archivos con formato correcto;
- `.venv\\Scripts\\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios en los cambios;
- `git status --short --ignored` -> entorno, cachés y artefactos de instalación ignorados;
- el primer chequeo de formato detectó ejemplos no ejecutables del documento de diseño;
  se excluyó ese documento del formateador y la repetición pasó;
- el primer escaneo de secretos detectó los placeholders documentales `sk-...` y
  `OPENAI_API_KEY=...`; el escaneo ajustado para claves con forma real no encontró secretos.

Seguridad:

- `.env`, sus variantes locales y `.venv` comprobados como ignorados;
- `.env.example` comprobado como versionable y sin valor para `OPENAI_API_KEY`;
- ningún archivo `.env` local está rastreado;
- no se detectaron patrones con forma de API key real fuera del entorno virtual.

Riesgos/Pendientes:

- FastAPI, configuración central y OpenAI no están implementados por estar fuera de F1.1;
- la versión de modelo de `.env.example` proviene del diseño y deberá validarse al abordar
  la integración de OpenAI.

Siguiente:

- F1.2 — Configuración central, sin iniciar hasta recibir instrucción del usuario.

---

# 21. Plantilla para nuevas entradas del historial

```text
## YYYY-MM-DD — Título

Fase:
Tarea:
Estado:

Cambios:
- ...

Archivos:
- ...

Validación:
- `comando` -> resultado

Seguridad:
- ...

Riesgos/Pendientes:
- ...

Siguiente:
- ...
```
