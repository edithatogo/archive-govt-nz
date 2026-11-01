"""Bounded WARC 1.1 transaction receipts without credential leakage."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
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


def _warc_date() -> str:
    """Return current time in WARC-Date format (ISO 8601, Zulu)."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_response_record(
    path: Path,
    *,
    url: str,
    status_code: int,
    headers: dict[str, str],
    body: bytes,
    record_id: str | None = None,
    request_url: str | None = None,
    exclusive: bool = False,
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
    http_lines = [f"HTTP/1.1 {status_code}"]
    http_lines += [f"{key}: {value}" for key, value in sorted(safe_headers.items())]
    http_block = "\r\n".join(http_lines).encode("utf-8") + b"\r\n\r\n"
    content_block = http_block + body
    request_digest = hashlib.sha256(
        (request_url if request_url is not None else url).encode()
    ).hexdigest()
    header_lines = [
        "WARC/1.1",
        f"WARC-Record-ID: <{identifier}>",
        f"WARC-Target-URI: {safe_url}",
        f"WARC-Date: {_warc_date()}",
        f"WARC-Request-URL-SHA256: {request_digest}",
        f"WARC-Final-URL-SHA256: {hashlib.sha256(url.encode()).hexdigest()}",
        "WARC-Type: response",
        "Content-Type: application/http; msgtype=response",
        f"WARC-Payload-Digest: sha256:{hashlib.sha256(body).hexdigest()}",
        f"Content-Length: {len(content_block)}",
    ]
    payload = (
        "\r\n".join(header_lines).encode("utf-8")
        + b"\r\n\r\n"
        + content_block
        + b"\r\n\r\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb" if exclusive else "wb") as output:
        output.write(payload)
    return WarcReceipt(
        path, identifier, hashlib.sha256(payload).hexdigest(), len(payload)
    )
