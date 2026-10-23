"""Fixity verification and read-only operational surface for canonical Gold."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_example,
    canonical_gold_export,
    canonical_gold_verification,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_example import (
    summarize_verified_canonical_gold,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_verification import (
    verify_canonical_gold_package,
)
from archive_govt_nz.mcp_server import PROTOCOL_VERSION, Server, call_tool, list_tools


def _budget_input_total_report() -> dict[str, Any]:
    return {
        "schema_version": "archive-govt-nz.health-budget-input-total-reconciliation/v1",
        "scope": "pinned_canonical_appropriation_facts_to_budget_gold_rows",
        "source_package_marker_sha256": ["a" * 64],
        "period_basis": "literal_source_token_only",
        "unit_currency_and_price_basis": "source_context_preserved_currency_unknown",
        "vintage_pooling": "not_performed",
        "donor_control": "not_performed",
        "official_source_control": "not_performed",
        "cross_source_comparison": "not_performed",
        "group_count": 1,
        "input_record_count": 2,
        "status": "exact_canonical_input_totals_reconciled",
        "groups": [
            {
                "source_vintage": "Budget 2025",
                "period_token": "FY2025/26",
                "amount_type": "appropriation",
                "unit": "NZD_thousands",
                "vote": "Health",
                "department": "Health",
                "portfolio": "Health",
                "source_label": "Care",
                "input_record_count": 2,
                "input_record_ids": ["record-1", "record-2"],
                "canonical_input_total": "4.000000000000000000",
                "gold_output_total": "4.000000000000000000",
                "status": "exact_match",
            }
        ],
    }


def _revenue_input_total_report() -> dict[str, Any]:
    return {
        "schema_version": "archive-govt-nz.health-revenue-input-total-reconciliation/v1",
        "scope": "pinned_canonical_revenue_facts_to_revenue_gold_rows",
        "source_package_marker_sha256": ["a" * 64],
        "period_basis": "literal_source_token_only",
        "unit_currency_and_price_basis": "source_context_preserved_currency_unknown",
        "revenue_netting": "not_performed",
        "vintage_pooling": "not_performed",
        "donor_control": "not_performed",
        "official_source_control": "not_performed",
        "cross_source_comparison": "not_performed",
        "group_count": 1,
        "input_record_count": 1,
        "status": "exact_canonical_input_totals_reconciled",
        "groups": [
            {
                "source_vintage": "Budget 2025",
                "period_token": "FY2025/26",
                "amount_type": "estimated_actual",
                "unit": "NZD_thousands",
                "vote": "Health",
                "department": "Health",
                "revenue_type": "Other revenue",
                "source_label": "Operating",
                "input_record_count": 1,
                "input_record_ids": ["record-1"],
                "canonical_input_total": "4.000000000000000000",
                "gold_output_total": "4.000000000000000000",
                "status": "exact_match",
            }
        ],
    }


def _pharmac_input_total_report() -> dict[str, Any]:
    return {
        "schema_version": "archive-govt-nz.health-pharmac-input-total-reconciliation/v1",
        "scope": "pinned_pharmac_silver_facts_to_pharmac_gold_rows",
        "source_package_marker_sha256": ["a" * 64],
        "source_object_sha256": "b" * 64,
        "period_basis": "literal_source_token_only",
        "unit_currency_and_price_basis": (
            "source_context_preserved_currency_and_price_basis_unqualified"
        ),
        "published_change_recalculation": "not_performed",
        "actual_expenditure": "not_asserted",
        "funding_regime_pooling": "not_performed",
        "donor_control": "not_performed",
        "official_source_control": "not_performed",
        "cross_source_comparison": "not_performed",
        "group_count": 1,
        "input_record_count": 1,
        "status": "exact_canonical_input_totals_reconciled",
        "groups": [
            {
                "source_vintage": "Pharmac-CPB-2026-08-07",
                "period_token": "2013/14",
                "amount_type": "published_budget_allocation",
                "unit": "$ Million",
                "source_label": "Medicines budget",
                "funding_regime": "district_health_board_budget_holder",
                "input_record_count": 1,
                "input_record_ids": ["silver-record-1"],
                "gold_record_ids": ["gold-record-1"],
                "canonical_input_total": "1234.500",
                "gold_output_total": "1234.500000000000000000",
                "status": "exact_match",
            }
        ],
    }


def _crown_control_fixture() -> tuple[dict[str, Any], pa.Table]:
    row = {
        "record_id": "gold-1",
        "source_record_id": "source-1",
        "source_object_sha256": "a" * 64,
        "source_vintage": "BEFU-2026",
        "period_token": "year_label:2026",
        "measure": "core_crown_expense",
        "amount_type": "estimated",
        "unit": "$ million",
        "value_token": "1.25",
        "amount": Decimal("1.25"),
    }
    table = pa.Table.from_pylist([row])
    report = canonical_gold_export.build_crown_projection_gold_reconciliation(
        {"crown_befu": table}
    )
    return report, table


def test_crown_projection_reconciliation_fails_closed_on_bad_inputs() -> None:
    report, table = _crown_control_fixture()
    assert report["row_count"] == 1

    with pytest.raises(ValueError, match="canonical_gold_export_invalid"):
        canonical_gold_export.build_crown_projection_gold_reconciliation({})
    for field, value in (
        ("source_record_id", ""),
        ("value_token", "not-a-number"),
        ("source_object_sha256", None),
    ):
        bad = table.to_pylist()
        bad[0][field] = value
        with pytest.raises(ValueError, match="canonical_gold_export_invalid"):
            canonical_gold_export.build_crown_projection_gold_reconciliation(
                {"crown_befu": pa.Table.from_pylist(bad)}
            )
    bad = table.to_pylist()
    bad[0]["amount"] = Decimal(2)
    with pytest.raises(ValueError, match="canonical_gold_export_invalid"):
        canonical_gold_export.build_crown_projection_gold_reconciliation(
            {"crown_befu": pa.Table.from_pylist(bad)}
        )


def test_crown_projection_verifier_binds_report_to_gold_rows(tmp_path: Path) -> None:
    report, table = _crown_control_fixture()
    product = {"projection_gold_reconciliation": report}
    manifest = {"crown_projection_gold_reconciliation_report": report}
    path = tmp_path / "crown_projection_gold_reconciliation.json"
    parquet = tmp_path / "crown_expense_befu_2026.parquet"
    path.write_text(json.dumps(report), encoding="utf-8")
    pq.write_table(table, parquet)
    assert canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
        tmp_path, manifest, {"crown_befu": product}
    )
    assert canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
        tmp_path,
        manifest,
        {
            "crown_befu": product,
            "crown_hyefu": {"projection_gold_reconciliation": report},
        },
    ) is False
    path.unlink()
    assert (
        canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
            tmp_path, manifest, {"crown_befu": product}
        )
        is False
    )
    path.write_text(json.dumps(report), encoding="utf-8")

    assert (
        canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
            tmp_path, {}, {}
        )
        is False
    )
    assert (
        canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
            tmp_path, manifest, {"crown_befu": {"projection_gold_reconciliation": {}}}
        )
        is False
    )

    path.write_text("{", encoding="utf-8")
    assert (
        canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
            tmp_path, manifest, {"crown_befu": product}
        )
        is False
    )
    path.write_text(json.dumps(report), encoding="utf-8")
    bad_table = table.to_pylist()
    different_amount_text = "2"
    bad_table[0]["value_token"] = different_amount_text
    pq.write_table(pa.Table.from_pylist(bad_table), parquet)
    assert (
        canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
            tmp_path, manifest, {"crown_befu": product}
        )
        is False
    )
    invalid_amount_text = "not-a-number"
    bad_table[0]["value_token"] = invalid_amount_text
    pq.write_table(pa.Table.from_pylist(bad_table), parquet)
    assert (
        canonical_gold_verification._crown_projection_control_matches(  # noqa: SLF001
            tmp_path, manifest, {"crown_befu": product}
        )
        is False
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda report: report.update(status="approved"),
        lambda report: report.update(families=[]),
        lambda report: report.update(families=[None]),
        lambda report: report["families"][0].update(row_count=True),
        lambda report: report["families"][0].update(gold_table="outside.parquet"),
        lambda report: report.update(row_count=2),
    ],
)
def test_crown_projection_report_shape_rejects_invalid_contracts(
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    report, _table = _crown_control_fixture()
    mutate(report)
    assert not canonical_gold_verification._valid_crown_projection_gold_reconciliation(  # noqa: SLF001
        None
    )
    assert not canonical_gold_verification._valid_crown_projection_gold_reconciliation(  # noqa: SLF001
        report
    )


def test_budget_input_total_report_rejects_unsupported_or_unequal_claims() -> None:
    report = _budget_input_total_report()
    assert canonical_gold_verification._valid_budget_input_total_reconciliation(  # noqa: SLF001
        report
    )

    mismatched = {**report, "groups": [{**report["groups"][0]}]}
    mismatched["groups"][0]["gold_output_total"] = "5"
    unsupported = {**report, "official_source_control": "reconciled"}
    duplicated = {**report, "groups": [{**report["groups"][0]}]}
    duplicated["groups"][0]["input_record_ids"] = ["record-1", "record-1"]

    assert not canonical_gold_verification._valid_budget_input_total_reconciliation(  # noqa: SLF001
        mismatched
    )
    assert not canonical_gold_verification._valid_budget_input_total_reconciliation(  # noqa: SLF001
        unsupported
    )
    assert not canonical_gold_verification._valid_budget_input_total_reconciliation(  # noqa: SLF001
        duplicated
    )


def test_budget_input_total_report_pins_are_bound_to_manifest_provenance() -> None:
    report = _budget_input_total_report()
    budget_product = {"input_total_reconciliation": report}
    products = {"budget": budget_product}
    markers = ["a" * 64]

    assert canonical_gold_verification._budget_reconciliation_matches_manifest(  # noqa: SLF001
        report, markers, products
    )

    unrelated = {**report, "source_package_marker_sha256": ["b" * 64]}
    unrelated_products = {"budget": {"input_total_reconciliation": unrelated}}
    assert not canonical_gold_verification._budget_reconciliation_matches_manifest(  # noqa: SLF001
        unrelated, markers, unrelated_products
    )
    assert not canonical_gold_verification._budget_reconciliation_matches_manifest(  # noqa: SLF001
        report, markers, {"budget": {"input_total_reconciliation": unrelated}}
    )


def test_revenue_input_total_report_pins_are_bound_to_manifest_provenance() -> None:
    report = _revenue_input_total_report()
    markers = ["a" * 64]
    products = {"revenue": {"input_total_reconciliation": report}}

    assert canonical_gold_verification._revenue_reconciliation_matches_manifest(  # noqa: SLF001
        report, markers, products
    )
    unrelated = {**report, "source_package_marker_sha256": ["b" * 64]}
    assert not canonical_gold_verification._revenue_reconciliation_matches_manifest(  # noqa: SLF001
        unrelated,
        markers,
        {"revenue": {"input_total_reconciliation": unrelated}},
    )
    assert not canonical_gold_verification._revenue_reconciliation_matches_manifest(  # noqa: SLF001
        report,
        markers,
        {"revenue": {"input_total_reconciliation": unrelated}},
    )


def test_pharmac_input_total_report_rejects_unequal_or_unsupported_claims() -> None:
    report = _pharmac_input_total_report()
    assert canonical_gold_verification._valid_pharmac_input_total_reconciliation(  # noqa: SLF001
        report
    )

    unequal = {**report, "groups": [{**report["groups"][0]}]}
    unequal["groups"][0]["gold_output_total"] = "5"
    duplicated = {**report, "groups": [{**report["groups"][0]}]}
    duplicated["groups"][0]["gold_record_ids"] = ["gold-record-1", "gold-record-1"]
    unsupported = {**report, "actual_expenditure": "verified"}

    for invalid in (unequal, duplicated, unsupported):
        assert (
            not canonical_gold_verification._valid_pharmac_input_total_reconciliation(  # noqa: SLF001
                invalid
            )
        )


def test_pharmac_input_total_report_copies_bind_to_manifest_and_source(
    tmp_path: Path,
) -> None:
    report = _pharmac_input_total_report()
    markers = ["a" * 64]
    products = {"pharmac": {"input_total_reconciliation": report}}
    projection = {"source_object_sha256": "b" * 64}
    manifest = {
        "package_marker_sha256": markers,
        "pharmac_input_total_reconciliation_report": report,
        "pharmac_projection": projection,
    }
    path = tmp_path / "pharmac_input_total_reconciliation.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    assert canonical_gold_verification._pharmac_reconciliation_matches_manifest(  # noqa: SLF001
        report, markers, products, projection
    )
    assert canonical_gold_verification._pharmac_control_copies_match(  # noqa: SLF001
        tmp_path, manifest, markers, products
    )

    missing_copy = {**manifest}
    del missing_copy["pharmac_input_total_reconciliation_report"]
    assert not canonical_gold_verification._pharmac_control_copies_match(  # noqa: SLF001
        tmp_path, missing_copy, markers, products
    )
    assert not canonical_gold_verification._pharmac_reconciliation_matches_manifest(  # noqa: SLF001
        report, ["c" * 64], products, projection
    )

    path.write_text("not-json", encoding="utf-8")
    assert not canonical_gold_verification._pharmac_control_copies_match(  # noqa: SLF001
        tmp_path, manifest, markers, products
    )
    path.unlink()
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    assert canonical_gold_verification._pharmac_control_copies_match(  # noqa: SLF001
        legacy_root, {}, markers, {}
    )
    (legacy_root / path.name).write_text("{}", encoding="utf-8")
    assert not canonical_gold_verification._pharmac_control_copies_match(  # noqa: SLF001
        legacy_root, {}, markers, {}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("unit", ""),
        ("input_record_count", 2),
        ("canonical_input_total", "not-a-decimal"),
        ("gold_output_total", "NaN"),
        ("gold_output_total", "5"),
    ],
)
def test_revenue_input_total_report_rejects_malformed_groups(
    field: str, value: object
) -> None:
    report = _revenue_input_total_report()
    report["groups"] = [dict(report["groups"][0])]
    report["groups"][0][field] = value

    assert not canonical_gold_verification._valid_revenue_input_total_reconciliation(  # noqa: SLF001
        report
    )


def test_revenue_input_total_report_rejects_duplicate_and_unsorted_groups() -> None:
    report = _revenue_input_total_report()
    original = report["groups"][0]
    later = {
        **original,
        "source_vintage": "Budget 2026",
        "input_record_ids": ["record-2"],
    }
    report["groups"] = [original, later]
    report["group_count"] = report["input_record_count"] = 2
    assert canonical_gold_verification._valid_revenue_input_total_reconciliation(  # noqa: SLF001
        report
    )

    assert not canonical_gold_verification._valid_revenue_input_total_reconciliation(  # noqa: SLF001
        {**report, "groups": [later, original]}
    )
    assert not canonical_gold_verification._valid_revenue_input_total_reconciliation(  # noqa: SLF001
        {
            **report,
            "groups": [original, {**later, "input_record_ids": ["record-1"]}],
        }
    )


def test_revenue_input_total_report_rejects_invalid_summary_and_group_shapes() -> None:
    assert not canonical_gold_verification._valid_revenue_input_total_reconciliation(  # noqa: SLF001
        []
    )
    for report in (
        {**_revenue_input_total_report(), "groups": []},
        {**_revenue_input_total_report(), "group_count": 0},
        {**_revenue_input_total_report(), "groups": [None]},
    ):
        assert (
            not canonical_gold_verification._valid_revenue_input_total_reconciliation(  # noqa: SLF001
                report
            )
        )


@pytest.mark.parametrize(
    ("product_name", "report_name", "output_name", "report_factory"),
    [
        (
            "budget",
            "budget_input_total_reconciliation_report",
            "budget_input_total_reconciliation.json",
            _budget_input_total_report,
        ),
        (
            "revenue",
            "revenue_input_total_reconciliation_report",
            "revenue_input_total_reconciliation.json",
            _revenue_input_total_report,
        ),
    ],
)
def test_input_total_controls_require_all_copies_or_none(
    tmp_path: Path,
    product_name: str,
    report_name: str,
    output_name: str,
    report_factory: Callable[[], dict[str, Any]],
) -> None:
    report = report_factory()
    marker = "a" * 64
    product = {"input_total_reconciliation": report}
    manifest = {
        "package_marker_sha256": [marker],
        report_name: report,
    }
    output = tmp_path / output_name
    output.write_text(json.dumps(report), encoding="utf-8")

    assert canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path, manifest, {product_name: product}
    )

    missing_manifest_copy = dict(manifest)
    del missing_manifest_copy[report_name]
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path, missing_manifest_copy, {product_name: product}
    )

    missing_product_copy = {product_name: {}}
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path, manifest, missing_product_copy
    )

    different_nested = {**report, "official_source_control": "reported"}
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path,
        manifest,
        {product_name: {"input_total_reconciliation": different_nested}},
    )

    output.write_text("not-json", encoding="utf-8")
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path, manifest, {product_name: product}
    )
    output.write_text(
        json.dumps({**report, "input_record_count": 99}), encoding="utf-8"
    )
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path, manifest, {product_name: product}
    )

    output.unlink()
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        tmp_path, manifest, {product_name: product}
    )

    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    assert canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        legacy_root, {}, {product_name: {}}
    )
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        legacy_root, {}, []
    )
    (legacy_root / output_name).write_text("{}", encoding="utf-8")
    assert not canonical_gold_verification._input_total_controls_match_manifest(  # noqa: SLF001
        legacy_root, {}, {product_name: {}}
    )


def _package(root: Path) -> tuple[Path, str]:
    root.mkdir()
    payload = b"verified-output-payload"
    output = root / "observations.parquet"
    output.write_bytes(payload)
    revision_report = {
        "schema_version": "archive-govt-nz.health-revision-reconciliation/v1",
        "scope": "same_recordset_measure_source_label_and_exact_context_period_across_observed_vintages",
        "key_fields": [
            "recordset",
            "measure",
            "source_label",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "institutional_coverage",
            "accounting_basis",
            "period_token",
        ],
        "completeness": "historical_budget_revenue_biff8_budget_biff8_revenue_pharmac_moh_crown_product_rows",
        "difference_interpretation": "not_assessed",
        "other_product_revisions": "not_assessed",
        "cross_source_comparison": "not_performed",
        "product_revisions": {
            "budget": {
                "scope": "same_literal_source_dimensions_and_period_token_within_product",
                "key_fields": [
                    "period_token",
                    "amount_type",
                    "unit",
                    "vote",
                    "department",
                    "portfolio",
                    "source_label",
                ],
                "completeness": "observed_rows_only",
                "shared_series_period_count": 0,
                "unchanged_series_period_count": 0,
                "ambiguous_series_period_count": 0,
                "changed_candidate_count": 0,
                "interpretation": "not_assessed",
                "candidates": [],
            },
            "revenue": {
                "scope": "same_literal_source_dimensions_and_period_token_within_product",
                "key_fields": [
                    "period_token",
                    "amount_type",
                    "unit",
                    "vote",
                    "department",
                    "revenue_type",
                    "source_label",
                ],
                "completeness": "observed_rows_only",
                "shared_series_period_count": 0,
                "unchanged_series_period_count": 0,
                "ambiguous_series_period_count": 0,
                "changed_candidate_count": 0,
                "interpretation": "not_assessed",
                "candidates": [],
            },
            "pharmac": {
                "scope": "same_literal_source_dimensions_and_period_token_within_product",
                "key_fields": [
                    "period_token",
                    "measure",
                    "unit",
                    "currency",
                    "price_basis",
                    "base_period",
                    "denominator_definition",
                    "amount_type",
                    "source_label",
                    "budget_scope",
                    "funding_regime",
                ],
                "completeness": "observed_rows_only",
                "shared_series_period_count": 0,
                "unchanged_series_period_count": 0,
                "ambiguous_series_period_count": 0,
                "changed_candidate_count": 0,
                "interpretation": "not_assessed",
                "candidates": [],
            },
            "moh": {
                "scope": "same_literal_source_dimensions_and_period_token_within_product",
                "key_fields": [
                    "period_token",
                    "profile",
                    "source_label",
                    "price_basis",
                    "per_capita",
                    "unit",
                    "price_base",
                    "denominator",
                ],
                "completeness": "observed_rows_only",
                "shared_series_period_count": 0,
                "unchanged_series_period_count": 0,
                "ambiguous_series_period_count": 0,
                "changed_candidate_count": 0,
                "interpretation": "not_assessed",
                "candidates": [],
            },
            "crown": {
                "scope": "same_literal_source_dimensions_and_period_token_within_product",
                "key_fields": [
                    "period_token",
                    "measure",
                    "amount_type",
                    "unit",
                    "currency",
                    "price_basis",
                    "base_period",
                    "denominator_definition",
                    "source_label",
                    "institutional_coverage",
                    "accounting_basis",
                ],
                "completeness": "observed_rows_only",
                "shared_series_period_count": 0,
                "unchanged_series_period_count": 0,
                "ambiguous_series_period_count": 0,
                "changed_candidate_count": 0,
                "interpretation": "not_assessed",
                "candidates": [],
            },
        },
        "shared_series_period_count": 2,
        "unchanged_series_period_count": 1,
        "changed_candidate_count": 1,
        "ambiguous_series_period_count": 0,
        "candidates": [],
    }
    for name, key_fields in (
        (
            "biff8_budget",
            [
                "period_token",
                "measure",
                "amount_type",
                "unit",
                "currency",
                "price_basis",
                "base_period",
                "denominator_definition",
                "source_label",
                "vote",
                "appropriation",
                "department",
                "portfolio",
                "value_basis",
            ],
        ),
        (
            "biff8_revenue",
            [
                "period_token",
                "measure",
                "amount_type",
                "unit",
                "currency",
                "price_basis",
                "base_period",
                "denominator_definition",
                "source_label",
                "vote",
                "department",
                "revenue_type",
                "source_application_id",
                "value_basis",
            ],
        ),
    ):
        revision_report["product_revisions"][name] = {
            **revision_report["product_revisions"]["budget"],
            "key_fields": key_fields,
        }
    revision_payload = (
        json.dumps(revision_report, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    revision_output = root / "historical_revision_reconciliation.json"
    revision_output.write_bytes(revision_payload)
    overlap_report = {
        "schema_version": "archive-govt-nz.health-cross-source-period-overlap/v1",
        "scope": "observed_canonical_product_rows_only",
        "match_basis": "literal_period_token_only",
        "completeness": "observed_rows_only",
        "comparability": "not_assessed",
        "numeric_variance": "not_computed",
        "cross_source_join": "not_performed",
        "overlap_group_count": 0,
        "groups": [],
    }
    overlap_payload = (
        json.dumps(overlap_report, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    overlap_output = root / "cross_source_period_overlap.json"
    overlap_output.write_bytes(overlap_payload)
    manifest = {
        "schema_version": "archive-govt-nz.health-canonical-gold/v2",
        "outputs": {
            output.name: {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "rows": 1,
            },
            revision_output.name: {
                "sha256": hashlib.sha256(revision_payload).hexdigest(),
                "bytes": len(revision_payload),
                "kind": "report",
            },
            overlap_output.name: {
                "sha256": hashlib.sha256(overlap_payload).hexdigest(),
                "bytes": len(overlap_payload),
                "kind": "report",
            },
        },
        "products": {"historical": {"input_records": 1}},
        "temporal_coverage_report": {
            "schema_version": "archive-govt-nz.health-temporal-coverage/v1",
            "groups": [
                {
                    "observed_periods": [
                        {"period_token": "FY2024/25", "observation_count": 2},
                        {"period_token": "FY2025/26", "observation_count": 1},
                    ]
                }
            ],
        },
        "classification_drift_report": {
            "schema_version": "archive-govt-nz.health-classification-drift/v1",
            "mapping": "not_inferred",
            "candidates": [],
        },
        "revision_reconciliation_report": revision_report,
        "cross_source_period_overlap_report": overlap_report,
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    marker = root / "MANIFEST.json"
    marker.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root, hashlib.sha256(marker.read_bytes()).hexdigest()


def _ready_server() -> Server:
    server = Server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "gold-verification-test", "version": "1"},
            },
        }
    )
    assert response is not None
    assert "result" in response
    assert (
        server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )
    return server


def test_cli_mcp_parity_and_no_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = _package(tmp_path / "gold")
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    receipt = verify_canonical_gold_package(root, pin)
    result = app(
        [
            "health-appropriations-verify-canonical-gold",
            str(root),
            pin,
        ],
        exit_on_error=False,
        result_action="return_value",
    )
    cli_receipt = json.loads(capsys.readouterr().out)
    assert result == 0
    assert cli_receipt.pop("command") == "health-appropriations-verify-canonical-gold"
    assert cli_receipt == receipt
    assert receipt["status"] == "verified"
    assert receipt["output_count"] == 3
    assert receipt["output_bytes"] == sum(
        (root / name).stat().st_size
        for name in (
            "observations.parquet",
            "historical_revision_reconciliation.json",
            "cross_source_period_overlap.json",
        )
    )
    assert receipt["products"] == ["historical"]
    assert receipt["temporal_coverage_groups"] == 1
    assert receipt["verification_scope"] == "manifest_declared_output_fixity"
    assert receipt["rights_state"] == "not_evaluated"
    assert receipt["publication"] == "not_performed"

    arguments = {"package_dir": str(root), "manifest_sha256": pin}
    assert (
        call_tool("health_appropriations_verify_canonical_gold", arguments) == receipt
    )
    tool = _ready_server().handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "health_appropriations_verify_canonical_gold",
                "arguments": arguments,
            },
        }
    )
    assert tool is not None
    assert "error" not in tool
    assert json.loads(tool["result"]["content"][0]["text"]) == receipt
    assert tool["result"]["isError"] is False
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before
    definition = next(
        item
        for item in list_tools()
        if item["name"] == "health_appropriations_verify_canonical_gold"
    )
    assert definition["annotations"] == {
        "title": "Verify canonical Health Gold package",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }


def test_consumer_example_summarizes_only_verified_manifest_reports(
    tmp_path: Path,
) -> None:
    root, manifest_sha256 = _package(tmp_path / "gold")
    summary = summarize_verified_canonical_gold(root, manifest_sha256)

    assert summary["status"] == "verified_package_summary"
    assert summary["manifest_sha256"] == manifest_sha256
    assert summary["products"] == {"historical": {"input_records": 1}}
    assert summary["temporal_coverage"] == {
        "exact_context_group_count": 1,
        "observation_count": 3,
        "period_token_count": 2,
    }
    assert summary["historical_revisions"]["changed_candidate_count"] == 1
    assert summary["historical_revisions"]["difference_interpretation"] == (
        "not_assessed"
    )
    assert summary["product_revisions"] == {
        "budget": {
            "shared_series_period_count": 0,
            "unchanged_series_period_count": 0,
            "changed_candidate_count": 0,
            "ambiguous_series_period_count": 0,
        },
        "revenue": {
            "shared_series_period_count": 0,
            "unchanged_series_period_count": 0,
            "changed_candidate_count": 0,
            "ambiguous_series_period_count": 0,
        },
        **{
            product: {
                "shared_series_period_count": 0,
                "unchanged_series_period_count": 0,
                "changed_candidate_count": 0,
                "ambiguous_series_period_count": 0,
            }
            for product in ("biff8_budget", "biff8_revenue", "pharmac", "moh", "crown")
        },
    }
    assert summary["cross_source_period_token_overlaps"] == {
        "overlap_group_count": 0,
        "match_basis": "literal_period_token_only",
        "comparability": "not_assessed",
        "numeric_variance": "not_computed",
    }
    assert summary["cross_source_comparison"] == "not_performed"
    assert summary["rights_state"] == "not_evaluated"
    assert summary["publication"] == "not_performed"


def test_legacy_v2_gold_package_remains_verifiable(tmp_path: Path) -> None:
    root, _pin = _package(tmp_path / "legacy-gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    report = manifest["revision_reconciliation_report"]
    report["completeness"] = "historical_budget_revenue_pharmac_moh_crown_product_rows"
    report["product_revisions"].pop("biff8_budget")
    report["product_revisions"].pop("biff8_revenue")
    payload = (
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    (root / "historical_revision_reconciliation.json").write_bytes(payload)
    manifest["outputs"]["historical_revision_reconciliation.json"].update(
        {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
    )
    marker.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)
    summary = summarize_verified_canonical_gold(root, pin)

    assert receipt["status"] == "verified"
    assert set(summary["product_revisions"]) == {
        "budget",
        "revenue",
        "pharmac",
        "moh",
        "crown",
    }


def test_consumer_example_fails_closed_on_unverified_or_malformed_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _pin = _package(tmp_path / "gold")
    with pytest.raises(ValueError, match=r"^canonical_gold_example_invalid$"):
        summarize_verified_canonical_gold(root, "0" * 64)

    monkeypatch.setattr(
        canonical_gold_example,
        "verify_canonical_gold_package",
        lambda *_args: {"status": "verified"},
    )
    marker = root / "MANIFEST.json"
    with pytest.raises(ValueError, match=r"^canonical_gold_example_invalid$"):
        summarize_verified_canonical_gold(root, "0" * 64)

    for payload in (b"{", b"\xff", b"[]"):
        marker.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        with pytest.raises(ValueError, match=r"^canonical_gold_example_invalid$"):
            summarize_verified_canonical_gold(root, digest)

    payload = b"{}"
    marker.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError, match=r"^canonical_gold_example_invalid$"):
        summarize_verified_canonical_gold(root, digest)

    malformed_inputs = (
        lambda: canonical_gold_example._temporal_counts([None]),  # noqa: SLF001
        lambda: canonical_gold_example._temporal_counts(  # noqa: SLF001
            [{"observed_periods": [None]}]
        ),
        lambda: canonical_gold_example._temporal_counts(  # noqa: SLF001
            [{"observed_periods": [{"period_token": 1, "observation_count": 1}]}]
        ),
        lambda: canonical_gold_example._product_counts({"historical": None}),  # noqa: SLF001
        lambda: canonical_gold_example._product_counts(  # noqa: SLF001
            {"historical": {"input_records": -1}}
        ),
        lambda: canonical_gold_example._revision_counts(  # noqa: SLF001
            {"changed_candidate_count": -1}
        ),
        lambda: canonical_gold_example._product_revision_counts(  # noqa: SLF001
            {"product_revisions": {}}
        ),
        lambda: canonical_gold_example._product_revision_counts(  # noqa: SLF001
            {"product_revisions": {"budget": None, "revenue": {}}}
        ),
        lambda: canonical_gold_example._product_revision_counts(  # noqa: SLF001
            {
                "product_revisions": {
                    "budget": {
                        "shared_series_period_count": -1,
                        "unchanged_series_period_count": 0,
                        "changed_candidate_count": 0,
                        "ambiguous_series_period_count": 0,
                    },
                    "revenue": {
                        "shared_series_period_count": 0,
                        "unchanged_series_period_count": 0,
                        "changed_candidate_count": 0,
                        "ambiguous_series_period_count": 0,
                    },
                }
            }
        ),
    )
    for operation in malformed_inputs:
        with pytest.raises(ValueError, match=r"^canonical_gold_example_invalid$"):
            operation()


@pytest.mark.parametrize(
    "failure",
    [
        "wrong_pin",
        "tampered_output",
        "tampered_output_size",
        "missing_output",
        "extra_output",
        "unsafe_name",
        "invalid_manifest_schema",
        "invalid_reports",
        "invalid_classification_report",
    ],
)
def test_invalid_package_fails_closed_and_redacted(
    tmp_path: Path, failure: str
) -> None:
    root, pin = _package(tmp_path / "gold")
    if failure == "wrong_pin":
        pin = "0" * 64
    elif failure == "tampered_output":
        (root / "observations.parquet").write_bytes(
            b"x" * len(b"verified-output-payload")
        )
    elif failure == "tampered_output_size":
        (root / "observations.parquet").write_bytes(b"short")
    elif failure == "missing_output":
        (root / "observations.parquet").unlink()
    elif failure == "extra_output":
        (root / "unlisted.txt").write_text("unlisted", encoding="utf-8")
    elif failure == "unsafe_name":
        manifest_path = root / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["outputs"]["../escape"] = manifest["outputs"].pop(
            "observations.parquet"
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        pin = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    elif failure in {
        "invalid_manifest_schema",
        "invalid_reports",
        "invalid_classification_report",
    }:
        manifest_path = root / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if failure == "invalid_manifest_schema":
            manifest["schema_version"] = "unsupported/v1"
        elif failure == "invalid_reports":
            manifest["temporal_coverage_report"] = []
        else:
            manifest["classification_drift_report"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        pin = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_canonical_gold_package"
    assert str(root) not in json.dumps(receipt)
    assert "verified-output-payload" not in json.dumps(receipt)

    response = _ready_server().handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "health_appropriations_verify_canonical_gold",
                "arguments": {"package_dir": str(root), "manifest_sha256": pin},
            },
        }
    )
    assert response is not None
    assert response["result"]["isError"] is True
    assert json.loads(response["result"]["content"][0]["text"]) == receipt


@pytest.mark.parametrize(
    "failure", ["wrong_shape", "candidate_type", "negative_count", "count_mismatch"]
)
def test_invalid_product_revision_reports_fail_closed(
    tmp_path: Path, failure: str
) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    report = manifest["revision_reconciliation_report"]
    if failure == "wrong_shape":
        report["product_revisions"] = []
    elif failure == "candidate_type":
        report["product_revisions"]["budget"]["candidates"] = None
    elif failure == "negative_count":
        report["product_revisions"]["budget"]["shared_series_period_count"] = -1
    else:
        report["product_revisions"]["budget"]["changed_candidate_count"] = 1
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_canonical_gold_package"


@pytest.mark.parametrize(
    "failure",
    [
        "bad_count",
        "unsorted_period",
        "single_product",
        "bad_unit",
        "noncanonical_product",
        "zero_rows",
        "empty_vintage",
        "empty_record_id",
        "duplicate_products",
        "bad_comparability",
        "bad_numeric_variance",
        "wrong_match_basis",
        "nonobject_group",
        "empty_period",
    ],
)
def test_invalid_cross_source_overlap_report_fails_closed(  # noqa: C901, PLR0912 - each mutation is one independent report contract
    tmp_path: Path, failure: str
) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    valid_group = {
        "period_token": "FY2024/25",
        "status": "literal_period_token_overlap_candidate",
        "product_groups": [
            {
                "product": "budget",
                "row_count": 1,
                "source_vintages": ["Budget 2025"],
                "units": ["NZD million"],
                "input_record_ids": ["budget-1"],
            },
            {
                "product": "historical",
                "row_count": 1,
                "source_vintages": ["History 2025"],
                "units": ["NZD million"],
                "input_record_ids": ["history-1"],
            },
        ],
        "comparability": "not_assessed",
        "numeric_variance": "not_computed",
    }
    report = manifest["cross_source_period_overlap_report"]
    report["groups"] = [valid_group]
    report["overlap_group_count"] = 1
    if failure == "bad_count":
        report["overlap_group_count"] = 2
    elif failure == "unsorted_period":
        report["groups"] = [
            {**valid_group, "period_token": "FY2025/26"},
            valid_group,
        ]
        report["overlap_group_count"] = 2
    elif failure == "single_product":
        valid_group["product_groups"] = valid_group["product_groups"][:1]
    elif failure == "bad_unit":
        valid_group["product_groups"][0]["units"] = [""]
    elif failure == "noncanonical_product":
        valid_group["product_groups"][0]["product"] = "unsupported"
    elif failure == "zero_rows":
        valid_group["product_groups"][0]["row_count"] = 0
    elif failure == "empty_vintage":
        valid_group["product_groups"][0]["source_vintages"] = [""]
    elif failure == "empty_record_id":
        valid_group["product_groups"][0]["input_record_ids"] = [""]
    elif failure == "duplicate_products":
        valid_group["product_groups"][1]["product"] = "budget"
    elif failure == "bad_comparability":
        valid_group["comparability"] = "comparable"
    elif failure == "bad_numeric_variance":
        valid_group["numeric_variance"] = "computed"
    elif failure == "wrong_match_basis":
        report["match_basis"] = "normalized_period"
    elif failure == "nonobject_group":
        report["groups"] = [None]
        report["overlap_group_count"] = 1
    else:
        valid_group["period_token"] = ""
    payload = (
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    output = root / "cross_source_period_overlap.json"
    output.write_bytes(payload)
    manifest["outputs"][output.name] = {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "kind": "report",
    }
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_canonical_gold_package"


def test_valid_overlap_report_accepts_concrete_and_unknown_units(
    tmp_path: Path,
) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    report = manifest["cross_source_period_overlap_report"]
    report["groups"] = [
        {
            "period_token": "FY2024/25",
            "status": "literal_period_token_overlap_candidate",
            "product_groups": [
                {
                    "product": "budget",
                    "row_count": 1,
                    "source_vintages": ["Budget 2025"],
                    "units": ["NZD million"],
                    "input_record_ids": ["budget-1"],
                },
                {
                    "product": "moh",
                    "row_count": 1,
                    "source_vintages": ["MoH HAIR 2024"],
                    "units": ["unknown_not_asserted"],
                    "input_record_ids": ["moh-1"],
                },
            ],
            "comparability": "not_assessed",
            "numeric_variance": "not_computed",
        }
    ]
    report["overlap_group_count"] = 1
    payload = (
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    output = root / "cross_source_period_overlap.json"
    output.write_bytes(payload)
    manifest["outputs"][output.name] = {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "kind": "report",
    }
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "verified"
    assert receipt["temporal_coverage_groups"] == 1


def test_invalid_revision_report_fails_closed(tmp_path: Path) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    manifest["revision_reconciliation_report"] = []
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_canonical_gold_package"


def test_duplicate_manifest_keys_fail_closed(tmp_path: Path) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    marker.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"


@pytest.mark.parametrize(
    "manifest_change",
    ["invalid_json_shape", "invalid_outputs", "invalid_output_metadata", "bad_digest"],
)
def test_malformed_manifest_contracts_fail_closed(
    tmp_path: Path, manifest_change: str
) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    if manifest_change == "invalid_json_shape":
        marker.write_text("[]", encoding="utf-8")
    else:
        if manifest_change == "invalid_outputs":
            manifest["outputs"] = []
        elif manifest_change == "invalid_output_metadata":
            manifest["outputs"]["observations.parquet"] = []
        elif manifest_change == "bad_digest":
            manifest["outputs"]["observations.parquet"]["sha256"] = "invalid"
        marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"


def test_output_byte_limit_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _pin = _package(tmp_path / "gold")
    extra_payload = b"x"
    extra = root / "extra.bin"
    extra.write_bytes(extra_payload)
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    manifest["outputs"][extra.name] = {
        "sha256": hashlib.sha256(extra_payload).hexdigest(),
        "bytes": len(extra_payload),
    }
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()
    monkeypatch.setattr(
        canonical_gold_verification,
        "MAX_PACKAGE_BYTES",
        len(b"verified-output-payload"),
    )

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"


def test_manifest_size_limit_and_invalid_root_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, pin = _package(tmp_path / "gold")
    monkeypatch.setattr(canonical_gold_verification, "MAX_MANIFEST_BYTES", 1)

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"
    assert (
        verify_canonical_gold_package(tmp_path / "missing", pin)["status"] == "failed"
    )


def test_missing_manifest_fails_closed(tmp_path: Path) -> None:
    root, pin = _package(tmp_path / "gold")
    (root / "MANIFEST.json").unlink()

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"
