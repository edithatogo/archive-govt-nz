"""Read reviewed Budget v1 packages without executing or reopening originals."""

from __future__ import annotations

import json
import re
from collections import Counter
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq
from openpyxl.utils.cell import column_index_from_string

from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    exact_number,
    identity,
    source_context,
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ROWS = 100_000
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_THRIFT_STRING_BYTES = 4 * 1024 * 1024
MAX_THRIFT_CONTAINERS = 100_000
FIRST_DATA_ROW = 2
MAX_COLUMNS = 16384
TRANSFORMATION = "budget-expenditure/v1"
# Deliberately frozen consumer contract, independent of the writer's private schema.
DISPOSITION_SCHEMA = pa.schema(
    [
        (name, pa.int64() if name == "source_row" else pa.string())
        for name in (
            "source_object_sha256",
            "source_locator",
            "sheet",
            "source_row",
            "disposition",
            "reason",
            "record_id",
            "raw_values_json",
        )
    ]
)
SCHEMAS = {
    "budget_facts.parquet": SILVER_SCHEMA,
    "field_lineage.parquet": LINEAGE_SCHEMA,
    "row_dispositions.parquet": DISPOSITION_SCHEMA,
}
FIELDS = {
    "Year": "year",
    "Department": "department",
    "Appropriation Name": "appropriation_name",
    "Functional Classification": "functional_classification",
    "Amount $000": "amount",
    "Amount Type": "amount_type",
    "Portfolio Name": "portfolio_name",
}


def _require(condition: object) -> None:
    if not condition:
        message = "budget_package_contract"
        raise ValueError(message)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(result) == len(pairs))
    return result


def _json(payload: bytes | str) -> dict[str, Any]:
    value = json.loads(payload, object_pairs_hook=_object)
    _require(isinstance(value, dict))
    return value


def _read(
    root: Path, pin: str
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    _require(isinstance(pin, str) and re.fullmatch(r"[0-9a-f]{64}", pin) is not None)
    _require(not root.is_symlink() and root.is_dir())
    _require(
        {path.name for path in islice(root.iterdir(), 5)}
        == set(SCHEMAS) | {"MANIFEST.json"}
    )
    for name in (*SCHEMAS, "MANIFEST.json"):
        _require(not (root / name).is_symlink() and (root / name).is_file())
    payload = verified_snapshot(root / "MANIFEST.json", pin, max_bytes=MAX_BYTES)
    manifest = _json(payload)
    _require(
        manifest["schema_version"] == "archive-govt-nz.health-budget-extraction/v1"
        and manifest["status"] == "passed"
        and manifest["transformation_id"] == TRANSFORMATION
        and manifest["rights_state"] == "not_evaluated"
    )
    _require(set(manifest["output_sha256"]) == set(SCHEMAS))
    total = len(payload)
    tables = {}
    for name, schema in SCHEMAS.items():
        payload = verified_snapshot(
            root / name, manifest["output_sha256"][name], max_bytes=MAX_BYTES
        )
        total += len(payload)
        _require(total <= MAX_TOTAL_BYTES)
        with pq.ParquetFile(
            BytesIO(payload),
            thrift_string_size_limit=MAX_THRIFT_STRING_BYTES,
            thrift_container_size_limit=MAX_THRIFT_CONTAINERS,
        ) as file:
            metadata = file.metadata
            _require(
                metadata.num_rows <= MAX_ROWS
                and sum(
                    metadata.row_group(i).total_byte_size
                    for i in range(metadata.num_row_groups)
                )
                <= MAX_EXPANDED_BYTES
            )
            _require(file.schema_arrow == schema)
            tables[name] = file.read().to_pylist()
    return tables, manifest


def _dispositions(
    rows: list[dict[str, Any]], manifest: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    sheets = [
        sheet
        for sheet in manifest["workbook_inventory"]["sheets"]
        if sheet["title"] == "Raw Data"
    ]
    _require(len(sheets) == 1)
    sheet = sheets[0]
    _require(
        type(sheet["max_row"]) is int
        and FIRST_DATA_ROW <= sheet["max_row"] <= MAX_ROWS + 1
    )
    _require(
        type(sheet["max_column"]) is int
        and len(FIELDS) + 1 <= sheet["max_column"] <= MAX_COLUMNS
    )
    _require(
        [row["source_row"] for row in rows] == list(range(2, sheet["max_row"] + 1))
    )
    counts = Counter(row["disposition"] for row in rows)
    expected = {
        name: counts[name]
        for name in ("normalized", "out_of_scope", "blank", "rejected")
    }
    _require(
        set(counts) <= set(expected)
        and counts["normalized"] > 0
        and counts["rejected"] == 0
    )
    _require(all(type(value) is int for value in manifest["counts"].values()))
    _require(manifest["counts"] == {**expected, "input": len(rows)})
    facts = {}
    headers = None
    for row in rows:
        _require(
            all(
                row[key] == manifest[key]
                for key in ("source_object_sha256", "source_locator")
            )
            and row["sheet"] == "Raw Data"
        )
        raw = _json(row["raw_values_json"])
        _require(
            len(raw) == sheet["max_column"]
            and {"Vote", *FIELDS} <= set(raw)
            and all(name.strip() for name in raw)
        )
        if headers is None:
            headers = set(raw)
        _require(set(raw) == headers)
        state = row["disposition"]
        if state == "normalized":
            record_id = identity(
                TRANSFORMATION,
                manifest["source_object_sha256"],
                "Raw Data",
                row["source_row"],
            )
            _require(
                row["record_id"] == record_id
                and row["reason"] == "named_columns"
                and raw["Vote"] == "Health"
            )
            facts[record_id] = row
        elif state == "blank":
            _require(
                row["record_id"] is None
                and row["reason"] == "empty_row"
                and all(value is None for value in raw.values())
            )
        else:
            _require(
                row["record_id"] is None
                and row["reason"] == "non_health_vote"
                and isinstance(raw["Vote"], str)
                and bool(raw["Vote"].strip())
                and raw["Vote"] != "Health"
            )
    return facts


def _facts(
    facts: list[dict[str, Any]],
    dispositions: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    context = source_context(
        manifest["source_object_sha256"],
        manifest["source_locator"],
        manifest["source_vintage"],
        manifest["observed_at"],
    )
    context.pop("source_observation_id")
    _require(
        len(facts) == len(dispositions)
        and {row["record_id"] for row in facts} == set(dispositions)
    )
    observations = {row["source_observation_id"] for row in facts}
    _require(
        len(observations) == 1
        and re.fullmatch(r"sha256:[0-9a-f]{64}", next(iter(observations))) is not None
    )
    for fact in facts:
        raw = _json(dispositions[fact["record_id"]]["raw_values_json"])
        expected = {
            **context,
            "schema_version": "archive-govt-nz.health-appropriations-silver/v1",
            "recordset": "appropriation_fact",
            "valid_time_start": None,
            "rights_state": "not_evaluated",
            "quality_flags": ["financial_year_basis_unverified"],
            "transformation_id": TRANSFORMATION,
            "lineage_id": identity(fact["record_id"], "lineage"),
            "donor_table": None,
            "donor_row_number": None,
            "measure": "appropriation_amount",
            "unit": "NZD_thousands",
            "raw_values_json": dispositions[fact["record_id"]]["raw_values_json"],
        }
        _require(all(fact[key] == value for key, value in expected.items()))
        for name, field in FIELDS.items():
            value = raw[name]
            if field in ("year", "amount"):
                value = exact_number(value, year=field == "year")
                _require(value is not None)
            else:
                _require(isinstance(value, str) and bool(value.strip()))
            _require(fact[field] == value)


def _lineage(
    facts: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    dispositions: dict[str, dict[str, Any]],
) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {fact["record_id"]: [] for fact in facts}
    for row in rows:
        _require(row["record_id"] in grouped)
        grouped[row["record_id"]].append(row)
    mapping = None
    for fact in facts:
        raw = _json(fact["raw_values_json"])
        fields = {FIELDS.get(name, f"raw:{name}"): name for name in raw}
        entries = grouped[fact["record_id"]]
        _require(
            len(entries) == len(fields)
            and {row["field"] for row in entries} == set(fields)
        )
        columns = {}
        for row in entries:
            name = fields[row["field"]]
            coordinate = re.fullmatch(
                r"'Raw Data'!([A-Z]+)([1-9][0-9]*)", row["source_coordinate"]
            )
            if coordinate is None:
                message = "budget_package_contract"
                raise ValueError(message)
            _require(
                int(coordinate[2]) == dispositions[fact["record_id"]]["source_row"]
            )
            columns[name] = column_index_from_string(coordinate[1])
            _require(
                all(
                    row[key] == fact[key]
                    for key in ("lineage_id", "source_object_sha256", "source_locator")
                )
                and row["rule"] == TRANSFORMATION
                and row["raw_value"] == str(raw[name])
                and row["normalized_value"] == str(fact.get(row["field"], raw[name]))
            )
        _require(set(columns.values()) == set(range(1, len(fields) + 1)))
        if mapping is None:
            mapping = columns
        _require(columns == mapping)


def read_verified_budget(
    root: Path, manifest_sha256: str
) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]
]:
    """Return typed facts, lineage, dispositions and manifest, in that order.

    Consumes capped hash-verified snapshots; no outputs, network, raw reopening,
    rights approval or hostile-Parquet sandbox is implied. v1 lost the original
    timestamp spelling used to hash observation IDs: their format/consistency,
    not their digest preimage, is checked. Record/lineage IDs are recomputed.
    Sorted raw JSON loses original header order; coordinates are checked for
    a consistent column bijection, not independently re-proven against XLSX.
    """
    tables, manifest = _read(root, manifest_sha256)
    facts = tables["budget_facts.parquet"]
    lineage = tables["field_lineage.parquet"]
    dispositions = tables["row_dispositions.parquet"]
    normalized = _dispositions(dispositions, manifest)
    _facts(facts, normalized, manifest)
    _lineage(facts, lineage, normalized)
    verified_snapshot(root / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES)
    return facts, lineage, dispositions, manifest
