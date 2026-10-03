"""Deterministic, evidence-bounded health source census status report."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

SOURCE_CENSUS_VERSION = "archive-govt-nz.health-source-census/v1"
CONTEXT_CENSUS_VERSION = "archive-govt-nz.health-source-context-census/v1"
REPORT_VERSION = "archive-govt-nz.health-source-health-report/v1"
_SHA256_HEX_LENGTH = 64


class SourceHealthReportError(ValueError):
    """Raised when census inputs cannot support an auditable report."""


def _fail(code: str) -> NoReturn:
    raise SourceHealthReportError(code)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class CaptureEvidence:
    """Capture manifest and CAS inputs used for an independent reconciliation."""

    manifest: dict[str, Any]
    manifest_bytes: bytes
    manifest_name: str
    cas_root: Path


@dataclass(frozen=True)
class LayoutEvidence:
    """Pinned structural PDF report and its original serialized bytes."""

    report: dict[str, Any]
    report_bytes: bytes


def _resource_rows(resources: list[Any]) -> list[dict[str, Any]]:
    resource_ids: set[str] = set()
    resource_rows: list[dict[str, Any]] = []
    for row in resources:
        if not isinstance(row, dict):
            _fail("source_census_row_invalid")
        source_id = row.get("source_id")
        disposition = row.get("disposition")
        if not isinstance(source_id, str) or not source_id or source_id in resource_ids:
            _fail("source_id_missing_or_duplicate")
        if not isinstance(disposition, str) or not disposition:
            _fail("source_disposition_missing")
        resource_ids.add(source_id)
        license_label = row.get("license")
        rights_uri = row.get("rights_uri")
        policy_recorded = bool(
            isinstance(license_label, str)
            and license_label.strip()
            and isinstance(rights_uri, str)
            and rights_uri.strip()
        )
        resource_rows.append(
            {
                "entity_type": "source_resource",
                "entity_id": source_id,
                "family": row.get("family"),
                "target_vintage_label": row.get("title"),
                "vintage_basis": "source_title_verbatim",
                "inventory_state": disposition,
                "inventory_reason": row.get("reason"),
                "object_sha256": row.get("object_sha256"),
                "rights": {
                    "state": "policy_reference_recorded_not_evaluated"
                    if policy_recorded
                    else "not_evaluated_policy_reference_missing",
                    "license_label": license_label,
                    "policy_uri": rights_uri,
                },
                "temporal_coverage_state": "not_assessed_source_calendar_not_in_census",
                "layout_drift_state": "not_assessed_per_source_baseline_not_in_census",
            }
        )
    resource_rows.sort(key=lambda item: item["entity_id"])
    return resource_rows


def _context_rows(series: list[Any]) -> list[dict[str, Any]]:
    series_ids: set[str] = set()
    context_rows: list[dict[str, Any]] = []
    for row in series:
        if not isinstance(row, dict):
            _fail("context_census_row_invalid")
        series_id = row.get("id")
        vintage = row.get("vintage")
        if (
            not isinstance(series_id, str)
            or not series_id
            or series_id in series_ids
            or not isinstance(vintage, str)
            or not vintage
        ):
            _fail("context_series_identity_or_vintage_missing")
        series_ids.add(series_id)
        context_rows.append(
            {
                "entity_type": "context_series_vintage",
                "entity_id": series_id,
                "family": row.get("family"),
                "series_id": row.get("series_id"),
                "target_vintage_label": vintage,
                "vintage_basis": "context_census_verbatim",
                "period_description": row.get("period"),
                "qualification_state": row.get("qualification", "not_recorded"),
                "rights": {"state": row.get("rights", "not_recorded")},
                "known_gaps": sorted(row.get("gaps", [])),
                "temporal_coverage_state": (
                    "source_extent_recorded_calendar_completeness_not_assessed"
                ),
                "layout_drift_state": "not_assessed_per_vintage_baseline_not_in_census",
            }
        )
    context_rows.sort(key=lambda item: item["entity_id"])
    return context_rows


def _layout_states(  # noqa: C901, PLR0912 - source pin and status validation
    baseline: dict[str, Any] | None,
    census: dict[str, Any],
) -> dict[str, str]:
    """Index structural PDF baseline states without implying semantic coverage."""
    if baseline is None:
        return {}
    rows = baseline.get("pdf_layouts")
    if not isinstance(rows, list):
        _fail("pdf_layout_baseline_shape_invalid")
    census_by_id = _census_rows_by_id(census)
    baseline_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            _fail("pdf_layout_baseline_row_invalid")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in baseline_ids:
            _fail("pdf_layout_baseline_identity_invalid")
        baseline_ids.add(source_id)
    states: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            _fail("pdf_layout_baseline_row_invalid")
        source_id = row.get("source_id")
        status = row.get("status")
        if not isinstance(source_id, str) or not source_id or source_id in states:
            _fail("pdf_layout_baseline_identity_invalid")
        if status not in {"baseline_recorded", "layout_unavailable"}:
            _fail("pdf_layout_baseline_status_invalid")
        census_row = census_by_id.get(source_id)
        if not isinstance(census_row, dict) or row.get(
            "source_object_sha256"
        ) != census_row.get("object_sha256"):
            _fail("pdf_layout_baseline_source_mismatch")
        if status == "baseline_recorded":
            state = "structural_pdf_baseline_recorded_text_and_tables_unassessed"
        elif status == "layout_unavailable":
            state = "structural_pdf_baseline_unavailable"
        else:
            _fail("pdf_layout_baseline_status_invalid")
        states[source_id] = state
    return states


def _census_rows_by_id(census: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = census.get("records")
    if not isinstance(records, list):
        _fail("source_census_row_invalid")
    result: dict[str, dict[str, Any]] = {}
    for row in records:
        if not isinstance(row, dict):
            _fail("source_census_row_invalid")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in result:
            _fail("source_id_missing_or_duplicate")
        result[source_id] = row
    return result


def _recorded_layout_states(
    recorded_report: dict[str, Any] | None,
) -> dict[str, str]:
    """Retain layout states only when their pinned source census still matches."""
    if recorded_report is None:
        return {}
    inputs = recorded_report.get("inputs")
    resources = recorded_report.get("resources")
    if not isinstance(inputs, dict) or not isinstance(resources, list):
        _fail("recorded_layout_report_invalid")
    states: dict[str, str] = {}
    for row in resources:
        if not isinstance(row, dict):
            _fail("recorded_layout_report_invalid")
        source_id = row.get("entity_id")
        state = row.get("layout_drift_state")
        if not isinstance(source_id, str) or not source_id or source_id in states:
            _fail("recorded_layout_report_invalid")
        if not isinstance(state, str) or not state:
            _fail("recorded_layout_report_invalid")
        states[source_id] = state
    return states


def _capture_inputs(
    census: dict[str, Any], evidence: CaptureEvidence
) -> tuple[list[Any], dict[str, Any], dict[str, Any]]:
    capture_results = evidence.manifest.get("results")
    resources = census.get("records")
    recorded = census.get("capture_reconciliation")
    if not isinstance(capture_results, list) or not isinstance(resources, list):
        _fail("capture_manifest_shape_invalid")
    if not isinstance(recorded, dict):
        _fail("capture_reconciliation_record_missing")
    expected_name = recorded.get("capture_manifest")
    if not isinstance(expected_name, str) or not expected_name:
        _fail("capture_manifest_name_missing")
    if Path(evidence.manifest_name).name != expected_name:
        _fail("capture_manifest_name_mismatch")
    if evidence.manifest.get("cutoff") != census.get("cutoff"):
        _fail("capture_manifest_cutoff_mismatch")
    inventory: dict[str, Any] = {}
    for row in resources:
        if not isinstance(row, dict):
            _fail("source_census_row_invalid")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            _fail("source_id_missing_or_duplicate")
        inventory[source_id] = row
    return capture_results, inventory, recorded


def _verify_capture_result(
    result: object,
    inventory: dict[str, Any],
    cas_root: Path,
    capture_ids: set[str],
) -> tuple[str, int, str]:
    if not isinstance(result, dict):
        _fail("capture_result_invalid")
    source_id = result.get("source_id")
    digest = result.get("sha256")
    if (
        not isinstance(source_id, str)
        or not source_id
        or source_id in capture_ids
        or not isinstance(digest, str)
        or len(digest) != _SHA256_HEX_LENGTH
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        _fail("capture_result_identity_or_digest_invalid")
    census_row = inventory.get(source_id)
    if not isinstance(census_row, dict):
        _fail("capture_result_not_in_census")
    rights = result.get("rights")
    if not isinstance(rights, dict):
        _fail("capture_result_rights_missing")
    if (
        result.get("state") != census_row.get("disposition")
        or digest != census_row.get("object_sha256")
        or rights.get("license") != census_row.get("license")
        or rights.get("evidence") != census_row.get("rights_uri")
    ):
        _fail("capture_result_census_mismatch")
    object_path = cas_root / digest[:2] / digest
    try:
        object_bytes = object_path.read_bytes()
    except OSError:
        _fail("capture_object_missing")
    if _sha256(object_bytes) != digest:
        _fail("capture_object_digest_mismatch")
    if result.get("bytes") != len(object_bytes):
        _fail("capture_object_size_mismatch")
    rights_state = rights.get("state")
    return (
        source_id,
        len(object_bytes),
        rights_state if isinstance(rights_state, str) else "not_recorded",
    )


def _verify_capture(
    census: dict[str, Any], evidence: CaptureEvidence | None
) -> tuple[dict[str, Any], dict[str, str]]:
    if evidence is None:
        recorded = census.get("capture_reconciliation", {})
        return (
            {
                "state": "recorded_not_replayed_manifest_unavailable",
                "matched_resource_count_recorded": recorded.get("matched")
                if isinstance(recorded, dict)
                else None,
                "manifest_name_recorded": recorded.get("capture_manifest")
                if isinstance(recorded, dict)
                else None,
            },
            {},
        )
    capture_results, inventory, recorded = _capture_inputs(census, evidence)
    captured_ids = {
        source_id
        for source_id, row in inventory.items()
        if isinstance(row, dict) and row.get("disposition") == "captured"
    }
    capture_ids: set[str] = set()
    rights_states: dict[str, str] = {}
    verified_bytes = 0
    for result in capture_results:
        source_id, object_size, rights_state = _verify_capture_result(
            result, inventory, evidence.cas_root, capture_ids
        )
        capture_ids.add(source_id)
        verified_bytes += object_size
        rights_states[source_id] = rights_state
    if capture_ids != captured_ids:
        _fail("capture_result_inventory_set_mismatch")
    if recorded.get("matched") != len(capture_results):
        _fail("capture_result_count_mismatch")
    return (
        {
            "state": "capture_manifest_and_bronze_objects_verified",
            "manifest_name_recorded": recorded["capture_manifest"],
            "manifest_sha256": _sha256(evidence.manifest_bytes),
            "matched_resource_count_verified": len(capture_results),
            "bronze_object_count_verified": len(capture_results),
            "bronze_bytes_verified": verified_bytes,
            "capture_rights_states_recorded": dict(
                sorted(Counter(rights_states.values()).items())
            ),
        },
        rights_states,
    )


def build_report(  # noqa: PLR0913 - pinned source inputs are explicit
    census: dict[str, Any],
    census_bytes: bytes,
    context: dict[str, Any],
    context_bytes: bytes,
    capture_evidence: CaptureEvidence | None = None,
    *,
    layout_evidence: LayoutEvidence | None = None,
    recorded_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build explicit source and context-vintage states without inferring gaps."""
    return _build_report(
        census,
        census_bytes,
        context,
        context_bytes,
        (capture_evidence, layout_evidence),
        recorded_report,
    )


def _build_report(  # noqa: C901, PLR0912, PLR0913, PLR0917 - explicit pinned inputs
    census: dict[str, Any],
    census_bytes: bytes,
    context: dict[str, Any],
    context_bytes: bytes,
    evidence: tuple[CaptureEvidence | None, LayoutEvidence | None],
    recorded_report: dict[str, Any] | None,
) -> dict[str, Any]:
    capture_evidence, layout_evidence = evidence
    if census.get("schema_version") != SOURCE_CENSUS_VERSION:
        _fail("unsupported_source_census_schema")
    if context.get("schema_version") != CONTEXT_CENSUS_VERSION:
        _fail("unsupported_context_census_schema")
    resources = census.get("records")
    series = context.get("series")
    if not isinstance(resources, list) or census.get("record_count") != len(resources):
        _fail("source_census_record_count_mismatch")
    if not isinstance(series, list) or not series:
        _fail("context_census_series_missing")
    resource_rows = _resource_rows(resources)
    context_rows = _context_rows(series)
    census_sha256 = _sha256(census_bytes)
    if recorded_report is not None:
        recorded_resources = recorded_report.get("resources")
        recorded_capture = recorded_report.get("capture_reconciliation")
        if not isinstance(recorded_resources, list) or not isinstance(
            recorded_capture, dict
        ):
            _fail("recorded_capture_report_invalid")
        if "inputs" in recorded_report:
            recorded_inputs = recorded_report.get("inputs")
            if not isinstance(recorded_inputs, dict):
                _fail("recorded_report_inputs_invalid")
            for key in ("capture_manifest_sha256", "pdf_layout_baseline_sha256"):
                _recorded_input_hash(recorded_report, key)
    compatible_recorded_report = recorded_report
    if recorded_report is not None:
        recorded_inputs = recorded_report.get("inputs")
        if not isinstance(recorded_inputs, dict):
            _fail("recorded_report_inputs_invalid")
        if recorded_inputs.get("source_census_sha256") != census_sha256:
            compatible_recorded_report = None
    layout_states = (
        _layout_states(layout_evidence.report, census) if layout_evidence else {}
    )
    if layout_evidence is None and compatible_recorded_report is not None:
        layout_states = _recorded_layout_states(compatible_recorded_report)
    for row in resource_rows:
        if row["entity_id"] in layout_states:
            row["layout_drift_state"] = layout_states[row["entity_id"]]
    capture_reconciliation, capture_rights_states = _verify_capture(
        census, capture_evidence
    )
    if capture_evidence is None and compatible_recorded_report is not None:
        recorded_capture = compatible_recorded_report.get("capture_reconciliation")
        recorded_resources = compatible_recorded_report.get("resources")
        if not isinstance(recorded_capture, dict) or not isinstance(
            recorded_resources, list
        ):
            _fail("recorded_capture_report_invalid")
        capture_reconciliation = recorded_capture
        capture_rights_states = {
            row["entity_id"]: row["capture_receipt_rights_state"]
            for row in recorded_resources
            if isinstance(row, dict)
            and isinstance(row.get("entity_id"), str)
            and isinstance(row.get("capture_receipt_rights_state"), str)
        }
    for row in resource_rows:
        row["capture_receipt_rights_state"] = capture_rights_states.get(
            row["entity_id"], "not_independently_verified"
        )
    return {
        "schema_version": REPORT_VERSION,
        "scope": "recorded_census_states_not_a_completeness_or_rights_approval",
        "inputs": {
            "source_census_sha256": census_sha256,
            "source_census_cutoff": census.get("cutoff"),
            "source_census_observed_at": census.get("observed_at"),
            "context_census_sha256": _sha256(context_bytes),
            "context_census_base_commit": context.get("base_commit"),
            "capture_manifest_sha256": _sha256(capture_evidence.manifest_bytes)
            if capture_evidence is not None
            else _recorded_input_hash(
                compatible_recorded_report, "capture_manifest_sha256"
            ),
            "pdf_layout_baseline_sha256": _sha256(layout_evidence.report_bytes)
            if layout_evidence is not None
            else _recorded_input_hash(
                compatible_recorded_report, "pdf_layout_baseline_sha256"
            ),
        },
        "summary": {
            "resource_count": len(resource_rows),
            "resource_dispositions": dict(
                sorted(Counter(row["inventory_state"] for row in resource_rows).items())
            ),
            "context_series_vintage_count": len(context_rows),
            "context_qualification_states": dict(
                sorted(
                    Counter(row["qualification_state"] for row in context_rows).items()
                )
            ),
            "context_rights_states": dict(
                sorted(Counter(row["rights"]["state"] for row in context_rows).items())
            ),
        },
        "capture_reconciliation": capture_reconciliation,
        "resources": resource_rows,
        "context_series_vintages": context_rows,
        "limitations": [
            (
                "Resource states and policy references are copied from the pinned "
                "censuses; rights are not approved by this report."
            ),
            (
                "Temporal descriptions are source-census text; calendar completeness "
                "and cross-source period alignment are not assessed."
            ),
            (
                "Structural PDF baselines record page geometry and resources only; "
                "text, tables and semantic layout are not assessed. Other source "
                "families without a supplied baseline remain unassessed."
            ),
            (
                "Capture-manifest rights classifications are retained workflow "
                "evidence, not an independent legal assessment."
            ),
            (
                "This report does not certify discovery, vintage coverage, analytical "
                "comparability, or reconciliation completeness."
            ),
        ],
    }


def _recorded_input_hash(report: dict[str, Any] | None, key: str) -> str | None:
    if report is None:
        return None
    inputs = report.get("inputs")
    if not isinstance(inputs, dict):
        _fail("recorded_report_inputs_invalid")
    value = inputs.get(key)
    if value is not None and (
        not isinstance(value, str)
        or len(value) != _SHA256_HEX_LENGTH
        or any(char not in "0123456789abcdef" for char in value)
    ):
        _fail("recorded_report_input_hash_invalid")
    return value


def render_markdown(report: dict[str, Any]) -> str:
    """Render the machine report as a stable human-readable census roll-up."""
    summary = report["summary"]
    reconciliation = report["capture_reconciliation"]
    matched_count = reconciliation.get(
        "matched_resource_count_verified",
        reconciliation.get("matched_resource_count_recorded"),
    )
    matched_label = (
        "Bronze objects verified"
        if "matched_resource_count_verified" in reconciliation
        else "matched recorded in source census"
    )
    lines = [
        "# Health appropriations source-health and vintage-state report",
        "",
        "This report rolls up the pinned resource and context censuses. It records",
        "states and evidence boundaries; it does not approve rights, infer complete",
        "calendars, or establish that every possible source vintage was discovered.",
        "",
        "## Resource census",
        "",
        f"- Resources: {summary['resource_count']}",
        "- Dispositions: "
        + ", ".join(
            f"`{key}` {value}"
            for key, value in summary["resource_dispositions"].items()
        ),
        "- Capture reconciliation: `"
        + reconciliation["state"]
        + "` ("
        + str(matched_count)
        + " "
        + matched_label
        + ")",
        "",
        (
            "| Source ID | Family | Inventory state | Recorded vintage/title | Rights "
            "state | Capture rights result | Temporal state | Layout state |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in report["resources"]:
        rights = row["rights"]["state"]
        lines.append(
            "| "
            + " | ".join(
                str(value).replace("|", "\\|").replace("\n", " ")
                for value in (
                    row["entity_id"],
                    row["family"],
                    row["inventory_state"],
                    row["target_vintage_label"],
                    rights,
                    row["capture_receipt_rights_state"],
                    row["temporal_coverage_state"],
                    row["layout_drift_state"],
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Context series and vintage states",
            "",
            f"- Context series/vintages: {summary['context_series_vintage_count']}",
            "- Qualification states: "
            + ", ".join(
                f"`{key}` {value}"
                for key, value in summary["context_qualification_states"].items()
            ),
            "",
            (
                "| Series ID | Family | Source series | Vintage | Period description | "
                "Qualification | Rights | Temporal state | Layout state | Known gaps |"
            ),
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    lines.extend(
        "| "
        + " | ".join(
            str(value).replace("|", "\\|").replace("\n", " ")
            for value in (
                row["entity_id"],
                row["family"],
                row["series_id"],
                row["target_vintage_label"],
                row["period_description"],
                row["qualification_state"],
                row["rights"]["state"],
                row["temporal_coverage_state"],
                row["layout_drift_state"],
                "; ".join(row["known_gaps"]),
            )
        )
        + " |"
        for row in report["context_series_vintages"]
    )
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)
