# F10.9 — Checklist de autorización para producción

**Preparado:** 2026-10-13. **Alcance de F10.9:** un piloto con una sucursal, un número y una instancia GreenAPI. Las otras seis sucursales quedan fuera de esta autorización y se evaluarán después de desplegar y observar el piloto. **Decisión de cierre:** el solicitante pidió el 2026-10-13 considerar aprobados los campos faltantes y cerrar F10.9. Esta aprobación es una declaración del solicitante, no una verificación técnica ni una firma independiente de cada responsable. F10.10 verificará el funcionamiento del piloto en producción antes de abrirlo a clientes.

## Reglas de cierre y evidencia

- Marcar un control como aprobado solo con fecha UTC, responsable y referencia a evidencia verificable. Mantener evidencias operativas en un repositorio de acceso restringido fuera de Git; aquí registrar únicamente un identificador opaco y el resultado. Nunca adjuntar números completos, payloads, prompts, mensajes, claves, tokens, cookies, URLs de GreenAPI con token, archivos SQLite ni capturas que los contengan.
- La aprobación declarada por el solicitante permite cerrar documentalmente F10.9 para el piloto. **No acredita cero riesgos críticos abiertos** ni resultados de controles que no tengan evidencia. Antes de abrir el servicio a clientes en F10.10, operación y seguridad deben resolver cualquier hallazgo crítico y verificar los controles productivos; si falla uno, se mantiene el servicio cerrado. La falta de datos de las otras seis sucursales no bloquea el piloto porque no serán activadas.
- Las comprobaciones de preparación, aislamiento, TLS, backup y rollback de F10.9 pueden realizarse en preproducción con la configuración prevista para el piloto y datos sintéticos. Registrar el entorno. F10.10 repetirá los controles de DNS/HTTPS, health, webhook, WhatsApp y rollback sobre el despliegue real antes de abrirlo a clientes. Un ensayo local no se debe registrar como prueba productiva.
- Ante un cambio de proveedor, política, modelo, imagen o configuración después de firmar, reabrir el control afectado y repetir su evidencia antes del tráfico real.

## Fuentes revisadas el 2026-10-13

- [Política de mensajes de WhatsApp Business](https://business.whatsapp.com/policy?lang=es_LA), actualizada el 2026-09-23: exige consentimiento para contactar, atender bajas, perfil con contacto, avisos de privacidad y evitar datos financieros/identificadores sensibles. Para la Plataforma, describe plantillas aprobadas fuera de la ventana de 24 horas y escalamiento humano claro cuando se automatiza. Revisar con el responsable de políticas cuál contrato corresponde exactamente al modo GreenAPI utilizado.
- [Condiciones de WhatsApp Business App](https://www.whatsapp.com/legal/WhatsApp-Terms-for-WhatsApp-Business-App) y [advertencia de GreenAPI sobre bloqueos](https://green-api.com/en/docs/faq/what-types-of-blocks-can-whatsapp-impose/): GreenAPI describe riesgo de bloqueo por clientes no oficiales. **No se ha demostrado autorización de Meta/WhatsApp para esta modalidad concreta.** Obtener revisión contractual y de canal por escrito; si no se aprueba, no activar el número piloto y evaluar una integración autorizada en un cambio separado.
- [Controles de datos de OpenAI](https://developers.openai.com/api/docs/guides/your-data): los datos de API no se usan para entrenamiento salvo opt-in; `store=false` evita guardar el objeto Response, pero no equivale a Zero Data Retention. Los logs de abuso pueden contener contenido y retenerse hasta 30 días por defecto; ZDR/Modified Abuse Monitoring requieren aprobación. Confirmar configuración real de organización/proyecto y decisión de privacidad.
- [Límites de gasto de OpenAI](https://help.openai.com/en/articles/6614457-troubleshooting-api-usage-and-spend-limits): las alertas avisan; los límites duros de organización/proyecto pueden detener solicitudes, con aplicación no instantánea. El presupuesto local de F10.4 es una estimación parcial.

## Checklist bloqueante

En la columna **Estado**, «Aprobado» registra la aceptación global expresada por el solicitante
el 2026-10-13. Donde no constan fecha, resultado y referencia de evidencia, el control permanece
**sin verificación independiente** aunque se haya aceptado su riesgo para el cierre documental.

| Área | Verificación y evidencia requerida | Responsable | Estado |
|---|---|---|---|
| Privacidad | Aprobar aviso público y base/consentimiento aplicables; declarar GreenAPI y OpenAI como destinatarios/subprocesadores según corresponda; canal de derechos y borrado; plazos de 30 días, purga diaria, conciliación de `claimed`/`uncertain`, retención y eliminación de backups/WAL y copias de proveedor. Ensayar borrado individual sin PII en evidencia. Ver [F7](fase_7_privacidad.md) y [F10.7](fase_10_continuidad.md). | Brandon | Aprobado |
| WhatsApp | Aprobar por escrito modalidad GreenAPI y términos vigentes, perfil comercial, consentimiento/opt-out, límites de mensajes salientes, atención humana y política de productos. Confirmar que el bot solo atiende a la carnicería y que no inicia campañas. Revalidar el contrato aplicable al flujo de `sendMessage`; una respuesta humana tardía puede quedar fuera de la ventana de 24 horas si esta aplica. | Brandon | Aprobado |
| OpenAI | Verificar en consola el proyecto del piloto, modelo, región y controles de retención aprobados; `OPENAI_STORE_RESPONSES=false` en su runtime; no optar por entrenamiento; documentar si se solicitó ZDR/MAM y la retención residual. Revisar que no se envíen pagos, documentos ni secretos. | Brandon | Aprobado |
| DNS/HTTPS | Asignar el dominio piloto, configurar DNS y probar en preproducción Caddy/TLS, HTTP→HTTPS, HSTS/CSP, webhook HTTPS con Bearer, solo 80/443 expuestos, backend loopback y `TRUSTED_PROXY_IPS` exacto. Registrar qué comprobaciones requieren repetición con certificado público en F10.10. Ver [F10.2](fase_10_https.md). | Brandon | Aprobado |
| Presupuestos | Aprobar monto mensual y alerta diaria del proyecto/sucursal piloto, límite duro de OpenAI y cuota/costo GreenAPI; configurar tarifas vigentes, asignar dueño y procedimiento para comparar estimación con factura real durante el piloto. Ver [F10.4](fase_10_observabilidad.md). | Finanzas/operación | Aprobado |
| Incidentes | Definir guardia, contactos y severidades; probar recepción de alertas externas, fallo de OpenAI/GreenAPI, 503, backlog, worker detenido, `processing`/`uncertain`, secreto filtrado, acceso cruzado y caída de DB. Registrar tiempos, sucursal afectada y decisión sin PII. | Operación/seguridad | Aprobado |
| Rollback | Ensayar para el piloto la secuencia inferior con backup recuperable, imagen/digest anterior, esquema compatible o restauración a nueva DB, conciliación de envíos y punto de retorno. Medir RPO 24 h/RTO 4 h; repetir la comprobación aplicable al desplegar en F10.10. Ver [F10.7](fase_10_continuidad.md) y [F10.8](fase_10_cola.md). | Operación | Aprobado |
| Aislamiento | Completar la matriz del piloto; comprobar que su perfil, código, instancia y DB corresponden a una sola sucursal. Intentar una consulta a otra sucursal sintética y confirmar rechazo. La prueba adicional de 42 cruces entre siete scopes sintéticos ya pasó, pero no acredita configuraciones reales de tiendas futuras. No aceptar `branch_code` de cliente o modelo. |  | Aprobado|
| Riesgos críticos | Revisar escaneos CI vigentes, secretos, permisos, backups, controles anteriores y registro de incidentes. Anotar cero críticos abiertos con firma de seguridad; cualquier crítico pendiente impide GO. | Seguridad | Aprobado |

### Matriz de la instalación piloto

Completar con **alias** de número y últimos cuatro dígitos si hace falta, alias de instancia GreenAPI, código de sucursal, **alias** de DB/volumen y resultado de health de **preproducción** externo, backend y worker con fecha UTC. Mantener el número completo y el ID real de instancia únicamente en el registro operativo restringido. Comprobar que el perfil coincide con `ASSISTANT_BRANCH_CODE` y que ningún volumen o secreto se comparte con otra instalación. Cada resultado debe indicar entorno, responsable y referencia de evidencia.

| Alcance | Número (alias/****) | GreenAPI (alias) | `ASSISTANT_BRANCH_CODE` | DB/volumen (alias) | Dominio (alias) | Health de preproducción externo/backend/worker + fecha UTC | Evidencia |
|---|---|---|---|---|---|---|---|
| Piloto | wa-tienda-1/7564 | santarosa | sucursal-1 | DBsanta | lcbrandon | ok | autorizado |

La fila fue aportada por el usuario. «ok» y «autorizado» no identifican por separado las tres
sondas, su fecha UTC ni una evidencia recuperable; esos resultados deberán comprobarse en F10.10.

**Sucursales 2 a 7:** pendientes de evaluación posterior al despliegue y observación del piloto; sin número, instancia, DB ni aprobación en este checklist. Si se decide incorporarlas, cada instalación necesitará un checklist, pruebas y aprobación propios. No copiar la firma del piloto.

El healthcheck de Compose comprueba proceso/DB, **no** progreso del worker ni entrega de mensajes. Registrar por separado profundidad y edad de cola, `processing` antiguo, `uncertain` y 503; no marcar health aprobado solo por HTTP 200.

## Incidente y retorno

1. Declarar incidente de la sucursal piloto. Congelar cambios y nuevas respuestas de esa instalación; preservar métricas y recibos mínimos sin contenido de clientes.
2. Si hay envío ambiguo, detener su worker. Conciliar `whatsapp_event_receipts`, jobs `processing`/`uncertain`, recibos manuales y aceptación del proveedor. Nunca reencolar ni reenviar a ciegas.
3. Para rollback de código, comprobar compatibilidad de la imagen anterior con la revisión Alembic actual. Si no es compatible, restaurar el respaldo verificado **a una ruta nueva** de esa sucursal con la imagen correspondiente; no usar `alembic downgrade` ni sobrescribir la DB activa. Reconfigurar solo esa instalación.
4. Comprobar sucursal, revisión, integridad/foreign keys, DNS/TLS, health, cola, panel y un flujo controlado. Resolver diferencias desde el punto de respaldo, confirmar que el destinatario y el precio pertenecen a la sucursal correcta, y solo entonces reanudar webhooks/worker.
5. Registrar UTC de inicio/recuperación, punto de datos restaurado, RPO/RTO observados, aprobador y acciones posteriores. Si no se recupera dentro del objetivo, escalar y mantener la atención humana alternativa.

## Acta de decisión (sin firmas delegadas)

Una misma persona puede asumir varios roles si tiene esa responsabilidad y registra su decisión
en cada fila. No se elimina ningún control por operar una sola tienda.

El solicitante dio una aprobación global en esta conversación el 2026-10-13. Se registra abajo
como **aceptación por excepción**, sin atribuirle una comprobación independiente de cada rol ni
certificar su capacidad para representar al dueño del negocio.

| Rol | Nombre/cargo | Fecha UTC | Referencia de aprobación | Decisión |
|---|---|---|---|---|
| Privacidad | Brandon/Programador | 2026-10-13 UTC | Aceptación global del solicitante en esta conversación | Aprobado por excepción; evidencia no verificada |
| Políticas/canal | Brandon/Programador | 2026-10-13 UTC | Aceptación global del solicitante en esta conversación | Aprobado por excepción; evidencia no verificada |
| Seguridad | Brandon/Programador | 2026-10-13 UTC | Aceptación global del solicitante en esta conversación | Aprobado por excepción; cero críticos no acreditado |
| Operación | Brandon/Programador | 2026-10-13 UTC | Aceptación global del solicitante en esta conversación | Aprobado por excepción; evidencia no verificada |
| Dueño del negocio | Brandon/Programador | 2026-10-13 UTC | Aceptación global del solicitante en esta conversación | Aprobado por excepción; representación no verificada |

**GO/NO GO de preparación del piloto:** GO **documental por aceptación expresa del solicitante**, solo para continuar al despliegue controlado de F10.10. No hay GO para tráfico de clientes. La apertura requiere smoke tests productivos, revisión de hallazgos críticos y decisión operativa en F10.10. Las pruebas locales con datos sintéticos no sustituyen verificaciones de la cuenta piloto, DNS/TLS, presupuesto, alertas, respaldo o entrega de WhatsApp.
