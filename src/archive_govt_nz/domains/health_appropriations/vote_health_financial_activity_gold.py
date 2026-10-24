# SPDX-License-Identifier: Apache-2.0
"""A pinned, source-separated Gold projection of Vote Health activity."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2014_15_financial_activity as silver_profile,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.vote-health-financial-activity-gold/v1"
QUERY_VERSION = "archive-govt-nz.vote-health-financial-activity-gold-query/v1"
MAX_BYTES = 16 * 1024 * 1024
_FACT_ROWS = 14
_LINEAGE_ROWS = _FACT_ROWS * len(silver_profile.COLUMNS)
_SOURCE_PAGE = 7
_HASH_LENGTH = 64
_MAX_PARQUET_ROWS = _LINEAGE_ROWS
MAX_ROWS = _FACT_ROWS
SILVER_FACTS = "vote_health_financial_activity_facts.parquet"
SILVER_LINEAGE = "field_lineage.parquet"
FACT_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("source_silver_manifest_sha256", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_vintage", pa.string()),
        ("source_page", pa.int64()),
        ("source_row_ordinal", pa.int64()),
        ("section", pa.string()),
        ("source_label", pa.string()),
        *((name, pa.decimal128(20, 3)) for name in silver_profile.COLUMNS),
        ("unit", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
LINEAGE_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("field", pa.string()),
        ("source_silver_manifest_sha256", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_coordinate", pa.string()),
        ("raw_value", pa.string()),
        ("normalized_value", pa.string()),
        ("rule", pa.string()),
    ]
)
_FACT_PAYLOAD = "financial_activity.parquet"
_LINEAGE_PAYLOAD = "financial_activity_lineage.parquet"
_SUMMARY_PAYLOAD = "summary.json"
_README_PAYLOAD = "README.md"
_PAYLOADS = frozenset(
    {_FACT_PAYLOAD, _LINEAGE_PAYLOAD, _SUMMARY_PAYLOAD, _README_PAYLOAD}
)


def _require(condition: object) -> None:
    if not condition:
        message = "vote_health_financial_activity_gold_invalid"
        raise ValueError(message)


def _raw_amount(token: str) -> Decimal | None:
    if token in {"-", "N/A"}:
        return None
    amount = Decimal(token.replace(",", "").strip("()"))
    return -amount if token.startswith("(") else amount


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _table_bytes(table: pa.Table) -> bytes:
    output = BytesIO()
    pq.write_table(
        table,
        output,
        compression="zstd",
        use_dictionary=False,
        version="2.6",
    )
    return output.getvalue()


def _parquet_schema_matches(actual: pa.Schema, expected: pa.Schema) -> bool:
    """Compare schemas while normalizing Parquet's standard list child label."""
    if actual.names != expected.names or len(actual) != len(expected):
        return False
    for actual_field, expected_field in zip(actual, expected, strict=True):
        actual_type, expected_type = actual_field.type, expected_field.type
        if pa.types.is_list(actual_type) and pa.types.is_list(expected_type):
            if actual_type.value_type != expected_type.value_type:
                return False
        elif actual_type != expected_type:
            return False
        if actual_field.nullable != expected_field.nullable:
            return False
        if actual_field.metadata != expected_field.metadata:
            return False
    return actual.metadata == expected.metadata


def _silver_tables(
    package_dir: Path, manifest_sha256: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require(package_dir.is_dir() and not package_dir.is_symlink())
    manifest_path = package_dir / "MANIFEST.json"
    _require(not manifest_path.is_symlink())
    manifest_bytes = verified_snapshot(
        manifest_path, manifest_sha256, max_bytes=MAX_BYTES
    )
    manifest = json.loads(manifest_bytes)
    _require(
        isinstance(manifest, dict)
        and set(manifest)
        == {
            "schema_version",
            "status",
            "profile",
            "source_object_sha256",
            "counts",
            "output_sha256",
        }
        and manifest.get("schema_version")
        == "archive-govt-nz.vote-health-financial-activity-extraction/v1"
        and manifest.get("status") == "passed"
        and manifest.get("profile") == silver_profile.PROFILE
        and manifest.get("source_object_sha256") == silver_profile.SOURCE_SHA256
        and manifest.get("counts")
        == {"pages": 1, "facts": _FACT_ROWS, "lineage": _LINEAGE_ROWS}
        and set(manifest.get("output_sha256", {}))
        == {SILVER_FACTS, SILVER_LINEAGE, "page_dispositions.parquet"}
    )
    _require(
        {path.name for path in islice(package_dir.iterdir(), 5)}
        == {SILVER_FACTS, SILVER_LINEAGE, "page_dispositions.parquet", "MANIFEST.json"}
    )
    tables: dict[str, list[dict[str, Any]]] = {}
    expected_schemas = {
        SILVER_FACTS: silver_profile.FACT_SCHEMA,
        SILVER_LINEAGE: silver_profile.LINEAGE_SCHEMA,
        "page_dispositions.parquet": silver_profile.PAGE_SCHEMA,
    }
    for name, schema in expected_schemas.items():
        path = package_dir / name
        _require(not path.is_symlink())
        payload = verified_snapshot(
            path, manifest["output_sha256"][name], max_bytes=MAX_BYTES
        )
        with pq.ParquetFile(
            BytesIO(payload),
            thrift_string_size_limit=MAX_BYTES,
            thrift_container_size_limit=100_000,
        ) as parquet:
            _require(_parquet_schema_matches(parquet.schema_arrow, schema))
            _require(parquet.metadata.num_rows <= _MAX_PARQUET_ROWS)
            tables[name] = parquet.read(use_threads=False).to_pylist()
    facts = tables[SILVER_FACTS]
    lineage = tables[SILVER_LINEAGE]
    pages = tables["page_dispositions.parquet"]
    _require(len(facts) == _FACT_ROWS and len(lineage) == _LINEAGE_ROWS)
    _require(
        len(pages) == 1
        and pages[0]["source_object_sha256"] == silver_profile.SOURCE_SHA256
        and pages[0]["source_locator"] == silver_profile.SOURCE_LOCATOR
        and pages[0]["source_page"] == _SOURCE_PAGE
        and pages[0]["disposition"] == "partially_normalized"
        and pages[0]["reason"] == "fourteen_named_summary_financial_activity_rows_only"
    )
    _require(len({row["record_id"] for row in facts}) == len(facts))
    _require(
        [
            (row["section"], row["source_label"])
            for row in sorted(
                facts,
                key=lambda row: json.loads(row["raw_values_json"])[
                    "source_row_ordinal"
                ],
            )
        ]
        == list(silver_profile._EXPECTED_ROWS)  # noqa: SLF001
    )
    _require(
        len({(row["record_id"], row["field"]) for row in lineage}) == _LINEAGE_ROWS
        and {row["record_id"] for row in lineage} == {row["record_id"] for row in facts}
    )
    lineage_by_id: dict[str, list[dict[str, Any]]] = {}
    for row in lineage:
        _require(row["field"] in silver_profile.COLUMNS)
        lineage_by_id.setdefault(row["record_id"], []).append(row)
    for fact in facts:
        _require(
            fact["source_object_sha256"] == silver_profile.SOURCE_SHA256
            and fact["source_vintage"] == silver_profile.VINTAGE
            and fact["source_page"] == _SOURCE_PAGE
            and fact["unit"] == "$000"
            and fact["rights_state"] == "not_evaluated"
        )
        source_row = json.loads(fact["raw_values_json"])
        ordinal = source_row.get("source_row_ordinal")
        _require(
            type(ordinal) is int
            and 1 <= ordinal <= _FACT_ROWS
            and source_row.get("source_page") == fact["source_page"]
            and source_row.get("section") == fact["section"]
            and source_row.get("source_label") == fact["source_label"]
            and set(source_row.get("tokens", {})) == set(silver_profile.COLUMNS)
        )
        field_rows = lineage_by_id[fact["record_id"]]
        _require({row["field"] for row in field_rows} == set(silver_profile.COLUMNS))
        for field_row in field_rows:
            name = field_row["field"]
            value = fact[name]
            token = field_row["raw_value"]
            _require(source_row["tokens"][name] == token)
            expected = _raw_amount(token)
            normalized = field_row["normalized_value"]
            normalized_matches = (
                normalized == "None" if value is None else Decimal(normalized) == value
            )
            _require(
                field_row["source_object_sha256"] == silver_profile.SOURCE_SHA256
                and field_row["record_id"] == fact["record_id"]
                and normalized_matches
                and field_row["source_coordinate"].startswith(
                    f"pdf:page={_SOURCE_PAGE};"
                )
                and value == expected
            )
    _require(
        {json.loads(row["raw_values_json"])["source_row_ordinal"] for row in facts}
        == set(range(1, _FACT_ROWS + 1))
    )
    return facts, lineage


def _projection(
    facts: list[dict[str, Any]],
    lineage: list[dict[str, Any]],
    silver_manifest_sha256: str,
) -> tuple[pa.Table, pa.Table]:
    fact_rows: list[dict[str, Any]] = []
    for fact in facts:
        raw = json.loads(fact["raw_values_json"])
        fact_rows.append(
            {
                "record_id": fact["record_id"],
                "source_silver_manifest_sha256": silver_manifest_sha256,
                "source_object_sha256": fact["source_object_sha256"],
                "source_vintage": fact["source_vintage"],
                "source_page": fact["source_page"],
                "source_row_ordinal": raw["source_row_ordinal"],
                "section": fact["section"],
                "source_label": fact["source_label"],
                **{name: fact[name] for name in silver_profile.COLUMNS},
                "unit": fact["unit"],
                "rights_state": fact["rights_state"],
                "quality_flags": fact["quality_flags"],
                "transformation_id": fact["transformation_id"],
                "raw_values_json": fact["raw_values_json"],
            }
        )
    fact_rows.sort(key=lambda row: row["source_row_ordinal"])
    lineage_rows = [
        {
            "record_id": row["record_id"],
            "field": row["field"],
            "source_silver_manifest_sha256": silver_manifest_sha256,
            "source_object_sha256": row["source_object_sha256"],
            "source_locator": row["source_locator"],
            "source_coordinate": row["source_coordinate"],
            "raw_value": row["raw_value"],
            "normalized_value": row["normalized_value"],
            "rule": row["rule"],
        }
        for row in sorted(lineage, key=lambda item: (item["record_id"], item["field"]))
    ]
    return (
        pa.Table.from_pylist(fact_rows, schema=FACT_SCHEMA),
        pa.Table.from_pylist(lineage_rows, schema=LINEAGE_SCHEMA),
    )


def _summary(facts: pa.Table, lineage: pa.Table, pin: str) -> dict[str, Any]:
    rows = facts.to_pylist()
    fields = list(silver_profile.COLUMNS)
    return {
        "schema_version": VERSION,
        "source_silver_manifest_sha256": pin,
        "source_object_sha256": silver_profile.SOURCE_SHA256,
        "profile": silver_profile.PROFILE,
        "row_count": facts.num_rows,
        "lineage_row_count": lineage.num_rows,
        "sections": {
            section: sum(row["section"] == section for row in rows)
            for section in sorted({row["section"] for row in rows})
        },
        "null_cells_by_source_column": {
            field: sum(row[field] is None for row in rows) for field in fields
        },
        "row_identity": "source_record_id_and_printed_row_ordinal",
        "values": "source_reported_exact_decimal_in_source_unit",
        "calculations": "none",
        "cross_source_comparison": "not_performed",
        "semantic_comparability": "not_established",
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def _readme(summary: dict[str, Any]) -> bytes:
    lines = [
        "# Vote Health 2014/15 Supplementary Estimates financial activity",
        "",
        "This source-separated Gold view is a row-preserving projection of the",
        "pinned Silver facts. It performs no arithmetic or cross-source joins.",
        "",
        f"- Source object SHA-256: `{summary['source_object_sha256']}`",
        f"- Silver manifest SHA-256: `{summary['source_silver_manifest_sha256']}`",
        f"- Fact rows: {summary['row_count']}",
        f"- Field-lineage rows: {summary['lineage_row_count']}",
        "- Values retain the source unit `$000`; currency semantics are not inferred.",
        "- Rights are not evaluated; publication is not performed.",
        "- The extracted page remains partial; no edition comparison is made.",
        "",
        "Exact values and source coordinates are in the Parquet products.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def export_vote_health_financial_activity(
    silver_package_dir: Path,
    silver_manifest_sha256: str,
    output_dir: Path,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Project a verified Silver edition into a reproducible local Gold package."""
    _require(
        isinstance(silver_manifest_sha256, str)
        and len(silver_manifest_sha256) == _HASH_LENGTH
        and all(char in "0123456789abcdef" for char in silver_manifest_sha256)
    )
    silver = silver_package_dir.resolve()
    output = output_dir.resolve()
    _require(not output.is_relative_to(silver) and not silver.is_relative_to(output))
    facts, lineage = _silver_tables(silver_package_dir, silver_manifest_sha256)
    gold_facts, gold_lineage = _projection(facts, lineage, silver_manifest_sha256)
    summary = _summary(gold_facts, gold_lineage, silver_manifest_sha256)
    base = {
        "schema_version": VERSION,
        "status": "dry_run" if not write else "written",
        "row_count": gold_facts.num_rows,
        "lineage_row_count": gold_lineage.num_rows,
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    if not write:
        return base
    output_dir.mkdir(parents=True, exist_ok=False)
    payloads = {
        _FACT_PAYLOAD: _table_bytes(gold_facts),
        _LINEAGE_PAYLOAD: _table_bytes(gold_lineage),
        _SUMMARY_PAYLOAD: _json_bytes(summary),
        _README_PAYLOAD: _readme(summary),
    }
    _require(all(len(payload) <= MAX_BYTES for payload in payloads.values()))
    for name, payload in payloads.items():
        with (output_dir / name).open("xb") as stream:
            stream.write(payload)
    manifest = {
        "schema_version": VERSION,
        "status": "complete",
        "source_silver_manifest_sha256": silver_manifest_sha256,
        "source_object_sha256": silver_profile.SOURCE_SHA256,
        "payloads": {
            name: {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
            for name, payload in sorted(payloads.items())
        },
        "row_count": gold_facts.num_rows,
        "lineage_row_count": gold_lineage.num_rows,
        "verification_scope": "pinned_gold_payloads_schema_and_projection",
        "source_reverification": "not_performed_by_reader",
        "semantic_comparability": "not_established",
        "rights": "not_evaluated",
        "publication": "not_performed",
    }
    manifest_bytes = _json_bytes(manifest)
    with (output_dir / "MANIFEST.json").open("xb") as stream:
        stream.write(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    read_vote_health_financial_activity(output_dir, manifest_sha256)
    return {**base, "manifest_sha256": manifest_sha256}


def read_vote_health_financial_activity(
    package_dir: Path, manifest_sha256: str
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify a closed Gold package and recompute its structured projections."""
    _require(package_dir.is_dir() and not package_dir.is_symlink())
    expected_files = _PAYLOADS | {"MANIFEST.json"}
    _require({path.name for path in islice(package_dir.iterdir(), 6)} == expected_files)
    _require(all(not (package_dir / name).is_symlink() for name in expected_files))
    manifest_bytes = verified_snapshot(
        package_dir / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES
    )
    manifest = json.loads(manifest_bytes)
    _require(
        set(manifest)
        == {
            "schema_version",
            "status",
            "source_silver_manifest_sha256",
            "source_object_sha256",
            "payloads",
            "row_count",
            "lineage_row_count",
            "verification_scope",
            "source_reverification",
            "semantic_comparability",
            "rights",
            "publication",
        }
        and manifest["schema_version"] == VERSION
        and manifest["status"] == "complete"
        and manifest["source_object_sha256"] == silver_profile.SOURCE_SHA256
        and set(manifest["payloads"]) == _PAYLOADS
        and manifest["verification_scope"]
        == "pinned_gold_payloads_schema_and_projection"
        and manifest["source_reverification"] == "not_performed_by_reader"
        and manifest["semantic_comparability"] == "not_established"
        and manifest["rights"] == "not_evaluated"
        and manifest["publication"] == "not_performed"
    )
    payloads: dict[str, bytes] = {}
    for name, binding in manifest["payloads"].items():
        _require(set(binding) == {"sha256", "bytes"} and type(binding["bytes"]) is int)
        data = verified_snapshot(
            package_dir / name, binding["sha256"], max_bytes=MAX_BYTES
        )
        _require(len(data) == binding["bytes"])
        payloads[name] = data
    tables: dict[str, pa.Table] = {}
    for name, schema in (
        (_FACT_PAYLOAD, FACT_SCHEMA),
        (_LINEAGE_PAYLOAD, LINEAGE_SCHEMA),
    ):
        with pq.ParquetFile(
            BytesIO(payloads[name]),
            thrift_string_size_limit=MAX_BYTES,
            thrift_container_size_limit=100_000,
        ) as parquet:
            _require(_parquet_schema_matches(parquet.schema_arrow, schema))
            _require(parquet.metadata.num_rows <= _MAX_PARQUET_ROWS)
            tables[name] = parquet.read(use_threads=False)
    facts, lineage = tables[_FACT_PAYLOAD], tables[_LINEAGE_PAYLOAD]
    _require(
        type(manifest["row_count"]) is int
        and manifest["row_count"] == facts.num_rows == _FACT_ROWS
        and type(manifest["lineage_row_count"]) is int
        and manifest["lineage_row_count"] == lineage.num_rows == _LINEAGE_ROWS
        and {row["source_silver_manifest_sha256"] for row in facts.to_pylist()}
        == {manifest["source_silver_manifest_sha256"]}
        and {row["source_object_sha256"] for row in facts.to_pylist()}
        == {manifest["source_object_sha256"]}
        and {row["source_vintage"] for row in facts.to_pylist()}
        == {silver_profile.VINTAGE}
        and {row["source_page"] for row in facts.to_pylist()} == {_SOURCE_PAGE}
        and {row["unit"] for row in facts.to_pylist()} == {"$000"}
        and {row["rights_state"] for row in facts.to_pylist()} == {"not_evaluated"}
        and {row["source_row_ordinal"] for row in facts.to_pylist()}
        == set(range(1, _FACT_ROWS + 1))
        and len({row["record_id"] for row in facts.to_pylist()}) == _FACT_ROWS
        and {row["source_silver_manifest_sha256"] for row in lineage.to_pylist()}
        == {manifest["source_silver_manifest_sha256"]}
        and len({(row["record_id"], row["field"]) for row in lineage.to_pylist()})
        == _LINEAGE_ROWS
        and {row["record_id"] for row in lineage.to_pylist()}
        == {row["record_id"] for row in facts.to_pylist()}
    )
    summary = _summary(facts, lineage, manifest["source_silver_manifest_sha256"])
    _require(payloads[_SUMMARY_PAYLOAD] == _json_bytes(summary))
    _require(payloads[_README_PAYLOAD] == _readme(summary))
    verified_snapshot(
        package_dir / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES
    )
    return facts, lineage, summary


def query_vote_health_financial_activity(
    package_dir: Path,
    manifest_sha256: str,
    *,
    section: str | None = None,
    limit: int = MAX_ROWS,
) -> dict[str, Any]:
    """Return bounded exact rows from the verified source-separated fact table."""
    base = {"schema_version": QUERY_VERSION}
    if type(limit) is not int or not 1 <= limit <= MAX_ROWS:
        return {**base, "status": "failed", "error": "invalid_query"}
    if section is not None and section not in {
        "appropriations",
        "crown_revenue_and_capital_receipts",
    }:
        return {**base, "status": "failed", "error": "invalid_query"}
    try:
        facts, _, summary = read_vote_health_financial_activity(
            package_dir, manifest_sha256
        )
        rows = _query_rows(facts, section, limit)
    except OSError, ValueError, TypeError, KeyError, duckdb.Error, pa.ArrowException:
        return {**base, "status": "failed", "error": "query_failed"}
    for row in rows:
        for name in silver_profile.COLUMNS:
            if isinstance(row[name], Decimal):
                row[name] = str(row[name])
        for name, value in row.items():
            if isinstance(value, date):
                row[name] = value.isoformat()
    return {
        **base,
        "status": "verified",
        "manifest_sha256": manifest_sha256,
        "row_count": len(rows),
        "total_rows": facts.num_rows,
        "truncated": len(rows) < facts.num_rows,
        "section_filter": section,
        "rows": rows,
        "source_reverification": "not_performed",
        "semantic_comparability": "not_established",
        "rights": "not_evaluated",
        "publication": "not_performed",
        "summary": summary,
    }


def _query_rows(
    facts: pa.Table, section: str | None, limit: int
) -> list[dict[str, Any]]:
    database = duckdb.connect(":memory:")
    try:
        database.register("financial_activity", facts)
        if section is None:
            relation = database.sql(
                "SELECT * FROM financial_activity ORDER BY source_row_ordinal LIMIT ?",
                params=[limit],
            )
        else:
            relation = database.sql(
                "SELECT * FROM financial_activity WHERE section = ? "
                "ORDER BY source_row_ordinal LIMIT ?",
                params=[section, limit],
            )
        return relation.to_arrow_table().to_pylist()
    finally:
        database.close()
