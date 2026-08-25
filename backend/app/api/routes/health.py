from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return the minimal process health status without external dependencies."""

    return {"status": "ok", "service": "carniceria-ai-chatbot"}
