# SPDX-License-Identifier: Apache-2.0
"""Source-specific CSV and HTML baselines from the exact retained Bronze cohort."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations import cpi, moh_indicators, pharmac
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_drift import (
    compare_adapter_drift,
)
from archive_govt_nz.domains.health_appropriations.cpi_adapter import (
    RECORDED_VINTAGE,
    cpi_registration,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    SOURCE_VINTAGE,
)
from archive_govt_nz.domains.health_appropriations.moh_indicator_adapter import (
    SOURCE_SHA256_BY_PROFILE,
)
from archive_govt_nz.domains.health_appropriations.moh_indicator_adapter import (
    registration as moh_registration,
)
from archive_govt_nz.domains.health_appropriations.pharmac_adapter import (
    pharmac_budget_registration,
)
from archive_govt_nz.domains.health_appropriations.schema_drift import (
    compare_fingerprints,
    layout_fingerprint,
    schema_fingerprint,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    import pyarrow as pa

REPORT_SCHEMA = "archive-govt-nz.health-source-text-layout-baseline/v1"


@dataclass(frozen=True, slots=True)
class TextProfile:
    """Reviewed source identity and parser limits, independent of census claims."""

    source_sha256: str
    profile: str
    vintage: str
    media_type: str
    max_bytes: int
    schema: pa.Schema


PROFILES = MappingProxyType(
    {
        "moh_vote_health-008": TextProfile(
            SOURCE_SHA256_BY_PROFILE["fig27/v1"],
            "fig27/v1",
            SOURCE_VINTAGE,
            "text/csv",
            moh_indicators.MAX_BYTES,
            moh_indicators.FACT_SCHEMA,
        ),
        "moh_vote_health-009": TextProfile(
            SOURCE_SHA256_BY_PROFILE["fig28/v1"],
            "fig28/v1",
            SOURCE_VINTAGE,
            "text/csv",
            moh_indicators.MAX_BYTES,
            moh_indicators.FACT_SCHEMA,
        ),
        "stats_nz_cpi-053a0705526fac8d": TextProfile(
            "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
            "cpiq-se9a/v1",
            RECORDED_VINTAGE,
            "text/csv",
            cpi.MAX_BYTES,
            cpi.FACT_SCHEMA,
        ),
        "pharmac_cpb-010": TextProfile(
            "eaf5801b819321f8aed7544fb16e6348779267fd3d5f8fb1d59410803acffbea",
            "pharmac-cpb/v1",
            "Pharmac-CPB-2026-08-07",
            "text/html",
            pharmac.MAX_BYTES,
            pharmac.FACT_SCHEMA,
        ),
    }
)


def _registration(profile: TextProfile, source: dict[str, Any]) -> AdapterRegistration:
    context = {
        "source_locator": source["url"],
        "source_vintage": profile.vintage,
        "observed_at": source["observed_at"],
    }
    if profile.profile.startswith("fig"):
        return moh_registration(profile=profile.profile, **context)
    if profile.media_type == "text/html":
        return pharmac_budget_registration(**context)
    return cpi_registration(**context)


def _check_snapshot(values: Mapping[str, object]) -> None:
    checked: dict[str, str] = {}
    for key, value in values.items():
        if not isinstance(value, str):
            message = "text_layout_report_fingerprint_invalid"
            raise TypeError(message)
        checked[key] = value
    compare_fingerprints(checked, checked)


def _report_rows(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if report.get("schema_version") != REPORT_SCHEMA or not isinstance(
        report.get("text_layouts"), list
    ):
        message = "text_layout_report_invalid"
        raise ValueError(message)
    cohort = {
        key: report.get(key)
        for key in ("source_census_sha256", "capture_manifest_sha256")
    }
    _check_snapshot(cohort)
    indexed = {}
    for row in report["text_layouts"]:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("source_id"), str)
            or row["source_id"] in indexed
        ):
            message = "text_layout_report_identity_invalid"
            raise ValueError(message)
        if row.get("status") == "baseline_recorded":
            if (
                not isinstance(row.get("layout"), dict)
                or layout_fingerprint(row["layout"]) != row.get("layout_sha256")
                or not isinstance(row.get("dispatch_drift"), dict)
            ):
                message = "text_layout_report_fingerprint_invalid"
                raise ValueError(message)
            compare_adapter_drift(row["dispatch_drift"], row["dispatch_drift"])
            declared = {
                "source": row.get("source_object_sha256"),
                "schema": row.get("declared_fact_schema_sha256"),
            }
            _check_snapshot(declared)
        elif (
            row.get("status") != "layout_unavailable"
            or not row.get("unavailable_reason")
            or "layout_sha256" in row
        ):
            message = "text_layout_report_status_invalid"
            raise ValueError(message)
        indexed[row["source_id"]] = row
    return indexed


def compare_text_layout_reports(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    """Report layout/schema/output drift without admitting changed profiles."""
    old, current = _report_rows(before), _report_rows(after)
    rows = []
    for source_id in sorted(old.keys() | current.keys()):
        left, right = old.get(source_id), current.get(source_id)
        if (
            left is None
            or right is None
            or left["status"] != "baseline_recorded"
            or right["status"] != "baseline_recorded"
        ):
            rows.append(
                {
                    "source_id": source_id,
                    "status": "held",
                    "reason": "source_missing_or_unavailable_in_comparison",
                    "baseline_reason": None
                    if left is None
                    else left.get("unavailable_reason"),
                    "current_reason": None
                    if right is None
                    else right.get("unavailable_reason"),
                }
            )
            continue
        structure = compare_fingerprints(
            {
                key: left[key]
                for key in ("layout_sha256", "declared_fact_schema_sha256")
            },
            {
                key: right[key]
                for key in ("layout_sha256", "declared_fact_schema_sha256")
            },
        )
        dispatch = compare_adapter_drift(
            left["dispatch_drift"], right["dispatch_drift"]
        )
        matching = (
            structure["status"] == dispatch["status"] == "matching"
            and dispatch["ordered_output_identical"]
        )
        rows.append(
            {
                "source_id": source_id,
                "status": "matching" if matching else "drift",
                "structure": structure,
                "dispatch": dispatch,
            }
        )
    cohort_changed = any(
        before.get(key) != after.get(key)
        for key in ("source_census_sha256", "capture_manifest_sha256")
    )
    return {
        "schema_version": "archive-govt-nz.health-source-text-layout-drift/v1",
        "baseline_canonical_sha256": hashlib.sha256(
            json.dumps(before, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "current_canonical_sha256": hashlib.sha256(
            json.dumps(after, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "status": "held"
        if not rows or cohort_changed or any(row["status"] == "held" for row in rows)
        else "matching"
        if all(row["status"] == "matching" for row in rows)
        else "drift",
        "cohort_changed": cohort_changed,
        "sources": rows,
        "normalization_approval": "not_granted",
    }


def text_layout_descriptor(payload: bytes, profile: TextProfile) -> dict[str, object]:
    """Describe only the reviewed CSV grid or CPB table/context structure."""
    if not 0 < len(payload) <= profile.max_bytes:
        message = "text_layout_source_byte_limit"
        raise ValueError(message)
    if profile.media_type == "text/html":
        parser = pharmac._parse(payload)  # noqa: SLF001 - reuse the reviewed bounded table parser.
        return {
            "profile": profile.profile,
            "scope": "reviewed_cpb_table_and_required_context_not_whole_dom",
            "header_cells": parser.rows[0],
            "row_spans": [[span for _, span in row] for row in parser.rows],
            "required_context_sha256": [
                hashlib.sha256(value.encode()).hexdigest() for value in pharmac.CONTEXT
            ],
        }
    rows = [
        next(csv.reader([line], strict=True))
        for line in payload.decode("utf-8-sig", errors="strict").splitlines()
    ]
    if not rows:
        message = "text_layout_csv_empty"
        raise ValueError(message)
    widths = Counter(len(row) for row in rows[1:])
    return {
        "profile": profile.profile,
        "scope": "reviewed_physical_line_csv_grid",
        "headers": rows[0],
        "data_row_count": len(rows) - 1,
        "data_row_width_counts": [
            [width, count] for width, count in sorted(widths.items())
        ],
    }


def _unavailable(source: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "source_object_sha256": source.get("object_sha256"),
        "media_type": source["media_type"],
        "status": "layout_unavailable",
        "unavailable_reason": reason,
    }


def _baseline_row(  # noqa: PLR0911 - retain explicit source refusal dispositions.
    source: dict[str, Any], capture: dict[str, Any], cas_root: Path
) -> dict[str, Any]:
    profile = PROFILES.get(source["source_id"])
    if profile is None:
        return _unavailable(source, "source_specific_text_profile_not_registered")
    digest = source["object_sha256"]
    if digest != profile.source_sha256 or source["media_type"] != profile.media_type:
        return _unavailable(source, "source_profile_identity_not_qualified")
    path = cas_root / digest[:2] / digest
    try:
        if not 0 < path.stat().st_size <= profile.max_bytes:
            return _unavailable(source, "text_layout_source_byte_limit")
        payload = path.read_bytes()
    except OSError:
        return _unavailable(source, "bronze_object_unavailable")
    if (
        hashlib.sha256(payload).hexdigest() != digest
        or len(payload) != capture["bytes"]
    ):
        return _unavailable(source, "bronze_object_fixity_mismatch")
    result = dispatch_bronze(
        payload,
        source_sha256=digest,
        media_type=profile.media_type,
        registrations=(_registration(profile, source),),
    )
    if result.selection.status != "selected" or result.output.layout == "unknown":
        return _unavailable(
            source, result.selection.reason or "source_specific_parser_refused"
        ) | {"dispatch_drift": result.to_drift_receipt()}
    descriptor = text_layout_descriptor(payload, profile)
    return {
        "source_id": source["source_id"],
        "source_object_sha256": digest,
        "media_type": profile.media_type,
        "source_bytes": len(payload),
        "profile": profile.profile,
        "status": "baseline_recorded",
        "layout": descriptor,
        "layout_sha256": layout_fingerprint(descriptor),
        "declared_fact_schema_sha256": schema_fingerprint(profile.schema),
        "dispatch_drift": result.to_drift_receipt(),
    }


def build_text_layout_baseline_report(
    census_bytes: bytes, capture_bytes: bytes, cas_root: Path
) -> dict[str, Any]:
    """Reconcile and inspect captured CSV/HTML only; unavailable sources stay held."""
    census, capture = json.loads(census_bytes), json.loads(capture_bytes)
    if (
        census.get("schema_version") != "archive-govt-nz.health-source-census/v1"
        or census.get("cutoff") != capture.get("cutoff")
        or not isinstance(census.get("records"), list)
        or not isinstance(capture.get("results"), list)
    ):
        message = "text_layout_cohort_invalid"
        raise ValueError(message)
    sources = [
        row
        for row in census["records"]
        if row.get("disposition") == "captured"
        and row.get("media_type") in {"text/csv", "text/html"}
    ]
    captures = [row for row in capture["results"] if row.get("state") == "captured"]
    by_id = {row["source_id"]: row for row in captures}
    if len(by_id) != len(captures) or len({row["source_id"] for row in sources}) != len(
        sources
    ):
        message = "text_layout_source_identity_duplicate"
        raise ValueError(message)
    layouts = []
    for source in sorted(sources, key=lambda row: row["source_id"]):
        retained = by_id.get(source["source_id"])
        if (
            retained is None
            or retained.get("sha256") != source.get("object_sha256")
            or type(retained.get("bytes")) is not int
        ):
            message = "text_layout_capture_identity_mismatch"
            raise ValueError(message)
        layouts.append(_baseline_row(source, retained, cas_root))
    return {
        "schema_version": REPORT_SCHEMA,
        "source_census_sha256": hashlib.sha256(census_bytes).hexdigest(),
        "capture_manifest_sha256": hashlib.sha256(capture_bytes).hexdigest(),
        "text_layouts": layouts,
        "summary": {
            "captured_text_source_count": len(layouts),
            "baseline_recorded_count": sum(
                row["status"] == "baseline_recorded" for row in layouts
            ),
            "layout_unavailable_count": sum(
                row["status"] == "layout_unavailable" for row in layouts
            ),
        },
        "normalization_approval": "not_granted",
        "limitations": [
            (
                "Profiles bind exact captured objects; changed objects require "
                "explicit qualification."
            ),
            (
                "CSV grids and the reviewed CPB table/context do not establish "
                "semantics, rights or whole-document HTML coverage."
            ),
            (
                "Observed dictionary field types are not trusted Arrow declarations; "
                "only declared native schemas receive Arrow fingerprints."
            ),
        ],
    }
