"""Pure Budget source-label occurrences, not an authoritative classification."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import budget_reader
from archive_govt_nz.domains.health_appropriations.silver import (
    LINEAGE_SCHEMA,
    SILVER_SCHEMA,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

RULE = "budget-functional-classification-source-label/v1"
SCHEME = "budget_workbook_functional_classification_source_label"
LABELS = frozenset(
    {
        "Health",
        "Core Government Services",
        "No Functional Classification",
        "Social Security and Welfare",
    }
)
_MAX_ROWS = 100_000
_TRANSPORT = SILVER_SCHEMA.set(
    SILVER_SCHEMA.get_field_index("quality_flags"),
    pa.field("quality_flags", pa.list_(pa.field("element", pa.string()))),
)


@dataclass(frozen=True)
class ClassificationProjection:
    """Fresh occurrence dimensions and complete original-lineage accounting."""

    tables: dict[str, pa.Table]
    receipt: dict[str, Any]


def _require(condition: object) -> None:
    if not condition:
        message = "budget_classification_contract"
        raise ValueError(message)


def _id(*parts: object) -> str:
    payload = json.dumps(
        parts,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _validate(
    manifest: dict[str, Any],
    pin: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require(isinstance(pin, str) and re.fullmatch(r"[0-9a-f]{64}", pin))
    _require(
        manifest["schema_version"] == "archive-govt-nz.health-budget-extraction/v1"
    )
    _require(manifest["status"] == "passed")
    _require(manifest["transformation_id"] == "budget-expenditure/v1")
    _require(manifest["rights_state"] == "not_evaluated")
    _require(manifest["source_vintage"] in ("Budget-2025", "Budget-2026"))
    _require(
        facts.schema.equals(SILVER_SCHEMA, check_metadata=True)
        or facts.schema.equals(_TRANSPORT, check_metadata=True)
    )
    for table, schema in (
        (lineage, LINEAGE_SCHEMA),
        (dispositions, budget_reader.DISPOSITION_SCHEMA),
    ):
        _require(table.schema.equals(schema, check_metadata=True))
    _require(
        all(0 < table.num_rows <= _MAX_ROWS for table in (facts, lineage, dispositions))
    )
    rows, links = facts.to_pylist(), lineage.to_pylist()
    # Reuse existing pure consistency checks only: no package/path read occurs.
    normalized = budget_reader._dispositions(  # noqa: SLF001 - shared pure contract
        sorted(dispositions.to_pylist(), key=lambda row: row["source_row"]),
        manifest,
    )
    budget_reader._facts(rows, normalized, manifest)  # noqa: SLF001
    budget_reader._lineage(rows, links, normalized)  # noqa: SLF001
    _require(all(row["functional_classification"] in LABELS for row in rows))
    return rows, links


def _dimension(row: dict[str, Any], link: dict[str, Any], pin: str) -> dict[str, Any]:
    record = dict.fromkeys(recordset_schema("classification_dimension").names)
    for field in (
        "source_object_sha256",
        "source_observation_id",
        "source_locator",
        "source_vintage",
        "observed_at",
        "rights_state",
    ):
        record[field] = row[field]
    record_id = _id(
        RULE,
        pin,
        row["source_object_sha256"],
        row["source_vintage"],
        row["record_id"],
        "functional_classification",
        link["source_coordinate"],
    )
    record.update(
        record_id=record_id,
        schema_version="archive-govt-nz.health-recordsets/v1",
        recordset="classification_dimension",
        domain="health_appropriations",
        source_record_id=row["record_id"],
        source_schema_version=row["schema_version"],
        transformation_id=RULE,
        lineage_id=_id(record_id, "lineage"),
        observation_context="caller_supplied_extraction_observation",
        valid_time_status="not_established",
        quality_flags=[
            *row["quality_flags"],
            "source_label_only",
            "unmapped_classification",
        ],
        scheme=SCHEME,
        source_label=row["functional_classification"],
        mapping_state="unmapped",
        mapping_method="source_label_retention_only",
        mapping_evidence=json.dumps(
            {
                "input_manifest_sha256": pin,
                "source_coordinate": link["source_coordinate"],
                "source_lineage_identity": _id(pin, link),
            },
            sort_keys=True,
        ),
    )
    return record


def project_budget_classification(
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> ClassificationProjection:
    """Project caller-verified inputs without I/O, crosswalk or rights promotion.

    Only the literal functional-classification field is projected. Input package
    retention and byte verification are caller responsibilities. Every original
    lineage row is mapped or explicitly retained-only; input objects are intact.
    """
    rows, links = _validate(manifest, manifest_sha256, facts, lineage, dispositions)
    selected = {
        link["record_id"]: link
        for link in links
        if link["field"] == "functional_classification"
    }
    dimensions = {
        row["record_id"]: _dimension(row, selected[row["record_id"]], manifest_sha256)
        for row in rows
    }
    output_links, accounting = [], []
    for link in links:
        source_id = _id(manifest_sha256, link)
        targets = []
        if link["field"] == "functional_classification":
            dimension = dimensions[link["record_id"]]
            record = {
                key: dimension[key]
                for key in recordset_schema("field_lineage").names
                if key in dimension
            }
            record_id = _id(RULE, dimension["record_id"], source_id, "source_label")
            record.update(
                record_id=record_id,
                recordset="field_lineage",
                source_schema_version=manifest["schema_version"],
                target_record_id=dimension["record_id"],
                field="source_label",
                source_coordinate=link["source_coordinate"],
                raw_value=link["raw_value"],
                normalized_value=dimension["source_label"],
                rule=RULE,
            )
            output_links.append(record)
            targets.append(record_id)
        accounting.append(
            {
                "source_lineage_id": source_id,
                "state": "mapped" if targets else "retained_only",
                "target_lineage_record_ids": targets,
            }
        )
    tables = {
        name: pa.Table.from_pylist(
            sorted(values, key=lambda row: row["record_id"]),
            schema=recordset_schema(name),
        )
        for name, values in (
            ("classification_dimension", list(dimensions.values())),
            ("field_lineage", output_links),
        )
    }
    return ClassificationProjection(
        tables,
        {
            "schema_version": (
                "archive-govt-nz.health-budget-classification-projection/v1"
            ),
            "status": "passed",
            "input_fixity": "not_performed",
            "input_manifest_sha256": manifest_sha256,
            "rights_state": "not_evaluated",
            "publication_approval": "not_granted",
            "authoritative_mapping": "not_performed",
            "lineage_accounting": sorted(
                accounting, key=lambda row: row["source_lineage_id"]
            ),
            "retained_source_fields": [
                name
                for name in SILVER_SCHEMA.names
                if name != "functional_classification"
            ],
        },
    )
