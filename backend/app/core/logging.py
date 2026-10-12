import logging
import sys

from backend.app.core.observability import operations_logger

HTTP_LOGGER_NAME = "backend.app.http"
WHATSAPP_BACKGROUND_LOGGER_NAME = "backend.app.whatsapp_background"
TOOL_AUDIT_LOGGER_NAME = "backend.app.tool_audit"
http_logger = logging.getLogger(HTTP_LOGGER_NAME)
whatsapp_background_logger = logging.getLogger(WHATSAPP_BACKGROUND_LOGGER_NAME)
tool_audit_logger = logging.getLogger(TOOL_AUDIT_LOGGER_NAME)


def configure_logging(log_level: str) -> None:
    """Configure minimal application logging without recording request contents."""

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    http_logger.setLevel(log_level)
    whatsapp_background_logger.setLevel(log_level)
    tool_audit_logger.setLevel(log_level)
    if not operations_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        operations_logger.addHandler(handler)
    operations_logger.setLevel(logging.INFO)
    operations_logger.propagate = False
