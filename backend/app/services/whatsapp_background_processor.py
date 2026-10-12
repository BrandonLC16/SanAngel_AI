import asyncio
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager

from backend.app.core.config import Settings
from backend.app.core.exceptions import ApplicationError
from backend.app.core.logging import whatsapp_background_logger
from backend.app.core.observability import request_reference
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.message_orchestrator import MessageOrchestrator

MessageOrchestratorFactory = Callable[
    [Settings],
    AbstractAsyncContextManager[MessageOrchestrator],
]


class WhatsAppBackgroundProcessor:
    """Run authenticated message batches after ACK with sanitized failure reporting."""

    def __init__(self, orchestrator_factory: MessageOrchestratorFactory) -> None:
        self._orchestrator_factory = orchestrator_factory

    async def process_messages(
        self,
        messages: Sequence[InboundMessage],
        settings: Settings,
        request_id: str,
    ) -> None:
        failed_count = 0
        safe_ref = request_reference(request_id)
        try:
            async with self._orchestrator_factory(settings) as orchestrator:
                for message in messages:
                    try:
                        await orchestrator.process_message(message)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        failed_count += 1
                        whatsapp_background_logger.error(
                            "background_message_processing_failed request_ref=%s "
                            "error_category=%s source_error_category=%s "
                            "provider_code=%s provider_subcode=%s",
                            safe_ref,
                            self._error_category(exc),
                            self._safe_source_category(exc),
                            self._safe_provider_code(getattr(exc, "provider_code", None)),
                            self._safe_provider_code(getattr(exc, "provider_subcode", None)),
                        )
        except asyncio.CancelledError:
            whatsapp_background_logger.warning(
                "background_message_batch_cancelled request_ref=%s",
                safe_ref,
            )
            raise
        except Exception as exc:
            whatsapp_background_logger.error(
                "background_message_batch_failed request_ref=%s error_category=%s",
                safe_ref,
                self._error_category(exc),
            )
            return

        whatsapp_background_logger.info(
            "background_message_batch_completed request_ref=%s message_count=%d failed_count=%d",
            safe_ref,
            len(messages),
            failed_count,
        )

    @staticmethod
    def _error_category(exc: Exception) -> str:
        if isinstance(exc, ApplicationError):
            return exc.error_code
        return "unhandled_exception"

    @staticmethod
    def _safe_source_category(exc: Exception) -> str:
        value = getattr(exc, "source_error_code", None)
        return (
            value
            if isinstance(value, str)
            and value in {"ai_service_unavailable", "whatsapp_service_unavailable"}
            else "none"
        )

    @staticmethod
    def _safe_provider_code(value: object) -> int | str:
        return value if type(value) is int and 0 <= value <= 99_999_999 else "none"
