"""Sanitized and structured logging configuration."""

import contextvars
import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

from apps.api.app.config import get_settings

# Global ContextVar for correlating logs within an asyncio task / request
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id_ctx", default=None
)


def get_current_request_id() -> str | None:
    """Retrieves the active request correlation ID from context."""
    return request_id_ctx.get()


def set_current_request_id(request_id: str | None) -> contextvars.Token:
    """Sets the active request correlation ID in context."""
    return request_id_ctx.set(request_id)


class SensitiveDataFilter(logging.Filter):
    """Masks database passwords, secret tokens, bearer auth, and cookies in log messages.

    Also sanitizes newline and control characters to prevent log injection.
    """

    # Matches URLs with passwords like postgresql://user:pass@host
    PASSWORD_URL_REGEX = re.compile(r":([^:@\s]+)@")

    # Matches Authorization: Bearer <token> or similar tokens
    AUTH_BEARER_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.]+", re.IGNORECASE)

    # Matches secret_key=... or password=... or token=... in query/form/kv strings
    KEY_VALUE_SECRET_REGEX = re.compile(
        r"(password|secret_key|api_key|token|access_token)(=|\s+|:\s*)([^\s&,;]+)",
        re.IGNORECASE,
    )

    # Matches cookie headers
    COOKIE_REGEX = re.compile(r"(Cookie:\s*)([^\r\n]+)", re.IGNORECASE)

    # Replaces control characters (except standard printable space) to prevent log injection
    CONTROL_CHAR_REGEX = re.compile(r"[\r\n\t\x00-\x1f\x7f-\x9f]")

    def sanitize_string(self, text: str, preserve_newlines: bool = False) -> str:
        if not text:
            return text
        # 1. Mask passwords in DB URLs
        text = self.PASSWORD_URL_REGEX.sub(":****@", text)
        # 2. Mask Bearer tokens
        text = self.AUTH_BEARER_REGEX.sub(r"\1****", text)
        # 3. Mask key-value and token secrets
        text = self.KEY_VALUE_SECRET_REGEX.sub(r"\1\2****", text)
        # 4. Mask Cookie contents
        text = self.COOKIE_REGEX.sub(r"\1****", text)
        # 5. Sanitize log injection characters if requested
        if not preserve_newlines:
            text = self.CONTROL_CHAR_REGEX.sub(" ", text)
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        # Attach request_id from contextvars if not already present on record
        if not getattr(record, "request_id", None):
            record.request_id = get_current_request_id()

        # Sanitize record.msg
        if isinstance(record.msg, str):
            record.msg = self.sanitize_string(
                record.msg, preserve_newlines=bool(record.exc_info)
            )

        # Sanitize record.args
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(self.sanitize_string(str(a)) for a in record.args)
            elif isinstance(record.args, dict):
                record.args = {
                    k: self.sanitize_string(str(v)) for k, v in record.args.items()
                }

        # Sanitize custom extra dictionary if present
        details = getattr(record, "details", None)
        if isinstance(details, dict):
            record.details = {
                k: self.sanitize_string(str(v)) if isinstance(v, str) else v
                for k, v in details.items()
            }

        return True


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records into machine-readable JSON compliant with the Phase 4.6 Logging Contract."""

    def __init__(self, service: str = "timeline-api", environment: str = "development"):
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        # Format message with arguments
        message = record.getMessage()

        # Extract standard Phase 4.6 contract fields
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.name),
            "service": self.service,
            "environment": self.environment,
            "message": message,
        }

        # Add correlation ID
        request_id = getattr(record, "request_id", None) or get_current_request_id()
        if request_id:
            payload["request_id"] = str(request_id)

        # Add optional contextual contract fields if populated
        for field in (
            "operation",
            "duration_ms",
            "status_code",
            "series_id",
            "resource_type",
            "resource_id",
            "chapter",
            "reader_chapter",
            "error_code",
            "outcome",
            "details",
        ):
            val = getattr(record, field, None)
            if val is not None:
                payload[field] = val

        # Handle exception tracebacks safely (only if present)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging():
    """Initializes root and application loggers with sanitization and structured formatting."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Attach SensitiveDataFilter to root and key app loggers
    app_loggers = [
        root_logger,
        logging.getLogger("timeline.api"),
        logging.getLogger("timeline.db"),
        logging.getLogger("timeline.publisher"),
        logging.getLogger("timeline.cache"),
    ]
    for l in app_loggers:
        if not any(isinstance(f, SensitiveDataFilter) for f in l.filters):
            l.addFilter(SensitiveDataFilter())

    # Ensure a structured StreamHandler exists for stdout
    stream_handlers = [
        h for h in root_logger.handlers if type(h) is logging.StreamHandler
    ]
    if not stream_handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = StructuredJsonFormatter(
            service="timeline-api", environment=settings.ENVIRONMENT.value
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for h in stream_handlers:
            h.setFormatter(
                StructuredJsonFormatter(
                    service="timeline-api", environment=settings.ENVIRONMENT.value
                )
            )

    logger = logging.getLogger("timeline.api")
    logger.info(
        "Application logging initialized for environment: %s (Log Level: %s, DB: %s)",
        settings.ENVIRONMENT.value,
        settings.LOG_LEVEL,
        settings.sanitized_database_url,
        extra={
            "event": "app.startup",
            "operation": "setup_logging",
            "outcome": "success",
        },
    )
