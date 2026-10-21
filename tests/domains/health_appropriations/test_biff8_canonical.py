"""Witness-aware canonical and Gold products replay every admitted source field."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_biff8 import _fixture
from tests.domains.health_appropriations.test_canonical_consumer import _package

from archive_govt_nz.domains.health_appropriations import (
    biff8_canonical,
    canonical_gold_export,
    canonical_gold_queries,
    canonical_gold_verification,
    gold_metadata,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_verified_canonical_tables,
)

if TYPE_CHECKING:
    from typing import Any


def _pin(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, *, edition: int = 2019
) -> tuple[Path, Path, str, dict[str, Any]]:
    payload, profile = _fixture(kind, edition=edition)
    profiles = getattr(
        biff8_canonical.budget_biff8,
        "PROFILES" if edition == 2019 else f"PROFILES_{edition}",
    )
    monkeypatch.setitem(profiles, kind, profile)
    original = tmp_path / "original.xls"
    original.write_bytes(payload)
    snapshot = biff8_canonical.budget_biff8.parse_snapshot(
        payload, profile=profile, observed_at="2026-10-20T00:00:00Z"
    )
    silver = tmp_path / "silver"
    biff8_canonical.write_workbook_outputs(
        silver, dict(snapshot.tables), dict(snapshot.metadata)
    )
    if kind == "revenue":
        # A different Parquet encoding must preserve the same source contracts.
        marker = silver / "MANIFEST.json"
        manifest = json.loads(marker.read_bytes())
        for name, table in snapshot.tables.items():
            pq.write_table(
                table, silver / name, compression="zstd", use_dictionary=False
            )
            manifest["output_sha256"][name] = _pin(silver / name)
        marker.write_text(json.dumps(manifest))
    return original, silver, _pin(silver / "MANIFEST.json"), dict(snapshot.tables)


def _assert_2014_lineage(kind: str, fields: list[str], flags: list[str]) -> None:
    assert ("is_mca" if kind == "expenditure" else "periodicity") in fields
    if kind == "revenue":
        assert (
            "source_edition_conflict_resolved_by_title_and_estimates_context" in flags
        )


@pytest.mark.parametrize(
    "edition", [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
)
@pytest.mark.parametrize("kind", ["expenditure", "revenue"])
def test_biff8_canonical_and_gold_preserve_binary_evidence_and_repeat_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, edition: int
) -> None:
    original, silver, pin, source = _source(
        tmp_path, monkeypatch, kind, edition=edition
    )
    name = biff8_canonical.FACTS[kind]
    canonical = tmp_path / "canonical"
    planned = biff8_canonical.export_canonical(
        silver, pin, original, kind, canonical, observed_at="2026-10-20T00:00:00Z"
    )
    assert planned["status"] == "planned"
    assert not canonical.exists()
    biff8_canonical.export_canonical(
        silver,
        pin,
        original,
        kind,
        canonical,
        write=True,
        observed_at="2026-10-20T00:00:00Z",
    )
    repeated = tmp_path / "canonical_again"
    biff8_canonical.export_canonical(
        silver,
        pin,
        original,
        kind,
        repeated,
        write=True,
        observed_at="2026-10-20T00:00:00Z",
    )
    assert {p.name: _pin(p) for p in canonical.iterdir()} == {
        p.name: _pin(p) for p in repeated.iterdir()
    }
    product = "biff8_budget" if kind == "expenditure" else "biff8_revenue"
    package = CanonicalPackageInput(
        product, canonical, _pin(canonical / "MANIFEST.json"), original, silver, pin
    )
    tables, _ = read_verified_canonical_tables(package)
    fact = tables[name].to_pylist()[0]
    assert fact["source_vintage"] == f"Budget-{edition}"
    assert fact["transformation_id"] == f"budget-{edition}-biff8-canonical/v1"
    assert fact["value_token"] is None
    assert fact["source_decimal_precision"] is None
    assert fact["value_basis"] == "biff8_stored_integer/v1"
    assert fact["canonical_stored_integer"] == "123"
    assert (
        fact["numeric_evidence_id"]
        in tables["numeric_evidence"]["numeric_evidence_id"].to_pylist()
    )
    assert fact["currency"] is None
    if edition == 2014:
        _assert_2014_lineage(
            kind, tables["field_lineage"]["field"].to_pylist(), fact["quality_flags"]
        )
    assert fact["valid_time_start"] is None
    assert tables["numeric_evidence"].equals(source["numeric_evidence.parquet"])
    assert tables["field_lineage"].num_rows == source["field_lineage.parquet"].num_rows
    gold = tmp_path / "gold"
    receipt = canonical_gold_export.export_canonical_gold((package,), gold, write=True)
    again = tmp_path / "gold_again"
    canonical_gold_export.export_canonical_gold((package,), again, write=True)
    assert {p.name: _pin(p) for p in gold.iterdir()} == {
        p.name: _pin(p) for p in again.iterdir()
    }
    assert receipt["products"][product]["aggregation"] == "none"
    assert receipt["quality_report"]["input_record_count"] == 1
    assert receipt["temporal_coverage_report"]["groups"][0]["observed_periods"] == [
        {"period_token": str(edition), "observation_count": 1}
    ]
    numeric_path = gold / (product + "_numeric.parquet")
    assert pq.read_table(numeric_path).equals(source["numeric_evidence.parquet"])
    queried = canonical_gold_queries.query_canonical_gold(
        gold, _pin(gold / "MANIFEST.json"), product=product
    )
    assert queried["status"] == "verified"
    assert queried["rows"][0]["numeric_evidence_id"] == fact["numeric_evidence_id"]
    assert queried["rows"][0]["amount"] == "123.000000000000000000"
    amount_links = [
        c
        for r in receipt["source_drillthrough"]["records"]
        for c in r["source_coordinates"]
        if c["field"] == "amount"
    ]
    assert amount_links[0]["numeric_evidence_id"] == fact["numeric_evidence_id"]
    assert amount_links[0]["witness_output"] == product + "_numeric.parquet"
    with pytest.raises(ValueError, match="biff8_canonical_contract"):
        biff8_canonical.export_canonical(
            silver,
            pin,
            original,
            kind,
            canonical,
            write=True,
            observed_at="2026-10-20T00:00:00Z",
        )
    (canonical / "unexpected").write_bytes(b"invalid")
    with pytest.raises(ValueError, match="local_provenance_reader_invalid"):
        read_verified_canonical_tables(package)


@pytest.mark.parametrize(
    "name",
    [
        "budget_facts.parquet",
        "field_lineage.parquet",
        "row_dispositions.parquet",
        "numeric_evidence.parquet",
    ],
)
def test_rehashed_silver_tampering_fails_original_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original, silver, _, _ = _source(tmp_path, monkeypatch, "revenue")
    path = silver / name
    table = pq.read_table(path)
    pq.write_table(table.slice(1), path)
    marker = silver / "MANIFEST.json"
    manifest = json.loads(marker.read_bytes())
    manifest["output_sha256"][name] = _pin(path)
    marker.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="biff8_canonical_contract"):
        biff8_canonical.project_package(
            silver,
            _pin(marker),
            original,
            "revenue",
            observed_at="2026-10-20T00:00:00Z",
        )


def test_mixed_gold_retains_full_legacy_lineage_in_fixed_companion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, silver, pin, _ = _source(tmp_path, monkeypatch, "expenditure")
    canonical = tmp_path / "canonical"
    biff8_canonical.export_canonical(
        silver,
        pin,
        original,
        "expenditure",
        canonical,
        write=True,
        observed_at="2026-10-20T00:00:00Z",
    )
    biff = CanonicalPackageInput(
        "biff8_budget",
        canonical,
        _pin(canonical / "MANIFEST.json"),
        original,
        silver,
        pin,
    )
    legacy = _package(tmp_path / "legacy")
    expected, _ = read_verified_canonical_tables(legacy)
    output = tmp_path / "mixed"
    receipt = canonical_gold_export.export_canonical_gold(
        (legacy, biff), output, write=True
    )
    companion = output / "canonical_input_lineage.parquet"
    assert pq.read_table(companion).equals(
        expected["field_lineage"].sort_by([("lineage_id", "ascending")]),
        check_metadata=True,
    )
    assert receipt["outputs"][companion.name]["sha256"] == _pin(companion)
    legacy_ids = set(expected["field_lineage"]["target_record_id"].to_pylist())
    coordinates = [
        c
        for r in receipt["source_drillthrough"]["records"]
        if r["input_record_id"] in legacy_ids
        for c in r["source_coordinates"]
    ]
    assert coordinates
    assert all(
        c["field"] in {"amount", "value", "unit", "period_token"} for c in coordinates
    )
    assert all(c["full_lineage_output"] == companion.name for c in coordinates)
    assert {c["canonical_lineage_id"] for c in coordinates} <= set(
        expected["field_lineage"]["lineage_id"].to_pylist()
    )
    for product in ("budget", "biff8_budget"):
        assert (
            canonical_gold_queries.query_canonical_gold(
                output, _pin(output / "MANIFEST.json"), product=product
            )["status"]
            == "verified"
        )
    repeated = tmp_path / "mixed_again"
    canonical_gold_export.export_canonical_gold((legacy, biff), repeated, write=True)
    assert {p.name: _pin(p) for p in output.iterdir()} == {
        p.name: _pin(p) for p in repeated.iterdir()
    }


def test_biff8_gold_preserves_distinct_vintages_and_refuses_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packages = []
    for kind in ("expenditure", "revenue"):
        for edition in (2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019):
            root = tmp_path / f"{kind}-{edition}"
            root.mkdir()
            original, silver, pin, _ = _source(root, monkeypatch, kind, edition=edition)
            canonical = root / "canonical"
            biff8_canonical.export_canonical(
                silver,
                pin,
                original,
                kind,
                canonical,
                write=True,
                observed_at="2026-10-20T00:00:00Z",
            )
            product = "biff8_budget" if kind == "expenditure" else "biff8_revenue"
            packages.append(
                CanonicalPackageInput(
                    product,
                    canonical,
                    _pin(canonical / "MANIFEST.json"),
                    original,
                    silver,
                    pin,
                )
            )
    gold = tmp_path / "gold"
    receipt = canonical_gold_export.export_canonical_gold(
        tuple(packages), gold, write=True
    )
    assert receipt["quality_report"]["input_record_count"] == 20
    reference = receipt["source_drillthrough"]
    assert (
        reference["schema_version"] == "archive-govt-nz.health-source-drillthrough/v3"
    )
    companion = gold / "source_drillthrough.json"
    drillthrough = json.loads(companion.read_bytes())
    assert reference["record_count"] == len(drillthrough["records"]) == 20
    assert reference["sha256"] == _pin(companion)
    assert reference["bytes"] == companion.stat().st_size
    assert all(row["source_coordinates"] for row in drillthrough["records"])
    assert (
        canonical_gold_verification.read_source_drillthrough(gold, receipt)
        == drillthrough
    )
    metadata_root = tmp_path / "metadata"
    metadata_receipt = gold_metadata.export_gold_metadata(
        (
            gold_metadata.GoldInput(
                "canonical_source_separated", gold, _pin(gold / "MANIFEST.json")
            ),
        ),
        metadata_root,
        write=True,
    )
    assert metadata_receipt["status"] == "written"
    projected = json.loads((metadata_root / "catalogue.json").read_bytes())["packages"][
        0
    ]
    expected_hashes = {
        coordinate["source_object_sha256"]
        for record in drillthrough["records"]
        for coordinate in record["source_coordinates"]
    }
    assert expected_hashes <= {
        ref["value"]
        for ref in projected["source_references"]
        if ref["field_path"].startswith("/source_drillthrough/records/")
        and ref["kind"] == "sha256"
    }
    for product in ("biff8_budget", "biff8_revenue"):
        result = canonical_gold_queries.query_canonical_gold(
            gold, _pin(gold / "MANIFEST.json"), product=product
        )
        assert result["status"] == "verified"
        assert result["total_rows"] == 10
        assert {r["source_vintage"] for r in result["rows"]} == {
            "Budget-2010",
            "Budget-2011",
            "Budget-2012",
            "Budget-2013",
            "Budget-2014",
            "Budget-2015",
            "Budget-2016",
            "Budget-2017",
            "Budget-2018",
            "Budget-2019",
        }
        assert receipt["products"][product]["aggregation"] == "none"
        assert receipt["products"][product]["vintage_pooling"] == "not_performed"
    repeat = tmp_path / "repeat"
    canonical_gold_export.export_canonical_gold(
        tuple(reversed(packages)), repeat, write=True
    )
    assert {p.name: _pin(p) for p in gold.iterdir()} == {
        p.name: _pin(p) for p in repeat.iterdir()
    }
    with pytest.raises(ValueError, match="canonical_gold_export_invalid"):
        canonical_gold_export.export_canonical_gold(
            (*packages, packages[0]), tmp_path / "duplicate"
        )
    original = companion.read_bytes()
    companion.write_bytes(original + b" ")
    assert (
        canonical_gold_queries.query_canonical_gold(
            gold, _pin(gold / "MANIFEST.json"), product="biff8_budget"
        )["status"]
        == "failed"
    )
    companion.write_bytes(original)
    invalid = json.loads((gold / "MANIFEST.json").read_bytes())
    invalid["source_drillthrough"]["record_count"] += 1
    (gold / "MANIFEST.json").write_text(json.dumps(invalid))
    assert (
        canonical_gold_verification.verify_canonical_gold_package(
            gold, _pin(gold / "MANIFEST.json")
        )["status"]
        == "failed"
    )
