# plan_de_trabajo.md
## Chatbot IA para Carnicerías — WhatsApp como interfaz del cliente

**Última actualización:** 2026-08-25  
**Fase activa:** Fase 1  
**Subfase siguiente:** F1.4 — Errores, request ID, logging y CORS
**Estado global:** 🟨 EN DESARROLLO  
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

**Estado:** 🟨 EN_PROGRESO

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

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] excepciones internas.

- [ ] mapeo HTTP seguro.

- [ ] request/correlation ID.

- [ ] logging mínimo.

- [ ] CORS allowlist para desarrollo/panel futuro.


### Criterios de aceptación

- [ ] errores no filtran stack traces.

- [ ] request ID propagable.

- [ ] CORS configurable.


### Seguridad

- [ ] no wildcard en producción.

- [ ] no body completo ni Authorization en logs.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.4 — Errores, request ID, logging y CORS. No inicies ninguna subfase posterior.

Alcance obligatorio: excepciones internas; mapeo HTTP seguro; request/correlation ID; logging mínimo; CORS allowlist para desarrollo/panel futuro.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: errores no filtran stack traces; request ID propagable; CORS configurable. Revisa específicamente esta seguridad: no wildcard en producción; no body completo ni Authorization en logs.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.5 — OpenAIService con Responses API

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] agregar/validar SDK oficial.

- [ ] encapsular cliente OpenAI.

- [ ] Responses API.

- [ ] prompt base.

- [ ] timeout.

- [ ] store configurable.

- [ ] errores de proveedor.


### Criterios de aceptación

- [ ] servicio mockeable.

- [ ] Responses API operativa.

- [ ] rutas desacopladas del SDK.


### Seguridad

- [ ] API key backend-only.

- [ ] no Assistants API.

- [ ] no logs de prompt/chat completo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.5 — OpenAIService con Responses API. No inicies ninguna subfase posterior.

Alcance obligatorio: agregar/validar SDK oficial; encapsular cliente OpenAI; Responses API; prompt base; timeout; store configurable; errores de proveedor.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: servicio mockeable; Responses API operativa; rutas desacopladas del SDK. Revisa específicamente esta seguridad: API key backend-only; no Assistants API; no logs de prompt/chat completo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.6 — Endpoint interno POST /api/v1/chat

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] ChatRequest/ChatResponse.

- [ ] validación del mensaje.

- [ ] conexión al servicio de aplicación/OpenAI.

- [ ] tests de éxito/error.


### Criterios de aceptación

- [ ] mensaje válido responde.

- [ ] vacío/largo se rechaza.

- [ ] fallo proveedor es controlado.


### Seguridad

- [ ] límite de entrada.

- [ ] endpoint identificado como desarrollo/interno.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.6 — Endpoint interno POST /api/v1/chat. No inicies ninguna subfase posterior.

Alcance obligatorio: ChatRequest/ChatResponse; validación del mensaje; conexión al servicio de aplicación/OpenAI; tests de éxito/error.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.6 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mensaje válido responde; vacío/largo se rechaza; fallo proveedor es controlado. Revisa específicamente esta seguridad: límite de entrada; endpoint identificado como desarrollo/interno.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.7 — Suite de pruebas y calidad

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] mock OpenAI.

- [ ] casos inválidos.

- [ ] casos de error.

- [ ] pytest.

- [ ] Ruff check.

- [ ] Ruff format --check.

- [ ] pip check si aplica.


### Criterios de aceptación

- [ ] suite pasa sin internet.

- [ ] lint/formato pasan.

- [ ] cero consumo accidental de API.


### Seguridad

- [ ] fixtures sin secretos.

- [ ] tests no salen a red.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.7 — Suite de pruebas y calidad. No inicies ninguna subfase posterior.

Alcance obligatorio: mock OpenAI; casos inválidos; casos de error; pytest; Ruff check; Ruff format --check; pip check si aplica.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.7 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: suite pasa sin internet; lint/formato pasan; cero consumo accidental de API. Revisa específicamente esta seguridad: fixtures sin secretos; tests no salen a red.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.8 — Prueba manual real con OpenAI

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] configurar key solo localmente.

- [ ] iniciar backend.

- [ ] probar /api/v1/chat.

- [ ] comprobar respuesta real.

- [ ] comprobar error seguro.


### Criterios de aceptación

- [ ] una llamada real funciona.

- [ ] credencial nunca aparece en evidencia.


### Seguridad

- [ ] no commitear .env.

- [ ] no copiar key en plan/logs.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_1_diseno.md antes de modificar código.

Trabaja únicamente en la subfase F1.8 — Prueba manual real con OpenAI. No inicies ninguna subfase posterior.

Alcance obligatorio: configurar key solo localmente; iniciar backend; probar /api/v1/chat; comprobar respuesta real; comprobar error seguro.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F1.8 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: una llamada real funciona; credencial nunca aparece en evidencia. Revisa específicamente esta seguridad: no commitear .env; no copiar key en plan/logs.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F1.9 — Cierre Fase 1

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] revisar DoD.

- [ ] README.

- [ ] tests.

- [ ] lint.

- [ ] secrets.

- [ ] checkpoint.


### Criterios de aceptación

- [ ] F1.1-F1.9 verificadas.

- [ ] Fase 1 marcada completa.


### Seguridad

- [ ] no abrir Fase 2 automáticamente.


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

**Estado:** ⬜ PENDIENTE

**Documento guía:** `docs/fase_2_whatsapp.md`


## F2.1 — Configuración Meta/WhatsApp

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] variables WhatsApp/Meta en Settings.

- [ ] .env.example.

- [ ] timeout.

- [ ] versión Graph API configurable.

- [ ] tests de secretos.


### Criterios de aceptación

- [ ] configuración carga sin exponer secretos.

- [ ] no valores reales versionados.


### Seguridad

- [ ] SecretStr para tokens sensibles.

- [ ] Graph API version no dispersa.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.1 — Configuración Meta/WhatsApp. No inicies ninguna subfase posterior.

Alcance obligatorio: variables WhatsApp/Meta en Settings; .env.example; timeout; versión Graph API configurable; tests de secretos.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.1 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: configuración carga sin exponer secretos; no valores reales versionados. Revisa específicamente esta seguridad: SecretStr para tokens sensibles; Graph API version no dispersa.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.2 — Handshake GET del webhook

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] ruta GET webhook.

- [ ] validar mode/token/challenge.

- [ ] tests válido/inválido.


### Criterios de aceptación

- [ ] Meta puede verificar endpoint en prueba.

- [ ] token incorrecto rechazado.


### Seguridad

- [ ] no log verify token.

- [ ] respuesta mínima.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.2 — Handshake GET del webhook. No inicies ninguna subfase posterior.

Alcance obligatorio: ruta GET webhook; validar mode/token/challenge; tests válido/inválido.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.2 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: Meta puede verificar endpoint en prueba; token incorrecto rechazado. Revisa específicamente esta seguridad: no log verify token; respuesta mínima.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.3 — Validación de firma del webhook POST

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] leer raw body.

- [ ] validar firma oficial vigente.

- [ ] HMAC SHA-256 cuando aplique.

- [ ] comparación segura.

- [ ] tests firmas.


### Criterios de aceptación

- [ ] payload no autenticado no se procesa.

- [ ] firma válida permite continuar.


### Seguridad

- [ ] usar META_APP_SECRET.

- [ ] validar antes de confiar en JSON.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.3 — Validación de firma del webhook POST. No inicies ninguna subfase posterior.

Alcance obligatorio: leer raw body; validar firma oficial vigente; HMAC SHA-256 cuando aplique; comparación segura; tests firmas.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.3 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: payload no autenticado no se procesa; firma válida permite continuar. Revisa específicamente esta seguridad: usar META_APP_SECRET; validar antes de confiar en JSON.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.4 — Parser y normalización de eventos

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] Pydantic/models de eventos necesarios.

- [ ] extraer message id/sender/text.

- [ ] ignorar status/eventos no relevantes.

- [ ] tipos no soportados.


### Criterios de aceptación

- [ ] mensaje texto produce InboundMessage interno.

- [ ] payload raro no rompe servidor.


### Seguridad

- [ ] límites de texto.

- [ ] no log raw body completo.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.4 — Parser y normalización de eventos. No inicies ninguna subfase posterior.

Alcance obligatorio: Pydantic/models de eventos necesarios; extraer message id/sender/text; ignorar status/eventos no relevantes; tipos no soportados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.4 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: mensaje texto produce InboundMessage interno; payload raro no rompe servidor. Revisa específicamente esta seguridad: límites de texto; no log raw body completo.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.5 — WhatsAppClient para mensajes salientes

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] cliente Graph API.

- [ ] send_text.

- [ ] timeout.

- [ ] errores.

- [ ] tests HTTP mockeados.


### Criterios de aceptación

- [ ] payload correcto.

- [ ] errores mapeados.

- [ ] cliente mockeable.


### Seguridad

- [ ] token solo header/backend.

- [ ] URL controlada por configuración.


### Prompt para Codex


```text
Lee AGENTS.md, plan_de_trabajo.md y docs/fase_2_whatsapp.md antes de modificar código.

Trabaja únicamente en la subfase F2.5 — WhatsAppClient para mensajes salientes. No inicies ninguna subfase posterior.

Alcance obligatorio: cliente Graph API; send_text; timeout; errores; tests HTTP mockeados.

Antes de programar revisa el estado actual del repositorio y preserva cambios existentes. Al comenzar, marca F2.5 como 🟨 EN_PROGRESO. Implementa cambios pequeños, agrega/actualiza tests y cumple estos criterios: payload correcto; errores mapeados; cliente mockeable. Revisa específicamente esta seguridad: token solo header/backend; URL controlada por configuración.

Antes de cerrar ejecuta los comandos de validación aplicables definidos en AGENTS.md. Si todo pasa, marca primero 🧪 VALIDACION y después ✅ COMPLETADO, actualiza el historial de plan_de_trabajo.md y reporta archivos, comandos, resultados, seguridad, riesgos y siguiente subfase. Si algo no puede comprobarse, no lo marques completado y documenta el bloqueo.
```


## F2.6 — Orquestación WhatsApp -> chatbot -> WhatsApp

**Estado:** ⬜ PENDIENTE


### Alcance

- [ ] conectar inbound normalizado al servicio de chat.

- [ ] obtener answer.

- [ ] enviar answer.

- [ ] manejar fallos.


### Criterios de aceptación

- [ ] mensaje de texto puede recorrer flujo completo con mocks.


### Seguridad

- [ ] webhook no contiene lógica OpenAI directa.

- [ ] fallo no filtra datos.


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
| OpenAI key backend-only | F1 | Sí | ✅ configuración |
| configuración con secretos protegidos | F1 | Sí | ✅ F1.2 |
| validación HTTP/Pydantic | F1 | Sí | ⬜ |
| input size limit | F1 | Sí | ✅ configuración / pendiente endpoint |
| timeout OpenAI | F1 | Sí | ✅ configuración / pendiente uso |
| errores seguros | F1 | Sí | ⬜ |
| logging sin secrets/PII | F1 | Sí | ⬜ |
| CORS allowlist | F1 | Sí cuando haya navegador | ⬜ |
| tests sin OpenAI real | F1 | Sí | 🟨 parcial |
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

**Fase activa:** Fase 1.  
**Subfase activa:** ninguna.
**Última subfase completada:** F1.3 — Aplicación FastAPI + health check.
**Siguiente subfase:** F1.4 — Errores, request ID, logging y CORS.
**WhatsApp:** diseñado para comenzar en Fase 2, no implementado todavía.

No iniciar F1.4 ni Fase 2 automáticamente sin instrucción del usuario.

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
