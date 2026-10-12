"""Process durable inbound work one message at a time without automatic resend."""

import asyncio

from backend.app.core.config import Settings
from backend.app.core.logging import whatsapp_background_logger
from backend.app.services.whatsapp_background_processor import MessageOrchestratorFactory
from backend.app.services.whatsapp_inbound_queue import PersistentInboundQueue


class WhatsAppInboundWorker:
    def __init__(
        self,
        queue: PersistentInboundQueue,
        orchestrator_factory: MessageOrchestratorFactory,
        settings: Settings,
    ) -> None:
        self._queue = queue
        self._orchestrator_factory = orchestrator_factory
        self._settings = settings

    async def run_once(self) -> bool:
        job = await self._queue.claim_next()
        if job is None:
            return False
        try:
            async with self._orchestrator_factory(self._settings) as orchestrator:
                await orchestrator.process_message(job.message)
            await self._queue.complete(job.id)
        except asyncio.CancelledError:
            await asyncio.shield(self._queue.mark_uncertain(job.id))
            raise
        except Exception:
            # The send may have started. Never replay without reconciling GreenAPI and receipts.
            await self._queue.mark_uncertain(job.id)
            whatsapp_background_logger.error(
                "inbound_job_uncertain error_category=processing_failed"
            )
        return True

    async def run_forever(self, *, poll_seconds: float = 0.25) -> None:
        while True:
            try:
                worked = await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                whatsapp_background_logger.error(
                    "inbound_worker_unavailable error_category=queue_failed"
                )
                await asyncio.sleep(1)
                continue
            if not worked:
                await asyncio.sleep(poll_seconds)
