"""Tests for the global CKAN discovery CLI tool."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from archive_govt_nz.ckan.global_discovery import (
    GlobalCkanScope,
    GlobalDatasetReference,
    GlobalDiscoveryPage,
    GlobalResourceReference,
)

_SPEC = importlib.util.spec_from_file_location(
    "discover_global_ckan",
    Path(__file__).parents[2] / "tools" / "discover_global_ckan.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
main = _MODULE.main


def test_discover_global_ckan_cli(tmp_path: Path) -> None:
    """Test CLI execution and receipt emission with mocked scope."""
    output_json = tmp_path / "global-scope.json"
    output_md = tmp_path / "global-scope.md"
    raw_dir = tmp_path / "raw"

    mock_scope = GlobalCkanScope(
        datasets=(
            GlobalDatasetReference(
                id="ds-1",
                name="dataset-1",
                title="Dataset 1",
                organization_name="org-1",
                organization_title="Org 1",
                license_id="cc-by",
                license_title="Creative Commons",
                metadata_created=None,
                metadata_modified=None,
                resources=(
                    GlobalResourceReference(
                        id="res-1",
                        name="Resource 1",
                        url="https://example.govt.nz/data.csv",
                        format="CSV",
                        size=500,
                        license_id=None,
                        created=None,
                        last_modified=None,
                        datastore_active=False,
                    ),
                ),
            ),
        ),
        pages=(
            GlobalDiscoveryPage(
                start=0,
                reported_count=1,
                dataset_ids=("ds-1",),
                raw_body=b'{"count":1,"results":[]}',
                raw_sha256="fake-sha256",
                observed_at=__import__("datetime").datetime(
                    2026, 8, 16, 0, 0, tzinfo=__import__("datetime").UTC
                ),
            ),
        ),
    )

    with (
        patch(
            "archive_govt_nz.ckan.global_discovery.GlobalCkanDiscovery.discover",
            new_callable=AsyncMock,
            return_value=mock_scope,
        ),
        patch(
            "sys.argv",
            [
                "discover_global_ckan.py",
                "--output",
                str(output_json),
                "--markdown-output",
                str(output_md),
                "--raw-dir",
                str(raw_dir),
                "--page-size",
                "50",
            ],
        ),
    ):
        code = main()

    assert code == 0
    assert output_json.is_file()
    assert output_md.is_file()
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert data["discovered_dataset_count"] == 1
    assert (raw_dir / "package_search-00000000.json").is_file()
