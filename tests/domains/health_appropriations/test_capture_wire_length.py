"""Content-Length refers to transport body bytes, never decoded payload size."""

from __future__ import annotations

import asyncio
import gzip
import tempfile
import zlib
from pathlib import Path

import httpx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.domains.health_appropriations.test_bronze_ingestion_contracts import (
    OnePassBody,
)

from archive_govt_nz.capture import CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore


@pytest.mark.anyio
@pytest.mark.parametrize("offset", [-1, 1])
async def test_encoded_length_mismatch_never_promotes(
    tmp_path: Path, offset: int
) -> None:
    """A decodable gzip is still incomplete when its declared body size differs."""
    payload = b"synthetic health" * 20
    wire = gzip.compress(payload)
    body = OnePassBody((wire[:7], wire[7:]))
    store = ContentAddressedStore(tmp_path / "cas")
    warc = tmp_path / "response.warc"
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                headers={
                    "content-encoding": "gzip",
                    "content-length": str(len(wire) + offset),
                },
                stream=body,
            )
        )
    ) as client:
        with pytest.raises(CaptureError, match="length_mismatch") as error:
            await capture_url(
                client,
                "https://example.test/health.csv",
                store,
                transaction_warc_path=warc,
            )
    assert error.value.attempts[-1].outcome == "length_mismatch"
    assert body.iterations == 1
    assert body.closed
    assert store.verified_inventory().object_count == 0
    assert not list(store.tmp.iterdir())
    assert not warc.exists()


@pytest.mark.anyio
@pytest.mark.parametrize("encoding", ["gzip", "deflate", "gzip, deflate"])
@pytest.mark.parametrize("advertised", [True, False])
async def test_transport_counter_is_before_decoding_and_counts_once(
    tmp_path: Path, encoding: str, *, advertised: bool
) -> None:
    """Exercise real HTTPX decoders; absent length makes no exact-length claim."""
    payload = b"synthetic health" * 20
    wire = gzip.compress(payload) if encoding.startswith("gzip") else payload
    if encoding.endswith("deflate"):
        wire = zlib.compress(wire)
    headers = {"content-encoding": encoding}
    if advertised:
        headers["content-length"] = str(len(wire))
    body = OnePassBody(tuple(wire[i : i + 3] for i in range(0, len(wire), 3)))
    response = httpx.Response(200, headers=headers, stream=body)
    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: response)
    ) as client:
        result = await capture_url(client, "https://example.test/health.csv", store)
    assert response.num_bytes_downloaded == len(wire)
    assert len(wire) != result.receipt.byte_count
    assert result.receipt.path.read_bytes() == payload
    assert body.iterations == 1
    assert body.closed


@pytest.mark.anyio
async def test_truncated_gzip_trailer_fails_advertised_body_length(
    tmp_path: Path,
) -> None:
    """Even when the decoder emits the full payload, missing encoded bytes fail."""
    payload = b"synthetic health" * 20
    wire = gzip.compress(payload)
    body = OnePassBody((wire[:-4],))
    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                headers={"content-encoding": "gzip", "content-length": str(len(wire))},
                stream=body,
            )
        )
    ) as client:
        with pytest.raises(CaptureError, match="length_mismatch"):
            await capture_url(client, "https://example.test/health.csv", store)
    assert store.verified_inventory().object_count == 0


@given(payload=st.binary(max_size=256), split=st.integers(min_value=1, max_value=20))
@settings(max_examples=20)
def test_encoded_length_is_independent_of_payload_and_chunking(
    payload: bytes, split: int
) -> None:
    """Property: exact compressed length accepts arbitrary bytes including empty."""

    async def run(root: Path) -> None:
        wire = gzip.compress(payload)
        body = OnePassBody(
            tuple(wire[i : i + split] for i in range(0, len(wire), split))
        )
        store = ContentAddressedStore(root / "cas")
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    headers={
                        "content-encoding": "gzip",
                        "content-length": str(len(wire)),
                    },
                    stream=body,
                )
            )
        ) as client:
            result = await capture_url(client, "https://example.test/health.csv", store)
        assert result.receipt.path.read_bytes() == payload
        assert body.iterations == 1
        assert body.closed

    with tempfile.TemporaryDirectory() as directory:
        asyncio.run(run(Path(directory)))


@pytest.mark.anyio
async def test_prebuffered_encoded_response_cannot_claim_wire_length(
    tmp_path: Path,
) -> None:
    """HTTPX constructor buffering resets its transport count; fail closed."""
    wire = gzip.compress(b"synthetic health" * 20)
    response = httpx.Response(
        200,
        headers={"content-encoding": "gzip", "content-length": str(len(wire))},
        content=wire,
    )
    assert response.is_stream_consumed
    assert response.num_bytes_downloaded == 0
    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: response)
    ) as client:
        with pytest.raises(CaptureError, match="wire_length_unverifiable"):
            await capture_url(client, "https://example.test/health.csv", store)
    assert store.verified_inventory().object_count == 0
    assert not list(store.tmp.iterdir())
