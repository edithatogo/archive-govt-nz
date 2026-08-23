"""Magic byte and MIME signature sniffer for Bronze ingestion stream verification.

Provides fast fail-closed payload validation over initial bytes to prevent
disguised HTML error pages, polyglots, and corrupt payloads from polluting CAS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

MAX_SNIFF_HEADER_BYTES: Final[int] = 512

# Prefix table for deterministic binary/container formats
_BINARY_MAGIC_MAP: Final[tuple[tuple[bytes, str], ...]] = (
    (b"%PDF-", "application/pdf"),
    (b"WARC/1.0", "application/warc"),
    (b"WARC/1.1", "application/warc"),
    (b"\x1f\x8b", "application/gzip"),
    (b"PK\x03\x04", "application/zip"),
)

_UTF8_BOM: Final[bytes] = b"\xef\xbb\xbf"

_XML_START_RE: Final[re.Pattern[bytes]] = re.compile(
    rb"^\s*(?:<\?xml\b|<(?:act|bill|regulation|notice|sitting|debate|"
    rb"feed|rss|atom|rdf|dcat|record)\b)",
    re.IGNORECASE,
)
_HTML_START_RE: Final[re.Pattern[bytes]] = re.compile(
    rb"^\s*(?:<!DOCTYPE\s+html|<html\b|<head\b|<body\b)",
    re.IGNORECASE,
)
_HTML_EMBEDDED_RE: Final[re.Pattern[bytes]] = re.compile(
    rb"<(?:!DOCTYPE\s+html|html|head|body|script)\b",
    re.IGNORECASE,
)

_COMPATIBLE_MIMES: Final[dict[str, set[str]]] = {
    "application/xml": {"application/xml", "text/xml", "text/plain"},
    "text/xml": {"application/xml", "text/xml", "text/plain"},
    "application/json": {"application/json", "text/plain"},
    "text/csv": {"text/csv", "text/plain"},
    "application/pdf": {"application/pdf"},
    "application/warc": {"application/warc", "application/gzip"},
    "text/plain": {
        "text/plain",
        "text/csv",
        "application/json",
        "application/xml",
    },
}


class InvalidPayloadSignatureError(ValueError):
    """Raised when payload magic bytes or content signatures fail verification."""

    def __init__(
        self,
        message: str,
        detected_mime: str | None = None,
        expected_mime: str | None = None,
    ) -> None:
        """Initialize exception with payload context."""
        super().__init__(message)
        self.detected_mime = detected_mime
        self.expected_mime = expected_mime


@dataclass(frozen=True, slots=True)
class SniffResult:
    """Outcome of magic byte inspection."""

    is_valid: bool
    detected_mime: str
    expected_mime: str | None
    is_polyglot: bool = False
    error: str | None = None


def _sniff_text_format(sample: bytes) -> str:
    """Classify text payload formats."""
    if _HTML_START_RE.match(sample):
        return "text/html"
    if _XML_START_RE.match(sample):
        return "application/xml"

    stripped = sample.lstrip()
    if stripped.startswith((b"{", b"[")):
        return "application/json"

    if b"\x00" not in sample:
        try:
            text = sample.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            lines = [line for line in text.splitlines() if line.strip()]
            if lines and ("," in lines[0] or "\t" in lines[0] or "|" in lines[0]):
                return "text/csv"
            return "text/plain"

    return "application/octet-stream"


def sniff_magic_mime(data: bytes) -> str:
    """Determine MIME type from the initial 512 bytes of raw data."""
    if not data:
        return "application/x-empty"

    sample = data[:MAX_SNIFF_HEADER_BYTES].removeprefix(_UTF8_BOM)

    for prefix, mime in _BINARY_MAGIC_MAP:
        if sample.startswith(prefix):
            return mime

    return _sniff_text_format(sample)


def _check_disguised_html(detected: str, expected: str | None) -> str | None:
    """Detect if an HTML error page is disguised under another MIME type."""
    if not expected or detected != "text/html":
        return None

    if expected in ("application/pdf", "pdf"):
        return "HTML error page disguised as PDF"

    text_or_binary_types = (
        "application/xml",
        "text/xml",
        "application/json",
        "text/csv",
        "application/warc",
    )
    if expected in text_or_binary_types:
        return f"HTML error page received when expecting {expected}"

    return None


def validate_payload_signature(
    data: bytes,
    expected_mime: str | None = None,
    *,
    allow_octet_stream: bool = False,
) -> SniffResult:
    """Validate payload bytes against expected MIME type and anti-polyglot rules.

    Rejects:
    - Empty payloads
    - HTML error pages when expecting PDF, XML, JSON, CSV, or WARC
    - Corrupt or mismatched binary signatures
    - Polyglot payloads containing conflicting format headers
    """
    if not data:
        return SniffResult(
            is_valid=False,
            detected_mime="application/x-empty",
            expected_mime=expected_mime,
            error="Payload is empty (0 bytes)",
        )

    detected = sniff_magic_mime(data)
    norm_expected = expected_mime.strip().lower() if expected_mime else None
    if norm_expected:
        norm_expected = norm_expected.split(";")[0].strip()

    sample = data[:MAX_SNIFF_HEADER_BYTES]
    is_polyglot = detected in (
        "application/pdf",
        "application/zip",
        "application/gzip",
    ) and bool(_HTML_EMBEDDED_RE.search(sample))

    if is_polyglot:
        return SniffResult(
            is_valid=False,
            detected_mime=detected,
            expected_mime=norm_expected,
            is_polyglot=True,
            error=(
                "Polyglot payload detected: conflicting MIME headers in "
                "initial 512 bytes"
            ),
        )

    disguised_err = _check_disguised_html(detected, norm_expected)
    if disguised_err:
        return SniffResult(
            is_valid=False,
            detected_mime=detected,
            expected_mime=norm_expected,
            error=disguised_err,
        )

    if norm_expected and norm_expected not in ("application/octet-stream", "*/*"):
        allowed_set = _COMPATIBLE_MIMES.get(norm_expected, {norm_expected})
        if detected not in allowed_set and not (
            allow_octet_stream and detected == "application/octet-stream"
        ):
            return SniffResult(
                is_valid=False,
                detected_mime=detected,
                expected_mime=norm_expected,
                error=(
                    f"MIME mismatch: detected '{detected}' does not match "
                    f"expected '{norm_expected}'"
                ),
            )

    return SniffResult(
        is_valid=True,
        detected_mime=detected,
        expected_mime=norm_expected,
    )
