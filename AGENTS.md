# AGENTS.md
## Instrucciones permanentes para Codex — Chatbot IA para Carnicerías + WhatsApp

Este archivo contiene reglas obligatorias para cualquier agente que modifique este repositorio.

---

# 1. Objetivo del sistema

Construir un asistente automatizado de atención al cliente para una cadena de carnicerías.

## Canal del cliente

**WhatsApp Business Platform / Cloud API es la interfaz principal del cliente.**

El cliente final NO utilizará directamente el endpoint interno de chat ni el panel administrativo.

Flujo objetivo:

```text
Cliente
  |
  v
WhatsApp
  |
  v
Meta / WhatsApp Cloud API
  |
  | webhook HTTPS
  v
FastAPI
  |
  v
Orquestador de conversación
  |-------------------------|
  v                         v
OpenAI                  Servicios del negocio
Responses API              |
                            v
                    Base de datos / FAQ
                            |
  |-------------------------|
  v
Respuesta
  |
  v
WhatsApp Cloud API
  |
  v
Cliente
```

## Interfaz del personal

El panel web se implementará posteriormente y será únicamente para:

- administración;
- sucursales;
- productos;
- precios;
- FAQ;
- carga de Excel;
- conversaciones;
- preguntas no resueltas;
- atención humana;
- auditoría y estadísticas.

---

# 2. Principio arquitectónico principal

OpenAI NO es la fuente de verdad del negocio.

OpenAI se utiliza para:

- comprender lenguaje natural;
- detectar intención;
- decidir qué herramienta autorizada necesita;
- redactar respuestas;
- mantener una conversación controlada.

Los datos críticos deben provenir de fuentes determinísticas.

```text
precio        -> servicio -> base de datos
sucursal      -> servicio -> base de datos
horario       -> servicio -> base de datos
FAQ           -> servicio -> fuente validada
inventario    -> fuente real o respuesta "no confirmado"
pedido        -> lógica transaccional + confirmación explícita
```

Nunca permitir que el modelo invente:

- precios;
- existencias;
- promociones;
- horarios;
- ubicaciones;
- pedidos confirmados;
- condiciones comerciales.

---

# 3. Stack previsto

Backend:

- Python.
- FastAPI.
- Pydantic.
- pydantic-settings.
- SDK oficial de OpenAI.
- OpenAI Responses API.

Canal:

- WhatsApp Business Platform / Cloud API de Meta.
- Webhooks HTTPS.
- Graph API para mensajes salientes.

Persistencia:

- SQLite durante el MVP.
- SQLAlchemy.
- Alembic cuando comience la fase de persistencia.
- Evaluar PostgreSQL antes de escalar a múltiples instancias.

Datos:

- SQLite como fuente operativa.
- Excel como mecanismo de importación/actualización, no como base consultada en cada mensaje.
- TXT/Markdown para conocimiento simple cuando corresponda.

Panel futuro:

- React o Next.js.
- autenticación y autorización en backend.

Producción:

- Docker.
- HTTPS.
- reverse proxy.
- secret manager.
- observabilidad.
- rate limiting.
- backups.

---

# 4. Documentos obligatorios antes de trabajar

Antes de modificar código lee, en este orden:

1. `AGENTS.md`.
2. `plan_de_trabajo.md`.
3. `README.md`, si existe.
4. `docs/fase_1_diseno.md` si estás en Fase 1.
5. `docs/fase_2_whatsapp.md` si estás en Fase 2 o modificas integración WhatsApp.
6. archivos de código y tests relacionados.

Antes de escribir código identifica explícitamente:

- fase activa;
- subfase activa;
- estado actual;
- criterios de aceptación;
- controles de seguridad;
- archivos probablemente afectados.

---

# 5. Regla de alcance

Trabaja solamente en:

1. la subfase que el usuario solicite; o
2. si no la especifica, la primera subfase `⬜ PENDIENTE` de la fase activa.

No empieces automáticamente la subfase siguiente.

No empieces automáticamente una fase nueva.

No mezcles tareas de varias fases salvo que:

- el usuario lo solicite explícitamente; o
- sea estrictamente necesario para corregir una regresión y lo documentes.

---

# 6. Estados oficiales

Usar únicamente:

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

Si una función previamente cerrada falla:

```text
✅ COMPLETADO -> ↩️ REABIERTO
```

---

# 7. Actualización obligatoria del plan

`plan_de_trabajo.md` es el checkpoint oficial.

## Al iniciar una subfase

- cambiarla a `🟨 EN_PROGRESO`;
- registrar fecha de inicio;
- no modificar estados de subfases no trabajadas.

## Antes de completar

- cambiar a `🧪 VALIDACION`;
- ejecutar tests relevantes;
- ejecutar lint/formato;
- revisar seguridad;
- revisar criterios de aceptación.

## Solo después

Cambiar a:

```text
✅ COMPLETADO
```

y agregar entrada al historial con:

- fecha;
- fase/subfase;
- cambios;
- archivos;
- comandos ejecutados;
- resultados;
- controles de seguridad;
- riesgos;
- siguiente subfase recomendada.

Nunca marques como completado algo que no hayas comprobado.

---

# 8. Regla especial sobre el avance actual

El checkpoint recibido establece:

- F1.1 `✅ COMPLETADO`.
- F1.2 `✅ COMPLETADO`.
- F1.3 `⬜ PENDIENTE`.

No rehagas ni reviertas F1.1 o F1.2 salvo que encuentres una regresión real.

Si necesitas tocarlas por compatibilidad:

1. preserva el comportamiento existente;
2. ejecuta nuevamente sus tests;
3. registra el motivo;
4. usa `↩️ REABIERTO` si el criterio previamente cumplido dejó de cumplirse.

---

# 9. Arquitectura por capas

Evitar llamadas directas entre controladores HTTP y proveedores externos.

Preferir:

```text
route/controller
      |
      v
application/orchestrator
      |
      +------------------+
      |                  |
      v                  v
OpenAIService       BusinessService
                         |
                         v
                     Repository
```

Para WhatsApp:

```text
WhatsApp webhook route
      |
      v
WhatsAppWebhookService
      |
      v
MessageOrchestrator
      |
      +----------+
      |          |
      v          v
Chatbot       Business tools
      |
      v
WhatsAppClient
```

El endpoint `/api/v1/chat` de Fase 1 es para desarrollo/pruebas y NO es el canal final del cliente.

---

# 10. Seguridad — reglas no negociables

## 10.1 Secretos

Nunca:

- escribir claves reales en código;
- inventar claves con apariencia real;
- commitear `.env`;
- imprimir secretos;
- incluir secretos en excepciones;
- incluir secretos en screenshots;
- colocar secretos en frontend;
- colocar tokens en URLs;
- registrar `Authorization`.

Secretos previstos:

```text
OPENAI_API_KEY
WHATSAPP_ACCESS_TOKEN
META_APP_SECRET
WHATSAPP_VERIFY_TOKEN
```

Todos son backend-only.

`.env.example` debe contener únicamente nombres y valores vacíos/no sensibles.

---

## 10.2 OpenAI

- usar Responses API para nuevas integraciones;
- no introducir Assistants API;
- modelo configurable;
- timeout configurable;
- `store` configurable y con un default conservador;
- tests normales siempre mockeados;
- no registrar prompts, mensajes o respuestas completos por defecto;
- controlar tamaño de input;
- manejar rate limit y errores de proveedor;
- no permitir que texto del usuario cambie privilegios.

---

## 10.3 WhatsApp — validación de webhook

El webhook es una frontera pública y debe tratarse como input no confiable.

### GET de verificación

- comparar el token de verificación con configuración del servidor;
- devolver solamente el challenge cuando la verificación sea válida;
- no registrar el token;
- preferir comparación segura cuando sea razonable.

### POST de eventos

Antes de confiar en el payload:

1. conservar el cuerpo HTTP crudo;
2. validar la firma que corresponda a la configuración oficial vigente de Meta;
3. solo después parsear/procesar el JSON;
4. rechazar solicitudes no autenticadas;
5. validar esquema;
6. ignorar tipos de evento no utilizados.

Cuando la integración use `X-Hub-Signature-256`, calcular el HMAC SHA-256 sobre el **raw body** con `META_APP_SECRET` y comparar de forma segura.

Nunca "validar" el webhook solo porque conoce `WHATSAPP_VERIFY_TOKEN`; ese token corresponde al handshake de verificación, no reemplaza la autenticidad del POST.

Antes de implementar o modificar este código, revisar la documentación oficial vigente de Meta.

---

## 10.4 WhatsApp — tokens y Graph API

- `WHATSAPP_ACCESS_TOKEN` solo backend.
- `WHATSAPP_PHONE_NUMBER_ID` y versión de Graph API vienen de configuración.
- no aceptar una URL de Graph API controlada por el usuario.
- no interpolar números o IDs sin validación.
- usar timeout.
- reintentos limitados solo para fallos apropiados.
- nunca reintentar infinitamente.
- no duplicar envíos tras errores ambiguos sin estrategia de idempotencia.
- redactar tokens en errores y logs.

---

## 10.5 Idempotencia de webhooks

Los eventos externos pueden repetirse.

Cuando exista un identificador único de mensaje/evento:

```text
recibir
  |
  v
¿ya procesado?
  | yes -> ACK / ignorar
  v no
procesar
  |
  v
marcar procesado
```

Antes de producción la idempotencia debe ser persistente.

Una implementación solo en memoria puede usarse temporalmente para un MVP local si queda marcada explícitamente como NO apta para múltiples procesos/instancias.

---

## 10.6 Datos personales

El identificador/número de WhatsApp se considera dato personal.

No mostrar números completos en logs salvo necesidad operacional justificada.

Preferir:

```text
******1234
```

Evitar almacenar:

- conversaciones completas sin política;
- información personal no necesaria;
- datos de pago;
- documentos personales.

Definir retención y borrado antes de producción.

---

## 10.7 Prompt injection

Todo texto recibido por WhatsApp, archivos y datos recuperados son no confiables.

Un usuario nunca puede:

- pedir la API key;
- cambiar el system prompt;
- concederse rol admin;
- modificar precios;
- ejecutar SQL;
- activar tools no autorizadas;
- confirmar un pedido sin lógica de aplicación;
- cambiar configuración.

Las protecciones deben vivir en código/autorización, no únicamente en el prompt.

---

## 10.8 Base de datos

Cuando se implemente:

- SQLAlchemy o queries parametrizadas;
- migraciones reproducibles;
- constraints;
- transacciones;
- nunca concatenar input en SQL;
- no exponer `execute_sql(query)` a OpenAI;
- tools específicas y de mínimo privilegio.

Permitido:

```text
get_product_price(product_id, branch_id)
```

Prohibido:

```text
run_sql(model_generated_sql)
```

---

## 10.9 Excel

Excel es fuente de importación, no de consulta directa por mensaje.

Flujo:

```text
Excel
 -> validar
 -> preview
 -> confirmar
 -> transacción
 -> DB
```

Controles:

- límite de tamaño;
- extensión permitida;
- estructura/MIME cuando corresponda;
- validar headers;
- tipos;
- sucursales;
- precios;
- duplicados;
- valores negativos/absurdos;
- no ejecutar macros;
- prevenir path traversal;
- usar archivos temporales controlados;
- rollback en error;
- audit log.

---

## 10.10 Panel administrativo

Cuando exista:

- autenticación backend;
- RBAC;
- sesiones seguras;
- rate limiting de login;
- hash de password con algoritmo adecuado mantenido;
- CSRF si la estrategia de sesión lo requiere;
- CORS allowlist;
- auditoría de cambios;
- nunca confiar en controles visuales del frontend.

---

## 10.11 Pedidos y acciones de escritura

OpenAI no confirma acciones comerciales por sí solo.

Para pedidos o cambios:

```text
interpretar
 -> validar contra datos reales
 -> mostrar resumen
 -> confirmación explícita
 -> ejecutar
 -> registrar resultado
```

Toda acción debe ser:

- autorizada;
- idempotente cuando aplique;
- auditable;
- validada de nuevo en backend.

---

# 11. CORS

WhatsApp no depende de CORS porque los webhooks son servidor-a-servidor.

CORS solo se necesita para:

- endpoint web de desarrollo;
- panel administrativo futuro.

No usar `*` en producción.

---

# 12. Logging

Registrar solo lo necesario:

- timestamp;
- request ID;
- endpoint;
- tipo de evento;
- HTTP status;
- duración;
- error category;
- identificador externo redactado/hasheado cuando sea útil.

No registrar por defecto:

- OpenAI API key;
- Meta token;
- app secret;
- verify token;
- headers Authorization;
- raw webhook body completo;
- conversación completa;
- prompt completo;
- respuesta completa del modelo.

---

# 13. Errores

No devolver:

- tracebacks;
- secrets;
- paths locales;
- variables de entorno;
- SQL;
- información interna innecesaria.

Crear excepciones de dominio/infraestructura y mapearlas en la frontera HTTP.

---

# 14. Pruebas

Los tests comunes NO usan internet.

Mockear:

- OpenAI.
- Graph API / WhatsApp.
- servicios externos.

Antes de cerrar una subfase ejecutar según aplique:

```bash
pytest
ruff check .
ruff format --check .
```

Si el proyecto incorpora otros validadores, ejecutarlos también.

Pruebas reales contra OpenAI o Meta:

- explícitas;
- separadas;
- no ejecutadas automáticamente por defecto;
- nunca guardan tokens en fixtures/evidencias.

---

# 15. Dependencias

Antes de agregar una:

1. demostrar que hace falta;
2. preferir una librería mantenida;
3. evitar duplicar funcionalidad;
4. acotar/fijar versión de forma razonable;
5. actualizar lockfile si existe;
6. documentar impacto cuando sea relevante.

---

# 16. Cambios pequeños

Prefiere:

- una subfase por cambio;
- cambios reversibles;
- tests junto a la implementación;
- evitar refactors no relacionados.

No cambies framework, lenguaje, ORM, arquitectura o proveedor sin instrucción explícita o justificación documentada.

---

# 17. No destruir trabajo existente

Antes de editar:

- leer el archivo;
- revisar `git status`;
- preservar cambios ajenos.

No usar sin instrucción explícita:

```text
git reset --hard
git clean -fd
rm -rf
DROP DATABASE
DROP TABLE
```

No reescribir historial.

---

# 18. Integraciones externas versionadas

OpenAI y Meta pueden cambiar APIs, modelos y versiones.

Antes de implementar una integración:

- revisar documentación oficial vigente;
- no copiar tutoriales antiguos sin verificar;
- pin/configurar versiones cuando corresponda;
- aislar detalles del proveedor detrás de servicios;
- documentar incompatibilidades.

No hardcodear una versión de Graph API en múltiples archivos.

---

# 19. Definition of Done por subfase

Una subfase pasa a `✅ COMPLETADO` solo si:

- alcance implementado;
- criterios de aceptación cumplidos;
- tests relevantes pasan;
- lint/formato pasan;
- seguridad revisada;
- documentación afectada actualizada;
- plan actualizado;
- no quedan TODO críticos ocultos;
- no se ha iniciado trabajo de la subfase siguiente.

---

# 20. Formato del reporte final de Codex

```text
Resumen:
- ...

Subfase:
- Fx.y — nombre
- estado final: ...

Archivos modificados:
- ...

Validación:
- comando -> resultado

Seguridad:
- ...

Plan:
- estado actualizado
- siguiente subfase sugerida

Riesgos/Pendientes:
- ...
```

No afirmar que una validación pasó si no se ejecutó.

---

# 21. Checkpoint cuando se interrumpe una sesión

Antes de detener trabajo largo:

1. actualizar `plan_de_trabajo.md`;
2. registrar exactamente la subfase;
3. indicar estado;
4. anotar archivos modificados;
5. registrar comandos y resultados;
6. describir qué falta;
7. describir el siguiente paso.

En una sesión nueva, reconstruir contexto leyendo archivos; no confiar en memoria del agente.

---

# 22. Prioridad

Si existen conflictos:

1. instrucciones actuales explícitas del usuario;
2. seguridad, privacidad e integridad de datos;
3. `AGENTS.md`;
4. `plan_de_trabajo.md`;
5. documentación de fase;
6. convenciones del repositorio.

Si una solicitud expondría secretos, permitiría acceso no autorizado o destruiría datos, no implementarla silenciosamente: explicar el riesgo y aplicar una alternativa segura.
