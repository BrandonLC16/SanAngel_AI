"""Run one branch's durable WhatsApp inbox worker or inspect safe counts."""

import argparse
import asyncio

from backend.app.api.dependencies import create_message_orchestrator
from backend.app.core.config import get_conversation_identity_settings, get_settings
from backend.app.db.session import get_database_session_factory
from backend.app.services.branch_scope import BranchScope
from backend.app.services.whatsapp_inbound_queue import PersistentInboundQueue
from backend.app.services.whatsapp_inbound_worker import WhatsAppInboundWorker


async def _run(*, once: bool, status: bool) -> None:
    settings = get_settings()
    queue = PersistentInboundQueue(
        get_database_session_factory(),
        branch_scope=BranchScope.from_settings(settings),
        identity_settings=get_conversation_identity_settings(),
    )
    if status:
        counts = await queue.counts()
        print(" ".join(f"{name}={counts[name]}" for name in ("pending", "processing", "uncertain")))
        return
    worker = WhatsAppInboundWorker(queue, create_message_orchestrator, settings)
    if once:
        print(f"processed={int(await worker.run_once())}")
    else:
        await worker.run_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process the scoped WhatsApp inbox")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args(argv)
    if args.once and args.status:
        parser.error("choose one mode")
    try:
        asyncio.run(_run(once=args.once, status=args.status))
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("No se pudo ejecutar el worker de WhatsApp.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
