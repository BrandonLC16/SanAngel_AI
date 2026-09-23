"""Closed, bounded dispatcher for the four validated read-only tools."""

import math
from collections.abc import Callable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from threading import BoundedSemaphore
from time import monotonic
from types import MappingProxyType

from sqlalchemy.orm import Session

from backend.app.core.config import AssistantSettings
from backend.app.core.exceptions import ToolExecutionTimeoutError
from backend.app.schemas.commercial import BranchInfo, ProductPriceInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.faq_response_policy import FAQAnswer, FAQFallback, HumanHelpProposal
from backend.app.services.tool_contracts import (
    ToolCallValidationError,
    ToolName,
    ValidatedToolCall,
    validate_tool_call,
)
from backend.app.services.tool_handlers import ProductPriceNotFoundResult, ToolHandlers

DEFAULT_TOOL_TIMEOUT_SECONDS = 3.0
MAX_TOOL_TIMEOUT_SECONDS = 30.0
MAX_TOOL_WORKERS = 4

type ToolResult = (
    ProductPriceInfo
    | ProductPriceNotFoundResult
    | BranchInfo
    | FAQAnswer
    | FAQFallback
    | HumanHelpProposal
)
type HandlerMethod = Callable[[ToolHandlers, ValidatedToolCall], ToolResult]

_HANDLERS: Mapping[ToolName, HandlerMethod] = MappingProxyType(
    {
        "get_product_price": ToolHandlers.get_product_price,
        "get_branch_info": ToolHandlers.get_branch_info,
        "search_faq": ToolHandlers.search_faq,
        "request_human_help": ToolHandlers.request_human_help,
    }
)
_WORKERS = ThreadPoolExecutor(max_workers=MAX_TOOL_WORKERS, thread_name_prefix="scoped-tool")
_WORKER_SLOTS = BoundedSemaphore(MAX_TOOL_WORKERS)


def _release_slot(_future: Future[ToolResult]) -> None:
    _WORKER_SLOTS.release()


class ToolDispatcher:
    """Validate model input, then run one mapped handler in a worker-owned DB session."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        faq_source_path: Path,
        assistant_settings: AssistantSettings,
        timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(assistant_settings, AssistantSettings):
            raise ToolCallValidationError("trusted branch configuration is required")
        if (
            type(timeout_seconds) not in (int, float)
            or not 0 < timeout_seconds <= MAX_TOOL_TIMEOUT_SECONDS
            or not math.isfinite(timeout_seconds)
        ):
            raise ValueError("tool timeout must be finite and between 0 and 30 seconds")
        self._session_factory = session_factory
        self._faq_source_path = faq_source_path
        self._assistant_settings = assistant_settings
        self._branch_scope = BranchScope.from_settings(assistant_settings)
        self._timeout_seconds = float(timeout_seconds)

    @property
    def branch_scope(self) -> BranchScope:
        """Expose the immutable backend scope for composition checks."""

        return self._branch_scope

    def dispatch(self, name: str, arguments_json: str) -> ToolResult:
        """Reject unknown names before parsing, with no dynamic attribute or SQL execution."""

        method = _HANDLERS.get(name) if isinstance(name, str) else None
        if method is None:
            raise ToolCallValidationError("unsupported tool")
        call = validate_tool_call(name, arguments_json, assistant_settings=self._assistant_settings)
        deadline = monotonic() + self._timeout_seconds
        if not _WORKER_SLOTS.acquire(timeout=self._timeout_seconds):
            raise ToolExecutionTimeoutError() from None
        try:
            future = _WORKERS.submit(self._execute, method, call)
        except RuntimeError:
            _WORKER_SLOTS.release()
            raise ToolExecutionTimeoutError() from None
        future.add_done_callback(_release_slot)
        try:
            return future.result(timeout=max(0.0, deadline - monotonic()))
        except FutureTimeoutError:
            future.cancel()
            raise ToolExecutionTimeoutError() from None

    def _execute(self, method: HandlerMethod, call: ValidatedToolCall) -> ToolResult:
        with self._session_factory() as session:
            handlers = ToolHandlers(
                session,
                self._faq_source_path,
                branch_scope=self._branch_scope,
            )
            return method(handlers, call)
