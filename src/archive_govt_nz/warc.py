"""Bounded WARC 1.1 transaction receipts without credential leakage."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

_SAFE_HEADERS = frozenset({"content-type", "content-length", "etag", "last-modified"})


class WarcError(ValueError):
    """WARC receipt construction failure."""

    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class WarcReceipt:
    """Written WARC evidence and its digest."""

    path: Path
    record_id: str
    sha256: str
    byte_count: int


def write_response_record(
    path: Path,
    *,
    url: str,
    status_code: int,
    headers: dict[str, str],
    body: bytes,
    record_id: str | None = None,
) -> WarcReceipt:
    """Write one bounded WARC response record with safe URL/header evidence."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise WarcError("unsafe_url")
    safe_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    identifier = record_id or f"urn:uuid:{uuid.uuid4()}"
    safe_headers = {
        key.lower(): value
        for key, value in headers.items()
        if key.lower() in _SAFE_HEADERS
    }
    lines = [
        "WARC/1.1",
        "WARC-Type: response",
        f"WARC-Record-ID: <{identifier}>",
        f"WARC-Target-URI: {safe_url}",
        "Content-Type: application/http; msgtype=response",
        f"WARC-Payload-Digest: sha256:{hashlib.sha256(body).hexdigest()}",
        "",
        f"HTTP/1.1 {status_code}",
        *[f"{key}: {value}" for key, value in sorted(safe_headers.items())],
        "",
    ]
    payload = "\r\n".join(lines).encode("utf-8") + body + b"\r\n\r\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return WarcReceipt(
        path, identifier, hashlib.sha256(payload).hexdigest(), len(payload)
    )
