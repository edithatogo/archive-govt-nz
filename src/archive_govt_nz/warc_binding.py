"""Bounded verification of capture-written, decoded-body WARC receipts."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import TYPE_CHECKING, NoReturn
from urllib.parse import urlsplit, urlunsplit

from warcio.archiveiterator import ArchiveIterator

from archive_govt_nz.cli_integrity import _verify_warc_stream

# Capture permits 64 MiB decoded bodies; reserve 1 MiB for envelope/header bytes.
MAX_WARC_BYTES = 65 * 1024 * 1024

if TYPE_CHECKING:
    from pathlib import Path


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _verify_capture_framing(payload: bytes) -> None:
    """Check the single-record writer profile, not permissive WARC EOF parsing."""
    envelope, block = payload.split(b"\r\n\r\n", 1)
    lengths = [
        line.split(b":", 1)[1].strip()
        for line in envelope.split(b"\r\n")[1:]
        if line.split(b":", 1)[0].lower() == b"content-length"
    ]
    if len(lengths) != 1 or not lengths[0].isdigit():
        _fail("resume_warc_framing_mismatch")
    # The HTTP Content-Length may describe encoded wire bytes; only the outer
    # WARC length frames the writer's decoded HTTP block and final terminator.
    if block[int(lengths[0]) :] != b"\r\n\r\n":
        _fail("resume_warc_framing_mismatch")


def verify_response_binding(  # noqa: PLR0913 -- explicit receipt bindings
    path: Path,
    *,
    request_url: str,
    final_url: str,
    status_code: int,
    content_type: str | None = None,
    body_sha256: str,
    body_bytes: int,
    warc_sha256: str,
) -> None:
    """Require exactly one response and capture-time full URL digest evidence.

    Legacy sanitized-only records are not migratable from mutable manifest
    assertions. Preserve them, but require a new capture for resumable binding.
    This is consistency verification, not authenticity against artifact forgery.
    """
    with path.open("rb") as stream:
        payload = stream.read(MAX_WARC_BYTES + 1)
    if len(payload) > MAX_WARC_BYTES:
        _fail("resume_warc_size_limit")
    if hashlib.sha256(payload).hexdigest() != warc_sha256:
        _fail("resume_warc_mismatch")
    parsed = urlsplit(final_url)
    expected = {
        "WARC-Target-URI": urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, "", "")
        ),
        "WARC-Request-URL-SHA256": hashlib.sha256(request_url.encode()).hexdigest(),
        "WARC-Final-URL-SHA256": hashlib.sha256(final_url.encode()).hexdigest(),
        "WARC-Payload-Digest": "sha256:" + body_sha256,
    }
    count = 0
    try:
        _verify_capture_framing(payload)
        _verify_warc_stream(BytesIO(payload))
        for record in ArchiveIterator(BytesIO(payload)):
            count += 1
            if (
                count != 1
                or record.rec_type != "response"
                or record.http_headers is None
                or record.http_headers.get_statuscode() != str(status_code)
                or [
                    value
                    for key, value in record.http_headers.headers
                    if key.lower() == "content-type"
                ]
                != ([] if content_type is None else [content_type])
            ):
                _fail("resume_warc_response_mismatch")
            for key, value in expected.items():
                values = [
                    v for k, v in record.rec_headers.headers if k.lower() == key.lower()
                ]
                if values != [value]:
                    _fail("resume_warc_binding_mismatch")
            # Writer stores decoded bytes; do not apply Content-Encoding again.
            body = record.raw_stream.read(MAX_WARC_BYTES + 1)
            if (
                len(body) != body_bytes
                or hashlib.sha256(body).hexdigest() != body_sha256
            ):
                _fail("resume_warc_body_mismatch")
    except Exception as error:
        message = "resume_warc_binding_invalid"
        raise ValueError(message) from error
