"""Verified canonical packages are the direct analytical input boundary."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs
from tests.domains.health_appropriations.test_budget_revenue_projection import (
    inputs as revenue_inputs,
)
from tests.domains.health_appropriations.test_historical_snapshot import (
    _package as historical_raw_package,
)
from tests.domains.health_appropriations.test_moh_indicators import source as moh_source
from tests.domains.health_appropriations.test_pharmac_canonical_projection import (
    package as pharmac_silver_package,
)

from archive_govt_nz.domains.health_appropriations import (
    budget_revenue_canonical_export,
    canonical_consumer,
    canonical_gold_export,
)
from archive_govt_nz.domains.health_appropriations.budget_export import (
    export_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.budget_revenue_canonical_export import (
    export_budget_revenue,
)
from archive_govt_nz.domains.health_appropriations.canonical_consumer import (
    HISTORICAL_COVERAGE_SCHEMA,
    HISTORICAL_NOMINAL_SCHEMA,
    HISTORICAL_OBSERVATION_SCHEMA,
    NOMINAL_BUDGET_SCHEMA,
    query_historical_nominal,
    query_historical_observations,
    query_nominal_budget,
    query_nominal_revenue,
    summarize_historical_coverage,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_export import (
    GoldInputs,
    MohGoldInput,
    PharmacGoldInput,
    export_canonical_gold,
    export_historical_gold,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_verification import (
    verify_canonical_gold_package,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    export_historical_canonical,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_verified_canonical_tables,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    PROFILES as MOH_PROFILES,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    MohIndicatorInput,
)
from archive_govt_nz.domains.health_appropriations.moh_indicators import (
    normalize_moh_indicators,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def _package(tmp_path: Path) -> CanonicalPackageInput:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = inputs(tmp_path)
    output = tmp_path / "canonical"
    export_budget_appropriations(
        tmp_path / "package",
        source["manifest_sha256"],
        tmp_path / "source.xlsx",
        output,
        dry_run=False,
    )
    marker = output / "LOCAL_BUDGET.json"
    return CanonicalPackageInput(
        kind="budget",
        root=output,
        marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest(),
        original=tmp_path / "source.xlsx",
        raw_root=tmp_path / "package",
        raw_manifest_sha256=source["manifest_sha256"],
    )


def _historical_package(tmp_path: Path) -> CanonicalPackageInput:
    tmp_path.mkdir(parents=True, exist_ok=True)
    raw, original, pin = historical_raw_package(tmp_path)
    output = tmp_path / "historical-canonical"
    export_historical_canonical(raw, original, pin, output, write=True)
    marker = output / "LOCAL_CANONICAL.json"
    return CanonicalPackageInput(
        kind="historical",
        root=output,
        marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest(),
        original=original,
        raw_root=raw,
        raw_manifest_sha256=pin,
    )


def _revenue_package(tmp_path: Path) -> CanonicalPackageInput:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = revenue_inputs(tmp_path)
    output = tmp_path / "canonical-revenue"
    export_budget_revenue(
        source["root"],
        source["manifest_sha256"],
        source["original"],
        output,
        dry_run=False,
    )
    marker = output / budget_revenue_canonical_export.MARKER
    return CanonicalPackageInput(
        kind="revenue",
        root=output,
        marker_sha256=hashlib.sha256(marker.read_bytes()).hexdigest(),
        original=source["original"],
        raw_root=source["root"],
        raw_manifest_sha256=source["manifest_sha256"],
    )


def _assert_temporal_report(manifest: dict[str, Any]) -> None:
    temporal = manifest["temporal_coverage_report"]
    assert manifest["plot_report"]["temporal_interpolation"] == "not_performed"
    assert manifest["plot_report"]["numeric_conversion"] == "float_for_display_only"
    assert temporal["schema_version"] == "archive-govt-nz.health-temporal-coverage/v1"
    assert temporal["gap_inference"] == "not_performed"
    assert temporal["cross_source_join"] == "not_performed"
    assert temporal["vintage_pooling"] == "not_performed"
    assert {item["output_name"] for item in temporal["groups"]} == {
        "historical_observations.parquet",
        "nominal_budget.parquet",
        "nominal_revenue.parquet",
    }


def _assert_dataset_card(output: Path, manifest: dict[str, Any]) -> None:
    card = (output / "dataset-card.md").read_text(encoding="utf-8")
    assert card.startswith("# Health Appropriations canonical Gold dataset card")
    assert (
        "| Product | Input records | Output rows | Exact-context temporal groups |"
        in card
    )
    for product, details in manifest["products"].items():
        assert f"| {product} |" in card
        assert str(details["input_records"]) in card
    for marker in manifest["package_marker_sha256"]:
        assert f"`{marker}`" in card
    for boundary in (
        "Analytical completeness: not evaluated.",
        "Source health: unresolved.",
        "Budget/revenue label-change candidates: observed only;",
        "Other classification drift: unresolved.",
        "Revision reconciliation: unresolved.",
        "Cross-source reconciliation: not performed.",
        "Rights: not evaluated.",
        "Publication: not performed.",
    ):
        assert boundary in card
    assert "license" not in card.lower()
    card_metadata = manifest["outputs"]["dataset-card.md"]
    assert card_metadata["kind"] == "dataset_card"
    assert card_metadata["rights_state"] == "not_evaluated"
    assert card_metadata["publication"] == "not_performed"


def _assert_canonical_gold_outputs(
    output: Path,
    repeated: Path,
    manifest: dict[str, Any],
    quality: dict[str, Any],
    packages: tuple[CanonicalPackageInput, ...],
) -> None:
    plot_paths = list(output.glob("plot_*.png"))
    assert any(path.name.startswith("plot_historical_") for path in plot_paths)
    assert any(path.name.startswith("plot_budget_") for path in plot_paths)
    assert any(path.name.startswith("plot_revenue_") for path in plot_paths)
    assert {
        "historical_observations.parquet",
        "historical_coverage.parquet",
        "nominal_budget.parquet",
        "nominal_revenue.parquet",
    }.issubset(set(manifest["outputs"]))
    drillthrough = manifest["source_drillthrough"]
    assert drillthrough["schema_version"] == (
        "archive-govt-nz.health-source-drillthrough/v2"
    )
    assert drillthrough["scope"] == "exact_row_and_source_coordinate_lookup_only"
    output_by_record = {
        row["input_record_id"]: row["output_rows"] for row in drillthrough["records"]
    }
    assert set(output_by_record) == set(quality["input_record_products"])
    expected_coordinates: dict[str, list[dict[str, Any]]] = {}
    for package in packages:
        canonical, _receipt = read_verified_canonical_tables(package)
        for lineage in canonical["field_lineage"].to_pylist():
            locator = lineage["source_locator"]
            expected_coordinates.setdefault(lineage["target_record_id"], []).append(
                {
                    "field": lineage["field"],
                    "source_coordinate": lineage["source_coordinate"],
                    "source_object_sha256": lineage["source_object_sha256"],
                    "source_locator_sha256": hashlib.sha256(
                        locator.encode("utf-8")
                    ).hexdigest(),
                    "source_vintage": lineage["source_vintage"],
                    "rights_state": lineage["rights_state"],
                }
            )
    for input_record_id, output_rows in output_by_record.items():
        assert output_rows
        record = next(
            item
            for item in drillthrough["records"]
            if item["input_record_id"] == input_record_id
        )
        assert record["source_coordinates"] == sorted(
            expected_coordinates[input_record_id],
            key=lambda item: (
                item["source_vintage"],
                item["source_object_sha256"],
                item["source_coordinate"],
                item["field"],
            ),
        )
        assert all(
            item["source_coordinate"]
            and item["field"]
            and item["source_object_sha256"]
            and item["source_locator_sha256"]
            and item["rights_state"] == "not_evaluated"
            for item in record["source_coordinates"]
        )
        for output_row in output_rows:
            metadata = manifest["outputs"][output_row["output_name"]]
            assert metadata["sha256"] == output_row["output_sha256"]
            rows = pq.read_table(output / output_row["output_name"]).to_pylist()
            row = rows[output_row["row_index"]]
            assert input_record_id in row.get(
                "input_record_ids", [row.get("input_record_id")]
            )
    assert {
        item["product"]: item["status"] for item in manifest["plot_report"]["series"]
    } == {
        "historical": "rendered",
        "budget": "rendered",
        "revenue": "rendered",
        "pharmac": "not_present",
        "moh": "not_present",
        "crown_befu": "not_present",
        "crown_hyefu": "not_present",
        "fiscal_crown": "not_present",
    }
    assert all(
        manifest["outputs"][name]["kind"] == "plot_png"
        and manifest["outputs"][name]["display_only"] is True
        for name in manifest["outputs"]
        if name.endswith(".png")
    )
    assert pq.read_table(output / "nominal_budget.parquet").to_pylist() == (
        query_nominal_budget((packages[1],))[0].to_pylist()
    )
    assert pq.read_table(output / "nominal_revenue.parquet").to_pylist() == (
        query_nominal_revenue((packages[2],))[0].to_pylist()
    )
    export_canonical_gold(packages, repeated, write=True)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        path.name: path.read_bytes() for path in repeated.iterdir()
    }


def test_exact_nominal_query_retains_source_labels_and_lineage(tmp_path: Path) -> None:
    package = _package(tmp_path)
    before = {
        path: path.read_bytes()
        for path in (
            package.original,
            *package.root.iterdir(),
            *package.raw_root.iterdir(),
        )
    }
    table, receipt = query_nominal_budget((package,))
    assert table.schema.equals(NOMINAL_BUDGET_SCHEMA, check_metadata=True)
    assert table.num_rows == 1
    row = table.to_pylist()[0]
    assert row["total_amount"] == Decimal("246.000000000000000000")
    assert row["input_count"] == 2
    assert row["source_label"] == "Care"
    assert row["vote"] == row["department"] == row["portfolio"] == "Health"
    assert row["unit"] == "NZD_thousands"
    assert len(row["input_record_ids"]) == 2
    assert receipt == query_nominal_budget((package,))[1]
    assert receipt["currency_state"] == "unknown"
    assert receipt["price_basis_state"] == "unknown"
    assert receipt["classification_mapping"] == "not_performed"
    assert before == {path: path.read_bytes() for path in before}


def test_wrong_kind_and_repeated_identity_fail_closed(tmp_path: Path) -> None:
    package = _package(tmp_path)
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget((package, package))
    wrong = CanonicalPackageInput(
        kind="classification",
        root=package.root,
        marker_sha256=package.marker_sha256,
        original=package.original,
        raw_root=package.raw_root,
        raw_manifest_sha256=package.raw_manifest_sha256,
    )
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget((wrong,))


def test_alternative_packages_for_one_vintage_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _package(tmp_path)
    canonical, receipt = canonical_consumer.read_verified_canonical_tables(package)
    table = canonical["appropriation_fact"]
    ids = [f"alternative-{index}" for index in range(table.num_rows)]
    alternative = table.set_column(
        table.schema.get_field_index("record_id"), "record_id", pa.array(ids)
    )
    responses = iter(
        ((canonical, receipt), ({"appropriation_fact": alternative}, receipt))
    )
    monkeypatch.setattr(
        canonical_consumer,
        "read_verified_canonical_tables",
        lambda _package: next(responses),
    )

    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget((package, package))


def test_historical_query_is_an_identity_projection(tmp_path: Path) -> None:
    package = _historical_package(tmp_path)
    table, receipt = query_historical_nominal((package,))
    assert table.schema.equals(HISTORICAL_NOMINAL_SCHEMA, check_metadata=True)
    assert table.num_rows == receipt["input_records"]
    assert receipt["aggregation"] == "none"
    assert receipt["currency_state"] == "source_assertion_preserved"
    assert receipt["price_basis_state"] == "unknown"
    assert all(
        row["formula_policy"] == "identity_projection_no_cross_source_aggregation/v1"
        for row in table.to_pylist()
    )


def test_historical_query_rejects_budget_package(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_historical_nominal((_package(tmp_path),))


def test_longitudinal_mart_preserves_health_and_fiscal_context_identity(
    tmp_path: Path,
) -> None:
    package = _historical_package(tmp_path)
    observations, receipt = query_historical_observations((package,))
    coverage = summarize_historical_coverage(observations)

    assert observations.schema.equals(
        HISTORICAL_OBSERVATION_SCHEMA, check_metadata=True
    )
    assert coverage.schema.equals(HISTORICAL_COVERAGE_SCHEMA, check_metadata=True)
    assert observations.num_rows == receipt["input_records"]
    assert coverage.num_rows == receipt["coverage_rows"]
    assert all(row["period_tokens"] for row in coverage.to_pylist())
    assert {row["recordset"] for row in observations.to_pylist()} == {
        "health_spending_fact",
        "fiscal_context_fact",
    }
    assert {
        item for group in coverage["input_record_ids"].to_pylist() for item in group
    } == set(observations["input_record_id"].to_pylist())
    assert all(
        row["formula_policy"] == "identity_projection_no_cross_source_aggregation/v1"
        for row in observations.to_pylist()
    )
    assert all(
        row["formula_policy"] == "exact_context_coverage_no_cross_source_join/v1"
        for row in coverage.to_pylist()
    )
    assert receipt["cross_source_join"] == "not_performed"
    assert receipt["vintage_pooling"] == "not_performed"


def test_coverage_rejects_duplicate_identity_and_unverified_shape(
    tmp_path: Path,
) -> None:
    observations, _receipt = query_historical_observations(
        (_historical_package(tmp_path),)
    )
    duplicate = pa.concat_tables([observations, observations.slice(0, 1)])
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        summarize_historical_coverage(duplicate)
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        summarize_historical_coverage(pa.table({"input_record_id": ["x"]}))


def test_longitudinal_query_redacts_verifier_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _historical_package(tmp_path)

    def fail_verification(_package: CanonicalPackageInput) -> object:
        failure_message = "sensitive source path"
        raise ValueError(failure_message)

    monkeypatch.setattr(
        canonical_consumer, "read_verified_canonical_tables", fail_verification
    )
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_historical_observations((package,))


def test_historical_gold_export_is_dry_run_first_and_repeatable(
    tmp_path: Path,
) -> None:
    package = _historical_package(tmp_path)
    source_paths = (
        package.original,
        *package.root.iterdir(),
        *package.raw_root.iterdir(),
    )
    before = {path: path.read_bytes() for path in source_paths}
    planned = export_historical_gold((package,), tmp_path / "planned")
    assert planned["status"] == "dry_run"
    assert not (tmp_path / "planned").exists()

    first = tmp_path / "gold-one"
    second = tmp_path / "gold-two"
    receipt_one = export_historical_gold((package,), first, write=True)
    receipt_two = export_historical_gold((package,), second, write=True)
    assert receipt_one == receipt_two
    assert receipt_one["cross_source_join"] == "not_performed"
    assert receipt_one["rights_state"] == "not_evaluated"
    assert {
        "MANIFEST.json",
        "historical_observations.parquet",
        "historical_coverage.parquet",
    }.issubset({path.name for path in first.iterdir()})
    assert any(path.name.startswith("plot_historical_") for path in first.iterdir())
    assert {
        name: (first / name).read_bytes()
        for name in (path.name for path in first.iterdir())
    } == {
        name: (second / name).read_bytes()
        for name in (path.name for path in second.iterdir())
    }
    assert before == {path: path.read_bytes() for path in before}


def test_historical_gold_export_rejects_input_overlap_and_existing_output(
    tmp_path: Path,
) -> None:
    package = _historical_package(tmp_path)
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_historical_gold((package,), package.root / "gold")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_historical_gold((package,), existing)
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_historical_gold((object(),), tmp_path / "bad-package")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_historical_gold((), tmp_path / "empty-packages")


def test_historical_gold_export_records_bounded_readback_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _historical_package(tmp_path)

    def fail_readback(
        _path: Path, _payload: bytes, _table: pa.Table | None = None
    ) -> None:
        failure_message = "sensitive output path"
        raise ValueError(failure_message)

    monkeypatch.setattr(canonical_gold_export, "_readback", fail_readback)
    output = tmp_path / "failed-gold"
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_historical_gold((package,), output, write=True)
    failure = json.loads((output / "FAILURE.json").read_text(encoding="utf-8"))
    assert failure == {
        "schema_version": "archive-govt-nz.health-canonical-gold/v2",
        "status": "incomplete",
        "error_type": "ValueError",
        "publication": "not_performed",
    }
    assert not (output / "MANIFEST.json").exists()


def _assert_ro_crate(output: Path, manifest: dict[str, Any]) -> None:
    crate = json.loads((output / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    assert crate["@context"] == "https://w3id.org/ro/crate/1.1/context"
    assert crate["@graph"][0] == {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        "about": {"@id": "./"},
    }
    nodes = {node["@id"]: node for node in crate["@graph"]}
    root = nodes["./"]
    assert root["@type"] == "Dataset"
    assert {item["@id"] for item in root["hasPart"]} == {
        name for name in manifest["outputs"] if name != "ro-crate-metadata.json"
    }
    document = json.dumps(crate)
    assert all(
        f'"{field}"' not in document
        for field in ("license", "publisher", "datePublished", "accessURL")
    )
    for part in root["hasPart"]:
        node = nodes[part["@id"]]
        payload = (output / part["@id"]).read_bytes()
        assert node["@type"] == "File"
        assert node["contentSize"] == len(payload)
        assert node["sha256"] == hashlib.sha256(payload).hexdigest()
        assert manifest["outputs"][part["@id"]]["sha256"] == node["sha256"]
    assert manifest["outputs"]["ro-crate-metadata.json"]["kind"] == (
        "ro_crate_metadata"
    )
    manifest_pin = hashlib.sha256((output / "MANIFEST.json").read_bytes()).hexdigest()
    verification = verify_canonical_gold_package(output, manifest_pin)
    assert verification["status"] == "verified"
    assert verification["output_count"] == len(manifest["outputs"])


def test_canonical_gold_builds_source_separated_facts_and_report(
    tmp_path: Path,
) -> None:
    historical = _historical_package(tmp_path / "historical")
    budget = _package(tmp_path / "budget")
    revenue = _revenue_package(tmp_path / "revenue")
    output = tmp_path / "combined-gold"
    repeated = tmp_path / "combined-gold-repeat"

    planned = export_canonical_gold((historical, budget, revenue), output)
    assert planned["status"] == "dry_run"
    assert set(planned["products"]) == {"historical", "budget", "revenue"}
    assert not output.exists()

    receipt = export_canonical_gold((historical, budget, revenue), output, write=True)
    assert receipt["status"] == "complete"
    assert receipt["cross_source_join"] == "not_performed"
    assert receipt["vintage_pooling"] == "not_performed"
    assert (
        receipt["products"]["budget"]["aggregation"]
        == "sum_within_exact_source_labels_and_unit"
    )
    assert receipt["products"]["revenue"]["netting"] == "prohibited"
    quality = receipt["quality_report"]
    assert quality["schema_version"] == (
        "archive-govt-nz.health-canonical-gold-quality/v1"
    )
    assert quality["unaccounted_input_records"] == 0
    assert quality["input_records_with_product"] == quality["input_record_count"]
    assert quality["unresolved_reports"] == [
        "source_health",
        "revision_reconciliation",
        "cross_source_reconciliation",
    ]
    assert receipt["classification_drift_report"]["schema_version"] == (
        "archive-govt-nz.health-classification-drift/v1"
    )
    assert receipt["classification_drift_report"]["mapping"] == "not_inferred"
    assert quality["input_record_products"]
    assert {
        "historical_observations.parquet",
        "historical_coverage.parquet",
        "nominal_budget.parquet",
        "nominal_revenue.parquet",
        "MANIFEST.json",
    }.issubset({path.name for path in output.iterdir()})
    manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
    _assert_ro_crate(output, manifest)
    _assert_dataset_card(output, manifest)
    _assert_temporal_report(manifest)
    _assert_canonical_gold_outputs(
        output, repeated, manifest, quality, (historical, budget, revenue)
    )
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_canonical_gold((object(),), tmp_path / "invalid")  # type: ignore[arg-type]


def test_canonical_gold_includes_pharmac_as_a_separate_source_product(
    tmp_path: Path,
) -> None:
    historical = _historical_package(tmp_path / "historical")
    budget = _package(tmp_path / "budget")
    revenue = _revenue_package(tmp_path / "revenue")
    pharmac_root = tmp_path / "pharmac"
    pharmac_root.mkdir()
    silver, cas, pin, source_sha256 = pharmac_silver_package(pharmac_root)
    pharmac_input = PharmacGoldInput(silver, pin, cas, source_sha256)
    output = tmp_path / "gold-with-pharmac"
    repeated = tmp_path / "gold-with-pharmac-repeat"

    receipt = export_canonical_gold(
        (historical, budget, revenue),
        output,
        inputs=GoldInputs(pharmac=pharmac_input),
    )
    assert receipt["status"] == "dry_run"
    assert receipt["products"]["pharmac"]["aggregation"] == (
        "none_source_record_rows_preserved"
    )
    assert receipt["products"]["pharmac"]["actual_expenditure"] == "not_asserted"
    assert receipt["cross_source_join"] == "not_performed"
    assert receipt["vintage_pooling"] == "not_performed"
    assert not output.exists()

    export_canonical_gold(
        (historical, budget, revenue),
        output,
        write=True,
        inputs=GoldInputs(pharmac=pharmac_input),
    )
    export_canonical_gold(
        (historical, budget, revenue),
        repeated,
        write=True,
        inputs=GoldInputs(pharmac=pharmac_input),
    )
    manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
    pharmac_rows = pq.read_table(
        output / "nominal_pharmaceutical_budget.parquet"
    ).to_pylist()
    lineage_rows = pq.read_table(
        output / "pharmaceutical_budget_lineage.parquet"
    ).to_pylist()
    assert len(pharmac_rows) == 14
    assert len(lineage_rows) == 14 * 8
    assert {row["rights_state"] for row in pharmac_rows} == {"not_evaluated"}
    assert {row["amount_type"] for row in pharmac_rows} == {
        "published_budget_allocation"
    }
    assert {row["funding_regime"] for row in pharmac_rows} == {
        "district_health_board_budget_holder",
        "government_appropriation_allocated_to_pharmac",
    }
    assert manifest["pharmac_projection"]["status"] == (
        "verified_source_faithful_projection"
    )

    assert manifest["products"]["pharmac"]["funding_regimes"] == sorted(
        {row["funding_regime"] for row in pharmac_rows}
    )
    pharmac_groups = [
        row
        for row in manifest["temporal_coverage_report"]["groups"]
        if row["output_name"] == "nominal_pharmaceutical_budget.parquet"
    ]
    assert len(pharmac_groups) == 2
    assert {row["context"]["funding_regime"] for row in pharmac_groups} == {
        "district_health_board_budget_holder",
        "government_appropriation_allocated_to_pharmac",
    }
    pharmac_plots = [
        item
        for item in manifest["plot_report"]["series"]
        if item["product"] == "pharmac"
    ]
    assert pharmac_plots[0]["status"] == "rendered"
    assert len(pharmac_plots[0]["plots"]) == 2
    drillthrough = {
        row["input_record_id"]: row
        for row in manifest["source_drillthrough"]["records"]
    }
    assert {row["record_id"] for row in pharmac_rows}.issubset(drillthrough)
    for row in pharmac_rows:
        record = drillthrough[row["record_id"]]
        assert len(record["source_coordinates"]) == 8
        assert any(
            item["output_name"] == "nominal_pharmaceutical_budget.parquet"
            for item in record["output_rows"]
        )
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        path.name: path.read_bytes() for path in repeated.iterdir()
    }


def test_canonical_gold_preserves_pinned_moh_indicator_profiles(tmp_path: Path) -> None:
    historical = _historical_package(tmp_path / "historical")
    budget = _package(tmp_path / "budget")
    revenue = _revenue_package(tmp_path / "revenue")
    cas_root = tmp_path / "moh-cas"
    packages = []
    for profile in ("fig27/v1", "fig28/v1"):
        source_dir = tmp_path / profile.replace("/", "-")
        source_dir.mkdir()
        source_path, source_sha256 = moh_source(source_dir, profile)
        cas_object = cas_root / source_sha256[:2] / source_sha256
        cas_object.parent.mkdir(parents=True, exist_ok=True)
        cas_object.write_bytes(source_path.read_bytes())
        silver = tmp_path / "silver" / profile.replace("/", "-")
        normalize_moh_indicators(
            cas_object,
            silver,
            expected_sha256=source_sha256,
            profile=profile,
            source_vintage="MoH-HAIR-2024",
            observed_at="2026-08-29T09:00:17Z",
            source_locator=MOH_PROFILES[profile],
            dry_run=False,
        )
        manifest_sha256 = hashlib.sha256(
            (silver / "MANIFEST.json").read_bytes()
        ).hexdigest()
        packages.append(
            MohIndicatorInput(profile, silver, manifest_sha256, source_sha256)
        )
    moh_input = MohGoldInput(tuple(packages), cas_root)
    inputs = (historical, budget, revenue)
    output = tmp_path / "gold-with-moh"
    repeated = tmp_path / "gold-with-moh-repeat"

    planned = export_canonical_gold(inputs, output, inputs=GoldInputs(moh=moh_input))
    assert planned["status"] == "dry_run"
    assert planned["products"]["moh"]["output_rows"] == 80
    assert not output.exists()

    export_canonical_gold(inputs, output, write=True, inputs=GoldInputs(moh=moh_input))
    export_canonical_gold(
        inputs, repeated, write=True, inputs=GoldInputs(moh=moh_input)
    )
    manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
    facts = pq.read_table(output / "published_health_indicators.parquet").to_pylist()
    lineage = pq.read_table(
        output / "published_health_indicator_lineage.parquet"
    ).to_pylist()
    assert len(facts) == 80
    assert len(lineage) == 240
    assert {row["profile"] for row in facts} == {"fig27/v1", "fig28/v1"}
    assert {row["unit"] for row in facts} == {None}
    assert {row["price_base"] for row in facts} == {None}
    assert {row["denominator"] for row in facts} == {None}
    assert {row["rights_state"] for row in facts} == {"not_evaluated"}
    assert manifest["products"]["moh"]["actual_expenditure"] == "not_asserted"
    assert manifest["moh_projection"]["cross_source_join"] == "not_performed"
    assert (
        len(
            [
                group
                for group in manifest["temporal_coverage_report"]["groups"]
                if group["output_name"] == "published_health_indicators.parquet"
            ]
        )
        == 4
    )
    assert any(path.name.startswith("plot_moh_") for path in output.glob("plot_*.png"))
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        path.name: path.read_bytes() for path in repeated.iterdir()
    }


def test_canonical_gold_preserves_befu_and_hyefu_as_separate_vintages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical = _historical_package(tmp_path / "historical")
    budget = _package(tmp_path / "budget")
    revenue = _revenue_package(tmp_path / "revenue")
    schema = recordset_schema("fiscal_context_fact")
    lineage_schema = recordset_schema("field_lineage")
    pins = ("a" * 64, "b" * 64)

    def projection(
        vintage: str, marker: str
    ) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
        facts = []
        lineage = []
        for index in range(10):
            record_id = f"{vintage}-{index}"
            facts.append(
                {
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.health-recordsets/v1",
                    "recordset": "fiscal_context_fact",
                    "domain": "health_appropriations",
                    "source_object_sha256": marker,
                    "source_observation_id": record_id,
                    "source_locator": "workbook.xlsx#sheet=Core",
                    "source_vintage": vintage,
                    "valid_time_start": None,
                    "valid_time_end": None,
                    "valid_time_status": "financial_year_boundaries_unqualified",
                    "period_token": f"year_label:{2015 + index}",
                    "observed_at": datetime(2026, 8, 29, 9, 0, 17, tzinfo=UTC),
                    "observation_context": f"treasury_{vintage.lower()}_core_crown_expense_formula_cache",
                    "rights_state": "not_evaluated",
                    "quality_flags": [
                        "canonical_projection_preserves_source_uncertainty"
                    ],
                    "transformation_id": f"{vintage}/v1",
                    "lineage_id": f"lineage-{record_id}",
                    "source_record_id": record_id,
                    "source_schema_version": "archive-govt-nz.health-recordsets/v1",
                    "measure": "core_crown_expense",
                    "amount": Decimal(index + 100),
                    "value_token": str(index + 100),
                    "null_reason": None,
                    "source_decimal_precision": 3,
                    "source_decimal_scale": 0,
                    "unit": "unknown_source_unit",
                    "currency": None,
                    "price_basis": None,
                    "base_period": None,
                    "denominator_definition": None,
                    "amount_type": "forecast",
                    "source_label": "Core Crown expense",
                    "institutional_coverage": "core_crown",
                    "accounting_basis": None,
                    "seasonal_adjustment": None,
                }
            )
            lineage.extend(
                {
                    "record_id": f"lineage-{record_id}-{field_index}",
                    "schema_version": "archive-govt-nz.health-recordsets/v1",
                    "recordset": "field_lineage",
                    "domain": "health_appropriations",
                    "source_object_sha256": marker,
                    "source_observation_id": record_id,
                    "source_locator": "workbook.xlsx#sheet=Core",
                    "source_vintage": vintage,
                    "valid_time_start": None,
                    "valid_time_end": None,
                    "valid_time_status": "financial_year_boundaries_unqualified",
                    "period_token": f"year_label:{2015 + index}",
                    "observed_at": datetime(2026, 8, 29, 9, 0, 17, tzinfo=UTC),
                    "observation_context": "source_coordinate_lineage",
                    "rights_state": "not_evaluated",
                    "quality_flags": [],
                    "transformation_id": f"{vintage}/v1",
                    "lineage_id": f"lineage-{record_id}-{field_index}",
                    "source_record_id": record_id,
                    "source_schema_version": "archive-govt-nz.health-recordsets/v1",
                    "target_record_id": record_id,
                    "field": f"field-{field_index}",
                    "source_coordinate": f"Core!A{index + field_index + 1}",
                    "raw_value": str(index),
                    "normalized_value": str(index),
                    "rule": f"{vintage}/v1",
                }
                for field_index in range(8)
            )
        return (
            pa.Table.from_pylist(facts, schema=schema),
            pa.Table.from_pylist(lineage, schema=lineage_schema),
            {"input_records": 10, "vintage": vintage},
        )

    def befu(
        _root: Path, marker: str, _cas: Path
    ) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
        return projection("BEFU-2026", marker)

    def hyefu(
        _root: Path, marker: str, _cas: Path
    ) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
        return projection("HYEFU-2025", marker)

    monkeypatch.setattr(
        canonical_gold_export.crown_expense_canonical_projection,
        "project_befu_core_expense",
        befu,
    )
    monkeypatch.setattr(
        canonical_gold_export.hyefu_crown_expense_canonical_projection,
        "project_hyefu_core_expense",
        hyefu,
    )
    crown = canonical_gold_export.CrownGoldInput(
        befu_root=tmp_path / "befu-silver",
        befu_manifest_sha256=pins[0],
        hyefu_root=tmp_path / "hyefu-silver",
        hyefu_manifest_sha256=pins[1],
        source_cas_root=tmp_path / "bronze-cas",
    )
    inputs = (historical, budget, revenue)
    output = tmp_path / "gold-with-crown"
    repeated = tmp_path / "gold-with-crown-repeat"

    planned = export_canonical_gold(inputs, output, inputs=GoldInputs(crown=crown))
    assert planned["status"] == "dry_run"
    assert planned["products"]["crown_befu"]["output_rows"] == 10
    assert planned["products"]["crown_hyefu"]["output_rows"] == 10
    assert not output.exists()

    export_canonical_gold(inputs, output, write=True, inputs=GoldInputs(crown=crown))
    export_canonical_gold(inputs, repeated, write=True, inputs=GoldInputs(crown=crown))
    manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
    befu_facts = pq.read_table(output / "crown_expense_befu_2026.parquet").to_pylist()
    hyefu_facts = pq.read_table(output / "crown_expense_hyefu_2025.parquet").to_pylist()
    assert {row["source_vintage"] for row in befu_facts} == {"BEFU-2026"}
    assert {row["source_vintage"] for row in hyefu_facts} == {"HYEFU-2025"}
    assert not {row["record_id"] for row in befu_facts} & {
        row["record_id"] for row in hyefu_facts
    }
    assert manifest["crown_projection"]["cross_source_join"] == "not_performed"
    assert manifest["products"]["crown_befu"]["currency_and_accounting_basis"] == (
        "unknown_not_inferred"
    )
    assert manifest["products"]["crown_hyefu"]["cross_vintage_comparison"] == (
        "not_performed"
    )
    assert {
        "crown_expense_befu_2026.parquet",
        "crown_expense_hyefu_2025.parquet",
    } <= set(manifest["outputs"])
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        path.name: path.read_bytes() for path in repeated.iterdir()
    }


def test_canonical_gold_preserves_historical_fiscal_crown_measure_families(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical = _historical_package(tmp_path / "historical")
    budget = _package(tmp_path / "budget")
    revenue = _revenue_package(tmp_path / "revenue")
    fact_schema = recordset_schema("fiscal_context_fact")
    lineage_schema = recordset_schema("field_lineage")
    source_sha256 = "c" * 64
    vintage = "Fiscal-Time-Series-1972-2025"
    observed_at = datetime(2026, 8, 29, 9, 0, 17, tzinfo=UTC)

    def project(_source: Path) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
        facts = []
        lineage = []
        for index in range(61):
            family = "core_crown" if index < 32 else "total_crown"
            measure = f"{family}_expenses"
            source_id = f"fiscal-source-{index}"
            record_id = f"fiscal-canonical-{index}"
            period_end = date(1994 + index, 6, 30)
            facts.append(
                {
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.health-recordsets/v1",
                    "recordset": "fiscal_context_fact",
                    "domain": "health_appropriations",
                    "source_object_sha256": source_sha256,
                    "source_observation_id": source_id,
                    "source_locator": "fiscal.xlsx#Spending!A1",
                    "source_vintage": vintage,
                    "valid_time_start": None,
                    "valid_time_end": period_end,
                    "valid_time_status": "june_year_end_start_unqualified",
                    "period_token": f"year_label:{1994 + index}",
                    "observed_at": observed_at,
                    "observation_context": "treasury_fiscal_time_series_crown_as_published",
                    "rights_state": "not_evaluated",
                    "quality_flags": ["consolidation_equivalence_not_asserted"],
                    "transformation_id": "fiscal-crown-canonical/v1",
                    "lineage_id": f"fact-lineage-{index}",
                    "source_record_id": source_id,
                    "source_schema_version": "archive-govt-nz.fiscal-crown-literal-admission/v1",
                    "measure": measure,
                    "amount": Decimal(index + 100),
                    "value_token": str(index + 100),
                    "null_reason": None,
                    "source_decimal_precision": 3,
                    "source_decimal_scale": 0,
                    "unit": "$ millions",
                    "currency": None,
                    "price_basis": None,
                    "base_period": None,
                    "denominator_definition": None,
                    "amount_type": "historical_as_published",
                    "source_label": measure,
                    "institutional_coverage": family,
                    "accounting_basis": "PBE Standards",
                    "seasonal_adjustment": None,
                }
            )
            lineage.extend(
                {
                    "record_id": f"fiscal-lineage-{index}-{field_index}",
                    "schema_version": "archive-govt-nz.health-recordsets/v1",
                    "recordset": "field_lineage",
                    "domain": "health_appropriations",
                    "source_object_sha256": source_sha256,
                    "source_observation_id": source_id,
                    "source_locator": "fiscal.xlsx#Spending!A1",
                    "source_vintage": vintage,
                    "valid_time_start": None,
                    "valid_time_end": period_end,
                    "valid_time_status": "june_year_end_start_unqualified",
                    "period_token": f"year_label:{1994 + index}",
                    "observed_at": observed_at,
                    "observation_context": "treasury_fiscal_time_series_crown_as_published",
                    "rights_state": "not_evaluated",
                    "quality_flags": [],
                    "transformation_id": "fiscal-crown-canonical/v1",
                    "lineage_id": f"fact-lineage-{index}",
                    "source_record_id": source_id,
                    "source_schema_version": "archive-govt-nz.fiscal-crown-literal-admission/v1",
                    "target_record_id": record_id,
                    "field": f"field-{field_index}",
                    "source_coordinate": f"Spending!A{index * 11 + field_index + 1}",
                    "raw_value": str(index),
                    "normalized_value": str(index),
                    "rule": "fiscal-crown-canonical/v1",
                }
                for field_index in range(11)
            )
        return (
            pa.Table.from_pylist(facts, schema=fact_schema),
            pa.Table.from_pylist(lineage, schema=lineage_schema),
            {
                "source_object_sha256": source_sha256,
                "source_vintage": vintage,
                "input_records": 61,
                "core_crown_records": 32,
                "total_crown_records": 29,
                "currency": "unknown",
                "accounting_basis": "source_label_retained",
                "financial_year_start": "unqualified",
                "rights_state": "not_evaluated",
                "cross_measure_comparison": "not_performed",
            },
        )

    monkeypatch.setattr(
        canonical_gold_export.fiscal_crown_canonical_projection,
        "project_fiscal_crown",
        project,
    )
    fiscal = canonical_gold_export.FiscalCrownGoldInput(
        source_path=tmp_path / "pinned-fiscal-bronze.xlsx"
    )
    packages = (historical, budget, revenue)
    output = tmp_path / "gold-with-fiscal-crown"
    repeated = tmp_path / "gold-with-fiscal-crown-repeat"

    planned = export_canonical_gold(
        packages, output, inputs=GoldInputs(fiscal_crown=fiscal)
    )
    assert planned["products"]["fiscal_crown"]["output_rows"] == 61
    assert planned["products"]["fiscal_crown"]["lineage_rows"] == 671
    assert not output.exists()

    export_canonical_gold(
        packages, output, write=True, inputs=GoldInputs(fiscal_crown=fiscal)
    )
    export_canonical_gold(
        packages, repeated, write=True, inputs=GoldInputs(fiscal_crown=fiscal)
    )
    manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
    facts = pq.read_table(output / "historical_fiscal_crown.parquet").to_pylist()
    lineage = pq.read_table(
        output / "historical_fiscal_crown_lineage.parquet"
    ).to_pylist()
    assert len(facts) == 61
    assert len(lineage) == 671
    assert {row["institutional_coverage"] for row in facts} == {
        "core_crown",
        "total_crown",
    }
    assert {row["measure"] for row in facts} == {
        "core_crown_expenses",
        "total_crown_expenses",
    }
    assert {row["currency"] for row in facts} == {None}
    assert manifest["products"]["fiscal_crown"]["cross_measure_comparison"] == (
        "not_performed"
    )
    assert manifest["products"]["fiscal_crown"]["rights_state"] == "not_evaluated"
    assert any(
        path.name.startswith("plot_fiscal_crown_") for path in output.glob("plot_*.png")
    )
    row_index = {
        row["input_record_id"]: row
        for row in manifest["source_drillthrough"]["records"]
    }
    assert all(
        len(row_index[f"fiscal-canonical-{index}"]["source_coordinates"]) == 11
        for index in range(61)
    )
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        path.name: path.read_bytes() for path in repeated.iterdir()
    }


def test_temporal_coverage_keeps_historical_source_series_distinct(
    tmp_path: Path,
) -> None:
    observations, _receipt = query_historical_observations(
        (_historical_package(tmp_path),)
    )
    original = observations.to_pylist()[0]
    alternate = {
        **original,
        "source_label": "A distinct historical source series",
        "source_locator": "sheet=Alternate!A1",
    }
    table = pa.Table.from_pylist([original, alternate], schema=observations.schema)

    report = canonical_gold_export.build_temporal_coverage_report(
        {"observations": table}
    )
    groups = report["groups"]

    assert len(groups) == 2
    assert {
        (group["context"]["source_label"], group["context"]["source_locator"])
        for group in groups
    } == {
        (original["source_label"], original["source_locator"]),
        (alternate["source_label"], alternate["source_locator"]),
    }


def test_classification_drift_report_flags_only_same_exact_budget_dimensions(
    tmp_path: Path,
) -> None:
    budget, _receipt = query_nominal_budget((_package(tmp_path),))
    rows = budget.to_pylist()
    first = rows[0]
    changed_label = {
        **first,
        "source_vintage": "Budget 2027",
        "source_label": "Changed source wording",
    }
    separate_vote = {
        **changed_label,
        "vote": "A separate Vote",
    }
    table = pa.Table.from_pylist(
        [first, changed_label, separate_vote], schema=budget.schema
    )

    report = canonical_gold_export.build_classification_drift_report({"budget": table})

    assert report["scope"] == (
        "same_source_family_and_exact_dimensions_across_observed_vintages"
    )
    assert report["mapping"] == "not_inferred"
    assert report["cross_source_comparison"] == "not_performed"
    assert len(report["candidates"]) == 1
    candidate = report["candidates"][0]
    assert candidate["key"]["vote"] == first["vote"]
    assert candidate["observed_labels"] == sorted(
        [first["source_label"], changed_label["source_label"]]
    )
    assert candidate["status"] == "source_label_change_candidate"


@pytest.mark.parametrize("packages", [[], (), [object()]])
def test_exact_tuple_boundary(packages: object) -> None:
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget(packages)  # type: ignore[arg-type]
