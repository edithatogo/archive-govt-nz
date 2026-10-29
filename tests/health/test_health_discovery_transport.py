"""Read-only transport contracts for the broader-health discovery command."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import httpx

from archive_govt_nz.ckan.client import BoundedCkanClient

if TYPE_CHECKING:
    import pytest


class _DiscoveryModule(Protocol):
    @staticmethod
    def validate_previous_fingerprints(
        previous: dict[str, object] | None,
    ) -> tuple[str, dict[str, str]]: ...


_MODULE_PATH = Path(__file__).parents[2] / "tools" / "discover_health_metadata.py"
_SPEC = importlib.util.spec_from_file_location("discover_health_metadata", _MODULE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
previous_fingerprints = cast(
    "_DiscoveryModule", cast("object", _MODULE)
).validate_previous_fingerprints


def test_discovery_uses_get_and_stops_on_access_challenge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A challenged read is retained once, without POST or page-size retries."""
    observed: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request)
        return httpx.Response(403, text="<html>Access denied</html>")

    original = BoundedCkanClient
    monkeypatch.setattr(
        _MODULE,
        "BoundedCkanClient",
        lambda config: original(config, transport=httpx.MockTransport(handler)),
    )
    result = asyncio.run(
        _MODULE._discover(  # noqa: SLF001 - exercise the bounded discovery driver
            "https://catalogue.data.govt.nz", 100, raw_dir=tmp_path
        )
    )
    assert result["status"] == "unavailable"
    assert len(observed) == 1
    assert observed[0].method == "GET"
    assert result["attempts"] == [
        {"method": "GET", "rows": 100, "status_code": 403, "error_class": "http_status"}
    ]
    assert result["policy"]["post_primary_get_after_failure"] is False


def test_previous_manifest_must_be_observed_and_fingerprint_complete() -> None:
    """Only a complete hash-pinned prior discovery can support drift counts."""
    assert previous_fingerprints(None) == ("absent", {})
    valid = {
        "schema_version": "archive-govt-nz.health-discovery/v1",
        "status": "observed",
        "dataset_count": 1,
        "metadata_fingerprints": {"one": "a" * 64},
    }
    assert previous_fingerprints(valid) == ("compared", {"one": "a" * 64})
    assert previous_fingerprints({**valid, "dataset_count": 2}) == ("invalid", {})
    assert previous_fingerprints(
        {**valid, "metadata_fingerprints": {"one": "unverified"}}
    ) == ("invalid", {})
