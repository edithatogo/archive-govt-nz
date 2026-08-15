"""Tests for unified harvest orchestrator CLI."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from archive_govt_nz.ckan.global_discovery import (
    GlobalCkanScope,
    GlobalDatasetReference,
    GlobalDiscoveryPage,
    GlobalResourceReference,
)
from archive_govt_nz.object_store import ObjectStoreReceipt

_SPEC = importlib.util.spec_from_file_location(
    "harvest_ckan",
    Path(__file__).parents[2] / "tools" / "harvest_ckan.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
HarvestConfig = _MODULE.HarvestConfig
execute_unified_harvest = _MODULE.execute_unified_harvest


def test_unified_harvest_orchestrator(tmp_path: Path) -> None:
    """Full orchestration runs discovery, policy, capture, and packaging."""
    evidence_dir = tmp_path / "evidence"
    objects_dir = tmp_path / "objects"

    fake_resource = GlobalResourceReference(
        id="res-1",
        name="Table 1",
        url="https://test.govt.nz/data.csv",
        format="CSV",
        size=1024,
        license_id="cc-by",
        created="2026-08-01T00:00:00Z",
        last_modified="2026-08-02T00:00:00Z",
        datastore_active=False,
    )
    fake_dataset = GlobalDatasetReference(
        id="ds-1",
        name="dataset-1",
        title="Dataset 1",
        organization_name="test-org",
        organization_title="Test Org",
        license_id="cc-by",
        license_title="Creative Commons Attribution 4.0",
        metadata_created="2026-08-01T00:00:00Z",
        metadata_modified="2026-08-02T00:00:00Z",
        resources=(fake_resource,),
    )
    fake_page = GlobalDiscoveryPage(
        start=0,
        reported_count=1,
        dataset_ids=("ds-1",),
        raw_body=b'{"success":true}',
        raw_sha256="fake-raw-sha256",
        observed_at=datetime.now(UTC),
    )
    fake_scope = GlobalCkanScope(datasets=(fake_dataset,), pages=(fake_page,))

    mock_receipt = ObjectStoreReceipt(
        object_id="sha256:abc1234",
        sha256="abc1234",
        blake3="blake1234",
        byte_count=1024,
        path=objects_dir / "abc1234",
    )

    async def mock_capture(*_args: object, **_kwargs: object) -> object:
        class MockResult:
            receipt = mock_receipt
            status_code = 200
            content_type = "text/csv"
            elapsed_seconds = 0.05

        return MockResult()

    with (
        patch(
            "archive_govt_nz.ckan.global_discovery.GlobalCkanDiscovery.discover",
            new_callable=AsyncMock,
            return_value=fake_scope,
        ),
        patch(
            "archive_govt_nz.global_capture.capture_url",
            side_effect=mock_capture,
        ),
    ):
        config = HarvestConfig(
            base_url="https://mock.catalogue.data.govt.nz",
            objects_dir=objects_dir,
            evidence_dir=evidence_dir,
            page_size=10,
            max_workers=2,
        )
        summary = execute_unified_harvest(config)

    assert summary["schema_version"] == "archive-govt-nz.global-harvest-summary/v1"
    assert summary["discovered_datasets"] == 1
    assert summary["discovered_resources"] == 1
    assert summary["successful_captures"] == 1
    assert (evidence_dir / "global-ckan-scope.json").is_file()
    assert (evidence_dir / "global-rights-classification.json").is_file()
    assert (evidence_dir / "global-capture-receipt.json").is_file()
    assert (evidence_dir / "ro-crate-metadata.jsonld").is_file()
    assert (evidence_dir / "preservation-bag" / "bagit.txt").is_file()
