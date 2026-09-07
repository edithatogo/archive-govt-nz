"""Capture-written framing rejects ambiguity even with re-pinned fixity."""

import gzip
import hashlib
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from archive_govt_nz.capture import capture_url
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.warc import write_response_record
from archive_govt_nz.warc_binding import verify_response_binding

URL = "https://example.test/data?q=one#fragment"


def _verify(path: Path, body: bytes) -> None:
    verify_response_binding(
        path,
        request_url=URL,
        final_url=URL,
        status_code=200,
        content_type="text/csv",
        body_sha256=hashlib.sha256(body).hexdigest(),
        body_bytes=len(body),
        warc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


@pytest.mark.parametrize("value", ["text/csv", "application/pdf"])
@pytest.mark.parametrize("name", ["content-type", "Content-Type", "CONTENT-TYPE"])
def test_duplicate_content_type_rejected(tmp_path: Path, name: str, value: str) -> None:
    """Same-value duplicates are as invalid as conflicting duplicates."""
    path = tmp_path / "response.warc"
    write_response_record(
        path,
        url=URL,
        status_code=200,
        headers={"content-type": "text/csv"},
        body=b"abc",
    )
    envelope, content = path.read_bytes().split(b"\r\n\r\n", 1)
    block = content[:-4]
    altered = block.replace(
        b"content-type: text/csv\r\n",
        f"content-type: text/csv\r\n{name}: {value}\r\n".encode(),
    )
    envelope = envelope.replace(
        f"Content-Length: {len(block)}".encode(),
        f"Content-Length: {len(altered)}".encode(),
    )
    payload = envelope + b"\r\n\r\n" + altered + b"\r\n\r\n"
    path.write_bytes(payload)
    with pytest.raises(ValueError, match="resume_warc"):
        _verify(path, b"abc")
    assert path.read_bytes() == payload


@pytest.mark.parametrize("length", [b"missing", b"same", b"conflicting", b"-1", b"no"])
def test_outer_length_unambiguous(tmp_path: Path, length: bytes) -> None:
    """The terminator offset must have one nonnegative decimal source."""
    path = tmp_path / "response.warc"
    write_response_record(
        path,
        url=URL,
        status_code=200,
        headers={"content-type": "text/csv"},
        body=b"abc",
    )
    payload = path.read_bytes()
    line = next(
        line for line in payload.split(b"\r\n") if line.startswith(b"Content-Length:")
    )
    replacements = {
        b"missing": b"",
        b"same": line + b"\r\n" + line,
        b"conflicting": line + b"\r\ncontent-length: 0",
    }
    payload = payload.replace(
        line, replacements.get(length, b"Content-Length: " + length)
    )
    path.write_bytes(payload)
    with pytest.raises(ValueError, match="resume_warc"):
        _verify(path, b"abc")
    assert path.read_bytes() == payload


@pytest.mark.anyio
async def test_emitted_redirect_encoded_response(tmp_path: Path) -> None:
    """Real capture writing retains decoded body despite compressed wire length."""
    body = b"synthetic payload" * 100
    encoded = gzip.compress(body, mtime=0)
    final = "https://example.test/final?q=two#end"

    class WireStream(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield encoded

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/data":
            return httpx.Response(302, headers={"location": final})
        return httpx.Response(
            200,
            headers={
                "content-type": "text/csv",
                "content-encoding": "gzip",
                "content-length": str(len(encoded)),
            },
            stream=WireStream(),
        )

    path = tmp_path / "response.warc"
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await capture_url(
            client,
            URL,
            ContentAddressedStore(tmp_path / "cas"),
            transaction_warc_path=path,
        )
    assert result.redirects == 1
    assert result.receipt.byte_count == len(body) != len(encoded)
    assert result.receipt.sha256 == hashlib.sha256(body).hexdigest()
    payload = path.read_bytes()
    verify_response_binding(
        path,
        request_url=URL,
        final_url=final,
        status_code=200,
        content_type="text/csv",
        body_sha256=result.receipt.sha256,
        body_bytes=result.receipt.byte_count,
        warc_sha256=hashlib.sha256(payload).hexdigest(),
    )
    assert path.read_bytes() == payload


@pytest.mark.parametrize("body", [b"", b"abc", b"abc\r\n\r\n"])
@pytest.mark.parametrize(
    "terminator",
    [b"", b"\r", b"\r\n", b"\r\n\r", b"\n\n", b"\r\n\r\n", b"\r\n\r\n\r\n"],
)
def test_exact_record_terminator(
    tmp_path: Path, body: bytes, terminator: bytes
) -> None:
    """Only the writer's exact terminator at the declared offset is accepted."""
    path = tmp_path / "response.warc"
    write_response_record(
        path, url=URL, status_code=200, headers={"content-type": "text/csv"}, body=body
    )
    payload = path.read_bytes()[:-4] + terminator
    path.write_bytes(payload)
    if terminator == b"\r\n\r\n":
        _verify(path, body)
    else:
        with pytest.raises(ValueError, match="resume_warc"):
            _verify(path, body)
    assert path.read_bytes() == payload
