"""Health Phase 2.1 contracts at the shared capture/CAS boundary."""

from __future__ import annotations

import argparse
import asyncio
import base64
import gzip
import hashlib
import json
import runpy
from pathlib import Path
from typing import TYPE_CHECKING

import blake3
import httpx
import pytest

from archive_govt_nz import capture
from archive_govt_nz.bronze.multihash import compute_cidv1_from_sha256
from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.capture_reconciliation import reconcile_capture_observations
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError
from archive_govt_nz.warc import write_response_record

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class OnePassBody(httpx.AsyncByteStream):
    """Fail if the response is consumed twice; optionally disconnect mid-body."""

    def __init__(self, chunks: tuple[bytes, ...], *, interrupt: bool = False) -> None:
        """Retain chunks and observable consumption state."""
        self.chunks = chunks
        self.interrupt = interrupt
        self.iterations = 0
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Yield each chunk once before the optional disconnect."""
        self.iterations += 1
        assert self.iterations == 1
        for chunk in self.chunks:
            yield chunk
        if self.interrupt:
            message = "synthetic private diagnostic"
            raise httpx.ReadError(message)

    async def aclose(self) -> None:
        """Record that capture released the response."""
        self.closed = True


@pytest.mark.anyio
@pytest.mark.parametrize("declared", ["2", "8"])
async def test_length_mismatch_never_promotes_or_writes_warc(
    tmp_path: Path, declared: str
) -> None:
    """Both truncated and overlong bodies below max_bytes must fail closed."""
    store = ContentAddressedStore(tmp_path / "cas")
    body = OnePassBody((b"abc", b"def"))
    warc = tmp_path / "transaction.warc"
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, headers={"content-length": declared}, stream=body
            )
        )
    ) as client:
        with pytest.raises(CaptureError, match="length_mismatch"):
            await capture_url(
                client,
                "https://example.test/health.csv",
                store,
                CaptureConfig(chunk_bytes=2),
                transaction_warc_path=warc,
            )
    assert body.closed
    assert body.iterations == 1
    assert store.verified_inventory().object_count == 0
    assert not list(store.tmp.iterdir())
    assert not warc.exists()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status", "headers", "config", "error"),
    [
        (403, {}, CaptureConfig(), "terminal_status"),
        (410, {}, CaptureConfig(), "terminal_status"),
        (503, {}, CaptureConfig(), "retryable_status"),
        (200, {"content-length": "invalid"}, CaptureConfig(), "capture_failed"),
        (
            200,
            {"etag": "new"},
            CaptureConfig(expected_etag="old"),
            "validator_mismatch",
        ),
        (
            200,
            {"last-modified": "new"},
            CaptureConfig(expected_last_modified="old"),
            "validator_mismatch",
        ),
    ],
)
async def test_status_and_version_rejections_leave_no_original(
    tmp_path: Path,
    status: int,
    headers: dict[str, str],
    config: CaptureConfig,
    error: str,
) -> None:
    """Denials, withdrawal and changed validators are never successful capture."""
    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                status, headers=headers, content=b"private diagnostic"
            )
        )
    ) as client:
        with pytest.raises(CaptureError, match=error):
            await capture_url(client, "https://example.test/health.csv", store, config)
    assert store.verified_inventory().object_count == 0
    assert not list(store.tmp.iterdir())


@pytest.mark.anyio
@pytest.mark.parametrize("phase", ["before_request", "mid_body"])
async def test_duration_interruption_cleans_unpromoted_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    """A deterministic clock interruption cannot publish a partial object."""
    ticks = iter([0, 2] if phase == "before_request" else [0, 0, 2])
    monkeypatch.setattr(capture, "monotonic", lambda: next(ticks, 2))
    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, stream=OnePassBody((b"partial",)))
        )
    ) as client:
        with pytest.raises(CaptureError, match="timeout"):
            await capture_url(
                client,
                "https://example.test/health.csv",
                store,
                CaptureConfig(max_duration_seconds=1),
            )
    assert store.verified_inventory().object_count == 0
    assert not list(store.tmp.iterdir())


@pytest.mark.anyio
@pytest.mark.parametrize("phase", ["spool", "promotion"])
async def test_storage_interruption_cleans_unpromoted_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    """Spool creation and CAS failures never return successful capture receipts."""
    store = ContentAddressedStore(tmp_path / "cas")

    def fail(*_args: object, **_kwargs: object) -> None:
        message = "synthetic storage failure"
        raise OSError(message)

    if phase == "spool":
        monkeypatch.setattr(capture.tempfile, "NamedTemporaryFile", fail)
    else:
        monkeypatch.setattr(store, "put_stream", fail)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=b"complete")
        )
    ) as client:
        with pytest.raises(CaptureError, match="storage_failed"):
            await capture_url(client, "https://example.test/health.csv", store)
    assert store.verified_inventory().object_count == 0
    assert not list(store.tmp.iterdir())


def test_invalid_capture_bound_is_not_silently_accepted() -> None:
    """Invalid byte budgets fail before any source can be read."""
    with pytest.raises(ValueError, match="invalid_capture_bound"):
        CaptureConfig(max_bytes=0)


@pytest.mark.anyio
async def test_partial_body_retry_reopens_store_and_links_exact_warc(
    tmp_path: Path,
) -> None:
    """Real partial bytes never become originals; retry preserves three hashes."""
    root = tmp_path / "cas"
    store = ContentAddressedStore(root)
    interrupted = OnePassBody((b"year,amount\n",), interrupt=True)
    payload = b"year,amount\n2026,123.450\n"
    complete = OnePassBody((payload[:12], payload[12:]))
    streams = iter((interrupted, complete))

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-length": str(len(payload)), "content-type": "text/csv"},
            stream=next(streams),
        )

    warc = tmp_path / "capture.warc"
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError, match="transport_retryable"):
            await capture_url(
                client,
                "https://example.test/health.csv",
                store,
                CaptureConfig(chunk_bytes=2),
                transaction_warc_path=warc,
            )
        assert not list(store.tmp.iterdir())
        assert store.verified_inventory().object_count == 0
        assert not warc.exists()
        reopened = ContentAddressedStore(root, create=False)
        result = await capture_url(
            client,
            "https://example.test/health.csv",
            reopened,
            CaptureConfig(chunk_bytes=2),
            transaction_warc_path=warc,
        )
    assert interrupted.closed
    assert complete.closed
    assert interrupted.iterations == complete.iterations == 1
    receipt = result.receipt
    assert receipt.path.read_bytes() == payload
    assert receipt.sha256 == hashlib.sha256(payload).hexdigest()
    assert receipt.blake3 == blake3.blake3(payload).hexdigest()
    cid = compute_cidv1_from_sha256(bytes.fromhex(receipt.sha256))
    decoded = base64.b32decode(cid[1:].upper() + "=" * (-len(cid[1:]) % 8))
    assert decoded == b"\x01\x55\x12\x20" + hashlib.sha256(payload).digest()
    raw = warc.read_bytes()
    assert f"WARC-Payload-Digest: sha256:{receipt.sha256}".encode() in raw
    assert raw.split(b"\r\n\r\n", 2)[2] == payload + b"\r\n\r\n"
    assert result.warc_receipt is not None
    assert result.warc_receipt.sha256 == hashlib.sha256(raw).hexdigest()
    assert result.warc_receipt.byte_count == len(raw)
    assert reopened.put_bytes(payload) == receipt
    assert reopened.verified_inventory().object_count == 1


@pytest.mark.parametrize("event", ["withdrawn", "disappeared", "policy_changed"])
def test_health_tombstone_never_removes_original_or_changed_version(
    tmp_path: Path, event: str
) -> None:
    """Policy/reconciliation changes keep both byte versions immutable."""
    store = ContentAddressedStore(tmp_path / "cas")
    old = store.put_bytes(b"year,amount\n2025,1\n")
    new = store.put_bytes(b"year,amount\n2025,2\n")
    before = store.verified_inventory()
    prior = {"health-budget": {"sha256": old.sha256}}
    current = {"health-budget": {"sha256": new.sha256}}
    assert reconcile_capture_observations(current, prior).changed_ids == (
        "health-budget",
    )
    assert reconcile_capture_observations(prior, prior).unchanged_ids == (
        "health-budget",
    )
    result = reconcile_capture_observations(
        current, prior, **{event: frozenset({"health-budget"})}
    )
    assert result.tombstone_ids == ("health-budget",)
    assert store.verified_inventory() == before
    assert store.verify(old.object_id) == old
    assert store.verify(new.object_id) == new


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["empty", "exact", "absent", "gzip"])
async def test_length_boundaries_do_not_compare_encoded_size_to_decoded_size(
    tmp_path: Path, mode: str
) -> None:
    """Content-Length is a wire length, not a decoded payload length."""
    payload = b"" if mode == "empty" else b"health" * 10
    wire = gzip.compress(payload) if mode == "gzip" else payload
    headers = {} if mode == "absent" else {"content-length": str(len(wire))}
    if mode == "gzip":
        headers["content-encoding"] = "gzip"
        assert len(wire) != len(payload)
    body = OnePassBody((wire,))
    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, headers=headers, stream=body)
        )
    ) as client:
        result = await capture_url(client, "https://example.test/health.csv", store)
    assert result.receipt.path.read_bytes() == payload
    assert body.iterations == 1
    assert body.closed


def test_durability_failure_precedes_promotion_and_preserves_prior_objects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed fsync cannot expose new bytes or replace historical objects."""
    store = ContentAddressedStore(tmp_path / "cas")
    prior = store.put_bytes(b"historical")

    def fail(_fd: int) -> None:
        assert store.verified_inventory().object_count == 1
        message = "synthetic durability failure"
        raise OSError(message)

    monkeypatch.setattr("archive_govt_nz.object_store.os.fsync", fail)
    with pytest.raises(ObjectStoreError, match="write_interrupted"):
        store.put_stream(iter((b"new", b" edition")))
    assert store.verify(prior.object_id) == prior
    assert store.verified_inventory().object_count == 1
    assert not list(store.tmp.iterdir())


@pytest.mark.anyio
async def test_health_capture_resumes_verified_checkpoint_without_replacing_warc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resume skips durable captures; new observations retain earlier WARCs."""
    namespace = runpy.run_path(
        str(Path(__file__).parents[3] / "tools/capture_health_resources.py")
    )
    execute = namespace["_capture"]
    census = tmp_path / "census.json"
    census.write_text(
        json.dumps(
            {
                "cutoff": "2026-09-07",
                "records": [
                    {
                        "source_id": name,
                        "url": f"https://www.treasury.govt.nz/{name}.csv",
                        "disposition": "discovered",
                        "media_type": "text/csv",
                    }
                    for name in ("one", "two")
                ],
            }
        )
    )
    args = argparse.Namespace(
        census=census,
        store_root=tmp_path / "cas",
        warc_dir=tmp_path / "warc",
        max_resource_bytes=1024,
        manifest=tmp_path / "manifest.json",
        resume=False,
    )
    calls = []

    async def local_capture(
        _client: object,
        url: str,
        store: ContentAddressedStore,
        _config: CaptureConfig,
        *,
        transaction_warc_path: Path,
    ) -> capture.CaptureResult:
        calls.append(url)
        if len(calls) == 2:
            raise asyncio.CancelledError
        payload = b"synthetic health original"
        receipt = store.put_bytes(payload)
        warc = write_response_record(
            transaction_warc_path,
            url=url,
            status_code=200,
            headers={"content-type": "text/csv"},
            body=payload,
        )
        return capture.CaptureResult(url, 200, "text/csv", receipt, warc)

    monkeypatch.setitem(execute.__globals__, "capture_url", local_capture)
    with pytest.raises(asyncio.CancelledError):
        await execute(args)
    checkpoint = json.loads(args.manifest.read_text())
    first = checkpoint["results"][0]
    prior_path = args.warc_dir / first["warc_path"]
    prior_warc = prior_path.read_bytes()
    assert (
        ContentAddressedStore(args.store_root, create=False)
        .verified_inventory()
        .object_count
        == 1
    )
    args.resume = True
    result = await execute(args)
    assert len(calls) == 3
    assert calls[1] == calls[2]
    assert result["captured"] == 2
    assert prior_path.read_bytes() == prior_warc
    assert result["results"][0] == first
    assert await execute(args) == result
    assert len(calls) == 3
    args.resume = False
    args.manifest = tmp_path / "new-observation.json"
    subsequent = await execute(args)
    assert len(calls) == 5
    assert subsequent["results"][0]["warc_path"] != first["warc_path"]
    assert prior_path.read_bytes() == prior_warc
    assert (
        ContentAddressedStore(args.store_root, create=False)
        .verified_inventory()
        .object_count
        == 1
    )
