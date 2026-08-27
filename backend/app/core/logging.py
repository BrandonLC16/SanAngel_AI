import logging

HTTP_LOGGER_NAME = "backend.app.http"
WHATSAPP_BACKGROUND_LOGGER_NAME = "backend.app.whatsapp_background"
http_logger = logging.getLogger(HTTP_LOGGER_NAME)
whatsapp_background_logger = logging.getLogger(WHATSAPP_BACKGROUND_LOGGER_NAME)


def configure_logging(log_level: str) -> None:
    """Configure minimal application logging without recording request contents."""

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    http_logger.setLevel(log_level)
    whatsapp_background_logger.setLevel(log_level)
