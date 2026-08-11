"""Transport fallback contracts for the broader-health discovery command."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Protocol, cast

import pytest

from archive_govt_nz.ckan.envelope import CkanProtocolError, CkanTransportError


class _DiscoveryModule(Protocol):
    @staticmethod
    async def page_with_fallback(
        client: object, params: dict[str, object]
    ) -> tuple[object, str, dict[str, object] | None]: ...


_MODULE_PATH = Path(__file__).parents[2] / "tools" / "discover_health_metadata.py"
_SPEC = importlib.util.spec_from_file_location("discover_health_metadata", _MODULE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
page_with_fallback = cast("_DiscoveryModule", _MODULE).page_with_fallback


class _Client:
    def __init__(self, failure: Exception) -> None:
        self.failure = failure
        self.get_calls: list[tuple[str, dict[str, object]]] = []

    async def action(self, _action: str, _params: dict[str, object]) -> object:
        raise self.failure

    async def action_get(self, action: str, params: dict[str, object]) -> str:
        self.get_calls.append((action, params))
        return "get-result"


@pytest.mark.parametrize(
    ("failure", "status_code", "error_class"),
    [
        (CkanTransportError(400, {}), 400, "http_status"),
        (CkanProtocolError(), None, "protocol_error"),
    ],
)
@pytest.mark.anyio
async def test_post_failure_uses_get_with_deterministic_receipt(
    failure: Exception,
    status_code: int | None,
    error_class: str,
) -> None:
    """Any bounded POST failure may fall back to the identically bounded GET path."""
    client = _Client(failure)
    params: dict[str, object] = {"q": "health", "rows": 25}

    result, method, receipt = await page_with_fallback(
        client,
        params,  # type: ignore[arg-type]
    )

    assert result == "get-result"
    assert method == "GET"
    assert client.get_calls == [("package_search", params)]
    assert receipt == {
        "method": "POST",
        "status": "failed",
        "status_code": status_code,
        "error_class": error_class,
    }
