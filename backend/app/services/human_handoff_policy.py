"""Closed rules for requesting human review in the WhatsApp conversation flow."""

import re
import unicodedata

HUMAN_HELP_ACK = (
    "Solicité ayuda al personal de esta sucursal. Todavía no hay una respuesta humana confirmada."
)

_REQUEST = re.compile(
    r"\b(?:quiero|necesito|quisiera|puedes|pueden|podrias|podrian|pasame|comunicame|"
    r"hablar|atencion)\b.{0,48}\b(?:humano|humana|persona|empleado|empleada|"
    r"asesor|asesora|agente|encargado|encargada|operador|operadora)\b"
)
_SHORT_REQUESTS = frozenset({"humano", "asesor", "asesora", "agente", "atencion humana"})


def explicitly_requests_human(message: str) -> bool:
    """Recognize conservative, direct requests; never infer a handoff from arbitrary text."""
    normalized = unicodedata.normalize("NFKD", message.casefold())
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    normalized = " ".join(re.findall(r"[a-z]+", normalized))
    return normalized in _SHORT_REQUESTS or _REQUEST.search(normalized) is not None
