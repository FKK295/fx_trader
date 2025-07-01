import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

# Note: We're not importing settings at the module level to avoid circular imports
# Settings will be imported inside the configure_logging function

def configure_logging(log_level: Optional[str] = None) -> None:
    """
    Configures structured logging using structlog.
    
    Args:
        log_level: The logging level as a string (e.g., 'INFO', 'DEBUG').
                  If None, will use the level from settings.LOG_LEVEL
    """
    # Import settings here to avoid circular imports
    from config.settings import settings
    
    # Use provided log_level or fall back to settings
    if log_level is None:
        log_level = settings.LOG_LEVEL

    # Convert string log level to logging constant
    log_level_numeric = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard logging first
    logging.basicConfig(
        level=log_level_numeric,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    # Configure structlog processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.APP_ENV in ["development", "dev"]:
        # Pretty, human-readable output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=sys.stdout.isatty(),
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
    else:
        # JSON output for production/staging
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger to use structlog
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_numeric)
    
    # Clear any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handler with structlog formatter
    handler = logging.StreamHandler()
    
    # Choose the appropriate processor based on environment
    if settings.APP_ENV in ["development", "dev"]:
        processor = structlog.dev.ConsoleRenderer(
            colors=sys.stdout.isatty(),
            exception_formatter=structlog.dev.plain_traceback,
        )
    else:
        processor = structlog.processors.JSONRenderer()
    
    # Configure the formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=processor,
        foreign_pre_chain=shared_processors,
    )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Configure default logger for the application
    logger = structlog.get_logger()
    logger.info("Logging configured", log_level=log_level, env=settings.APP_ENV)
    
    # Configure log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:  # structlog.stdlib.BoundLogger is the actual type
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger to get.
        
    Returns:
        A configured logger instance.
    """
    return structlog.get_logger(name)
