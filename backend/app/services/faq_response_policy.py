"""Deterministic FAQ answer policy with safe unresolved outcomes."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from backend.app.services.faq_service import FAQService, normalize_faq_question

UNKNOWN_FALLBACK = (
    "No tengo una respuesta confirmada para esa pregunta. "
    "El personal de la sucursal puede ayudarte a verificarla."
)
AMBIGUOUS_FALLBACK = (
    "No puedo identificar una respuesta confirmada. "
    "Reformula tu pregunta o consulta al personal de la sucursal."
)


class HumanHelpReason(StrEnum):
    FAQ_UNKNOWN = "faq_unknown"
    FAQ_AMBIGUOUS = "faq_ambiguous"


@dataclass(frozen=True, slots=True)
class HumanHelpProposal:
    """Conceptual handoff intent; no person has been contacted."""

    reason: HumanHelpReason
    action: Literal["request_human_help"] = "request_human_help"
    executed: Literal[False] = False


@dataclass(frozen=True, slots=True)
class FAQAnswer:
    """Text from one exact FAQ row, identified as source data."""

    text: str
    source_question: str
    source: Literal["faq"] = "faq"
    trust_level: Literal["untrusted_source"] = "untrusted_source"


@dataclass(frozen=True, slots=True)
class FAQFallback:
    """Fixed response when no single exact FAQ answer can be confirmed."""

    text: str
    human_help: HumanHelpProposal


def request_human_help(reason: HumanHelpReason) -> HumanHelpProposal:
    """Represent a future handoff request without dispatching or storing personal data."""

    if not isinstance(reason, HumanHelpReason):
        raise ValueError("unsupported human help reason")
    return HumanHelpProposal(reason=reason)


class FAQResponsePolicy:
    """Only allow an exact, unique FAQ question to supply response content."""

    def __init__(self, faq_service: FAQService) -> None:
        self._faq_service = faq_service

    def resolve(self, query: str) -> FAQAnswer | FAQFallback:
        matches = self._faq_service.search_faq(query)
        query_key = normalize_faq_question(query)
        exact = [
            record for record in matches if normalize_faq_question(record.question) == query_key
        ]
        if len(exact) == 1:
            record = exact[0]
            return FAQAnswer(text=record.answer, source_question=record.question)
        if matches:
            return FAQFallback(
                text=AMBIGUOUS_FALLBACK,
                human_help=request_human_help(HumanHelpReason.FAQ_AMBIGUOUS),
            )
        return FAQFallback(
            text=UNKNOWN_FALLBACK,
            human_help=request_human_help(HumanHelpReason.FAQ_UNKNOWN),
        )
