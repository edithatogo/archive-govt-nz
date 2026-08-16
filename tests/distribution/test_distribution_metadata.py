"""Test suite for open distribution metadata generation (Croissant, RO-Crate, DCAT)."""

from __future__ import annotations

from archive_govt_nz.distribution.metadata import (
    generate_croissant_metadata,
    generate_dcat_metadata,
    generate_ro_crate_metadata,
)


def test_generate_croissant_metadata() -> None:
    """Validate Croissant JSON-LD structure."""
    res = generate_croissant_metadata(
        dataset_id="edithatogo/corpus-social-media-government-nz",
        title="NZ Government Social Media Corpus",
        description="Archival records of NZ public communications.",
    )
    assert res["@type"] == "Dataset"
    assert res["name"] == "edithatogo/corpus-social-media-government-nz"
    assert res["@context"]["citeAs"] == "cr:citeAs"


def test_generate_ro_crate_metadata() -> None:
    """Validate RO-Crate 1.1 structure."""
    records = [{"id": "rec-1", "path": "data/rec-1.json"}]
    res = generate_ro_crate_metadata(
        crate_id="crate-001",
        title="Preservation RO-Crate",
        records=records,
    )
    assert "@graph" in res
    assert len(res["@graph"]) == 2
    assert res["@graph"][1]["identifier"] == "crate-001"


def test_generate_dcat_metadata() -> None:
    """Validate DCAT-AP catalog metadata."""
    datasets = [{"@type": "dcat:Dataset", "dct:title": "Health Dataset"}]
    res = generate_dcat_metadata(
        catalog_id="cat-nz-govt",
        title="NZ Govt Open Catalog",
        datasets=datasets,
    )
    assert res["@type"] == "dcat:Catalog"
    assert res["dct:identifier"] == "cat-nz-govt"
    assert len(res["dcat:dataset"]) == 1
