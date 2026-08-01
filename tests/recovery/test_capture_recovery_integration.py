"""Real capture/object-store/ledger restart and idempotency proof."""

from pathlib import Path

import httpx
import pytest

from archive_govt_nz.capture import CaptureError, capture_url
from archive_govt_nz.ledger import Ledger, LedgerError
from archive_govt_nz.object_store import ContentAddressedStore


@pytest.mark.anyio
async def test_interrupted_capture_retries_and_unchanged_rerun_is_idempotent(
    tmp_path: Path,
) -> None:
    """A real interrupted stream leaves no partial object and reruns deduplicate."""
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            message = "simulated disconnect"
            raise httpx.ReadError(message, request=request)
        return httpx.Response(
            200, headers={"content-type": "text/csv"}, content=b"a,b\n1,2\n"
        )

    store = ContentAddressedStore(tmp_path / "objects")
    ledger = Ledger(tmp_path / "ledger.sqlite")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError, match="transport_retryable"):
            await capture_url(client, "https://example.test/data", store)
        result = await capture_url(client, "https://example.test/data", store)
        rerun = await capture_url(client, "https://example.test/data", store)

    assert calls == 3
    assert result.receipt.object_id == rerun.receipt.object_id
    assert len(tuple((store.objects).rglob("*"))) == 2  # one directory and one object
    ledger.record_object(
        result.receipt.object_id,
        result.receipt.sha256,
        result.receipt.blake3,
        result.receipt.byte_count,
        "source",
    )
    with pytest.raises(LedgerError, match="duplicate_object"):
        ledger.record_object(
            rerun.receipt.object_id,
            rerun.receipt.sha256,
            rerun.receipt.blake3,
            rerun.receipt.byte_count,
            "source",
        )
    ledger.close()
