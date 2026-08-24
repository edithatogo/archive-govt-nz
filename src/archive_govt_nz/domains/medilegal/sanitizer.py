"""Anonymization and health data sanitization for Medico-Legal decisions."""

from __future__ import annotations

import re
from typing import Final

# NHI pattern: 3 uppercase letters followed by 4 digits (e.g. ABC1234)
_NHI_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[A-HJ-NP-Z]{3}\d{4}\b", re.IGNORECASE
)

# Sensitive contact data patterns
_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
_PHONE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:\+?64|0)[ -]?(?:\d[ -]?){7,10}\b"
)
_DOB_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:DOB|Date of Birth)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    re.IGNORECASE,
)


def sanitize_medilegal_text(text: str) -> str:
    """Sanitize patient identifiers and contact details deterministically."""
    sanitized = text

    # Redact NHI numbers
    sanitized = _NHI_PATTERN.sub("[REDACTED NHI]", sanitized)

    # Redact Emails
    sanitized = _EMAIL_PATTERN.sub("[REDACTED EMAIL]", sanitized)

    # Redact Phone numbers
    sanitized = _PHONE_PATTERN.sub("[REDACTED PHONE]", sanitized)

    # Redact Explicit DOB values
    return _DOB_PATTERN.sub("DOB: [REDACTED DOB]", sanitized)


def verify_sanitization(text: str) -> bool:
    """Verify decision text does not leak explicit unredacted NHIs/contacts."""
    if _NHI_PATTERN.search(text):
        return False
    return not _EMAIL_PATTERN.search(text)
