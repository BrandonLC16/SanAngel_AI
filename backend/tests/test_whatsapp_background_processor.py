import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import MessageProcessingError
from backend.app.core.logging import WHATSAPP_BACKGROUND_LOGGER_NAME
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.whatsapp_background_processor import WhatsAppBackgroundProcessor


class RecordingOrchestrator:
    def __init__(
        self,
        *,
        failing_ids: set[str] | None = None,
        blocker: asyncio.Event | None = None,
    ) -> None:
        self.failing_ids = failing_ids or set()
        self.blocker = blocker
        self.calls: list[str] = []

    async def process_message(self, message: InboundMessage) -> bool:
        self.calls.append(message.external_message_id)
        if self.blocker is not None:
            await self.blocker.wait()
        if message.external_message_id in self.failing_ids:
            raise MessageProcessingError("test-only-private-background-failure-marker")
        return True


def make_settings() -> Settings:
    return Settings(
        openai_api_key="test-only-openai-credential-placeholder",
        _env_file=None,
    )


def make_message(message_id: str, text: str) -> InboundMessage:
    return InboundMessage(
        external_message_id=message_id,
        sender_id="5215550000001",
        text=text,
        timestamp=1720000000,
    )


def processor_for(orchestrator: RecordingOrchestrator) -> WhatsAppBackgroundProcessor:
    @asynccontextmanager
    async def use_orchestrator(_settings: Settings) -> AsyncIterator[RecordingOrchestrator]:
        yield orchestrator

    return WhatsAppBackgroundProcessor(use_orchestrator)  # type: ignore[arg-type]


def test_background_processor_continues_batch_after_failure_without_retrying(
    caplog: pytest.LogCaptureFixture,
) -> None:
    private_text = "test-only-private-background-text-marker"
    failing_id = "wamid.test-only-failing-id"
    successful_id = "wamid.test-only-success-id"
    orchestrator = RecordingOrchestrator(failing_ids={failing_id})
    processor = processor_for(orchestrator)

    with caplog.at_level(logging.INFO, logger=WHATSAPP_BACKGROUND_LOGGER_NAME):
        asyncio.run(
            processor.process_messages(
                (
                    make_message(failing_id, private_text),
                    make_message(successful_id, "segundo mensaje privado"),
                ),
                make_settings(),
                "safe-background-request-id",
            )
        )

    assert orchestrator.calls == [failing_id, successful_id]
    assert caplog.text.count("background_message_processing_failed") == 1
    assert "error_category=message_processing_failed" in caplog.text
    assert "message_count=2 failed_count=1" in caplog.text
    assert "safe-background-request-id" in caplog.text
    assert failing_id not in caplog.text
    assert successful_id not in caplog.text
    assert private_text not in caplog.text
    assert "test-only-private-background-failure-marker" not in caplog.text


def test_background_factory_failure_is_swallowed_and_logged_without_private_detail(
    caplog: pytest.LogCaptureFixture,
) -> None:
    private_detail = "test-only-private-factory-failure-marker"

    @asynccontextmanager
    async def failing_factory(_settings: Settings) -> AsyncIterator[RecordingOrchestrator]:
        raise RuntimeError(private_detail)
        yield RecordingOrchestrator()

    processor = WhatsAppBackgroundProcessor(failing_factory)  # type: ignore[arg-type]

    with caplog.at_level(logging.ERROR, logger=WHATSAPP_BACKGROUND_LOGGER_NAME):
        result = asyncio.run(
            processor.process_messages(
                (make_message("wamid.test-only-id", "texto privado"),),
                make_settings(),
                "safe-factory-request-id",
            )
        )

    assert result is None
    assert "background_message_batch_failed" in caplog.text
    assert "error_category=unhandled_exception" in caplog.text
    assert "safe-factory-request-id" in caplog.text
    assert private_detail not in caplog.text
    assert "texto privado" not in caplog.text


def test_background_cancellation_is_logged_and_propagated(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def cancel_processing() -> None:
        blocker = asyncio.Event()
        orchestrator = RecordingOrchestrator(blocker=blocker)
        processor = processor_for(orchestrator)
        task = asyncio.create_task(
            processor.process_messages(
                (make_message("wamid.test-only-id", "texto privado"),),
                make_settings(),
                "safe-cancelled-request-id",
            )
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    with caplog.at_level(logging.WARNING, logger=WHATSAPP_BACKGROUND_LOGGER_NAME):
        asyncio.run(cancel_processing())

    assert "background_message_batch_cancelled" in caplog.text
    assert "safe-cancelled-request-id" in caplog.text
    assert "wamid.test-only-id" not in caplog.text
    assert "texto privado" not in caplog.text
