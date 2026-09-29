"""Structured logging via structlog — dev console vs JSON for Cloud Run."""

from __future__ import annotations

import logging
import sys

import structlog

from app.config.settings import get_settings


def configure_logging() -> None:
    """Configure structlog for the application.

    Development: human-readable colored console output at DEBUG level.
    Staging/Production: JSON output at INFO level for Cloud Run / Google Cloud Logging.
    Called once at application startup in main.py lifespan.
    """
    settings = get_settings()
    is_development = settings.APP_ENV.value == "development"

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_development:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        log_level = logging.DEBUG
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        log_level = logging.INFO

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Silence noisy loggers and prevent duplicate propagation
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").propagate = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Returns a bound structlog logger for the given module name.

    Usage:
        from app.config.logging import get_logger
        logger = get_logger(__name__)
        logger.info("profile_created", profile_id=str(profile_id), user_id=str(user_id))
    """
    return structlog.get_logger(name)
