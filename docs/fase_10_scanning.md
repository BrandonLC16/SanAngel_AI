# F10.5 — Auditoría de dependencias y secretos

## Comprobaciones en CI

`.github/workflows/security.yml` corre en cada pull request, push a `main`, despacho manual y
una vez por semana. Los tres jobs fallan ante un hallazgo o un error del scanner:

| Job | Comprobación |
|---|---|
| `secrets` | Gitleaks 8.30.1 sobre toda la historia Git disponible, con `fetch-depth: 0`. |
| `python` | Tests, Ruff, `pip check` y `pip-audit` del entorno resuelto con dependencias de desarrollo. |
| `frontend` | `npm ci` desde el lockfile, tests, build y `npm audit` de todas las dependencias. |

El binario Linux de Gitleaks se descarga desde su release oficial y se compara con un SHA-256
fijado antes de ejecutarlo. Los Actions se fijan por commit. El workflow usa token de solo
lectura, no persiste credenciales de checkout, no carga secretos de aplicación, no usa
`pull_request_target` y no sube reportes ni artefactos. `scripts.scan_secrets` suprime toda la
salida del scanner y comunica solo éxito o fallo; Gitleaks recibe además `--redact=100`.
Nunca convertir un reporte crudo de secretos en artefacto, comentario de PR o log de CI.

`pip-audit` consulta avisos para las versiones instaladas en un entorno limpio de CI. El paquete
local `carniceria-ai-chatbot` no está publicado en PyPI y puede aparecer como no auditable;
sus dependencias instaladas sí se auditan. Python aún no tiene lockfile: cada ejecución resuelve
de nuevo los rangos de `pyproject.toml`. Auditar también el conjunto exacto que se despliegue.
`npm audit` usa el `frontend/package-lock.json` versionado e incluye dependencias de desarrollo.
La primera auditoría de F10.5 encontró `source-map-js` 1.2.1 con un aviso alto; el lockfile se
actualizó a 1.2.2. También se detectó `pip` 26.1.2 en el entorno local; CI fija 26.2.0.

## Ejecución local

Desde un entorno aislado con la aplicación y las dependencias de desarrollo instaladas:

```powershell
python -m pip install --upgrade pip==26.2.0
python -m pip install pip-audit==2.10.1
python -m pip_audit --local --progress-spinner off
npm ci --prefix frontend --ignore-scripts --no-audit
npm audit --prefix frontend
```

Descargar Gitleaks desde su [release oficial](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1),
verificar el SHA-256 de la plataforma y ejecutar, con la historia Git completa:

```powershell
python -m scripts.scan_secrets --scanner <ruta-al-binario-gitleaks>
```

Un fallo del wrapper no imprime el secreto, la línea, el archivo ni la salida de diagnóstico.
Para investigar un hallazgo, usar un entorno local con acceso restringido y no copiar el valor
en tickets, capturas, logs, PR o documentación. Si puede ser una credencial real, revocarla
primero y seguir el [procedimiento de compromiso y rotación](fase_10_secrets.md); después retirar
la exposición del código y coordinar la limpieza de historial cuando proceda. No añadir una
exclusión general ni reescribir historial sin revisión del impacto.

## Política de actualización

Dependabot abre propuestas semanales separadas para `pip`, `npm` y GitHub Actions. Una persona
revisa el aviso, la versión corregida, la compatibilidad y los resultados del workflow antes
de integrar; no hay merge automático. Para un aviso alto o crítico, detener integración y
despliegue del componente afectado y revisar el mismo día hábil; para moderado o bajo, revisar
en el ciclo semanal. El pipeline bloquea cualquier severidad conocida y no contiene supresiones.
Revisar mensualmente las versiones fijadas de Gitleaks, `pip-audit`, `pip` y Node en el workflow;
Dependabot no cambia automáticamente los comandos `run` ni el SHA-256 del binario descargado.
Si no existe corrección, mantener el bloqueo, documentar alcance y mitigación fuera de los logs
de CI y decidir explícitamente cuándo se puede volver a desplegar. Un falso positivo requiere
evidencia y una excepción estrecha, revisada y con fecha de expiración.

Actualizar `pyproject.toml` o `frontend/package-lock.json` junto con los tests afectados;
volver a auditar el entorno resuelto. El propietario del repositorio debe configurar los tres
jobs como checks requeridos para proteger `main` y activar alertas de dependencias en GitHub.
Esas opciones remotas no se cambian desde este repositorio y deben verificarse al habilitar CI.
