"""The actual redirect budget bounds requests and retains terminal evidence."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore


@pytest.mark.anyio
@pytest.mark.parametrize("budget", [0, 1, 3])
@pytest.mark.parametrize("extra", [0, 1])
async def test_redirect_budget_accepts_exact_limit_and_rejects_next_hop(
    tmp_path: Path, budget: int, extra: int
) -> None:
    """Real bounded HTTP responses, not patched ranges or invalid configs."""
    calls: list[str] = []
    responses: list[httpx.Response] = []
    payload = b"synthetic fiscal original"
    redirects = budget + extra

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        number = int(request.url.path.rsplit("/", 1)[-1])
        response = (
            httpx.Response(302, headers={"location": f"/{number + 1}"})
            if number < redirects
            else httpx.Response(200, content=payload)
        )
        responses.append(response)
        return response

    store = ContentAddressedStore(tmp_path / "cas")
    warc = tmp_path / "response.warc"
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        if extra:
            with pytest.raises(CaptureError, match=r"^redirect_limit$") as error:
                await capture_url(
                    client,
                    "https://example.test/0",
                    store,
                    CaptureConfig(max_redirects=budget),
                    transaction_warc_path=warc,
                )
            assert [attempt.outcome for attempt in error.value.attempts] == [
                "redirect"
            ] * budget + ["redirect_limit"]
            assert [attempt.status_code for attempt in error.value.attempts] == [
                302
            ] * (budget + 1)
            assert [attempt.url for attempt in error.value.attempts] == calls
            assert store.verified_inventory().object_count == 0
            assert not warc.exists()
        else:
            result = await capture_url(
                client,
                "https://example.test/0",
                store,
                CaptureConfig(max_redirects=budget),
                transaction_warc_path=warc,
            )
            assert result.receipt.path.read_bytes() == payload
            assert result.redirects == budget
            assert result.attempts == budget + 1
            assert [attempt.outcome for attempt in result.attempt_receipts] == [
                "redirect"
            ] * budget + ["captured"]
            assert warc.exists()
    assert calls == [f"https://example.test/{number}" for number in range(budget + 1)]
    assert all(response.is_closed for response in responses)
    assert not list(store.tmp.iterdir())


@pytest.mark.anyio
@pytest.mark.parametrize("budget", [0, 3])
async def test_missing_location_fails_immediately_without_using_remaining_budget(
    tmp_path: Path, budget: int
) -> None:
    """A malformed redirect is terminal even with unused request budget."""
    calls = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(302)

    store = ContentAddressedStore(tmp_path / "cas")
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(CaptureError, match=r"^redirect_limit$") as error:
            await capture_url(
                client,
                "https://example.test/0",
                store,
                CaptureConfig(max_redirects=budget),
            )
    assert calls == ["https://example.test/0"]
    assert len(error.value.attempts) == 1
    assert error.value.attempts[0].outcome == "redirect_limit"
    assert error.value.attempts[0].status_code == 302
    assert store.verified_inventory().object_count == 0
