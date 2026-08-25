# Carniceria AI Chatbot

Backend en Python para un chatbot de atencion al cliente de una cadena de carnicerias.
El proyecto se construye por fases para mantener los datos comerciales en fuentes
deterministicas y evitar que el modelo invente precios, existencias, direcciones, horarios,
promociones o pedidos.

## Estado actual

F1.1 inicializa el repositorio y su estructura. Todavia no se implementan FastAPI, la
configuracion central, endpoints ni la integracion con OpenAI; corresponden a tareas
posteriores de la Fase 1.

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
