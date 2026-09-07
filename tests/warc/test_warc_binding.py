"""Source/response binding, bounded malformed records and redirect semantics."""

import hashlib
from functools import partial
from pathlib import Path

import httpx
import pytest

from archive_govt_nz import warc_binding
from archive_govt_nz.capture import capture_url
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.warc import write_response_record

URL = "https://example.test/data?q=one#fragment"


def test_decoded_body_is_not_measured_by_wire_content_length(tmp_path: Path) -> None:
    """WARC framing covers decoded bytes even with a different wire length."""
    path = tmp_path / "response.warc"
    receipt = write_response_record(
        path,
        url=URL,
        status_code=200,
        headers={"content-length": "99", "content-encoding": "gzip"},
        body=b"abc",
    )
    warc_binding.verify_response_binding(
        path,
        request_url=URL,
        final_url=URL,
        status_code=200,
        body_sha256=hashlib.sha256(b"abc").hexdigest(),
        body_bytes=3,
        warc_sha256=receipt.sha256,
    )


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "hash",
        "size",
        "empty",
        "multiple",
        "truncated",
        "type",
        "status",
        "body",
        "digest",
        "duplicate",
        "target",
        "legacy",
        "content_type",
    ],
)
def test_bounded_binding(  # noqa: C901 -- explicit corruption matrix
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    """Reject altered envelopes even when the mutable WARC hash is updated."""
    path = tmp_path / "response.warc"
    write_response_record(path, url=URL, status_code=200, headers={}, body=b"abc")
    payload = path.read_bytes()
    if fault == "empty":
        payload = b""
    elif fault == "multiple":
        payload *= 2
    elif fault == "truncated":
        payload = payload[:-6]
    elif fault == "type":
        payload = payload.replace(b"WARC-Type: response", b"WARC-Type: resource")
    elif fault == "status":
        payload = payload.replace(b"HTTP/1.1 200", b"HTTP/1.1 201")
    elif fault == "body":
        payload = payload.replace(b"abc", b"abd")
    elif fault == "digest":
        payload = payload.replace(
            hashlib.sha256(b"abc").hexdigest().encode(), b"0" * 64
        )
    elif fault == "target":
        payload = payload.replace(
            b"https://example.test/data\r", b"https://example.test/other\r"
        )
    elif fault in {"duplicate", "legacy"}:
        line = next(
            line
            for line in payload.splitlines(keepends=True)
            if line.startswith(b"WARC-Request-URL-SHA256:")
        )
        payload = payload.replace(line, line * 2 if fault == "duplicate" else b"")
    path.write_bytes(payload)
    monkeypatch.setattr(
        warc_binding, "MAX_WARC_BYTES", len(payload) - (fault == "size")
    )
    verify = partial(
        warc_binding.verify_response_binding,
        path,
        request_url=URL,
        final_url=URL,
        status_code=200,
        content_type="text/csv" if fault == "content_type" else None,
        body_sha256=hashlib.sha256(b"abc").hexdigest(),
        body_bytes=3,
        warc_sha256=hashlib.sha256(payload).hexdigest()
        if fault != "hash"
        else "0" * 64,
    )
    if fault == "none":
        verify()
    else:
        with pytest.raises(ValueError, match="resume_warc"):
            verify()


@pytest.mark.anyio
async def test_real_capture_redirect_binds_initial_and_final_urls(
    tmp_path: Path,
) -> None:
    """A redirected response is bound to original request and final response."""
    initial = "https://example.test/start?q=one#fragment"
    final = "https://example.test/final?q=two"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": final})
        return httpx.Response(200, content=b"abc")

    path = tmp_path / "response.warc"
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await capture_url(
            client,
            initial,
            ContentAddressedStore(tmp_path / "cas"),
            transaction_warc_path=path,
        )
    assert result.url == final
    assert result.redirects == 1
    for request_url in (initial, final):
        if request_url == initial:
            warc_binding.verify_response_binding(
                path,
                request_url=request_url,
                final_url=result.url,
                status_code=result.status_code,
                body_sha256=result.receipt.sha256,
                body_bytes=result.receipt.byte_count,
                warc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        else:
            with pytest.raises(ValueError, match="resume_warc"):
                warc_binding.verify_response_binding(
                    path,
                    request_url=request_url,
                    final_url=result.url,
                    status_code=result.status_code,
                    body_sha256=result.receipt.sha256,
                    body_bytes=result.receipt.byte_count,
                    warc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                )
    assert b"q=one" not in path.read_bytes()
    assert b"q=two" not in path.read_bytes()
