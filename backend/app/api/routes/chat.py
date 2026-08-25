from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_chat_service
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1", tags=["internal-development"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat interno de desarrollo",
    description="Endpoint interno para desarrollo y pruebas; no es el canal final del cliente.",
)
async def chat(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    answer = await service.answer(payload.message)
    return ChatResponse(answer=answer)
