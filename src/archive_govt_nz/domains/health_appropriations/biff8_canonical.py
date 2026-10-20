"""Canonical Budget facts replayed from closed Silver and original BIFF8.

Stored integers retain encoded witnesses. Text tokens, decimal source precision,
ISO currency, period starts and parent/category aggregation are not inferred.
"""

from __future__ import annotations

import json
from decimal import localcontext
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import budget_biff8
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    verified_snapshot,
    write_workbook_outputs,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
        CanonicalPackageInput,
    )

VERSION = "archive-govt-nz.health-biff8-canonical/v1"
RULE = "budget-2019-biff8-canonical/v1"
MAX_BYTES = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_ROWS = 100000
KINDS = {"biff8_budget": "expenditure", "biff8_revenue": "revenue"}
FACTS = {"expenditure": "appropriation_fact", "revenue": "revenue_fact"}


def _require(condition: object) -> None:
    if not condition:
        message = "biff8_canonical_contract"
        raise ValueError(message)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    _require(len(pairs) == len(result))
    return result


def _manifest(root: Path, pin: str) -> dict[str, Any]:
    _require(root.is_dir() and not root.is_symlink())
    _require(not (root / "MANIFEST.json").is_symlink())
    payload = verified_snapshot(root / "MANIFEST.json", pin, max_bytes=MAX_BYTES)
    value = json.loads(payload, object_pairs_hook=_object)
    _require(isinstance(value, dict))
    return value


def _transport_schema(schema: pa.Schema) -> pa.Schema:
    buffer = BytesIO()
    pq.write_table(pa.Table.from_batches([], schema=schema), buffer)
    with pq.ParquetFile(BytesIO(buffer.getvalue())) as file:
        return file.schema_arrow


def _read_table(payload: bytes, expected: pa.Table) -> None:
    _require(expected.nbytes <= MAX_EXPANDED)
    buffer = BytesIO()
    pq.write_table(expected, buffer)
    # Exact regeneration avoids decoding any attacker-controlled dictionary.
    if payload == buffer.getvalue():
        return
    with pq.ParquetFile(
        BytesIO(payload),
        thrift_string_size_limit=MAX_BYTES,
        thrift_container_size_limit=MAX_ROWS,
    ) as file:
        _require(
            file.schema_arrow.equals(
                _transport_schema(expected.schema), check_metadata=True
            )
        )
        _require(file.metadata.num_rows == expected.num_rows <= MAX_ROWS)
        _require(0 <= file.metadata.num_row_groups <= MAX_ROWS)
        expanded = 0
        for index in range(file.metadata.num_row_groups):
            group = file.metadata.row_group(index)
            for column_index in range(group.num_columns):
                column = group.column(column_index)
                _require(
                    not column.file_path
                    and column.total_uncompressed_size >= 0
                    and column.num_values >= 0
                    and group.num_rows >= 0
                )
                size = column.total_uncompressed_size
                if column.physical_type == "BYTE_ARRAY":
                    size *= max(1, column.num_values)
                expanded += size + 8 * (column.num_values + group.num_rows + 1)
        _require(expanded <= MAX_EXPANDED)
        restored = file.read(use_threads=False)
    _require(restored.cast(expected.schema).equals(expected, check_metadata=True))


def _check_package(
    root: Path,
    manifest: dict[str, Any],
    tables: Mapping[str, pa.Table],
    receipt: Mapping[str, Any],
) -> None:
    _require({p.name for p in root.iterdir()} == {*tables, "MANIFEST.json"})
    _require(set(manifest) == {*receipt, "output_sha256"})
    _require(encode_json({k: manifest[k] for k in receipt}) == encode_json(receipt))
    hashes = manifest["output_sha256"]
    _require(isinstance(hashes, dict) and set(hashes) == set(tables))
    total = 0
    for name, table in tables.items():
        path = root / name
        _require(not path.is_symlink())
        payload = verified_snapshot(path, hashes[name], max_bytes=MAX_BYTES)
        total += len(payload)
        _require(total <= MAX_EXPANDED)
        _read_table(payload, table)


def _common(
    fact: dict[str, Any], recordset: str, record_id: str, rule: str
) -> dict[str, Any]:
    schema = recordset_schema(recordset, version="v3")
    result = dict.fromkeys(schema.names)
    for name in (
        "source_object_sha256",
        "source_observation_id",
        "source_locator",
        "source_vintage",
        "valid_time_start",
        "valid_time_end",
        "observed_at",
        "rights_state",
        "quality_flags",
    ):
        result[name] = fact[name]
    result.update(
        record_id=record_id,
        schema_version="archive-govt-nz.health-recordsets/v3",
        recordset=recordset,
        domain="health_appropriations",
        valid_time_status="source_year_end_only",
        period_token=str(fact["year"]),
        observation_context="caller_supplied_not_capture_attestation",
        transformation_id=rule,
        lineage_id=identity(rule, fact["lineage_id"]),
        source_record_id=fact["record_id"],
        source_schema_version=fact["schema_version"],
        value_basis=fact["value_basis"],
    )
    return result


def _project(
    snapshot: budget_biff8.BiffBudgetSnapshot, kind: str, rule: str
) -> dict[str, pa.Table]:
    name = FACTS[kind]
    facts, links = [], []
    source_facts = snapshot.tables["budget_facts.parquet"].to_pylist()
    by_id = {fact["record_id"]: fact for fact in source_facts}
    for source in source_facts:
        record_id = identity(rule, source["record_id"])
        fact = _common(source, name, record_id, rule)
        for field in (
            "amount",
            "unit",
            "currency",
            "amount_type",
            "vote",
            "department",
            "canonical_stored_integer",
            "numeric_evidence_id",
        ):
            fact[field] = source[field]
        fact.update(
            measure="published_appropriation"
            if kind == "expenditure"
            else "published_revenue",
            source_label=source[
                "appropriation_name" if kind == "expenditure" else "description"
            ],
        )
        if kind == "expenditure":
            fact.update(
                appropriation=source["appropriation_name"],
                portfolio=source["portfolio_name"],
                classification_ids=[],
            )
        else:
            fact.update(
                revenue_type=source["revenue_type"],
                source_application_id=source["app_id"],
            )
        facts.append(fact)
    for index, source in enumerate(
        snapshot.tables["field_lineage.parquet"].to_pylist()
    ):
        parent = by_id[source["record_id"]]
        link = _common(
            parent,
            "field_lineage",
            identity(rule, "field", index, parent["record_id"]),
            rule,
        )
        link.update(
            target_record_id=identity(rule, parent["record_id"]),
            field=source["field"],
            source_coordinate=source["source_coordinate"],
            raw_value=source["raw_value"],
            normalized_value=source["normalized_value"],
            rule=rule,
            value_basis=source["value_basis"],
            numeric_evidence_id=source["numeric_evidence_id"],
            canonical_stored_integer=None,
        )
        if source["numeric_evidence_id"] is not None:
            link["canonical_stored_integer"] = str(int(parent[source["field"]]))
        links.append(link)
    return {
        name: pa.Table.from_pylist(facts, schema=recordset_schema(name, version="v3")),
        "field_lineage": pa.Table.from_pylist(
            links, schema=recordset_schema("field_lineage", version="v3")
        ),
        "numeric_evidence": snapshot.tables["numeric_evidence.parquet"],
    }


def _source_profile(
    kind: str, manifest: dict[str, Any]
) -> budget_biff8.BiffBudgetProfile:
    candidates = [
        profile
        for profile in budget_biff8.declared_profiles()
        if profile.kind == kind
        and (
            profile.profile_id,
            profile.source_sha256,
            profile.source_locator,
            profile.source_vintage,
        )
        == (
            manifest.get("profile"),
            manifest.get("source_object_sha256"),
            manifest.get("source_locator"),
            manifest.get("source_vintage"),
        )
    ]
    _require(len(candidates) == 1)
    return candidates[0]


def project_package(
    silver: Path, pin: str, original: Path, kind: str, *, observed_at: str
) -> tuple[dict[str, pa.Table], dict[str, Any]]:
    """Replay every Silver row, definition and witness against trusted Bronze."""
    _require(kind in FACTS and not original.is_symlink())
    manifest = _manifest(silver, pin)
    spec = _source_profile(kind, manifest)
    rule = f"budget-{spec.edition}-biff8-canonical/v1"
    payload = verified_snapshot(
        original, spec.source_sha256, max_bytes=budget_biff8.MAX_BYTES
    )
    with localcontext() as context:
        context.prec = 50
        snapshot = budget_biff8.parse_snapshot(
            payload, profile=spec, observed_at=observed_at
        )
    _require(snapshot.metadata["status"] == "passed")
    _check_package(silver, manifest, snapshot.tables, snapshot.metadata)
    tables = _project(snapshot, kind, rule)
    _require(
        all(
            field.nullable or table[field.name].null_count == 0
            for table in tables.values()
            for field in table.schema
        )
    )
    receipt = {
        "schema_version": VERSION,
        "transformation_id": rule,
        "kind": kind,
        "source_object_sha256": spec.source_sha256,
        "source_vintage": spec.source_vintage,
        "silver_manifest_sha256": pin,
        "observation_time_token": observed_at,
        "rows": {name: table.num_rows for name, table in tables.items()},
        "aggregation": "none",
        "netting": "not_performed",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    return tables, receipt


def export_canonical(  # noqa: PLR0913 - explicit pins and original observation token.
    silver: Path,
    pin: str,
    original: Path,
    kind: str,
    output: Path,
    *,
    write: bool = False,
    observed_at: str,
) -> dict[str, Any]:
    """Use the existing exclusive writer; never overwrite inputs or derivatives."""
    _require(type(write) is bool and not output.exists() and not output.is_symlink())
    for protected in (silver, original):
        _require(not output.resolve().is_relative_to(protected.resolve()))
        _require(not protected.resolve().is_relative_to(output.resolve()))
    tables, receipt = project_package(
        silver, pin, original, kind, observed_at=observed_at
    )
    if not write:
        return {**receipt, "status": "planned"}
    result = write_workbook_outputs(
        output, {name + ".parquet": table for name, table in tables.items()}, receipt
    )
    _check_package(
        output,
        result,
        {name + ".parquet": table for name, table in tables.items()},
        receipt,
    )
    return result


def read_canonical(
    value: CanonicalPackageInput,
) -> tuple[dict[str, pa.Table], dict[str, Any]]:
    """Recompute canonical facts and every companion table before consumption."""
    kind = KINDS[value.kind]
    manifest = _manifest(value.root, value.marker_sha256)
    tables, receipt = project_package(
        value.raw_root,
        value.raw_manifest_sha256,
        value.original,
        kind,
        observed_at=manifest["observation_time_token"],
    )
    _check_package(
        value.root,
        manifest,
        {name + ".parquet": table for name, table in tables.items()},
        receipt,
    )
    return tables, {
        "kind": value.kind,
        "vintage": receipt["source_vintage"],
        "marker_sha256": value.marker_sha256,
        "raw_manifest_sha256": value.raw_manifest_sha256,
        "original_sha256": receipt["source_object_sha256"],
        "projection_equality": receipt["transformation_id"],
    }


def add_gold_products(
    packages: tuple[CanonicalPackageInput, ...],
    tables: dict[str, pa.Table],
    products: dict[str, dict[str, Any]],
    receipts: list[dict[str, Any]],
) -> None:
    """Carry verified canonical rows and witnesses into existing Gold exports."""
    seen: set[tuple[str, str]] = set()
    selected: dict[str, list[tuple[dict[str, pa.Table], dict[str, Any]]]] = {
        kind: [] for kind in KINDS
    }
    for package in packages:
        if package.kind not in KINDS:
            continue
        canonical, receipt = read_canonical(package)
        key = (package.kind, receipt["vintage"])
        _require(key not in seen)
        seen.add(key)
        selected[package.kind].append((canonical, receipt))
    for kind, values in selected.items():
        if not values:
            continue
        for suffix, source_name, order in (
            ("", FACTS[KINDS[kind]], "record_id"),
            ("_lineage", "field_lineage", "record_id"),
            ("_numeric", "numeric_evidence", "numeric_evidence_id"),
        ):
            parts = [canonical[source_name] for canonical, _ in values]
            tables[kind + suffix] = (
                parts[0]
                if len(parts) == 1
                else pa.concat_tables(parts).sort_by([(order, "ascending")])
            )
        count = tables[kind].num_rows
        products[kind] = {
            "input_records": count,
            "output_rows": count,
            "aggregation": "none",
            "netting": "not_performed",
            "vintage_pooling": "not_performed",
            "value_basis": budget_biff8.BASIS,
            "canonical_schema": "archive-govt-nz.health-recordsets/v3",
            "numeric_witness_rows": tables[kind + "_numeric"].num_rows,
            "revision_reconciliation": (
                "excluded_unqualified_cross_profile_comparability"
            ),
            "classification_mapping": "not_inferred",
            "plots": "excluded_unqualified_parent_category_series",
        }
        receipts.append(
            {
                "input_records": count,
                "package_marker_sha256": sorted(
                    receipt["marker_sha256"] for _, receipt in values
                ),
            }
        )


def initialize_gold(
    packages: tuple[CanonicalPackageInput, ...],
    tables: dict[str, pa.Table],
    receipts: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Initialize optional stored-integer products within the common exporter."""
    products: dict[str, dict[str, Any]] = {}
    add_gold_products(packages, tables, products, receipts)
    return products


def drillthrough_evidence(kind: str, lineage: dict[str, Any]) -> dict[str, Any]:
    """Add an explicit witness lookup to source coordinates for BIFF8 only."""
    if kind not in KINDS:
        return {}
    return {
        "full_lineage_output": kind + "_lineage.parquet",
        "canonical_lineage_id": lineage["lineage_id"],
        "value_basis": lineage["value_basis"],
        "numeric_evidence_id": lineage["numeric_evidence_id"],
        "witness_output": (
            kind + "_numeric.parquet" if lineage["numeric_evidence_id"] else None
        ),
    }


def is_companion(name: str) -> bool:
    """Drill through fact rows once; retain companion files in output fixity."""
    return name in {
        kind + suffix for kind in KINDS for suffix in ("_numeric", "_lineage")
    }


def gold_inline_lineage(kind: str, table: pa.Table) -> list[dict[str, Any]]:
    """Inline numeric lookups; the hashed companion retains every source link."""
    rows = table.to_pylist()
    if kind in KINDS:
        return [row for row in rows if row["numeric_evidence_id"] is not None]
    return rows
