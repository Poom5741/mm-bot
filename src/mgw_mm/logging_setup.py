"""Structured logging configuration for the MGW/USDC Market-Maker Bot.

Configures structlog to emit valid JSON on every log line (D-01, D-02):
  - Format: JSON always — no human-readable mode
  - Destination: stdout only (12-factor, D-04)
  - Level: configurable via LOG_LEVEL env var, default INFO (D-03)

Usage:
    from mgw_mm.logging_setup import configure_logging
    configure_logging("INFO")   # call once at startup, before any log calls
"""

import logging


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog and stdlib logging for JSON output to stdout.

    Args:
        log_level: Log level name string (e.g. "INFO", "DEBUG", "WARNING").
                   Case-insensitive. Raises ValueError for unknown levels.

    Raises:
        ValueError: If log_level is not a recognized logging level name.
    """
    import structlog

    # Validate the level — getLevelName returns "Level <N>" for unknowns in 3.11+
    level_int = logging.getLevelName(log_level.upper())
    if not isinstance(level_int, int):
        raise ValueError(
            f"Unknown log level: {log_level!r}. "
            f"Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )

    # Configure stdlib root logger — third-party libs respect this level too
    logging.basicConfig(
        level=level_int,
        format="%(message)s",  # structlog handles formatting
    )
    logging.root.setLevel(level_int)

    def _add_logger_name(logger, method_name, event_dict):
        """Add logger name to the event dict (compatible with PrintLoggerFactory)."""
        # PrintLogger does not expose .name; fall back to the bound logger's name
        # that structlog passes when get_logger(__name__) is used.
        name = getattr(logger, "name", None) or event_dict.pop("_logger_name", None)
        if name:
            event_dict["logger"] = name
        return event_dict

    # Configure structlog with JSON pipeline
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            _add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_int),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
