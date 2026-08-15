"""Complete, drift-aware global CKAN catalogue discovery contracts."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.ckan.client import ActionObservation, TransportAttempt
from archive_govt_nz.ckan.envelope import ActionResponse
from archive_govt_nz.ckan.global_discovery import (
    GlobalCkanDiscovery,
    GlobalCkanDiscoveryError,
    canonical_global_scope_manifest,
    global_scope_report_markdown,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

OBSERVED_AT = datetime(2026, 8, 16, 2, 0, tzinfo=UTC)


def make_observation(result: dict[str, object]) -> ActionObservation:
    """Build exact deterministic Action evidence for a fixture result."""
    document: dict[str, object] = {"success": True, "result": result}
    raw_body = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return ActionObservation(
        response=ActionResponse(
            status_code=200,
            result=result,
            response_document=document,
        ),
        raw_body=raw_body,
        raw_sha256=hashlib.sha256(raw_body).hexdigest(),
        observed_at=OBSERVED_AT,
        attempts=(
            TransportAttempt(
                attempt=1,
                status_code=200,
                error_class=None,
                observed_at=OBSERVED_AT,
            ),
        ),
        response_headers={"content-type": "application/json"},
    )


class FakeActionClient:
    """Ordered deterministic Action client fixture."""

    def __init__(self, *responses: ActionObservation) -> None:
        """Retain expected observations."""
        self._responses = iter(responses)
        self.requests: list[tuple[str, dict[str, object]]] = []

    async def action(
        self,
        action: str,
        params: Mapping[str, object] | None = None,
    ) -> ActionObservation:
        """Record the request and return its fixture observation."""
        self.requests.append((action, dict(params or {})))
        return next(self._responses)

    async def action_get(
        self,
        action: str,
        params: Mapping[str, object] | None = None,
    ) -> ActionObservation:
        """Record GET request and return its fixture observation."""
        return await self.action(action, params)


def sample_dataset(
    identifier: str,
    org: str = "test-org",
    res_ids: list[str] | None = None,
) -> dict[str, object]:
    """Return a representative CKAN dataset payload."""
    res_list = res_ids or [f"res-{identifier}-1"]
    return {
        "id": identifier,
        "name": f"dataset-{identifier}",
        "title": f"Dataset {identifier}",
        "organization": {"name": org, "title": f"Org {org}"},
        "license_id": "cc-by",
        "license_title": "Creative Commons Attribution 4.0",
        "metadata_modified": "2026-08-16T00:00:00.000000",
        "resources": [
            {
                "id": r_id,
                "name": f"Resource {r_id}",
                "url": f"https://data.example.govt.nz/{r_id}.csv",
                "format": "CSV",
                "size": 1024,
                "datastore_active": False,
            }
            for r_id in res_list
        ],
    }


def page(count: int, *identifiers: str) -> ActionObservation:
    """Return one unconstrained package_search page observation."""
    return make_observation(
        {
            "count": count,
            "results": [sample_dataset(identifier) for identifier in identifiers],
        }
    )


def test_discovers_global_catalog_across_all_organizations() -> None:
    """Global discovery queries package_search across all packages."""
    client = FakeActionClient(
        page(3, "ds-1", "ds-2"),
        page(3, "ds-3"),
    )
    discovery = GlobalCkanDiscovery(client, page_size=2)
    scope = asyncio.run(discovery.discover())

    assert scope.discovered_dataset_count == 3
    assert scope.discovered_resource_count == 3
    assert scope.dataset_ids == ("ds-1", "ds-2", "ds-3")
    assert scope.reported_counts == (3, 3)
    assert len(scope.pages) == 2
    assert client.requests == [
        (
            "package_search",
            {"q": "*:*", "rows": 2, "sort": "id asc", "start": 0},
        ),
        (
            "package_search",
            {"q": "*:*", "rows": 2, "sort": "id asc", "start": 2},
        ),
    ]


def test_global_scope_manifest_and_markdown_serialization() -> None:
    """Manifest and report serialize deterministically with exact hashes."""
    first_page = page(2, "ds-1", "ds-2")
    client = FakeActionClient(first_page)
    scope = asyncio.run(GlobalCkanDiscovery(client, page_size=2).discover())

    manifest_bytes = canonical_global_scope_manifest(scope)
    markdown_bytes = global_scope_report_markdown(scope)

    assert manifest_bytes.endswith(b"\n")
    assert markdown_bytes.startswith(b"# Global CKAN discovery scope\n")
    manifest = json.loads(manifest_bytes)
    assert manifest["schema_version"] == "archive-govt-nz.global-ckan-scope/v1"
    assert manifest["discovered_dataset_count"] == 2
    assert manifest["discovered_resource_count"] == 2
    assert len(manifest["datasets"]) == 2
    assert (
        manifest["datasets"][0]["resources"][0]["url"]
        == "https://data.example.govt.nz/res-ds-1-1.csv"
    )


def test_duplicate_dataset_identifier_fails_closed() -> None:
    """Duplicate dataset IDs during global pagination trigger an error."""
    search = make_observation(
        {
            "count": 2,
            "results": [sample_dataset("ds-1"), sample_dataset("ds-1")],
        }
    )
    with pytest.raises(GlobalCkanDiscoveryError) as exc_info:
        asyncio.run(GlobalCkanDiscovery(FakeActionClient(search)).discover())

    assert exc_info.value.error_class == "duplicate_dataset_id"


def test_invalid_page_size_fails() -> None:
    """Page size must be at least 1."""
    with pytest.raises(GlobalCkanDiscoveryError) as exc_info:
        GlobalCkanDiscovery(FakeActionClient(), page_size=0)

    assert exc_info.value.error_class == "page_size"
