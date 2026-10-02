"""Verified source-specific Gold coverage for contextual time series.

This product preserves declared source packages, vintages, periods and status
limits. It performs no joins, deflation, annualization or denominator selection.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import suppress
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.canonical_gold_plots import (
    build_context_plots,
)
from archive_govt_nz.domains.health_appropriations.price_wage_context import (
    _PROFILES as PRICE_WAGE_PROFILES,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_ROWS = 25_000
_ERROR = "context_gold_invalid"
_DIGEST_LENGTH = 64
_EXPECTED_SOURCES = {
    "cpi": (
        "CPIQ.SE9A",
        "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
    ),
    "wage": (
        "QEMQ.SASZ9A",
        "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97",
    ),
    "gdp": (
        "SNEQ/SG03AB01GE00S900",
        "a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21",
    ),
    "population": (
        "DPE056AA:Mean year ended:Total:Total All Ages:Annual-Jun",
        "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9",
    ),
}
_EXPECTED_VINTAGES = {
    "cpi": "Stats-NZ-CPI-2026-Q2",
    "wage": "QES-2026-Q2",
    "gdp": "StatsNZ-GDP-2026Q1",
    "population": "2026-08-18",
}
_EXPECTED_MANIFESTS = {
    "cpi": "edb62f4b106948502e717f5f6c5e3da00efc0a64bb10b5dcbafc48cd1a6c257e",
    "wage": "0bf89bd6c10a0458ef4c578b209c3252292961976d2f50b3c27fe92907c3cb04",
    "gdp": "639b3c7da60f2afa1b860c5f6c8f1c4c0ae24bf17aa7af63bf8a06a1f6471b35",
    "population": "067255c4ac18377312d0a8234dc94804c876ba68866cfba3a483a4dd89415798",
    "gdp_june": "f54b0ad605b54e480cd0623360159b3ce14b6a9f762185d5244dec89837ffbfd",
}
_EXPECTED_PROFILE_SOURCES = {
    "cpi": (
        "raw-cpi-20260831-v1",
        "cpi_facts.parquet",
        "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
        "cpi",
        "CPIQ.SE9A",
    ),
    "wage": (
        "raw-qes-2026q2-20260831-v3",
        "qes_facts.parquet",
        "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97",
        "wage",
        "QEMQ.SASZ9A",
    ),
    "gdp": (
        "raw-stats-gdp-20260831-v1",
        "gdp_facts.parquet",
        "a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21",
        "gdp",
        "SNEQ/SG03AB01GE00S900",
    ),
    "gdp_june": (
        "gdp-june-1",
        "gdp_facts.parquet",
        "b6d2fe15b4656143f600abeb1849432f60d769570667eb90d07ddacd3498e22d",
        "gdp",
        "SNEQ/SG03AB01GE00S900",
    ),
    "population": (
        "population-annual-mean-context-20260925-v1",
        "population_facts.parquet",
        "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9",
        "population",
        "DPE056AA:Mean year ended:Total:Total All Ages:Annual-Jun",
    ),
}
_EXPECTED_SOURCE_IDENTITIES = {
    ("cpi", _EXPECTED_SOURCES["cpi"][1]): (
        _EXPECTED_SOURCES["cpi"][0],
        _EXPECTED_VINTAGES["cpi"],
    ),
    ("wage", _EXPECTED_SOURCES["wage"][1]): (
        _EXPECTED_SOURCES["wage"][0],
        _EXPECTED_VINTAGES["wage"],
    ),
    ("gdp", _EXPECTED_SOURCES["gdp"][1]): (
        _EXPECTED_SOURCES["gdp"][0],
        _EXPECTED_VINTAGES["gdp"],
    ),
    ("gdp", "b6d2fe15b4656143f600abeb1849432f60d769570667eb90d07ddacd3498e22d"): (
        "SNEQ/SG03AB01GE00S900",
        "StatsNZ-GDP-2026Q2",
    ),
    ("population", _EXPECTED_SOURCES["population"][1]): (
        _EXPECTED_SOURCES["population"][0],
        _EXPECTED_VINTAGES["population"],
    ),
}
_EXPECTED_PACKAGE_COUNT = len(_EXPECTED_PROFILE_SOURCES)
SCHEMA = "archive-govt-nz.health-context-gold/v1"
OBSERVATION_SCHEMA = pa.schema(
    [
        ("family", pa.string(), False),
        ("series_id", pa.string(), False),
        ("source_vintage", pa.string(), False),
        ("source_sha256", pa.string(), False),
        ("source_locator", pa.string(), False),
        ("period_token", pa.string(), False),
        ("period_end", pa.string(), True),
        ("value", pa.decimal128(38, 18), True),
        ("value_token", pa.string(), False),
        ("unit", pa.string(), True),
        ("basis", pa.string(), True),
        ("status", pa.string(), True),
        ("input_record_id", pa.string(), False),
        ("admission", pa.string(), False),
        ("admission_reason", pa.string(), False),
    ],
    metadata={
        b"schema_version": SCHEMA.encode(),
        b"query": b"context_observation_coverage",
    },
)
COVERAGE_SCHEMA = pa.schema(
    [
        ("family", pa.string(), False),
        ("series_id", pa.string(), False),
        ("source_vintage", pa.string(), False),
        ("source_sha256", pa.string(), False),
        ("source_locator", pa.string(), False),
        ("unit", pa.string(), True),
        ("basis", pa.string(), True),
        ("first_period", pa.string(), False),
        ("last_period", pa.string(), False),
        ("observation_count", pa.int64(), False),
        ("eligible_count", pa.int64(), False),
        ("excluded_count", pa.int64(), False),
        ("input_record_ids", pa.list_(pa.field("element", pa.string())), False),
        ("period_policy", pa.string(), False),
        ("measure_policy", pa.string(), False),
    ],
    metadata={
        b"schema_version": SCHEMA.encode(),
        b"query": b"context_coverage_by_exact_source_series",
    },
)

QUALITY_SCHEMA = pa.schema(
    [
        ("family", pa.string(), False),
        ("series_id", pa.string(), False),
        ("source_vintage", pa.string(), False),
        ("source_sha256", pa.string(), False),
        ("source_locator", pa.string(), False),
        ("observation_count", pa.int64(), False),
        ("eligible_count", pa.int64(), False),
        ("excluded_count", pa.int64(), False),
        ("exclusion_reasons_json", pa.string(), False),
        ("period_tokens_json", pa.string(), False),
        ("period_continuity", pa.string(), False),
        ("rights_state", pa.string(), False),
        ("denominator_selection", pa.string(), False),
    ],
    metadata={
        b"schema_version": SCHEMA.encode(),
        b"query": b"exact_source_series_status_and_period_quality",
    },
)


def _require(value: object) -> None:
    if not value:
        raise ValueError(_ERROR)


def _json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _table(table: pa.Table) -> bytes:
    buffer = BytesIO()
    pq.write_table(
        table, buffer, compression="zstd", use_dictionary=False, version="2.6"
    )
    return buffer.getvalue()


def _source_path(root: Path, digest: str) -> Path:
    path = root / digest[:2] / digest
    _require(path.is_file() and not path.is_symlink())
    with path.open("rb") as source:
        _require(hashlib.file_digest(source, "sha256").hexdigest() == digest)
    return path


def _lineage(path: Path, manifest: dict[str, Any], name: str) -> dict[str, set[str]]:
    entry = manifest["output_sha256"].get(name)
    _require(type(entry) is str and len(entry) == _DIGEST_LENGTH)
    payload = verified_snapshot(path, entry, max_bytes=MAX_SOURCE_BYTES)
    table = pq.read_table(BytesIO(payload))
    _require(table.num_rows <= MAX_ROWS)
    result: dict[str, set[str]] = {}
    for row in table.to_pylist():
        result.setdefault(str(row["record_id"]), set()).add(str(row["field"]))
    return result


def _fact_package(  # noqa: C901, PLR0912, PLR0913, PLR0915 - one fail-closed package boundary
    silver_root: Path,
    *,
    package: str,
    facts_file: str,
    source_digest: str,
    family: str,
    series_id: str,
    source_root: Path,
) -> tuple[list[dict[str, Any]], str]:
    root = silver_root / package
    _require(root.is_dir() and not root.is_symlink())
    manifest_path = root / "MANIFEST.json"
    _require(manifest_path.is_file() and not manifest_path.is_symlink())
    manifest_bytes = manifest_path.read_bytes()
    _require(len(manifest_bytes) <= MAX_SOURCE_BYTES)
    manifest = json.loads(manifest_bytes)
    _require(manifest["source_object_sha256"] == source_digest)
    _require(manifest["rights_state"] == "not_evaluated")
    source_path = _source_path(source_root, source_digest)
    _require(source_path.stat().st_size <= MAX_SOURCE_BYTES)
    facts_bytes = verified_snapshot(
        root / facts_file,
        manifest["output_sha256"][facts_file],
        max_bytes=MAX_SOURCE_BYTES,
    )
    facts = pq.read_table(BytesIO(facts_bytes)).to_pylist()
    _require(0 < len(facts) <= MAX_ROWS)
    lineage = _lineage(
        root / "field_lineage.parquet", manifest, "field_lineage.parquet"
    )
    seen: set[str] = set()
    result = []
    for fact in facts:
        record_id = fact["record_id"]
        _require(type(record_id) is str and record_id not in seen)
        seen.add(record_id)
        _require(fact["source_object_sha256"] == source_digest)
        _require(fact["source_vintage"] == manifest["source_vintage"])
        _validate_fact_lineage(record_id, lineage)
        amount = fact.get("amount")
        _require(amount is None or isinstance(amount, Decimal))
        status = fact.get("raw_status", fact.get("status"))
        value_token = fact.get("value_token", fact.get("source_number_token"))
        if value_token is None:
            value_token = str(amount) if amount is not None else ""
        if family == "population" and status in {"P", "E", "C", "S"}:
            reason = {
                "P": "provisional",
                "E": "early_estimate",
                "C": "confidential",
                "S": "suppressed",
            }[status]
        elif amount is None:
            reason = str(
                fact.get("null_reason") or fact.get("missing_reason") or "missing_value"
            )
        elif family == "cpi":
            reason = "source_value_admitted_base_unverified"
        elif family == "gdp" and (
            fact.get("currency") is None or fact.get("denominator_not_selected")
        ):
            reason = "source_value_admitted_currency_unqualified"
        elif family == "wage":
            reason = "source_value_admitted_context_measure"
        else:
            reason = "source_value_admitted"
        eligible = (
            reason
            in {
                "source_value_admitted",
                "source_value_admitted_base_unverified",
                "source_value_admitted_context_measure",
                "source_value_admitted_currency_unqualified",
            }
            and amount is not None
        )
        period_token = fact.get("period_token")
        if period_token is None:
            period_token = fact.get("source_quarter_token") or fact.get(
                "source_year_token"
            )
        if period_token is None:
            period_token = fact.get("valid_time_end")
        _require(period_token is not None)
        if family == "population":
            raw_values = json.loads(fact.get("raw_values_json") or "{}")
            status = str(raw_values.get("status") or "") or None
            if amount is None:
                reason = str(fact.get("null_reason") or "missing_value")
            elif status in {"P", "E", "C", "S"}:
                reason = {
                    "P": "provisional",
                    "E": "early_estimate",
                    "C": "confidential",
                    "S": "suppressed",
                }[status]
            elif fact["period_token"] in {"FY2025", "FY2026"}:
                reason = "status_not_retained_in_shared_fact"
            else:
                reason = "source_value_admitted"
            eligible = reason == "source_value_admitted"
        result.append(
            {
                "family": family,
                "series_id": series_id,
                "source_vintage": manifest["source_vintage"],
                "source_sha256": source_digest,
                "source_locator": fact["source_locator"],
                "period_token": str(period_token),
                "period_end": str(
                    fact.get("period_end") or fact.get("valid_time_end") or ""
                )
                or None,
                "value": amount,
                "value_token": str(value_token),
                "unit": fact.get("unit")
                or fact.get("unit_label")
                or fact.get("scaling"),
                "basis": fact.get("index_base")
                or fact.get("price_basis")
                or fact.get("unit_basis")
                or fact.get("population_definition"),
                "status": status,
                "input_record_id": record_id,
                "admission": "eligible_context_only"
                if eligible
                else "excluded_from_numeric_series",
                "admission_reason": reason,
            }
        )
    return result, hashlib.sha256(manifest_bytes).hexdigest()


def _validate_fact_lineage(record_id: str, lineage: dict[str, set[str]]) -> None:
    fields = lineage.get(record_id, set())
    _require("amount" in fields)
    _require(bool({"period_token", "period_end", "source_year_token"} & fields))


def _source_native_packages(
    silver_root: Path, source_root: Path
) -> tuple[list[dict[str, Any]], list[str]]:
    output: list[dict[str, Any]] = []
    marker_digests: list[str] = []
    for profile_id, (
        package,
        filename,
        digest,
        family,
        series,
    ) in _EXPECTED_PROFILE_SOURCES.items():
        facts, _marker_digest = _fact_package(
            silver_root,
            package=package,
            facts_file=filename,
            source_digest=digest,
            family=family,
            series_id=series,
            source_root=source_root,
        )
        _require(_marker_digest == _EXPECTED_MANIFESTS[profile_id])
        marker_digests.append(_marker_digest)
        if family == "cpi":
            profile = PRICE_WAGE_PROFILES["cpi"]
            for row in facts:
                row["basis"] = f"{profile[8]}={profile[9]};unit={profile[7]}"
                row["admission"] = (
                    "eligible_context_only"
                    if row["admission_reason"]
                    == "source_value_admitted_base_unverified"
                    and row["status"] == "FINAL"
                    else "excluded_from_numeric_series"
                )
                if (
                    row["status"] != "FINAL"
                    and row["admission_reason"]
                    == "source_value_admitted_base_unverified"
                ):
                    row["admission_reason"] = "non_final_source_status"
        elif family == "wage":
            for row in facts:
                row["admission"] = (
                    "eligible_context_only"
                    if row["admission_reason"]
                    == "source_value_admitted_context_measure"
                    and row["value"] is not None
                    else "excluded_from_numeric_series"
                )
        elif family == "gdp":
            for row in facts:
                row["basis"] = "current_prices;actual_as_published;quarterly"
                row["admission"] = (
                    "eligible_context_only"
                    if row["admission_reason"]
                    == "source_value_admitted_currency_unqualified"
                    and row["value"] is not None
                    else "excluded_from_numeric_series"
                )
        output.extend(facts)
    return output, marker_digests


def _coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["family"],
            row["series_id"],
            row["source_vintage"],
            row["source_sha256"],
            row["source_locator"],
            row["unit"],
            row["basis"],
        )
        groups.setdefault(key, []).append(row)
    output = []
    for key, members in sorted(
        groups.items(), key=lambda item: tuple(str(value) for value in item[0])
    ):
        periods = sorted({row["period_token"] for row in members})
        output.append(
            dict(
                zip(
                    (
                        "family",
                        "series_id",
                        "source_vintage",
                        "source_sha256",
                        "source_locator",
                        "unit",
                        "basis",
                    ),
                    key,
                    strict=True,
                )
            )
            | {
                "first_period": periods[0],
                "last_period": periods[-1],
                "observation_count": len(members),
                "eligible_count": sum(
                    row["admission"] == "eligible_context_only" for row in members
                ),
                "excluded_count": sum(
                    row["admission"] != "eligible_context_only" for row in members
                ),
                "input_record_ids": sorted(row["input_record_id"] for row in members),
                "period_policy": (
                    "source_tokens_sorted_lexically_without_cross_series_alignment"
                ),
                "measure_policy": (
                    "source_literal_context_only_no_deflation_annualization_"
                    "or_denominator_join"
                ),
            }
        )
    return output


def _quality(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize exact source-series status and observed period tokens only."""
    grouped: dict[tuple[object, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(
            row[field]
            for field in (
                "family",
                "series_id",
                "source_vintage",
                "source_sha256",
                "source_locator",
            )
        )
        grouped.setdefault(key, []).append(row)
    output = []
    for key, members in sorted(grouped.items(), key=lambda item: item[0]):
        reasons: dict[str, int] = {}
        for row in members:
            if row["admission"] != "eligible_context_only":
                reason = row["admission_reason"]
                reasons[reason] = reasons.get(reason, 0) + 1
        output.append(
            {
                **dict(
                    zip(
                        (
                            "family",
                            "series_id",
                            "source_vintage",
                            "source_sha256",
                            "source_locator",
                        ),
                        key,
                        strict=True,
                    )
                ),
                "observation_count": len(members),
                "eligible_count": sum(
                    row["admission"] == "eligible_context_only" for row in members
                ),
                "excluded_count": sum(
                    row["admission"] != "eligible_context_only" for row in members
                ),
                "exclusion_reasons_json": _json(dict(sorted(reasons.items()))).decode(),
                "period_tokens_json": _json(
                    sorted({row["period_token"] for row in members})
                ).decode(),
                "period_continuity": "not_assessed_source_calendar_not_supplied",
                "rights_state": "not_evaluated",
                "denominator_selection": "not_performed",
            }
        )
    return output


def _quality_markdown(rows: list[dict[str, Any]]) -> bytes:
    """Render exact source-series quality counts without inferring gaps."""
    lines = [
        "# Health Appropriations contextual Gold quality report",
        "",
        "This report describes five explicitly pinned, source-separated Silver",
        "series, including separate March and June 2026 GDP vintages. Period",
        "tokens are reported as observed; chronology, continuity,",
        "and missing-period inference are not assessed.",
        "",
        "| Family | Series | Vintage | Observations | Eligible | Excluded |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in sorted(rows, key=lambda item: (item["family"], item["series_id"])):
        table_row = (
            "| {family} | {series} | {vintage} | {observations} | "
            "{eligible} | {excluded} |"
        ).format(
            family=row["family"],
            series=row["series_id"].replace("|", "\\|"),
            vintage=row["source_vintage"].replace("|", "\\|"),
            observations=row["observation_count"],
            eligible=row["eligible_count"],
            excluded=row["excluded_count"],
        )
        lines.append(table_row)
        exclusions = json.loads(row["exclusion_reasons_json"])
        tokens = json.loads(row["period_tokens_json"])
        lines.extend(
            [
                "",
                f"### {row['family']} — {row['source_vintage']}",
                "",
                f"Observed period tokens: {len(tokens)} distinct.",
                "Exclusion reasons: "
                + (
                    ", ".join(f"`{key}` ({value})" for key, value in exclusions.items())
                    if exclusions
                    else "none recorded"
                ),
            ]
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Period continuity: not assessed; source calendars were not supplied.",
            "- Cross-source joins and denominator selection: not performed.",
            "- Rights: not evaluated.",
            "- Publication: not performed.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _validate_rows(rows: list[dict[str, Any]]) -> None:
    _require(0 < len(rows) <= MAX_ROWS)
    ids = [row["input_record_id"] for row in rows]
    _require(len(ids) == len(set(ids)))
    source_ids_by_package: dict[str, set[str]] = {}
    for row in rows:
        expected = _EXPECTED_SOURCE_IDENTITIES.get(
            (row["family"], row["source_sha256"])
        )
        _require(expected is not None)
        _require((row["series_id"], row["source_vintage"]) == expected)
        _require(re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"]) is not None)
        _require(
            row["admission"]
            in {"eligible_context_only", "excluded_from_numeric_series"}
        )
        _require(
            row["admission"] != "eligible_context_only" or row["value"] is not None
        )
        source_ids_by_package.setdefault(row["source_sha256"], set()).add(
            row["input_record_id"]
        )
        _require(row["source_sha256"] in source_ids_by_package)
        if row["family"] == "population" and row["status"] in {"P", "E", "C", "S"}:
            _require(row["admission"] == "excluded_from_numeric_series")
            _require(
                row["admission_reason"]
                in {"provisional", "early_estimate", "confidential", "suppressed"}
            )
        _require(
            row["admission"] == "eligible_context_only"
            or row["admission_reason"] != "source_value_admitted"
        )


def _export(
    silver_root: Path, source_root: Path, output: Path, *, write: bool
) -> dict[str, Any]:
    _require(type(write) is bool and silver_root.is_dir() and source_root.is_dir())
    _require(not silver_root.is_symlink() and not source_root.is_symlink())
    _require(
        output.parent.is_dir()
        and not output.parent.is_symlink()
        and not output.exists()
        and not output.is_symlink()
    )
    target = output.resolve()
    for protected in (silver_root.resolve(), source_root.resolve()):
        _require(
            not target.is_relative_to(protected)
            and not protected.is_relative_to(target)
        )
    rows, marker_digests = _source_native_packages(silver_root, source_root)
    _validate_rows(rows)
    _require(len(marker_digests) == _EXPECTED_PACKAGE_COUNT)
    observations = pa.Table.from_pylist(rows, schema=OBSERVATION_SCHEMA)
    coverage_rows = _coverage(rows)
    quality_rows = _quality(rows)
    coverage = pa.Table.from_pylist(coverage_rows, schema=COVERAGE_SCHEMA)
    quality = pa.Table.from_pylist(quality_rows, schema=QUALITY_SCHEMA)
    plot_payloads, plot_report = build_context_plots(rows)
    payloads = {
        "context_observations.parquet": _table(observations),
        "context_coverage.parquet": _table(coverage),
        "context_quality.parquet": _table(quality),
        "context-quality-report.md": _quality_markdown(quality_rows),
        **plot_payloads,
    }
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES)
    outputs = {
        name: {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "rows": (
                observations.num_rows
                if name == "context_observations.parquet"
                else coverage.num_rows
                if name == "context_coverage.parquet"
                else quality.num_rows
                if name == "context_quality.parquet"
                else 0
            ),
        }
        for name, payload in sorted(payloads.items())
    }
    receipt = {
        "schema_version": SCHEMA,
        "status": "complete" if write else "dry_run",
        "products": outputs,
        "input_records": len(rows),
        "series": len(coverage.to_pylist()),
        "source_quality": {
            "status_counts_from_retained_silver": "complete",
            "period_continuity": "not_assessed_source_calendar_not_supplied",
            "rights": "not_evaluated",
            "denominator_selection": "not_performed",
            "report_rows": quality.num_rows,
        },
        "plot_report": plot_report,
        "eligible_context_observations": sum(
            row["admission"] == "eligible_context_only" for row in rows
        ),
        "excluded_observations": sum(
            row["admission"] != "eligible_context_only" for row in rows
        ),
        "source_marker_sha256": sorted(marker_digests),
        "source_family_policy": "separate_series_vintages_no_joins_or_pooling",
        "rights_state": "not_evaluated",
        "denominator_selection": "not_performed",
        "publication": "not_performed",
    }
    marker = _json(receipt)
    _require(sum(map(len, payloads.values())) + len(marker) <= MAX_OUTPUT_BYTES)
    if not write:
        return receipt | {"planned_outputs": outputs}
    output.mkdir()
    try:
        for name, payload in payloads.items():
            with (output / name).open("xb") as handle:
                _require(handle.write(payload) == len(payload))
            _require((output / name).read_bytes() == payload)
            if name.endswith(".parquet"):
                restored = pq.read_table(output / name)
                expected = (
                    observations
                    if name == "context_observations.parquet"
                    else coverage
                    if name == "context_coverage.parquet"
                    else quality
                )
                _require(restored.equals(expected, check_metadata=True))
        with (output / "MANIFEST.json").open("xb") as handle:
            _require(handle.write(marker) == len(marker))
        _require((output / "MANIFEST.json").read_bytes() == marker)
        _require(
            {path.name for path in output.iterdir()} == {*payloads, "MANIFEST.json"}
        )
    except (OSError, ValueError, TypeError, pa.ArrowException) as error:
        with suppress(OSError, ValueError, TypeError):
            (output / "FAILURE.json").write_bytes(
                _json(
                    {
                        "schema_version": SCHEMA,
                        "status": "incomplete",
                        "error_type": type(error).__name__,
                        "publication": "not_performed",
                    }
                )
            )
        raise
    return receipt


def export_context_gold(
    silver_root: Path, source_root: Path, output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build verified, source-separated contextual observations and coverage."""
    try:
        return _export(silver_root, source_root, output, write=write)
    except OSError, ValueError, TypeError, KeyError, AttributeError, pa.ArrowException:
        raise ValueError(_ERROR) from None
