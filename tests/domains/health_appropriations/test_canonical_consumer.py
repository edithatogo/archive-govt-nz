"""Verified canonical packages are the direct analytical input boundary."""

from __future__ import annotations

import hashlib
import json
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
    export_canonical_gold,
    export_historical_gold,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    export_historical_canonical,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)


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
    for group in temporal["groups"]:
        periods = group["observed_periods"]
        assert periods == sorted(periods, key=lambda item: item["period_token"])
        assert all(item["observation_count"] > 0 for item in periods)
        assert group["context"]["source_vintage"]


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
    assert receipt["products"]["historical"]["cross_source_join"] == "not_performed"
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
        "classification_drift",
        "revision_reconciliation",
        "cross_source_reconciliation",
    ]
    assert quality["products"]["historical"]["analytical_completeness"] == (
        "not_evaluated"
    )
    assert quality["input_record_products"]
    assert {
        "historical_observations.parquet",
        "historical_coverage.parquet",
        "nominal_budget.parquet",
        "nominal_revenue.parquet",
        "MANIFEST.json",
    }.issubset({path.name for path in output.iterdir()})
    plot_paths = list(output.glob("plot_*.png"))
    assert any(path.name.startswith("plot_historical_") for path in plot_paths)
    assert any(path.name.startswith("plot_budget_") for path in plot_paths)
    assert any(path.name.startswith("plot_revenue_") for path in plot_paths)
    manifest = json.loads((output / "MANIFEST.json").read_text(encoding="utf-8"))
    assert {
        "historical_observations.parquet",
        "historical_coverage.parquet",
        "nominal_budget.parquet",
        "nominal_revenue.parquet",
    }.issubset(set(manifest["outputs"]))
    _assert_temporal_report(manifest)
    drillthrough = manifest["source_drillthrough"]
    assert drillthrough["schema_version"] == (
        "archive-govt-nz.health-source-drillthrough/v1"
    )
    output_by_record = {
        row["input_record_id"]: row["output_rows"] for row in drillthrough["records"]
    }
    assert set(output_by_record) == set(quality["input_record_products"])
    for input_record_id, output_rows in output_by_record.items():
        assert output_rows
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
    } == {"historical": "rendered", "budget": "rendered", "revenue": "rendered"}
    assert all(
        manifest["outputs"][name]["kind"] == "plot_png"
        and manifest["outputs"][name]["display_only"] is True
        for name in manifest["outputs"]
        if name.endswith(".png")
    )
    assert pq.read_table(output / "nominal_budget.parquet").to_pylist() == (
        query_nominal_budget((budget,))[0].to_pylist()
    )
    assert pq.read_table(output / "nominal_revenue.parquet").to_pylist() == (
        query_nominal_revenue((revenue,))[0].to_pylist()
    )
    export_canonical_gold((historical, budget, revenue), repeated, write=True)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        path.name: path.read_bytes() for path in repeated.iterdir()
    }
    with pytest.raises(ValueError, match=r"^canonical_gold_export_invalid$"):
        export_canonical_gold((object(),), tmp_path / "invalid")  # type: ignore[arg-type]


@pytest.mark.parametrize("packages", [[], (), [object()]])
def test_exact_tuple_boundary(packages: object) -> None:
    with pytest.raises(ValueError, match=r"^canonical_consumer_invalid$"):
        query_nominal_budget(packages)  # type: ignore[arg-type]
