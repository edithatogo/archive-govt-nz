"""Structured JSON logging configuration using Python standard library."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import TextIO


class JsonLogFormatter(logging.Formatter):
    """Formats log records as structured JSON Lines objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a standard LogRecord into JSON."""
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            log_entry.update(extra)
        return json.dumps(log_entry, sort_keys=True)


def configure_structured_logging(
    level: int = logging.INFO, stream: TextIO | None = None
) -> logging.Logger:
    """Configure and return the root archive-govt-nz structured logger."""
    logger = logging.getLogger("archive_govt_nz")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
