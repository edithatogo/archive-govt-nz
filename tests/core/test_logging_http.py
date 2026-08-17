"""Test suite for unified logging and HTTP client modules."""

from __future__ import annotations

import io
import json
import logging
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.http import ArchiveHttpClient
from archive_govt_nz.logging import JsonLogFormatter, configure_structured_logging
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def _raise_test_error() -> None:
    msg = "test error"
    raise ValueError(msg)


def test_structured_logging_json_output() -> None:
    """Validate structured logging emits compliant JSON Lines."""
    stream = io.StringIO()
    logger = configure_structured_logging(level=logging.INFO, stream=stream)
    logger.info("Test message")

    output = stream.getvalue().strip()
    data = json.loads(output)
    assert data["level"] == "INFO"
    assert data["logger"] == "archive_govt_nz"
    assert data["message"] == "Test message"
    assert "timestamp" in data


def test_structured_logging_formatter_exception() -> None:
    """Validate exception formatting in JSON logger."""
    formatter = JsonLogFormatter()
    try:
        _raise_test_error()
    except ValueError as exc:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=35,
            msg="An error occurred",
            args=(),
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert data["level"] == "ERROR"
        assert "ValueError: test error" in data["exception"]


@pytest.mark.anyio
async def test_archive_http_client_get_bytes() -> None:
    """Validate ArchiveHttpClient get_bytes method."""
    mock_transport = httpx.MockTransport(
        lambda _req: httpx.Response(200, content=b"Mocked HTTP payload")
    )
    mock_client = httpx.AsyncClient(transport=mock_transport)
    async with ArchiveHttpClient(client=mock_client) as client:
        content = await client.get_bytes("https://api.example.govt.nz/data")
        assert content == b"Mocked HTTP payload"


@pytest.mark.anyio
async def test_archive_http_client_stream_to_cas(tmp_path: Path) -> None:
    """Validate ArchiveHttpClient stream_to_cas direct writing."""
    mock_transport = httpx.MockTransport(
        lambda _req: httpx.Response(200, content=b"Streamed Content")
    )
    mock_client = httpx.AsyncClient(transport=mock_transport)
    store = ContentAddressedStore(tmp_path / "cas")

    async with ArchiveHttpClient(client=mock_client) as client:
        receipt = await client.stream_to_cas(
            "https://api.example.govt.nz/stream", store
        )
        assert receipt.byte_count == len(b"Streamed Content")
        assert store.verify(receipt.object_id).sha256 == receipt.sha256


@pytest.mark.anyio
async def test_archive_http_client_stream_chunks() -> None:
    """Validate ArchiveHttpClient stream_chunks generator."""
    mock_transport = httpx.MockTransport(
        lambda _req: httpx.Response(200, content=b"Chunk1Chunk2")
    )
    mock_client = httpx.AsyncClient(transport=mock_transport)
    async with ArchiveHttpClient(client=mock_client) as client:
        chunks = [
            chunk
            async for chunk in client.stream_chunks(
                "https://api.example.govt.nz/chunks"
            )
        ]
        assert b"".join(chunks) == b"Chunk1Chunk2"
