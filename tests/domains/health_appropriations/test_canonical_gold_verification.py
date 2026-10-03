"""Fixity verification and read-only operational surface for canonical Gold."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_example,
    canonical_gold_verification,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_example import (
    summarize_verified_canonical_gold,
)
from archive_govt_nz.domains.health_appropriations.canonical_gold_verification import (
    verify_canonical_gold_package,
)
from archive_govt_nz.mcp_server import PROTOCOL_VERSION, Server, call_tool, list_tools


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
        "completeness": "historical_budget_revenue_pharmac_moh_crown_product_rows",
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
            for product in ("pharmac", "moh", "crown")
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
    "failure", ["bad_count", "unsorted_period", "single_product", "bad_unit"]
)
def test_invalid_cross_source_overlap_report_fails_closed(
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
    else:
        valid_group["product_groups"][0]["units"] = ["NZD million", "unknown"]
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
