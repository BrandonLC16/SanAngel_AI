from fastapi import FastAPI

from backend.app.api.routes.health import router as health_router

app = FastAPI(title="Carniceria AI Chatbot")
app.include_router(health_router)
