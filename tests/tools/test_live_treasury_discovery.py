"""Live-observation evidence writer contracts without network access."""

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from archive_govt_nz.ckan.client import (
    CapabilityObservation,
    TransportAttempt,
)
from archive_govt_nz.ckan.discovery import (
    DatasetReference,
    DiscoveryPage,
    OrganizationObservation,
    TreasuryScope,
)
from archive_govt_nz.ckan.live_evidence import write_live_evidence

if TYPE_CHECKING:
    from pathlib import Path

OBSERVED_AT = datetime(2026, 7, 31, 5, 22, tzinfo=UTC)


def test_writes_exact_raw_observations_and_paired_reports(tmp_path: Path) -> None:
    """A reconciled observation is promoted as a closed local evidence set."""
    capability = CapabilityObservation(
        catalogue_url="https://catalogue.data.govt.nz",
        action_api_version="3",
        ckan_version="2.10.9",
        site_url="https://catalogue.data.govt.nz",
        observed_at=OBSERVED_AT,
        raw_body=b'{"capability":true}',
        raw_sha256="a" * 64,
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
    scope = TreasuryScope(
        organization=OrganizationObservation(
            id="stable-organization-id",
            name="the-treasury",
            title="The Treasury",
            raw_body=b'{"organization":true}',
            raw_sha256="b" * 64,
            observed_at=OBSERVED_AT,
        ),
        datasets=(
            DatasetReference(
                id="dataset-a",
                name="dataset-a",
                metadata_modified="2026-07-31T00:00:00",
            ),
        ),
        pages=(
            DiscoveryPage(
                start=0,
                reported_count=1,
                dataset_ids=("dataset-a",),
                raw_body=b'{"page":true}',
                raw_sha256="c" * 64,
                observed_at=OBSERVED_AT,
            ),
        ),
    )

    summary = write_live_evidence(tmp_path, capability, scope)

    assert summary["status"] == "observed"
    assert summary["treasury_dataset_count"] == 1
    assert (tmp_path / "raw/status_show.json").read_bytes() == capability.raw_body
    assert (
        tmp_path / "raw/organization_show.json"
    ).read_bytes() == scope.organization.raw_body
    assert (tmp_path / "raw/package_search-00000000.json").read_bytes() == scope.pages[
        0
    ].raw_body
    assert (
        json.loads((tmp_path / "ckan-capability.json").read_bytes())["raw_sha256"]
        == capability.raw_sha256
    )
    assert (
        json.loads((tmp_path / "treasury-scope.json").read_bytes())["discovered_count"]
        == 1
    )
    assert (tmp_path / "ckan-capability.md").read_bytes().startswith(b"# CKAN")
    assert (tmp_path / "treasury-scope.md").read_bytes().startswith(b"# Treasury")
    assert not list(tmp_path.rglob("*.tmp"))
