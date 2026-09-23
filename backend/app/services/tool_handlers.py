"""Explicit, read-only implementations of validated tool calls."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ProductNotFoundError, ProductPriceNotFoundError
from backend.app.schemas.commercial import BranchInfo, ProductPriceInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.commercial_query_service import CommercialQueryService
from backend.app.services.faq_response_policy import (
    FAQAnswer,
    FAQFallback,
    FAQResponsePolicy,
    HumanHelpProposal,
    HumanHelpReason,
    request_human_help,
)
from backend.app.services.faq_service import FAQService
from backend.app.services.tool_contracts import (
    GetBranchInfoArguments,
    GetProductPriceArguments,
    RequestHumanHelpArguments,
    SearchFAQArguments,
    ToolCallValidationError,
    ToolName,
    ValidatedToolCall,
)

ArgumentsT = TypeVar("ArgumentsT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class ProductPriceNotFoundResult:
    """One indistinguishable outcome for missing, inactive or unpriced products."""

    status: Literal["not_found"] = "not_found"


class ToolHandlers:
    """Use only the backend-bound branch; each public method implements one tool."""

    def __init__(
        self, session: Session, faq_source_path: Path, *, branch_scope: BranchScope
    ) -> None:
        if not isinstance(branch_scope, BranchScope):
            raise ToolCallValidationError("trusted branch scope is required")
        self._session = session
        self._faq_source_path = faq_source_path
        self._branch_scope = branch_scope

    def get_product_price(
        self, call: ValidatedToolCall
    ) -> ProductPriceInfo | ProductPriceNotFoundResult:
        args = self._arguments(call, "get_product_price", GetProductPriceArguments)
        service = CommercialQueryService(self._session, branch_scope=self._branch_scope)
        try:
            return service.get_product_price(args.product_id, unit=args.unit)
        except (ProductNotFoundError, ProductPriceNotFoundError):
            return ProductPriceNotFoundResult()

    def get_branch_info(self, call: ValidatedToolCall) -> BranchInfo:
        self._arguments(call, "get_branch_info", GetBranchInfoArguments)
        service = CommercialQueryService(self._session, branch_scope=self._branch_scope)
        return service.get_branch_info()

    def search_faq(self, call: ValidatedToolCall) -> FAQAnswer | FAQFallback:
        args = self._arguments(call, "search_faq", SearchFAQArguments)
        service = FAQService(self._faq_source_path, branch_scope=self._branch_scope)
        return FAQResponsePolicy(service).resolve(args.query)

    def request_human_help(self, call: ValidatedToolCall) -> HumanHelpProposal:
        args = self._arguments(call, "request_human_help", RequestHumanHelpArguments)
        return request_human_help(HumanHelpReason(args.reason))

    def _arguments(
        self, call: ValidatedToolCall, name: ToolName, argument_type: type[ArgumentsT]
    ) -> ArgumentsT:
        if (
            not isinstance(call, ValidatedToolCall)
            or call.name != name
            or type(call.arguments) is not argument_type
            or call.branch_scope != self._branch_scope
        ):
            raise ToolCallValidationError("tool call does not match the configured handler")
        return call.arguments
