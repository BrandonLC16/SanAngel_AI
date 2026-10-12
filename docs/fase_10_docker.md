# F10.6 — Docker seguro

## Imágenes comunes

El backend (`Dockerfile`) y el panel servido por Caddy (`Dockerfile.frontend`) se construyen una
sola vez y se usan sin cambios para las siete sucursales. Las bases son imágenes fijadas por
versión y digest; Python se instala desde `requirements-prod.lock` con versiones y hashes, y el
panel usa `npm ci` con `frontend/package-lock.json`. El build no recibe argumentos de sucursal ni
secretos. `.dockerignore` deja entrar solo los archivos necesarios para compilar y ejecutar.

```powershell
docker build --build-arg SOURCE_DATE_EPOCH=0 --platform linux/amd64 -f Dockerfile -t sanangel-backend:<version> .
docker build --build-arg SOURCE_DATE_EPOCH=0 --platform linux/amd64 -f Dockerfile.frontend -t sanangel-panel:<version> .
```

`SOURCE_DATE_EPOCH=0` fija la fecha de creación de la imagen. Dos builds sin caché dieron el
mismo contenido de aplicación/dependencias y los mismos archivos estáticos; los IDs locales de
imagen aún pueden diferir por marcas de tiempo de capas `RUN`. Para comparar el digest de un
artefacto OCI normalizado, exportar a un archivo temporal **fuera** del repositorio y repetir con
`--no-cache`:

```powershell
docker buildx build --build-arg SOURCE_DATE_EPOCH=0 --output "type=oci,dest=<archivo-backend-fuera-repo>.tar,rewrite-timestamp=true" --platform linux/amd64 -f Dockerfile .
docker buildx build --build-arg SOURCE_DATE_EPOCH=0 --output "type=oci,dest=<archivo-panel-fuera-repo>.tar,rewrite-timestamp=true" --platform linux/amd64 -f Dockerfile.frontend .
```

En la validación F10.6, ambos digests OCI coincidieron entre build con caché y sin caché. Al
cambiar dependencias Python de
producción, regenerar el lock con `uv pip compile` para Python 3.14 y Linux x86_64, solo wheels y
hashes; revisar el diff, auditarlo con `pip-audit --require-hashes -r requirements-prod.lock` y
reconstruir. Al cambiar dependencias del panel,
actualizar su lockfile y ejecutar `npm audit --prefix frontend`. CI compila ambas imágenes y
comprueba usuario y healthcheck. Las imágenes se fijan por digest en despliegues reales tras
publicarlas en un registro controlado; la etiqueta de ejemplo es local y mutable.

Comando de regeneración usado con `uv==0.12.24`:

```powershell
uv --no-config pip compile pyproject.toml --python-version 3.14 --python-platform x86_64-unknown-linux-gnu --only-binary :all: --generate-hashes --index-url https://pypi.org/simple --output-file requirements-prod.lock
```

## Una instalación por sucursal

`deploy/compose.branch.yml` es una plantilla: iniciar **siete proyectos Compose distintos**, cada
uno con su `ASSISTANT_BRANCH_CODE`, `GREEN_API_INSTANCE_ID`, dominio, puertos o host propios,
directorio externo de secretos y volúmenes nombrados independientes. Usar exactamente los mismos
digests de backend y panel en los siete archivos de entorno de despliegue. No copiar perfiles,
archivos SQLite ni secretos al contexto de build. Aprovisionar el perfil correspondiente mediante
el flujo de importación ya existente, comprobando que su código coincida con el alcance de la
instalación. La DB vive en `branch_data`, fuera de la imagen; certificados de Caddy en
`caddy_data` y `caddy_config`.

Ejemplo para **una** instalación, con valores no secretos en un archivo externo al repositorio:

```text
BACKEND_IMAGE=registry.example/sanangel-backend@sha256:<digest-revisado>
PANEL_IMAGE=registry.example/sanangel-panel@sha256:<digest-revisado>
ASSISTANT_BRANCH_CODE=<codigo-asignado>
GREEN_API_INSTANCE_ID=<instancia-asignada>
SECRETS_DIR_HOST=<ruta-absoluta-del-montaje-del-secret-manager>
PUBLIC_DOMAIN=<dominio-de-la-sucursal>
PUBLIC_HTTP_PORT=80
PUBLIC_HTTPS_PORT=443
```

```powershell
docker compose --env-file <archivo-externo> -p <proyecto-unico> -f deploy/compose.branch.yml config --quiet
docker compose --env-file <archivo-externo> -p <proyecto-unico> -f deploy/compose.branch.yml up -d
docker compose --env-file <archivo-externo> -p <proyecto-unico> -f deploy/compose.branch.yml ps
```

El gestor de secretos debe montar archivos legibles por UID 10001 y no incluirlos en variables de
entorno ni en la imagen. El backend exige los cinco archivos documentados en
`docs/fase_10_secrets.md`; solo él monta ese directorio, de solo lectura. Cada despliegue debe
tener credenciales propias. La configuración de sucursal queda en el entorno **de ejecución**
del backend. Compose crea un volumen SQLite exclusivo por nombre de proyecto; no compartir ese
volumen entre instalaciones. La rotación de secretos sigue el procedimiento de F10.3.

Desde F10.8, cada proyecto Compose incluye un `worker` sin puerto publicado que usa exactamente
la imagen backend, el volumen SQLite y el montaje de secretos de **esa** sucursal. El webhook
confirma solo después del commit de un job cifrado y el worker lo procesa fuera de la solicitud.
Aplicar la migración `20261012_0015` antes de levantar esta versión. El healthcheck del worker
comprueba acceso a su cola, pero se deben vigilar además profundidad y jobs inciertos conforme a
la [guía de F10.8](fase_10_cola.md). No añadir una segunda instancia del worker a una sucursal
sin medir la carga; el reclamo atómico preserva la idempotencia si hubiera concurrencia.

## Red y comprobación

Caddy y backend comparten solo el espacio de red de la instalación. FastAPI escucha en
`127.0.0.1:8000`, sin puerto publicado; Caddy termina TLS y sirve panel/API desde el mismo
origen. El backend confía únicamente en la declaración HTTPS del proxy local exacto
`127.0.0.1`; Uvicorn no interpreta cabeceras de proxy automáticamente. Docker publica los
puertos 80/443 del host hacia 8080/8443 internos para permitir que ambos procesos corran sin
root ni `NET_BIND_SERVICE`. Con puertos de host alternos para pruebas, la redirección HTTP
anuncia el puerto HTTPS estándar; probar HTTPS en el puerto alterno de forma explícita.

Ambas imágenes ejecutan como UID/GID 10001, con filesystem raíz de solo lectura, sin
capabilities y con `no-new-privileges` en Compose. El backend verifica `/health` por loopback
con la cabecera HTTPS que Caddy aporta; el panel verifica que el listener TLS esté abierto.
Comprobar además una petición HTTPS a `/health`, el HTML/CSP del panel y la redirección HTTP.
El healthcheck del panel verifica disponibilidad del listener, no vigencia del certificado ni
entrega externa del webhook. DNS, certificados públicos, conectividad real con proveedores y
aislamiento operativo de los siete hosts deben validarse en cada despliegue.
