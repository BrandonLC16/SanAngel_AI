# Carniceria AI Chatbot

Backend en Python para un chatbot de atencion al cliente de una cadena de carnicerias.
El proyecto se construye por fases para mantener los datos comerciales en fuentes
deterministicas y evitar que el modelo invente precios, existencias, direcciones, horarios,
promociones o pedidos.

## Estado actual

F1.1 y F1.2 inicializan el repositorio e implementan la configuracion central validada.
Todavia no se implementan FastAPI, endpoints ni la integracion con OpenAI; corresponden a
tareas posteriores de la Fase 1.

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

`backend.app.core.config.Settings` es el unico punto de lectura de variables de entorno. La
configuracion se valida al solicitarla mediante `get_settings()`; importar el modulo no lee ni
imprime secretos y tampoco realiza llamadas externas.

Valores y limites iniciales:

- `OPENAI_API_KEY` es obligatoria y se mantiene como valor secreto;
- `OPENAI_MODEL` es configurable y usa `gpt-5.6` por defecto;
- `OPENAI_STORE_RESPONSES` usa `false` por defecto;
- `OPENAI_TIMEOUT_SECONDS` acepta valores mayores a 0 y hasta 120 segundos;
- `CHAT_MAX_MESSAGE_CHARS` acepta valores entre 1 y 10000, con 2000 por defecto.

Si falta configuración obligatoria, la aplicación genera un error de validación sin incluir el
valor de ninguna credencial.

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
