# Carniceria AI Chatbot

Backend en Python para un chatbot de atencion al cliente de una cadena de carnicerias.
El proyecto se construye por fases para mantener los datos comerciales en fuentes
deterministicas y evitar que el modelo invente precios, existencias, direcciones, horarios,
promociones o pedidos.

## Estado actual

F1.1-F1.4 inicializan el repositorio, implementan la configuracion central validada y crean la
aplicacion FastAPI con health check, errores HTTP seguros, request ID, logging minimo y CORS
configurable. Todavia no se implementan el endpoint de chat ni la integracion con OpenAI;
corresponden a tareas posteriores de la Fase 1.

## Health check

`GET /health` responde sin requerir credenciales de proveedor ni llamar a servicios externos:

```json
{
  "status": "ok",
  "service": "carniceria-ai-chatbot"
}
```

## Requisitos

- Python 3.12, 3.13 o 3.14.
- `pip` disponible mediante `python -m pip`.

## Preparacion local

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Completa `OPENAI_API_KEY` solamente en el archivo local `.env` cuando una tarea posterior
requiera una prueba manual. Nunca guardes una clave real en archivos versionados.

## Configuracion

`backend.app.core.config` es el unico punto de lectura de variables de entorno. `HttpSettings`
carga al iniciar solo configuracion HTTP no sensible; `Settings` agrega la credencial y opciones
de OpenAI cuando un servicio futuro las solicite. Ninguno imprime secretos ni realiza llamadas
externas.

Valores y limites iniciales:

- `OPENAI_API_KEY` es obligatoria y se mantiene como valor secreto;
- `OPENAI_MODEL` es configurable y usa `gpt-5.6` por defecto;
- `OPENAI_STORE_RESPONSES` usa `false` por defecto;
- `OPENAI_TIMEOUT_SECONDS` acepta valores mayores a 0 y hasta 120 segundos;
- `CORS_ALLOWED_ORIGINS` acepta una lista separada por comas de origenes HTTP/HTTPS exactos;
- `CHAT_MAX_MESSAGE_CHARS` acepta valores entre 1 y 10000, con 2000 por defecto.

Si falta configuración obligatoria, la aplicación genera un error de validación sin incluir el
valor de ninguna credencial.

Sin `CORS_ALLOWED_ORIGINS`, el acceso desde navegador queda deshabilitado. Cada origen debe
contener solo esquema, host y puerto opcional; no se permiten comodines, paths, credenciales,
query strings ni duplicados. `.env.example` incluye exclusivamente los origenes locales de
desarrollo.

## Frontera HTTP

- `X-Request-ID` se conserva si es valido o se genera de forma segura y se devuelve en la
  respuesta;
- las excepciones internas se convierten a un JSON estable con codigo publico y request ID;
- los errores inesperados responden HTTP 500 sin traceback ni detalle interno;
- los logs incluyen request ID, metodo, plantilla de endpoint, estado, duracion y categoria;
- no se registran body, query string, headers ni `Authorization`.

## Validaciones disponibles

```powershell
pytest
ruff check .
ruff format --check .
```

## Estructura base

```text
backend/
  app/
    api/routes/
    core/
    prompts/
    schemas/
    services/
  tests/
docs/
```

Consulta `docs/fase_1_diseno.md` para el diseño de la fase activa y
`plan_de_trabajo.md` para el estado oficial de cada tarea.

## Seguridad

- La API key de OpenAI será utilizada solo por el backend y se cargará desde el entorno.
- `.env` y sus variantes locales están ignorados; `.env.example` no contiene secretos.
- Las pruebas automatizadas normales no deben invocar servicios externos ni consumir créditos.
- CORS utiliza origenes explicitos y no permite `*`, incluso fuera de produccion.
