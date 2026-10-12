"""Measure 50 synthetic authenticated webhooks against the real SQLite inbox."""

import asyncio
import logging
import os
import statistics
import tempfile
import time
from pathlib import Path

from alembic import command
from alembic.config import Config

from backend.app.api.dependencies import get_inbound_queue_factory
from backend.app.core.config import ConversationIdentitySettings, get_database_settings
from backend.app.db.models.branch import Branch
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.services.branch_scope import BranchScope
from backend.app.services.whatsapp_inbound_queue import PersistentInboundQueue
from backend.tests.test_whatsapp_webhook import (
    authorization_headers,
    make_application,
    send_webhook,
    text_message_payload,
)

ROOT = Path(__file__).resolve().parents[1]


async def measure(queue: PersistentInboundQueue) -> tuple[float, float, float, float]:
    app = make_application()
    app.dependency_overrides[get_inbound_queue_factory] = lambda: lambda _settings: queue
    latencies: list[float] = []
    started = time.perf_counter()
    for index in range(50):
        body = text_message_payload(
            "5215550000001@c.us", "synthetic capacity probe", message_id=f"capacity-{index:04d}"
        )
        request_started = time.perf_counter()
        response = await send_webhook(app, body, authorization_headers())
        if response.status_code != 200:
            raise RuntimeError("synthetic webhook was not acknowledged")
        latencies.append((time.perf_counter() - request_started) * 1_000)
    elapsed = time.perf_counter() - started
    if (await queue.counts())["pending"] != 50:
        raise RuntimeError("synthetic webhook work was not persisted")
    ordered = sorted(latencies)
    return statistics.median(ordered), ordered[47], max(ordered), 50 / elapsed


def main() -> int:
    old_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with tempfile.TemporaryDirectory(prefix="sanangel-webhook-measure-") as temporary:
            database_path = Path(temporary) / "capacity.db"
            os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{database_path.as_posix()}"
            get_database_settings.cache_clear()
            command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
            engine = create_database_engine(os.environ["DATABASE_URL"])
            try:
                sessions = create_database_session_factory(engine)
                with sessions.begin() as session:
                    session.add(
                        Branch(
                            code="sucursal-demo",
                            name="Demo",
                            address="Calle 1",
                            business_hours="Lunes",
                        )
                    )
                identity = ConversationIdentitySettings(
                    assistant_branch_code="sucursal-demo",
                    conversation_identity_key="test-only-queue-identity-key-123456789",
                    _env_file=None,
                )
                queue = PersistentInboundQueue(
                    sessions,
                    branch_scope=BranchScope("sucursal-demo"),
                    identity_settings=identity,
                )
                p50, p95, maximum, rate = asyncio.run(measure(queue))
            finally:
                engine.dispose()
                get_database_settings.cache_clear()
    finally:
        logging.disable(old_disable)
    print(
        f"synthetic_count=50 p50_ms={p50:.2f} p95_ms={p95:.2f} "
        f"max_ms={maximum:.2f} rate_rps={rate:.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
