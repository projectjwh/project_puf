"""Structured JSON logging for all pipeline operations.

Uses structlog for consistent, machine-readable log output.
Every log entry includes source, stage, and run_id context.
"""

import logging
import sys

import structlog


def setup_logging(level: str = "INFO") -> None:
    """Configure structlog with JSON output for pipeline use.

    Call once at application startup (e.g., in Prefect flow entry points).
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(source: str | None = None, stage: str | None = None, **kwargs: object) -> structlog.stdlib.BoundLogger:
    """Get a bound logger with pipeline context.

    Args:
        source: Data source short name (e.g., "nppes", "partb").
        stage: Pipeline stage (e.g., "acquire", "validate", "transform", "load").
        **kwargs: Additional context fields bound to every log entry.
    """
    logger = structlog.get_logger()
    bindings: dict[str, object] = {}
    if source:
        bindings["source"] = source
    if stage:
        bindings["stage"] = stage
    bindings.update(kwargs)
    return logger.bind(**bindings)  # type: ignore[no-any-return]
