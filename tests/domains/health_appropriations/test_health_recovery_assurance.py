"""Contract tests for clean-room recovery receipts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

SCRIPT = Path(__file__).parents[3] / "tools" / "health_recovery_assurance.py"
SPEC = importlib.util.spec_from_file_location("health_recovery_assurance", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_digest_and_tree_are_content_based(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a").write_bytes(b"bronze")
    expected = MODULE.digest(source / "a")
    assert MODULE.tree(source) == {"a": {"bytes": 6, "sha256": expected}}


def test_repeat_build_mismatch_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "MANIFEST.json").write_bytes(b"first")
    (second / "MANIFEST.json").write_bytes(b"second")
    with pytest.raises(RuntimeError, match=r"^canonical_gold_repeat_mismatch$"):
        MODULE.compare_product_outputs(first, second, "canonical_gold")


def test_gdp_vintage_recovery_is_bound_to_recorded_comparison(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "gdp-canonical-1").mkdir()
    (tmp_path / "gdp-june-canonical-1").mkdir()
    track = tmp_path / "track"
    track.mkdir()
    receipt_path = track / "gdp-vintage-reconciliation-20260930.json"
    report = {"status": "verified_source_vintage_comparison"}
    march_manifest = "march-manifest-pin"
    june_manifest = "june-manifest-pin"
    expected = {
        **report,
        "march_source_manifest_sha256": march_manifest,
        "june_source_manifest_sha256": june_manifest,
        "repeat_identical": True,
    }
    receipt_path.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.setattr(MODULE, "TRACK", track)
    monkeypatch.setattr(
        MODULE.gdp_canonical_projection,
        "SOURCE_MANIFEST_SHA256",
        march_manifest,
    )
    monkeypatch.setattr(
        MODULE.gdp_canonical_projection,
        "JUNE_SOURCE_MANIFEST_SHA256",
        june_manifest,
    )
    monkeypatch.setattr(
        MODULE.pq,
        "read_table",
        lambda _path: SimpleNamespace(to_pylist=list),
    )
    monkeypatch.setattr(
        MODULE.gdp_vintage_comparison,
        "compare_gdp_vintages",
        lambda _march, _june: report.copy(),
    )

    result = MODULE.gdp_vintage_comparison_report(tmp_path)

    assert result == {
        **report,
        "march_source_manifest_sha256": march_manifest,
        "june_source_manifest_sha256": june_manifest,
        "recorded_comparison_sha256": MODULE.digest(receipt_path),
        "recorded_repeat_identical": True,
    }

    monkeypatch.setattr(
        MODULE.gdp_vintage_comparison,
        "compare_gdp_vintages",
        lambda _march, _june: {**report, "changed_period_count": 50},
    )
    with pytest.raises(
        RuntimeError, match=r"^gdp_vintage_comparison_recorded_mismatch:"
    ):
        MODULE.gdp_vintage_comparison_report(tmp_path)


def _classification_package_fixture(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    packages: dict[int, dict[str, object]] = {}
    for year, label in ((2025, "Health"), (2026, "No Functional Classification")):
        source_sha = str(year) * 64
        manifest_sha = str(year - 2024) * 64
        package_name = f"classification-{year}"
        package = tmp_path / "silver" / package_name
        package.mkdir(parents=True)
        dimension_path = package / "classification_dimension.parquet"
        table = pa.table(
            {
                "source_vintage": [f"Budget-{year}"],
                "source_object_sha256": [source_sha],
                "source_label": [label],
                "scheme": ["budget_workbook_functional_classification_source_label"],
                "scheme_version": pa.array([None], type=pa.string()),
                "normalized_identifier": pa.array([None], type=pa.string()),
                "mapping_state": ["unmapped"],
                "valid_time_status": ["not_established"],
                "rights_state": ["not_evaluated"],
            }
        )
        pq.write_table(table, dimension_path)
        for filename, content in (
            ("field_lineage.parquet", b"lineage"),
            ("lineage_accounting.jsonl", b"{}\n"),
            ("projection_receipt.json", b"{}\n"),
        ):
            (package / filename).write_bytes(content)
        metadata = pq.read_metadata(dimension_path)
        schema_sha = MODULE.hashlib.sha256(
            metadata.schema.to_arrow_schema().serialize().to_pybytes()
        ).hexdigest()
        files = []
        for path in sorted(package.iterdir()):
            file_pin: dict[str, object] = {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": MODULE.digest(path),
            }
            if path.name.endswith(".parquet"):
                file_pin["schema_sha256"] = schema_sha
                file_pin["rows"] = 1
            files.append(file_pin)
        marker = {
            "schema_version": "archive-govt-nz.health-local-classification/v1",
            "source_vintage": f"Budget-{year}",
            "original_sha256": source_sha,
            "input_manifest_sha256": manifest_sha,
            "authoritative_mapping": "not_performed",
            "publication_approval": "not_granted",
            "rights_state": "not_evaluated",
            "files": files,
        }
        marker_path = package / "LOCAL_CLASSIFICATION.json"
        marker_path.write_text(json.dumps(marker, sort_keys=True))
        packages[year] = {
            "path": package_name,
            "marker_sha256": MODULE.digest(marker_path),
            "source_sha256": source_sha,
            "manifest_sha256": manifest_sha,
            "rows": 1,
        }
    monkeypatch.setattr(MODULE, "ARCHIVE", tmp_path)
    monkeypatch.setattr(MODULE, "CLASSIFICATION_PACKAGES", packages)


def test_classification_label_occurrence_report_verifies_retained_packages(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    _classification_package_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        MODULE,
        "bind_recorded_comparison",
        lambda report, _path, _error_code: {
            **report,
            "recorded_repeat_identical": True,
        },
    )
    report = MODULE.classification_label_occurrence_report()
    assert report["schema_version"] == (
        "archive-govt-nz.health-classification-label-occurrences/v1"
    )
    assert report["status"] == "verified_exact_literal_occurrence_counts"
    assert report["comparison_scope"] == "exact_literal_label_occurrence_counts"
    assert report["packages"]["2025"]["dimension_rows"] == 1
    assert report["packages"]["2026"]["dimension_rows"] == 1
    assert report["classification_system_identity"] == "not_established"
    assert report["authoritative_crosswalk"] == "not_performed"
    assert report["rights"] == "not_evaluated"
    assert report["comparability"] == "not_asserted"
    assert report["recorded_repeat_identical"] is True


def test_classification_label_report_rejects_changed_marker_pin(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    _classification_package_fixture(tmp_path, monkeypatch)
    marker = (
        tmp_path
        / "silver"
        / MODULE.CLASSIFICATION_PACKAGES[2025]["path"]
        / "LOCAL_CLASSIFICATION.json"
    )
    marker.write_text("{}")
    with pytest.raises(
        RuntimeError, match=r"^classification_marker_pin_mismatch:2025$"
    ):
        MODULE.classification_label_occurrence_report()


def test_context_source_binding_uses_captured_source_census() -> None:
    binding = MODULE.context_source_binding("wage")
    assert binding == {
        "source_object_sha256": (
            "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97"
        ),
        "source_locator": (
            "https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/"
            "Labour-market-statistics-June-2026-quarter/Download-data/"
            "quarterly-employment-survey-june-2026-quarter.xlsx"
        ),
        "source_vintage": "QES-2026-Q2",
        "observed_at": "2026-08-29T09:00:17Z",
    }


def test_context_source_binding_rejects_changed_census_pin(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(MODULE, "CONTEXT_CENSUS_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match=r"^context_census_pin_mismatch$"):
        MODULE.context_source_binding("wage")


def test_donor_parity_recovery_report_retains_unapproved_deviations(
    monkeypatch: MonkeyPatch,
) -> None:
    class FakeLoader:
        def exec_module(self, _module: object) -> None:
            return None

    donor = {
        "status": "exact_parity",
        "matched_rows": 312,
        "table_counts": {"five": "tables"},
    }
    raw = {
        "status": "explained_deviations",
        "matched_rows": 312,
        "unresolved_rows": 0,
        "explained_rows": 30,
        "table_counts": {"five": "tables"},
    }
    receipt = {
        "gold": donor,
        "raw": raw,
        "donor_manifest_sha256": "a" * 64,
        "raw_manifest_sha256": "b" * 64,
        "donor_objects_verified": 23,
        "donor_bytes_verified": 6604301,
        "historical_counts": {"source_only": 29, "value_difference": 1},
        "exact_decimal_deviations": [{}] * 30,
        "historical_deviation_dispositions": "accepted_retain_both_no_replacement",
        "binary_representation_flags": 15,
        "repair_approval": "not_asserted",
        "rights_state": "not_evaluated",
        "publication_state": "no_action",
    }
    fake_replay = SimpleNamespace(replay=lambda _root: receipt)
    fake_spec = SimpleNamespace(loader=FakeLoader())
    monkeypatch.setattr(
        MODULE.importlib.util,
        "spec_from_file_location",
        lambda *_args: fake_spec,
    )
    monkeypatch.setattr(
        MODULE.importlib.util, "module_from_spec", lambda _spec: fake_replay
    )

    result = MODULE.donor_parity_recovery_report()

    assert result["status"] == "verified_with_nonmutating_deviations"
    assert result["gold"]["matched_rows"] == 312
    assert result["historical_deviation_count"] == 30
    assert result["repair_approval"] == "not_asserted"
    assert result["repeat_identical"] is True


def test_source_health_recovery_report_replays_capture_and_census(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "archive"
    track = tmp_path / "track"
    manifest_name = "official-capture-2026-09-30-health-refresh.json"
    (archive / "manifests").mkdir(parents=True)
    (track).mkdir()
    source_bytes = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-census/v1",
            "cutoff": "2026-09-30",
            "record_count": 1,
            "capture_reconciliation": {
                "capture_manifest": manifest_name,
                "matched": 1,
            },
            "records": [
                {
                    "source_id": "source-1",
                    "family": "fixture",
                    "title": "Fixture source",
                    "disposition": "captured",
                    "reason": "fixture capture",
                    "object_sha256": MODULE.hashlib.sha256(b"captured").hexdigest(),
                    "license": "CC-BY-4.0",
                    "rights_uri": "https://example.test/rights",
                }
            ],
        },
        sort_keys=True,
    ).encode()
    context_bytes = json.dumps(
        {
            "schema_version": "archive-govt-nz.health-source-context-census/v1",
            "base_commit": "a" * 40,
            "series": [
                {
                    "id": "fixture-v1",
                    "family": "fixture",
                    "series_id": "fixture-series",
                    "vintage": "fixture-v1",
                    "period": "2026",
                    "qualification": "unqualified",
                    "rights": "not_evaluated",
                    "gaps": [],
                }
            ],
        },
        sort_keys=True,
    ).encode()
    object_digest = MODULE.hashlib.sha256(b"captured").hexdigest()
    manifest_bytes = json.dumps(
        {
            "cutoff": "2026-09-30",
            "results": [
                {
                    "source_id": "source-1",
                    "state": "captured",
                    "sha256": object_digest,
                    "bytes": len(b"captured"),
                    "rights": {
                        "license": "CC-BY-4.0",
                        "evidence": "https://example.test/rights",
                        "state": "eligible",
                    },
                }
            ],
        },
        sort_keys=True,
    ).encode()
    source_path = track / "source-census.json"
    context_path = track / "context-census.json"
    manifest_path = archive / "manifests" / manifest_name
    source_path.write_bytes(source_bytes)
    context_path.write_bytes(context_bytes)
    manifest_path.write_bytes(manifest_bytes)
    cas_object = archive / "bronze-cas" / "sha256" / object_digest[:2] / object_digest
    cas_object.parent.mkdir(parents=True)
    cas_object.write_bytes(b"captured")
    monkeypatch.setattr(MODULE, "TRACK", track)
    monkeypatch.setattr(MODULE, "ARCHIVE", archive)
    monkeypatch.setattr(
        MODULE,
        "SOURCE_CENSUS_SHA256",
        MODULE.hashlib.sha256(source_bytes).hexdigest(),
    )
    monkeypatch.setattr(
        MODULE,
        "CONTEXT_CENSUS_SHA256",
        MODULE.hashlib.sha256(context_bytes).hexdigest(),
    )
    monkeypatch.setattr(
        MODULE,
        "CAPTURE_MANIFEST_SHA256",
        MODULE.hashlib.sha256(manifest_bytes).hexdigest(),
    )
    generated = MODULE.build_source_health_report(
        json.loads(source_bytes),
        source_bytes,
        json.loads(context_bytes),
        context_bytes,
        MODULE.CaptureEvidence(
            manifest=json.loads(manifest_bytes),
            manifest_bytes=manifest_bytes,
            manifest_name=manifest_name,
            cas_root=archive / "bronze-cas" / "sha256",
        ),
    )
    (track / "source-health-report.json").write_text(
        json.dumps(generated, sort_keys=True, indent=2) + "\n"
    )

    result = MODULE.source_health_recovery_report()

    assert result["status"] == "verified_repeat_identical"
    assert result["report_sha256"] == MODULE.digest(
        MODULE.TRACK / "source-health-report.json"
    )
    assert result["summary"]["resource_count"] == 1
    assert result["summary"]["resource_dispositions"] == {"captured": 1}
    assert result["summary"]["context_series_vintage_count"] == 1
    assert result["capture_reconciliation"]["bronze_object_count_verified"] == 1
    assert any("not assess" in limit for limit in result["limitations"])


def test_clean_room_rebuilds_supported_products_and_reports_blockers(  # noqa: PLR0915
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "archive"
    cas = archive / "bronze-cas"
    obj_digest = "a" * 64
    obj = cas / "sha256" / obj_digest[:2] / obj_digest
    obj.parent.mkdir(parents=True)
    obj.write_bytes(b"immutable bronze")
    track = tmp_path / "track"
    track.mkdir()
    (track / "population-annual-context.json").write_text(
        '{"retrieved_at":"2026-09-25T09:37:50Z","release_date":"2026-08-18",'
        '"export_route":"https://example.test/export"}'
    )
    monkeypatch.setattr(MODULE, "ARCHIVE", archive)
    monkeypatch.setattr(MODULE, "TRACK", track)
    monkeypatch.setattr(MODULE, "CONTEXT", {})
    monkeypatch.setattr(
        MODULE,
        "gdp_june_recovery_report",
        lambda _root, **_kwargs: {
            "repeat_identical": True,
            "source_vintage": "StatsNZ-GDP-2026Q2",
        },
    )
    monkeypatch.setattr(MODULE, "canonical_inputs", lambda: ())
    monkeypatch.setattr(
        MODULE,
        "source_health_recovery_report",
        lambda: {
            "status": "verified_repeat_identical",
            "summary": {"resource_count": 142},
        },
    )
    monkeypatch.setattr(
        MODULE,
        "classification_label_occurrence_report",
        lambda: {"status": "verified_exact_literal_occurrence_counts"},
    )
    monkeypatch.setattr(
        MODULE,
        "donor_parity_recovery_report",
        lambda: {
            "status": "verified_with_nonmutating_deviations",
            "repeat_identical": True,
        },
    )
    monkeypatch.setattr(
        MODULE,
        "rebuild_donor_products",
        lambda _root, _index: {
            "raw": {"MANIFEST.json": {"sha256": "raw"}},
            "compatibility": {"compatibility.sqlite": {"sha256": "sqlite"}},
            "gold": {"MANIFEST.json": {"sha256": "gold"}},
            "plots": {"plot.png": {"sha256": "plot"}},
            "raw_manifest_sha256": "raw-pin",
            "compatibility_facts": 341,
            "gold_selected_facts": 321,
            "plot_count": 6,
        },
    )

    def fake_eight_stage(root: Path, index: int) -> dict[str, object]:
        output = root / f"eight-stage-{index}"
        output.mkdir()
        (output / "MANIFEST.json").write_bytes(b"fixed eight stage")
        return {
            "files": MODULE.tree(output),
            "manifest_sha256": "eight-stage-pin",
            "profile_count": 12,
            "fact_count": 739,
            "rights_state": "not_evaluated",
            "gold_selection": "not_performed",
            "publication": "not_performed",
        }

    monkeypatch.setattr(MODULE, "rebuild_eight_stage", fake_eight_stage)
    monkeypatch.setattr(
        MODULE,
        "_rebuild_pharmac_canonical",
        lambda _root, _index: {
            "source_object_sha256": "a" * 64,
            "canonical_fact_sha256": "facts",
            "canonical_lineage_sha256": "lineage",
        },
    )
    monkeypatch.setattr(
        MODULE,
        "_moh_recovery_report",
        lambda _root: {
            "status": "complete",
            "profiles": {"fig27/v1": {}, "fig28/v1": {}},
            "canonical_projection": {
                "status": "verified_source_faithful_projection",
                "input_records": 80,
            },
        },
    )
    monkeypatch.setattr(
        MODULE,
        "_rebuild_qes_canonical",
        lambda _root, _index: {
            "source_object_sha256": "b" * 64,
            "canonical_fact_sha256": "qes-facts",
            "canonical_lineage_sha256": "qes-lineage",
        },
    )
    monkeypatch.setattr(
        MODULE,
        "_rebuild_crown_canonical",
        lambda _root, _index: {
            "source_object_sha256": "c" * 64,
            "canonical_fact_sha256": "crown-facts",
            "canonical_lineage_sha256": "crown-lineage",
        },
    )
    monkeypatch.setattr(
        MODULE,
        "_rebuild_hyefu_crown_canonical",
        lambda _root, _index: {
            "source_object_sha256": "d" * 64,
            "canonical_fact_sha256": "hyefu-crown-facts",
            "canonical_lineage_sha256": "hyefu-crown-lineage",
        },
    )
    monkeypatch.setattr(
        MODULE,
        "_rebuild_fiscal_crown_canonical",
        lambda _root, _index: {
            "source_object_sha256": "e" * 64,
            "canonical_fact_sha256": "fiscal-crown-facts",
            "canonical_lineage_sha256": "fiscal-crown-lineage",
            "projection": {"status": "verified_source_faithful_projection"},
            "build_index": _index,
        },
    )

    def fake_context(
        _silver_root: Path, _source_root: Path, output: Path, *, write: bool = False
    ) -> dict[str, str]:
        _ = write
        output.mkdir()
        (output / "MANIFEST.json").write_bytes(b"fixed context")
        return {"status": "complete"}

    monkeypatch.setattr(MODULE, "export_context_gold", fake_context)

    class FakeColumn:
        def to_pylist(self) -> list[str]:
            return []

    class FakeTable:
        num_rows = 0

        def column(self, _name: str) -> FakeColumn:
            return FakeColumn()

    monkeypatch.setattr(
        MODULE, "query_context_observations", lambda _root, _pin: FakeTable()
    )
    monkeypatch.setattr(
        MODULE,
        "normalize_population_annual",
        lambda _source, output, **_kwargs: (
            output.mkdir(),
            (output / "MANIFEST.json").write_bytes(b"silver"),
            {"counts": {"facts": 1}},
        )[-1],
    )
    result = MODULE.run()
    assert result["status"] == "partial_with_blockers"
    assert result["bronze_objects_unchanged"] is True
    assert result["products_rebuilt"]["canonical_gold"]["status"] == "blocked"
    assert result["products_rebuilt"]["context_gold"]["repeat_identical"] is True
    assert (
        result["products_rebuilt"]["pharmac_canonical_projection"]["repeat_identical"]
        is True
    )
    assert (
        result["products_rebuilt"]["moh_indicators_canonical_projection"][
            "canonical_projection"
        ]["input_records"]
        == 80
    )
    assert (
        result["products_rebuilt"]["qes_canonical_projection"]["repeat_identical"]
        is True
    )
    assert (
        result["products_rebuilt"]["crown_canonical_projection"]["repeat_identical"]
        is True
    )
    assert (
        result["products_rebuilt"]["hyefu_crown_canonical_projection"][
            "repeat_identical"
        ]
        is True
    )
    assert (
        result["products_rebuilt"]["historical_fiscal_crown_canonical_projection"][
            "repeat_identical"
        ]
        is True
    )
    assert (
        result["products_rebuilt"]["canonical_context_consumer"]["status"]
        == "verified_read_only_projection"
    )
    assert result["products_rebuilt"]["donor_sqlite_gold_plots"]["repeat_identical"]
    assert result["products_rebuilt"]["donor_source_native_silver"]["repeat_identical"]
    assert (
        result["products_rebuilt"]["classification_label_occurrences"]["status"]
        == "verified_exact_literal_occurrence_counts"
    )
    assert result["products_rebuilt"]["gdp_june_successor_silver"]["repeat_identical"]
    assert result["products_rebuilt"]["donor_and_canonical_reports"][
        "unresolved_canonical_reports"
    ] == ["canonical_gold_not_rebuilt"]
    assert (
        result["products_rebuilt"]["donor_sqlite_gold_plots"]["compatibility_facts"]
        == 341
    )
    assert "compatibility_sqlite" not in result["required_but_not_rebuilt"]
    assert "all_source_native_silver" not in result["required_but_not_rebuilt"]
    assert (
        "canonical_gold_revision_and_cross_source_reports"
        in result["required_but_not_rebuilt"]
    )
    assert (
        "canonical_classification_drift_revision_and_cross_source_reports"
        not in result["required_but_not_rebuilt"]
    )
    assert (
        "remaining_source_native_silver_profiles_and_canonical_adapters"
        in result["required_but_not_rebuilt"]
    )
