import logging
import sys
from typing import Any, Dict

import structlog

from fx_trader.config import settings


def configure_logging(log_level: str = settings.LOG_LEVEL) -> None:
    """
    Configures structured logging using structlog.
    """
    shared_processors: list[Any] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.APP_ENV in ["development", "dev"]:
        # Pretty, human-readable output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        # JSON output for production/staging, suitable for log aggregators
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog processors
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():  # Avoid adding handlers multiple times
        handler = logging.StreamHandler(sys.stdout)
        # Use structlog's stdlib processor to format standard log records
        # This ensures that logs from other libraries are also processed by structlog
        formatter = structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
            # Basic formatter, structlog handles the rest
            logging.Formatter('%(message)s'),
            logger=None,  # Not needed here
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta] + processors
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(log_level.upper())
    logging.getLogger("httpx").setLevel(
        logging.WARNING)  # Quieten noisy libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:  # structlog.stdlib.BoundLogger is the actual type
    return structlog.get_logger(name)
