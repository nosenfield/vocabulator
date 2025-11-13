"""Logging utilities for Vocabulator.

This module provides structured JSON logging with correlation ID support,
sensitive data masking, and environment-based log level configuration.
"""

import json
import logging
import re
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from src.utils.config import Environment, LogLevel, get_config

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for current context.

    Args:
        cid: Correlation ID to set. If None, generates a new UUID.

    Returns:
        The correlation ID that was set.
    """
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current context.

    Returns:
        Current correlation ID, or None if not set.
    """
    try:
        return correlation_id.get()
    except LookupError:
        return None


def mask_sensitive_data(value: str) -> str:
    """Mask sensitive data in log messages.

    Masks:
    - OpenAI API keys (sk-*)
    - AWS secret keys
    - Student IDs (STU-*)

    Args:
        value: String value that may contain sensitive data.

    Returns:
        Masked string with sensitive parts replaced with ***.
    """
    if not isinstance(value, str):
        return str(value)

    # Mask OpenAI API keys (sk- followed by alphanumeric, at least 10 chars total)
    value = re.sub(r"sk-[a-zA-Z0-9]{10,}", "sk-***", value)

    # Mask AWS secret access keys (long alphanumeric strings, 40+ chars)
    value = re.sub(r"[A-Za-z0-9/+=]{40,}", "***", value)

    # Mask student IDs (STU- followed by digits)
    value = re.sub(r"STU-\d+", "STU-***", value)

    return value


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON string representation of log record.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": mask_sensitive_data(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        cid = get_correlation_id()
        if cid:
            log_data["correlation_id"] = cid

        # Add extra fields (with masking)
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                # Mask sensitive data in extra fields
                if isinstance(value, str):
                    log_data[key] = mask_sensitive_data(value)
                else:
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def _create_cloudwatch_handler() -> Optional[logging.Handler]:
    """Create CloudWatch Logs handler (stub for local development).

    This is a placeholder for future CloudWatch integration.
    In production, this would create a CloudWatch handler.

    Returns:
        CloudWatch handler or None if not in production.
    """
    config = get_config()

    # Only create CloudWatch handler in production
    if config.environment == Environment.PRODUCTION:
        # TODO: Implement CloudWatch handler in infrastructure phase
        # For now, return None (stub)
        pass

    return None


def configure_logging() -> None:
    """Configure logging for the application.

    Sets up:
    - JSON formatter for structured logging
    - Log level based on environment configuration
    - CloudWatch handler (in production, stub for now)
    """
    config = get_config()
    logger = logging.getLogger("vocabulator")

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set log level based on configuration
    log_level_map = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }
    logger.setLevel(log_level_map.get(config.log_level, logging.INFO))

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # Add CloudWatch handler if in production (stub for now)
    cloudwatch_handler = _create_cloudwatch_handler()
    if cloudwatch_handler:
        logger.addHandler(cloudwatch_handler)

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a component.

    Args:
        name: Component name (e.g., 'api', 'processing', 'ai').

    Returns:
        Logger instance with 'vocabulator.{name}' as the name.
    """
    logger_name = f"vocabulator.{name}"
    logger = logging.getLogger(logger_name)

    # Ensure logging is configured
    if not logger.handlers:
        configure_logging()

    return logger

