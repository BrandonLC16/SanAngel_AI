# plan_de_trabajo.md
## Chatbot IA para Carnicerías — WhatsApp como interfaz del cliente

**Última actualización:** 2026-08-27
**Fase activa:** Fase 2
**Subfase siguiente:** F2.7 — Idempotencia mínima (no iniciada)
**Estado global:** 🟨 EN DESARROLLO — Fase 2 iniciada
**Canal principal del cliente:** WhatsApp Business Platform / Cloud API  
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
Meta Cloud API
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


# 6. FASE 2 — WhatsApp Cloud API — interfaz del cliente

**Objetivo:** Recibir mensajes de WhatsApp mediante webhook, procesarlos con el núcleo de chat y responder por WhatsApp de forma segura.

**Estado:** 🟨 EN_PROGRESO

**Fecha de inicio:** 2026-08-26

**Documento guía:** `docs/fase_2_whatsapp.md`


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

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] interfaz IdempotencyStore.

- [ ] detectar IDs duplicados.

- [ ] implementación MVP explícitamente temporal.

- [ ] tests duplicados.


### Criterios de aceptación

- [ ] mismo message id no genera dos respuestas.


### Seguridad

- [ ] documentar límite de memoria/multiproceso.

- [ ] persistencia obligatoria antes de producción.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.7 — Idempotencia mínima. No inicies ninguna subfase posterior.

Alcance obligatorio: interfaz IdempotencyStore; detectar IDs duplicados; implementación MVP explícitamente temporal; tests duplicados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mismo message id no genera dos respuestas. Revisa específicamente esta seguridad: documentar límite de memoria/multiproceso; persistencia obligatoria antes de producción.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.8 — ACK rápido y separación de procesamiento

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] separar validación/ACK de trabajo largo.

- [ ] mecanismo MVP seguro.

- [ ] manejo de excepciones de background.

- [ ] tests.


### Criterios de aceptación

- [ ] webhook responde de forma predecible.

- [ ] trabajo externo no bloquea innecesariamente.


### Seguridad

- [ ] sin tareas huérfanas silenciosas.

- [ ] sin reintentos infinitos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.8 — ACK rápido y separación de procesamiento. No inicies ninguna subfase posterior.

Alcance obligatorio: separar validación/ACK de trabajo largo; mecanismo MVP seguro; manejo de excepciones de background; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.8 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: webhook responde de forma predecible; trabajo externo no bloquea innecesariamente. Revisa específicamente esta seguridad: sin tareas huérfanas silenciosas; sin reintentos infinitos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.9 — Prueba real en entorno de Meta

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] configurar aplicación/número de prueba.

- [ ] URL HTTPS accesible.

- [ ] suscribir webhook.

- [ ] enviar mensaje real.

- [ ] recibir respuesta.


### Criterios de aceptación

- [ ] WhatsApp -> backend -> OpenAI -> WhatsApp funciona.


### Seguridad

- [ ] tokens solo locales/secrets.

- [ ] no pegar payloads sensibles completos en documentos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.9 — Prueba real en entorno de Meta. No inicies ninguna subfase posterior.

Alcance obligatorio: configurar aplicación/número de prueba; URL HTTPS accesible; suscribir webhook; enviar mensaje real; recibir respuesta.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.9 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: WhatsApp -> backend -> OpenAI -> WhatsApp funciona. Revisa específicamente esta seguridad: tokens solo locales/secrets; no pegar payloads sensibles completos en documentos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.10 — Cierre Fase 2

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] pruebas.

- [ ] documentación.

- [ ] revisión seguridad.

- [ ] actualizar plan.


### Criterios de aceptación

- [ ] Fase 2 completa y reproducible.


### Seguridad

- [ ] no declarar producción-ready todavía.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.10 — Cierre Fase 2. No inicies ninguna subfase posterior.

Alcance obligatorio: pruebas; documentación; revisión seguridad; actualizar plan.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.10 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Fase 2 completa y reproducible. Revisa específicamente esta seguridad: no declarar producción-ready todavía.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


# 7. FASE 3 — Persistencia comercial — sucursales, productos y precios

**Objetivo:** Crear SQLite como primera fuente de verdad para datos comerciales.

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F3.1 — SQLAlchemy + Alembic + SQLite

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] configuración DB.

- [ ] engine/session.

- [ ] Alembic.

- [ ] primera migración base.

- [ ] tests.


### Criterios de aceptación

- [ ] DB reproducible desde migraciones.

- [ ] tests aislados.


### Seguridad

- [ ] URL DB configurable.

- [ ] no SQL concatenado.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.1 — SQLAlchemy + Alembic + SQLite. No inicies ninguna subfase posterior.

Alcance obligatorio: configuración DB; engine/session; Alembic; primera migración base; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: DB reproducible desde migraciones; tests aislados. Revisa específicamente esta seguridad: URL DB configurable; no SQL concatenado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.2 — Entidad sucursales

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] modelo Branch.

- [ ] constraints.

- [ ] repository.

- [ ] service.

- [ ] fixtures ficticios.

- [ ] tests.


### Criterios de aceptación

- [ ] CRUD interno/repository válido.


### Seguridad

- [ ] dirección/teléfono tratados como datos de negocio.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.2 — Entidad sucursales. No inicies ninguna subfase posterior.

Alcance obligatorio: modelo Branch; constraints; repository; service; fixtures ficticios; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: CRUD interno/repository válido. Revisa específicamente esta seguridad: dirección/teléfono tratados como datos de negocio.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.3 — Entidad productos

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] Product.

- [ ] categoría.

- [ ] estado activo.

- [ ] repositorio.

- [ ] tests.


### Criterios de aceptación

- [ ] productos consultables de forma determinística.


### Seguridad

- [ ] nombres/inputs validados.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.3 — Entidad productos. No inicies ninguna subfase posterior.

Alcance obligatorio: Product; categoría; estado activo; repositorio; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: productos consultables de forma determinística. Revisa específicamente esta seguridad: nombres/inputs validados.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.4 — Entidad precios por sucursal

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] Price.

- [ ] producto+sucursal.

- [ ] unidad.

- [ ] vigencia/updated_at.

- [ ] constraints.

- [ ] repositorio.

- [ ] tests.


### Criterios de aceptación

- [ ] precio exacto por producto/sucursal.

- [ ] no duplicados inválidos.


### Seguridad

- [ ] Decimal, no float para dinero.

- [ ] precio no negativo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.4 — Entidad precios por sucursal. No inicies ninguna subfase posterior.

Alcance obligatorio: Price; producto+sucursal; unidad; vigencia/updated_at; constraints; repositorio; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: precio exacto por producto/sucursal; no duplicados inválidos. Revisa específicamente esta seguridad: Decimal, no float para dinero; precio no negativo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.5 — Servicios de consulta comercial

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] get_branch_info.

- [ ] search_product.

- [ ] get_product_price.

- [ ] casos no encontrados.

- [ ] tests.


### Criterios de aceptación

- [ ] servicios no dependen de OpenAI.


### Seguridad

- [ ] solo lectura para chatbot.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F3.5 — Servicios de consulta comercial. No inicies ninguna subfase posterior.

Alcance obligatorio: get_branch_info; search_product; get_product_price; casos no encontrados; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F3.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: servicios no dependen de OpenAI. Revisa específicamente esta seguridad: solo lectura para chatbot.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F3.6 — Integridad, migraciones y cierre

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] probar migración desde cero.

- [ ] constraints.

- [ ] rollback.

- [ ] README.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 3 completa.


### Seguridad

- [ ] backup antes de futuras migraciones productivas.


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

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F4.1 — Formato y fuente FAQ

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] definir estructura TXT/Markdown o tabla.

- [ ] categorías.

- [ ] sucursal opcional.

- [ ] ejemplos ficticios.


### Criterios de aceptación

- [ ] formato documentado y validable.


### Seguridad

- [ ] sin secretos.

- [ ] documentos son datos no instrucciones.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.1 — Formato y fuente FAQ. No inicies ninguna subfase posterior.

Alcance obligatorio: definir estructura TXT/Markdown o tabla; categorías; sucursal opcional; ejemplos ficticios.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: formato documentado y validable. Revisa específicamente esta seguridad: sin secretos; documentos son datos no instrucciones.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.2 — Loader/servicio de FAQ

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] loader.

- [ ] normalización.

- [ ] búsqueda básica.

- [ ] errores.

- [ ] tests.


### Criterios de aceptación

- [ ] FAQ consultable sin OpenAI.


### Seguridad

- [ ] límites de tamaño.

- [ ] encoding/control de errores.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.2 — Loader/servicio de FAQ. No inicies ninguna subfase posterior.

Alcance obligatorio: loader; normalización; búsqueda básica; errores; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: FAQ consultable sin OpenAI. Revisa específicamente esta seguridad: límites de tamaño; encoding/control de errores.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.3 — Política de respuesta y desconocidos

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] reglas no inventar.

- [ ] fallback.

- [ ] request_human_help conceptual.

- [ ] tests.


### Criterios de aceptación

- [ ] pregunta desconocida no genera dato falso.


### Seguridad

- [ ] defensa contra prompt injection.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.3 — Política de respuesta y desconocidos. No inicies ninguna subfase posterior.

Alcance obligatorio: reglas no inventar; fallback; request_human_help conceptual; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: pregunta desconocida no genera dato falso. Revisa específicamente esta seguridad: defensa contra prompt injection.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.4 — Pruebas adversariales de conocimiento

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] prompt injection.

- [ ] pedido de secrets.

- [ ] conflicto documento/system.

- [ ] FAQ ambigua.


### Criterios de aceptación

- [ ] reglas internas prevalecen.


### Seguridad

- [ ] no confiar en texto recuperado.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F4.4 — Pruebas adversariales de conocimiento. No inicies ninguna subfase posterior.

Alcance obligatorio: prompt injection; pedido de secrets; conflicto documento/system; FAQ ambigua.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F4.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: reglas internas prevalecen. Revisa específicamente esta seguridad: no confiar en texto recuperado.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F4.5 — Cierre Fase 4

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] documentación.

- [ ] tests.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 4 completa.


### Seguridad

- [ ] no añadir RAG si no es necesario.


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

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F5.1 — Contrato/plantilla Excel

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] columnas obligatorias.

- [ ] IDs/nombres.

- [ ] unidad.

- [ ] precio.

- [ ] fecha.

- [ ] ejemplo ficticio.


### Criterios de aceptación

- [ ] plantilla inequívoca.


### Seguridad

- [ ] no macros.

- [ ] no datos reales en fixtures si no se proporcionan.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.1 — Contrato/plantilla Excel. No inicies ninguna subfase posterior.

Alcance obligatorio: columnas obligatorias; IDs/nombres; unidad; precio; fecha; ejemplo ficticio.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: plantilla inequívoca. Revisa específicamente esta seguridad: no macros; no datos reales en fixtures si no se proporcionan.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.2 — Parser y validación

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] pandas/openpyxl.

- [ ] extensión.

- [ ] tamaño.

- [ ] headers.

- [ ] tipos.

- [ ] duplicados.

- [ ] rangos.

- [ ] errores por fila.


### Criterios de aceptación

- [ ] archivo inválido no modifica DB.


### Seguridad

- [ ] prevenir path traversal.

- [ ] no ejecutar macros.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.2 — Parser y validación. No inicies ninguna subfase posterior.

Alcance obligatorio: pandas/openpyxl; extensión; tamaño; headers; tipos; duplicados; rangos; errores por fila.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: archivo inválido no modifica DB. Revisa específicamente esta seguridad: prevenir path traversal; no ejecutar macros.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.3 — Preview de cambios

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] diff altas/cambios/errores.

- [ ] sin persistir.

- [ ] tests.


### Criterios de aceptación

- [ ] administrador puede revisar impacto.


### Seguridad

- [ ] no mostrar datos sensibles innecesarios.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.3 — Preview de cambios. No inicies ninguna subfase posterior.

Alcance obligatorio: diff altas/cambios/errores; sin persistir; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: administrador puede revisar impacto. Revisa específicamente esta seguridad: no mostrar datos sensibles innecesarios.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.4 — Importación transaccional

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] confirmación.

- [ ] transacción.

- [ ] upserts controlados.

- [ ] rollback.

- [ ] tests.


### Criterios de aceptación

- [ ] todo-o-nada ante error.


### Seguridad

- [ ] auditabilidad.

- [ ] Decimal para dinero.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.4 — Importación transaccional. No inicies ninguna subfase posterior.

Alcance obligatorio: confirmación; transacción; upserts controlados; rollback; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: todo-o-nada ante error. Revisa específicamente esta seguridad: auditabilidad; Decimal para dinero.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.5 — Auditoría y reporte

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] registro de quién/cuándo/archivo lógico.

- [ ] resumen.

- [ ] errores.


### Criterios de aceptación

- [ ] importación trazable.


### Seguridad

- [ ] no conservar archivo más de lo necesario.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F5.5 — Auditoría y reporte. No inicies ninguna subfase posterior.

Alcance obligatorio: registro de quién/cuándo/archivo lógico; resumen; errores.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F5.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: importación trazable. Revisa específicamente esta seguridad: no conservar archivo más de lo necesario.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F5.6 — Cierre Fase 5

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] tests.

- [ ] documentación.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 5 completa.


### Seguridad

- [ ] revisión de carga maliciosa.


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

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F6.1 — Schemas de tools

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] get_product_price.

- [ ] get_branch_info.

- [ ] search_faq.

- [ ] request_human_help.

- [ ] schemas estrictos.


### Criterios de aceptación

- [ ] argumentos claramente validados.


### Seguridad

- [ ] allowlist cerrada.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.1 — Schemas de tools. No inicies ninguna subfase posterior.

Alcance obligatorio: get_product_price; get_branch_info; search_faq; request_human_help; schemas estrictos.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: argumentos claramente validados. Revisa específicamente esta seguridad: allowlist cerrada.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.2 — Implementaciones de tools

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] adaptar servicios comerciales/FAQ.

- [ ] resultados tipados.

- [ ] no encontrado.

- [ ] tests.


### Criterios de aceptación

- [ ] tools funcionan sin modelo.


### Seguridad

- [ ] solo mínimo privilegio.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.2 — Implementaciones de tools. No inicies ninguna subfase posterior.

Alcance obligatorio: adaptar servicios comerciales/FAQ; resultados tipados; no encontrado; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: tools funcionan sin modelo. Revisa específicamente esta seguridad: solo mínimo privilegio.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.3 — Dispatcher allowlist

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] map nombre->handler.

- [ ] rechazar tool desconocida.

- [ ] validar argumentos.

- [ ] timeouts.

- [ ] tests.


### Criterios de aceptación

- [ ] no ejecución arbitraria.


### Seguridad

- [ ] prohibido execute_sql.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.3 — Dispatcher allowlist. No inicies ninguna subfase posterior.

Alcance obligatorio: map nombre->handler; rechazar tool desconocida; validar argumentos; timeouts; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: no ejecución arbitraria. Revisa específicamente esta seguridad: prohibido execute_sql.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.4 — Loop Responses API + tool calls

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] detectar tool call.

- [ ] ejecutar.

- [ ] devolver resultado.

- [ ] respuesta final.

- [ ] límite de iteraciones.

- [ ] tests mockeados.


### Criterios de aceptación

- [ ] flujo determinista y acotado.


### Seguridad

- [ ] evitar loop infinito.

- [ ] no confiar en args modelo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.4 — Loop Responses API + tool calls. No inicies ninguna subfase posterior.

Alcance obligatorio: detectar tool call; ejecutar; devolver resultado; respuesta final; límite de iteraciones; tests mockeados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: flujo determinista y acotado. Revisa específicamente esta seguridad: evitar loop infinito; no confiar en args modelo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.5 — Desambiguación de sucursal/producto

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] si falta sucursal preguntar.

- [ ] coincidencias múltiples.

- [ ] producto inexistente.

- [ ] tests.


### Criterios de aceptación

- [ ] no mezclar precios de sucursales.


### Seguridad

- [ ] nunca adivinar.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.5 — Desambiguación de sucursal/producto. No inicies ninguna subfase posterior.

Alcance obligatorio: si falta sucursal preguntar; coincidencias múltiples; producto inexistente; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: no mezclar precios de sucursales. Revisa específicamente esta seguridad: nunca adivinar.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.6 — Pruebas de seguridad de tools

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] prompt injection.

- [ ] tool inexistente.

- [ ] args inválidos.

- [ ] SQL injection.

- [ ] exfiltración.


### Criterios de aceptación

- [ ] modelo no amplía privilegios.


### Seguridad

- [ ] auditar tool name/result status sin datos excesivos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F6.6 — Pruebas de seguridad de tools. No inicies ninguna subfase posterior.

Alcance obligatorio: prompt injection; tool inexistente; args inválidos; SQL injection; exfiltración.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F6.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: modelo no amplía privilegios. Revisa específicamente esta seguridad: auditar tool name/result status sin datos excesivos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F6.7 — Cierre Fase 6

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] tests.

- [ ] docs.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 6 completa.


### Seguridad

- [ ] revisar costos/loops.


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

**Estado:** ⬜ PENDIENTE

**Documento guía:** `plan_de_trabajo.md`


## F7.1 — Esquema conversations/messages/events

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] Conversation.

- [ ] Message mínimo.

- [ ] WhatsAppEventReceipt.

- [ ] migraciones.

- [ ] tests.


### Criterios de aceptación

- [ ] modelo soporta canal WhatsApp.


### Seguridad

- [ ] minimización de datos.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.1 — Esquema conversations/messages/events. No inicies ninguna subfase posterior.

Alcance obligatorio: Conversation; Message mínimo; WhatsAppEventReceipt; migraciones; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: modelo soporta canal WhatsApp. Revisa específicamente esta seguridad: minimización de datos.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.2 — Identidad externa y contexto de sucursal

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] external_user_id.

- [ ] branch context.

- [ ] actualización segura.

- [ ] tests.


### Criterios de aceptación

- [ ] '¿y el rib eye?' conserva sucursal cuando corresponde.


### Seguridad

- [ ] identificador redactado en logs.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.2 — Identidad externa y contexto de sucursal. No inicies ninguna subfase posterior.

Alcance obligatorio: external_user_id; branch context; actualización segura; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: '¿y el rib eye?' conserva sucursal cuando corresponde. Revisa específicamente esta seguridad: identificador redactado en logs.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.3 — Idempotencia persistente

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] reemplazar store temporal.

- [ ] unique external message id.

- [ ] transacción.

- [ ] tests concurrentes razonables.


### Criterios de aceptación

- [ ] duplicados no producen doble respuesta.


### Seguridad

- [ ] manejar carrera.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.3 — Idempotencia persistente. No inicies ninguna subfase posterior.

Alcance obligatorio: reemplazar store temporal; unique external message id; transacción; tests concurrentes razonables.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: duplicados no producen doble respuesta. Revisa específicamente esta seguridad: manejar carrera.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.4 — Política de retención y redacción

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] definir qué guardar.

- [ ] retention.

- [ ] borrado.

- [ ] redacción.

- [ ] tests.


### Criterios de aceptación

- [ ] privacidad documentada.


### Seguridad

- [ ] no almacenar más de lo necesario.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.4 — Política de retención y redacción. No inicies ninguna subfase posterior.

Alcance obligatorio: definir qué guardar; retention; borrado; redacción; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: privacidad documentada. Revisa específicamente esta seguridad: no almacenar más de lo necesario.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.5 — Preguntas no resueltas

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] entidad/contador.

- [ ] normalización.

- [ ] registro.

- [ ] tests.


### Criterios de aceptación

- [ ] panel futuro puede consultarlas.


### Seguridad

- [ ] no guardar PII innecesaria.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y plan_de_trabajo.md antes de modificar código.

Trabaja únicamente en la subfase F7.5 — Preguntas no resueltas. No inicies ninguna subfase posterior.

Alcance obligatorio: entidad/contador; normalización; registro; tests.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F7.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: panel futuro puede consultarlas. Revisa específicamente esta seguridad: no guardar PII innecesaria.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F7.6 — Cierre Fase 7

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] migraciones desde cero.

- [ ] tests.

- [ ] docs.

- [ ] plan.


### Criterios de aceptación

- [ ] Fase 7 completa.


### Seguridad

- [ ] backup/restore planificado.


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


### Criterios de aceptación

- [ ] backend bloquea privilegios.


### Seguridad

- [ ] no confiar en frontend.


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


### Criterios de aceptación

- [ ] datos administrables.


### Seguridad

- [ ] audit log en cambios críticos.


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


### Criterios de aceptación

- [ ] flujo seguro usable.


### Seguridad

- [ ] CSRF/autorización, límites archivo.


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


### Criterios de aceptación

- [ ] mensaje manual llega por el mismo canal.


### Seguridad

- [ ] solo usuario autorizado.


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


### Criterios de aceptación

- [ ] imagen reproducible.


### Seguridad

- [ ] secrets no baked.


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


### Criterios de aceptación

- [ ] go-live checklist firmado/documentado.


### Seguridad

- [ ] sin riesgos críticos abiertos.


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


### Criterios de aceptación

- [ ] MVP accesible de forma segura.


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
| Meta tokens backend-only | F2 | Sí | ⬜ |
| verificación GET webhook | F2 | Sí | ⬜ |
| firma/autenticidad POST webhook | F2 | Sí | ⬜ |
| raw body para firma | F2 | Sí | ⬜ |
| idempotencia de mensajes | F2/F7 | Sí | ⬜ |
| Graph API timeout/retries acotados | F2 | Sí | ⬜ |
| PII WhatsApp redactada en logs | F2 | Sí | ⬜ |
| SQLAlchemy/queries parametrizadas | F3 | Sí | ⬜ |
| migraciones | F3 | Sí | ⬜ |
| Decimal para dinero | F3 | Sí | ⬜ |
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

---

# 18. Checkpoint actual

**Fase activa:** Fase 2 — WhatsApp Cloud API (`🟨 EN_PROGRESO`).
**Subfase activa:** ninguna.
**Última subfase completada:** F2.5 — WhatsAppClient para mensajes salientes.
**Siguiente subfase:** F2.6 — Orquestación WhatsApp -> chatbot -> WhatsApp, pendiente de
instrucción explícita.
**WhatsApp:** configuración, handshake GET, autenticación del POST y parser completados; cliente
Graph API completado; orquestación todavía no implementada.

No iniciar F2.6 automáticamente.

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
