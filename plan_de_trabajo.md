# plan_de_trabajo.md
## Siete asistentes IA para Carnicerías — uno por sucursal y número de WhatsApp

**Última actualización:** 2026-09-24
**Fase activa:** ninguna; Fase 7 — Conversaciones WhatsApp + idempotencia persistente (`✅ COMPLETADO`)
**Subfase activa:** ninguna; F7.6 — Cierre Fase 7 (`✅ COMPLETADO`)
**Estado global:** ✅ COMPLETADO — Fase 7; Fase 8 pendiente
**Canal principal del cliente:** WhatsApp mediante GreenAPI
**Panel web:** administración y atención humana, no chat público del cliente.

> Este archivo es el checkpoint oficial. Codex debe actualizarlo después de cada avance relevante.

---

# 1. Estados oficiales

| Estado | Significado |
|---|---|
| ⬜ PENDIENTE | No iniciado |
| 🟨 EN_PROGRESO | Trabajo activo |
| 🧪 VALIDACION | Implementado, comprobándose |
| ✅ COMPLETADO | Criterios verificados |
| ⛔ BLOQUEADO | No puede continuar |
| ↩️ REABIERTO | Se había cerrado y requiere corrección |

---

# 2. Flujo de actualización

```text
⬜ PENDIENTE
 -> 🟨 EN_PROGRESO
 -> 🧪 VALIDACION
 -> ✅ COMPLETADO
```

Una subfase no puede avanzar a `✅` si:

- fallan tests relevantes;
- falta validar seguridad;
- falta documentación requerida;
- existe un error conocido que invalida el criterio;
- se afirmó una prueba que no se ejecutó.

Al finalizar cada subfase, actualizar el historial.

---

# 3. Arquitectura objetivo

```text
CLIENTE
   |
   v
WhatsApp
   |
   v
GreenAPI
   |
   v
Webhook FastAPI
   |
   v
MessageOrchestrator
   |
   +-----------------------+
   |                       |
   v                       v
OpenAI                 Business Services
Responses API              |
                            v
                       SQLite/DB/FAQ
   |                       |
   +-----------+-----------+
               |
               v
         WhatsAppClient
               |
               v
            CLIENTE


PERSONAL
   |
   v
Panel web seguro
   |
   v
Admin API / Human Handoff
```

Principios:

1. WhatsApp es el canal del cliente.
2. `/api/v1/chat` es una herramienta de desarrollo/integración, no el canal final.
3. OpenAI interpreta y redacta; DB/servicios son la fuente de verdad.
4. Seguridad se implementa en cada fase.
5. Excel importa a DB; el chatbot no abre el Excel por mensaje.
6. Toda acción comercial sensible requiere validación backend.
7. Webhooks se autentican y deduplican.
8. El número/identificador de WhatsApp se trata como dato personal.
9. El mismo código y prompt se despliega siete veces, una por sucursal/número.
10. `ASSISTANT_BRANCH_CODE` fija el único alcance de datos de cada instalación.
11. El cliente y el modelo nunca eligen `branch_id`/`branch_code`; el backend lo inyecta.

## 3.1 Decisión de despliegue por sucursal — 2026-09-22

```text
mismo repositorio + mismo prompt
             |
             +-- instalación/número 1 -> código tienda 1 -> DB/perfil tienda 1
             +-- instalación/número 2 -> código tienda 2 -> DB/perfil tienda 2
             +-- ...
             +-- instalación/número 7 -> código tienda 7 -> DB/perfil tienda 7
```

- cada instalación tiene `.env`, instancia GreenAPI, webhook token y `DATABASE_URL` propios;
- durante el MVP se recomienda un archivo SQLite separado por instalación;
- la carga se realiza mediante un perfil JSON versionado cuyo código debe coincidir con
  `ASSISTANT_BRANCH_CODE`;
- el prompt no contiene datos particulares de una tienda;
- servicios, tools, conversaciones, importaciones y administración conservan el alcance backend;
- si posteriormente se comparte PostgreSQL, se mantiene el aislamiento lógico y se agregan
  pruebas explícitas contra acceso cruzado.

---

# 4. Checkpoint preservado

El plan recibido registra:

```text
F1.1 ✅ COMPLETADO
F1.2 ✅ COMPLETADO
F1.3 ⬜ PENDIENTE
```

No reiniciar Fase 1.

F1.1 creó estructura, empaquetado, `.gitignore`, `.env.example` y pruebas base.  
F1.2 implementó `Settings`, protección de `OPENAI_API_KEY`, configuración y 12 pruebas.

---

# 5. FASE 1 — Backend base + OpenAI

**Objetivo:** Crear un núcleo FastAPI seguro y desacoplado del canal, validarlo con OpenAI y dejarlo listo para ser reutilizado por WhatsApp.

**Estado:** ✅ COMPLETADO

**Fecha de finalización:** 2026-08-26

**Documento guía:** `docs/fase_1_diseno.md`


## F1.1 — Inicialización del repositorio

**Estado:** ✅ COMPLETADO

**Checkpoint:** completada el 2026-08-25 según historial existente.


### Alcance

- [x] estructura base de paquetes.

- [x] pyproject.toml y entorno.

- [x] .gitignore y .env.example.

- [x] README inicial.

- [x] prueba mínima de paquete.


### Criterios de aceptación

- [x] proyecto instalable.

- [x] estructura coherente.

- [x] ningún secreto versionado.


### Seguridad

- [x] preservar .env ignorado.

- [x] no API keys reales.


### Prompt para Codex


> Prompt histórico/reproducible. **No ejecutar de nuevo** salvo reapertura justificada.


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.1 — Inicialización del repositorio. No inicies ninguna subfase posterior.

Alcance obligatorio: estructura base de paquetes; pyproject.toml y entorno; .gitignore y .env.example; README inicial; prueba mínima de paquete.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: proyecto instalable; estructura coherente; ningún secreto versionado. Revisa específicamente esta seguridad: preservar .env ignorado; no API keys reales.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.2 — Configuración central

**Estado:** ✅ COMPLETADO

**Checkpoint:** completada el 2026-08-25; 12 pruebas aprobadas según historial existente.


### Alcance

- [x] Settings central.

- [x] carga de entorno/.env.

- [x] modelo y timeout configurables.

- [x] límite de mensaje.

- [x] SecretStr para OPENAI_API_KEY.


### Criterios de aceptación

- [x] configuración validada.

- [x] tests existentes siguen pasando.

- [x] secretos no se serializan.


### Seguridad

- [x] no imprimir secretos.

- [x] defaults conservadores.


### Prompt para Codex


> Prompt histórico/reproducible. **No ejecutar de nuevo** salvo reapertura justificada.


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.2 — Configuración central. No inicies ninguna subfase posterior.

Alcance obligatorio: Settings central; carga de entorno/.env; modelo y timeout configurables; límite de mensaje; SecretStr para OPENAI_API_KEY.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: configuración validada; tests existentes siguen pasando; secretos no se serializan. Revisa específicamente esta seguridad: no imprimir secretos; defaults conservadores.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.3 — Aplicación FastAPI + health check

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-25

**Fecha de finalización:** 2026-08-25


### Alcance

- [x] crear app FastAPI.

- [x] registrar router de health.

- [x] GET /health.

- [x] tests del health check.


### Criterios de aceptación

- [x] HTTP 200.

- [x] respuesta mínima estable.

- [x] no llamadas externas.


### Seguridad

- [x] health no expone configuración, versiones o secrets.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.3 — Aplicación FastAPI + health check. No inicies ninguna subfase posterior.

Alcance obligatorio: crear app FastAPI; registrar router de health; GET /health; tests del health check.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: HTTP 200; respuesta mínima estable; no llamadas externas. Revisa específicamente esta seguridad: health no expone configuración, versiones o secrets.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.4 — Errores, request ID, logging y CORS

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-25

**Fecha de finalización:** 2026-08-25


### Alcance

- [x] excepciones internas.

- [x] mapeo HTTP seguro.

- [x] request/correlation ID.

- [x] logging mínimo.

- [x] CORS allowlist para desarrollo/panel futuro.


### Criterios de aceptación

- [x] errores no filtran stack traces.

- [x] request ID propagable.

- [x] CORS configurable.


### Seguridad

- [x] no wildcard en producción.

- [x] no body completo ni Authorization en logs.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.4 — Errores, request ID, logging y CORS. No inicies ninguna subfase posterior.

Alcance obligatorio: excepciones internas; mapeo HTTP seguro; request/correlation ID; logging mínimo; CORS allowlist para desarrollo/panel futuro.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: errores no filtran stack traces; request ID propagable; CORS configurable. Revisa específicamente esta seguridad: no wildcard en producción; no body completo ni Authorization en logs.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.5 — OpenAIService con Responses API

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-25

**Fecha de finalización:** 2026-08-25


### Alcance

- [x] agregar/validar SDK oficial.

- [x] encapsular cliente OpenAI.

- [x] Responses API.

- [x] prompt base.

- [x] timeout.

- [x] store configurable.

- [x] errores de proveedor.


### Criterios de aceptación

- [x] servicio mockeable.

- [x] Responses API operativa.

- [x] rutas desacopladas del SDK.


### Seguridad

- [x] API key backend-only.

- [x] no Assistants API.

- [x] no logs de prompt/chat completo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.5 — OpenAIService con Responses API. No inicies ninguna subfase posterior.

Alcance obligatorio: agregar/validar SDK oficial; encapsular cliente OpenAI; Responses API; prompt base; timeout; store configurable; errores de proveedor.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: servicio mockeable; Responses API operativa; rutas desacopladas del SDK. Revisa específicamente esta seguridad: API key backend-only; no Assistants API; no logs de prompt/chat completo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.6 — Endpoint interno POST /api/v1/chat

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-25

**Fecha de finalización:** 2026-08-25


### Alcance

- [x] ChatRequest/ChatResponse.

- [x] validación del mensaje.

- [x] conexión al servicio de aplicación/OpenAI.

- [x] tests de éxito/error.


### Criterios de aceptación

- [x] mensaje válido responde.

- [x] vacío/largo se rechaza.

- [x] fallo proveedor es controlado.


### Seguridad

- [x] límite de entrada.

- [x] endpoint identificado como desarrollo/interno.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.6 — Endpoint interno POST /api/v1/chat. No inicies ninguna subfase posterior.

Alcance obligatorio: ChatRequest/ChatResponse; validación del mensaje; conexión al servicio de aplicación/OpenAI; tests de éxito/error.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mensaje válido responde; vacío/largo se rechaza; fallo proveedor es controlado. Revisa específicamente esta seguridad: límite de entrada; endpoint identificado como desarrollo/interno.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.7 — Suite de pruebas y calidad

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-25

**Fecha de finalización:** 2026-08-25


### Alcance

- [x] mock OpenAI.

- [x] casos inválidos.

- [x] casos de error.

- [x] pytest.

- [x] Ruff check.

- [x] Ruff format --check.

- [x] pip check si aplica.


### Criterios de aceptación

- [x] suite pasa sin internet.

- [x] lint/formato pasan.

- [x] cero consumo accidental de API.


### Seguridad

- [x] fixtures sin secretos.

- [x] tests no salen a red.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.7 — Suite de pruebas y calidad. No inicies ninguna subfase posterior.

Alcance obligatorio: mock OpenAI; casos inválidos; casos de error; pytest; Ruff check; Ruff format --check; pip check si aplica.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: suite pasa sin internet; lint/formato pasan; cero consumo accidental de API. Revisa específicamente esta seguridad: fixtures sin secretos; tests no salen a red.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.8 — Prueba manual real con OpenAI

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-25
**Fecha de reanudación:** 2026-08-26

**Fecha de finalización:** 2026-08-26

**Resultado:** la llamada real respondió HTTP 200 con request ID y texto no vacío; las
validaciones finales y los controles de seguridad fueron aprobados.


### Alcance

- [x] configurar key solo localmente.

- [x] iniciar backend.

- [x] probar /api/v1/chat.

- [x] comprobar respuesta real.

- [x] comprobar error seguro.


### Criterios de aceptación

- [x] una llamada real funciona.

- [x] credencial nunca aparece en evidencia.


### Seguridad

- [x] no commitear .env.

- [x] no copiar key en plan/logs.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.8 — Prueba manual real con OpenAI. No inicies ninguna subfase posterior.

Alcance obligatorio: configurar key solo localmente; iniciar backend; probar /api/v1/chat; comprobar respuesta real; comprobar error seguro.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.8 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: una llamada real funciona; credencial nunca aparece en evidencia. Revisa específicamente esta seguridad: no commitear .env; no copiar key en plan/logs.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.9 — Cierre Fase 1

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-26

**Fecha de finalización:** 2026-08-26


### Alcance

- [x] revisar DoD.

- [x] README.

- [x] tests.

- [x] lint.

- [x] secrets.

- [x] checkpoint.


### Criterios de aceptación

- [x] F1.1-F1.9 verificadas.

- [x] Fase 1 marcada completa.


### Seguridad

- [x] no abrir Fase 2 automáticamente.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.9 — Cierre Fase 1. No inicies ninguna subfase posterior.

Alcance obligatorio: revisar DoD; README; tests; lint; secrets; checkpoint.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.9 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: F1.1-F1.9 verificadas; Fase 1 marcada completa. Revisa específicamente esta seguridad: no abrir Fase 2 automáticamente.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 6. FASE 2 — WhatsApp mediante GreenAPI — interfaz del cliente

**Objetivo:** Recibir mensajes de WhatsApp mediante webhook, procesarlos con el núcleo de chat y responder por WhatsApp de forma segura.

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-26

**Fecha de finalización:** 2026-09-21

**Documento guía:** `docs/fase_2_whatsapp.md`

> Registro preservado: F2.1-F2.8 documentan la implementación original con Meta y mantienen su
> estado histórico. El reemplazo del proveedor se autorizó y se implementa dentro de F2.9 sin
> renumerar, reabrir ni borrar las fases ya establecidas; se conservan sus contratos internos.


## F2.1 — Configuración Meta/WhatsApp

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-26

**Fecha de finalización:** 2026-08-26


### Alcance

- [x] variables WhatsApp/Meta en Settings.

- [x] .env.example.

- [x] timeout.

- [x] versión Graph API configurable.

- [x] tests de secretos.


### Criterios de aceptación

- [x] configuración carga sin exponer secretos.

- [x] no valores reales versionados.


### Seguridad

- [x] SecretStr para tokens sensibles.

- [x] Graph API version no dispersa.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.1 — Configuración Meta/WhatsApp. No inicies ninguna subfase posterior.

Alcance obligatorio: variables WhatsApp/Meta en Settings; .env.example; timeout; versión Graph API configurable; tests de secretos.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: configuración carga sin exponer secretos; no valores reales versionados. Revisa específicamente esta seguridad: SecretStr para tokens sensibles; Graph API version no dispersa.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.2 — Handshake GET del webhook

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-08-26
**Fecha de finalización:** 2026-08-26


### Alcance

- [x] ruta GET webhook.

- [x] validar mode/token/challenge.

- [x] tests válido/inválido.


### Criterios de aceptación

- [x] Meta puede verificar endpoint en prueba.

- [x] token incorrecto rechazado.


### Seguridad

- [x] no log verify token.

- [x] respuesta mínima.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.2 — Handshake GET del webhook. No inicies ninguna subfase posterior.

Alcance obligatorio: ruta GET webhook; validar mode/token/challenge; tests válido/inválido.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Meta puede verificar endpoint en prueba; token incorrecto rechazado. Revisa específicamente esta seguridad: no log verify token; respuesta mínima.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.3 — Validación de firma del webhook POST

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-08-26
**Fecha de finalización:** 2026-08-26


### Alcance

- [x] leer raw body.

- [x] validar firma oficial vigente.

- [x] HMAC SHA-256 cuando aplique.

- [x] comparación segura.

- [x] tests firmas.


### Criterios de aceptación

- [x] payload no autenticado no se procesa.

- [x] firma válida permite continuar.


### Seguridad

- [x] usar META_APP_SECRET.

- [x] validar antes de confiar en JSON.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.3 — Validación de firma del webhook POST. No inicies ninguna subfase posterior.

Alcance obligatorio: leer raw body; validar firma oficial vigente; HMAC SHA-256 cuando aplique; comparación segura; tests firmas.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: payload no autenticado no se procesa; firma válida permite continuar. Revisa específicamente esta seguridad: usar META_APP_SECRET; validar antes de confiar en JSON.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.4 — Parser y normalización de eventos

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-08-26
**Fecha de finalización:** 2026-08-26


### Alcance

- [x] Pydantic/models de eventos necesarios.

- [x] extraer message id/sender/text.

- [x] ignorar status/eventos no relevantes.

- [x] tipos no soportados.


### Criterios de aceptación

- [x] mensaje texto produce InboundMessage interno.

- [x] payload raro no rompe servidor.


### Seguridad

- [x] límites de texto.

- [x] no log raw body completo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.4 — Parser y normalización de eventos. No inicies ninguna subfase posterior.

Alcance obligatorio: Pydantic/models de eventos necesarios; extraer message id/sender/text; ignorar status/eventos no relevantes; tipos no soportados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mensaje texto produce InboundMessage interno; payload raro no rompe servidor. Revisa específicamente esta seguridad: límites de texto; no log raw body completo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.5 — WhatsAppClient para mensajes salientes

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-08-26
**Fecha de finalización:** 2026-08-26


### Alcance

- [x] cliente Graph API.

- [x] send_text.

- [x] timeout.

- [x] errores.

- [x] tests HTTP mockeados.


### Criterios de aceptación

- [x] payload correcto.

- [x] errores mapeados.

- [x] cliente mockeable.


### Seguridad

- [x] token solo header/backend.

- [x] URL controlada por configuración.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.5 — WhatsAppClient para mensajes salientes. No inicies ninguna subfase posterior.

Alcance obligatorio: cliente Graph API; send_text; timeout; errores; tests HTTP mockeados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: payload correcto; errores mapeados; cliente mockeable. Revisa específicamente esta seguridad: token solo header/backend; URL controlada por configuración.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.6 — Orquestación WhatsApp -> chatbot -> WhatsApp

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-26

**Fecha de finalización:** 2026-08-27


### Alcance

- [x] conectar inbound normalizado al servicio de chat.

- [x] obtener answer.

- [x] enviar answer.

- [x] manejar fallos.


### Criterios de aceptación

- [x] mensaje de texto puede recorrer flujo completo con mocks.


### Seguridad

- [x] webhook no contiene lógica OpenAI directa.

- [x] fallo no filtra datos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.6 — Orquestación WhatsApp -> chatbot -> WhatsApp. No inicies ninguna subfase posterior.

Alcance obligatorio: conectar inbound normalizado al servicio de chat; obtener answer; enviar answer; manejar fallos.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mensaje de texto puede recorrer flujo completo con mocks. Revisa específicamente esta seguridad: webhook no contiene lógica OpenAI directa; fallo no filtra datos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.7 — Idempotencia mínima

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-27

**Fecha de finalización:** 2026-08-27


### Alcance

- [x] interfaz IdempotencyStore.

- [x] detectar IDs duplicados.

- [x] implementación MVP explícitamente temporal.

- [x] tests duplicados.


### Criterios de aceptación

- [x] mismo message id no genera dos respuestas.


### Seguridad

- [x] documentar límite de memoria/multiproceso.

- [x] persistencia obligatoria antes de producción.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.7 — Idempotencia mínima. No inicies ninguna subfase posterior.

Alcance obligatorio: interfaz IdempotencyStore; detectar IDs duplicados; implementación MVP explícitamente temporal; tests duplicados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mismo message id no genera dos respuestas. Revisa específicamente esta seguridad: documentar límite de memoria/multiproceso; persistencia obligatoria antes de producción.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.8 — ACK rápido y separación de procesamiento

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-27

**Fecha de finalización:** 2026-08-27


### Alcance

- [x] separar validación/ACK de trabajo largo.

- [x] mecanismo MVP seguro.

- [x] manejo de excepciones de background.

- [x] tests.


### Criterios de aceptación

- [x] webhook responde de forma predecible.

- [x] trabajo externo no bloquea innecesariamente.


### Seguridad

- [x] sin tareas huérfanas silenciosas.

- [x] sin reintentos infinitos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.8 — ACK rápido y separación de procesamiento. No inicies ninguna subfase posterior.

Alcance obligatorio: separar validación/ACK de trabajo largo; mecanismo MVP seguro; manejo de excepciones de background; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.8 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: webhook responde de forma predecible; trabajo externo no bloquea innecesariamente. Revisa específicamente esta seguridad: sin tareas huérfanas silenciosas; sin reintentos infinitos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.9 — Migración y prueba real con GreenAPI

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-08-27

**Fecha de finalización:** 2026-09-21


### Alcance

- [x] preservar el registro y los contratos internos de F2.1-F2.8.

- [x] reemplazar configuración, webhook, schemas y cliente de Meta por GreenAPI.

- [x] actualizar pruebas y documentación sin llamadas externas.

- [x] conservar como evidencia histórica la configuración, túnel, suscripción y envío realizados
  anteriormente con Meta.

- [x] configurar una instancia real, tokens y webhook de GreenAPI.

- [x] enviar un mensaje real y recibir la respuesta mediante GreenAPI.


### Criterios de aceptación

- [x] WhatsApp -> backend -> OpenAI -> WhatsApp funciona.


### Seguridad

- [x] tokens solo locales/secrets.

- [x] no pegar payloads sensibles completos en documentos.

- [x] restringir el host configurable y evitar que el token incluido en la URL de GreenAPI llegue
  a logs o errores.


### Checkpoint histórico de Meta — 2026-08-27

**Estado de la subfase:** `🟨 EN_PROGRESO`.

Completado en esta sesión:

- aplicación, número de prueba y WABA ID configurados localmente;
- `cloudflared` 2026.8.2 instalado;
- Quick Tunnel temporal levantado y salud pública comprobada con HTTP 200;
- handshake de Meta comprobado con HTTP 200 y devolución exacta del challenge;
- identificador del número validado inicialmente mediante Graph API con HTTP 200;
- usuario confirmó el envío de un mensaje real desde el WhatsApp registrado;
- secretos conservados únicamente en `.env`; no se documentaron números, tokens ni
  payloads;
- Uvicorn ejecutado sin access log y logs temporales anteriores eliminados para evitar
  registrar el verify token de la query.

Comandos y resultados relevantes:

- `.venv\Scripts\python.exe -m pytest` -> 165 passed;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 48 archivos formateados;
- prueba pública del handshake -> HTTP 200 y challenge coincidente;
- dos monitores de eventos reales, de 58 y 30 segundos -> ningún POST recibido;
- validación previa a `POST /{WABA-ID}/subscribed_apps` -> HTTP 401, `code=190`,
  `subcode=463`; el access token temporal expiró y la suscripción no fue modificada.

Archivos modificados:

- `plan_de_trabajo.md` solamente;
- `.env` contiene configuración local del usuario y permanece fuera de Git.

Cierre seguro de la sesión:

- backend local y Quick Tunnel temporal detenidos;
- la URL `trycloudflare.com` usada en esta sesión ya no debe considerarse válida;
- la próxima sesión debe generar una nueva URL y actualizar la callback de Meta.

Falta para completar F2.9:

- generar un nuevo `WHATSAPP_ACCESS_TOKEN` con `whatsapp_business_management` y
  `whatsapp_business_messaging` y reemplazarlo solo en `.env`;
- levantar un nuevo túnel temporal y actualizar/verificar su callback en Meta;
- validar que la WABA contiene el número configurado;
- ejecutar `POST /{WABA-ID}/subscribed_apps` y verificar la suscripción;
- enviar otro mensaje real y comprobar POST autenticado, ACK 200, procesamiento OpenAI y
  respuesta recibida en WhatsApp;
- pasar F2.9 por `🧪 VALIDACION`, repetir validadores y solo entonces marcar
  `✅ COMPLETADO` y agregar el historial de cierre.

Siguiente paso exacto para la próxima sesión:

1. leer `AGENTS.md`, `plan_de_trabajo.md` y `docs/fase_2_whatsapp.md`;
2. confirmar que F2.9 sigue `🟨 EN_PROGRESO` y que F2.10 continúa pendiente;
3. comprobar sin mostrar valores que el nuevo access token está en `.env`;
4. retomar desde la validación segura de token/WABA y la suscripción a
   `/{WABA-ID}/subscribed_apps`.


### Avance histórico de Meta — 2026-09-21

**Estado de la subfase:** `🟨 EN_PROGRESO`.

Completado en esta sesión:

- backend levantado nuevamente sin access log y salud local comprobada con HTTP 200;
- nuevo Quick Tunnel temporal levantado, con registro DNS público y salud HTTPS comprobada con
  HTTP 200;
- handshake público comprobado con HTTP 200 y devolución exacta del challenge;
- callback actualizada y verificada en Meta; el backend registró un nuevo `GET` del webhook con
  HTTP 200;
- el token local anterior fue rechazado por Meta con `code=190` porque pertenecía a una
  aplicación eliminada; el usuario lo reemplazó directamente en `.env` sin compartirlo;
- el token nuevo fue aceptado por Graph API y conserva los permisos
  `whatsapp_business_management` y `whatsapp_business_messaging` en estado `granted`;
- la WABA configurada fue validada y contiene exactamente el número configurado;
- el número coincide con la configuración, usa `CLOUD_API`, conserva calidad `GREEN` y nombre
  `AVAILABLE_WITHOUT_REVIEW`; Meta reporta `code_verification_status=NOT_VERIFIED` para este
  número de prueba;
- `POST /{WABA-ID}/subscribed_apps` respondió `success=true` y la lectura posterior confirmó al
  menos una suscripción; el conteo pasó de una a dos aplicaciones suscritas;
- backend y túnel permanecen activos para continuar la prueba real.

Comandos y resultados relevantes:

- `GET /health` local -> HTTP 200;
- `GET /health` mediante el Quick Tunnel -> HTTP 200;
- handshake público del webhook -> HTTP 200 y challenge coincidente;
- `GET /me` -> token aceptado;
- `GET /me/permissions` -> ambos permisos requeridos en estado `granted`;
- consultas de WABA y número -> identificadores coincidentes y un único número asociado;
- `POST /{WABA-ID}/subscribed_apps` -> `success=true`;
- `GET /{WABA-ID}/subscribed_apps` -> dos aplicaciones suscritas;
- revisión sanitizada del log -> sin errores HTTP ni errores de aplicación durante la
  actualización; ningún body, token, número o payload fue registrado.

Seguridad:

- secretos conservados únicamente en `.env` y enviados a Graph API solo mediante
  `Authorization: Bearer`;
- ningún access token fue enviado en URL, impreso, copiado al plan o compartido en la
  conversación;
- el verify token no aparece en logs porque Uvicorn continúa sin access log y el middleware no
  registra query strings;
- no se documentaron IDs, números completos, nombres de negocio ni payloads de Meta.

Falta para completar F2.9:

- enviar un nuevo mensaje real al número de prueba;
- comprobar POST autenticado, ACK HTTP 200, procesamiento OpenAI y respuesta recibida en
  WhatsApp;
- pasar F2.9 por `🧪 VALIDACION`, repetir validadores y solo entonces marcar
  `✅ COMPLETADO`.

### Migración a GreenAPI — 2026-09-21

**Estado de la subfase:** `✅ COMPLETADO`.

Cambio de proveedor autorizado por el usuario:

- confirmada la viabilidad técnica con la documentación oficial de GreenAPI;
- sustituidas las variables de Meta por ID de instancia, token de instancia, host API y token de
  webhook de GreenAPI;
- eliminado el handshake GET y reemplazada la firma HMAC de Meta por autenticación
  `Authorization: Bearer` previa a la lectura del body;
- adaptado el parser a `incomingMessageReceived`, `textMessage`, `extendedTextMessage` y
  `quotedMessage`, validando que el evento pertenezca a la instancia configurada;
- adaptado `WhatsAppClient` a `sendMessage`, conservando la interfaz usada por el orquestador;
- mantenidos `InboundMessage`, `MessageOrchestrator`, idempotencia, `BackgroundTasks` y el
  registro de fases ya establecido;
- añadido allowlist HTTPS para hosts GreenAPI y supresión de logs informativos de `httpx` y
  `httpcore`, ya que el protocolo del proveedor exige el token en el path;
- actualizados tests, `.env.example`, README, guía técnica y reglas del repositorio;
- actualizado el `.env` local: eliminadas las cinco entradas obsoletas de Meta y agregadas las
  cuatro entradas GreenAPI; las credenciales reales se configuraron posteriormente sin
  compartirlas ni versionarlas;
- backend y túnel reiniciados posteriormente para cargar el código y entorno actuales.

Validación automática:

- suite completa -> 171 pruebas aprobadas sin red externa;
- pruebas específicas cubren autenticación antes del body, payloads entrantes, envío saliente,
  errores seguros, deduplicación y ausencia del token en logs;
- validadores finales de lint, formato, dependencias y diff se registran en el historial de esta
  migración.

Cierre de la migración:

- instancia autorizada, credenciales locales, host asignado y webhook configurados;
- backend y endpoint HTTPS público verificados;
- mensaje real procesado con ACK 200 y sin fallos de background;
- respuesta final recibida en WhatsApp y confirmada por el usuario;
- F2.9 pasó a `🧪 VALIDACION`; F2.10 permanece sin iniciar.

### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.9 — Migración y prueba real con GreenAPI. No inicies ninguna subfase posterior.

Alcance obligatorio: configurar instancia y tokens locales de GreenAPI; URL HTTPS accesible; registrar el webhook autenticado; enviar mensaje real; recibir respuesta.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.9 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: WhatsApp -> backend -> OpenAI -> WhatsApp funciona. Revisa específicamente esta seguridad: tokens solo locales/secrets; no pegar payloads sensibles completos en documentos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.10 — Cierre Fase 2

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-21

**Fecha de finalización:** 2026-09-21


### Alcance

- [x] pruebas.

- [x] documentación.

- [x] revisión seguridad.

- [x] actualizar plan.


### Criterios de aceptación

- [x] Fase 2 completa y reproducible.


### Seguridad

- [x] no declarar producción-ready todavía.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.10 — Cierre Fase 2. No inicies ninguna subfase posterior.

Alcance obligatorio: pruebas; documentación; revisión seguridad; actualizar plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.10 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 2 completa y reproducible. Revisa específicamente esta seguridad: no declarar producción-ready todavía.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 7. FASE 3 — Persistencia comercial — sucursales, productos y precios

**Objetivo:** Crear SQLite como primera fuente de verdad para datos comerciales, aislados por la
sucursal asignada a cada asistente.

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-21

**Fecha de finalización:** 2026-09-22

**Documento guía:** `plan_de_trabajo.md`


## F3.1 — SQLAlchemy + Alembic + SQLite

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-21

**Fecha de finalización:** 2026-09-21


### Alcance

- [x] configuración DB.

- [x] engine/session.

- [x] Alembic.

- [x] primera migración base.

- [x] tests.


### Criterios de aceptación

- [x] DB reproducible desde migraciones.

- [x] tests aislados.


### Seguridad

- [x] URL DB configurable.

- [x] no SQL concatenado.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.1 — SQLAlchemy + Alembic + SQLite. No inicies ninguna subfase posterior.

Alcance obligatorio: configuración DB; engine/session; Alembic; primera migración base; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: DB reproducible desde migraciones; tests aislados. Revisa específicamente esta seguridad: URL DB configurable; no SQL concatenado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.2 — Entidad sucursales e identidad por asistente

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-22

**Fecha de finalización:** 2026-09-22


### Alcance

- [x] modelo Branch.

- [x] constraints.

- [x] repository.

- [x] service.

- [x] identidad fija `ASSISTANT_BRANCH_CODE` por instalación.

- [x] perfil JSON versionado y carga idempotente por instalación.

- [x] fixtures ficticios.

- [x] tests.


### Criterios de aceptación

- [x] CRUD interno/repository válido.

- [x] una instalación solo puede cargar y consultar su propia sucursal.


### Seguridad

- [x] dirección/teléfono tratados como datos de negocio.

- [x] `branch_id`/`branch_code` no provienen del mensaje ni de argumentos del modelo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.2 — Entidad sucursales e identidad por asistente. No inicies ninguna subfase posterior.

Alcance obligatorio: modelo Branch; constraints; repository; servicio limitado a la sucursal configurada; ASSISTANT_BRANCH_CODE obligatorio; perfil JSON versionado; carga idempotente con preview/confirmación; fixtures ficticios; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: CRUD interno/repository válido; una instalación solo carga y consulta su propia sucursal. Revisa específicamente esta seguridad: dirección/teléfono tratados como datos de negocio; branch_id/branch_code nunca vienen del cliente o del modelo; rechazar perfiles de otra instalación antes de escribir.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.3 — Entidad productos

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-22
**Fecha de finalización:** 2026-09-22


### Alcance

- [x] Product.

- [x] categoría.

- [x] estado activo.

- [x] relación/alcance obligatorio de sucursal para disponibilidad del catálogo.

- [x] repositorio.

- [x] tests.


### Criterios de aceptación

- [x] productos consultables de forma determinística dentro de la sucursal configurada.


### Seguridad

- [x] nombres/inputs validados.

- [x] ninguna consulta del asistente puede enumerar productos de otra sucursal.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.3 — Entidad productos. No inicies ninguna subfase posterior.

Alcance obligatorio: Product; categoría; estado activo; repositorio; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: productos consultables de forma determinística. Revisa específicamente esta seguridad: nombres/inputs validados.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.4 — Entidad precios por sucursal

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-22
**Fecha de finalización:** 2026-09-22


### Alcance

- [x] Price.

- [x] producto+sucursal.

- [x] unidad.

- [x] vigencia/updated_at.

- [x] constraints.

- [x] repositorio.

- [x] filtro obligatorio por sucursal inyectado por backend.

- [x] tests.


### Criterios de aceptación

- [x] precio exacto por producto/sucursal.

- [x] no duplicados inválidos.

- [x] una instalación no puede leer el precio de otra sucursal.


### Seguridad

- [x] Decimal, no float para dinero.

- [x] precio no negativo.

- [x] `branch_id` no se acepta desde el modelo o cliente.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.4 — Entidad precios por sucursal. No inicies ninguna subfase posterior.

Alcance obligatorio: Price; producto+sucursal; unidad; vigencia/updated_at; constraints; repositorio; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: precio exacto por producto/sucursal; no duplicados inválidos. Revisa específicamente esta seguridad: Decimal, no float para dinero; precio no negativo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.5 — Servicios de consulta comercial

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-22
**Fecha de finalización:** 2026-09-22


### Alcance

- [x] get_branch_info.

- [x] search_product.

- [x] get_product_price.

- [x] `BranchScope` inyectado desde `ASSISTANT_BRANCH_CODE`.

- [x] casos no encontrados.

- [x] tests.


### Criterios de aceptación

- [x] servicios no dependen de OpenAI.

- [x] la API interna del asistente no recibe sucursal como argumento.


### Seguridad

- [x] solo lectura para chatbot.

- [x] pruebas de acceso cruzado entre al menos dos sucursales.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.5 — Servicios de consulta comercial. No inicies ninguna subfase posterior.

Alcance obligatorio: get_branch_info; search_product; get_product_price; BranchScope backend; casos no encontrados; pruebas de aislamiento entre sucursales.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: servicios no dependen de OpenAI y no reciben la sucursal desde input no confiable. Revisa específicamente esta seguridad: solo lectura para chatbot; BranchScope inyectado; pruebas negativas de acceso cruzado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.6 — Integridad, migraciones y cierre

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-22

**Fecha de validación:** 2026-09-22

**Fecha de finalización:** 2026-09-22


### Alcance

- [x] probar migración desde cero.

- [x] constraints.

- [x] rollback.

- [x] README.

- [x] plan.


### Criterios de aceptación

- [x] Fase 3 completa.


### Seguridad

- [x] backup antes de futuras migraciones productivas.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.6 — Integridad, migraciones y cierre. No inicies ninguna subfase posterior.

Alcance obligatorio: probar migración desde cero; constraints; rollback; README; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 3 completa. Revisa específicamente esta seguridad: backup antes de futuras migraciones productivas.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 8. FASE 4 — FAQ y conocimiento general del negocio

**Objetivo:** Responder información general mediante una fuente controlada sin convertir documentos en instrucciones privilegiadas.

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-22

**Fecha de finalización:** 2026-09-23

**Documento guía:** `plan_de_trabajo.md`


## F4.1 — Formato y fuente FAQ

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-22

**Fecha de validación:** 2026-09-22

**Fecha de finalización:** 2026-09-22


### Alcance

- [x] definir estructura TXT/Markdown o tabla.

- [x] categorías.

- [x] sucursal obligatoria/interna para cada registro cargado por una instalación.

- [x] ejemplos ficticios.


### Criterios de aceptación

- [x] formato documentado y validable.


### Seguridad

- [x] sin secretos.

- [x] documentos son datos no instrucciones.

- [x] un asistente no busca FAQ de otra sucursal.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.1 — Formato y fuente FAQ. No inicies ninguna subfase posterior.

Alcance obligatorio: definir estructura TXT/Markdown o tabla; categorías; alcance obligatorio de la sucursal configurada; ejemplos ficticios.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: formato documentado y validable. Revisa específicamente esta seguridad: sin secretos; documentos son datos no instrucciones.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.2 — Loader/servicio de FAQ

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-22

**Fecha de validación:** 2026-09-22

**Fecha de finalización:** 2026-09-22


### Alcance

- [x] loader.

- [x] normalización.

- [x] búsqueda básica.

- [x] filtro de sucursal inyectado por backend.

- [x] errores.

- [x] tests.


### Criterios de aceptación

- [x] FAQ consultable sin OpenAI.

- [x] resultados limitados a la instalación actual.


### Seguridad

- [x] límites de tamaño.

- [x] encoding/control de errores.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.2 — Loader/servicio de FAQ. No inicies ninguna subfase posterior.

Alcance obligatorio: loader; normalización; búsqueda básica; errores; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: FAQ consultable sin OpenAI. Revisa específicamente esta seguridad: límites de tamaño; encoding/control de errores.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.3 — Política de respuesta y desconocidos

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-22

**Fecha de validación:** 2026-09-22

**Fecha de cierre:** 2026-09-22


### Alcance

- [x] reglas no inventar.

- [x] fallback.

- [x] request_human_help conceptual.

- [x] tests.


### Criterios de aceptación

- [x] pregunta desconocida no genera dato falso.


### Seguridad

- [x] defensa contra prompt injection.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.3 — Política de respuesta y desconocidos. No inicies ninguna subfase posterior.

Alcance obligatorio: reglas no inventar; fallback; request_human_help conceptual; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: pregunta desconocida no genera dato falso. Revisa específicamente esta seguridad: defensa contra prompt injection.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.4 — Pruebas adversariales de conocimiento

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-23

**Fecha de finalización:** 2026-09-23


### Alcance

- [x] prompt injection.

- [x] pedido de secrets.

- [x] conflicto documento/system.

- [x] FAQ ambigua.


### Criterios de aceptación

- [x] reglas internas prevalecen.


### Seguridad

- [x] no confiar en texto recuperado.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.4 — Pruebas adversariales de conocimiento. No inicies ninguna subfase posterior.

Alcance obligatorio: prompt injection; pedido de secrets; conflicto documento/system; FAQ ambigua.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: reglas internas prevalecen. Revisa específicamente esta seguridad: no confiar en texto recuperado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.5 — Cierre Fase 4

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-23

**Fecha de finalización:** 2026-09-23


### Alcance

- [x] documentación.

- [x] tests.

- [x] plan.


### Criterios de aceptación

- [x] Fase 4 completa.


### Seguridad

- [x] no añadir RAG si no es necesario.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.5 — Cierre Fase 4. No inicies ninguna subfase posterior.

Alcance obligatorio: documentación; tests; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 4 completa. Revisa específicamente esta seguridad: no añadir RAG si no es necesario.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 9. FASE 5 — Importación segura de Excel

**Objetivo:** Permitir que personal autorizado actualice precios mediante un archivo validado y transaccional.

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-23
**Fecha de finalización:** 2026-09-23

**Documento guía:** `plan_de_trabajo.md`


## F5.1 — Contrato/plantilla Excel

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-23

**Fecha de finalización:** 2026-09-23


### Alcance

- [x] columnas obligatorias.

- [x] IDs/nombres.

- [x] unidad.

- [x] precio.

- [x] fecha.

- [x] código de sucursal del archivo igual a `ASSISTANT_BRANCH_CODE`.

- [x] ejemplo ficticio.


### Criterios de aceptación

- [x] plantilla inequívoca.

- [x] un archivo pertenece a una sola sucursal.


### Seguridad

- [x] no macros.

- [x] no datos reales en fixtures si no se proporcionan.

- [x] contrato de un solo `branch_code` por archivo; el rechazo operativo de archivos alterados
  corresponde al parser de F5.2.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.1 — Contrato/plantilla Excel. No inicies ninguna subfase posterior.

Alcance obligatorio: columnas obligatorias; IDs/nombres; unidad; precio; fecha; ejemplo ficticio.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: plantilla inequívoca. Revisa específicamente esta seguridad: no macros; no datos reales en fixtures si no se proporcionan.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.2 — Parser y validación

**Estado:** ✅ COMPLETADO

**Fecha de inicio:** 2026-09-23
**Fecha de finalización:** 2026-09-23


### Alcance

- [x] pandas/openpyxl: `openpyxl`.

- [x] extensión.

- [x] tamaño.

- [x] headers.

- [x] tipos.

- [x] duplicados.

- [x] rangos.

- [x] errores por fila.

- [x] rechazo temprano de código de sucursal ajeno.


### Criterios de aceptación

- [x] archivo inválido no modifica DB.

- [x] archivo de otra sucursal no modifica DB.


### Seguridad

- [x] prevenir path traversal.

- [x] no ejecutar macros.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.2 — Parser y validación. No inicies ninguna subfase posterior.

Alcance obligatorio: pandas/openpyxl; extensión; tamaño; headers; tipos; duplicados; rangos; errores por fila.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: archivo inválido no modifica DB. Revisa específicamente esta seguridad: prevenir path traversal; no ejecutar macros.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.3 — Preview de cambios

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-23
**Fecha de finalización:** 2026-09-23


### Alcance

- [x] diff altas/cambios/errores.

- [x] sin persistir.

- [x] tests.


### Criterios de aceptación

- [x] administrador puede revisar impacto mediante resultado estructurado del servicio.


### Seguridad

- [x] no mostrar datos sensibles innecesarios.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.3 — Preview de cambios. No inicies ninguna subfase posterior.

Alcance obligatorio: diff altas/cambios/errores; sin persistir; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: administrador puede revisar impacto. Revisa específicamente esta seguridad: no mostrar datos sensibles innecesarios.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.4 — Importación transaccional

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-23
**Fecha de finalización:** 2026-09-23


### Alcance

- [x] confirmación.

- [x] transacción.

- [x] upserts controlados.

- [x] `branch_id` inyectado por backend, nunca tomado como autoridad desde una celda.

- [x] rollback.

- [x] tests.


### Criterios de aceptación

- [x] todo-o-nada ante error.


### Seguridad

- [x] auditabilidad mediante recibo con SHA-256, sucursal y conteos; registro duradero en F5.5.

- [x] Decimal para dinero.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.4 — Importación transaccional. No inicies ninguna subfase posterior.

Alcance obligatorio: confirmación; transacción; upserts controlados; rollback; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: todo-o-nada ante error. Revisa específicamente esta seguridad: auditabilidad; Decimal para dinero.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.5 — Auditoría y reporte

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-23
**Fecha de cierre:** 2026-09-23


### Alcance

- [x] registro de quién/cuándo/archivo lógico.

- [x] resumen.

- [x] errores.


### Criterios de aceptación

- [x] importación trazable.


### Seguridad

- [x] no conservar archivo más de lo necesario.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.5 — Auditoría y reporte. No inicies ninguna subfase posterior.

Alcance obligatorio: registro de quién/cuándo/archivo lógico; resumen; errores.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: importación trazable. Revisa específicamente esta seguridad: no conservar archivo más de lo necesario.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.6 — Cierre Fase 5

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-23
**Fecha de finalización:** 2026-09-23


### Alcance

- [x] tests.

- [x] documentación.

- [x] plan.


### Criterios de aceptación

- [x] Fase 5 completa para el servicio interno de importación.


### Seguridad

- [x] revisión de carga maliciosa.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.6 — Cierre Fase 5. No inicies ninguna subfase posterior.

Alcance obligatorio: tests; documentación; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 5 completa. Revisa específicamente esta seguridad: revisión de carga maliciosa.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 10. FASE 6 — OpenAI tool calling para datos exactos

**Objetivo:** Permitir que el modelo solicite operaciones de solo lectura específicas sin acceso libre a SQL.

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-23
**Fecha de cierre:** 2026-09-24

**Documento guía:** `plan_de_trabajo.md`


## F6.1 — Schemas de tools

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-23
**Fecha de finalización:** 2026-09-23


### Alcance

- [x] get_product_price.

- [x] get_branch_info.

- [x] search_faq.

- [x] request_human_help.

- [x] schemas estrictos.

- [x] ningún schema expone `branch_id` o `branch_code` al modelo.


### Criterios de aceptación

- [x] argumentos claramente validados.


### Seguridad

- [x] allowlist cerrada.

- [x] alcance de sucursal inyectado después de validar la tool.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.1 — Schemas de tools. No inicies ninguna subfase posterior.

Alcance obligatorio: get_product_price; get_branch_info; search_faq; request_human_help; schemas estrictos.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: argumentos claramente validados. Revisa específicamente esta seguridad: allowlist cerrada.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.2 — Implementaciones de tools

**Estado:** ✅ COMPLETADO

**Inicio:** 2026-09-23.
**Cierre:** 2026-09-23; pasó por `🧪 VALIDACION`.


### Alcance

- [x] adaptar servicios comerciales/FAQ.

- [x] resultados tipados.

- [x] no encontrado.

- [x] tests.

- [x] `BranchScope` obligatorio para handlers comerciales/FAQ.


### Criterios de aceptación

- [x] tools funcionan sin modelo.


### Seguridad

- [x] solo mínimo privilegio.

- [x] pruebas demuestran que argumentos del modelo no cambian sucursal.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.2 — Implementaciones de tools. No inicies ninguna subfase posterior.

Alcance obligatorio: adaptar servicios comerciales/FAQ; resultados tipados; no encontrado; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: tools funcionan sin modelo. Revisa específicamente esta seguridad: solo mínimo privilegio.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.3 — Dispatcher allowlist

**Estado:** ✅ COMPLETADO
**Inicio:** 2026-09-23.
**Cierre:** 2026-09-23; pasó por `🧪 VALIDACION`.


### Alcance

- [x] map nombre->handler.

- [x] rechazar tool desconocida.

- [x] validar argumentos.

- [x] timeouts.

- [x] tests.


### Criterios de aceptación

- [x] no ejecución arbitraria.


### Seguridad

- [x] prohibido execute_sql.

- [x] dispatcher compone handlers con la sucursal de la instalación.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.3 — Dispatcher allowlist. No inicies ninguna subfase posterior.

Alcance obligatorio: map nombre->handler; rechazar tool desconocida; validar argumentos; timeouts; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: no ejecución arbitraria. Revisa específicamente esta seguridad: prohibido execute_sql.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.4 — Loop Responses API + tool calls

**Estado:** ✅ COMPLETADO
**Inicio:** 2026-09-23.
**Cierre:** 2026-09-23; pasó por `🧪 VALIDACION`.


### Alcance

- [x] detectar tool call.

- [x] ejecutar.

- [x] devolver resultado.

- [x] respuesta final.

- [x] límite de iteraciones.

- [x] tests mockeados.


### Criterios de aceptación

- [x] flujo determinista y acotado.


### Seguridad

- [x] evitar loop infinito.

- [x] no confiar en args modelo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.4 — Loop Responses API + tool calls. No inicies ninguna subfase posterior.

Alcance obligatorio: detectar tool call; ejecutar; devolver resultado; respuesta final; límite de iteraciones; tests mockeados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: flujo determinista y acotado. Revisa específicamente esta seguridad: evitar loop infinito; no confiar en args modelo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.5 — Desambiguación de producto con sucursal fija

**Estado:** ✅ COMPLETADO
**Inicio:** 2026-09-23.
**Cierre:** 2026-09-23; pasó por `🧪 VALIDACION`.


### Alcance

- [x] informar la sucursal propia cuando sea útil, sin pedir al cliente que la seleccione.

- [x] coincidencias múltiples.

- [x] producto inexistente.

- [x] tests.


### Criterios de aceptación

- [x] no mezclar precios de sucursales.

- [x] mencionar otra tienda no cambia el alcance de datos.


### Seguridad

- [x] nunca adivinar producto ni sucursal.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.5 — Desambiguación de producto con sucursal fija. No inicies ninguna subfase posterior.

Alcance obligatorio: informar sucursal propia sin permitir selección; coincidencias múltiples de producto; producto inexistente; mención de otra tienda sin cambio de alcance; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: no mezclar precios de sucursales. Revisa específicamente esta seguridad: nunca adivinar.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.6 — Pruebas de seguridad de tools

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] prompt injection.

- [x] tool inexistente.

- [x] args inválidos.

- [x] SQL injection.

- [x] exfiltración.


### Criterios de aceptación

- [x] modelo no amplía privilegios.


### Seguridad

- [x] auditar tool name/result status sin datos excesivos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.6 — Pruebas de seguridad de tools. No inicies ninguna subfase posterior.

Alcance obligatorio: prompt injection; tool inexistente; args inválidos; SQL injection; exfiltración.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: modelo no amplía privilegios. Revisa específicamente esta seguridad: auditar tool name/result status sin datos excesivos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.7 — Cierre Fase 6

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] tests.

- [x] docs.

- [x] plan.


### Criterios de aceptación

- [x] Fase 6 completa.


### Seguridad

- [x] revisar costos/loops.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.7 — Cierre Fase 6. No inicies ninguna subfase posterior.

Alcance obligatorio: tests; docs; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 6 completa. Revisa específicamente esta seguridad: revisar costos/loops.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 11. FASE 7 — Conversaciones WhatsApp + idempotencia persistente

**Objetivo:** Guardar el contexto mínimo necesario para conversaciones, deduplicar eventos y registrar preguntas no resueltas.

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24

**Documento guía:** `plan_de_trabajo.md`


## F7.1 — Esquema conversations/messages/events

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] Conversation.

- [x] Message mínimo.

- [x] WhatsAppEventReceipt.

- [x] migraciones.

- [x] tests.


### Criterios de aceptación

- [x] modelo soporta canal WhatsApp.


### Seguridad

- [x] minimización de datos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.1 — Esquema conversations/messages/events. No inicies ninguna subfase posterior.

Alcance obligatorio: Conversation; Message mínimo; WhatsAppEventReceipt; migraciones; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: modelo soporta canal WhatsApp. Revisa específicamente esta seguridad: minimización de datos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.2 — Identidad externa y sucursal inmutable de la instalación

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] external_user_id.

- [x] branch context derivado de la instalación.

- [x] impedir que mensajes actualicen la sucursal.

- [x] tests.


### Criterios de aceptación

- [x] '¿y el rib eye?' conserva sucursal cuando corresponde.

- [x] toda conversación del número pertenece a la sucursal configurada.


### Seguridad

- [x] identificador redactado en logs.

- [x] no persistir una sucursal proporcionada por el cliente o el modelo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.2 — Identidad externa y sucursal inmutable de la instalación. No inicies ninguna subfase posterior.

Alcance obligatorio: external_user_id; branch context derivado de configuración; impedir cambios desde mensajes; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: '¿y el rib eye?' conserva sucursal cuando corresponde. Revisa específicamente esta seguridad: identificador redactado en logs.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.3 — Idempotencia persistente

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] reemplazar store temporal.

- [x] unique external message id.

- [x] transacción.

- [x] tests concurrentes razonables.


### Criterios de aceptación

- [x] duplicados no producen doble respuesta.


### Seguridad

- [x] manejar carrera.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.3 — Idempotencia persistente. No inicies ninguna subfase posterior.

Alcance obligatorio: reemplazar store temporal; unique external message id; transacción; tests concurrentes razonables.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: duplicados no producen doble respuesta. Revisa específicamente esta seguridad: manejar carrera.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.4 — Política de retención y redacción

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] definir qué guardar.

- [x] retention.

- [x] borrado.

- [x] redacción.

- [x] tests.


### Criterios de aceptación

- [x] privacidad documentada.


### Seguridad

- [x] no almacenar más de lo necesario.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.4 — Política de retención y redacción. No inicies ninguna subfase posterior.

Alcance obligatorio: definir qué guardar; retention; borrado; redacción; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: privacidad documentada. Revisa específicamente esta seguridad: no almacenar más de lo necesario.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.5 — Preguntas no resueltas

**Estado:** ✅ COMPLETADO
**Inicio:** 2026-09-24
**Cierre:** 2026-09-24


### Alcance

- [x] entidad/contador.

- [x] normalización.

- [x] registro.

- [x] tests.


### Criterios de aceptación

- [x] panel futuro puede consultarlas.


### Seguridad

- [x] no guardar PII innecesaria.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.5 — Preguntas no resueltas. No inicies ninguna subfase posterior.

Alcance obligatorio: entidad/contador; normalización; registro; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: panel futuro puede consultarlas. Revisa específicamente esta seguridad: no guardar PII innecesaria.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.6 — Cierre Fase 7

**Estado:** ✅ COMPLETADO
**Fecha de inicio:** 2026-09-24
**Fecha de cierre:** 2026-09-24


### Alcance

- [x] migraciones desde cero.

- [x] tests.

- [x] docs.

- [x] plan.


### Criterios de aceptación

- [x] Fase 7 completa.


### Seguridad

- [x] backup/restore planificado.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.6 — Cierre Fase 7. No inicies ninguna subfase posterior.

Alcance obligatorio: migraciones desde cero; tests; docs; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 7 completa. Revisa específicamente esta seguridad: backup/restore planificado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 12. FASE 8 — Panel administrativo seguro

**Objetivo:** Crear una interfaz de PC para administrar datos, revisar conversaciones y operar el sistema sin exponer secretos.

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F8.1 — Autenticación backend

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] modelo AdminUser.

- [ ] hash password mantenido.

- [ ] login/logout.

- [ ] sesión/token.

- [ ] tests.


### Criterios de aceptación

- [ ] password nunca plano.


### Seguridad

- [ ] rate limiting login.

- [ ] cookies/JWT correctamente configurados.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.1 — Autenticación backend. No inicies ninguna subfase posterior.

Alcance obligatorio: modelo AdminUser; hash password mantenido; login/logout; sesión/token; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: password nunca plano. Revisa específicamente esta seguridad: rate limiting login; cookies/JWT correctamente configurados.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.2 — RBAC y endpoints admin

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] roles.

- [ ] dependencias autorización.

- [ ] /api/v1/admin.

- [ ] tests 401/403.

- [ ] permisos por sucursal cuando un usuario no sea global.


### Criterios de aceptación

- [ ] backend bloquea privilegios.


### Seguridad

- [ ] no confiar en frontend.

- [ ] backend impide CRUD cruzado entre sucursales.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.2 — RBAC y endpoints admin. No inicies ninguna subfase posterior.

Alcance obligatorio: roles; dependencias autorización; /api/v1/admin; tests 401/403.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: backend bloquea privilegios. Revisa específicamente esta seguridad: no confiar en frontend.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.3 — Shell frontend

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] React/Next.js.

- [ ] login UI.

- [ ] layout.

- [ ] cliente API.

- [ ] error states.


### Criterios de aceptación

- [ ] panel abre en PC.


### Seguridad

- [ ] sin secrets.

- [ ] XSS/CORS.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.3 — Shell frontend. No inicies ninguna subfase posterior.

Alcance obligatorio: React/Next.js; login UI; layout; cliente API; error states.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: panel abre en PC. Revisa específicamente esta seguridad: sin secrets; XSS/CORS.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.4 — CRUD comercial

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] sucursales.

- [ ] productos.

- [ ] precios.

- [ ] FAQ.

- [ ] validación.

- [ ] tests.

- [ ] filtros y autorización de sucursal en backend.


### Criterios de aceptación

- [ ] datos administrables.


### Seguridad

- [ ] audit log en cambios críticos.

- [ ] un operador de tienda no modifica otra tienda.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.4 — CRUD comercial. No inicies ninguna subfase posterior.

Alcance obligatorio: sucursales; productos; precios; FAQ; validación; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: datos administrables. Revisa específicamente esta seguridad: audit log en cambios críticos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.5 — UI importación Excel

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] upload.

- [ ] preview.

- [ ] confirmación.

- [ ] resultado.

- [ ] mostrar la sucursal destino fijada por backend.


### Criterios de aceptación

- [ ] flujo seguro usable.


### Seguridad

- [ ] CSRF/autorización, límites archivo.

- [ ] no permitir cambiar sucursal manipulando el formulario.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.5 — UI importación Excel. No inicies ninguna subfase posterior.

Alcance obligatorio: upload; preview; confirmación; resultado.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: flujo seguro usable. Revisa específicamente esta seguridad: CSRF/autorización, límites archivo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.6 — Conversaciones y preguntas no resueltas

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] listado.

- [ ] filtros.

- [ ] detalle mínimo.

- [ ] resolver FAQ.


### Criterios de aceptación

- [ ] operación útil.


### Seguridad

- [ ] PII minimizada.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.6 — Conversaciones y preguntas no resueltas. No inicies ninguna subfase posterior.

Alcance obligatorio: listado; filtros; detalle mínimo; resolver FAQ.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: operación útil. Revisa específicamente esta seguridad: PII minimizada.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.7 — Auditoría administrativa

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] actor.

- [ ] acción.

- [ ] timestamp.

- [ ] entidad.

- [ ] before/after seguro.


### Criterios de aceptación

- [ ] cambios de precio trazables.


### Seguridad

- [ ] no guardar passwords/tokens.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.7 — Auditoría administrativa. No inicies ninguna subfase posterior.

Alcance obligatorio: actor; acción; timestamp; entidad; before/after seguro.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: cambios de precio trazables. Revisa específicamente esta seguridad: no guardar passwords/tokens.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.8 — Pruebas seguridad panel

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] authz.

- [ ] CSRF si aplica.

- [ ] XSS.

- [ ] CORS.

- [ ] fuerza bruta básica.

- [ ] session expiry.


### Criterios de aceptación

- [ ] controles pasan.


### Seguridad

- [ ] ningún endpoint admin anónimo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.8 — Pruebas seguridad panel. No inicies ninguna subfase posterior.

Alcance obligatorio: authz; CSRF si aplica; XSS; CORS; fuerza bruta básica; session expiry.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.8 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: controles pasan. Revisa específicamente esta seguridad: ningún endpoint admin anónimo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F8.9 — Cierre Fase 8

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] tests.

- [ ] build.

- [ ] docs.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 8 completa.


### Seguridad

- [ ] no exponer aún a internet sin F10.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F8.9 — Cierre Fase 8. No inicies ninguna subfase posterior.

Alcance obligatorio: tests; build; docs; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F8.9 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 8 completa. Revisa específicamente esta seguridad: no exponer aún a internet sin F10.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 13. FASE 9 — Atención humana desde el panel

**Objetivo:** Permitir que un empleado tome una conversación de WhatsApp y responda sin que la IA compita con él.

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F9.1 — Estado AI/HUMAN

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] conversation mode.

- [ ] transiciones.

- [ ] servicio.

- [ ] tests.


### Criterios de aceptación

- [ ] un solo responsable responde.


### Seguridad

- [ ] transiciones autorizadas.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F9.1 — Estado AI/HUMAN. No inicies ninguna subfase posterior.

Alcance obligatorio: conversation mode; transiciones; servicio; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F9.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: un solo responsable responde. Revisa específicamente esta seguridad: transiciones autorizadas.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F9.2 — Bandeja de conversaciones

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] lista activas.

- [ ] filtros.

- [ ] detalle.

- [ ] tomar/liberar.


### Criterios de aceptación

- [ ] empleado puede tomar chat.


### Seguridad

- [ ] RBAC/PII.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F9.2 — Bandeja de conversaciones. No inicies ninguna subfase posterior.

Alcance obligatorio: lista activas; filtros; detalle; tomar/liberar.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F9.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: empleado puede tomar chat. Revisa específicamente esta seguridad: RBAC/PII.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F9.3 — Respuesta humana por WhatsApp

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] endpoint admin.

- [ ] WhatsAppClient.

- [ ] confirmación de envío.

- [ ] estado.

- [ ] tests.

- [ ] cliente GreenAPI seleccionado por la sucursal de la conversación.


### Criterios de aceptación

- [ ] mensaje manual llega por el mismo canal.


### Seguridad

- [ ] solo usuario autorizado.

- [ ] nunca enviar desde el número de otra sucursal.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F9.3 — Respuesta humana por WhatsApp. No inicies ninguna subfase posterior.

Alcance obligatorio: endpoint admin; WhatsAppClient; confirmación de envío; estado; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F9.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mensaje manual llega por el mismo canal. Revisa específicamente esta seguridad: solo usuario autorizado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F9.4 — Handoff automático/manual

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] request_human_help.

- [ ] fallback IA.

- [ ] reglas.

- [ ] notificación panel.


### Criterios de aceptación

- [ ] casos sin respuesta se escalan.


### Seguridad

- [ ] no prometer que humano respondió hasta confirmación.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F9.4 — Handoff automático/manual. No inicies ninguna subfase posterior.

Alcance obligatorio: request_human_help; fallback IA; reglas; notificación panel.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F9.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: casos sin respuesta se escalan. Revisa específicamente esta seguridad: no prometer que humano respondió hasta confirmación.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F9.5 — Auditoría y cierre

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] actor.

- [ ] mensajes.

- [ ] tests.

- [ ] docs.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 9 completa.


### Seguridad

- [ ] retención conforme política.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F9.5 — Auditoría y cierre. No inicies ninguna subfase posterior.

Alcance obligatorio: actor; mensajes; tests; docs; plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F9.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 9 completa. Revisa específicamente esta seguridad: retención conforme política.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 14. FASE 10 — Hardening, observabilidad y despliegue

**Objetivo:** Preparar el sistema para exposición pública con controles de seguridad, operación, costos y recuperación.

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F10.1 — Rate limiting y límites de recursos

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] webhook/admin/internal endpoints.

- [ ] body limits.

- [ ] timeouts.

- [ ] retries.

- [ ] tests.


### Criterios de aceptación

- [ ] abuso básico mitigado.


### Seguridad

- [ ] no bloquear webhooks legítimos por diseño deficiente.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.1 — Rate limiting y límites de recursos. No inicies ninguna subfase posterior.

Alcance obligatorio: webhook/admin/internal endpoints; body limits; timeouts; retries; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: abuso básico mitigado. Revisa específicamente esta seguridad: no bloquear webhooks legítimos por diseño deficiente.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.2 — HTTPS, proxy y headers

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] TLS.

- [ ] reverse proxy.

- [ ] trusted proxies.

- [ ] security headers.

- [ ] CSP panel.


### Criterios de aceptación

- [ ] HTTPS obligatorio.


### Seguridad

- [ ] no confiar X-Forwarded-* indiscriminadamente.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.2 — HTTPS, proxy y headers. No inicies ninguna subfase posterior.

Alcance obligatorio: TLS; reverse proxy; trusted proxies; security headers; CSP panel.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: HTTPS obligatorio. Revisa específicamente esta seguridad: no confiar X-Forwarded-* indiscriminadamente.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.3 — Secrets y rotación

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] secret manager.

- [ ] rotación OpenAI/Meta/admin.

- [ ] procedimiento.

- [ ] tests/config.


### Criterios de aceptación

- [ ] secretos fuera de imagen/repositorio.


### Seguridad

- [ ] revocar credencial comprometida.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.3 — Secrets y rotación. No inicies ninguna subfase posterior.

Alcance obligatorio: secret manager; rotación OpenAI/Meta/admin; procedimiento; tests/config.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: secretos fuera de imagen/repositorio. Revisa específicamente esta seguridad: revocar credencial comprometida.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.4 — Observabilidad y costos

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] structured logs.

- [ ] metrics.

- [ ] latencia.

- [ ] errores Meta/OpenAI.

- [ ] uso/costo.

- [ ] alertas.


### Criterios de aceptación

- [ ] operación medible.


### Seguridad

- [ ] PII/tokens redactados.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.4 — Observabilidad y costos. No inicies ninguna subfase posterior.

Alcance obligatorio: structured logs; metrics; latencia; errores Meta/OpenAI; uso/costo; alertas.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: operación medible. Revisa específicamente esta seguridad: PII/tokens redactados.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.5 — Dependency/secret scanning

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] scanner dependencias.

- [ ] secret scanning.

- [ ] CI.

- [ ] política actualización.


### Criterios de aceptación

- [ ] pipeline detecta riesgos.


### Seguridad

- [ ] no subir hallazgos con secrets reales.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.5 — Dependency/secret scanning. No inicies ninguna subfase posterior.

Alcance obligatorio: scanner dependencias; secret scanning; CI; política actualización.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: pipeline detecta riesgos. Revisa específicamente esta seguridad: no subir hallazgos con secrets reales.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.6 — Docker seguro

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] Dockerfile backend.

- [ ] frontend si existe.

- [ ] non-root.

- [ ] healthcheck.

- [ ] .dockerignore.

- [ ] una imagen común y siete configuraciones externas de despliegue.


### Criterios de aceptación

- [ ] imagen reproducible.


### Seguridad

- [ ] secrets no baked.

- [ ] perfiles/DB de sucursal no incluidos en la imagen común.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.6 — Docker seguro. No inicies ninguna subfase posterior.

Alcance obligatorio: Dockerfile backend; frontend si existe; non-root; healthcheck; .dockerignore.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: imagen reproducible. Revisa específicamente esta seguridad: secrets no baked.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.7 — Backup/restore y continuidad

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] backup DB.

- [ ] restore probado.

- [ ] RPO/RTO inicial.

- [ ] procedimiento.


### Criterios de aceptación

- [ ] restore verificado.


### Seguridad

- [ ] backups protegidos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.7 — Backup/restore y continuidad. No inicies ninguna subfase posterior.

Alcance obligatorio: backup DB; restore probado; RPO/RTO inicial; procedimiento.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: restore verificado. Revisa específicamente esta seguridad: backups protegidos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.8 — Cola/worker — decisión y adaptación

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] medir webhook.

- [ ] decidir si BackgroundTasks basta.

- [ ] si no Redis/worker.

- [ ] idempotencia.

- [ ] tests.


### Criterios de aceptación

- [ ] arquitectura adecuada al volumen.


### Seguridad

- [ ] no añadir infraestructura sin evidencia.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.8 — Cola/worker — decisión y adaptación. No inicies ninguna subfase posterior.

Alcance obligatorio: medir webhook; decidir si BackgroundTasks basta; si no Redis/worker; idempotencia; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.8 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: arquitectura adecuada al volumen. Revisa específicamente esta seguridad: no añadir infraestructura sin evidencia.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.9 — Checklist producción

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] privacy.

- [ ] WhatsApp policies vigentes.

- [ ] OpenAI data controls.

- [ ] DNS/HTTPS.

- [ ] budgets.

- [ ] incidentes.

- [ ] rollback.

- [ ] matriz de siete números, instancias, sucursales, DB y health checks sin registrar secretos.


### Criterios de aceptación

- [ ] go-live checklist firmado/documentado.


### Seguridad

- [ ] sin riesgos críticos abiertos.

- [ ] prueba negativa de acceso cruzado para las siete instalaciones.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.9 — Checklist producción. No inicies ninguna subfase posterior.

Alcance obligatorio: privacy; WhatsApp policies vigentes; OpenAI data controls; DNS/HTTPS; budgets; incidentes; rollback.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.9 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: go-live checklist firmado/documentado. Revisa específicamente esta seguridad: sin riesgos críticos abiertos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F10.10 — Despliegue y smoke tests

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] deploy.

- [ ] health.

- [ ] webhook.

- [ ] mensaje WhatsApp.

- [ ] panel.

- [ ] rollback check.

- [ ] smoke test independiente de cada uno de los siete números/asistentes.


### Criterios de aceptación

- [ ] MVP accesible de forma segura.

- [ ] cada número responde únicamente con datos de su sucursal.


### Seguridad

- [ ] no incluir secretos en evidencias.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F10.10 — Despliegue y smoke tests. No inicies ninguna subfase posterior.

Alcance obligatorio: deploy; health; webhook; mensaje WhatsApp; panel; rollback check.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F10.10 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: MVP accesible de forma segura. Revisa específicamente esta seguridad: no incluir secretos en evidencias.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 15. FASE 11 — Funciones comerciales avanzadas

**Objetivo:** Añadir capacidades opcionales una vez estable la atención básica.

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F11.1 — Plantillas y mensajes iniciados por negocio

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] revisar políticas vigentes.

- [ ] templates aprobados.

- [ ] consentimiento/categoría.

- [ ] servicio.

- [ ] tests.


### Criterios de aceptación

- [ ] envíos cumplen reglas vigentes.


### Seguridad

- [ ] no iniciar campañas sin autorización/política.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F11.1 — Plantillas y mensajes iniciados por negocio. No inicies ninguna subfase posterior.

Alcance obligatorio: revisar políticas vigentes; templates aprobados; consentimiento/categoría; servicio; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F11.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: envíos cumplen reglas vigentes. Revisa específicamente esta seguridad: no iniciar campañas sin autorización/política.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F11.2 — Pedidos

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] carrito/resumen.

- [ ] validación.

- [ ] confirmación explícita.

- [ ] persistencia.

- [ ] idempotencia.

- [ ] tests.


### Criterios de aceptación

- [ ] IA no confirma por sí sola.


### Seguridad

- [ ] precios revalidados, audit trail.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F11.2 — Pedidos. No inicies ninguna subfase posterior.

Alcance obligatorio: carrito/resumen; validación; confirmación explícita; persistencia; idempotencia; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F11.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: IA no confirma por sí sola. Revisa específicamente esta seguridad: precios revalidados, audit trail.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F11.3 — Inventario real

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] fuente POS/ERP.

- [ ] consulta.

- [ ] staleness.

- [ ] fallback.


### Criterios de aceptación

- [ ] existencia proviene de sistema real.


### Seguridad

- [ ] no inventar stock.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F11.3 — Inventario real. No inicies ninguna subfase posterior.

Alcance obligatorio: fuente POS/ERP; consulta; staleness; fallback.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F11.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: existencia proviene de sistema real. Revisa específicamente esta seguridad: no inventar stock.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F11.4 — POS/ERP

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] API adapter.

- [ ] auth.

- [ ] timeouts.

- [ ] retries.

- [ ] tests.


### Criterios de aceptación

- [ ] integración aislada.


### Seguridad

- [ ] mínimo privilegio.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F11.4 — POS/ERP. No inicies ninguna subfase posterior.

Alcance obligatorio: API adapter; auth; timeouts; retries; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F11.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: integración aislada. Revisa específicamente esta seguridad: mínimo privilegio.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F11.5 — Recomendaciones para carne asada

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] reglas cantidades.

- [ ] tools precios.

- [ ] presupuesto.

- [ ] tests.


### Criterios de aceptación

- [ ] recomendación usa datos reales.


### Seguridad

- [ ] distinguir estimación de hecho.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F11.5 — Recomendaciones para carne asada. No inicies ninguna subfase posterior.

Alcance obligatorio: reglas cantidades; tools precios; presupuesto; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F11.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: recomendación usa datos reales. Revisa específicamente esta seguridad: distinguir estimación de hecho.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F11.6 — Analytics

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] productos consultados.

- [ ] sucursales.

- [ ] unanswered.

- [ ] handoff.

- [ ] costos.


### Criterios de aceptación

- [ ] métricas útiles.


### Seguridad

- [ ] agregación/minimización.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F11.6 — Analytics. No inicies ninguna subfase posterior.

Alcance obligatorio: productos consultados; sucursales; unanswered; handoff; costos.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F11.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: métricas útiles. Revisa específicamente esta seguridad: agregación/minimización.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```

# 16. Matriz transversal de seguridad

| Control | Primera fase | Obligatorio antes de producción | Estado |
|---|---:|---:|---|
| `.env` ignorado | F1 | Sí | ✅ |
| OpenAI key backend-only | F1 | Sí | ✅ F1.5 |
| configuración con secretos protegidos | F1 | Sí | ✅ F1.2 |
| validación HTTP/Pydantic | F1 | Sí | ✅ F1.6 |
| input size limit | F1 | Sí | ✅ F1.6 |
| timeout OpenAI | F1 | Sí | ✅ F1.5 |
| errores seguros | F1 | Sí | ✅ F1.4 |
| logging sin secrets/PII | F1 | Sí | ✅ F1.4 |
| CORS allowlist | F1 | Sí cuando haya navegador | ✅ F1.4 |
| tests sin OpenAI real | F1 | Sí | ✅ F1.7 |
| tokens GreenAPI backend-only | F2 | Sí | ✅ F2.9 |
| autenticación Bearer del webhook antes del body | F2 | Sí | ✅ F2.9 |
| instancia del webhook validada | F2 | Sí | ✅ F2.9 |
| host GreenAPI HTTPS en allowlist | F2 | Sí | ✅ F2.9 |
| idempotencia de mensajes | F2/F7 | Sí | ⬜ |
| GreenAPI timeout/retries acotados | F2 | Sí | ✅ F2.9 |
| PII WhatsApp redactada en logs | F2 | Sí | ✅ F2.9 |
| token webhook fuerte y acotado | F2 | Sí | ✅ F2.10 |
| SQLAlchemy/queries parametrizadas | F3 | Sí | ✅ F3.1 |
| URL DB configurable/protegida | F3 | Sí | ✅ F3.1 |
| migraciones | F3 | Sí | ✅ F3.1 |
| identidad fija por instalación | F3 | Sí | ✅ F3.2 |
| carga de perfil limitada a sucursal | F3 | Sí | ✅ F3.2 |
| consultas DB con alcance de sucursal | F3/F6 | Sí | ✅ F3.5 |
| pruebas de acceso cruzado | F3/F6/F8 | Sí | ✅ F3.5 |
| Decimal para dinero | F3 | Sí | ✅ F3.4 |
| integridad/constraints | F3 | Sí | ⬜ |
| documentos tratados como no confiables | F4 | Sí | ⬜ |
| defensa prompt injection | F4/F6 | Sí | ⬜ |
| Excel validado | F5 | Sí | ⬜ |
| importación transaccional | F5 | Sí | ⬜ |
| tools allowlist/mínimo privilegio | F6 | Sí | ⬜ |
| prohibir SQL libre generado por IA | F6 | Sí | ⬜ |
| límite de iteraciones tool calling | F6 | Sí | ⬜ |
| idempotencia persistente | F7 | Sí | ⬜ |
| política de retención | F7 | Sí | ⬜ |
| autenticación admin | F8 | Sí | ⬜ |
| RBAC | F8 | Sí | ⬜ |
| password hashing adecuado | F8 | Sí | ⬜ |
| rate limit login | F8 | Sí | ⬜ |
| audit log precios | F8 | Sí | ⬜ |
| handoff AI/HUMAN exclusivo | F9 | Sí si se usa | ⬜ |
| HTTPS | F10 | Sí | ⬜ |
| rate limiting | F10 | Sí | ⬜ |
| secret manager | F10 | Sí | ⬜ |
| rotación de secretos | F10 | Sí | ⬜ |
| dependency scanning | F10 | Sí | ⬜ |
| secret scanning | F10 | Sí | ⬜ |
| backup + restore probado | F10 | Sí | ⬜ |
| observabilidad/costos | F10 | Sí | ⬜ |
| política/ventanas WhatsApp vigentes | F10/F11 | Sí | ⬜ |
| confirmación explícita de pedidos | F11 | Si se implementa | ⬜ |

---

# 17. Riesgos principales

## R-01 — Precio inventado
**Severidad:** crítica.  
**Mitigación:** DB + tool específica; nunca memoria del modelo.

## R-02 — API key/token expuesto
**Severidad:** crítica.  
**Mitigación:** backend-only, SecretStr, `.env`, secret manager, scanning y rotación.

## R-03 — Webhook falso
**Severidad:** crítica.  
**Mitigación:** autenticidad/firma del POST sobre raw body + validación de schema.

## R-04 — Mensaje duplicado
**Severidad:** alta.  
**Mitigación:** external message ID + idempotencia persistente.

## R-05 — Prompt injection
**Severidad:** alta.  
**Mitigación:** datos no confiables, tools allowlist, authz y mínimo privilegio.

## R-06 — Excel modifica precios incorrectamente
**Severidad:** alta.  
**Mitigación:** validación + preview + confirmación + transacción + audit log.

## R-07 — Panel comprometido
**Severidad:** crítica.  
**Mitigación:** auth, RBAC, sesiones seguras, HTTPS, rate limiting, audit.

## R-08 — Costo OpenAI/WhatsApp no controlado
**Severidad:** alta.  
**Mitigación:** límites, métricas, alertas, modelo configurable, presupuesto.

## R-09 — PII en logs
**Severidad:** alta.  
**Mitigación:** minimización/redacción; no raw webhook/chat por defecto.

## R-10 — Proveedor externo caído
**Severidad:** media/alta.  
**Mitigación:** timeout, retry acotado, errores claros, cola/worker si el volumen lo exige.

## R-11 — Fuga o mezcla de datos entre sucursales
**Severidad:** crítica.
**Mitigación:** una instalación/número por sucursal, `ASSISTANT_BRANCH_CODE` inmutable, perfil con
código coincidente, alcance inyectado por backend, DB SQLite separada durante el MVP y pruebas
negativas de acceso cruzado en repositorios, tools, panel y despliegue.

---

# 18. Checkpoint actual

**Fase activa:** ninguna; Fase 7 — Conversaciones WhatsApp + idempotencia persistente (`✅ COMPLETADO`).
**Subfase activa:** ninguna; F7.6 — Cierre Fase 7 (`✅ COMPLETADO`).
**Última subfase completada:** F7.6 — Cierre Fase 7.
**Siguiente subfase recomendada:** F8.1 — Autenticación backend, `⬜ PENDIENTE`;
Fase 8 no iniciada.
**WhatsApp:** instancia GreenAPI configurada y autorizada; webhook autenticado, ACK, OpenAI,
`sendMessage` y recepción final en WhatsApp confirmados de extremo a extremo.

**Arquitectura vigente:** siete instalaciones/números, una por sucursal, con código y prompt
comunes; cada instalación usa identidad, credenciales, DB y perfil propios.

F7.1 completada el 2026-09-24 tras crear el esquema mínimo de WhatsApp y validar la migración
desde cero y sobre revisiones previas. F7.2 completada el 2026-09-24 tras resolver la identidad
externa con HMAC y sucursal de configuración. F7.3 completada el 2026-09-24 con recibos
transaccionales por sucursal y protección ante carreras. F7.4 completada el 2026-09-24 con
purga, borrado individual y política técnica de privacidad; 557 pruebas de la suite completa.
F7.5 completada el 2026-09-24 con agregados FAQ sin texto, conteo atómico por sucursal,
consulta interna acotada y purga a 30 días; 564 pruebas de la suite completa.
F7.6 y Fase 7 cerradas el 2026-09-24 tras probar migraciones desde cero y desde la revisión
F7.1, restaurar un respaldo aislado y documentar el plan operativo; 566 pruebas de la suite completa.

---

# 19. Historial preservado del plan anterior
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

## 2026-08-25 — Configuración central

**Fase:** Fase 1
**Tarea:** F1.2 — Configuración central
**Estado:** ✅ COMPLETADO

Cambios:

- implementado `Settings` como punto único de configuración con carga desde entorno y `.env`;
- agregada validación de entorno, host, puerto, modelo, retención, timeout, límite de
  mensaje y nivel de log;
- configurada `OPENAI_API_KEY` como `SecretStr` obligatorio, excluido de representaciones y
  protegido mediante errores que ocultan valores de entrada;
- agregado `get_settings()` con caché por proceso, sin evaluar configuración al importar;
- agregadas dependencias acotadas de Pydantic y pydantic-settings;
- documentado el comportamiento de configuración y sus límites en README;
- revisada la documentación oficial de OpenAI para mantener la clave en una variable de
  entorno del servidor.

Archivos:

- `backend/app/core/config.py`
- `backend/tests/test_config.py`
- `pyproject.toml`
- `README.md`
- `plan_de_trabajo.md`

Validación:

- `.venv\\Scripts\\python.exe -m pip install -e ".[dev]"` -> instalación actualizada correcta;
- `.venv\\Scripts\\python.exe -m pytest` -> 12 pruebas aprobadas;
- `.venv\\Scripts\\ruff.exe check .` -> sin hallazgos;
- `.venv\\Scripts\\ruff.exe format --check .` -> 15 archivos con formato correcto;
- `.venv\\Scripts\\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios en los cambios.

Seguridad:

- `OPENAI_API_KEY` permanece vacía en `.env.example` y `.env` continúa ignorado;
- no se detectaron claves con forma real en el repositorio;
- representación, serialización y errores de validación comprobados sin revelar el secreto;
- configuración comprobada sin `print` ni logging directo;
- las pruebas usan un marcador aleatorio que no tiene formato de API key y no hacen llamadas
  externas.

Riesgos/Pendientes:

- la configuración de CORS se abordará en F1.4;
- la API key solo se exigirá cuando `get_settings()` sea solicitado; no existe integración con
  OpenAI ni verificación de credenciales en F1.2;
- el modelo configurado se validará operativamente durante la integración de OpenAI.

Siguiente:

- F1.3 — Aplicación FastAPI y health check, sin iniciar hasta recibir instrucción del usuario.

---
---

## 2026-08-25 — Reorientación del producto a WhatsApp

**Fase:** planificación transversal  
**Estado:** ✅ COMPLETADO

Cambios:

- WhatsApp Business Platform / Cloud API pasa a ser la interfaz principal del cliente.
- El panel web se reserva para administración y atención humana.
- Se preservan F1.1 y F1.2 como completadas.
- F1.3 sigue siendo la siguiente subfase.
- Fase 2 se redefine como integración WhatsApp.
- Se agregan subfases y prompts de Codex para todo el roadmap.
- Se agregan controles de webhook, firma, idempotencia, privacidad y tokens Meta.
- Se separa el endpoint interno `/api/v1/chat` del canal real del cliente.

Archivos documentales actualizados:

- `AGENTS.md`
- `plan_de_trabajo.md`
- `docs/fase_1_diseno.md`
- `docs/fase_2_whatsapp.md`

Código:

- no se modificó código de aplicación durante esta replanificación.

Siguiente:

- F1.3 — Aplicación FastAPI + health check.

---

## 2026-08-25 — Aplicación FastAPI + health check

**Fase:** Fase 1
**Tarea:** F1.3 — Aplicación FastAPI + health check
**Estado:** ✅ COMPLETADO

Cambios:

- creada la aplicación FastAPI en un módulo importable;
- creado y registrado un router independiente con `GET /health`;
- definida la respuesta mínima y estable `status`/`service`;
- agregada una prueba HTTP en proceso que rechaza acceso a configuración y resolución DNS;
- agregadas FastAPI como dependencia de ejecución y HTTPX como dependencia de pruebas;
- actualizados README, diseño de Fase 1 y checkpoint oficial.

Archivos:

- `backend/app/main.py`
- `backend/app/api/routes/health.py`
- `backend/tests/test_health.py`
- `pyproject.toml`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`

Validación:

- `.venv\\Scripts\\python.exe -m pip install -e ".[dev]"` -> instalación editable correcta;
- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_health.py -q` -> la primera ejecución
  detectó que el bloqueo global de sockets impedía el socket local del event loop; tras acotar
  la protección, 1 prueba aprobada;
- `.venv\\Scripts\\python.exe -m pytest` -> 12 pruebas aprobadas y 1 error de entorno por
  permisos en la carpeta temporal global de pytest;
- `.venv\\Scripts\\python.exe -m pytest --basetemp=.venv\\pytest-temp -o
  cache_dir=.venv\\pytest-cache` -> 13 pruebas aprobadas;
- `.venv\\Scripts\\ruff.exe check .` -> sin hallazgos;
- `.venv\\Scripts\\ruff.exe format --check .` -> 19 archivos con formato correcto;
- `.venv\\Scripts\\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> señaló espacios Markdown en cambios documentales preexistentes;
- `git diff --check -- README.md pyproject.toml` -> cambios propios rastreados sin errores de
  espacios.

Seguridad:

- `/health` devuelve únicamente `status` y un identificador estable del servicio;
- el endpoint no carga `Settings`, no necesita `OPENAI_API_KEY` y no llama a OpenAI;
- la prueba falla si el endpoint intenta leer configuración o resolver un host externo;
- no se exponen configuración, versiones, secretos ni errores internos en la respuesta.

Riesgos/Pendientes:

- la carpeta temporal global de pytest tiene permisos ajenos al código; la suite fue comprobada
  usando rutas ignoradas dentro de `.venv`;
- permanecen espacios Markdown en cambios documentales que ya existían al comenzar y se
  preservaron para no reescribir trabajo ajeno;
- logging, request ID, errores seguros y CORS siguen fuera de alcance hasta F1.4.

Siguiente:

- F1.4 — Errores, request ID, logging y CORS, sin iniciar hasta recibir instrucción del usuario.

---

## 2026-08-25 — Errores, request ID, logging y CORS

**Fase:** Fase 1
**Tarea:** F1.4 — Errores, request ID, logging y CORS
**Estado:** ✅ COMPLETADO

Cambios:

- agregada una jerarquía mínima de excepciones internas con mensajes públicos fijos;
- agregado mapeo HTTP estable para errores de aplicación y errores inesperados;
- agregado `X-Request-ID` validado, generado cuando falta y propagado en respuestas;
- agregado logging HTTP de metadatos mínimos con método, plantilla de endpoint, estado,
  duración, categoría y request ID;
- agregada configuración HTTP no sensible para iniciar FastAPI sin requerir credenciales de
  OpenAI;
- agregado CORS con allowlist configurable, default vacío y métodos/headers explícitos;
- agregadas pruebas de errores, logging, request ID, allowlist y preflight CORS;
- actualizados README, diseño de Fase 1, matriz de seguridad y checkpoint oficial.

Archivos:

- `backend/app/core/config.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/logging.py`
- `backend/app/api/errors.py`
- `backend/app/api/middleware.py`
- `backend/app/main.py`
- `backend/tests/test_config.py`
- `backend/tests/test_http_safety.py`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`

Validación:

- `.venv\\Scripts\\python.exe -m pytest backend\\tests\\test_config.py
  backend\\tests\\test_health.py backend\\tests\\test_http_safety.py
  --basetemp=.venv\\pytest-f14-target -o cache_dir=.venv\\pytest-cache-f14-target -q`
  -> 24 pruebas aprobadas;
- la primera revisión de Ruff detectó un orden de imports y una línea de formato; ambos se
  corrigieron mecánicamente y la repetición pasó;
- `.venv\\Scripts\\python.exe -m pytest --basetemp=.venv\\pytest-f14 -o
  cache_dir=.venv\\pytest-cache-f14` -> 25 pruebas aprobadas;
- `.venv\\Scripts\\ruff.exe check .` -> sin hallazgos;
- `.venv\\Scripts\\ruff.exe format --check .` -> 24 archivos con formato correcto;
- `.venv\\Scripts\\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios; solo avisos informativos LF/CRLF.

Seguridad:

- respuestas 500/503 comprobadas sin traceback, detalle interno, paths ni secretos;
- request IDs entrantes se aceptan solo con caracteres seguros y longitud acotada;
- logs comprobados sin body, query string, headers ni contenido de `Authorization`;
- CORS usa orígenes exactos y rechaza wildcard, paths, credenciales, queries y duplicados;
- el default CORS vacío evita habilitar acceso desde navegador por omisión;
- preflight y errores conservan request ID; errores para orígenes permitidos conservan CORS.

Riesgos/Pendientes:

- el logging todavía usa la infraestructura estándar del proceso; agregación y observabilidad
  productiva corresponden a fases posteriores;
- el request ID es correlación, no autenticación ni autorización;
- los orígenes reales del panel deberán configurarse explícitamente antes de desplegarlo;
- OpenAIService y sus errores de proveedor siguen fuera de alcance hasta F1.5.

Siguiente:

- F1.5 — OpenAIService con Responses API, sin iniciar hasta recibir instrucción del usuario.

---

## 2026-08-25 — OpenAIService con Responses API

**Fase:** Fase 1
**Tarea:** F1.5 — OpenAIService con Responses API
**Estado:** ✅ COMPLETADO

Cambios:

- agregado y acotado el SDK oficial `openai>=3.3,<3.4`; versión instalada y comprobada: 3.3.1;
- creado `OpenAIService` asincrónico, con cliente inyectable y sin dependencias desde rutas HTTP;
- implementada la llamada exclusiva a Responses API mediante `responses.create` y lectura de
  `output_text`;
- agregados prompt base versionado, modelo, timeout, reintentos acotados y `store` configurables;
- agregada jerarquía interna para timeout, rate limit, conexión, estado HTTP y respuesta vacía;
- agregadas pruebas completamente simuladas para parámetros, salida, errores y ausencia de red
  o logs con contenido privado;
- actualizados configuración, ejemplo de entorno, README, diseño y checkpoint oficial.

Archivos:

- `pyproject.toml`
- `.env.example`
- `backend/app/core/config.py`
- `backend/app/core/exceptions.py`
- `backend/app/prompts/base_system_prompt.txt`
- `backend/app/services/openai_service.py`
- `backend/tests/test_config.py`
- `backend/tests/test_openai_service.py`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`

Validación:

- `git status --short --branch` al inicio -> árbol limpio sobre `main` antes de los cambios;
- `.venv\Scripts\python.exe -m pip index versions openai` -> versión oficial disponible 3.3.1;
- `.venv\Scripts\python.exe -m pip install -e ".[dev]"` -> dependencia instalada en el entorno;
- revisión de OpenAI Docs -> confirmados `AsyncOpenAI`, `responses.create`, `output_text`,
  `instructions`, `input`, `model`, `store`, timeout y jerarquía de errores del SDK;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_config.py
  backend\tests\test_openai_service.py --basetemp=.venv\pytest-f15-target -o
  cache_dir=.venv\pytest-cache-f15-target -q` -> 29 pruebas aprobadas en la primera revisión;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f15 -o
  cache_dir=.venv\pytest-cache-f15` -> 38 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 26 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios; solo avisos informativos LF/CRLF;
- búsquedas con `rg` -> ninguna referencia a Assistants API y ninguna importación de OpenAI en
  rutas HTTP.

Seguridad:

- la API key permanece como `SecretStr`, se entrega solo al cliente backend y no aparece en la
  representación del servicio;
- el servicio usa únicamente Responses API; no se agregó Assistants API;
- `store` conserva el default `false` y solo cambia mediante configuración validada;
- timeout y reintentos están configurados y acotados;
- el servicio no emite logs con prompt, mensaje o respuesta; las pruebas usan marcadores y
  comprueban su ausencia;
- los errores del SDK se traducen a categorías internas sin URL, cuerpo, traceback ni detalle
  del proveedor;
- todas las pruebas usan clientes simulados y bloquean cualquier resolución de red.

Riesgos/Pendientes:

- no se hizo una llamada real con credenciales ni se consumieron créditos; esa comprobación
  explícita corresponde a F1.8;
- el servicio todavía no está conectado a una ruta HTTP; esa integración y la validación de
  longitud del mensaje corresponden a F1.6;
- el costo y la latencia reales dependen del modelo y deberán medirse en la prueba manual.

Siguiente:

- F1.6 — Endpoint interno POST /api/v1/chat, sin iniciar hasta recibir instrucción del usuario.

---

## 2026-08-25 — Endpoint interno POST /api/v1/chat

**Fase:** Fase 1
**Tarea:** F1.6 — Endpoint interno POST /api/v1/chat
**Estado:** ✅ COMPLETADO

Cambios:

- agregados los esquemas `ChatRequest` y `ChatResponse` con validación de tipo, vacío y límite;
- agregado `ChatService` como frontera de aplicación entre HTTP y el generador de respuestas;
- agregada composición diferida `ChatService -> OpenAIService` para no cargar credenciales al
  iniciar FastAPI ni al consultar `/health`;
- creado y registrado `POST /api/v1/chat` con metadatos explícitos de uso interno/desarrollo;
- agregado mapeo HTTP 422 estable que no devuelve el contenido rechazado por Pydantic;
- conservado el mapeo seguro HTTP 503 para fallos del proveedor;
- agregadas pruebas de éxito, vacío, espacios, exceso configurable, composición, error de
  proveedor, ausencia de red/logs de contenido e identificación OpenAPI;
- actualizados README, diseño de Fase 1, matriz de seguridad y checkpoint oficial.

Archivos:

- `backend/app/schemas/chat.py`
- `backend/app/services/chat_service.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/routes/chat.py`
- `backend/app/api/errors.py`
- `backend/app/core/exceptions.py`
- `backend/app/main.py`
- `backend/tests/test_chat.py`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`

Validación:

- `git status --short --branch` al inicio -> árbol limpio sobre `main` antes de los cambios;
- revisión de OpenAI Docs -> confirmada la frontera vigente `responses.create` usada por el
  servicio encapsulado de F1.5;
- primera ejecución dirigida de `pytest` -> 23 pruebas aprobadas;
- primera revisión de Ruff -> detectó únicamente una línea de 102 caracteres y formato en el
  test nuevo; se corrigió mecánicamente;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_chat.py
  backend\tests\test_http_safety.py backend\tests\test_openai_service.py
  --basetemp=.venv\pytest-f16-target-3 -o cache_dir=.venv\pytest-cache-f16-target-3 -q`
  -> 24 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f16 -o
  cache_dir=.venv\pytest-cache-f16` -> 45 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 31 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` y revisión de archivos nuevos -> sin errores de espacios; solo avisos
  informativos LF/CRLF;
- búsquedas con `rg` -> ruta y servicio de aplicación sin imports del SDK ni Assistants API;
  F1.7 permanece pendiente.

Seguridad:

- `CHAT_MAX_MESSAGE_CHARS` se aplica sobre el mensaje original antes de llamar al proveedor;
- mensajes vacíos, solo espacios o demasiado largos responden 422 y no invocan el generador;
- errores de validación usan respuesta pública fija sin eco del body rechazado;
- fallos del proveedor responden 503 sin detalle interno ni traceback;
- la ruta depende de `ChatService`, no del SDK, y la API key permanece en composición backend;
- los tests comprueban que mensaje y respuesta completos no aparecen en logs y bloquean la red
  en el flujo exitoso;
- OpenAPI y README identifican el endpoint como interno/de desarrollo y no como canal final.

Riesgos/Pendientes:

- la etiqueta interno/desarrollo no es autenticación; antes de producción el endpoint debe
  deshabilitarse, restringirse o protegerse;
- no se realizó una llamada real a OpenAI; corresponde explícitamente a F1.8;
- la revisión integral de mocks, casos inválidos y bloqueo de red de toda la suite corresponde
  a F1.7.

Siguiente:

- F1.7 — Suite de pruebas y calidad, sin iniciar hasta recibir instrucción del usuario.

---

## 2026-08-25 — Suite de pruebas y calidad

**Fase:** Fase 1
**Tarea:** F1.7 — Suite de pruebas y calidad
**Estado:** ✅ COMPLETADO

Cambios:

- agregada una fixture `autouse` que bloquea DNS y conexiones externas para toda la suite y
  conserva solo loopback para pruebas en proceso;
- agregadas pruebas de la propia barrera para DNS, conexión por IP y resolución loopback;
- sustituidos valores aleatorios con apariencia de credencial por placeholders explícitos y no
  sensibles;
- auditados los puntos de construcción de OpenAI: cliente inyectado o constructor reemplazado
  por un doble antes de usarse;
- ampliados los casos inválidos del chat con campo ausente, nulo, tipo incorrecto y longitud
  absoluta excesiva, sin eco del contenido ni llamada al proveedor;
- documentados los comandos de calidad y la política de red de los tests.

Archivos:

- `backend/tests/conftest.py`
- `backend/tests/test_network_guard.py`
- `backend/tests/test_chat.py`
- `backend/tests/test_config.py`
- `backend/tests/test_openai_service.py`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`

Validación:

- `git status --short --branch` al inicio -> árbol limpio sobre `main` antes de los cambios;
- revisión de OpenAI Docs -> confirmada la operación `responses.create` que la suite mantiene
  detrás de dobles del servicio;
- primera suite con bloqueo global -> 52 pruebas aprobadas;
- primera revisión de Ruff -> detectó dos ajustes mecánicos de imports; ambos se corrigieron;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f17-target-2 -o
  cache_dir=.venv\pytest-cache-f17-target-2 -q` -> 52 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f17 -o
  cache_dir=.venv\pytest-cache-f17` -> 52 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 33 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios; solo avisos informativos LF/CRLF;
- búsquedas con `rg` -> todos los usos de OpenAI en tests están inyectados/reemplazados, sin
  patrones de API key real; F1.8 permanece pendiente.

Seguridad:

- toda prueba falla si intenta resolver un host externo o conectar a una IP no loopback;
- el guard intercepta `getaddrinfo`, `connect`, `connect_ex` y `create_connection`;
- los clientes OpenAI son simulados y no existe consumo accidental de API o créditos;
- fixtures y archivos temporales contienen placeholders claros, nunca credenciales reales;
- payloads inválidos no se reflejan en respuestas y no alcanzan el proveedor;
- no se ejecutó ninguna prueba manual ni llamada real de F1.8.

Riesgos/Pendientes:

- el guard cubre networking Python a nivel socket y permite loopback; un futuro test que lance
  un binario externo o use networking nativo deberá aislarse adicionalmente;
- no hay un escáner especializado de secretos configurado todavía; la revisión de fixtures y
  patrones conocidos pasó;
- la comprobación real con una credencial local corresponde exclusivamente a F1.8.

Siguiente:

- F1.8 — Prueba manual real con OpenAI, sin iniciar hasta recibir instrucción del usuario.

---

## 2026-08-25 — Prueba manual real con OpenAI (bloqueada)

**Fase:** Fase 1
**Tarea:** F1.8 — Prueba manual real con OpenAI
**Estado:** ⛔ BLOQUEADO

Cambios:

- agregado Uvicorn 0.52.x como dependencia de desarrollo para iniciar el backend local;
- creado un probe manual que solo acepta `/api/v1/chat` en loopback y nunca imprime la clave,
  el mensaje enviado ni el texto de respuesta;
- agregadas pruebas del resumen seguro, forma de error y restricción de URL del probe;
- creado `.env` local ignorado con `OPENAI_API_KEY=` vacío para que la credencial sea agregada
  únicamente por el usuario en su equipo;
- agregados `AGENTS.md` y `plan_de_trabajo.md` a `.gitignore` según instrucción explícita;
- documentado el procedimiento local seguro en README.

Archivos:

- `.gitignore`
- `pyproject.toml`
- `scripts/__init__.py`
- `scripts/manual_chat_probe.py`
- `backend/tests/test_manual_chat_probe.py`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`
- `.env` local ignorado, no versionado y con la clave vacía

Validación:

- `git status --short --branch` al inicio -> árbol limpio sobre `main` antes de los cambios;
- comprobación local sin revelar valores -> `.env` y `OPENAI_API_KEY` no existían al iniciar;
- revisión de OpenAI Docs -> confirmada la operación vigente `responses.create` y su
  autenticación backend;
- `.venv\Scripts\python.exe -m pip index versions uvicorn` -> versión disponible 0.52.4;
- `.venv\Scripts\python.exe -m pip install -e ".[dev]"` -> Uvicorn 0.52.4 instalado;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_manual_chat_probe.py ... -q`
  -> 6 pruebas aprobadas;
- backend iniciado en `127.0.0.1:8765`; `GET /health` -> HTTP 200;
- probe con placeholder inválido y `--expect provider-error` -> proveedor respondió 401 y la
  aplicación devolvió HTTP 503, request ID presente y error público seguro; no se imprimió el
  cuerpo completo;
- servidor detenido inmediatamente después de la prueba de error;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f18 -o
  cache_dir=.venv\pytest-cache-f18` -> 58 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 34 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios; solo avisos informativos LF/CRLF;
- revisión del diff -> sin patrones de API key; `.env` confirmado como ignorado.

Seguridad:

- ninguna credencial real fue recibida, mostrada, copiada o almacenada en evidencia;
- `.env` está ignorado y no aparece en `git status`;
- la prueba inválida usó un placeholder sin privilegios, reintentos en cero y `store=false`;
- el probe muestra solo status, flags, request ID presente y longitud de respuesta;
- el error real de autenticación se mapeó a la forma pública estable sin traceback ni detalle;
- `AGENTS.md` y `plan_de_trabajo.md` tienen reglas de ignore, aunque siguen versionados por
  haber estado rastreados antes de agregarlas.

Bloqueo/Riesgos:

- falta una API key local válida; por eso no se comprobó HTTP 200 ni respuesta real del modelo;
- Git no aplica `.gitignore` retroactivamente: `AGENTS.md` y `plan_de_trabajo.md` continúan
  rastreados. No se ejecutó `git rm --cached` porque el plan es el checkpoint oficial y el
  usuario solo pidió agregar reglas de ignore;
- el endpoint interno sigue sin autenticación y no debe exponerse públicamente.

Siguiente:

- reanudar F1.8 después de colocar la clave únicamente en `.env`; no iniciar F1.9 todavía.

---

## 2026-08-25 — Reanudación de prueba manual real con OpenAI (bloqueada por proveedor)

**Fase:** Fase 1
**Tarea:** F1.8 — Prueba manual real con OpenAI
**Estado:** ⛔ BLOQUEADO

Cambios:

- reanudada F1.8 tras detectar una credencial presente únicamente en el `.env` local ignorado;
- validada la configuración sin leer, imprimir ni copiar el valor secreto;
- iniciado el backend exclusivamente en loopback y comprobado nuevamente `/health`;
- ejecutados dos intentos reales y seguros contra `/api/v1/chat` mediante Responses API;
- actualizado el procedimiento manual para indicar la revisión de cuota, facturación y límites
  cuando OpenAI responda HTTP 429;
- no se inició F1.9 ni ninguna tarea de Fase 2.

Archivos:

- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`
- `.env` local ignorado, no leído ni versionado

Validación:

- revisión de OpenAI Docs -> confirmados `responses.create`, `output_text`, `instructions`,
  `input` y `store` en la API/SDK vigentes;
- comprobación local reducida a booleanos -> `.env` existe, la clave está presente, `Settings`
  carga correctamente, `store=false` y timeout dentro del rango permitido;
- `git check-ignore -v .env` -> `.env` está cubierto por `.gitignore`;
- backend iniciado en `127.0.0.1:8765` sin access log;
- `GET /health` -> HTTP 200 y request ID presente;
- primer probe real de `/api/v1/chat` -> OpenAI respondió HTTP 429 y la aplicación devolvió
  HTTP 503 con JSON y request ID, sin texto de respuesta;
- segundo probe controlado con reintentos de aplicación desactivados -> OpenAI volvió a
  responder HTTP 429 y la aplicación conservó el error público HTTP 503;
- servidor detenido inmediatamente después de cada intento;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f18-resume -o
  cache_dir=.venv\pytest-cache-f18-resume` -> 58 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 34 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores de espacios; solo avisos informativos LF/CRLF.

Seguridad:

- la credencial nunca apareció en comandos, salida, plan, logs ni evidencia;
- `.env` permanece ignorado y ausente de `git status`;
- el probe no imprime mensaje, prompt, respuesta del modelo ni cuerpo completo de error;
- los logs observados contienen solo metadatos HTTP, request ID, estado y categoría segura;
- el 429 del proveedor se mapea a HTTP 503 sin traceback ni detalle interno;
- `store=false` conserva el valor conservador durante la prueba.

Bloqueo/Riesgos:

- no se obtuvo HTTP 200 ni texto real porque el proveedor respondió HTTP 429 en ambos intentos;
- se debe revisar en la cuenta/proyecto de OpenAI la cuota, facturación y límites antes de
  repetir; no se puede marcar el criterio de llamada real como cumplido;
- el endpoint interno sigue sin autenticación y no debe exponerse públicamente;
- `AGENTS.md` y `plan_de_trabajo.md` siguen rastreados aunque tengan reglas de ignore, porque
  `.gitignore` no actúa retroactivamente.

Siguiente:

- reanudar exclusivamente F1.8 cuando el proveedor permita la llamada; no iniciar F1.9.

---

## 2026-08-26 — Reanudación de F1.8 (bloqueada por credencial local ausente)

**Fase:** Fase 1
**Tarea:** F1.8 — Prueba manual real con OpenAI
**Estado:** ⛔ BLOQUEADO

Cambios:

- reconstruido el entorno virtual local ignorado e instaladas las dependencias declaradas;
- revisada la integración contra la referencia oficial vigente de Responses API;
- comprobada la configuración mediante indicadores booleanos, sin leer ni imprimir secretos;
- iniciado el backend únicamente en loopback y validado `/health`;
- no se llamó a `/api/v1/chat` porque no existe `.env` ni una credencial en el entorno;
- no se modificó código y no se inició F1.9 ni ninguna tarea de Fase 2.

Archivos:

- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`
- `.venv` local ignorado, recreado únicamente para validación

Validación:

- referencia oficial de OpenAI -> `POST /responses` conserva `input`, `instructions`, `store` y
  el campo auxiliar `output_text` recomendado por los SDK;
- comprobación local reducida a booleanos -> `.env` ausente, `OPENAI_API_KEY` ausente y
  `Settings` no puede cargar la configuración completa;
- `git check-ignore -v .env` -> `.env` continúa cubierto por `.gitignore`;
- backend iniciado en `127.0.0.1:8765` sin access log;
- `GET /health` -> HTTP 200 y request ID presente;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f18-final -o
  cache_dir=.venv\pytest-cache-f18-final -q` -> 58 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 34 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git ls-files .env .env.example` -> solo `.env.example` está versionado.

Seguridad:

- no se buscó, recuperó, creó, solicitó ni copió ninguna credencial;
- las comprobaciones reportaron únicamente presencia/ausencia y nunca valores de configuración;
- `.env` sigue ignorado y no aparece en `git status`;
- no se envió una llamada con credencial inventada ni se consumieron créditos;
- el servidor se limitó a loopback, sin access log, y se detuvo tras validar `/health`.

Bloqueo/Riesgos:

- falta una credencial local válida; por ello no se obtuvo HTTP 200 ni respuesta real y el
  criterio de aceptación pendiente no puede marcarse como cumplido;
- una credencial futura debe agregarse solo a `.env` o al entorno local del proceso, nunca al
  repositorio, comandos compartidos, logs o documentación;
- el endpoint interno sigue sin autenticación y no debe exponerse públicamente.

Siguiente:

- agregar una credencial válida únicamente en `.env` y reanudar exclusivamente F1.8; no iniciar
  F1.9.

---

## 2026-08-26 — Prueba manual real con OpenAI completada

**Fase:** Fase 1
**Tarea:** F1.8 — Prueba manual real con OpenAI
**Estado:** ✅ COMPLETADO

Cambios:

- detectada la credencial proporcionada en `.env.example` sin leer ni mostrar su valor;
- movida la configuración proporcionada a `.env`, archivo local ignorado, y restaurado
  `.env.example` exactamente a su versión segura rastreada;
- validada la configuración completa mediante indicadores booleanos;
- iniciado el backend exclusivamente en loopback sin access log y con reintentos desactivados;
- ejecutada una única llamada real a `/api/v1/chat` mediante Responses API;
- comprobada una respuesta HTTP 200, con request ID y texto no vacío, sin mostrar su contenido;
- no se modificó código y no se inició F1.9 ni ninguna tarea de Fase 2.

Archivos:

- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`
- `.env` local ignorado, no versionado
- `.env.example` restaurado, sin diferencias respecto de Git

Validación:

- referencia oficial vigente de OpenAI -> confirmados `POST /responses`, `input`,
  `instructions`, `store` y `output_text`;
- comprobación local reducida a booleanos -> `.env` existe, la credencial está presente,
  `Settings` carga, `store=false`, modelo configurado, timeout y reintentos dentro de rango;
- `git check-ignore -v .env` -> `.env` está cubierto por `.gitignore`;
- backend iniciado en `127.0.0.1:8765` sin access log y detenido tras la prueba;
- `GET /health` -> HTTP 200;
- `scripts/manual_chat_probe.py --expect success` -> HTTP 200, request ID presente, JSON válido
  y respuesta no vacía de 6 caracteres;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f18-success -o
  cache_dir=.venv\pytest-cache-f18-success -q` -> 58 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 34 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes.

Seguridad:

- la credencial nunca apareció en comandos, salidas, logs, documentación ni evidencia;
- `.env.example` no conserva la credencial y solo `.env.example` está rastreado por Git;
- el probe no imprimió el mensaje, prompt ni texto de respuesta del modelo;
- `store=false` se mantuvo y la aplicación realizó un solo intento, sin reintentos;
- servidor limitado a loopback, sin access log y detenido inmediatamente después del probe;
- la suite automatizada permaneció sin acceso a internet y usó dobles de OpenAI.

Riesgos/Pendientes:

- `/api/v1/chat` continúa siendo un endpoint interno sin autenticación y no debe exponerse
  públicamente;
- la disponibilidad, cuota y costo del proveedor siguen siendo dependencias externas;
- `.env` debe mantenerse local y nunca agregarse a Git.

Siguiente:

- F1.9 — Cierre Fase 1, sin iniciar hasta recibir instrucción explícita del usuario.

---

## 2026-08-26 — Cierre de Fase 1

**Fase:** Fase 1
**Tarea:** F1.9 — Cierre Fase 1
**Estado:** ✅ COMPLETADO

Cambios:

- revisado el Definition of Done de Fase 1 y los criterios de F1.1-F1.9;
- actualizado README para declarar Fase 1 completada y Fase 2 no iniciada;
- actualizado el diseño técnico con F1.9 y el cierre de Fase 1;
- agregadas pruebas de repositorio para mantener vacía la credencial de `.env.example` y
  conservar las reglas de ignore de `.env`;
- auditados código, pruebas, dependencias, documentación, secretos y checkpoint;
- no se modificó funcionalidad de aplicación ni se inició ninguna subfase de Fase 2.

Archivos:

- `backend/tests/test_repository_security.py`
- `README.md`
- `docs/fase_1_diseno.md`
- `plan_de_trabajo.md`

Validación:

- `.venv\Scripts\python.exe -m pytest backend\tests\test_repository_security.py
  --basetemp=.venv\pytest-f19-security -o cache_dir=.venv\pytest-cache-f19-security -q`
  -> 2 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f19-final -o
  cache_dir=.venv\pytest-cache-f19-final -q` -> 60 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 35 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- backend iniciado con Uvicorn en `127.0.0.1:8765` sin access log;
- `GET /health` -> HTTP 200, respuesta mínima correcta y request ID presente;
- `git diff --check` -> sin errores de espacios;
- auditoría normalizada de archivos rastreados -> cero asignaciones de secretos no vacías y
  cero patrones con apariencia de API key;
- `git ls-files .env .env.example` y `git check-ignore -v .env` -> solo `.env.example` está
  rastreado y `.env` permanece ignorado;
- revisión de código -> sin TODO/FIXME/HACK críticos y sin Assistants API;
- revisión de estados -> F1.1-F1.9 completas y las 11 entradas de Fase 2 pendientes.

Seguridad:

- `.env.example` conserva `OPENAI_API_KEY` vacío y la nueva prueba evita su regresión;
- `.env` local no está rastreado ni apareció en el diff;
- la suite bloqueó conexiones externas y utilizó dobles de OpenAI;
- no se ejecutó una nueva llamada real ni se consumieron créditos durante F1.9;
- no se imprimieron credenciales, prompts, mensajes ni respuestas;
- Fase 2 y todas sus subfases permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- `/api/v1/chat` es interno, no tiene autenticación y no debe exponerse públicamente;
- no hay todavía un escáner especializado de secretos; existen prueba determinística y auditoría
  por patrones, pero conviene incorporar secret scanning en la fase de hardening;
- disponibilidad, cuota y costo de OpenAI siguen siendo dependencias externas;
- `.env` debe mantenerse local y fuera de Git.

Siguiente:

- ninguna fase iniciada; Fase 2 solo puede comenzar mediante instrucción explícita del usuario.

---

## 2026-08-26 — Configuración Meta/WhatsApp

**Fase:** Fase 2
**Tarea:** F2.1 — Configuración Meta/WhatsApp
**Estado:** ✅ COMPLETADO

Cambios:

- agregadas a `Settings` las variables de access token, phone-number ID, verify token, app
  secret, versión Graph API y timeout de WhatsApp;
- protegidos `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN` y `META_APP_SECRET` mediante
  `SecretStr`, campos sin representación y validación segura;
- mantenidos los secretos opcionales hasta habilitar los adaptadores posteriores para preservar
  el funcionamiento independiente del chat interno de Fase 1;
- validado `WHATSAPP_PHONE_NUMBER_ID` como identificador numérico cuando está configurado;
- centralizado el default de Graph API en `Settings` con formato configurable `vN.0`;
- fijado `v26.0` como default tras verificar el changelog oficial vigente de Meta;
- acotado `WHATSAPP_REQUEST_TIMEOUT_SECONDS` a valores mayores que 0 y hasta 120 segundos, con
  default de 15;
- ampliado `.env.example` únicamente con nombres vacíos/no sensibles;
- actualizados README, diseño de Fase 2, pruebas y checkpoint;
- no se implementó ni inició F2.2, webhook, firma o cliente Graph API.

Archivos:

- `backend/app/core/config.py`
- `backend/tests/test_config.py`
- `backend/tests/test_repository_security.py`
- `.env.example`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- changelog oficial de Meta recuperado desde `developers.facebook.com` -> HTTP 200; `v26.0`
  declarada como versión más reciente e introducida el 2026-07-29;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_config.py
  backend\tests\test_repository_security.py --basetemp=.venv\pytest-f21-target-2 -o
  cache_dir=.venv\pytest-cache-f21-target-2 -q` -> 35 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f21 -o
  cache_dir=.venv\pytest-cache-f21 -q` -> 74 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 35 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- auditoría normalizada -> cero secretos no vacíos y cero patrones de token en archivos
  rastreados;
- búsqueda de versiones en `backend/app` -> solo `backend/app/core/config.py` contiene una
  versión Graph API;
- `git ls-files .env .env.example` y `git check-ignore -v .env` -> `.env` permanece ignorado y
  solo `.env.example` está rastreado;
- revisión de estados -> F2.1 completada; F2.2-F2.10 permanecen pendientes.

Seguridad:

- secretos Meta/WhatsApp usan `SecretStr`, no aparecen en `repr`, serialización ni errores de
  validación;
- `.env.example` contiene campos sensibles vacíos y la prueba de repositorio lo exige;
- phone-number ID, versión y timeout rechazan valores con formato o límites inseguros;
- no se modificó ni mostró el contenido del `.env` local;
- no se realizaron llamadas a Meta ni se usaron credenciales reales;
- la versión Graph API no está hardcodeada en rutas o servicios;
- F2.2 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- los adaptadores futuros deben rechazar configuración ausente antes de usar cada secreto;
- `v26.0` depende del ciclo externo de Meta y debe revisarse antes de pruebas reales/despliegue;
- todavía no existen handshake, autenticación POST, parser, idempotencia ni cliente saliente.

Siguiente:

- F2.2 — Handshake GET del webhook, sin iniciar hasta recibir instrucción explícita del usuario.

---

## 2026-08-26 — Handshake GET del webhook

**Fase:** Fase 2
**Tarea:** F2.2 — Handshake GET del webhook
**Estado:** ✅ COMPLETADO

Cambios:

- agregada la ruta `GET /api/v1/whatsapp/webhook` y registrada en la aplicación FastAPI;
- validadas instancias únicas de `hub.mode`, `hub.verify_token` y `hub.challenge`;
- exigido `hub.mode=subscribe` y challenge decimal de hasta 20 dígitos conforme al contrato de
  verificación documentado por Meta;
- comparado el verify token configurado mediante `hmac.compare_digest` sin reflejarlo ni
  registrarlo;
- devuelto únicamente el challenge como texto plano para solicitudes válidas;
- rechazados mode, token, challenge, parámetros ausentes o duplicados con HTTP 403 sin cuerpo;
- aplicada respuesta cerrada HTTP 503 sin cuerpo cuando `WHATSAPP_VERIFY_TOKEN` no está
  configurado;
- agregadas pruebas HTTP sin red para casos válidos, inválidos y controles de logs;
- actualizados README, diseño de Fase 2 y checkpoint;
- no se implementó ni inició F2.3 ni ningún método POST.

Archivos:

- `backend/app/api/routes/whatsapp.py`
- `backend/app/main.py`
- `backend/tests/test_whatsapp_webhook.py`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- documentación oficial de Webhooks de Meta recuperada desde `developers.facebook.com` -> HTTP
  200; confirmó `hub.mode=subscribe`, verify token y devolución del challenge entero;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_whatsapp_webhook.py
  --basetemp=.venv\pytest-f22-target-2 -o cache_dir=.venv\pytest-cache-f22-target-2 -q` -> 7
  pruebas aprobadas sin acceso externo;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f22 -o
  cache_dir=.venv\pytest-cache-f22 -q` -> 81 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 37 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado, `.env.example`
  sin secretos y cero valores sensibles versionados;
- auditoría de superficie -> una única ruta GET de WhatsApp; ninguna ruta POST añadida;
- revisión de estados -> F2.2 completada; F2.3-F2.10 permanecen pendientes.

Seguridad:

- el verify token permanece como `SecretStr` en configuración y solo se revela localmente para
  la comparación segura;
- ni el token recibido ni el configurado se incluyen en respuestas, logs o excepciones;
- el middleware registra la plantilla del endpoint, no el query string;
- respuestas válidas contienen solo el challenge; rechazos y configuración ausente no contienen
  cuerpo;
- parámetros ausentes o duplicados fallan de forma cerrada;
- no se realizaron llamadas a Meta ni se usaron credenciales reales;
- F2.3 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- la prueba verifica el endpoint dentro de la aplicación; una verificación real de Meta requiere
  HTTPS público y configuración local válida;
- el método POST, su firma, el raw body y el procesamiento de eventos todavía no existen;
- el verify token debe mantenerse únicamente en el entorno backend y fuera de logs y Git.

Siguiente:

- F2.3 — Validación de firma del webhook POST, sin iniciar hasta recibir instrucción explícita
  del usuario.

---

## 2026-08-26 — Validación de firma del webhook POST

**Fase:** Fase 2
**Tarea:** F2.3 — Validación de firma del webhook POST
**Estado:** ✅ COMPLETADO

Cambios:

- agregada la ruta `POST /api/v1/whatsapp/webhook` sobre el path existente;
- leído el body crudo mediante `Request.body()` antes de cualquier acceso a JSON;
- validado exactamente un header `X-Hub-Signature-256` con prefijo `sha256=` y digest de 64
  caracteres hexadecimales;
- calculado HMAC-SHA256 sobre los bytes exactos recibidos usando `META_APP_SECRET`;
- comparados los digests mediante `hmac.compare_digest`;
- aceptadas firmas válidas con ACK HTTP 200 sin cuerpo;
- rechazadas firmas ausentes, duplicadas, malformadas, incorrectas o correspondientes a otros
  bytes mediante HTTP 403 sin cuerpo;
- aplicada respuesta cerrada HTTP 503 sin cuerpo cuando `META_APP_SECRET` no está configurado;
- agregadas pruebas de bytes crudos, firmas válidas/inválidas, orden previo a JSON y ausencia de
  body, firma y secreto en logs;
- actualizados README, diseño de Fase 2 y checkpoint;
- no se implementó ni inició F2.4, parsing, schema o normalización de eventos.

Archivos:

- `backend/app/api/routes/whatsapp.py`
- `backend/tests/test_whatsapp_webhook.py`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- documentación oficial de Webhooks de Meta recuperada desde `developers.facebook.com` -> HTTP
  200; confirmó SHA-256, header `X-Hub-Signature-256`, prefijo `sha256=` y uso del App Secret;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_whatsapp_webhook.py
  --basetemp=.venv\pytest-f23-target-2 -o cache_dir=.venv\pytest-cache-f23-target-2 -q` -> 17
  pruebas aprobadas sin acceso externo;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f23 -o
  cache_dir=.venv\pytest-cache-f23 -q` -> 91 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 37 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado, `.env.example`
  sin secretos y cero valores sensibles versionados;
- auditoría de superficie -> POST usa `request.body()` y no usa `request.json()`;
- revisión de estados -> F2.3 completada; F2.4-F2.10 permanecen pendientes.

Seguridad:

- `META_APP_SECRET` permanece como `SecretStr` y solo se revela localmente para calcular HMAC;
- la firma cubre el body crudo exacto, incluidos espacios y representación de bytes;
- una prueba instrumentada confirma que un payload no autenticado se rechaza antes de acceder a
  JSON;
- secreto, body y firma no se incluyen en respuestas, logs o excepciones;
- parámetros de firma ausentes, duplicados o malformados fallan de forma cerrada;
- no se realizaron llamadas a Meta ni se usaron credenciales reales;
- F2.4 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- un payload autenticado solo recibe ACK; el schema, parsing y tipos soportados comienzan en F2.4;
- la ruta almacena el body completo en memoria; debe definirse un límite compatible con Meta antes
  de producción;
- no existe todavía idempotencia ni protección contra replays de eventos válidamente firmados;
- una prueba real contra Meta requiere HTTPS público y configuración local válida.

Siguiente:

- F2.4 — Parser y normalización de eventos, sin iniciar hasta recibir instrucción explícita del
  usuario.

---

## 2026-08-26 — Parser y normalización de eventos

**Fase:** Fase 2
**Tarea:** F2.4 — Parser y normalización de eventos
**Estado:** ✅ COMPLETADO

Cambios:

- agregados modelos Pydantic tolerantes a campos extra para el envelope, entries, changes,
  values, mensajes y contenido de texto de Meta;
- agregado el modelo interno inmutable `InboundMessage` con provider, message id, sender, tipo,
  texto y timestamp;
- implementado `WhatsAppWebhookService` para validar y normalizar payloads ya autenticados;
- procesados únicamente `object=whatsapp_business_account`, `field=messages`,
  `messaging_product=whatsapp` y mensajes `type=text`;
- extraídos `id`, `from`, `text.body` y timestamp, con normalización de espacios;
- ignorados webhooks de estado, objetos/cambios ajenos y tipos no soportados;
- aplicados `CHAT_MAX_MESSAGE_CHARS` y un máximo estructural absoluto de 10000 caracteres;
- acotadas colecciones del payload a 1000 elementos por nivel;
- convertidos JSON malformado y estructuras inesperadas en cero mensajes sin romper la ruta;
- conectado el parser después de la validación HMAC, conservando ACK HTTP 200;
- agregadas pruebas de normalización, status, eventos irrelevantes, tipos no soportados, límites,
  payloads raros y ausencia del raw body en logs;
- actualizados README, diseño de Fase 2 y checkpoint;
- no se implementó ni inició F2.5, Graph API, envío u orquestación.

Archivos:

- `backend/app/schemas/whatsapp.py`
- `backend/app/services/whatsapp_webhook_service.py`
- `backend/app/api/routes/whatsapp.py`
- `backend/tests/test_whatsapp_webhook_service.py`
- `backend/tests/test_whatsapp_webhook.py`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- ejemplos oficiales de payloads de WhatsApp recuperados desde `developers.facebook.com` -> HTTP
  200; confirmaron `messages`, `statuses`, `from`, `id`, `timestamp`, `type` y `text.body`;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_whatsapp_webhook_service.py
  backend\tests\test_whatsapp_webhook.py --basetemp=.venv\pytest-f24-target -o
  cache_dir=.venv\pytest-cache-f24-target -q` -> 46 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f24 -o
  cache_dir=.venv\pytest-cache-f24 -q` -> 120 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 40 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado y `.env.example`
  sin secretos;
- auditoría de orden -> firma HMAC validada antes de invocar el parser;
- revisión de estados -> F2.4 completada; F2.5-F2.10 permanecen pendientes.

Seguridad:

- el parser solo recibe el body después de una firma válida;
- no se añadió acceso a `Request.json()` antes de la autenticación;
- el texto se limita con configuración y con un techo estructural absoluto;
- colecciones de Meta tienen límites para evitar procesamiento ilimitado;
- raw body, texto y sender no se registran ni se reflejan en respuestas;
- payloads desconocidos se tratan como input no confiable y producen cero mensajes;
- no se realizaron llamadas a Meta ni se usaron credenciales reales;
- F2.5 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- la ruta normaliza pero todavía descarta el resultado; la orquestación comienza en F2.6;
- el body completo continúa almacenándose en memoria antes del parser y requiere un límite HTTP
  compatible con Meta antes de producción;
- un payload autenticado pero inválido recibe ACK 200; deberá existir observabilidad por categoría
  sin contenido sensible para detectar cambios de schema;
- todavía no existen envío saliente, idempotencia ni protección contra replays.

Siguiente:

- F2.5 — WhatsAppClient para mensajes salientes, sin iniciar hasta recibir instrucción explícita
  del usuario.

---

## 2026-08-26 — WhatsAppClient para mensajes salientes

**Fase:** Fase 2
**Tarea:** F2.5 — WhatsAppClient para mensajes salientes
**Estado:** ✅ COMPLETADO

Cambios:

- implementado `WhatsAppClient` asíncrono con `send_text` y cliente HTTP inyectable;
- fijada la base `https://graph.facebook.com` y construido el endpoint con versión y phone-number
  ID validados desde `Settings`;
- enviado `WHATSAPP_ACCESS_TOKEN` únicamente mediante `Authorization: Bearer`;
- construido el payload oficial para producto WhatsApp, destinatario individual y texto;
- validados destinatarios internacionales y texto no vacío de hasta 4096 caracteres;
- aplicado `WHATSAPP_REQUEST_TIMEOUT_SECONDS` en cada request;
- deshabilitados redirects y reintentos automáticos para no reenviar tokens ni duplicar envíos
  ante resultados ambiguos;
- validada la respuesta exitosa de Meta y devuelto su message ID;
- mapeados timeout, conexión, rate limit, estados HTTP y respuesta inválida a excepciones internas
  sin encadenar detalles del proveedor;
- soportados `aclose()` y context manager asíncrono para el cliente HTTP propio;
- movido `httpx>=0.28,<0.29` de extra de desarrollo a dependencia de ejecución;
- agregadas pruebas con `httpx.MockTransport`, sin red ni credenciales reales;
- actualizados README, diseño de Fase 2 y checkpoint;
- no se implementó ni inició F2.6 ni la conexión webhook -> chatbot -> WhatsApp.

Archivos:

- `backend/app/services/whatsapp_client.py`
- `backend/app/core/exceptions.py`
- `backend/app/schemas/whatsapp.py`
- `backend/tests/test_whatsapp_client.py`
- `pyproject.toml`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- documentación oficial de mensajes de texto de WhatsApp recuperada desde
  `developers.facebook.com` -> HTTP 200; confirmó endpoint versionado, phone-number ID,
  `Authorization: Bearer` y payload de texto;
- `.venv\Scripts\python.exe -m pip install -e ".[dev]"` -> editable reinstalado; `httpx 0.28.1`
  satisface la dependencia de ejecución;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_whatsapp_client.py
  --basetemp=.venv\pytest-f25-target-3 -o cache_dir=.venv\pytest-cache-f25-target-3 -q` -> 23
  pruebas aprobadas sin acceso externo;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f25 -o
  cache_dir=.venv\pytest-cache-f25 -q` -> 143 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 42 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores;
- metadata del paquete -> `httpx` declarada entre las dependencias requeridas;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado y `.env.example`
  sin secretos;
- revisión de estados -> F2.5 completada; F2.6-F2.10 permanecen pendientes.

Seguridad:

- el token permanece backend-only, no aparece en URL, body, logs o excepciones;
- la URL no acepta base controlada por usuario y usa solo configuración validada;
- destinatario y texto se validan antes de cualquier request;
- redirects están deshabilitados incluso con un cliente inyectado;
- no se realizan reintentos automáticos tras fallos ambiguos;
- cuerpos y detalles de error de Graph API no se incorporan a excepciones internas;
- todas las pruebas HTTP usan `MockTransport` y la barrera global de red;
- F2.6 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- el cliente todavía no está conectado al webhook o al chatbot; comienza en F2.6;
- idempotencia y estrategia ante timeouts ambiguos comienzan en F2.7;
- `send_text` solo debe usarse dentro de la ventana/reglas vigentes de servicio; mensajes iniciados
  por negocio requieren plantillas y validación posterior;
- no se realizó una llamada real a Meta; corresponde a F2.9;
- el caller debe cerrar clientes propios mediante context manager o `aclose()`.

Siguiente:

- F2.6 — Orquestación WhatsApp -> chatbot -> WhatsApp, sin iniciar hasta recibir instrucción
  explícita del usuario.

---

## 2026-08-27 — Orquestación WhatsApp -> chatbot -> WhatsApp

**Fase:** Fase 2
**Tarea:** F2.6 — Orquestación WhatsApp -> chatbot -> WhatsApp
**Estado:** ✅ COMPLETADO

Cambios:

- agregado `MessageOrchestrator` como frontera de aplicación entre `InboundMessage`, el servicio
  de chat y el cliente saliente de WhatsApp;
- definida la composición perezosa de `ChatService` y `WhatsAppClient`, con cierre seguro del
  cliente HTTP al terminar el procesamiento;
- conectado el webhook autenticado y normalizado al orquestador sin introducir lógica directa de
  OpenAI o Graph API en la ruta;
- procesados secuencialmente los mensajes de texto soportados y enviado cada resultado al mismo
  `sender_id` validado;
- mapeados los fallos conocidos del chat o del envío a `MessageProcessingError`, con respuesta
  HTTP 503 estable y sin detalles privados o del proveedor;
- agregadas pruebas unitarias y de integración HTTP completamente mockeadas para el recorrido
  inbound -> chatbot -> outbound y sus errores;
- actualizados README, diseño de Fase 2 y checkpoint;
- no se implementó ni inició F2.7, idempotencia, procesamiento en background o reintentos.

Archivos:

- `backend/app/services/message_orchestrator.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/routes/whatsapp.py`
- `backend/app/core/exceptions.py`
- `backend/tests/test_message_orchestrator.py`
- `backend/tests/test_whatsapp_webhook.py`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- `.venv\Scripts\python.exe -m pytest backend\tests\test_message_orchestrator.py
  backend\tests\test_whatsapp_webhook.py --basetemp=.venv\pytest-f26-resume-target -o
  cache_dir=.venv\pytest-cache-f26-resume-target -q` -> 28 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f26-resume -o
  cache_dir=.venv\pytest-cache-f26-resume -q` -> 150 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 44 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado y `.env.example`
  sin secretos;
- auditoría de capas -> la ruta de WhatsApp no importa ni invoca OpenAI, `answer` o `send_text`;
- revisión de estados -> F2.6 completada; F2.7-F2.10 permanecen pendientes.

Seguridad:

- la firma HMAC y el parsing seguro permanecen antes de la construcción de adaptadores;
- solicitudes no autenticadas no construyen clientes de OpenAI o WhatsApp;
- texto, respuesta, sender y detalles internos no aparecen en la respuesta HTTP, excepciones ni
  logs probados;
- el access token continúa encapsulado en `WhatsAppClient` y no se mueve a la ruta o al
  orquestador;
- no se realizaron llamadas reales a OpenAI o Meta ni se usaron credenciales reales;
- F2.7 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- F2.6 procesa dentro de la solicitud HTTP; el ACK rápido se separará en F2.8;
- todavía no existe idempotencia, por lo que Meta podría provocar respuestas duplicadas al
  reenviar un mismo message ID; corresponde a F2.7;
- los lotes se procesan secuencialmente y un fallo detiene los mensajes restantes;
- no se realizó una prueba real con Meta; corresponde a F2.9.

Siguiente:

- F2.7 — Idempotencia mínima, sin iniciar hasta recibir instrucción explícita del usuario.

---

## 2026-08-27 — Idempotencia mínima

**Fase:** Fase 2
**Tarea:** F2.7 — Idempotencia mínima
**Estado:** ✅ COMPLETADO

Cambios:

- definida la interfaz asíncrona `IdempotencyStore` con operaciones para reclamar, completar y
  liberar IDs de mensajes;
- implementado `InMemoryIdempotencyStore` como almacén MVP temporal, atómico dentro del proceso y
  acotado a 10000 entradas;
- aplicado desalojo del ID completado más antiguo al alcanzar el límite, sin expulsar mensajes en
  curso y con fallo seguro si toda la capacidad está activa;
- integrada una instancia compartida por proceso en la composición de dependencias;
- actualizado `MessageOrchestrator` para reclamar `provider:external_message_id` antes del chat,
  ignorar duplicados y marcar el ID únicamente después del envío exitoso;
- liberada la reserva tras fallos para permitir un reintento posterior;
- agregadas pruebas de concurrencia, duplicados completados, liberación, límite, desalojo y flujo
  HTTP repetido con chatbot y WhatsApp mockeados;
- documentados el límite de memoria, pérdida al reiniciar, aislamiento por proceso/instancia,
  desalojo de IDs antiguos y obligación de persistencia antes de producción;
- no se implementó ni inició F2.8, background processing, colas o persistencia.

Archivos:

- `backend/app/services/idempotency_store.py`
- `backend/app/services/message_orchestrator.py`
- `backend/app/api/dependencies.py`
- `backend/app/core/exceptions.py`
- `backend/tests/test_idempotency_store.py`
- `backend/tests/test_message_orchestrator.py`
- `backend/tests/test_whatsapp_webhook.py`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- primera ejecución dirigida -> 37 pruebas aprobadas y 1 fallida por una expectativa incorrecta
  del test de desalojo; el caso se corrigió para no intentar expulsar entradas activas;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_idempotency_store.py
  backend\tests\test_message_orchestrator.py backend\tests\test_whatsapp_webhook.py
  --basetemp=.venv\pytest-f27-target-2 -o cache_dir=.venv\pytest-cache-f27-target-2 -q` -> 39
  pruebas aprobadas sin acceso externo;
- validación dirigida de Ruff -> 6 archivos sin hallazgos y con formato correcto;
- primera validación completa de formato -> detectó finales de línea inconsistentes en
  `backend/app/core/exceptions.py`; corregidos con Ruff;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f27-final -o
  cache_dir=.venv\pytest-cache-f27-final -q` -> 161 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 46 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado y `.env.example`
  sin secretos;
- auditoría de alcance -> no se añadieron `BackgroundTasks`, colas, Redis, SQLAlchemy ni trabajo
  correspondiente a F2.8 o fases posteriores;
- revisión de estados -> F2.7 completada; F2.8-F2.10 permanecen pendientes.

Seguridad:

- la reclamación atómica evita dos respuestas para el mismo ID mientras la entrada permanece en
  el almacén local;
- se conservan únicamente IDs con namespace de proveedor; no se almacenan texto, respuesta,
  remitente, token o body del webhook;
- la capacidad está acotada y el almacén nunca expulsa trabajo en curso;
- una reserva fallida se libera y los errores del almacén se mapean a respuestas seguras;
- todas las pruebas usan dobles locales y la barrera de red; no hubo llamadas reales a OpenAI o
  Meta ni uso de credenciales reales;
- la implementación está marcada como no apta para múltiples procesos/instancias y la
  persistencia compartida es obligatoria antes de producción;
- F2.8 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- el estado se pierde en cada reinicio y no se comparte entre procesos o instancias;
- al superar 10000 entradas, un ID completado antiguo puede desalojarse y volver a aceptarse;
- existe una ventana de duplicación si el proceso termina después de enviar a Meta pero antes de
  marcar el ID como completado;
- la idempotencia persistente y coordinada se implementará antes de producción en la fase de
  persistencia correspondiente;
- el procesamiento sigue bloqueando el ACK; su separación corresponde a F2.8.

Siguiente:

- F2.8 — ACK rápido y separación de procesamiento, sin iniciar hasta recibir instrucción
  explícita del usuario.

---

## 2026-08-27 — ACK rápido y separación de procesamiento

**Fase:** Fase 2
**Tarea:** F2.8 — ACK rápido y separación de procesamiento
**Estado:** ✅ COMPLETADO

Cambios:

- separada la autenticación/parsing del webhook respecto del chatbot y el envío por Graph API;
- programada una única tarea `BackgroundTasks` de FastAPI por lote autenticado, después de
  preparar el ACK HTTP 200;
- agregado `WhatsAppBackgroundProcessor` para construir/cerrar los adaptadores dentro del trabajo
  diferido y procesar el lote secuencialmente;
- capturados los fallos por mensaje para continuar con los mensajes restantes sin reintentos;
- capturados los fallos de construcción/cierre del lote y registradas las cancelaciones antes de
  propagarlas;
- limitados los logs de background a request ID, categoría segura y conteos, sin PII o contenido;
- mantenida la ruta libre de llamadas directas a OpenAI y Graph API;
- agregadas pruebas del ACK previo a la ejecución, procesamiento exitoso, fallo por mensaje,
  fallo de factory, cancelación observable, ausencia de reintentos y no filtración de datos;
- documentado que el mecanismo es local/no durable y que requiere evaluar cola/worker antes de
  producción;
- no se implementó ni inició F2.9 ni se realizaron pruebas reales con Meta.

Archivos:

- `backend/app/services/whatsapp_background_processor.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/routes/whatsapp.py`
- `backend/app/core/logging.py`
- `backend/tests/test_whatsapp_background_processor.py`
- `backend/tests/test_whatsapp_webhook.py`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- documentación oficial vigente de FastAPI y Starlette revisada -> `BackgroundTasks` se ejecuta
  después de enviar la respuesta y las excepciones posteriores no pueden reemplazar el ACK;
- colección oficial de Meta para WhatsApp Business Platform revisada -> webhook HTTPS como canal
  de notificaciones preservado sin modificar firma o schema;
- `.venv\Scripts\python.exe -m pytest backend\tests\test_whatsapp_background_processor.py
  backend\tests\test_whatsapp_webhook.py backend\tests\test_message_orchestrator.py
  backend\tests\test_idempotency_store.py --basetemp=.venv\pytest-f28-target-1 -o
  cache_dir=.venv\pytest-cache-f28-target-1 -q` -> 43 pruebas aprobadas sin acceso externo;
- validación dirigida de Ruff -> lint aprobado; formato detectó dos archivos y se corrigieron con
  Ruff antes de la validación completa;
- `.venv\Scripts\python.exe -m pytest --basetemp=.venv\pytest-f28 -o
  cache_dir=.venv\pytest-cache-f28 -q` -> 165 pruebas aprobadas sin acceso externo;
- `.venv\Scripts\ruff.exe check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check --no-cache .` -> 48 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores;
- prueba de seguridad del repositorio incluida en la suite -> `.env` ignorado y `.env.example`
  sin secretos;
- auditoría de alcance -> ningún `asyncio.create_task`, retry loop, cola o worker en código de
  aplicación; F2.9-F2.10 permanecen pendientes.

Seguridad:

- raw body, firma y parsing siguen ocurriendo antes de programar cualquier trabajo;
- solicitudes no autenticadas no ejecutan ni programan llamadas a proveedores;
- cada lote usa una tarea adjunta a la respuesta, no una tarea deliberadamente huérfana;
- fallos operativos y no esperados se capturan sin registrar excepción, texto, sender, message ID,
  respuesta, token o detalle del proveedor;
- las cancelaciones son observables y se propagan; no se ocultan silenciosamente;
- no existen reintentos en el procesador de background;
- todas las pruebas usan dobles locales y la barrera de red; no hubo llamadas reales a OpenAI o
  Meta ni uso de credenciales reales;
- F2.9 y todas las subfases posteriores permanecen `⬜ PENDIENTE`.

Riesgos/Pendientes:

- `BackgroundTasks` vive en el proceso y no es durable: una caída después del ACK puede perder el
  lote sin que Meta lo reenvíe;
- no existe backpressure persistente, recuperación tras reinicio ni coordinación entre procesos;
- una cancelación queda registrada pero no se reprograma automáticamente;
- los lotes permanecen secuenciales y pueden acumular trabajo bajo carga;
- antes de producción debe evaluarse una cola/worker durable con apagado y métricas verificables;
- la prueba real end-to-end corresponde exclusivamente a F2.9.

Siguiente:

- F2.9 — Prueba real en entorno de Meta, sin iniciar hasta recibir instrucción explícita del
  usuario.

---

## 2026-09-21 — Migración del proveedor de WhatsApp a GreenAPI

**Fase:** Fase 2
**Tarea:** F2.9 — Migración y prueba real con GreenAPI
**Estado:** 🧪 VALIDACION

Cambios:

- localizado el repositorio solicitado en `C:\Proyectos\SanAngel_AI` y preservados los cambios
  existentes relacionados con diagnósticos numéricos seguros del proveedor;
- verificada la viabilidad contra la documentación oficial vigente de GreenAPI;
- migradas configuración, autenticación del webhook, schemas entrantes y envío saliente desde
  Meta Cloud API a GreenAPI;
- mantenidos los contratos `InboundMessage`, `WhatsAppClient`, `MessageOrchestrator`,
  idempotencia y procesamiento en background;
- conservados los estados e historial de F2.1-F2.8; el cambio de proveedor se registra en F2.9;
- actualizadas pruebas, reglas del repositorio, ejemplo de entorno, README y diseño de Fase 2;
- actualizado `.env` local sin mostrar valores: retiradas las entradas de Meta, agregados los
  placeholders GreenAPI y preservada la configuración de OpenAI; no se detuvieron los procesos
  locales existentes.

Archivos:

- `.env.example`
- `AGENTS.md`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`
- `backend/app/api/routes/whatsapp.py`
- `backend/app/core/config.py`
- `backend/app/core/exceptions.py`
- `backend/app/schemas/whatsapp.py`
- `backend/app/services/message_orchestrator.py`
- `backend/app/services/whatsapp_background_processor.py`
- `backend/app/services/whatsapp_client.py`
- `backend/app/services/whatsapp_webhook_service.py`
- pruebas relacionadas en `backend/tests/`.

Validación:

- `.venv\Scripts\python.exe -m pytest -q` -> 171 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 48 archivos con formato
  correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores después de corregir un espacio final en este plan;
- inspección sanitizada de `.env` -> una entrada por cada variable GreenAPI, tres credenciales aún
  vacías, host default válido, cero entradas Meta y configuración OpenAI preservada;
- carga de `Settings` con el `.env` actualizado -> correcta, sin imprimir secretos.

Seguridad:

- tokens GreenAPI protegidos con `SecretStr` y configuración ausente tratada con fallo cerrado;
- token Bearer del webhook comparado en tiempo constante antes de leer el body;
- `idInstance`, `chatId` y host HTTPS validados;
- allowlist restringida a `green-api.com` y subdominios;
- URL final de `sendMessage`, bodies, tokens, texto y destinatarios ausentes de errores/logs;
- logs informativos de URL de `httpx` y `httpcore` deshabilitados debido al token obligatorio en
  el path de GreenAPI;
- pruebas reales no ejecutadas sin credenciales del usuario.

Riesgos/Pendientes:

- F2.9 no cumple todavía el criterio end-to-end y no se marca completada;
- el `.env` local aún necesita valores reales para ID de instancia, token de instancia y token de
  webhook; los procesos activos deben reiniciarse después para cargar configuración y código
  actuales;
- el token de instancia viaja en el path por diseño de GreenAPI; cualquier proxy externo también
  debe evitar registrar URLs completas;
- continúan las limitaciones conocidas de idempotencia en memoria y `BackgroundTasks` no durable.

Siguiente:

- continuar F2.9 con configuración local de una instancia GreenAPI, registro del webhook y prueba
  real completa; no iniciar F2.10 automáticamente.

---

## 2026-09-21 — Preparación operativa del webhook GreenAPI

**Fase:** Fase 2
**Tarea:** F2.9 — Migración y prueba real con GreenAPI
**Estado:** 🧪 VALIDACION

Cambios:

- cargadas de forma sanitizada las credenciales locales reales y confirmado que la instancia
  GreenAPI está autorizada, sin imprimir ID, tokens ni URLs con secretos;
- ampliada la validación numérica de `idInstance` hasta 20 dígitos en configuración, schema y
  servicio de webhook para admitir el ID real de 12 dígitos;
- ampliada la allowlist HTTPS para admitir tanto `green-api.com` como `greenapi.com` y sus
  subdominios, incluido el host asignado por la consola de la instancia;
- reiniciado el backend en `127.0.0.1:8000` y renovado el túnel HTTPS temporal de Cloudflare;
- verificados el health check público y las respuestas 405/403/200 esperadas del webhook;
- ejecutada la prueba real; el usuario confirmó la respuesta final en WhatsApp y F2.10 no fue
  iniciada.

Archivos:

- `AGENTS.md`
- `README.md`
- `backend/app/core/config.py`
- `backend/app/schemas/whatsapp.py`
- `backend/app/services/whatsapp_webhook_service.py`
- `backend/tests/test_config.py`
- `backend/tests/test_whatsapp_webhook.py`
- `backend/tests/test_whatsapp_webhook_service.py`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- prueba real sanitizada de `getStateInstance` -> HTTP 200 y estado `authorized`;
- comprobación local de `GET /health` -> HTTP 200;
- comprobación pública de `GET /health` a través del túnel -> HTTP 200;
- comprobación pública de `GET /api/v1/whatsapp/webhook` -> HTTP 405;
- comprobación pública de POST sin autenticación -> HTTP 403;
- comprobación pública de POST autenticado con payload inocuo -> HTTP 200;
- prueba real iniciada por el usuario -> notificación entrante aceptada con HTTP 200, un mensaje
  procesado y `background_message_batch_completed message_count=1 failed_count=0`;
- cuatro notificaciones posteriores de GreenAPI recibidas y confirmadas con HTTP 200, sin
  inspeccionar ni almacenar sus payloads;
- validación dirigida inicial -> 63 pruebas aprobadas; Ruff detectó finales de línea y se
  normalizaron;
- primera validación ampliada -> 112 pruebas aprobadas y 9 fallidas, lo que reveló el límite
  antiguo de 10 dígitos en el schema; se corrigió antes del reinicio final;
- segunda validación ampliada -> 121 pruebas aprobadas, lint y formato aprobados;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f29-runtime -o
  cache_dir=.venv\pytest-cache-f29-runtime` -> 172 pruebas aprobadas;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 48 archivos con formato
  correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas de conversión LF/CRLF.

Seguridad:

- la allowlist sigue exigiendo HTTPS, host exacto o subdominio y prohíbe credenciales, path,
  query y fragmentos en `GREEN_API_API_URL`;
- `idInstance` continúa limitado a dígitos, sin cero inicial y con longitud acotada;
- los probes no mostraron tokens, números, bodies, mensajes ni URLs que contengan el token de
  instancia;
- el webhook rechazó solicitudes no autenticadas antes de procesar el body;
- `.env` permaneció ignorado y no se copiaron credenciales a archivos versionados.

Riesgos/Pendientes:

- el túnel `trycloudflare.com` es temporal: su URL cambia si se reinicia `cloudflared` y no es
  adecuado para producción;
- la URL pública actual, el mismo `webhookUrlToken` local e `incomingWebhook=yes` quedaron
  configurados en GreenAPI;
- el recorrido WhatsApp -> GreenAPI -> webhook -> OpenAI -> GreenAPI -> WhatsApp fue confirmado
  de extremo a extremo por el usuario;
- continúan las limitaciones conocidas de idempotencia en memoria y `BackgroundTasks` no
  durable.

Siguiente:

- ejecutar los validadores finales y cerrar F2.9; mantener F2.10 `⬜ PENDIENTE`.

---

## 2026-09-21 — Cierre de la migración y prueba real con GreenAPI

**Fase:** Fase 2
**Tarea:** F2.9 — Migración y prueba real con GreenAPI
**Estado:** ✅ COMPLETADO

Cambios:

- sustituida la frontera de Meta por configuración, webhook autenticado, schemas y cliente
  saliente de GreenAPI sin cambiar los contratos internos del chatbot;
- admitidos el ID numérico y host HTTPS asignados por la instancia real, con longitud acotada y
  allowlist de `green-api.com`, `greenapi.com` y sus subdominios;
- configurados localmente instancia, token de instancia y token independiente del webhook sin
  versionar ni mostrar sus valores;
- publicado el webhook mediante un túnel HTTPS temporal y reiniciado el backend;
- completado el recorrido WhatsApp -> GreenAPI -> webhook -> OpenAI -> GreenAPI -> WhatsApp;
- confirmada por el usuario la recepción final de la respuesta;
- F2.10 no fue iniciada.

Archivos:

- `.env.example`
- `AGENTS.md`
- `README.md`
- `docs/fase_2_whatsapp.md`
- `backend/app/api/routes/whatsapp.py`
- `backend/app/core/config.py`
- `backend/app/core/exceptions.py`
- `backend/app/schemas/whatsapp.py`
- `backend/app/services/message_orchestrator.py`
- `backend/app/services/whatsapp_background_processor.py`
- `backend/app/services/whatsapp_client.py`
- `backend/app/services/whatsapp_webhook_service.py`
- pruebas relacionadas en `backend/tests/`
- `plan_de_trabajo.md`

Validación:

- instancia real -> `getStateInstance` HTTP 200 y estado `authorized`;
- health local y público -> HTTP 200;
- webhook público -> GET HTTP 405, POST no autenticado HTTP 403 y POST autenticado HTTP 200;
- mensaje real -> ACK HTTP 200, `message_count=1`, `failed_count=0` y respuesta recibida en
  WhatsApp confirmada por el usuario;
- cuatro notificaciones posteriores del proveedor -> HTTP 200 sin inspeccionar payloads;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f29-close -o
  cache_dir=.venv\pytest-cache-f29-close` -> 172 pruebas aprobadas;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 48 archivos con formato
  correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas de conversión LF/CRLF;
- cierre operativo solicitado por el usuario -> procesos de Uvicorn y `cloudflared` detenidos,
  puerto 8000 libre y URL temporal respondiendo HTTP 530.

Seguridad:

- credenciales conservadas en `.env` ignorado y representadas como `SecretStr`;
- Bearer del webhook validado en tiempo constante antes de leer el body;
- host restringido a HTTPS y allowlist, sin credenciales, path, query o fragmento configurable;
- token exigido por GreenAPI en el path construido solo en backend y excluido de logs y errores;
- no se conservaron payloads, mensajes, números, destinatarios, tokens ni respuestas completas;
- pruebas normales ejecutadas sin red y con dobles de proveedores.

Riesgos/Pendientes:

- el túnel `trycloudflare.com` fue detenido y su URL ya no es válida; para otra prueba se debe
  generar una URL nueva y actualizar `webhookUrl` en GreenAPI;
- idempotencia continúa en memoria y no sirve para múltiples procesos/instancias;
- `BackgroundTasks` no es una cola durable y puede perder trabajo si el proceso cae tras el ACK;
- Fase 2 permanece abierta hasta ejecutar F2.10.

Siguiente:

- F2.10 — Cierre Fase 2, `⬜ PENDIENTE`; no iniciar sin instrucción explícita.

---

## 2026-09-21 — Cierre de Fase 2

**Fase:** Fase 2 — WhatsApp mediante GreenAPI
**Tarea:** F2.10 — Cierre Fase 2
**Estado:** ✅ COMPLETADO

Cambios:

- verificados F2.1-F2.10, incluido el recorrido real completado en F2.9;
- reforzado `GREEN_API_WEBHOOK_TOKEN` con formato URL-safe y longitud de 32 a 256 caracteres;
- aislada una prueba de caché de configuración respecto del `.env` local;
- documentada la generación y rotación segura del token del webhook;
- actualizado `.env.example` sin agregar valores sensibles;
- documentado que el MVP de Fase 2 no es production-ready;
- mantenidos backend y túnel detenidos;
- Fase 3 no fue iniciada.

Archivos:

- `.env.example`
- `AGENTS.md`
- `README.md`
- `backend/app/core/config.py`
- `backend/tests/test_config.py`
- `docs/fase_2_whatsapp.md`
- `plan_de_trabajo.md`

Validación:

- validación base previa al refuerzo -> 172 pruebas aprobadas, lint/formato aprobados,
  dependencias consistentes y diff sin errores;
- primera validación dirigida del token -> 61 pruebas aprobadas y 1 fallida porque una prueba de
  caché heredaba el `.env` real; la prueba se aisló con un marcador seguro;
- segunda validación dirigida -> 62 pruebas aprobadas, lint y formato aprobados;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f210-final -o
  cache_dir=.venv\pytest-cache-f210-final` -> 175 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 48 archivos con formato
  correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas de conversión LF/CRLF;
- `git ls-files .env .env.example` y `git check-ignore -v .env` -> solo `.env.example` está
  versionado y `.env` permanece ignorado;
- escaneo exacto sanitizado de secretos fuertes -> cero coincidencias en archivos versionados y
  logs de runtime;
- inspección de procesos -> puerto 8000 libre y `cloudflared` detenido.

Seguridad:

- el token corto usado durante la prueba real no se mostró y ahora es rechazado por
  configuración; el backend falla cerrado hasta rotarlo;
- la rotación debe aplicar el mismo valor aleatorio nuevo en `.env` y `webhookUrlToken` de
  GreenAPI antes del próximo arranque;
- `.env.example` conserva vacíos todos los secretos;
- no se registraron payloads, conversaciones, números, tokens ni URLs con credenciales;
- se mantienen autenticación previa al body, comparación constante, validación de instancia,
  allowlist HTTPS y errores seguros;
- la documentación declara expresamente los controles pendientes antes de producción.

Riesgos/Pendientes:

- rotar `GREEN_API_WEBHOOK_TOKEN` localmente y en GreenAPI antes de reiniciar;
- sustituir el túnel temporal por HTTPS estable antes de cualquier despliegue;
- reemplazar idempotencia en memoria por persistencia coordinada;
- reemplazar `BackgroundTasks` por procesamiento durable cuando el riesgo operativo lo exija;
- completar rate limiting, secret manager, observabilidad, backups y demás controles de
  producción en sus fases correspondientes.

Siguiente:

- F3.1 — SQLAlchemy + Alembic + SQLite, `⬜ PENDIENTE`; no iniciar sin instrucción explícita.

---

## 2026-09-21 — Base de persistencia con SQLAlchemy, Alembic y SQLite

**Fase:** Fase 3 — Persistencia comercial
**Tarea:** F3.1 — SQLAlchemy + Alembic + SQLite
**Estado:** ✅ COMPLETADO

Cambios:

- agregados SQLAlchemy 2.0.54 y Alembic 1.20.0 como dependencias runtime con rangos acotados;
- incorporado `DatabaseSettings` independiente de OpenAI y GreenAPI, con `DATABASE_URL`
  protegido por `SecretStr` y limitado a SQLite;
- creados base declarativa con convenciones de nombres, engine lazy, `sessionmaker` y dependencia
  de sesión sin commits implícitos;
- agregado entorno Alembic sin URL embebida ni configuración de logging que pueda mostrarla;
- creada revisión inicial vacía que establece `alembic_version` sin anticipar entidades de
  F3.2;
- ignorados archivos SQLite y sidecars locales;
- documentados configuración, migraciones, límites transaccionales y comandos reproducibles;
- F3.2 no fue iniciada.

Archivos:

- `.env.example`
- `.gitignore`
- `pyproject.toml`
- `alembic.ini`
- `backend/app/core/config.py`
- `backend/app/db/__init__.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `migrations/README.md`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/20260921_0001_initial_schema.py`
- `backend/tests/test_database_config.py`
- `backend/tests/test_database_session.py`
- `backend/tests/test_migrations.py`
- `backend/tests/test_repository_security.py`
- `README.md`
- `plan_de_trabajo.md`

Validación:

- `.venv\Scripts\python.exe -m pip install -e ".[dev]"` -> instalación correcta de SQLAlchemy
  2.0.54, Alembic 1.20.0 y dependencias transitivas;
- primera validación dirigida -> 17 pruebas aprobadas y 2 fallidas por expectativas incorrectas
  de representación oculta y cadena vacía; las pruebas se corrigieron sin relajar validación;
- segunda validación dirigida -> 19 pruebas aprobadas;
- validación dirigida ampliada -> 22 pruebas aprobadas, lint y formato aprobados;
- CLI Alembic sobre SQLite temporal -> `upgrade head`, `current`, `check` y `downgrade base`
  correctos; head `20260921_0001` y cero operaciones nuevas detectadas;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f31-full-1 -o
  cache_dir=.venv\pytest-cache-f31-full-1` -> 194 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 57 archivos con formato
  correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas de conversión LF/CRLF;
- auditoría de alcance -> una sola revisión y solo tabla `alembic_version`; ninguna entidad de
  F3.2 creada.

Seguridad:

- `DATABASE_URL` es configurable, se oculta de `repr` y errores, y no se almacena en
  `alembic.ini`;
- F3.1 acepta solo `sqlite`/`sqlite+pysqlite`, sin host, usuario o password;
- migraciones cargan exclusivamente la configuración DB y no requieren secretos de proveedores;
- no existe SQL manual, SQL concatenado ni `Base.metadata.create_all()` en la aplicación;
- las pruebas usan rutas `tmp_path`, no comparten DB y no acceden a red externa;
- archivos `.db`, `.sqlite`, `.sqlite3` y sidecars están ignorados por Git.

Riesgos/Pendientes:

- el path SQLite relativo depende de ejecutar comandos desde la raíz del repositorio;
- SQLite y el engine síncrono son adecuados para el MVP, no una decisión final de escalamiento;
- la revisión inicial no contiene tablas de negocio por diseño;
- entidades, constraints, repositories y servicios comienzan en F3.2 y subfases posteriores;
- antes de múltiples instancias se debe evaluar PostgreSQL, concurrencia, backups y restore.

Siguiente:

- F3.2 — Entidad sucursales, `⬜ PENDIENTE`; no iniciar sin instrucción explícita.

---

## 2026-09-22 — Un asistente y número por sucursal

**Fase:** Fase 3 — Persistencia comercial
**Tarea:** F3.2 — Entidad sucursales e identidad por asistente
**Estado:** ✅ COMPLETADO

Cambios:

- cambiado el alcance de un solo número para siete tiendas a siete instalaciones/números, uno
  por sucursal, conservando un único código y prompt común;
- agregado `ASSISTANT_BRANCH_CODE` obligatorio, inmutable y validado para fijar el alcance de
  cada runtime sin aceptar selección desde mensajes o argumentos del modelo;
- creada la entidad `Branch` con código único, nombre, dirección, teléfono, horario, estado,
  timestamps y constraints reproducibles mediante Alembic;
- implementado CRUD interno parametrizado y `BranchService`, cuya superficie para el asistente
  solo obtiene y aprovisiona la sucursal configurada;
- agregado perfil JSON v1 ficticio y comando de instalación con validación previa, confirmación
  `--apply` y upsert idempotente;
- ignorados perfiles reales con sufijo `*.assistant-profile.json` y mantenidos fuera del prompt;
- actualizado el prompt común para declarar una sola sucursal asignada sin datos particulares;
- replanificadas consultas, FAQ, Excel, tools, conversaciones, panel, atención humana y
  despliegue para conservar el alcance de sucursal en backend;
- F3.3 y las entidades de productos/precios no fueron iniciadas.

Archivos:

- `.env.example`, `.gitignore`, `AGENTS.md`, `README.md`;
- `backend/app/core/config.py`, `backend/app/core/exceptions.py`;
- `backend/app/prompts/base_system_prompt.txt`;
- `backend/app/schemas/branch.py`;
- `backend/app/db/models/branch.py`, `backend/app/db/models/__init__.py`;
- `backend/app/repositories/branch_repository.py`, `backend/app/repositories/__init__.py`;
- `backend/app/services/branch_service.py`;
- `backend/app/cli/provision_assistant.py`, `backend/app/cli/__init__.py`;
- `migrations/versions/20260922_0002_branches.py`, `migrations/env.py`,
  `migrations/README.md`;
- `examples/assistant_profile.example.json`;
- `backend/tests/test_branches.py` y pruebas existentes de configuración, migraciones, prompt,
  composición y seguridad del repositorio;
- `docs/fase_1_diseno.md`, `docs/fase_2_whatsapp.md`, `plan_de_trabajo.md`.

Validación:

- validación dirigida inicial -> 74 pruebas aprobadas; Ruff señaló una línea larga y cuatro
  archivos con formato inconsistente, corregidos antes del cierre;
- Alembic sobre SQLite temporal -> `upgrade head`, `current`, `check`, `downgrade
  20260921_0001` y nuevo `upgrade head` correctos; head `20260922_0002` y cero operaciones
  nuevas detectadas;
- aprovisionamiento manual ficticio -> preview sin escritura, primer `--apply` con `created` y
  segundo `--apply` con `unchanged`;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f32-final -o
  cache_dir=.venv\pytest-cache-f32-final` -> 219 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 67 archivos con formato
  correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- auditoría de archivos -> `.env` ignorado, ningún perfil real versionado, sin `execute_sql`,
  SQL concatenado ni `create_all()` en la aplicación.

Seguridad:

- un perfil cuyo código no coincide con `ASSISTANT_BRANCH_CODE` se rechaza antes de escribir;
- código de sucursal inmutable y consultas del asistente sin parámetro público de sucursal;
- datos de perfil no se incorporan al system prompt ni a logs del aprovisionador;
- el ejemplo contiene datos ficticios y los perfiles reales quedan ignorados;
- la CLI usa transacción, queries SQLAlchemy parametrizadas y no imprime URL DB, dirección,
  teléfono, horario ni secretos;
- se preservan `SecretStr`, autenticación GreenAPI, bloqueo de red en tests y controles previos.

Riesgos/Pendientes:

- cada `.env` existente debe recibir un `ASSISTANT_BRANCH_CODE` válido antes de volver a iniciar
  el chatbot; la ausencia produce fallo cerrado;
- F3.2 carga únicamente identidad y datos básicos; productos, precios y consultas comerciales
  se implementarán en F3.3-F3.5 y hasta entonces el asistente no los obtiene de la DB;
- durante el MVP se recomienda una DB SQLite distinta por instalación; compartir una futura DB
  exige mantener filtros y pruebas negativas de acceso cruzado en todas las capas;
- la asociación operacional de cada número con su instalación vive en las credenciales GreenAPI
  de cada `.env` y debe verificarse en el checklist de los siete despliegues.

Siguiente:

- F3.3 — Entidad productos, `⬜ PENDIENTE`; no iniciar sin instrucción explícita.

---

## 2026-09-22 — Catálogo de productos por sucursal

**Fase:** Fase 3 — Persistencia comercial
**Tarea:** F3.3 — Entidad productos
**Estado:** ✅ COMPLETADO

Cambios:

- creada la entidad `Product` con nombre, categoría, estado activo, timestamps y pertenencia
  obligatoria a una sucursal;
- agregada la migración reproducible `20260922_0003`, con clave foránea restrictiva, checks de
  texto, unicidad de nombre por sucursal e índice de catálogo;
- habilitada la comprobación de claves foráneas en cada conexión SQLite;
- agregado `ProductData` estricto, con normalización de bordes y rechazo de valores vacíos,
  entradas sin letras/números, controles, campos extra y longitudes inválidas;
- implementado `ProductRepository`, ligado al construirlo a un `Branch` persistido, con CRUD,
  estado activo, consultas siempre filtradas y orden estable por categoría, nombre e id;
- agregadas pruebas de validación, integridad, CRUD, orden determinista y aislamiento negativo
  entre dos sucursales;
- F3.4 y las entidades de precios no fueron iniciadas.

Archivos:

- `README.md`;
- `backend/app/db/session.py`;
- `backend/app/db/models/product.py`, `backend/app/db/models/__init__.py`;
- `backend/app/schemas/product.py`;
- `backend/app/repositories/product_repository.py`, `backend/app/repositories/__init__.py`;
- `migrations/versions/20260922_0003_products.py`, `migrations/env.py`,
  `migrations/README.md`;
- `backend/tests/test_products.py`, `backend/tests/test_migrations.py`;
- `plan_de_trabajo.md`.

Validación:

- baseline dirigido de F3.2 -> 25 pruebas aprobadas;
- validación dirigida de productos, sucursales y migraciones -> 39 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f33-final -o
  cache_dir=.venv\pytest-cache-f33-final` -> 240 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 72 archivos con formato
  correcto;
- Alembic sobre SQLite temporal -> `upgrade head`, `current`, `check`, `downgrade
  20260922_0002`, nuevo `upgrade head` y segundo `check` correctos; head `20260922_0003` y cero
  operaciones nuevas detectadas;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- auditoría estática -> sin `execute_sql`, SQL concatenado, `create_all()` ni sucursal expuesta
  en schemas públicos.

Seguridad:

- los datos del producto no aceptan `branch_id` ni `branch_code`; el repositorio recibe un
  `Branch` persistido resuelto por backend y aplica su id a todas las operaciones;
- `get_by_id`, `list_active` y `list_all` siempre filtran por sucursal; mutaciones sobre un
  producto de otra sucursal se rechazan antes de escribir;
- nombres y categorías se validan en Pydantic y cuentan con límites/checks adicionales en DB;
- claves foráneas de SQLite verificadas mediante una prueba negativa con sucursal inexistente;
- consultas SQLAlchemy parametrizadas y pruebas automatizadas sin red ni secretos.

Riesgos/Pendientes:

- SQLite compara la unicidad y el orden de nombres con su colación predeterminada; F3.5 deberá
  definir la normalización de búsqueda y manejar coincidencias ambiguas sin adivinar;
- el repositorio es infraestructura interna: aún no existen tools ni servicios del chatbot para
  consultar productos, previstos para F3.5;
- aún no hay precios, unidad ni vigencia; pertenecen exclusivamente a F3.4;
- cada instalación debe seguir usando su configuración y, durante el MVP, preferentemente su
  archivo SQLite propio para reforzar el aislamiento.

Siguiente:

- F3.4 — Entidad precios por sucursal, `⬜ PENDIENTE`; no iniciada.

---

## 2026-09-22 — Precios exactos por sucursal

**Fase:** Fase 3 — Persistencia comercial
**Tarea:** F3.4 — Entidad precios por sucursal
**Estado:** ✅ COMPLETADO

Cambios:

- creada la entidad `Price` para mantener un único precio actual por sucursal, producto y unidad,
  con `Decimal`/`NUMERIC(12,2)`, `created_at` y `updated_at`;
- agregada la migración reproducible `20260922_0004`, con importe no negativo, escala máxima de
  dos decimales, límite de precisión, unidad validada y unicidad comercial;
- agregada una relación compuesta producto-sucursal que impide persistir un precio bajo una
  sucursal distinta a la propietaria del producto;
- agregada a `products` la unicidad auxiliar `(id, branch_id)` requerida por esa relación, sin
  cambiar el comportamiento del catálogo de F3.3;
- implementado `PriceData`, que rechaza `float`, campos extra, importes negativos o inexactos y
  unidades inválidas;
- implementado `PriceRepository`, ligado a un `Branch` persistido, con CRUD y consultas
  deterministas siempre filtradas por la sucursal backend;
- agregadas pruebas de exactitud decimal, vigencia mediante `updated_at`, duplicados, constraints,
  rollback de migración y accesos cruzados entre dos sucursales;
- F3.5 y los servicios/tools de consulta comercial no fueron iniciados.

Archivos:

- `README.md`;
- `backend/app/db/models/price.py`, `backend/app/db/models/product.py`,
  `backend/app/db/models/__init__.py`;
- `backend/app/schemas/price.py`;
- `backend/app/repositories/price_repository.py`, `backend/app/repositories/__init__.py`;
- `migrations/versions/20260922_0004_prices.py`, `migrations/env.py`,
  `migrations/README.md`;
- `backend/tests/test_prices.py`, `backend/tests/test_migrations.py`;
- `plan_de_trabajo.md`.

Validación:

- baseline dirigido de productos, migraciones y seguridad -> 31 pruebas aprobadas;
- validación dirigida de precios, productos y migraciones -> 47 pruebas aprobadas;
- prueba dirigida final de precios -> 22 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f34-final-2 -o
  cache_dir=.venv\pytest-cache-f34-final-2` -> 263 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 77 archivos con formato
  correcto;
- Alembic sobre SQLite temporal -> `upgrade head`, `current`, `check`, `downgrade
  20260922_0003`, nuevo `upgrade head` y segundo `check` correctos; head `20260922_0004` y cero
  operaciones nuevas detectadas;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- auditoría estática -> sin `Float`, conversiones `float`, `execute_sql`, SQL concatenado,
  `create_all()` ni ids de sucursal/producto expuestos en schemas públicos.

Seguridad:

- el importe se representa como `Decimal` en Python y `NUMERIC(12,2)` en SQL; los `float` se
  rechazan antes de validar o escribir;
- aplicación y DB rechazan precios negativos, más de dos decimales y valores fuera de precisión;
- `PriceData` no acepta `branch_id` ni `product_id`; el repositorio recibe entidades resueltas por
  backend y filtra todas las lecturas por la sucursal fijada;
- la clave foránea compuesta y las pruebas negativas impiden mezclar productos y precios entre
  sucursales incluso al evitar el repositorio;
- consultas SQLAlchemy parametrizadas y pruebas automatizadas sin red ni secretos.

Riesgos/Pendientes:

- F3.4 conserva solo el precio actual y usa `updated_at` como vigencia operacional; un historial
  o programación de precios futuros requeriría un diseño temporal explícito posterior;
- las unidades son códigos internos validados, pero su catálogo comercial y traducción para el
  cliente deberán definirse antes de importaciones o administración masiva;
- el repositorio es infraestructura interna: `get_product_price` y las tools del chatbot siguen
  pendientes para F3.5;
- durante el MVP cada instalación debe mantener preferentemente su propio archivo SQLite; antes
  de compartir PostgreSQL se debe volver a validar aislamiento y precisión del tipo monetario.

Siguiente:

- F3.5 — Servicios de consulta comercial, `⬜ PENDIENTE`; no iniciada.

---

## 2026-09-22 — Consultas comerciales con alcance backend

**Fase:** Fase 3 — Persistencia comercial
**Tarea:** F3.5 — Servicios de consulta comercial
**Estado:** ✅ COMPLETADO

Cambios:

- agregado `BranchScope` inmutable, validado y construible desde `AssistantSettings`, para
  transportar el `ASSISTANT_BRANCH_CODE` de confianza sin recibir sucursal desde el cliente;
- implementado `CommercialQueryService` con los únicos métodos públicos `get_branch_info`,
  `search_product` y `get_product_price`;
- agregada búsqueda determinista solo sobre productos activos, con límite de entrada,
  normalización Unicode, comparación sin mayúsculas/acentos y ranking exacto/prefijo/parcial;
- agregada consulta exacta de precios por id de producto y unidad dentro de la sucursal inyectada;
- agregados casos explícitos para sucursal no configurada, producto inexistente/inactivo, precio
  ausente, búsqueda sin coincidencias e inputs inválidos;
- agregados DTOs Pydantic inmutables para impedir que el chatbot reciba entidades ORM mutables;
- agregados errores de dominio con mensajes públicos fijos y sin datos de sucursal o consultas;
- agregadas pruebas negativas con dos sucursales, verificación de solo lectura, firmas sin
  sucursal y ausencia de dependencia de OpenAI;
- F3.6, las tools y cualquier integración con el modelo no fueron iniciadas.

Archivos:

- `README.md`;
- `backend/app/core/exceptions.py`;
- `backend/app/services/branch_scope.py`;
- `backend/app/services/commercial_query_service.py`;
- `backend/app/schemas/commercial.py`;
- `backend/tests/test_commercial_query_service.py`;
- `plan_de_trabajo.md`.

Validación:

- baseline dirigido de sucursales, productos, precios y seguridad -> 64 pruebas aprobadas;
- validación dirigida inicial de servicios y persistencia -> 77 pruebas aprobadas;
- prueba dirigida final del servicio comercial -> 21 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -q --basetemp=.venv\pytest-f35-final-2 -o
  cache_dir=.venv\pytest-cache-f35-final-2` -> 284 pruebas aprobadas sin red externa;
- `.venv\Scripts\python.exe -m ruff check --no-cache .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check --no-cache .` -> 81 archivos con formato
  correcto;
- Alembic sobre SQLite temporal -> `upgrade head`, `current` y `check` correctos; head
  `20260922_0004` y cero operaciones nuevas detectadas;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- auditoría estática y de firmas -> sin importaciones de OpenAI, métodos de escritura ni
  argumentos públicos `branch_id`/`branch_code`; el único código de sucursal observado procede
  del `BranchScope` interno.

Seguridad:

- el servicio recibe `BranchScope` por construcción y nunca acepta la sucursal en sus tres
  métodos públicos;
- las búsquedas y lecturas reutilizan repositorios filtrados por la sucursal configurada;
- un id válido de producto de otra sucursal se presenta como no encontrado, sin revelar su
  existencia ni precio;
- el servicio expone solo lectura, no hace commit ni mutaciones y devuelve DTOs congelados;
- inputs de búsqueda, producto y unidad tienen validación y límites antes de consultar;
- errores públicos no incluyen query, ids internos, código de sucursal, SQL ni secretos.

Riesgos/Pendientes:

- la búsqueda MVP recorre el catálogo activo de la sucursal en memoria; antes de catálogos
  grandes conviene incorporar claves normalizadas e índices manteniendo el mismo aislamiento;
- la búsqueda usa el nombre del producto, sin aliases, sinónimos ni categorías; la desambiguación
  conversacional pertenece a F6.5;
- `get_product_price` exige una unidad exacta y validada; su traducción a lenguaje del cliente se
  resolverá en las futuras tools/orquestación;
- F3.5 no conecta el servicio con OpenAI, WhatsApp ni rutas HTTP; esa separación es intencional y
  las tools se implementarán en Fase 6;
- F3.6 debe ejecutar el cierre integral de migraciones e integridad antes de completar Fase 3.

Siguiente:

- F3.6 — Integridad, migraciones y cierre, `⬜ PENDIENTE`; no iniciada.

---

## 2026-09-22 — F3.6 integridad, migraciones y cierre de Fase 3

Fase: Fase 3 — Persistencia comercial, `✅ COMPLETADO`.
Subfase: F3.6 — Integridad, migraciones y cierre, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- ampliadas las pruebas de migración desde una SQLite vacía, revisión por revisión, hasta
  `20260922_0004`, y comprobado que Alembic no detecta divergencias de esquema;
- inspeccionadas las restricciones de sucursales, productos y precios; comprobado el downgrade,
  la nueva aplicación de migraciones, la conservación de datos de tablas anteriores y el rollback
  completo de una transacción fallida;
- agregado un comando de respaldo SQLite que no sobrescribe un archivo anterior y verifica la
  integridad de la copia; documentado el respaldo y recuperación antes de migraciones productivas;
- cerradas F3.6 y la Fase 3 sin iniciar Fase 4.

Archivos:

- `README.md`;
- `migrations/README.md`;
- `scripts/backup_sqlite.py`;
- `backend/tests/test_backup_sqlite.py`;
- `backend/tests/test_migrations.py`;
- `plan_de_trabajo.md`.

Validación:

- `pytest backend/tests/test_migrations.py backend/tests/test_database_session.py -q` ->
  `pytest` no estaba en el PATH; se usó el entorno virtual existente;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_migrations.py
  backend/tests/test_backup_sqlite.py -q` -> 10 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 289 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 83 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git -c safe.directory=C:/Proyectos/SanAngel_AI diff --check` -> sin errores; solo
  advertencias informativas LF/CRLF.

Seguridad:

- el respaldo lee el origen en modo de solo lectura, incluye datos confirmados en WAL, rechaza
  origen ausente y destino existente, comprueba `PRAGMA integrity_check` y evita mostrar rutas o
  datos en el error público del comando;
- el procedimiento exige detener escrituras, verificar que el archivo corresponde a la sucursal,
  guardar la copia fuera del repositorio con acceso restringido y ensayar una recuperación antes
  de una futura migración productiva; un downgrade no sustituye un respaldo;
- las pruebas ejercitan constraints y claves foráneas en bases temporales y no alteran datos de
  instalaciones existentes.

Riesgos/Pendientes:

- no se ejecutó una migración ni un respaldo de una base productiva; el procedimiento debe
  realizarse por instalación cuando exista tal despliegue;
- las pruebas de migración cubren SQLite; una eventual adopción de PostgreSQL requerirá sus
  propias migraciones, pruebas y un plan de respaldo;
- Fase 3 cerrada no implica preparación para producción: siguen pendientes idempotencia
  persistente, cola durable, políticas operativas y demás controles planificados.

Siguiente:

- F4.1 — Formato y fuente FAQ, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-22 — F4.1 formato y fuente FAQ

Fase: Fase 4 — FAQ y conocimiento general del negocio, `🟨 EN_PROGRESO`.
Subfase: F4.1 — Formato y fuente FAQ, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- definido TSV UTF-8 versionado con cabecera exacta, cinco categorías y campos acotados;
- validada cada fila contra el `BranchScope` creado desde configuración backend, con código
  obligatorio por fila y registro resultante inmutable;
- agregado un ejemplo ficticio de cinco categorías y documentado el contrato de la fuente;
- separados el contrato de esquema y la validación de alcance, sin implementar lectura, búsqueda
  ni integración conversacional de F4.2.

Archivos:

- `.gitignore`;
- `README.md`;
- `backend/app/schemas/faq.py`;
- `backend/app/services/faq_scope.py`;
- `backend/tests/test_faq_format.py`;
- `docs/fase_4_faq.md`;
- `examples/faq_table.example.tsv`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_format.py -q`
  -> 20 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 310 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 87 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git -c safe.directory=C:/Proyectos/SanAngel_AI diff --check` -> sin errores; solo
  advertencias informativas LF/CRLF;
- `git check-ignore` -> archivos `*.assistant-faq.tsv` ignorados; el ejemplo sigue versionable;
- búsqueda de patrones de tokens en el ejemplo -> sin coincidencias.

Seguridad:

- cada fila exige un código válido coincidente con el alcance backend y la prueba negativa intenta
  ambos sentidos de acceso cruzado entre dos sucursales;
- columnas extra como `role`, categorías desconocidas, controles en texto y errores que revelen
  el contenido de una respuesta se rechazan o evitan;
- el ejemplo contiene solo datos ficticios y ningún secreto; los archivos reales se ignoran por
  Git; el documento FAQ se trata como dato sin privilegios de prompt ni tools.

Riesgos/Pendientes:

- F4.1 no lee archivos en runtime ni ofrece búsqueda; límites de tamaño, codificación,
  normalización, errores y consulta con filtro backend corresponden a F4.2;
- el contenido FAQ real deberá ser aprobado y mantenido por el negocio; esta subfase valida su
  forma y alcance, no verifica la veracidad de afirmaciones comerciales;
- ninguna FAQ se conecta todavía con OpenAI, WhatsApp o rutas HTTP.

Siguiente:

- F4.2 — Loader/servicio de FAQ, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-22 — F4.2 loader y consulta local de FAQ

Fase: Fase 4 — FAQ y conocimiento general del negocio, `🟨 EN_PROGRESO`.
Subfase: F4.2 — Loader/servicio de FAQ, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- agregado un loader TSV de snapshot único que valida cabecera y todas las filas con el alcance
  de sucursal inyectado desde backend; no entrega resultados parciales ante errores;
- implementada búsqueda de solo lectura sobre preguntas, con normalización de Unicode, acentos,
  mayúsculas y espacios; ranking estable de coincidencias exactas, prefijos y parciales;
- definidos errores seguros de fuente y de consulta, documentación operativa y pruebas de
  lectura, búsqueda, límites, codificación y acceso cruzado.

Archivos:

- `README.md`;
- `backend/app/core/exceptions.py`;
- `backend/app/services/faq_service.py`;
- `backend/tests/test_faq_service.py`;
- `docs/fase_4_faq.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_service.py
  backend/tests/test_faq_format.py -q` -> 40 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 329 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 89 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git -c safe.directory=C:/Proyectos/SanAngel_AI diff --check` -> sin errores; solo
  advertencias informativas LF/CRLF.

Seguridad:

- la lectura está acotada a 256 KiB y 500 filas, exige UTF-8 y TSV válido y rechaza una sola fila
  de otra sucursal sin dejar FAQ parcial disponible;
- la búsqueda limita entrada a 240 caracteres y resultados a cinco registros, no acepta
  `branch_code` ni `branch_id` y no llama a OpenAI ni a proveedores externos;
- `FAQSourceError` y `FAQQueryInputError` usan mensajes públicos fijos sin rutas, contenido de
  archivo ni textos de consulta; las pruebas negativas cubren errores de archivo y ambos sentidos
  de acceso cruzado.

Riesgos/Pendientes:

- la ruta del TSV debe elegirse desde configuración o código backend de cada instalación; el
  servicio todavía no está conectado al orquestador ni a HTTP;
- el servicio conserva un snapshot; para aplicar cambios del archivo se debe construir otro;
- las decisiones de respuesta ante preguntas sin coincidencias o ambiguas corresponden a F4.3;
  la aprobación y actualización del contenido real siguen siendo responsabilidad del negocio.

Siguiente:

- F4.3 — Política de respuesta y desconocidos, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-22 — F4.3 política de respuesta y desconocidos

Fase: Fase 4 — FAQ y conocimiento general del negocio, `🟨 EN_PROGRESO`.
Subfase: F4.3 — Política de respuesta y desconocidos, `✅ COMPLETADO`.

Cambios:

- incorporada una política determinista que solo devuelve el contenido de una pregunta FAQ exacta
  y única; consultas desconocidas, parciales o ambiguas reciben texto fijo sin datos comerciales;
- representada `request_human_help` como propuesta con motivo cerrado y `executed=False`, sin
  contactar al personal ni guardar datos personales;
- documentados el origen no confiable del contenido FAQ, las reglas de respuesta y las pruebas
  de fallback, ambigüedad e intento de cambio de instrucciones.

Archivos:

- `README.md`;
- `backend/app/services/faq_response_policy.py`;
- `backend/tests/test_faq_response_policy.py`;
- `docs/fase_4_faq.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_response_policy.py
  backend/tests/test_faq_service.py -q` -> 27 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 337 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 91 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git -c safe.directory=C:/Proyectos/SanAngel_AI diff --check` -> sin errores; solo
  advertencias informativas LF/CRLF.

Seguridad:

- la política no invoca OpenAI, herramientas, WhatsApp ni escrituras; preserva el alcance de
  sucursal fijado por el backend en `FAQService`;
- consultas con instrucciones añadidas reciben fallback y no cambian permisos ni sucursal;
- el texto recuperado se identifica como dato `untrusted_source`, nunca como instrucción
  privilegiada; los fallback no incluyen la consulta ni contenido de la FAQ;
- la propuesta de ayuda humana no ejecuta el traspaso ni almacena teléfono o conversación.

Riesgos/Pendientes:

- el contenido real de la FAQ requiere aprobación del negocio; la política no garantiza su
  veracidad ni sustituye fuentes deterministas de precios, existencias y otros hechos críticos;
- la política aún no está conectada al orquestador ni al canal WhatsApp; la ejecución del
  traspaso humano requiere autorización, idempotencia y auditoría en fases posteriores.

Siguiente:

- F4.4 — Pruebas adversariales de conocimiento, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F4.4 pruebas adversariales de conocimiento

Fase: Fase 4 — FAQ y conocimiento general del negocio, `🟨 EN_PROGRESO`.
Subfase: F4.4 — Pruebas adversariales de conocimiento, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- añadidos casos adversariales con el loader y la política reales para prompt injection del
  cliente, pedidos de credenciales, instrucciones de documento que se presentan como `SYSTEM`,
  una columna `role` no autorizada, intento de cambiar de sucursal y preguntas FAQ equivalentes
  con respuestas contradictorias;
- reproducido y corregido un conflicto de normalización: búsqueda y decisión exacta ahora
  comparten la misma clave, de modo que respuestas equivalentes no se eligen arbitrariamente;
- documentados la cobertura local y el límite de confianza del texto recuperado.

Archivos:

- `README.md`;
- `backend/app/services/faq_service.py`;
- `backend/app/services/faq_response_policy.py`;
- `backend/tests/test_faq_adversarial.py`;
- `docs/fase_4_faq.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_response_policy.py
  backend/tests/test_faq_service.py -q` -> baseline: 27 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_adversarial.py
  -q` -> antes de corregir, 8 aprobadas y 2 fallidas por selección indebida de una respuesta
  entre preguntas equivalentes;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_adversarial.py
  backend/tests/test_faq_response_policy.py backend/tests/test_faq_service.py -q` -> 38 pruebas
  aprobadas tras la corrección;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 348 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 92 archivos con formato correcto;
  un hallazgo inicial en el nuevo test se corrigió antes de repetir la validación;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- revisión de diff y de dependencias del servicio FAQ -> sin proveedor, tool, escritura ni acceso
  a secretos en la ruta de respuesta.

Seguridad:

- los pedidos de `OPENAI_API_KEY` y tokens GreenAPI reciben fallback fijo; los marcadores de
  prueba colocados en el entorno no aparecen en resultados;
- el texto recuperado que se presenta como `SYSTEM` permanece identificado como
  `untrusted_source` y no se transforma en instrucciones privilegiadas; una columna `role` se
  rechaza al cargar la fuente;
- una fila de otra sucursal invalida toda la fuente; las instrucciones del cliente no cambian el
  alcance ni ejecutan ayuda humana, modificación de precios o confirmación de pedidos;
- dos respuestas FAQ canónicamente equivalentes producen fallback ambiguo sin revelar ninguna.

Riesgos/Pendientes:

- una respuesta FAQ exacta conserva el texto del TSV; su contenido real requiere aprobación del
  negocio y nunca debe promoverse a instrucciones de sistema o herramientas;
- esta suite cubre el servicio FAQ local, todavía no integrado con OpenAI o WhatsApp; la futura
  integración deberá volver a probar el límite de confianza del contenido recuperado.

Siguiente:

- F4.5 — Cierre Fase 4, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F4.5 cierre de Fase 4

Fase: Fase 4 — FAQ y conocimiento general del negocio, `✅ COMPLETADO`.
Subfase: F4.5 — Cierre Fase 4, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- añadida una prueba de integración del ejemplo TSV versionado: las cinco categorías atraviesan
  el loader y la política, devuelven su respuesta exacta y conservan `untrusted_source`;
- actualizados README y guía de Fase 4 con el alcance completado, los límites de integración y
  la decisión de mantener búsqueda local determinista sin RAG;
- cerradas F4.5 y Fase 4 sin iniciar Fase 5.

Archivos:

- `README.md`;
- `backend/tests/test_faq_response_policy.py`;
- `docs/fase_4_faq.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_faq_format.py
  backend/tests/test_faq_service.py backend/tests/test_faq_response_policy.py
  backend/tests/test_faq_adversarial.py -q` -> baseline: 59 pruebas aprobadas; cierre: 60
  pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 349 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 92 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- búsqueda de dependencias RAG, embeddings, vectores y librerías asociadas en servicios,
  esquemas y `pyproject.toml` -> sin coincidencias; revisión de imports FAQ -> sin proveedor
  OpenAI, WhatsApp ni infraestructura de recuperación adicional.

Seguridad:

- la FAQ mantiene el alcance de sucursal backend, valida el archivo completo y entrega respuestas
  como datos `untrusted_source`, sin ejecutar texto recuperado como instrucciones;
- las pruebas adversariales de F4.4 y la nueva prueba del ejemplo completo pasan sin red ni
  credenciales reales;
- no se añadió RAG ni dependencia nueva: el límite de 500 filas y la búsqueda local cubren este
  alcance y evitan una frontera de autorización adicional.

Riesgos/Pendientes:

- el contenido real debe ser aprobado por el negocio; la suite usa solo un ejemplo ficticio;
- el servicio FAQ aún no está conectado al orquestador, a OpenAI ni a WhatsApp. La integración
  posterior deberá preservar el carácter no confiable del texto recuperado y repetir las pruebas
  adversariales; la ayuda humana continúa siendo una propuesta sin ejecución.

Siguiente:

- F5.1 — Contrato/plantilla Excel, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F5.1 contrato y plantilla Excel de precios

Fase: Fase 5 — Importación segura de Excel, `🟨 EN_PROGRESO`.
Subfase: F5.1 — Contrato/plantilla Excel, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- definida una hoja `.xlsx` única `Precios`, versión `1`, con un solo `branch_code` de archivo en
  `E3`, encabezados exactos en fila 6 y datos desde fila 7;
- fijadas columnas `product_id`, `product_name`, `unit`, `price_mxn` y `verified_on`, con tipos,
  límites, moneda, significado de fecha y correspondencia ID/nombre documentados;
- añadido ejemplo exclusivamente ficticio y prueba del paquete Excel, de celdas numéricas y de
  fecha, estructura, estilos, ausencia de macros, fórmulas y vínculos externos;
- ignorados por Git los archivos locales `*.assistant-prices.xlsx`, preservando el ejemplo
  versionado; no se implementó parser, preview ni escritura de precios.

Archivos:

- `.gitignore`;
- `README.md`;
- `backend/app/schemas/price_import_template.py`;
- `backend/tests/test_price_import_template.py`;
- `docs/fase_5_excel.md`;
- `examples/price_import.example.xlsx`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider backend/tests/test_price_import_template.py
  -q` -> 3 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` -> 352 pruebas aprobadas sin red;
- `.venv\Scripts\python.exe -m ruff check .` -> sin hallazgos;
- `.venv\Scripts\python.exe -m ruff format --check .` -> 95 archivos con formato correcto;
  un hallazgo inicial del nuevo test se corrigió antes de la validación final;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; solo advertencias informativas LF/CRLF;
- `git check-ignore` -> un archivo de trabajo `*.assistant-prices.xlsx` se ignora y
  `price_import.example.xlsx` permanece versionable;
- inspección visual y del ZIP `.xlsx` -> importes y fechas legibles, una hoja, sin partes de macro,
  fórmulas ni vínculos externos.

Seguridad:

- la plantilla tiene un único código de sucursal a nivel archivo; el contrato exige compararlo
  con `ASSISTANT_BRANCH_CODE` y resolver cada producto dentro de ese alcance;
- ejemplo, IDs, nombres y precios son ficticios; no se agregaron datos reales ni credenciales;
- `.xlsx` sin macros ni ejecución de código; la futura carga debe seguir validación, preview,
  confirmación, transacción y auditoría antes de escribir en DB.

Riesgos/Pendientes:

- la plantilla y el contrato no son un importador: F5.2 debe rechazar código ajeno, filas
  multi-sucursal, fórmulas, archivos alterados, duplicados, tipos y rangos inválidos antes de
  cualquier escritura;
- `verified_on` documenta verificación comercial, no programa vigencia; la base conserva solo
  el precio actual y su `updated_at`;
- los IDs de ejemplo no representan productos existentes y deben reemplazarse antes de una carga.

Siguiente:

- F5.2 — Parser y validación, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F5.2 Parser y validación

Fase: Fase 5 — Importación segura de Excel, `🟨 EN_PROGRESO`.
Subfase: F5.2 — Parser y validación.
Estado: ✅ COMPLETADO.

Cambios:

- agregado `openpyxl` como única dependencia de lectura Excel; parser de `.xlsx` en memoria y
  de solo lectura con contrato versionado, límite de tamaño/filas, tipos, rangos, duplicados y
  errores por fila;
- rechazo de sucursal distinta al alcance backend antes de procesar filas; cualquier error deja
  el resultado sin filas para una futura etapa de preview;
- añadidas pruebas adversariales y documentación del parser y sus límites.

Archivos:

- `pyproject.toml`;
- `backend/app/services/price_import_parser.py`;
- `backend/tests/test_price_import_parser.py`;
- `docs/fase_5_excel.md`;
- `README.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pip install -e '.[dev]'` -> instalación correcta de `openpyxl 3.1.5`;
- `.venv\Scripts\python.exe -m pytest backend/tests/test_price_import_parser.py -q` ->
  32 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest` -> 384 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 97 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; advertencias informativas de LF/CRLF.

Seguridad:

- no se abren rutas ni se extrae el ZIP; se rechazan nombres con path traversal, entradas
  peligrosas, macros, fórmulas, vínculos externos y dimensiones de hoja que oculten filas;
- límites de paquete/filas y errores sin valores del archivo; `openpyxl` se abre en modo de solo
  lectura, sin conservar VBA ni vínculos;
- parser sin acceso a DB y prueba de archivo inválido/ajeno sin cambios en DB; `branch_code`
  proviene de `BranchScope`, no de filas ni del modelo.

Riesgos/Pendientes:

- F5.2 valida sintaxis y alcance de archivo, pero todavía no consulta si `product_id` existe ni
  si `product_name` coincide con el producto de la sucursal. Esa consulta de solo lectura y el
  preview de impacto corresponden a F5.3;
- no hay confirmación, escritura transaccional ni auditoría en esta subfase.

Siguiente:

- F5.3 — Preview de cambios, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F5.3 Preview de cambios

Fase: Fase 5 — Importación segura de Excel, `🟨 EN_PROGRESO`.
Subfase: F5.3 — Preview de cambios.
Estado: ✅ COMPLETADO.

Cambios:

- añadido servicio de preview que compara cada fila válida del XLSX con producto y precio de la
  sucursal configurada: alta, cambio o precio sin cambio;
- verificación de producto activo y nombre exacto, errores por fila y resumen de impacto;
- salida mínima apta para JSON con precios como texto decimal exacto, más documentación y pruebas.

Archivos:

- `backend/app/services/price_import_preview.py`;
- `backend/tests/test_price_import_preview.py`;
- `docs/fase_5_excel.md`;
- `README.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest backend/tests/test_price_import_preview.py -q` ->
  6 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest` -> 390 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 99 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; advertencias informativas LF/CRLF.

Seguridad:

- solo consultas `SELECT` comprobadas con instrumentación SQL; sin `flush`, `commit` ni escritura;
  se rechazan sesiones con cambios pendientes;
- búsqueda de producto y precio a través de repositorios acotados por `BranchScope`; un ID ajeno
  recibe el mismo error que uno no disponible;
- un archivo inválido o de otra sucursal no consulta DB; la salida no repite valores inválidos,
  datos de otras sucursales, dirección, teléfono, archivo completo ni credenciales.

Riesgos/Pendientes:

- el preview es una lectura puntual y puede quedar desactualizado; F5.4 deberá repetir la
  validación en una transacción antes de escribir;
- no existe todavía endpoint/panel administrativo ni persistencia del preview. Su futura
  exposición requiere autenticación y autorización backend.

Siguiente:

- F5.4 — Importación transaccional, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F5.4 Importación transaccional

Fase: Fase 5 — Importación segura de Excel, `🟨 EN_PROGRESO`.
Subfase: F5.4 — Importación transaccional.
Estado: ✅ COMPLETADO.

Cambios:

- añadido servicio interno de preparación y confirmación explícita, ligado a nombre, SHA-256
  del archivo, sucursal y preview revisado;
- importación en una transacción SQLite con revalidación bajo bloqueo de escritura, alta de
  precios ausentes, actualización de importes distintos y omisión de filas iguales;
- recibo mínimo con huella, sucursal y conteos; documentación y pruebas de reversión completa.

Archivos:

- `backend/app/services/price_import_transaction.py`;
- `backend/tests/test_price_import_transaction.py`;
- `docs/fase_5_excel.md`;
- `README.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\python.exe -m pytest backend/tests/test_price_import_transaction.py -q` ->
  10 pruebas aprobadas;
- `.venv\Scripts\python.exe -m pytest` -> 400 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 101 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; advertencias informativas LF/CRLF.

Seguridad:

- `confirmed` exige el booleano `True`; el archivo y el preview se comparan de nuevo antes de
  escribir y se rechaza contenido alterado o desactualizado;
- repositorios acotados por `BranchScope` inyectan `branch_id`; no se acepta sucursal de celda,
  cliente o modelo y se conserva el precio ajeno en las pruebas;
- `PriceData` recibe `Decimal`; un fallo en la segunda escritura revierte también la primera;
  errores de DB usan mensaje seguro sin SQL ni valores del archivo;
- el recibo ofrece trazabilidad mínima sin conservar el XLSX.

Riesgos/Pendientes:

- F5.5 debe persistir el registro de quién/cuándo/archivo lógico, resumen y errores; el recibo
  de F5.4 todavía no es un audit log duradero;
- no hay endpoint ni panel administrativo; su futura exposición requiere autenticación,
  autorización y mantener el objeto preparado bajo control backend;
- `BEGIN IMMEDIATE` corresponde al MVP con SQLite; se deberá revisar la estrategia de bloqueo
  al migrar a otra base.

Siguiente:

- F5.5 — Auditoría y reporte, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F5.5 Auditoría y reporte

Fase: Fase 5 — Importación segura de Excel, `🟨 EN_PROGRESO`.
Subfase: F5.5 — Auditoría y reporte.
Estado: ✅ COMPLETADO.

Cambios:

- añadida migración y modelo de auditoría con ID de intento, actor opaco, hora UTC, sucursal,
  SHA-256 del archivo lógico, estado, conteos y códigos de error;
- registro de éxito atómico con la importación de precios; rechazos y fallos registrados después
  del rollback, con error seguro si la auditoría tampoco está disponible;
- recibo enlazado al reporte y consultas de reportes acotadas por sucursal; documentación y
  pruebas de trazabilidad, privacidad y reversión.

Archivos:

- `backend/app/db/models/price_import_audit.py`;
- `backend/app/db/models/__init__.py`;
- `backend/app/repositories/price_import_audit_repository.py`;
- `backend/app/services/price_import_transaction.py`;
- `backend/tests/test_migrations.py`;
- `backend/tests/test_price_import_transaction.py`;
- `migrations/versions/20260923_0005_price_import_audits.py`;
- `migrations/env.py`;
- `migrations/README.md`;
- `docs/fase_5_excel.md`;
- `README.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\pytest.exe backend/tests/test_price_import_transaction.py backend/tests/test_migrations.py -q`
  -> 26 pruebas aprobadas;
- `.venv\Scripts\pytest.exe` -> 409 pruebas aprobadas;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 104 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; advertencias informativas LF/CRLF.

Seguridad:

- la tabla no tiene columnas de nombre, ruta, bytes del Excel ni valores de celdas; el servicio
  no crea una copia persistente del archivo y solo calcula SHA-256 si el contenido cabe en 2 MiB;
- los errores guardados contienen únicamente fila, campo y código, con límite de 200 detalles;
  el reporte conserva el conteo total y filtra siempre por sucursal configurada;
- una falla de auditoría revierte los precios; se probaron fallo de DB, acceso entre sucursales y
  ausencia de detalles internos en el error público;
- `ImportActor` exige un identificador opaco; la futura integración administrativa debe crearlo
  desde una identidad autenticada, nunca desde Excel, cliente o modelo.

Riesgos/Pendientes:

- todavía no hay ruta ni panel administrativo; la exposición de reportes requiere autenticación
  y autorización backend;
- los previews abandonados no generan registro; se registran intentos de `confirm` con actor
  válido. La retención y el borrado del historial de auditoría deben definirse antes de producción;
- `BEGIN IMMEDIATE` sigue siendo la estrategia del MVP SQLite y deberá revisarse si cambia la DB.

Siguiente:

- F5.6 — Cierre Fase 5, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F5.6 Cierre Fase 5

Fase: Fase 5 — Importación segura de Excel, `✅ COMPLETADO`.
Subfase: F5.6 — Cierre Fase 5, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- añadidas pruebas adversariales para expansión ZIP, exceso y duplicación de miembros, XML con
  DTD o bytes nulos y rechazo transaccional de un paquete con macro;
- cerrado un hallazgo de la revisión: el parser aceptaba un DTD en `xl/workbook.xml`; ahora
  rechaza directivas DTD/entidades y bytes nulos en partes XML antes de invocar `openpyxl`;
- actualizados la guía y README con el alcance completo de la Fase 5 y los límites de la futura
  interfaz administrativa; cerradas F5.6 y Fase 5 sin iniciar F6.1.

Archivos:

- `backend/app/services/price_import_parser.py`;
- `backend/tests/test_price_import_parser.py`;
- `backend/tests/test_price_import_transaction.py`;
- `docs/fase_5_excel.md`;
- `README.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\pytest.exe backend/tests/test_price_import_parser.py
  backend/tests/test_price_import_transaction.py backend/tests/test_price_import_preview.py
  backend/tests/test_price_import_template.py backend/tests/test_migrations.py -q` -> 73 pruebas
  aprobadas;
- `.venv\Scripts\pytest.exe` -> 415 pruebas aprobadas sin red;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 104 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; advertencias informativas LF/CRLF.

Seguridad:

- los límites de 2 MiB por archivo, 10 MiB descomprimidos y 128 miembros están probados;
  la expansión ZIP se prueba con un archivo pequeño y el parser no extrae miembros a disco;
- se rechazan DTD/entidades y bytes nulos antes del cargador XML, además de macros, fórmulas,
  referencias externas, path traversal y miembros duplicados;
- un XLSX con componente de macro se rechaza durante preview y confirmación, no cambia precios,
  y su reporte contiene solo un código de error, sin el contenido de la carga.

Riesgos/Pendientes:

- el servicio de importación sigue siendo interno. La futura ruta administrativa deberá exigir
  autenticación/autorización y limitar el upload antes de recibir el body completo;
- el historial de auditoría requiere una política de retención y borrado antes de producción;
- las pruebas usan archivos ficticios y no sustituyen una revisión operativa de infraestructura
  y despliegue productivo.

Siguiente:

- F6.1 — Schemas de tools, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F6.1 Schemas de tools

Fase: Fase 6 — OpenAI tool calling para datos exactos, `🟨 EN_PROGRESO`.
Subfase: F6.1 — Schemas de tools, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- definidos cuatro schemas de función para Responses API con `strict: true`, propiedades
  requeridas y `additionalProperties: false`: precio, sucursal, FAQ y propuesta de ayuda humana;
- añadida validación backend de allowlist, JSON acotado, tipos, rangos, unidad, texto, razones
  cerradas, claves duplicadas y campos extra; la sucursal se vincula desde configuración backend
  solo después de validar nombre y argumentos;
- documentado el contrato y su límite: todavía no hay handlers ni ejecución de tool calls.

Archivos:

- `backend/app/services/tool_contracts.py`;
- `backend/tests/test_tool_contracts.py`;
- `docs/fase_6_tools.md`;
- `README.md`;
- `plan_de_trabajo.md`.

Validación:

- `.venv\Scripts\pytest.exe backend/tests/test_tool_contracts.py -q` -> 36 pruebas aprobadas;
- `.venv\Scripts\pytest.exe` -> 451 pruebas aprobadas sin red;
- `.venv\Scripts\ruff.exe check .` -> sin hallazgos;
- `.venv\Scripts\ruff.exe format --check .` -> 107 archivos con formato correcto;
- `.venv\Scripts\python.exe -m pip check` -> dependencias consistentes;
- `git diff --check` -> sin errores; advertencias informativas LF/CRLF.

Seguridad:

- ninguna tool expone `branch_id` o `branch_code`; `run_sql`, escrituras y nombres no registrados
  se rechazan antes del parseo y no pueden ampliar la allowlist;
- los modelos Pydantic son estrictos e inmutables; la validación rechaza claves repetidas, JSON
  no estándar, argumentos grandes o con campos extra y no devuelve texto recibido en errores;
- `BranchScope` se deriva de `AssistantSettings` proporcionado por backend después de validar la
  llamada; pruebas con dos instalaciones confirman que los mismos argumentos no cambian alcance;
- las definiciones siguen la [documentación oficial de OpenAI para strict mode](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)
  y el [subconjunto admitido de JSON Schema](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas).

Riesgos/Pendientes:

- F6.2 deberá implementar handlers de solo lectura que consuman `ValidatedToolCall` y mantener
  el alcance backend; F6.1 no ejecuta ninguna tool ni contacta personal;
- el código `customer_requested` de ayuda humana deberá mapearse a una propuesta permitida en
  F6.2; no representa un traspaso ejecutado;
- algunas restricciones de patrón/rango del schema no son admitidas en modelos ajustados: la
  integración futura debe verificar el modelo configurado y conservar la validación backend.

Siguiente:

- F6.2 — Implementaciones de tools, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F6.2 Implementaciones de tools

Fase: Fase 6 — OpenAI tool calling para datos exactos, `🟨 EN_PROGRESO`.
Subfase: F6.2 — Implementaciones de tools, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- implementados cuatro handlers explícitos que consumen `ValidatedToolCall`, exigen el
  `BranchScope` backend y reutilizan los servicios comerciales y la política FAQ;
- precio inexistente, inactivo, ajeno o sin precio se expresa mediante el mismo resultado tipado
  `ProductPriceNotFoundResult`; la FAQ conserva respuestas marcadas como fuente no confiable y
  fallbacks fijos para búsquedas desconocidas o ambiguas;
- `customer_requested` ahora produce una propuesta conceptual de ayuda humana sin ejecución;
- añadidos tests locales de resultados, no encontrado, alcance entre sucursales y llamadas
  incompatibles; actualizados README y documentación de tools.

Archivos: `backend/app/services/tool_handlers.py`,
`backend/app/services/faq_response_policy.py`, `backend/tests/test_tool_handlers.py`,
`docs/fase_6_tools.md`, `README.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_tool_handlers.py`: 8 passed;
- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_tool_handlers.py backend/tests/test_tool_contracts.py backend/tests/test_commercial_query_service.py backend/tests/test_faq_response_policy.py backend/tests/test_faq_service.py`: 93 passed;
- `.\.venv\Scripts\python.exe -m pytest`: 459 passed;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 109 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace (avisos de conversión LF/CRLF).

Seguridad:

- handlers de solo lectura y métodos explícitos; sin SQL libre, escritura, contacto a personal
  ni acceso a proveedor externo;
- argumentos de modelo no incluyen sucursal; el handler rechaza un `ValidatedToolCall` vinculado
  a otra sucursal antes de leer DB o FAQ;
- productos ajenos no revelan precio ni existencia diferenciada; un archivo FAQ ajeno se rechaza
  entero y el contenido recuperado sigue etiquetado como no confiable.

Riesgos/Pendientes:

- los handlers aún no están conectados a OpenAI ni al flujo WhatsApp; la selección centralizada y
  la serialización segura del resultado corresponden a F6.3;
- la propuesta de ayuda humana no implica transferencia realizada.

Siguiente:

- F6.3 — Dispatcher allowlist, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F6.3 Dispatcher allowlist

Fase: Fase 6 — OpenAI tool calling para datos exactos, `🟨 EN_PROGRESO`.
Subfase: F6.3 — Dispatcher allowlist, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- añadido un dispatcher con mapa inmutable de los cuatro nombres autorizados a los métodos
  explícitos de `ToolHandlers`; un nombre desconocido se rechaza antes de abrir una sesión;
- la validación de F6.1 se aplica otra vez a los argumentos y vincula el alcance desde
  `AssistantSettings`; cada ejecución crea su sesión en el worker y compone handlers con ese
  mismo `BranchScope`;
- añadido timeout de espera configurable en backend (predeterminado 3 s, máximo 30 s), cuatro
  workers como límite global y una excepción segura de timeout;
- agregadas pruebas locales del enrutamiento, rechazo de `execute_sql`, argumentos inválidos,
  lectura entre sucursales, propiedad de la sesión por el worker y timeout; actualizados README
  y documentación de tools.

Archivos: `backend/app/services/tool_dispatcher.py`, `backend/app/core/exceptions.py`,
`backend/tests/test_tool_dispatcher.py`, `docs/fase_6_tools.md`, `README.md`,
`plan_de_trabajo.md`.

Comandos y resultados:

- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_tool_dispatcher.py`: 21 passed;
- `.\.venv\Scripts\python.exe -m pytest`: 480 passed;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 111 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace (avisos de conversión LF/CRLF).

Seguridad:

- mapa cerrado sin `getattr`, `eval`, SQL libre ni funciones aportadas por el modelo;
  `execute_sql` y nombres no autorizados se rechazan antes de parsear argumentos o acceder DB;
- argumentos extra, ambiguos o inválidos se rechazan antes de ejecutar un handler; la sucursal
  proviene solo de configuración backend y una lectura de producto ajeno no revela su precio;
- cada worker posee su sesión de DB; la espera está acotada y como máximo cuatro lecturas pueden
  seguir activas tras el timeout del solicitante; los errores no incluyen argumentos recibidos.

Riesgos/Pendientes:

- el timeout no cancela forzosamente una consulta SQLite o lectura de archivo ya iniciada; una
  operación que quede colgada ocupa uno de los cuatro workers hasta terminar;
- el dispatcher aún no se conecta a Responses API ni serializa resultados para el modelo;
  esa integración corresponde a F6.4.

Siguiente:

- F6.4 — Loop Responses API + tool calls, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F6.4 Loop Responses API + tool calls

Fase: Fase 6 — OpenAI tool calling para datos exactos, `🟨 EN_PROGRESO`.
Subfase: F6.4 — Loop Responses API + tool calls, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- `OpenAIService.generate_reply_with_tools` detecta elementos `function_call`, ejecuta hasta
  cuatro llamadas por respuesta mediante `ToolDispatcher`, devuelve JSON tipado con el `call_id`
  correspondiente y solicita la respuesta final;
- preserva todos los elementos de salida, incluidos los de razonamiento, en las solicitudes
  siguientes; conserva `store` configurable y los errores de proveedor existentes;
- limita la ejecución a tres rondas de tools, cuatro solicitudes a Responses API, 16 elementos
  por respuesta, 1024 tokens de salida por solicitud y 8192 bytes por resultado de tool;
- comprueba la coincidencia del alcance entre servicio y dispatcher, ajusta el prompt para datos
  comerciales obtenidos por tools y etiqueta la FAQ como contenido no confiable;
- añadidas 22 pruebas mockeadas de respuesta final, llamadas múltiples, serialización, límite de
  rondas, argumentos inválidos y respuestas malformadas; actualizados README y documentación.

Archivos: `backend/app/services/openai_service.py`,
`backend/app/services/tool_dispatcher.py`, `backend/app/prompts/base_system_prompt.txt`,
`backend/tests/test_openai_tool_loop.py`, `backend/tests/test_openai_service.py`,
`docs/fase_6_tools.md`, `README.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_openai_tool_loop.py backend/tests/test_openai_service.py backend/tests/test_tool_dispatcher.py`: 53 passed antes de la última prueba de borde;
- primera ejecución de `.\.venv\Scripts\python.exe -m pytest`: 500 passed, 1 failed por un
  salto de línea en una frase del prompt; corregido y repetido;
- primera ejecución de `.\.venv\Scripts\ruff.exe format --check .`: fallo de formato en el test
  actualizado; corregido con `.\.venv\Scripts\ruff.exe format backend/tests/test_openai_service.py`;
- `.\.venv\Scripts\python.exe -m pytest`: 502 passed en la validación final;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 112 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace (avisos de conversión LF/CRLF).

Seguridad:

- nombres y argumentos del modelo pasan por la allowlist y validación de F6.1/F6.3; llamadas
  desconocidas, argumentos extra y sucursal distinta fallan antes de ejecutar un handler;
- respuestas incompletas, IDs repetidos, tipos inesperados y más llamadas que el límite se
  rechazan; el loop no puede continuar indefinidamente;
- la FAQ conserva `trust_level="untrusted_source"` en el JSON devuelto al modelo; el prompt
  prohíbe obedecer instrucciones recuperadas y no presenta ayuda humana como ejecutada;
- tests con cliente mockeado y guardia de red; no se usaron credenciales reales.

Riesgos/Pendientes:

- el método aún no está compuesto con el endpoint interno ni con WhatsApp; falta configurar la
  fuente FAQ de la instalación al integrarlo;
- una respuesta final del modelo puede contener una afirmación comercial no respaldada aunque
  no invoque tools; se debe tratar como riesgo en la integración y pruebas de seguridad futuras;
- el timeout del dispatcher limita la espera, pero no interrumpe una lectura ya iniciada.

Siguiente:

- F6.5 — Desambiguación de producto con sucursal fija, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-23 — F6.5 Desambiguación de producto con sucursal fija

Fase: Fase 6 — OpenAI tool calling para datos exactos, `🟨 EN_PROGRESO`.
Subfase: F6.5 — Desambiguación de producto con sucursal fija, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- nueva política determinista de desambiguación sobre `CommercialQueryService`, limitada a la
  sucursal configurada: coincidencia exacta única, parcial que requiere confirmación, varias
  opciones y producto no encontrado;
- informa el nombre verificado de la sucursal propia; muestra hasta cinco nombres en casos
  ambiguos y solo expone un ID seleccionable para una coincidencia exacta única;
- prompt, README y documentación de Fase 6 actualizados; cinco pruebas nuevas con dos
  sucursales ficticias, precios distintos y mención de otra tienda.

Archivos: `backend/app/services/product_disambiguation.py`,
`backend/tests/test_commercial_query_service.py`, `backend/app/prompts/base_system_prompt.txt`,
`docs/fase_6_tools.md`, `README.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `pytest` y `ruff` sin ruta no se encontraron en `PATH`; se usaron los ejecutables de `.venv`;
- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_commercial_query_service.py`:
  26 passed;
- `.\.venv\Scripts\python.exe -m pytest`: 507 passed;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 113 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace; avisos de conversión LF/CRLF.

Seguridad:

- el alcance viene de `BranchScope` del backend; la API no acepta una sucursal del cliente;
- coincidencias parciales o múltiples no producen ID seleccionado ni precio; productos ajenos
  no aparecen en opciones y sus IDs siguen rechazados por la consulta de precio;
- una mención de otra tienda no cambia el alcance; los textos de respuesta no incluyen el
  término de búsqueda sin validar ni precios de otra sucursal; pruebas sin red ni secretos.

Riesgos/Pendientes:

- el servicio recibe un término de producto explícito; aún no se compone con el flujo de
  WhatsApp ni extrae productos de mensajes libres;
- la búsqueda comercial existente recorre el catálogo activo en memoria; para catálogos grandes
  convendrá indexarla sin alterar el aislamiento ni la regla de confirmación.

Siguiente:

- F6.6 — Pruebas de seguridad de tools, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F6.6 Pruebas de seguridad de tools

Fase: Fase 6 — OpenAI tool calling para datos exactos, `🟨 EN_PROGRESO`.
Subfase: F6.6 — Pruebas de seguridad de tools, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- pruebas adversariales offline del loop y dispatcher: prompt injection del cliente y de FAQ,
  nombres inexistentes, argumentos inválidos, SQL como argumento y texto de búsqueda, y destino
  de exfiltración; el modelo no puede ampliar la allowlist ni cambiar la sucursal backend;
- auditoría mínima del dispatcher con nombre permitido o `unsupported` y estado fijo por intento;
  no incluye argumentos, resultados ni detalles de excepciones;
- guía de Fase 6 actualizada con cobertura y límites de las pruebas.

Archivos: `backend/app/core/logging.py`, `backend/app/services/tool_dispatcher.py`,
`backend/tests/test_openai_tool_loop.py`, `backend/tests/test_tool_dispatcher.py`,
`docs/fase_6_tools.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `git status --short` inicial: limpio; final: solo los seis archivos anteriores modificados;
- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_tool_contracts.py backend/tests/test_tool_dispatcher.py backend/tests/test_openai_tool_loop.py`: 89 passed;
- `.\.venv\Scripts\python.exe -m pytest`: 517 passed;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 113 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace; avisos de conversión LF/CRLF.

Seguridad:

- un nombre desconocido se rechaza antes de abrir sesión y se audita como `unsupported` para
  evitar inyección en logs; los argumentos extra, SQL en `product_id`, selección de sucursal,
  destino URL y datos personales adicionales se rechazan antes del handler;
- texto SQL en una consulta FAQ se trata como dato y produce fallback; la respuesta FAQ maliciosa
  conserva `trust_level="untrusted_source"` y no concede acceso a `read_env`;
- los tests usan proveedor simulado, guardia de red y placeholders sin credenciales reales; se
  comprueba que el marcador de secreto no llegue a las llamadas simuladas y que el log de auditoría
  omita nombres hostiles, argumentos, texto SQL y detalles de excepciones.

Riesgos/Pendientes:

- las pruebas demuestran los límites de privilegios del backend; no demuestran que un modelo real
  nunca genere una afirmación comercial no respaldada en el texto final;
- el loop de tools aún no está conectado al canal WhatsApp ni al endpoint interno; la integración
  necesita configurar la fuente FAQ y validar el texto final antes de ofrecerlo al cliente;
- el estado auditado corresponde al handler; un fallo posterior al serializar su resultado no
  cambia esa línea de auditoría.

Siguiente:

- F6.7 — Cierre Fase 6, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F6.7 Cierre Fase 6

Fase: Fase 6 — OpenAI tool calling para datos exactos, `✅ COMPLETADO`.
Subfase: F6.7 — Cierre Fase 6, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- revisados los criterios de F6.1–F6.6 y los límites de ejecución del loop; una prueba nueva
  confirma el máximo agregado de cuatro solicitudes Responses y doce ejecuciones de tools;
  otra rechaza más de 16 elementos de respuesta antes de ejecutar tools;
- guía de Fase 6 y README actualizados con el alcance interno, costos y trabajo operativo pendiente;
- F6.7 y Fase 6 cerradas en el checkpoint sin iniciar Fase 7.

Archivos: `backend/tests/test_openai_tool_loop.py`, `docs/fase_6_tools.md`, `README.md`,
`plan_de_trabajo.md`.

Comandos y resultados:

- `git status --short` inicial: limpio; final: solo los cuatro archivos anteriores modificados;
- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_openai_tool_loop.py backend/tests/test_tool_dispatcher.py backend/tests/test_tool_contracts.py backend/tests/test_tool_handlers.py backend/tests/test_commercial_query_service.py backend/tests/test_faq_adversarial.py`: 136 passed;
- `.\.venv\Scripts\python.exe -m pytest`: 519 passed;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 113 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace; avisos de conversión LF/CRLF.

Seguridad:

- la cuarta respuesta no ejecuta más tools, aun si pide otras cuatro; cada solicitud mantiene
  `max_output_tokens=1024` y `parallel_tool_calls=False`;
- los topes de rondas, llamadas, tamaño de resultados, concurrencia, timeout y reintentos limitan
  trabajo y exposición; las pruebas siguen mockeadas y bloquean red externa;
- se contrastó el flujo y el costo de schemas/contexto con la documentación oficial de OpenAI.

Riesgos/Pendientes:

- no existe todavía un presupuesto monetario por conversación ni medición de tokens de entrada;
  los schemas y el contexto reenviado generan costo aunque la salida tenga un tope;
- el SDK puede reintentar según configuración; el máximo de 4 solicitudes es del loop lógico,
  no un máximo de intentos HTTP;
- el loop de tools no está integrado al canal WhatsApp ni al endpoint interno; antes de habilitarlo
  para clientes se requieren fuente FAQ por instalación, métricas/alertas de gasto y revisión de
  respuestas finales no respaldadas.

Siguiente:

- F7.1 — Esquema conversations/messages/events, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F7.1 Esquema conversations/messages/events

Fase: Fase 7 — Conversaciones WhatsApp + idempotencia persistente, `🟨 EN_PROGRESO`.
Subfase: F7.1 — Esquema conversations/messages/events, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- modelos `Conversation`, `Message` y `WhatsAppEventReceipt` para el canal WhatsApp, con sucursal
  obligatoria, unicidad por sucursal, restricciones de formato/estado y clave foránea compuesta
  que impide asociar un mensaje a una conversación de otra sucursal;
- revisión Alembic `20260924_0006` reproducible y reversible; modelos registrados para
  autocomprobación de metadatos;
- pruebas de esquema, migraciones, rollback, unicidad y accesos cruzados; README y guía de
  migraciones actualizados.

Archivos: `backend/app/db/models/conversation.py`, `backend/app/db/models/message.py`,
`backend/app/db/models/whatsapp_event_receipt.py`, `backend/app/db/models/__init__.py`,
`migrations/versions/20260924_0006_whatsapp_conversation_schema.py`, `migrations/env.py`,
`backend/tests/test_conversation_schema.py`, `backend/tests/test_migrations.py`, `README.md`,
`migrations/README.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `git status --short` inicial: limpio; final: solo los once archivos anteriores modificados o
  creados;
- `.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_conversation_schema.py backend/tests/test_migrations.py`: 19 passed;
- `.\.venv\Scripts\python.exe -m pytest`: 530 passed;
- `.\.venv\Scripts\ruff.exe check .`: sin errores;
- `.\.venv\Scripts\ruff.exe format --check .`: 118 archivos formateados;
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas;
- `git diff --check`: sin errores de whitespace; avisos de conversión LF/CRLF.

Seguridad:

- `Conversation` guarda una clave opaca de 64 caracteres y no guarda el chat ID/número; `Message`
  solo dirección y hora, sin contenido; el recibo no guarda raw webhook body;
- checks y FKs de SQLite impiden canal diferente, estado inválido, duplicado dentro de la
  sucursal, sucursal inexistente y asociación cruzada de mensajes;
- las pruebas usan bases temporales, no red ni secretos reales. La derivación segura de la clave
  opaca desde `external_user_id` queda expresamente para F7.2.

Riesgos/Pendientes:

- el webhook todavía no usa estas tablas; F7.3 debe conectar la deduplicación persistente y
  resolver las carreras transaccionales. La idempotencia actual sigue siendo temporal;
- `Message` no conserva texto ni resumen; antes de guardar contexto hay que definir retención,
  borrado y redacción en F7.4. El ID externo del recibo debe tratarse como dato identificable;
- antes de aplicar la migración a una instalación con datos se requiere respaldo SQLite
  verificado, según el procedimiento del README.

Siguiente:

- F7.2 — Identidad externa y sucursal inmutable de la instalación, `⬜ PENDIENTE`; recomendada,
  no iniciada.

---

## 2026-09-24 — F7.2 Identidad externa y sucursal inmutable de la instalación

Fase: Fase 7 — Conversaciones WhatsApp + idempotencia persistente, `🟨 EN_PROGRESO`.
Subfase: F7.2 — Identidad externa y sucursal inmutable de la instalación, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- configuración backend `CONVERSATION_IDENTITY_KEY` obligatoria para el servicio de identidad,
  independiente de los tokens de proveedor y oculta en representaciones;
- `ConversationIdentityService` deriva con HMAC-SHA256 una clave opaca del `sender_id` normalizado,
  obtiene la sucursal únicamente de `ASSISTANT_BRANCH_CODE` y reutiliza la conversación para el
  mismo remitente sin guardar número ni texto;
- repositorio limitado a la sucursal resuelta, pruebas de seguimiento «¿y el rib eye?», intentos
  de cambio de sucursal por mensaje, aislamiento entre sucursales, fallos cerrados y logs sin ID;
- README y `.env.example` documentan la configuración y la estabilidad necesaria de la clave.

Archivos: `.env.example`, `README.md`, `backend/app/core/config.py`,
`backend/app/repositories/conversation_repository.py`,
`backend/app/services/conversation_identity_service.py`,
`backend/tests/test_conversation_identity_service.py`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_conversation_identity_service.py backend/tests/test_conversation_schema.py backend/tests/test_config.py -q` → 64 passed;
- `.\\.venv\\Scripts\\python.exe -m pytest -q` → 539 passed;
- `.\\.venv\\Scripts\\ruff.exe check .` → sin errores;
- `.\\.venv\\Scripts\\ruff.exe format --check .` → 121 archivos conformes;
- `.\\.venv\\Scripts\\python.exe -m pip check` → sin dependencias rotas;
- `git diff --check` → sin errores de whitespace; Git mostró avisos de normalización LF/CRLF.

Seguridad:

- la sucursal sale solo de configuración validada y el mensaje no admite un campo de sucursal;
- la BD guarda HMAC de identidad y la sucursal configurada, nunca el número ni el texto;
- el log registra solo código de sucursal y estado `created`/`existing`; la prueba verifica que
  no aparecen el número, texto ni secreto;
- sucursal ausente o inactiva rechazada; sin acceso cruzado entre sucursales.

Riesgos/Pendientes:

- el servicio de identidad aún no está conectado al procesamiento del webhook y la idempotencia
  sigue en memoria; la integración transaccional y carreras concurrentes corresponden a F7.3;
- rotar `CONVERSATION_IDENTITY_KEY` sin migrar los HMAC existentes cambia el mapeo de remitentes;
  conservar la clave estable por instalación hasta definir un procedimiento de rotación.

Siguiente:

- F7.3 — Idempotencia persistente, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F7.3 Idempotencia persistente

Fase: Fase 7 — Conversaciones WhatsApp + idempotencia persistente, `🟨 EN_PROGRESO`.
Subfase: F7.3 — Idempotencia persistente, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- el orquestador real usa `PersistentIdempotencyStore` en lugar del store en memoria; reclama
  `idMessage` entrante mediante `INSERT ... ON CONFLICT DO NOTHING` y la unicidad de
  `(branch_id, provider_message_id)` ya migrada en F7.1;
- reserva, finalización y liberación previa al envío tienen transacciones SQLite independientes;
  se conserva `claimed` tras iniciar un envío ambiguo o fallar el marcado para impedir una segunda
  respuesta automática;
- el flujo conecta el contexto de conversación de F7.2 antes de responder y su inserción también
  tolera carreras del mismo remitente; configuración de identidad y alcance del orquestador deben
  coincidir;
- tests de dos orquestadores y doce stores concurrentes, nueva conexión, ramas separadas,
  errores previos y posteriores al envío; README y guía de WhatsApp actualizados.

Archivos: `README.md`, `docs/fase_2_whatsapp.md`, `backend/app/api/dependencies.py`,
`backend/app/repositories/conversation_repository.py`,
`backend/app/services/conversation_identity_service.py`,
`backend/app/services/message_orchestrator.py`,
`backend/app/services/persistent_idempotency_store.py`,
`backend/tests/test_conversation_identity_service.py`,
`backend/tests/test_message_orchestrator.py`,
`backend/tests/test_persistent_idempotency_store.py`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_persistent_idempotency_store.py backend/tests/test_conversation_identity_service.py backend/tests/test_message_orchestrator.py -q` → 24 passed;
- `.\\.venv\\Scripts\\python.exe -m pytest -q` → 549 passed;
- `.\\.venv\\Scripts\\ruff.exe check .` → sin errores;
- `.\\.venv\\Scripts\\ruff.exe format --check .` → 123 archivos conformes;
- `.\\.venv\\Scripts\\python.exe -m pip check` → sin dependencias rotas;
- `git diff --check` → sin errores de whitespace; Git avisó sobre normalización LF/CRLF.

Seguridad:

- la restricción única y la inserción atómica dejan un solo ganador, también entre stores
  independientes; duplicados no generan una segunda consulta al chatbot ni envío;
- la sucursal se deriva de la configuración backend y una sucursal inactiva falla de forma cerrada;
- IDs, números, texto y secretos no aparecen en los nuevos logs o errores de infraestructura;
- el envío incierto retiene la reserva y bloquea reintentos automáticos que podrían duplicar la
  respuesta.

Riesgos/Pendientes:

- un proceso puede detenerse tras reservar o un envío puede quedar ambiguo; `claimed` requiere
  conciliación operacional antes de reenvío y no existe entrega exactamente una vez entre SQLite
  y GreenAPI;
- `BackgroundTasks` sigue sin ser una cola durable: un fallo posterior al ACK puede perder trabajo;
- se requiere ejecutar migraciones y configurar `CONVERSATION_IDENTITY_KEY` estable antes de usar
  el flujo persistente en cada instalación.

Siguiente:

- F7.4 — Política de retención y redacción, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F7.4 Política de retención y redacción

Fase: Fase 7 — Conversaciones WhatsApp + idempotencia persistente, `🟨 EN_PROGRESO`.
Subfase: F7.4 — Política de retención y redacción, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- política técnica documentada para las tres tablas de WhatsApp: campos mínimos, omisión de
  identificadores y texto en logs, retención de 30 días y excepciones de seguridad;
- servicio con vista previa y purga transaccional por sucursal, borrado individual de conversación
  y metadatos de mensajes por identidad HMAC, y conteo de reservas `claimed` para revisión;
- comando local de purga con vista previa por defecto y `--apply` para el borrado; la purga puede
  continuar aunque falte la clave HMAC, mientras el borrado individual la exige;
- la resolución de cada mensaje entrante actualiza `Conversation.updated_at` para que el plazo
  de inactividad refleje la actividad real; pruebas de plazos, aislamiento, redacción y CLI.

Archivos: `README.md`, `docs/fase_2_whatsapp.md`, `docs/fase_7_privacidad.md`,
`backend/app/cli/purge_whatsapp_metadata.py`,
`backend/app/repositories/conversation_repository.py`,
`backend/app/services/conversation_identity_service.py`,
`backend/app/services/whatsapp_privacy_service.py`,
`backend/tests/test_whatsapp_privacy_service.py`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_whatsapp_privacy_service.py backend/tests/test_conversation_identity_service.py backend/tests/test_persistent_idempotency_store.py -q` → 27 passed;
- `.\\.venv\\Scripts\\python.exe -m pytest -q` → 557 passed;
- `.\\.venv\\Scripts\\ruff.exe check .` → sin errores;
- `.\\.venv\\Scripts\\ruff.exe format --check .` → 127 archivos conformes;
- `.\\.venv\\Scripts\\python.exe -m pip check` → sin dependencias rotas;
- `git diff --check` → sin errores de whitespace; Git avisó sobre normalización LF/CRLF.

Seguridad:

- la purga y el borrado individual usan únicamente `ASSISTANT_BRANCH_CODE`, nunca una sucursal
  de input; las pruebas mantienen intactos los datos de otra sucursal;
- no se escriben números, texto, HMAC ni IDs de proveedor en los logs/resultado del comando;
- recibos `claimed` no se borran automáticamente para evitar una segunda respuesta tras un
  envío ambiguo; se informa solo su conteo cuando llevan más de un día;
- el esquema sigue sin contenido conversacional; el recibo conserva solo ID/estado/horas hasta
  su vencimiento.

Riesgos/Pendientes:

- programar `--apply` diariamente por instalación antes de producción; aquí se entrega el
  comando pero no se cambia ningún planificador ni base real;
- una reentrega después de 30 días puede volver a procesarse; el plazo debe revisarse con datos
  operativos y el responsable de privacidad;
- `claimed` necesita conciliación manual; `DELETE` no sanea páginas libres, WAL, respaldos ni
  copias externas, que requieren un procedimiento operacional separado.

Siguiente:

- F7.5 — Preguntas no resueltas, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F7.5 Preguntas no resueltas

Fase: Fase 7 — Conversaciones WhatsApp + idempotencia persistente, `🟨 EN_PROGRESO`.
Subfase: F7.5 — Preguntas no resueltas, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- entidad y migración `unresolved_questions` con índice único por sucursal, motivo y HMAC de
  pregunta normalizada; incremento atómico de ocurrencias con `UPSERT`;
- registro únicamente de fallbacks determinísticos de FAQ cuando el dispatcher recibe la
  configuración de identidad; consulta interna acotada para un panel autorizado futuro;
- purga de agregados 30 días después de su última aparición, más política de privacidad y README;
- pruebas de normalización, minimización de datos, aislamiento entre sucursales, concurrencia,
  dispatcher, retención y migraciones.

Archivos: `backend/app/db/models/unresolved_question.py`, `backend/app/db/models/__init__.py`,
`migrations/versions/20260924_0007_unresolved_questions.py`,
`backend/app/services/unresolved_question_service.py`, `backend/app/services/tool_dispatcher.py`,
`backend/app/services/whatsapp_privacy_service.py`, `backend/app/cli/purge_whatsapp_metadata.py`,
`backend/tests/test_unresolved_question_service.py`, `backend/tests/test_migrations.py`,
`docs/fase_7_privacidad.md`, `README.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.venv\Scripts\python.exe -m pytest backend/tests/test_unresolved_question_service.py backend/tests/test_whatsapp_privacy_service.py backend/tests/test_tool_dispatcher.py backend/tests/test_migrations.py -q` → 53 passed;
- `.venv\Scripts\python.exe -m pytest -q` → 564 passed;
- `.venv\Scripts\python.exe -m ruff check .` → sin errores;
- `.venv\Scripts\python.exe -m ruff format --check .` → 131 archivos conformes;
- `.venv\Scripts\python.exe -m pip check` → sin dependencias rotas;
- `git diff --check` → sin errores de whitespace; avisos de normalización LF/CRLF.

Seguridad:

- no se guarda texto, remitente ni ID de conversación en el agregado; el HMAC usa dominio
  separado y la clave backend `CONVERSATION_IDENTITY_KEY`;
- registro y consulta derivan sucursal de configuración; el dispatcher rechaza configuración de
  registro de otra sucursal; logs de tools mantienen solo nombre y estado;
- preguntas con correo/teléfono no aparecen en filas ni logs; purga por sucursal y sin texto.

Riesgos/Pendientes:

- el canal WhatsApp actual usa chat simple, sin dispatcher FAQ, así que todavía no genera estos
  agregados automáticamente; no se infiere falta de respuesta de texto libre del modelo;
- rotar la clave HMAC interrumpe la agrupación con agregados anteriores; la purga diaria requiere
  programación operacional y el plazo de 30 días debe revisarse antes de producción.

Siguiente:

- F7.6 — Cierre Fase 7, `⬜ PENDIENTE`; recomendada, no iniciada.

---

## 2026-09-24 — F7.6 Cierre Fase 7

Fase: Fase 7 — Conversaciones WhatsApp + idempotencia persistente, `✅ COMPLETADO`.
Subfase: F7.6 — Cierre Fase 7, `✅ COMPLETADO`.
Estado: pasó por `🟨 EN_PROGRESO` y `🧪 VALIDACION` antes del cierre.

Cambios:

- revisión final de F7.1–F7.5 y declaración del alcance comprobado en la guía de cierre;
- Alembic registra explícitamente `UnresolvedQuestion`; una prueba migra desde cero y restaura
  en otra ruta un respaldo con datos de las cuatro tablas F7, y otra conserva filas existentes
  al migrar desde `20260924_0006` hasta `20260924_0007`;
- README y guía de migraciones actualizados a siete revisiones e idempotencia persistente;
- plan de backup/restore por instalación, verificación aislada, protección de respaldos y
  conciliación de recibos antes de reanudar webhooks.

Archivos: `backend/tests/test_fase_7_recovery.py`, `backend/tests/test_migrations.py`,
`migrations/env.py`, `migrations/README.md`, `docs/fase_7_cierre.md`,
`docs/fase_7_privacidad.md`, `README.md`, `plan_de_trabajo.md`.

Comandos y resultados:

- `.venv\Scripts\python.exe -m pytest -q` → 566 passed; incluye migración desde cero,
  actualización desde F7.1 y restore aislado;
- `.venv\Scripts\python.exe -m ruff check .` → sin errores;
- `.venv\Scripts\python.exe -m ruff format --check .` → 133 archivos conformes;
- `.venv\Scripts\python.exe -m pip check` → sin dependencias rotas;
- `git diff --check` → sin errores de whitespace; avisos de normalización LF/CRLF.

Seguridad:

- el restore de prueba usa solo rutas temporales y no sobrescribe la base original;
- la guía exige respaldo nuevo y protegido por instalación, conservar la clave de identidad por
  separado, verificar integridad, claves foráneas, revisión y sucursal antes de reanudar;
- recibos posteriores al punto de respaldo y estados `claimed` requieren conciliación para no
  duplicar respuestas; no se usa `downgrade` como recuperación.

Riesgos/Pendientes:

- el restore comprobado es local y aislado; automatización, protección externa, RPO/RTO y ensayos
  operativos de producción permanecen pendientes para F10.7;
- el flujo WhatsApp actual no llena `messages` ni invoca el dispatcher FAQ para agregar preguntas
  no resueltas automáticamente; no se presenta la Fase 7 como preparación para producción.

Siguiente:

- F8.1 — Autenticación backend, `⬜ PENDIENTE`; Fase 8 no iniciada.

---

# 20. Plantilla para historial futuro

```text
## YYYY-MM-DD — Título

Fase:
Subfase:
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
